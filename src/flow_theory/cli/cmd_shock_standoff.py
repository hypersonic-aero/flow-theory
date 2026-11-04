"""CLI handler for ``flow-theory shock-standoff``."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from flow_theory.config import ShockStandoffConfig
from flow_theory.runners import run_shock_standoff

from .focused_config import write_focused_config

shock_standoff_app = typer.Typer(
    name="shock-standoff",
    help="Normal-shock standoff distance calculations.",
    no_args_is_help=True,
)


@shock_standoff_app.command(name="init")
def cmd_init_shock_standoff(
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output TOML path."),
    ] = Path("shock_standoff.toml"),
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Overwrite existing output file."),
    ] = False,
) -> None:
    """Write a focused shock-standoff configuration."""
    try:
        write_focused_config(
            "shock_standoff",
            output,
            force,
            "flow-theory shock-standoff run",
        )
    except (OSError, ValueError) as error:
        typer.echo(f"error: {error}", err=True)
        raise typer.Exit(1) from None


# --------------------------------------------------
# main function for the shock-standoff command
# --------------------------------------------------
@shock_standoff_app.command(name="run")
def cmd_shock_standoff(
    config: Annotated[
        Path | None,
        typer.Option("--config", "-c", help="Config TOML path."),
    ] = None,
    flow_conditions: Annotated[
        Path | None,
        typer.Option(
            "--flow-conditions",
            help="Required flow-state JSON file with freestream conditions.",
        ),
    ] = None,
    nose_radius: Annotated[
        float | None,
        typer.Option("--nose-radius", help="Body nose radius."),
    ] = None,
    geometry: Annotated[
        str,
        typer.Option("--geometry", help="Nose geometry: sphere or cylinder."),
    ] = "sphere",
    method: Annotated[
        str,
        typer.Option(
            "--method",
            help=(
                "Shock-standoff correlation: ambrosio_wortman, "
                "ambrosio_wortman_density_ratio, or serbin."
            ),
        ),
    ] = "ambrosio_wortman",
    output: Annotated[
        Path | None,
        typer.Option("--output", help="Optional Tecplot output path."),
    ] = None,
) -> None:
    """Compute a normal-shock standoff estimate."""

    try:
        # select direct-option mode when either required input is supplied
        use_direct_options = flow_conditions is not None or nose_radius is not None

        if use_direct_options:
            if config is not None:
                raise ValueError("--config cannot be combined with direct inputs")
            if flow_conditions is None:
                raise ValueError(
                    "flow_conditions is required unless --config is provided"
                )
            if nose_radius is None:
                raise ValueError("nose_radius is required unless --config is provided")

            # build the shared runner configuration from direct options
            runner_config = ShockStandoffConfig.from_dict(
                {
                    "flow_conditions": flow_conditions,
                    "nose_radius": nose_radius,
                    "geometry": geometry,
                    "method": method,
                    "output": output,
                }
            )
        else:
            # load the focused default configuration when no direct inputs are given
            config_path = Path("shock_standoff.toml") if config is None else config
            runner_config = ShockStandoffConfig.from_file(config_path)

        # run the shared shock-standoff implementation
        run_shock_standoff(runner_config)

    except typer.Exit:
        raise
    except Exception as error:
        typer.echo(f"error: {error}", err=True)
        raise typer.Exit(1) from None
