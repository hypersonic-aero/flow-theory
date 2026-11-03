"""Tests for shock-standoff and shock-shape estimates."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

import math

import numpy as np
import pytest
from gasdyn import solve_oblique, solve_taylor_maccoll

from flow_theory.geometry import parse_geometry
from flow_theory.shock import compute_shock_shape, compute_shock_standoff


# --------------------------------------------------
# shock-standoff tests
# --------------------------------------------------
def test_sphere_standoff_matches_ambrosio_wortman_air_correlation() -> None:
    """The sphere result should reproduce the published air fit."""

    # evaluate a representative supersonic condition
    result = compute_shock_standoff(
        mach=6.0,
        nose_radius=0.01,
    )

    # independently evaluate the non-dimensional relation
    expected_ratio = 0.143 * math.exp(3.24 / 6.0**2)

    # check dimensional and non-dimensional results
    assert result.delta_over_radius == pytest.approx(expected_ratio)
    assert result.delta == pytest.approx(expected_ratio * 0.01)
    assert result.geometry == "sphere"
    assert result.method == "ambrosio_wortman"


def test_cylinder_standoff_matches_ambrosio_wortman_air_correlation() -> None:
    """The cylinder result should reproduce the published air fit."""

    # evaluate a representative supersonic condition
    result = compute_shock_standoff(
        mach=6.0,
        nose_radius=0.01,
        geometry="cylinder",
    )

    # independently evaluate the non-dimensional relation
    expected_ratio = 0.386 * math.exp(4.67 / 6.0**2)

    # check dimensional and non-dimensional results
    assert result.delta_over_radius == pytest.approx(expected_ratio)
    assert result.delta == pytest.approx(expected_ratio * 0.01)
    assert result.geometry == "cylinder"


@pytest.mark.parametrize(
    ("geometry", "coefficient", "exponent"),
    [
        ("sphere", 0.52, -0.861),
        ("cylinder", 2.52, -1.25),
    ],
)
def test_ambrosio_wortman_density_ratio_correlation(
    geometry: str,
    coefficient: float,
    exponent: float,
) -> None:
    """The density-ratio method should reproduce Eqs. (2) and (3)."""

    # evaluate the correlation through the public API
    result = compute_shock_standoff(
        mach=6.0,
        gamma=1.4,
        nose_radius=0.01,
        geometry=geometry,
        method="ambrosio_wortman_density_ratio",
    )

    # independently compute the perfect-gas normal-shock density ratio
    density_ratio = (2.4 * 6.0**2) / (0.4 * 6.0**2 + 2.0)
    expected_ratio = coefficient * (density_ratio - 1.0) ** exponent

    # check the selected geometry correlation
    assert result.delta_over_radius == pytest.approx(expected_ratio)
    assert result.gamma == 1.4


def test_serbin_sphere_standoff_matches_density_ratio_relation() -> None:
    """The Serbin method should reproduce its published sphere relation."""

    # evaluate the sphere correlation through the public API
    result = compute_shock_standoff(
        mach=6.0,
        gamma=1.4,
        nose_radius=0.01,
        method="serbin",
    )

    # independently evaluate Serbin's density-ratio relation
    density_ratio = (2.4 * 6.0**2) / (0.4 * 6.0**2 + 2.0)
    expected_ratio = (2.0 / 3.0) * (density_ratio - 1.0) ** -1.0

    # check the non-dimensional result
    assert result.delta_over_radius == pytest.approx(expected_ratio)
    assert result.method == "serbin"


def test_serbin_rejects_cylinder_at_public_boundary() -> None:
    """The public API should reject the unsupported Serbin cylinder pairing."""

    # check method-specific geometry validation
    with pytest.raises(ValueError, match="does not support geometry 'cylinder'"):
        compute_shock_standoff(
            mach=6.0,
            gamma=1.4,
            nose_radius=0.01,
            geometry="cylinder",
            method="serbin",
        )


def test_density_ratio_method_requires_gamma() -> None:
    """Density-ratio methods should require a specific heat ratio."""

    # check method-specific input validation
    with pytest.raises(ValueError, match="gamma is required"):
        compute_shock_standoff(
            mach=6.0,
            nose_radius=0.01,
            method="serbin",
        )


def test_standoff_rejects_unsupported_geometry() -> None:
    """The standoff method should reject unsupported nose geometries."""

    # check
    with pytest.raises(ValueError, match="geometry must be one of"):
        compute_shock_standoff(
            mach=6.0,
            nose_radius=0.01,
            geometry="blunt_cone",
        )


# --------------------------------------------------
# shock-shape tests
# --------------------------------------------------
# one body per geometry type, all ending at the same x_e
SHAPE_X_E = 0.3
SHAPE_GEOMETRIES = {
    "plate": {"type": "plate", "nose_radius": 0.01},
    "wedge": {"type": "wedge", "nose_radius": 0.01, "half_angle": 10.0},
    "cone": {"type": "cone", "nose_radius": 0.01, "half_angle": 7.0},
    "tangent-ogive": {
        "type": "tangent-ogive",
        "nose_radius": 0.002,
        "length": 0.25,
        "base_radius": 0.03,
    },
}


def billig_hyperbola_x(y, result, shock_angle: float):
    """Billig's closed-form hyperbola x(y) with a constant asymptote angle [deg]."""

    # Billig (1967) in nose-tip coordinates
    tan_shock = math.tan(math.radians(shock_angle))
    radius = result.shock_radius
    x = -result.standoff.delta + radius / tan_shock**2 * (
        np.sqrt(1.0 + (y * tan_shock / radius) ** 2) - 1.0
    )

    return x


