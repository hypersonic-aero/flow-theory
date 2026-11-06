"""Runner for the [shock_shape] section."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

from canonical_geometries.config import load_geometry
from flow_state.io import read_json

from flow_theory.config import GeometryFile, ShockShapeConfig
from flow_theory.geometry import resolve_x_e
from flow_theory.io import write_shock_shape
from flow_theory.shock import compute_shock_shape


# --------------------------------------------------
# runner for shock-shape calculations
# --------------------------------------------------
def run_shock_shape(config: ShockShapeConfig) -> None:
    """Execute a shock-shape calculation."""

    # validate runner input type at the boundary
    if not isinstance(config, ShockShapeConfig):
        raise TypeError(
            "wrong input: run_shock_shape expects a ShockShapeConfig instance"
        )

    # read the complete freestream state
    flow_state = read_json(config.flow_conditions)

    # read the body: from its geometry file (the one grid-generator reads too), or as
    # given in [shock_shape.geometry]; messages name where it came from
    if isinstance(config.geometry, GeometryFile):
        geometry = load_geometry(config.geometry.file)
        body_source = str(config.geometry.file)
    else:
        geometry = config.geometry
        body_source = "[shock_shape.geometry]"

    # where the shock ends: x_e on the body, or the body's end when x_e is left out
    x_e = resolve_x_e(geometry, config.x_e, source=body_source)

    # compute the requested shock locus
    result = compute_shock_shape(
        mach=flow_state.mach,
        gamma=flow_state.gamma,
        geometry=geometry,
        x_e=x_e,
        n_points=config.n_points,
        method=config.method,
        blend_nose_radii=config.blend_nose_radii,
    )

    # report and optionally write the result
    write_shock_shape(result, config.output)
