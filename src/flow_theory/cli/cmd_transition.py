"""CLI handler for ``flow-theory transition``.

Computes the flat-plate transition location for one input case.
"""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from flow_theory.config import TransitionConfig
from flow_theory.runners import run_transition

from .focused_config import write_focused_config

transition_app = typer.Typer(
    name="transition",
    help="Flat-plate transition location calculations.",
    no_args_is_help=True,
)


@transition_app.command(name="init")
def cmd_init_transition(
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output TOML path."),
    ] = Path("transition.toml"),
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Overwrite existing output file."),
    ] = False,
) -> None:
    """Write a focused transition configuration."""
    try:
        write_focused_config(
            "transition",
            output,
            force,
            "flow-theory transition run",
        )
    except (OSError, ValueError) as error:
        typer.echo(f"error: {error}", err=True)
        raise typer.Exit(1) from None


# --------------------------------------------------
# main function for the 'transition' cli command
# --------------------------------------------------
@transition_app.command(name="run")
def cmd_transition(
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
    tw_te: Annotated[
        float | None,
        typer.Option("--tw-te", help="Wall-to-edge temperature ratio."),
    ] = None,
    method: Annotated[
        str,
        typer.Option(
            "--method", help="Transition-onset criterion (van_driest_blumer)."
        ),
    ] = "van_driest_blumer",
    output: Annotated[
        Path | None, typer.Option("--output", help="Optional Tecplot .dat output path.")
    ] = None,
) -> None:
    """Compute flat-plate transition location x_transition."""

    try:
        # select direct-option mode when any required direct input is supplied
        use_direct_options = any(value is not None for value in (mach, re1, tw_te))

        if use_direct_options:
            if config is not None:
                raise ValueError("--config cannot be combined with direct inputs")
            if mach is None or re1 is None or tw_te is None:
                raise ValueError(
                    "mach, re1, and tw_te are required unless --config is provided"
                )

            # build the shared runner configuration from direct options
            runner_config = TransitionConfig.from_dict(
                {
                    "mach": mach,
                    "re1": re1,
                    "tw_te": tw_te,
                    "method": method,
                    "output": output,
                }
            )
        else:
            # load the focused default configuration when no direct inputs are given
            config_path = Path("transition.toml") if config is None else config
            runner_config = TransitionConfig.from_file(config_path)

        # run the shared transition implementation
        run_transition(runner_config)

    except typer.Exit:
        raise
    except Exception as error:
        typer.echo(f"error: {error}", err=True)
        raise typer.Exit(1) from None