@pytest.mark.parametrize("geometry_type", list(SHAPE_GEOMETRIES))
def test_shock_shape_runs_from_the_vertex_to_x_e(geometry_type: str) -> None:
    """The shock starts at the standoff vertex, ends at x_e, and lies outside the body."""

    # compute
    geometry = parse_geometry(SHAPE_GEOMETRIES[geometry_type], SHAPE_X_E)
    result = compute_shock_shape(6.0, 1.4, geometry, SHAPE_X_E, n_points=200)

    # check the shock: vertex, end, monotonic in x
    assert result.x.shape == (200,)
    assert (result.x[0], result.y[0]) == (pytest.approx(-result.standoff.delta), 0.0)
    assert result.x[-1] == pytest.approx(SHAPE_X_E)
    assert np.all(np.diff(result.x) > 0.0)

    # check the body: stagnation point to x_e
    assert (result.body_x[0], result.body_y[0]) == (
        pytest.approx(0.0),
        pytest.approx(0.0),
    )
    assert result.body_x[-1] == pytest.approx(SHAPE_X_E)

    # check: the shock lies above the body everywhere
    shock_y_at_body = np.interp(result.body_x, result.x, result.y)
    assert np.all(shock_y_at_body[1:] > result.body_y[1:])


def test_shock_shape_matches_billig_worked_point() -> None:
    """The sampled locus should reproduce Billig's reported sphere point."""

    # compute the worked Mach 19.25 case (a sphere-cylinder) in the nose-tip frame
    geometry = parse_geometry(
        {"type": "cone", "nose_radius": 1.0, "half_angle": 0.0}, 1.8
    )
    result = compute_shock_shape(19.25, 1.4, geometry, 1.8, n_points=2000)

    # Billig's x=0 is the sphere center, which is x=R in this package
    y_at_sphere_center = np.interp(1.0, result.x, result.y)

    # check against the three-significant-figure value reported by Billig
    assert y_at_sphere_center == pytest.approx(1.64, rel=5.0e-3)


@pytest.mark.parametrize(
    ("geometry_type", "shock_angle"),
    [
        ("plate", math.degrees(math.asin(1.0 / 6.0))),
        ("wedge", solve_oblique(mach=6.0, deflection_angle=10.0).shock_angle),
        ("cone", solve_taylor_maccoll(mach=6.0, cone_angle=7.0).shock_angle),
    ],
)
def test_straight_bodies_give_billigs_hyperbola(
    geometry_type: str, shock_angle: float
) -> None:
    """With a constant surface angle, the shock is Billig's hyperbola with the sharp-body angle."""

    # compute
    geometry = parse_geometry(SHAPE_GEOMETRIES[geometry_type], SHAPE_X_E)
    result = compute_shock_shape(6.0, 1.4, geometry, SHAPE_X_E, n_points=400)

    # check against the closed form (to the shock-angle table's interpolation error)
    expected_x = billig_hyperbola_x(result.y, result, shock_angle)
    assert np.max(np.abs(result.x - expected_x)) < 1.0e-4 * SHAPE_X_E


