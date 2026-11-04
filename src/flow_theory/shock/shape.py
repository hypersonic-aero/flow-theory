"""Empirical detached bow-shock shapes for blunt hypersonic bodies.

Billig (1967) fits the bow shock ahead of a blunt body with a hyperbola,

    x = -delta + R_c cot^2(beta) [ sqrt(1 + y^2 tan^2(beta) / R_c^2) - 1 ],

with the nose tip at x = 0, the standoff distance delta, the shock radius of
curvature at the vertex R_c, and the asymptote angle beta: the shock angle of the
sharp body behind the nose (sharp cone or wedge; the Mach angle for a plate or
cylinder). Written as a slope,

    dx/dy = (y / R_c) / sqrt(1 + y^2 tan^2(beta) / R_c^2),

the same curve follows from integrating dx/dy in y from the vertex. Here beta is
taken at the local body station instead of once for the whole body: the sharp-cone
(Taylor-Maccoll) or sharp-wedge (oblique-shock) angle of the surface angle at the
same x. For a constant surface angle (plate, wedge, cone) this is Billig's
hyperbola; for a curved body (tangent ogive) the shock angle follows the surface.

The hyperbola's asymptote is offset from the sharp-body shock by about
R_c cot(beta), which holds near the nose but overpredicts the shock far
downstream, where the nose's influence fades; on a curved body the local angle
also lets the shock follow the surface too quickly. Method "billig_blended"
(wedges, cones, tangent ogives) blends two shocks:

- near the nose, Billig's hyperbola with the sharp body's tip shock angle as its
  asymptote;
- downstream, the shock of the sharp body the blunt body follows behind its nose,
  starting at its virtual origin (the sharp tip): computed by the method of
  characteristics (gasdyn.solve_sharp_body), a straight line for wedges and cones
  (from x_v = R_n (1 - 1 / sin(theta))) and a curved shock for ogives,

    y(x) = w y_billig(x) + (1 - w) y_sharp(x),   w = 1 / (1 + (x / R_n) / L),

with the blend length L in nose radii. Both are inviscid: a laminar boundary
layer pushes the real shock out further downstream (by about
tan(beta)/tan(theta) times its displacement thickness on a cone).
"""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from canonical_geometries.config import GeometryConfig
from gasdyn import solve_oblique, solve_sharp_body, solve_taylor_maccoll
from numpy.typing import NDArray
from scipy.integrate import solve_ivp

from flow_theory.geometry import Body, build_body

from .standoff import ShockStandoffResult, compute_shock_standoff

# --------------------------------------------------
# module constants
# --------------------------------------------------

# Billig (1967) shock radius-of-curvature constants by geometry
_BILLIG_RC_PARAMS = {
    "sphere": {
        "coefficient": 1.143,
        "exponent_coefficient": 0.54,
        "exponent_power": 1.2,
    },
    "cylinder": {
        "coefficient": 1.386,
        "exponent_coefficient": 1.8,
        "exponent_power": 0.75,
    },
}

SHOCK_SHAPE_METHODS = ("billig", "billig_blended")

# billig_blended: default blend length L [nose radii]
_DEFAULT_BLEND_NOSE_RADII = 35.0

# billig_blended needs a sharp body behind the nose (it has a virtual origin)
_SHARP_BODY_TYPES = ("wedge", "cone", "tangent-ogive")

# points of the sharp-body profile handed to the method of characteristics
_SHARP_BODY_SIZE = 20001

# sharp-body shock table: shock angles from just above the Mach angle [deg] to near
# normal, spaced geometrically so small surface angles (an ogive's base) are resolved
_TABLE_SIZE = 200
_TABLE_EXCESS_MIN = 1.0e-6
_TABLE_SHOCK_ANGLE_MAX = 89.5

# points of the dense body and shock samples the output points are taken from
_DENSE_SIZE = 20001

# the dense samples cluster geometrically toward the nose, starting at this fraction
# of the nose scale (nose radius on the body, shock radius on the shock)
_DENSE_FIRST_FRACTION = 1.0e-3


