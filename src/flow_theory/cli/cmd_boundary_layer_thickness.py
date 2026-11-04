"""CLI handler for ``flow-theory boundary-layer-thickness``."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from flow_theory.config import BoundaryLayerThicknessConfig
from flow_theory.runners import run_boundary_layer_thickness

from .focused_config import write_focused_config

boundary_layer_app = typer.Typer(
    name="bl",
    help="Laminar flat-plate boundary-layer thickness calculations.",
    no_args_is_help=True,
)


@boundary_layer_app.command(name="init")
def cmd_init_boundary_layer_thickness(
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output TOML path."),
    ] = Path("boundary_layer_thickness.toml"),
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Overwrite existing output file."),
    ] = False,
) -> None:
    """Write a focused boundary-layer thickness configuration."""
    try:
        write_focused_config(
            "boundary_layer_thickness",
            output,
            force,
            "flow-theory bl run",
        )
    except (OSError, ValueError) as error:
        typer.echo(f"error: {error}", err=True)
        raise typer.Exit(1) from None


@boundary_layer_app.command(name="run")
def cmd_boundary_layer_thickness(
    config: Annotated[
        Path | None,
        typer.Option("--config", "-c", help="Config TOML path."),
    ] = None,
    x: Annotated[
        float | None,
        typer.Option("--x", help="Streamwise station \\[m]."),
    ] = None,
    re1: Annotated[
        float | None,
        typer.Option("--re1", help="Unit Reynolds number [1/m]."),
    ] = None,
    method: Annotated[
        str,
        typer.Option("--method", help="Thickness correlation name."),
    ] = "blasius",
    mach: Annotated[
        float | None,
        typer.Option("--mach", help="Edge Mach number."),
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
    """Compute laminar flat-plate boundary-layer thickness."""

    try:
        # select direct-option mode when either required input is supplied
        use_direct_options = x is not None or re1 is not None

        if use_direct_options:
            if config is not None:
                raise ValueError("--config cannot be combined with direct inputs")
            if x is None:
                raise ValueError("x is required unless --config is provided")
            if re1 is None:
                raise ValueError("re1 is required unless --config is provided")

            # build the shared runner configuration from direct options
            runner_config = BoundaryLayerThicknessConfig.from_dict(
                {
                    "x": x,
                    "re1": re1,
                    "method": method,
                    "mach": mach,
                    "tw_t0": tw_t0,
                    "gamma": gamma,
                    "output": output,
                }
            )
        else:
            # load the focused default configuration when no direct inputs are given
            config_path = (
                Path("boundary_layer_thickness.toml") if config is None else config
            )
            runner_config = BoundaryLayerThicknessConfig.from_file(config_path)

        # run the shared thickness implementation
        run_boundary_layer_thickness(runner_config)
    except typer.Exit:
        raise
    except Exception as error:
        typer.echo(f"error: {error}", err=True)
        raise typer.Exit(1) from None
