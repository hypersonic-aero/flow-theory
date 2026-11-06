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
from flow_theory.config import GeometryFile, ShockShapeConfig, ShockStandoffConfig
from flow_theory.runners import run_shock_shape, run_shock_standoff

run_shock_shape_module = importlib.import_module("flow_theory.runners.run_shock_shape")
run_shock_standoff_module = importlib.import_module(
    "flow_theory.runners.run_shock_standoff"
)


def write_geometry(path: Path, table: dict, n_cylinder: int | None = None) -> Path:
    """Write a geometry file (canonical-geometries' geometry.toml) holding one body.

    Args:
        path: File to write.
        table: [geometry] table, length included.
        n_cylinder: Points on the cylinder, for a tangent ogive with one.

    Returns:
        The path written.
    """

    # build the [geometry] table, and [points] when the body has a cylinder
    lines = ["[geometry]"]
    for key, value in table.items():
        lines.append(f"{key} = {value!r}".replace("'", '"'))
    if n_cylinder is not None:
        lines += ["", "[points]", f"n_cylinder = {n_cylinder}"]

    # write
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return path


# the cone most tests use: 1 cm nose, 7 deg, 5 cm long
CONE_TABLE = {"type": "cone", "nose_radius": 0.01, "length": 0.05, "half_angle": 7.0}


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
            "geometry": {"file": "body.toml"},
        }
    )

    # check independent workflow contracts
    assert isinstance(standoff, ShockStandoffConfig)
    assert standoff.geometry == "cylinder"
    assert isinstance(shape, ShockShapeConfig)
    assert shape.n_points == 51
    assert shape.x_e == 0.05
    assert shape.geometry == GeometryFile(file=Path("body.toml"))


# --------------------------------------------------
# FlowState handoff tests
# --------------------------------------------------
def standoff_config(flow_state_path: Path) -> ShockStandoffConfig:
    """Standoff config for a 1 cm nose."""
    return ShockStandoffConfig(flow_conditions=flow_state_path, nose_radius=0.01)


def shape_config(flow_state_path: Path) -> ShockShapeConfig:
    """Shape config for a cone with a 1 cm nose, its geometry file next to the flow state."""
    geometry_path = write_geometry(flow_state_path.parent / "geometry.toml", CONE_TABLE)
    return ShockShapeConfig(
        flow_conditions=flow_state_path,
        geometry=GeometryFile(file=geometry_path),
        x_e=0.05,
    )


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
file = "geometry.toml"
"""
    config_path.write_text(config_text, encoding="utf-8")

    # the body next to the config (a sphere-cylinder), found relative to the config
    write_geometry(tmp_path / "geometry.toml", CONE_TABLE | {"half_angle": 0.0})

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


def write_flow_state(tmp_path: Path) -> Path:
    """Write a Mach 6 air freestream (flow-state JSON) and return its path."""

    # build and write a complete freestream state
    state = solve(
        mach=6.0,
        pres=101325.0,
        temp=300.0,
        gas=PerfectGas.air(),
    )
    flow_state_path = tmp_path / "flow_state.json"
    write_json(state, flow_state_path)

    return flow_state_path


def test_shock_shape_x_e_defaults_to_the_body_end(tmp_path: Path) -> None:
    """Without x_e, the shock ends where the body in the geometry file ends."""

    # a config without x_e, and the 5 cm cone next to it
    flow_state_path = write_flow_state(tmp_path)
    write_geometry(tmp_path / "geometry.toml", CONE_TABLE)
    shape_path = tmp_path / "shock.csv"
    config_path = tmp_path / "shock_shape.toml"
    config_path.write_text(
        f"""
[shock_shape]
flow_conditions = "{flow_state_path}"
n_points = 21
output = "{shape_path}"
""",
        encoding="utf-8",
    )

    # run
    run_shock_shape(ShockShapeConfig.from_file(config_path))

    # check: the last shock point lies at the body's end
    lines = shape_path.read_text(encoding="utf-8").splitlines()
    x_last, _ = (float(value) for value in lines[-1].split(","))
    assert x_last == pytest.approx(0.05, rel=1.0e-12)


def test_shock_shape_refuses_x_e_past_the_body(tmp_path: Path) -> None:
    """x_e past the end of the body is refused, naming the geometry file."""

    # x_e = 0.1 m on a 5 cm cone
    flow_state_path = write_flow_state(tmp_path)
    geometry_path = write_geometry(tmp_path / "geometry.toml", CONE_TABLE)
    config = ShockShapeConfig(
        flow_conditions=flow_state_path,
        geometry=GeometryFile(file=geometry_path),
        x_e=0.1,
    )

    # check
    message = r"x_e = 0\.1 m lies past the end of the body in"
    with pytest.raises(ValueError, match=message) as raised:
        run_shock_shape(config)
    assert str(geometry_path) in str(raised.value)
    assert "(x = 0.05 m)" in str(raised.value)


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
file = "ogive.toml"
"""
    config_path.write_text(config_text, encoding="utf-8")

    # an ogive with a cylinder behind its base (x = 0.04), so x_e lies on the cylinder
    ogive_table = {
        "type": "tangent-ogive",
        "nose_radius": 0.002,
        "length": 0.04,
        "base_radius": 0.006,
        "cylinder_length": 0.02,
    }
    write_geometry(tmp_path / "ogive.toml", ogive_table, n_cylinder=20)

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