def test_planar_and_axisymmetric_bodies_use_their_own_correlations() -> None:
    """A wedge (cylinder nose) and a cone (sphere nose) of the same angle differ."""

    # compute both
    wedge_table = {"type": "wedge", "nose_radius": 0.01, "half_angle": 7.0}
    wedge = compute_shock_shape(6.0, 1.4, parse_geometry(wedge_table, 0.1), 0.1)
    cone = compute_shock_shape(
        6.0, 1.4, parse_geometry(SHAPE_GEOMETRIES["cone"], 0.1), 0.1
    )

    # check: the cylinder nose stands the shock off further, and the wedge shock is steeper
    assert wedge.standoff.delta > cone.standoff.delta
    assert wedge.y[-1] > cone.y[-1]


def test_ogive_shock_follows_the_surface_angle() -> None:
    """The ogive shock bends from the nose-end hyperbola toward the Mach-angle hyperbola."""

    # compute an ogive ending on its cylinder
    geometry = parse_geometry(SHAPE_GEOMETRIES["tangent-ogive"], SHAPE_X_E)
    result = compute_shock_shape(6.0, 1.4, geometry, SHAPE_X_E, n_points=400)

    # the two bounding hyperbolas: the cone angle where the nose ends, and the Mach angle
    ogive = geometry.build()
    nose_end_angle = math.degrees(ogive.tangency_angle)
    steepest = solve_taylor_maccoll(mach=6.0, cone_angle=nose_end_angle).shock_angle
    flattest = math.degrees(math.asin(1.0 / 6.0))
    x_steepest = billig_hyperbola_x(result.y, result, steepest)
    x_flattest = billig_hyperbola_x(result.y, result, flattest)

    # check: on the steepest hyperbola ahead of the nose's end, between the two after it
    x_nose_end, _ = ogive.junction_point
    ahead = result.x < x_nose_end
    behind = result.x > 2.0 * x_nose_end
    np.testing.assert_allclose(
        result.x[ahead], x_steepest[ahead], atol=1.0e-4 * SHAPE_X_E
    )
    assert np.all(result.x[behind] > x_steepest[behind])
    assert np.all(result.x[behind] < x_flattest[behind])


@pytest.mark.parametrize("mach", [30.0, 50.0])
def test_shock_shape_runs_at_very_high_mach(mach: float) -> None:
    """The weakest table shocks, on cones too thin to solve, don't stop the calculation."""

    # compute an ogive (surface angles down to 0) at very high Mach
    geometry = parse_geometry(SHAPE_GEOMETRIES["tangent-ogive"], SHAPE_X_E)
    result = compute_shock_shape(mach, 1.4, geometry, SHAPE_X_E)

    # check
    assert result.x[-1] == pytest.approx(SHAPE_X_E)
    assert np.all(np.isfinite(result.y))


@pytest.mark.parametrize("nose_radius", [1.0e-3, 1.0e-6])
def test_small_noses_are_resolved(nose_radius: float) -> None:
    """A nose a million times smaller than the body still gets smooth shock and body points."""

    # compute a 1 m cone
    table = {"type": "cone", "nose_radius": nose_radius, "half_angle": 7.0}
    result = compute_shock_shape(
        6.0, 1.4, parse_geometry(table, 1.0), 1.0, n_points=201
    )

    # turning angle between neighboring segments [deg]
    shock_heading = np.arctan2(np.diff(result.y), np.diff(result.x))
    body_heading = np.arctan2(np.diff(result.body_y), np.diff(result.body_x))
    shock_turning = np.degrees(np.abs(np.diff(shock_heading)))
    body_turning = np.degrees(np.abs(np.diff(body_heading)))

    # check: no kinks at the vertex or the stagnation point
    assert shock_turning.max() < 2.0
    assert body_turning.max() < 2.0