# --------------------------------------------------
# result type
# --------------------------------------------------
@dataclass(frozen=True, slots=True)
class ShockShapeResult:
    """Computed detached bow-shock locus and the body it belongs to.

    Attributes:
        x: Shock x from the vertex (x = -delta) to x_e [m]; points equally spaced in
            arc length and turning angle (half each), so the vertex is resolved.
        y: Shock y (distance from the axis or symmetry plane) [m].
        body_x: Body x from the stagnation point to x_e [m], spread like the shock.
        body_y: Body y [m].
        standoff: Standoff estimate that places the shock vertex.
        geometry: Body geometry type.
        method: Shock-shape correlation name.
        x_e: Streamwise end [m].
        shock_radius: Shock radius of curvature at the vertex [m].
    """

    x: NDArray[np.float64]
    y: NDArray[np.float64]
    body_x: NDArray[np.float64]
    body_y: NDArray[np.float64]
    standoff: ShockStandoffResult
    geometry: str
    method: str
    x_e: float
    shock_radius: float


# --------------------------------------------------
# sharp-body shock angles: cones for axisymmetric bodies, wedges for planar ones
# --------------------------------------------------
def _cone_angle(mach: float, shock_angle: float, gamma: float) -> float:
    """Cone half-angle [deg] whose attached shock has the given angle (Taylor-Maccoll)."""
    result = solve_taylor_maccoll(mach=mach, shock_angle=shock_angle, gamma=gamma)
    cone_angle = float(result.cone_angle)
    return cone_angle


def _wedge_angle(mach: float, shock_angle: float, gamma: float) -> float:
    """Wedge half-angle [deg] whose attached shock has the given angle (oblique shock)."""
    result = solve_oblique(mach=mach, shock_angle=shock_angle, gamma=gamma)
    wedge_angle = float(result.deflection_angle)
    return wedge_angle


# body angle behind a given sharp-body shock, by nose shape: spherical noses sit on
# axisymmetric bodies (cones), cylindrical noses on planar bodies (wedges)
_BODY_ANGLE_SOLVERS = {
    "sphere": _cone_angle,
    "cylinder": _wedge_angle,
}


