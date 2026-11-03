"""Tests for calculator-scoped init and run commands."""

from __future__ import annotations

import logging
import tomllib
from collections.abc import Iterator
from pathlib import Path

import pytest
from typer.testing import CliRunner

from flow_theory.cli.app import app
from flow_theory.io.examples import list_examples

runner = CliRunner()


@pytest.fixture(autouse=True)
def use_temporary_working_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Run each CLI test from an isolated temporary directory."""

    monkeypatch.chdir(tmp_path)


@pytest.fixture(autouse=True)
def restore_flow_theory_logger() -> Iterator[None]:
    """Restore logger state after each in-process CLI invocation."""

    # save the logger state modified by the global CLI callback
    logger = logging.getLogger("flow-theory")
    original_level = logger.level
    original_propagate = logger.propagate
    original_handlers = list(logger.handlers)

    yield

    # close handlers created by the CLI and restore the original state
    for handler in logger.handlers:
        if handler not in original_handlers:
            handler.close()
    logger.handlers = original_handlers
    logger.setLevel(original_level)
    logger.propagate = original_propagate


def test_root_global_init_and_run_are_not_registered() -> None:
    """Independent calculators should not expose a global batch workflow."""
    init_result = runner.invoke(app, ["init"])
    run_result = runner.invoke(app, ["run"])

    assert init_result.exit_code != 0
    assert "No such command 'init'" in init_result.output
    assert run_result.exit_code != 0
    assert "No such command 'run'" in run_result.output


def test_shock_shape_init_writes_focused_config() -> None:
    """Shock-shape init should write one section without a run toggle."""
    result = runner.invoke(app, ["shock-shape", "init"])
    config_text = Path("shock_shape.toml").read_text(encoding="utf-8")

    assert result.exit_code == 0
    assert config_text.count("[shock_shape]") == 1
    assert "run =" not in config_text
    assert "[shock_standoff]" not in config_text


def test_shock_shape_group_lists_init_and_run() -> None:
    """Shock-shape should expose the common scoped command interface."""
    result = runner.invoke(app, ["shock-shape", "--help"])

    assert result.exit_code == 0
    assert "init" in result.output
    assert "run" in result.output


def test_boundary_layer_init_writes_focused_config() -> None:
    """Boundary-layer init should write one section without a run toggle."""
    result = runner.invoke(app, ["bl", "init"])
    config_text = Path("boundary_layer_thickness.toml").read_text(encoding="utf-8")

    assert result.exit_code == 0
    assert config_text.count("[boundary_layer_thickness]") == 1
    assert "run =" not in config_text
    assert "[cf_ch]" not in config_text


def test_boundary_layer_group_lists_init_and_run() -> None:
    """Boundary-layer should expose the common scoped command interface."""
    result = runner.invoke(app, ["bl", "--help"])

    assert result.exit_code == 0
    assert "init" in result.output
    assert "run" in result.output


def test_flow_condition_calculators_have_scoped_workflows() -> None:
    """Flow-condition calculators should generate focused configs and list commands."""
    cases = [
        ("cf-ch", "cf_ch.toml", "[cf_ch]"),
        ("shock-standoff", "shock_standoff.toml", "[shock_standoff]"),
    ]

    for command, filename, section in cases:
        init_result = runner.invoke(app, [command, "init"])
        config_text = Path(filename).read_text(encoding="utf-8")
        help_result = runner.invoke(app, [command, "--help"])

        assert init_result.exit_code == 0
        assert section in config_text
        assert "run =" not in config_text
        assert help_result.exit_code == 0
        assert "init" in help_result.output
        assert "run" in help_result.output


def test_entropy_layer_calculators_have_scoped_workflows() -> None:
    """Entropy-layer calculators should generate focused configs and list commands."""
    cases = [
        (
            "entropy-layer-estimate",
            "entropy_layer_estimate.toml",
            "[entropy_layer_estimate]",
        ),
        (
            "entropy-layer-swallowing",
            "entropy_layer_swallowing.toml",
            "[entropy_layer_swallowing]",
        ),
    ]

    for command, filename, section in cases:
        init_result = runner.invoke(app, [command, "init"])
        config_text = Path(filename).read_text(encoding="utf-8")
        help_result = runner.invoke(app, [command, "--help"])

        assert init_result.exit_code == 0
        assert section in config_text
        assert "run =" not in config_text
        assert help_result.exit_code == 0
        assert "init" in help_result.output
        assert "run" in help_result.output


def test_transition_has_scoped_workflow() -> None:
    """Transition should generate a focused config and list both commands."""
    init_result = runner.invoke(app, ["transition", "init"])
    config_text = Path("transition.toml").read_text(encoding="utf-8")
    help_result = runner.invoke(app, ["transition", "--help"])

    assert init_result.exit_code == 0
    assert "[transition]" in config_text
    assert "run =" not in config_text
    assert help_result.exit_code == 0
    assert "init" in help_result.output
    assert "run" in help_result.output


# --------------------------------------------------
# examples
# --------------------------------------------------

# CLI command name of each calculator (config section name -> command)
CALCULATOR_COMMANDS = {
    "boundary_layer_thickness": "bl",
    "cf_ch": "cf-ch",
    "entropy_layer_estimate": "entropy-layer-estimate",
    "entropy_layer_swallowing": "entropy-layer-swallowing",
    "shock_shape": "shock-shape",
    "shock_standoff": "shock-standoff",
    "transition": "transition",
}

# every bundled example as (calculator, name)
ALL_EXAMPLES = [
    (calculator, name)
    for calculator in CALCULATOR_COMMANDS
    for name in list_examples(calculator)
]


def test_examples_exist() -> None:
    """At least one calculator ships examples (guards against a packaging slip)."""
    assert ALL_EXAMPLES


@pytest.mark.parametrize(("calculator", "name"), ALL_EXAMPLES)
def test_every_example_copies_and_runs(
    calculator: str, name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Each example lands in the current folder and runs there with run's default config."""
    command = CALCULATOR_COMMANDS[calculator]

    # list: the example appears with its description
    list_result = runner.invoke(app, [command, "examples"])
    assert list_result.exit_code == 0
    assert name in list_result.output
    assert list_examples(calculator)[name] in list_result.output

    # copy into the current folder, then run there
    copy_result = runner.invoke(app, [command, "examples", name])
    assert copy_result.exit_code == 0
    run_result = runner.invoke(app, [command, "run"])

    # check: the run succeeded and wrote the output its config names
    assert run_result.exit_code == 0, run_result.output
    config = tomllib.loads(Path(f"{calculator}.toml").read_text(encoding="utf-8"))
    output = config[calculator].get("output")
    if output is not None:
        assert Path(output).exists()


def test_examples_refuse_to_overwrite_files_unless_forced() -> None:
    """A second copy fails without --force (the files exist) and overwrites with it."""
    calculator, name = ALL_EXAMPLES[0]
    command = CALCULATOR_COMMANDS[calculator]
    runner.invoke(app, [command, "examples", name])

    refused = runner.invoke(app, [command, "examples", name])
    forced = runner.invoke(app, [command, "examples", name, "--force"])

    assert refused.exit_code == 1
    assert "would overwrite" in refused.output
    assert forced.exit_code == 0


def test_examples_reject_an_unknown_name() -> None:
    """An unknown name fails, lists the available examples, and writes nothing."""
    calculator, name = ALL_EXAMPLES[0]
    command = CALCULATOR_COMMANDS[calculator]

    result = runner.invoke(app, [command, "examples", "nope"])

    assert result.exit_code == 1
    assert "unknown example" in result.output
    assert name in result.output
    assert list(Path(".").iterdir()) == []
