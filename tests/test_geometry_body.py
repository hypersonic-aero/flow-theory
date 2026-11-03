"""Tests for bodies built from canonical-geometries [geometry] tables."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

import pytest

from flow_theory.geometry import build_body, parse_geometry

# a tangent ogive whose base lies near x = 0.25
OGIVE_TABLE = {"type": "tangent-ogive", "nose_radius": 0.002, "length": 0.25, "base_radius": 0.03}


# --------------------------------------------------
# parse_geometry
# --------------------------------------------------
@pytest.mark.parametrize(
    "table",
    [
        {"type": "plate", "nose_radius": 0.01},
        {"type": "wedge", "nose_radius": 0.01, "half_angle": 10.0},
        {"type": "cone", "nose_radius": 0.01, "half_angle": 7.0},
    ],
)
def test_parse_fills_length_from_x_e(table: dict) -> None:
    """Plate, wedge and cone take their length from x_e."""

    # parse
    geometry = parse_geometry(table, 0.2)

    # check
    assert geometry.length == 0.2


@pytest.mark.parametrize(
    ("table", "key"),
    [
        ({"type": "cone", "nose_radius": 0.01, "half_angle": 7.0, "length": 0.2}, "length"),
        (OGIVE_TABLE | {"cylinder_length": 0.1}, "cylinder_length"),
    ],
)
def test_parse_rejects_the_extent_key(table: dict, key: str) -> None:
    """The key that only sets the body's extent is an error: x_e sets it."""

    # check
    with pytest.raises(ValueError, match=f"{key} isn't used"):
        parse_geometry(table, 0.2, label="shock_shape.geometry")


def test_parse_rejects_unknown_types_and_keys() -> None:
    """Unsupported types list the supported ones; misspelled keys fail validation."""

    # check
    with pytest.raises(ValueError, match="plate, wedge, cone, tangent-ogive"):
        parse_geometry({"type": "sphere", "nose_radius": 0.01}, 0.2)
    with pytest.raises(ValueError, match="half_angel"):
        parse_geometry({"type": "cone", "nose_radius": 0.01, "half_angel": 7.0}, 0.2)


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
    table = {"type": geometry_type, "nose_radius": 0.01}
    if geometry_type == "cone":
        table["half_angle"] = 7.0
    body = build_body(parse_geometry(table, 0.2), 0.2)

    # check
    assert body.nose_shape == nose_shape
    assert body.axisymmetric is axisymmetric
    assert body.nose_radius == 0.01


def test_build_body_extends_the_ogive_with_a_cylinder() -> None:
    """An x_e past the ogive base adds a cylinder that ends at x_e."""

    # build
    body = build_body(parse_geometry(OGIVE_TABLE, 0.4), 0.4)

    # check: the profile ends at x_e, at the base radius
    x_end, y_end = body.profile.point(body.s_end)
    assert body.s_end == pytest.approx(body.profile.total_length)
    assert float(x_end) == pytest.approx(0.4)
    assert float(y_end) == pytest.approx(0.03)


def test_build_body_stops_on_the_ogive() -> None:
    """An x_e ahead of the base ends the body there, without a cylinder."""

    # build
    body = build_body(parse_geometry(OGIVE_TABLE, 0.1), 0.1)

    # check: s_end lies inside the profile, at x_e
    x_end, _ = body.profile.point(body.s_end)
    assert body.s_end < body.profile.total_length
    assert float(x_end) == pytest.approx(0.1, abs=1.0e-12)
