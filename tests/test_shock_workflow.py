"""Tests for config-driven shock workflows."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

import importlib
from pathlib import Path

import pytest
import typer
from flow_state.gas import PerfectGas
from flow_state.io import write_json
from flow_state.solvers import solve

from flow_theory.cli.cmd_shock_shape import cmd_shock_shape
from flow_theory.cli.cmd_shock_standoff import cmd_shock_standoff
from flow_theory.config import ShockShapeConfig, ShockStandoffConfig
from flow_theory.geometry import parse_geometry
from flow_theory.runners import run_shock_shape, run_shock_standoff

run_shock_shape_module = importlib.import_module("flow_theory.runners.run_shock_shape")
run_shock_standoff_module = importlib.import_module(
    "flow_theory.runners.run_shock_standoff"
)


# --------------------------------------------------
# configuration tests
# --------------------------------------------------
def test_parse_shock_workflow_configs() -> None:
    """Each workflow section should produce its own typed configuration."""

    # parse representative sections
    standoff = ShockStandoffConfig.from_dict(
        {
            "flow_conditions": "flow.json",
            "geometry": "cylinder",
            "nose_radius": 0.01,
        }
    )
    shape = ShockShapeConfig.from_dict(
        {
            "flow_conditions": "flow.json",
            "n_points": 51,
            "x_e": 0.05,
            "geometry": {"type": "cone", "nose_radius": 0.01, "half_angle": 7.0},
        }
    )

    # check independent workflow contracts
    assert isinstance(standoff, ShockStandoffConfig)
    assert standoff.geometry == "cylinder"
    assert isinstance(shape, ShockShapeConfig)
    assert shape.n_points == 51
    assert shape.x_e == 0.05
    assert shape.geometry.type == "cone"
    assert shape.geometry.length == 0.05


# --------------------------------------------------
# FlowState handoff tests
# --------------------------------------------------
def standoff_config(flow_state_path: Path) -> ShockStandoffConfig:
    """Standoff config for a 1 cm nose."""
    return ShockStandoffConfig(flow_conditions=flow_state_path, nose_radius=0.01)


def shape_config(flow_state_path: Path) -> ShockShapeConfig:
    """Shape config for a cone with a 1 cm nose."""
    geometry = parse_geometry({"type": "cone", "nose_radius": 0.01, "half_angle": 7.0}, 0.05)
    return ShockShapeConfig(flow_conditions=flow_state_path, geometry=geometry, x_e=0.05)


@pytest.mark.parametrize(
    ("make_config", "runner", "runner_module", "compute_name", "writer_name", "body_key"),
    [
        (
            standoff_config,
            run_shock_standoff,
            run_shock_standoff_module,
            "compute_shock_standoff",
            "write_shock_standoff",
            "nose_radius",
        ),
        (
            shape_config,
            run_shock_shape,
            run_shock_shape_module,
            "compute_shock_shape",
            "write_shock_shape",
            "geometry",
        ),
    ],
)
def test_shock_runners_use_reconstructed_flow_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    make_config,
    runner,
    runner_module,
    compute_name: str,
    writer_name: str,
    body_key: str,
) -> None:
    """Both runners should get Mach and gamma from canonical FlowState JSON."""

    # build and write a complete freestream state
    state = solve(
        mach=6.0,
        pres=101325.0,
        temp=300.0,
        gas=PerfectGas.air(),
    )
    flow_state_path = tmp_path / "flow_state.json"
    write_json(state, flow_state_path)

    config = make_config(flow_state_path)
    captured: dict[str, object] = {}

    def capture_compute(**kwargs):
        captured.update(kwargs)
        return object()

    # isolate the runner's data handoff
    monkeypatch.setattr(runner_module, compute_name, capture_compute)
    monkeypatch.setattr(runner_module, writer_name, lambda result, output: None)

    # run through the public workflow boundary
    runner(config)

    # check canonical state values reach the physics API
    assert captured["mach"] == state.mach
    assert captured["gamma"] == state.gamma
    assert body_key in captured


def test_run_commands_execute_their_own_shock_section(tmp_path: Path) -> None:
    """One config file can hold both shock sections; each run command reads its own."""

    # build and write the shared canonical freestream state
    state = solve(
        mach=6.0,
        pres=101325.0,
        temp=300.0,
        gas=PerfectGas.air(),
    )
    flow_state_path = tmp_path / "flow_state.json"
    write_json(state, flow_state_path)

    # build a config that enables both independent shock workflows
    standoff_path = tmp_path / "standoff.dat"
    shape_path = tmp_path / "shape.dat"
    config_path = tmp_path / "flow_theory.toml"
    config_text = f"""