def write_shape_config(
    folder: Path, flow_state_path: Path, geometry_table: str
) -> Path:
    """Write a [shock_shape] config with the given [shock_shape.geometry] lines (csv output)."""

    # write
    output_path = folder / "shock.csv"
    config_path = folder / "shock_shape.toml"
    config_path.write_text(
        f"""
[shock_shape]
flow_conditions = "{flow_state_path}"
n_points = 21
output = "{output_path}"

[shock_shape.geometry]
{geometry_table}
""",
        encoding="utf-8",
    )

    return config_path


def test_shock_shape_body_by_its_keys_matches_the_geometry_file(tmp_path: Path) -> None:
    """The body's keys in [shock_shape.geometry] give the same shock as the same body's file."""

    # the 5 cm cone as a file, and by its keys (the same [geometry] keys)
    flow_state_path = write_flow_state(tmp_path)
    file_folder = tmp_path / "file"
    keys_folder = tmp_path / "keys"
    file_folder.mkdir()
    keys_folder.mkdir()
    write_geometry(file_folder / "geometry.toml", CONE_TABLE)
    body_keys = "\n".join(
        f"{key} = {value!r}".replace("'", '"') for key, value in CONE_TABLE.items()
    )
    file_config = write_shape_config(
        file_folder, flow_state_path, 'file = "geometry.toml"'
    )
    keys_config = write_shape_config(keys_folder, flow_state_path, body_keys)

    # run both
    run_shock_shape(ShockShapeConfig.from_file(file_config))
    run_shock_shape(ShockShapeConfig.from_file(keys_config))

    # check: the same shock, point for point
    file_shock = (file_folder / "shock.csv").read_text(encoding="utf-8")
    keys_shock = (keys_folder / "shock.csv").read_text(encoding="utf-8")
    assert keys_shock == file_shock


def test_shock_shape_without_a_geometry_table_reads_geometry_toml(
    tmp_path: Path,
) -> None:
    """No [shock_shape.geometry] table: the body is geometry.toml next to the config."""

    # a config without the table
    config_path = tmp_path / "shock_shape.toml"
    config_path.write_text(
        '[shock_shape]\nflow_conditions = "flow.json"\n', encoding="utf-8"
    )

    # check
    config = ShockShapeConfig.from_file(config_path)
    assert config.geometry == GeometryFile(file=tmp_path / "geometry.toml")


@pytest.mark.parametrize(
    ("geometry", "message"),
    [
        (
            {"file": "geometry.toml", "type": "cone", "nose_radius": 0.01},
            "give either file or the body's keys, not both",
        ),
        ({"type": "cone", "nose_radius": 0.01, "length": 0.05}, "half_angle"),
        ("geometry.toml", r"must be a \[shock_shape.geometry\] table"),
    ],
)
def test_shock_shape_geometry_table_takes_one_form(geometry, message: str) -> None:
    """A file and body keys together, an incomplete body, or a plain value are refused."""

    with pytest.raises(ValueError, match=message):
        ShockShapeConfig.from_dict(
            {"flow_conditions": "flow.json", "geometry": geometry}
        )


def test_shock_shape_refuses_x_e_past_a_body_given_by_its_keys(tmp_path: Path) -> None:
    """x_e past the end of a body in [shock_shape.geometry] names that table."""

    # x_e = 0.1 m on a 5 cm cone given by its keys
    flow_state_path = write_flow_state(tmp_path)
    config = ShockShapeConfig.from_dict(
        {"flow_conditions": flow_state_path, "geometry": CONE_TABLE, "x_e": 0.1}
    )

    # check
    message = (
        r"lies past the end of the body in \[shock_shape\.geometry\] \(x = 0\.05 m\)"
    )
    with pytest.raises(ValueError, match=message):
        run_shock_shape(config)


def test_cmd_shock_shape_direct_options_write_csv(tmp_path: Path) -> None:
    """Direct options take the geometry file; .csv output holds the shock as x, y."""

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
    geometry_path = write_geometry(
        tmp_path / "wedge.toml",
        {"type": "wedge", "nose_radius": 0.01, "length": 0.1, "half_angle": 10.0},
    )
    shape_path = tmp_path / "shock.csv"
    try:
        cmd_shock_shape(
            flow_conditions=flow_state_path,
            geometry=geometry_path,
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