def test_shock_shape_rejects_a_detached_sharp_body_shock() -> None:
    """A wedge steeper than the largest attached angle fails with a clear message."""

    # check
    geometry = parse_geometry(
        {"type": "wedge", "nose_radius": 0.01, "half_angle": 50.0}, 0.1
    )
    with pytest.raises(ValueError, match="attached shock"):
        compute_shock_shape(6.0, 1.4, geometry, 0.1)


def test_shock_shape_rejects_bad_selectors() -> None:
    """Unknown methods and too few points fail."""

    # check
    geometry = parse_geometry(SHAPE_GEOMETRIES["cone"], 0.1)
    with pytest.raises(ValueError, match="method must be one of"):
        compute_shock_shape(6.0, 1.4, geometry, 0.1, method="hyperbola")
    with pytest.raises(ValueError, match="n_points"):
        compute_shock_shape(6.0, 1.4, geometry, 0.1, n_points=1)


# --------------------------------------------------
# billig_blended
# --------------------------------------------------
def test_billig_blended_fades_from_billig_to_the_virtual_origin_shock() -> None:
    """The blend is Billig at the nose and the virtual-origin sharp-cone shock far downstream."""

    # compute both methods on a long cone (x_e = 2000 nose radii)
    nose_radius, half_angle, x_e = 0.001, 7.0, 2.0
    geometry = parse_geometry(
        {"type": "cone", "nose_radius": nose_radius, "half_angle": half_angle}, x_e
    )
    billig = compute_shock_shape(6.0, 1.4, geometry, x_e, n_points=4000)
    blended = compute_shock_shape(
        6.0,
        1.4,
        geometry,
        x_e,
        n_points=4000,
        method="billig_blended",
        blend_nose_radii=30.0,
    )

    # the virtual-origin sharp-cone shock
    shock_angle = solve_taylor_maccoll(mach=6.0, cone_angle=half_angle).shock_angle
    x_virtual = nose_radius * (1.0 - 1.0 / math.sin(math.radians(half_angle)))

    # check the blend formula at stations from the nose to the end
    for x in (0.0, 0.01, 0.1, 1.0, 2.0):
        y_billig = np.interp(x, billig.x, billig.y)
        y_virtual = (x - x_virtual) * math.tan(math.radians(shock_angle))
        weight = 1.0 / (1.0 + (x / nose_radius) / 30.0)
        expected = weight * y_billig + (1.0 - weight) * y_virtual
        assert np.interp(x, blended.x, blended.y) == pytest.approx(
            expected, rel=1.0e-4, abs=2.0e-5
        )

    # check: same vertex, and the shock stays ahead of the body
    assert blended.x[0] == pytest.approx(billig.x[0])
    assert np.all(
        np.interp(blended.body_x, blended.x, blended.y)[1:] > blended.body_y[1:]
    )


@pytest.mark.parametrize(
    "table",
    [
        {"type": "plate", "nose_radius": 0.01},
        {"type": "cone", "nose_radius": 0.01, "half_angle": 0.0},
        {
            "type": "tangent-ogive",
            "nose_radius": 0.002,
            "length": 0.25,
            "base_radius": 0.03,
        },
    ],
)
def test_billig_blended_needs_a_straight_surface(table: dict) -> None:
    """Bodies without a virtual origin (no straight, inclined surface) are rejected."""

    # check
    geometry = parse_geometry(table, SHAPE_X_E)
    with pytest.raises(ValueError, match="virtual origin"):
        compute_shock_shape(6.0, 1.4, geometry, SHAPE_X_E, method="billig_blended")


def test_blend_length_only_applies_to_billig_blended() -> None:
    """A blend length with method billig is an error, not silently ignored."""

    # check
    geometry = parse_geometry(SHAPE_GEOMETRIES["cone"], SHAPE_X_E)
    with pytest.raises(ValueError, match="only applies"):
        compute_shock_shape(6.0, 1.4, geometry, SHAPE_X_E, blend_nose_radii=30.0)
