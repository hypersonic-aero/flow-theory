"""Bodies for the shock workflows, built from canonical-geometries.

The [geometry] table is canonical-geometries' contract, without the key that only
says how far the body extends: the calculation ends at x_e, so the body does too.
For plate, wedge and cone the length is filled in from x_e; for the tangent ogive
(whose length is a shape parameter) a cylinder carries the body on when x_e lies past
the base.
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

# [geometry] key per type that only says how far the body extends; x_e sets it
# instead (the tangent ogive's length is a shape parameter and stays)
EXTENT_KEYS = {
    "plate": "length",
    "wedge": "length",
    "cone": "length",
    "tangent-ogive": "cylinder_length",
}

# nose shape per geometry type: planar bodies have a cylindrical nose, axisymmetric
# bodies a spherical one (this picks the standoff and shock-shape correlations)
NOSE_SHAPES = {
    "plate": "cylinder",
    "wedge": "cylinder",
    "cone": "sphere",
    "tangent-ogive": "sphere",
}

BODY_GEOMETRIES = tuple(NOSE_SHAPES)

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
        profile: Exact wall profile from the stagnation point (x = 0) to x_e.
        s_end: Arc length of the profile at x_e (or its end, if it is shorter).
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
def parse_geometry(
    table: dict[str, Any], x_e: float, label: str = "geometry"
) -> GeometryConfig:
    """Validate a [geometry] table whose body ends at x_e.

    Args:
        table: Raw [geometry] table (canonical-geometries' contract without its extent key).
        x_e: Streamwise end of the calculation [m], measured from the nose tip.
        label: Table name for error messages.

    Returns:
        Validated geometry model, with length filled in from x_e where it is only the extent.

    Raises:
        ValueError: If the type isn't supported, the extent key is given, or the
            table doesn't validate.
    """

    # fill in the extent from x_e
    filled = fill_geometry_extent(table, x_e, label=label)

    # validate (pydantic's ValidationError is a ValueError)
    geometry = _GEOMETRY_ADAPTER.validate_python(filled)

    return geometry


def fill_geometry_extent(
    table: dict[str, Any], x_e: float, label: str = "geometry"
) -> dict[str, Any]:
    """Check a raw [geometry] table and fill in its extent from x_e (no validation).

    Args:
        table: Raw [geometry] table (canonical-geometries' contract without its extent key).
        x_e: Streamwise end of the calculation [m], measured from the nose tip.
        label: Table name for error messages.

    Returns:
        A copy of the table with length set to x_e where it is only the extent.

    Raises:
        ValueError: If the type isn't supported or the extent key is given.
    """

    # check: a supported type
    geometry_type = table.get("type")
    if geometry_type not in NOSE_SHAPES:
        raise ValueError(
            f"[{label}] type must be one of {', '.join(BODY_GEOMETRIES)}: got {geometry_type!r}"
        )

    # check: no extent of its own
    extent_key = EXTENT_KEYS[geometry_type]
    if extent_key in table:
        raise ValueError(
            f"[{label}] {extent_key} isn't used: the body ends at x_e; remove {extent_key}"
        )

    # fill in length where it is only the extent
    filled = dict(table)
    if extent_key == "length":
        filled["length"] = x_e

    return filled


def build_body(geometry: GeometryConfig, x_e: float) -> Body:
    """Build the body profile up to x_e.

    Args:
        geometry: Validated geometry model (see parse_geometry).
        x_e: Streamwise end of the calculation [m], measured from the nose tip.

    Returns:
        The body, with its profile reaching x_e where the geometry allows.

    Raises:
        ValueError: If x_e isn't positive and finite.
    """

    # validate inputs
    if not math.isfinite(x_e) or x_e <= 0.0:
        raise ValueError(f"x_e must be finite and positive: {x_e}")

    # build the body as given
    profile = geometry.build()

    # tangent ogive: a cylinder carries the body on to an x_e past the base
    if geometry.type == "tangent-ogive":
        x_base, _ = profile.base_point
        if x_e > x_base:
            cylinder_length = x_e - x_base
            extended = geometry.model_copy(update={"cylinder_length": cylinder_length})
            profile = extended.build()

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