# --------------------------------------------------
# helper functions
# --------------------------------------------------
def _shock_angle_table(
    mach: float, gamma: float, nose_shape: str
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Sharp-body shock angle against body angle, from 0 to the largest attached angle.

    The table is built by sweeping the shock angle and solving for the body angle,
    which needs no root-finding and stays well-posed down to a body angle of zero
    (where the shock is the Mach wave).

    Returns:
        Body angles [deg] (increasing, starting at 0) and their shock angles [deg]
        (weak branch, starting at the Mach angle).
    """

    # shock angles, clustered just above the Mach angle
    mach_angle = math.degrees(math.asin(1.0 / mach))
    excess = np.geomspace(
        _TABLE_EXCESS_MIN, _TABLE_SHOCK_ANGLE_MAX - mach_angle, _TABLE_SIZE
    )
    shock_angles = mach_angle + excess

    # body angle behind each shock
    solve_body_angle = _BODY_ANGLE_SOLVERS[nose_shape]
    kept_shock = []
    kept_body = []
    for shock_angle in shock_angles:
        try:
            body_angle = solve_body_angle(mach, shock_angle, gamma)
        except RuntimeError:
            # the weakest shocks at high Mach sit on cones thinner than the
            # Taylor-Maccoll solver resolves; skip them, the table's (0, Mach angle)
            # entry covers them (the shock angle barely changes down there)
            if not kept_body:
                continue
            raise
        kept_shock.append(shock_angle)
        kept_body.append(body_angle)
    body_angles = np.array(kept_body)
    shock_angles = np.array(kept_shock)

    # keep the weak branch: up to the largest body angle (beyond it the shock detaches)
    i_max = int(np.argmax(body_angles))
    table_body = np.concatenate([[0.0], body_angles[: i_max + 1]])
    table_shock = np.concatenate([[mach_angle], shock_angles[: i_max + 1]])

    return table_body, table_shock


def _surface_angle_along_x(
    body: Body,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Surface angle [deg] of the body behind the nose, sampled against x.

    Interpolating in the result holds the end values, so the nose region (and the
    region ahead of the body) takes the angle where the nose ends.
    """

    # from the end of the nose to x_e (a single station if x_e lies on the nose)
    s_junction = float(body.profile.junctions[0])
    s_last = max(body.s_end, s_junction)
    s = np.linspace(s_junction, s_last, _DENSE_SIZE)

    # x and the surface angle at each station
    x, _ = body.profile.point(s)
    tx, ty = body.profile.tangent(s)
    surface_angle = np.degrees(np.arctan2(ty, tx))

    return x, surface_angle


def _integrate_billig(
    standoff_delta: float,
    shock_radius: float,
    station_x: NDArray[np.float64],
    station_tan_shock: NDArray[np.float64],
    x_e: float,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Integrate Billig's slope dx/dy from the vertex to x_e, with the local asymptote angle.

    Args:
        standoff_delta: Standoff distance; the vertex is at x = -delta.
        shock_radius: Shock radius of curvature at the vertex.
        station_x: Body stations (x).
        station_tan_shock: tan of the sharp-body shock angle at each station.
        x_e: Streamwise end.

    Returns:
        Dense shock points (x, y) from the vertex to x_e.
    """

    # Billig's slope, with the asymptote angle of the body station at the same x
    def slope(y: float, x: NDArray[np.float64]) -> list[float]:
        tan_shock = np.interp(x[0], station_x, station_tan_shock)
        ratio = y * tan_shock / shock_radius
        dx_dy = (y / shock_radius) / math.sqrt(1.0 + ratio**2)
        return [dx_dy]

    # stop where the shock reaches x_e
    def reaches_x_e(y: float, x: NDArray[np.float64]) -> float:
        return x[0] - x_e

    reaches_x_e.terminal = True
    reaches_x_e.direction = 1

    # bound on y: even the steepest asymptote angle reaches x_e by then
    tan_max = float(np.max(station_tan_shock))
    reach = 1.0 + (x_e + standoff_delta) * tan_max**2 / shock_radius
    y_bound = 1.01 * shock_radius / tan_max * math.sqrt(reach**2 - 1.0)

    # integrate from the vertex
    scale = x_e + standoff_delta
    solution = solve_ivp(
        slope,
        (0.0, y_bound),
        [-standoff_delta],
        events=reaches_x_e,
        rtol=1.0e-10,
        atol=1.0e-12 * scale,
        dense_output=True,
    )
    if solution.status != 1:
        raise RuntimeError(f"shock integration did not reach x_e: {solution.message}")
    y_end = float(solution.t_events[0][0])

    # dense samples, clustered at the vertex, with exact ends
    y = _dense_samples(y_end, shock_radius)
    x = solution.sol(y)[0]
    x[0] = -standoff_delta
    x[-1] = x_e

    return x, y


def _dense_samples(end: float, nose_scale: float) -> NDArray[np.float64]:
    """Dense samples from 0 to end, spaced geometrically from the nose scale down.

    Evenly spaced samples would put a small nose on a long body inside a single
    step; geometric spacing gives every length scale, from a fraction of the nose
    to the whole body, the same number of samples.

    Args:
        end: Last sample (arc length or y at x_e).
        nose_scale: Length of the nose region (nose radius or shock radius).

    Returns:
        Increasing samples, starting at 0 and ending exactly at end.
    """

    # first nonzero sample: a fraction of the nose, but never past the end
    first = min(_DENSE_FIRST_FRACTION * nose_scale, 0.5 * end)

    # geometric samples behind a sample at 0
    clustered = np.geomspace(first, end, _DENSE_SIZE - 1)
    samples = np.concatenate([[0.0], clustered])

    return samples


def _spacing_measure(
    x: NDArray[np.float64], y: NDArray[np.float64]
) -> NDArray[np.float64]:
    """Measure along a dense curve that weighs arc length and turning angle equally.

    Points equally spaced in this measure put half of them evenly along the length
    and half where the curve turns, so a small nose (or the shock vertex) is resolved
    on a long body.

    Returns:
        Cumulative measure at each dense point, from 0 to 1.
    """

    # arc length along the dense curve
    segment_lengths = np.hypot(np.diff(x), np.diff(y))
    arc = np.concatenate([[0.0], np.cumsum(segment_lengths)])

    # turning angle, counted at the point between two segments
    heading = np.unwrap(np.arctan2(np.diff(y), np.diff(x)))
    turning = np.zeros_like(arc)
    turning[1:-1] = np.cumsum(np.abs(np.diff(heading)))
    turning[-1] = turning[-2]

    # half each; arc length alone for a straight curve
    measure = arc / arc[-1]
    if turning[-1] > 0.0:
        measure = 0.5 * (arc / arc[-1] + turning / turning[-1])

    return measure


def _spread_points(
    x: NDArray[np.float64], y: NDArray[np.float64], n_points: int
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Points along a densely sampled curve, equally spaced in arc length and turning angle."""

    # equal steps in the measure
    measure = _spacing_measure(x, y)
    measure_out = np.linspace(0.0, 1.0, n_points)
    x_out = np.interp(measure_out, measure, x)
    y_out = np.interp(measure_out, measure, y)

    return x_out, y_out


def _blend(
    x: NDArray[np.float64],
    y_billig: NDArray[np.float64],
    sharp_x: NDArray[np.float64],
    sharp_y: NDArray[np.float64],
    nose_radius: float,
    blend_nose_radii: float,
) -> NDArray[np.float64]:
    """Blend Billig's shock into the sharp-body shock, at the same x.

    Args:
        x: Dense Billig shock x [m].
        y_billig: Dense Billig shock y [m].
        sharp_x: Sharp-body shock x [m], from the virtual origin.
        sharp_y: Sharp-body shock y [m].
        nose_radius: Nose radius [m].
        blend_nose_radii: Blend length L [nose radii].

    Returns:
        Blended shock y at the same x.
    """

    # sharp-body shock at Billig's stations (zero ahead of the virtual origin)
    y_sharp = np.interp(x, sharp_x, sharp_y, left=0.0)

    # weight: Billig at the nose (x <= 0), fading algebraically with x / R_n
    xi = np.maximum(x, 0.0) / nose_radius
    weight = 1.0 / (1.0 + xi / blend_nose_radii)

    # blend at the same x
    y_blended = weight * y_billig + (1.0 - weight) * y_sharp

    return y_blended


# --------------------------------------------------
# public API
# --------------------------------------------------
def compute_shock_shape(
    mach: float,
    gamma: float,
    geometry: GeometryConfig,
    x_e: float,
    n_points: int = 100,
    method: str = "billig",
    blend_nose_radii: float | None = None,
) -> ShockShapeResult:
    """Compute a detached bow-shock locus.

    The body nose tip is at ``x=0`` and the freestream points in the positive
    x direction. The shock vertex is therefore located at ``x=-delta``.

    Args:
        mach: Freestream Mach number.
        gamma: Specific heat ratio.
        geometry: Body geometry (see flow_theory.geometry.parse_geometry).
        x_e: Streamwise end of the shock and body [m].
        n_points: Number of points on the shock and on the body.
        method: Shock-shape correlation name: "billig", or "billig_blended"
            (wedges, cones and tangent ogives; see the module docstring).
        blend_nose_radii: billig_blended only: blend length L [nose radii]
            (default 35).

    Returns:
        Shock and body points and the standoff result used to place the shock.

    Raises:
        ValueError: If an input or selector is invalid, or the sharp-body shock
            would detach somewhere on the body.

    References:
        Billig (1967), "Shock-wave shapes around spherical- and cylindrical-nosed
        bodies", J. Spacecraft Rockets, 4(6), 822-823.
    """

    # normalize selectors
    method_name = str(method).strip().lower()

    # validate inputs
    if method_name not in SHOCK_SHAPE_METHODS:
        raise ValueError(
            f"method must be one of {SHOCK_SHAPE_METHODS}: got {method_name!r}"
        )
    if isinstance(n_points, bool) or not isinstance(n_points, int) or n_points < 2:
        raise ValueError(f"n_points must be an integer of at least 2: {n_points}")
    if blend_nose_radii is not None:
        if method_name != "billig_blended":
            raise ValueError("blend_nose_radii only applies to method 'billig_blended'")
        if not math.isfinite(blend_nose_radii) or blend_nose_radii <= 0.0:
            raise ValueError(f"blend_nose_radii must be positive: {blend_nose_radii}")

    # build the body up to x_e
    body = build_body(geometry, x_e)

    # check: billig_blended needs a sharp body behind the nose (a virtual origin)
    if method_name == "billig_blended":
        has_virtual_origin = body.geometry in _SHARP_BODY_TYPES
        if body.geometry in ("wedge", "cone"):
            has_virtual_origin = geometry.half_angle > 0.0
        if not has_virtual_origin:
            raise ValueError(
                "method 'billig_blended' needs a wedge or cone with half_angle > 0, or a "
                f"tangent ogive (a sharp body with a virtual origin): got {body.geometry}"
            )

    # compute the standoff distance used by the shock-shape correlation
    standoff = compute_shock_standoff(
        mach=mach,
        nose_radius=body.nose_radius,
        geometry=body.nose_shape,
        method="ambrosio_wortman",
        gamma=gamma,
    )

    # read Billig geometry constants for the shock radius relation
    radius_params = _BILLIG_RC_PARAMS[body.nose_shape]
    radius_coefficient = radius_params["coefficient"]
    exponent_coefficient = radius_params["exponent_coefficient"]
    exponent_power = radius_params["exponent_power"]

    # compute Billig's shock radius of curvature at the nose
    shock_radius = (
        radius_coefficient
        * math.exp(exponent_coefficient / (mach - 1.0) ** exponent_power)
        * body.nose_radius
    )

    # sharp-body shock angle for every surface angle the body has
    table_body, table_shock = _shock_angle_table(mach, gamma, body.nose_shape)
    station_x, surface_angle = _surface_angle_along_x(body)

    # check: the sharp-body shock stays attached everywhere
    steepest = float(np.max(surface_angle))
    if steepest > table_body[-1]:
        raise ValueError(
            f"the surface angle reaches {steepest:.2f} deg, past the largest angle with an "
            f"attached shock at M = {mach} ({table_body[-1]:.2f} deg)"
        )

    # asymptote angle at each body station
    station_shock = np.interp(surface_angle, table_body, table_shock)
    station_tan_shock = np.tan(np.radians(station_shock))

    # billig_blended: Billig's asymptote is the sharp body's tip shock, the same at every
    # station (the sharp-body shock takes over the body's shape downstream)
    if method_name == "billig_blended":
        # the sharp body behind the nose, from its tip (virtual origin) to x_e
        sharp_x, sharp_r = geometry.build().sharp_profile(x_e, _SHARP_BODY_SIZE)
        tip_angle = math.degrees(
            math.atan2(sharp_r[1] - sharp_r[0], sharp_x[1] - sharp_x[0])
        )
        if tip_angle > table_body[-1]:
            raise ValueError(
                f"the sharp body's tip angle is {tip_angle:.2f} deg, past the largest angle "
                f"with an attached shock at M = {mach} ({table_body[-1]:.2f} deg)"
            )
        tip_shock = float(np.interp(tip_angle, table_body, table_shock))
        station_tan_shock = np.full_like(
            station_tan_shock, math.tan(math.radians(tip_shock))
        )

    # integrate the shock from the vertex to x_e, then spread its points
    x_dense, y_dense = _integrate_billig(
        standoff_delta=standoff.delta,
        shock_radius=shock_radius,
        station_x=station_x,
        station_tan_shock=station_tan_shock,
        x_e=x_e,
    )

    # billig_blended: fade into the sharp-body shock from the virtual origin
    if method_name == "billig_blended":
        if blend_nose_radii is None:
            blend_nose_radii = _DEFAULT_BLEND_NOSE_RADII

        # sharp-body shock by the method of characteristics
        sharp = solve_sharp_body(
            mach,
            sharp_x,
            sharp_r,
            x_end=x_e,
            gamma=gamma,
            axisymmetric=body.axisymmetric,
        )

        # blend
        y_dense = _blend(
            x=x_dense,
            y_billig=y_dense,
            sharp_x=sharp.shock_x,
            sharp_y=sharp.shock_y,
            nose_radius=body.nose_radius,
            blend_nose_radii=blend_nose_radii,
        )

    x, y = _spread_points(x_dense, y_dense, n_points)

    # body points from the stagnation point to x_e, spread the same way (exact points)
    s_dense = _dense_samples(body.s_end, body.nose_radius)
    x_body_dense, y_body_dense = body.profile.point(s_dense)
    measure = _spacing_measure(x_body_dense, y_body_dense)
    s_body = np.interp(np.linspace(0.0, 1.0, n_points), measure, s_dense)
    body_x, body_y = body.profile.point(s_body)

    result = ShockShapeResult(
        x=x,
        y=y,
        body_x=np.asarray(body_x, dtype=float),
        body_y=np.asarray(body_y, dtype=float),
        standoff=standoff,
        geometry=body.geometry,
        method=method_name,
        x_e=float(x_e),
        shock_radius=shock_radius,
    )

    return result
