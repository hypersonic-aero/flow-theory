"""CLI handler for ``flow-theory shock-shape``."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from flow_theory.config import ShockShapeConfig
from flow_theory.geometry import BODY_GEOMETRIES
from flow_theory.runners import run_shock_shape

from .examples_command import build_examples_command
from .focused_config import write_focused_config

# --------------------------------------------------
# shock-shape command group
# --------------------------------------------------
shock_shape_app = typer.Typer(
    name="shock-shape",
    help="Approximate detached bow-shock shape calculations.",
    no_args_is_help=True,
)


@shock_shape_app.command(name="init")
def cmd_init_shock_shape(
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output TOML path."),
    ] = Path("shock_shape.toml"),
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Overwrite existing output file."),
    ] = False,
) -> None:
    """Write a shock-shape configuration starter file."""
    try:
        write_focused_config(
            "shock_shape",
            output,
            force,
            "flow-theory shock-shape run",
        )
    except (OSError, ValueError) as error:
        typer.echo(f"error: {error}", err=True)
        raise typer.Exit(1) from None


# --------------------------------------------------
# main function for the 'shock-shape' cli command
# --------------------------------------------------
@shock_shape_app.command(name="run")
def cmd_shock_shape(
    config: Annotated[
        Path | None,
        typer.Option(
            "--config",
            "--cfg",
            "-c",
            help="Config TOML path. Defaults to shock_shape.toml when no direct inputs are provided.",
        ),
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
        typer.Option("--geometry", help=f"Body geometry ({', '.join(BODY_GEOMETRIES)})."),
    ] = "cone",
    method: Annotated[
        str,
        typer.Option(
            "--method", help="Shock-shape correlation: billig (default) or billig_blended."
        ),
    ] = "billig",
    half_angle: Annotated[
        float | None,
        typer.Option(
            "--half-angle",
            help="Half-angle \\[deg], required for cone and wedge geometries.",
        ),
    ] = None,
    length: Annotated[
        float | None,
        typer.Option(
            "--length",
            help="Sharp-ogive length, tip to base \\[m], tangent-ogive only.",
        ),
    ] = None,
    base_radius: Annotated[
        float | None,
        typer.Option("--base-radius", help="Base radius \\[m], tangent-ogive only."),
    ] = None,
    n_points: Annotated[
        int,
        typer.Option(
            "--n-points",
            help="Number of sample points used for both shock and surface zones.",
        ),
    ] = 100,
    blend_nose_radii: Annotated[
        float | None,
        typer.Option(
            "--blend-nose-radii",
            help="billig_blended only: blend length in nose radii (default 35).",
        ),
    ] = None,
    x_e: Annotated[
        float,
        typer.Option(
            "--x-e",
            help="Streamwise endpoint for body and shock sampling.",
        ),
    ] = 0.1,
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            help="Optional output path: .csv (shock x, y) or Tecplot ASCII (other extensions).",
        ),
    ] = None,
) -> None:
    """Compute an approximate shock shape."""

    try:
        # use direct options whenever either required direct input is present
        use_direct_options = flow_conditions is not None or nose_radius is not None

        # read and run from the focused config when direct inputs are absent
        if not use_direct_options:
            config_path = Path("shock_shape.toml") if config is None else config
            shock_shape_cfg = ShockShapeConfig.from_file(config_path)
            run_shock_shape(shock_shape_cfg)
            return

        if config is not None:
            raise ValueError("--config cannot be combined with direct solver inputs")

        # validate required direct inputs when config path is not provided
        if flow_conditions is None:
            raise ValueError("flow_conditions is required unless --config is provided")
        if nose_radius is None:
            raise ValueError("nose_radius is required unless --config is provided")

        # build the [geometry] table from the options that were given
        geometry_table = {"type": geometry, "nose_radius": nose_radius}
        shape_options = {"half_angle": half_angle, "length": length, "base_radius": base_radius}
        for key, value in shape_options.items():
            if value is not None:
                geometry_table[key] = value

        # get the typed configuration dataclass
        config = ShockShapeConfig.from_dict(
            {
                "flow_conditions": flow_conditions,
                "geometry": geometry_table,
                "x_e": x_e,
                "method": method,
                "n_points": n_points,
                "blend_nose_radii": blend_nose_radii,
                "output": output,
            }
        )

        # run the shared shock-shape implementation
        run_shock_shape(config)

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"error: {e}", err=True)
        raise typer.Exit(1)


# --------------------------------------------------
# examples: bundled cases, copied into ./<name>/ to run
# --------------------------------------------------
shock_shape_app.command(name="examples")(
    build_examples_command("shock_shape", "shock-shape")
)
