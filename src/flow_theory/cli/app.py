"""flow-theory command-line interface (typer).

Subcommands are defined in separate ``cmd_*.py`` modules and
registered on the shared ``app`` Typer instance below.
"""

# --------------------------------------------------
# import necessary modules
# --------------------------------------------------
from __future__ import annotations

from typing import Annotated

import typer

from .callbacks import verbose_callback, version_callback
from .cmd_boundary_layer_thickness import boundary_layer_app
from .cmd_cf_ch import cf_ch_app
from .cmd_entropy_layer_estimate import entropy_layer_estimate_app
from .cmd_entropy_layer_swallowing import entropy_layer_swallowing_app
from .cmd_shock_shape import shock_shape_app
from .cmd_shock_standoff import shock_standoff_app
from .cmd_transition import transition_app

# --------------------------------------------------
# app
# --------------------------------------------------
app = typer.Typer(
    name="flow-theory",
    help="flow-theory command-line interface",
    no_args_is_help=True,
    add_completion=False,
)


# --------------------------------------------------
# callback for --version and --verbose options
# version_callback and verbose_callback are defined in callbacks.py
# --------------------------------------------------
@app.callback()
def callback(
    # --version -V option
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            "-V",
            help="Show version and exit.",
            callback=version_callback,
            is_eager=True,
        ),
    ] = None,
    # --verbose -v option
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose", "-v", help="Enable verbose output.", callback=verbose_callback
        ),
    ] = False,
) -> None:
    """flow-theory: useful engineering correlations and theoretical estimates."""


# --------------------------------------------------
# register subcommands
# notes:
# - the order at which they are registered is the order in which they display
# --------------------------------------------------

# calculators: each has its own init (config template) and run
app.add_typer(boundary_layer_app, name="bl")
app.add_typer(cf_ch_app, name="cf-ch")
app.add_typer(entropy_layer_estimate_app, name="entropy-layer-estimate")
app.add_typer(entropy_layer_swallowing_app, name="entropy-layer-swallowing")
app.add_typer(shock_standoff_app, name="shock-standoff")
app.add_typer(shock_shape_app, name="shock-shape")
app.add_typer(transition_app, name="transition")

# --------------------------------------------------
# main entry point
# --------------------------------------------------
if __name__ == "__main__":
    app()
