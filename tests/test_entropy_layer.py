"""Tests for entropy-layer estimates and swallowing calculations."""

from pathlib import Path

import pytest
import typer

from flow_theory.cli.cmd_entropy_layer_estimate import cmd_entropy_layer_estimate
from flow_theory.cli.cmd_entropy_layer_swallowing import cmd_entropy_layer_swallowing
from flow_theory.config import (
    EntropyLayerEstimateConfig,
    EntropyLayerSwallowingConfig,
)
from flow_theory.entropy_layer import (
    entropy_layer_thickness,
    is_swallowed,
    swallowing_distance,
)


def test_entropy_layer_thickness_is_zero_at_nose() -> None:
    thickness = entropy_layer_thickness(
        x=0.0,
        r_nose=1.0,
        mach=10.0,
    )

    assert thickness == 0.0


def test_entropy_layer_thickness_matches_classical_scaling() -> None:
    thickness = entropy_layer_thickness(
        x=8.0,
        r_nose=1.0,
        mach=10.0,
        gamma=1.4,
    )

    density_ratio = ((1.4 - 1.0) * 10.0**2 + 2.0) / ((1.4 + 1.0) * 10.0**2)
    expected = 1.0 * 8.0 ** (1.0 / 3.0) * density_ratio

    assert thickness == pytest.approx(expected)


def test_swallowing_distance_separates_unswallowed_and_swallowed_regions() -> None:
    inputs = {
        "r_nose": 0.0254,
        "re1": 3.0e6,
        "mach": 8.0,
        "tw_t0": 0.4,
    }

    distance = swallowing_distance(**inputs)
    before_crossing = is_swallowed(x=0.99 * distance, **inputs)
    after_crossing = is_swallowed(x=1.01 * distance, **inputs)

    assert distance > 0.0
    assert before_crossing is False
    assert after_crossing is True


def test_parse_entropy_layer_workflow_configs() -> None:
    estimate = EntropyLayerEstimateConfig.from_dict(
        {
            "x": 0.1,
            "mach": 8.0,
            "nose_radius": 0.0254,
        }
    )
    swallowing = EntropyLayerSwallowingConfig.from_dict(
        {
            "mach": 8.0,
            "re1": 3.0e6,
            "nose_radius": 0.0254,
            "tw_t0": 0.4,
        }
    )

    assert isinstance(estimate, EntropyLayerEstimateConfig)
    assert estimate.x == 0.1
    assert isinstance(swallowing, EntropyLayerSwallowingConfig)
    assert swallowing.re1 == 3.0e6


def test_run_commands_execute_their_own_entropy_layer_section(tmp_path: Path) -> None:
    """One config file can hold both sections; each run command reads its own."""
    estimate_path = tmp_path / "entropy_estimate.dat"
    swallowing_path = tmp_path / "entropy_swallowing.dat"
    config_path = tmp_path / "flow_theory.toml"
    config_text = f"""
[entropy_layer_estimate]
x = [0.1, 0.2]
mach = 8.0
nose_radius = 0.0254
output = "{estimate_path}"

[entropy_layer_swallowing]
mach = 8.0
re1 = 3.0e6
nose_radius = 0.0254
tw_t0 = 0.4
output = "{swallowing_path}"
"""
    config_path.write_text(config_text, encoding="utf-8")

    try:
        cmd_entropy_layer_estimate(config=config_path)
        cmd_entropy_layer_swallowing(config=config_path)
    except typer.Exit as error:
        pytest.fail(f"entropy-layer run exited unexpectedly: {error}")

    estimate_text = estimate_path.read_text(encoding="utf-8")
    swallowing_text = swallowing_path.read_text(encoding="utf-8")

    assert 'ZONE T="entropy-layer estimate", I=2' in estimate_text
    assert 'ZONE T="entropy-layer swallowing distance", I=1' in swallowing_text