[shock_standoff]
flow_conditions = "{flow_state_path}"
nose_radius = 0.01
method = "serbin"
output = "{standoff_path}"

[shock_shape]
flow_conditions = "{flow_state_path}"
n_points = 11
x_e = 0.05
output = "{shape_path}"

[shock_shape.geometry]
type = "cone"
nose_radius = 0.01
half_angle = 0.0
"""
    config_path.write_text(config_text, encoding="utf-8")

    # run each section with its own command
    try:
        cmd_shock_standoff(config=config_path)
        cmd_shock_shape(config=config_path)
    except typer.Exit as error:
        pytest.fail(f"shock run exited unexpectedly: {error}")

    # check both workflows produced their own output
    assert standoff_path.exists()
    assert shape_path.exists()
    assert (
        'ZONE T="shock standoff sphere serbin", I=1'
        in standoff_path.read_text(encoding="utf-8")
    )
    shape_text = shape_path.read_text(encoding="utf-8")
    assert 'ZONE T="shock shape cone billig", I=11' in shape_text
    assert 'ZONE T="body surface cone", I=11' in shape_text


def test_shock_shape_config_cone_requires_x_e() -> None:
    """Cone geometry config should fail when x_e is omitted."""

    with pytest.raises(ValueError, match="x_e: Field required"):
        ShockShapeConfig.from_dict(
            {
                "flow_conditions": "flow.json",
                "geometry": {"type": "cone", "nose_radius": 0.01, "half_angle": 15.0},
                "method": "billig",
                "n_points": 101,
            }
        )


def test_cmd_shock_shape_accepts_config_path(tmp_path: Path) -> None:
    """shock-shape command should run from a [shock_shape] config section."""

    # build and write a complete freestream state
    state = solve(
        mach=6.0,
        pres=101325.0,
        temp=300.0,
        gas=PerfectGas.air(),
    )
    flow_state_path = tmp_path / "flow_state.json"
    write_json(state, flow_state_path)

    # build a dedicated shock-shape config file
    shape_path = tmp_path / "shape.dat"
    config_path = tmp_path / "flow_theory.toml"
    config_text = f"""
[shock_shape]
flow_conditions = "{flow_state_path}"
n_points = 11
x_e = 0.05
output = "{shape_path}"

[shock_shape.geometry]
type = "tangent-ogive"
nose_radius = 0.002
length = 0.04
base_radius = 0.006
"""
    config_path.write_text(config_text, encoding="utf-8")

    # execute the command in config-file mode
    try:
        cmd_shock_shape(config=config_path)
    except typer.Exit as error:
        pytest.fail(f"shock-shape config mode exited unexpectedly: {error}")

    # check the output was produced from config inputs
    assert shape_path.exists()
    shape_text = shape_path.read_text(encoding="utf-8")
    assert 'ZONE T="shock shape tangent-ogive billig", I=11' in shape_text
    assert 'ZONE T="body surface tangent-ogive", I=11' in shape_text


def test_cmd_shock_shape_requires_direct_inputs_without_config() -> None:
    """Direct shock-shape mode should fail when required direct inputs are missing."""

    with pytest.raises(typer.Exit):
        cmd_shock_shape()


def test_shock_shape_config_rejects_the_old_flat_geometry() -> None:
    """geometry = "sphere" (the former flat keys) points to the [shock_shape.geometry] table."""

    with pytest.raises(ValueError, match=r"\[shock_shape.geometry\] table"):
        ShockShapeConfig.from_dict(
            {
                "flow_conditions": "flow.json",
                "geometry": "sphere",
                "x_e": 0.05,
            }
        )


def test_cmd_shock_shape_direct_options_write_csv(tmp_path: Path) -> None:
    """Direct options build the geometry table; .csv output holds the shock as x, y."""

    # build and write a complete freestream state
    state = solve(
        mach=6.0,
        pres=101325.0,
        temp=300.0,
        gas=PerfectGas.air(),
    )
    flow_state_path = tmp_path / "flow_state.json"
    write_json(state, flow_state_path)

    # run a wedge from direct options
    shape_path = tmp_path / "shock.csv"
    try:
        cmd_shock_shape(
            flow_conditions=flow_state_path,
            nose_radius=0.01,
            geometry="wedge",
            half_angle=10.0,
            n_points=21,
            x_e=0.1,
            output=shape_path,
        )
    except typer.Exit as error:
        pytest.fail(f"shock-shape direct mode exited unexpectedly: {error}")

    # check: header, then 21 rows from the vertex to x_e
    lines = shape_path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "x,y"
    assert len(lines) == 22
    x_last, _ = (float(value) for value in lines[-1].split(","))
    assert x_last == pytest.approx(0.1)
