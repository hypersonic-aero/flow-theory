"""CLI handler for ``flow-theory cf-ch``.

The commands read edge flow conditions from a flow-state JSON file and sweep
``x`` from ``xs`` to ``xe``.
"""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from flow_theory.config import CfChConfig
from flow_theory.runners import run_cf_ch

from .focused_config import write_focused_config

cf_ch_app = typer.Typer(
    name="cf-ch",
    help="Flat-plate skin-friction and heat-transfer calculations.",
    no_args_is_help=True,
)


@cf_ch_app.command(name="init")
def cmd_init_cf_ch(
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output TOML path."),
    ] = Path("cf_ch.toml"),
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Overwrite existing output file."),
    ] = False,
) -> None:
    """Write a focused cf/ch configuration."""
    try:
        write_focused_config("cf_ch", output, force, "flow-theory cf-ch run")
    except (OSError, ValueError) as error:
        typer.echo(f"error: {error}", err=True)
        raise typer.Exit(1) from None


# --------------------------------------------------
# main function for the 'cf' cli command
# --------------------------------------------------
@cf_ch_app.command(name="run")
def cmd_cf_ch(
    config: Annotated[
        Path | None,
        typer.Option("--config", "-c", help="Config TOML path."),
    ] = None,
    xs: Annotated[
        float | None,
        typer.Option("--xs", help="Start x location \\[m]."),
    ] = None,
    xe: Annotated[
        float | None,
        typer.Option("--xe", help="End x location \\[m]."),
    ] = None,
    nx: Annotated[
        int | None,
        typer.Option("--nx", help="Number of x stations."),
    ] = None,
    flow_conditions: Annotated[
        Path | None,
        typer.Option(
            "--flow-conditions",
            help="Required flow-state JSON file with edge conditions.",
        ),
    ] = None,
    temp_wall: Annotated[
        float | None,
        typer.Option(
            "--temp-wall",
            help="Wall temperature [K]. Omit for adiabatic wall temperature.",
        ),
    ] = None,
    mode: Annotated[
        str | None,
        typer.Option("--mode", help="'laminar', 'turbulent', or omit for both."),
    ] = None,
    method: Annotated[
        str | None,
        typer.Option(
            "--method",
            help=(
                "Method name. Omit to evaluate all methods for the selected mode(s). "
                "Laminar: blasius, eckert_reference, similarity. "
                "Turbulent: van_driest_ii, spalding_chi, sommer_short, "
                "white_christoph."
            ),
        ),
    ] = None,
    output: Annotated[
        Path | None, typer.Option("--output", help="Optional Tecplot .dat output path.")
    ] = None,
) -> None:
    """Compute flat-plate cf and Ch along an x sweep."""

    try:
        # select direct-option mode when any required direct input is supplied
        use_direct_options = any(
            value is not None for value in (xs, xe, nx, flow_conditions)
        )

        if use_direct_options:
            if config is not None:
                raise ValueError("--config cannot be combined with direct inputs")
            if xs is None or xe is None or nx is None or flow_conditions is None:
                raise ValueError(
                    "xs, xe, nx, and flow_conditions are required unless --config is provided"
                )

            # build the shared runner configuration from direct options
            wall_type = "isothermal" if temp_wall is not None else "adiabatic"
            runner_config = CfChConfig.from_dict(
                {
                    "flow_conditions": flow_conditions,
                    "x": [xs, xe, nx],
                    "mode": mode,
                    "method": method,
                    "wall_type": wall_type,
                    "temp_wall": temp_wall,
                    "output": output,
                }
            )
        else:
            # load the focused default configuration when no direct inputs are given
            config_path = Path("cf_ch.toml") if config is None else config
            runner_config = CfChConfig.from_file(config_path)

        # run the shared cf/ch implementation
        run_cf_ch(runner_config)

    except typer.Exit:
        raise
    except Exception as error:
        typer.echo(f"error: {error}", err=True)
        raise typer.Exit(1) from None
