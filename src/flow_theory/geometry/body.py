"""Bodies for the shock workflows, built from canonical-geometries.

The body is canonical-geometries' [geometry] contract, as a geometry file gives it
(geometry.toml, written by `geometry <type> init` and read with load_geometry; the
same file grid-generator reads), or as a config gives its keys directly. A calculation along the body ends at x_e, which
lies on the body: by default at its end, otherwise before it. The body is never
lengthened to reach x_e; a longer body (or a tangent ogive's cylinder) is set in
the geometry file.
"""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from canonical_geometries import Profile2D
from canonical_geometries.config import GeometryConfig
from pydantic import TypeAdapter
from scipy.optimize import brentq

# --------------------------------------------------
# module constants
# --------------------------------------------------

# nose shape per geometry type: planar bodies have a cylindrical nose, axisymmetric
# bodies a spherical one (this picks the standoff and shock-shape correlations)
NOSE_SHAPES = {
    "plate": "cylinder",
    "wedge": "cylinder",
    "cone": "sphere",
    "tangent-ogive": "sphere",
}

BODY_GEOMETRIES = tuple(NOSE_SHAPES)

# x_e may pass the body's end by this fraction of it (round-off in the end point)
END_TOLERANCE = 1.0e-12

# validates a raw [geometry] table into the model its "type" picks
_GEOMETRY_ADAPTER = TypeAdapter(GeometryConfig)


# --------------------------------------------------
# result type
# --------------------------------------------------
@dataclass(frozen=True, slots=True)
class Body:
    """A body profile and what the shock correlations need to know about it.

    Attributes:
        geometry: Geometry type ("plate", "wedge", "cone", "tangent-ogive").
        nose_radius: Nose radius [m].
        nose_shape: "sphere" (axisymmetric bodies) or "cylinder" (planar bodies).
        profile: Exact wall profile from the stagnation point (x = 0) to the body's
            end, at or past x_e.
        s_end: Arc length of the profile at x_e.
    """

    geometry: str
    nose_radius: float
    nose_shape: str
    profile: Profile2D
    s_end: float

    @property
    def axisymmetric(self) -> bool:
        """Whether the profile is the meridian of an axisymmetric body."""
        return self.nose_shape == "sphere"


# --------------------------------------------------
# public API
# --------------------------------------------------
def parse_geometry(table: dict[str, Any], label: str = "geometry") -> GeometryConfig:
    """Validate a raw [geometry] table (canonical-geometries' contract, length included).

    Configs give the body in [shock_shape.geometry], as a geometry file or by these
    keys; this is for building a body in Python.

    Args:
        table: Raw [geometry] table, e.g. {"type": "cone", "nose_radius": 0.01,
            "length": 0.1, "half_angle": 7.0}.
        label: Table name for error messages.

    Returns:
        Validated geometry model.

    Raises:
        ValueError: If the type isn't supported or the table doesn't validate.
    """

    # check: a supported type
    geometry_type = table.get("type")
    if geometry_type not in NOSE_SHAPES:
        raise ValueError(
            f"[{label}] type must be one of {', '.join(BODY_GEOMETRIES)}: got {geometry_type!r}"
        )

    # validate (pydantic's ValidationError is a ValueError)
    geometry = _GEOMETRY_ADAPTER.validate_python(table)

    return geometry


def body_end(geometry: GeometryConfig) -> float:
    """Streamwise end of the body [m]: x of its profile's last point.

    Args:
        geometry: Validated geometry model.

    Returns:
        x [m] where the body ends, measured from the nose tip.
    """

    # build the profile and take its last point
    profile = geometry.build()
    x_end, _ = profile.point(profile.total_length)

    return float(x_end)


def resolve_x_e(
    geometry: GeometryConfig, x_e: float | None, source: str | None = None
) -> float:
    """Where a calculation along the body ends: x_e, at most the body's end.

    Args:
        geometry: Validated geometry model.
        x_e: Streamwise end [m], measured from the nose tip; None for the body's end.
        source: Where the body came from (e.g. the geometry file), for the message.

    Returns:
        x_e [m], or the body's end if x_e is None.

    Raises:
        ValueError: If x_e isn't positive and finite, or lies past the body's end.
    """

    # default: the body's end
    x_body_end = body_end(geometry)
    if x_e is None:
        return x_body_end

    # validate inputs
    if not math.isfinite(x_e) or x_e <= 0.0:
        raise ValueError(f"x_e must be finite and positive: {x_e}")

    # check: x_e lies on the body (the body is never lengthened to reach it)
    if x_e > x_body_end * (1.0 + END_TOLERANCE):
        # name where the body came from, when known
        where = "the body"
        fix = "lengthen the body"
        if source is not None:
            where = f"the body in {source}"
            fix = f"lengthen the body in {source}"
        raise ValueError(
            f"x_e = {x_e:.6g} m lies past the end of {where} (x = {x_body_end:.6g} m): "
            f"{fix}, or lower x_e"
        )

    return x_e


def build_body(geometry: GeometryConfig, x_e: float) -> Body:
    """Build the body profile, and where x_e lies on it.

    Args:
        geometry: Validated geometry model (load_geometry, or parse_geometry).
        x_e: Streamwise end of the calculation [m], measured from the nose tip; at
            most the body's end.

    Returns:
        The body, its profile as the geometry gives it, and s_end at x_e.

    Raises:
        ValueError: If x_e isn't positive and finite, or lies past the body's end.
    """

    # validate inputs: x_e on the body
    resolve_x_e(geometry, x_e)

    # build the body as given
    profile = geometry.build()

    # arc length at x_e (x grows along all these profiles)
    s_end = arc_length_at_x(profile, x_e)

    body = Body(
        geometry=geometry.type,
        nose_radius=geometry.nose_radius,
        nose_shape=NOSE_SHAPES[geometry.type],
        profile=profile,
        s_end=s_end,
    )

    return body


def arc_length_at_x(profile: Profile2D, x: float) -> float:
    """Arc length where the profile reaches x; the profile's end if it never does.

    Args:
        profile: Wall profile whose x grows with arc length.
        x: Streamwise position [m].

    Returns:
        Arc length s with x(s) = x, clamped to the profile.
    """

    # the ends: before the stagnation point, or past the end of the body
    total_length = profile.total_length
    x_last = float(profile.point(total_length)[0])
    if x >= x_last:
        return total_length
    if x <= 0.0:
        return 0.0

    # solve x(s) = x
    def distance_to_x(s: float) -> float:
        return float(profile.point(s)[0]) - x

    s_at_x = brentq(distance_to_x, 0.0, total_length, xtol=1.0e-14)

    return s_at_x
