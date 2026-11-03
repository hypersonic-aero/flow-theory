"""Tests for boundary-layer thickness correlations."""

from pathlib import Path

import pytest
import typer

from flow_theory.boundary_layer import compute_boundary_layer_thickness
from flow_theory.cli.cmd_boundary_layer_thickness import cmd_boundary_layer_thickness
from flow_theory.config import BoundaryLayerThicknessConfig
from flow_theory.entropy_layer import swallowing_distance


def test_blasius_thicknesses_match_profile_constants() -> None:
    result = compute_boundary_layer_thickness(
        x=1.0,
        re1=1.0e6,
        method="blasius",
    )

    assert result.re_x == pytest.approx(1.0e6)
    assert result.delta_99 == pytest.approx(5.0e-3)
    assert result.displacement_thickness == pytest.approx(1.7208e-3)
    assert result.momentum_thickness == pytest.approx(0.664e-3)


def test_eckert_reference_requires_thermal_inputs() -> None:
    with pytest.raises(ValueError, match="mach is required"):
        compute_boundary_layer_thickness(
            x=1.0,
            re1=1.0e6,
            method="eckert_reference",
        )


def test_eckert_reference_does_not_infer_integral_thicknesses() -> None:
    result = compute_boundary_layer_thickness(
        x=1.0,
        re1=1.0e6,
        method="eckert_reference",
        mach=8.0,
        tw_t0=0.4,
    )

    assert result.delta_99 > 0.0
    assert result.displacement_thickness is None
    assert result.momentum_thickness is None


def test_entropy_swallowing_preserves_reference_temperature_result() -> None:
    distance = swallowing_distance(
        r_nose=0.0254,
        re1=3.0e6,
        mach=8.0,
        tw_t0=0.4,
    )

    assert distance == pytest.approx(0.6656732, rel=1.0e-6)


def test_parse_boundary_layer_thickness_config() -> None:
    config = BoundaryLayerThicknessConfig.from_dict(
        {
            "x": [0.1, 1.0],
            "re1": 3.0e6,
            "method": "eckert_reference",
            "mach": 8.0,
            "tw_t0": 0.4,
        }
    )

    assert isinstance(config, BoundaryLayerThicknessConfig)
    assert config.method == "eckert_reference"
    assert config.mach == 8.0


def test_run_command_executes_boundary_layer_thickness_section(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "boundary_layer_thickness.dat"
    config_path = tmp_path / "flow_theory.toml"
    config_text = f"""
[boundary_layer_thickness]
x = [0.1, 1.0]
re1 = 1.0e6
method = "blasius"
output = "{output_path}"
"""
    config_path.write_text(config_text, encoding="utf-8")

    try:
        cmd_boundary_layer_thickness(config=config_path)
    except typer.Exit as error:
        pytest.fail(f"flow-theory bl run exited unexpectedly: {error}")

    output_text = output_path.read_text(encoding="utf-8")
    assert 'ZONE T="boundary-layer thickness blasius", I=2' in output_text
