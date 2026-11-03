"""Runner for the [shock_shape] section."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

from flow_state.io import read_json

from flow_theory.config import ShockShapeConfig
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

    # compute the requested shock locus
    result = compute_shock_shape(
        mach=flow_state.mach,
        gamma=flow_state.gamma,
        geometry=config.geometry,
        x_e=config.x_e,
        n_points=config.n_points,
        method=config.method,
        blend_nose_radii=config.blend_nose_radii,
    )

    # report and optionally write the result
    write_shock_shape(result, config.output)
