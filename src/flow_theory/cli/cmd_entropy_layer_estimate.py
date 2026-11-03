"""CLI handler for ``flow-theory entropy-layer-estimate``."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from flow_theory.config import EntropyLayerEstimateConfig
from flow_theory.runners import run_entropy_layer_estimate

from .focused_config import write_focused_config

entropy_layer_estimate_app = typer.Typer(
    name="entropy-layer-estimate",
    help="Entropy-layer thickness estimates.",
    no_args_is_help=True,
)


@entropy_layer_estimate_app.command(name="init")
def cmd_init_entropy_layer_estimate(
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output TOML path."),
    ] = Path("entropy_layer_estimate.toml"),
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Overwrite existing output file."),
    ] = False,
) -> None:
    """Write a focused entropy-layer estimate configuration."""
    try:
        write_focused_config(
            "entropy_layer_estimate",
            output,
            force,
            "flow-theory entropy-layer-estimate run",
        )
    except (OSError, ValueError) as error:
        typer.echo(f"error: {error}", err=True)
        raise typer.Exit(1) from None


@entropy_layer_estimate_app.command(name="run")
def cmd_entropy_layer_estimate(
    config: Annotated[
        Path | None,
        typer.Option("--config", "--cfg", "-c", help="Config TOML path."),
    ] = None,
    x: Annotated[
        float | None,
        typer.Option("--x", help="Streamwise station \\[m]."),
    ] = None,
    mach: Annotated[
        float | None,
        typer.Option("--mach", help="Edge Mach number."),
    ] = None,
    nose_radius: Annotated[
        float | None,
        typer.Option("--nose-radius", help="Nose radius \\[m]."),
    ] = None,
    gamma: Annotated[
        float,
        typer.Option("--gamma", help="Specific heat ratio."),
    ] = 1.4,
    output: Annotated[
        Path | None,
        typer.Option("--output", help="Optional Tecplot output path."),
    ] = None,
) -> None:
    """Estimate entropy-layer thickness at one station."""

    try:
        # select direct-option mode when any required direct input is supplied
        use_direct_options = any(value is not None for value in (x, mach, nose_radius))

        if use_direct_options:
            if config is not None:
                raise ValueError("--config cannot be combined with direct inputs")
            if x is None or mach is None or nose_radius is None:
                raise ValueError(
                    "x, mach, and nose_radius are required unless --config is provided"
                )

            runner_config = EntropyLayerEstimateConfig.from_dict(
                {
                    "x": x,
                    "mach": mach,
                    "nose_radius": nose_radius,
                    "gamma": gamma,
                    "output": output,
                }
            )
        else:
            config_path = (
                Path("entropy_layer_estimate.toml") if config is None else config
            )
            runner_config = EntropyLayerEstimateConfig.from_file(config_path)

        run_entropy_layer_estimate(runner_config)
    except typer.Exit:
        raise
    except Exception as error:
        typer.echo(f"error: {error}", err=True)
        raise typer.Exit(1) from None
