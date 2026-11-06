"""Tests for bodies built from canonical-geometries [geometry] tables."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

import pytest

from flow_theory.geometry import body_end, build_body, parse_geometry, resolve_x_e

# a tangent ogive whose base lies near x = 0.25
OGIVE_TABLE = {"type": "tangent-ogive", "nose_radius": 0.002, "length": 0.25, "base_radius": 0.03}


# --------------------------------------------------
# parse_geometry
# --------------------------------------------------
@pytest.mark.parametrize(
    "table",
    [
        {"type": "plate", "nose_radius": 0.01, "length": 0.2},
        {"type": "wedge", "nose_radius": 0.01, "length": 0.2, "half_angle": 10.0},
        {"type": "cone", "nose_radius": 0.01, "length": 0.2, "half_angle": 7.0},
    ],
)
def test_parse_keeps_the_length_of_the_table(table: dict) -> None:
    """Plate, wedge and cone keep the length their table gives: the body is never stretched."""

    # parse
    geometry = parse_geometry(table)

    # check
    assert geometry.length == 0.2
    assert body_end(geometry) == pytest.approx(0.2, rel=1.0e-14)


def test_parse_rejects_unknown_types_and_keys() -> None:
    """Unsupported types list the supported ones; misspelled keys fail validation."""

    # check
    with pytest.raises(ValueError, match="plate, wedge, cone, tangent-ogive"):
        parse_geometry({"type": "sphere", "nose_radius": 0.01, "length": 0.2})
    with pytest.raises(ValueError, match="half_angel"):
        parse_geometry(
            {"type": "cone", "nose_radius": 0.01, "length": 0.2, "half_angel": 7.0}
        )


# --------------------------------------------------
# resolve_x_e
# --------------------------------------------------
def test_resolve_x_e_defaults_to_the_body_end() -> None:
    """Left out, x_e is where the body ends."""

    # a cone 0.2 m long
    geometry = parse_geometry(
        {"type": "cone", "nose_radius": 0.01, "length": 0.2, "half_angle": 7.0}
    )

    # check: the body's end, and a given x_e on the body as it is
    assert resolve_x_e(geometry, None) == body_end(geometry)
    assert resolve_x_e(geometry, 0.1) == 0.1


def test_resolve_x_e_refuses_an_end_past_the_body() -> None:
    """x_e past the body's end is refused, naming where the body came from."""

    # a cone 0.2 m long
    geometry = parse_geometry(
        {"type": "cone", "nose_radius": 0.01, "length": 0.2, "half_angle": 7.0}
    )

    # check: the message names the file and both ends
    with pytest.raises(ValueError, match=r"x_e = 0\.3 m lies past the end") as raised:
        resolve_x_e(geometry, 0.3, source="geometry.toml")
    assert "geometry.toml (x = 0.2 m)" in str(raised.value)
    assert "lengthen the body in geometry.toml" in str(raised.value)


# --------------------------------------------------
# build_body
# --------------------------------------------------
@pytest.mark.parametrize(
    ("geometry_type", "nose_shape", "axisymmetric"),
    [("plate", "cylinder", False), ("cone", "sphere", True)],
)
def test_build_body_picks_the_nose_shape(
    geometry_type: str, nose_shape: str, axisymmetric: bool
) -> None:
    """Planar bodies get a cylindrical nose, axisymmetric bodies a spherical one."""

    # build
    table = {"type": geometry_type, "nose_radius": 0.01, "length": 0.2}
    if geometry_type == "cone":
        table["half_angle"] = 7.0
    body = build_body(parse_geometry(table), 0.2)

    # check
    assert body.nose_shape == nose_shape
    assert body.axisymmetric is axisymmetric
    assert body.nose_radius == 0.01


def test_build_body_takes_the_ogive_cylinder_from_the_geometry() -> None:
    """A cylinder behind the ogive comes from cylinder_length; x_e can lie on it."""

    # an ogive with a cylinder from its base (near x = 0.25) past x = 0.4
    geometry = parse_geometry(OGIVE_TABLE | {"cylinder_length": 0.2})
    body = build_body(geometry, 0.4)

    # check: x_e lies on the cylinder, at the base radius
    x_end, y_end = body.profile.point(body.s_end)
    assert body.s_end < body.profile.total_length
    assert float(x_end) == pytest.approx(0.4, abs=1.0e-12)
    assert float(y_end) == pytest.approx(0.03)


def test_build_body_refuses_x_e_past_the_ogive() -> None:
    """Without a cylinder, x_e past the ogive's base is refused: the body isn't lengthened."""

    # check
    with pytest.raises(ValueError, match="lies past the end of the body"):
        build_body(parse_geometry(OGIVE_TABLE), 0.4)


def test_build_body_stops_on_the_ogive() -> None:
    """An x_e ahead of the base ends the body there, without a cylinder."""

    # build
    body = build_body(parse_geometry(OGIVE_TABLE), 0.1)

    # check: s_end lies inside the profile, at x_e
    x_end, _ = body.profile.point(body.s_end)
    assert body.s_end < body.profile.total_length
    assert float(x_end) == pytest.approx(0.1, abs=1.0e-12)
