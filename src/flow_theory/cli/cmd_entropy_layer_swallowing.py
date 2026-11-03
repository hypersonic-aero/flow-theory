"""CLI handler for ``flow-theory entropy-layer-swallowing``."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from flow_theory.config import EntropyLayerSwallowingConfig
from flow_theory.runners import run_entropy_layer_swallowing

from .focused_config import write_focused_config

entropy_layer_swallowing_app = typer.Typer(
    name="entropy-layer-swallowing",
    help="Entropy-layer swallowing distance calculations.",
    no_args_is_help=True,
)


@entropy_layer_swallowing_app.command(name="init")
def cmd_init_entropy_layer_swallowing(
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output TOML path."),
    ] = Path("entropy_layer_swallowing.toml"),
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Overwrite existing output file."),
    ] = False,
) -> None:
    """Write a focused entropy-layer swallowing configuration."""
    try:
        write_focused_config(
            "entropy_layer_swallowing",
            output,
            force,
            "flow-theory entropy-layer-swallowing run",
        )
    except (OSError, ValueError) as error:
        typer.echo(f"error: {error}", err=True)
        raise typer.Exit(1) from None


@entropy_layer_swallowing_app.command(name="run")
def cmd_entropy_layer_swallowing(
    config: Annotated[
        Path | None,
        typer.Option("--config", "--cfg", "-c", help="Config TOML path."),
    ] = None,
    mach: Annotated[
        float | None,
        typer.Option("--mach", help="Edge Mach number."),
    ] = None,
    re1: Annotated[
        float | None,
        typer.Option("--re1", help="Unit Reynolds number [1/m]."),
    ] = None,
    nose_radius: Annotated[
        float | None,
        typer.Option("--nose-radius", help="Nose radius \\[m]."),
    ] = None,
    tw_t0: Annotated[
        float | None,
        typer.Option("--tw-t0", help="Wall-to-stagnation temperature ratio."),
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
    """Compute the entropy-layer swallowing distance."""

    try:
        # select direct-option mode when any required direct input is supplied
        use_direct_options = any(
            value is not None for value in (mach, re1, nose_radius, tw_t0)
        )

        if use_direct_options:
            if config is not None:
                raise ValueError("--config cannot be combined with direct inputs")
            if mach is None or re1 is None or nose_radius is None or tw_t0 is None:
                raise ValueError(
                    "mach, re1, nose_radius, and tw_t0 are required unless --config is provided"
                )

            runner_config = EntropyLayerSwallowingConfig.from_dict(
                {
                    "mach": mach,
                    "re1": re1,
                    "nose_radius": nose_radius,
                    "tw_t0": tw_t0,
                    "gamma": gamma,
                    "output": output,
                }
            )
        else:
            config_path = (
                Path("entropy_layer_swallowing.toml") if config is None else config
            )
            runner_config = EntropyLayerSwallowingConfig.from_file(config_path)

        run_entropy_layer_swallowing(runner_config)
    except typer.Exit:
        raise
    except Exception as error:
        typer.echo(f"error: {error}", err=True)
        raise typer.Exit(1) from None
