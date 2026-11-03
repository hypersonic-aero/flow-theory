"""Runner for the [shock_standoff] section."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

from flow_state.io import read_json

from flow_theory.config import ShockStandoffConfig
from flow_theory.io import write_shock_standoff
from flow_theory.shock import compute_shock_standoff


# --------------------------------------------------
# runner for shock-standoff calculations
# --------------------------------------------------
def run_shock_standoff(config: ShockStandoffConfig) -> None:
    """Execute a shock-standoff calculation."""

    # validate runner input type at the boundary
    if not isinstance(config, ShockStandoffConfig):
        raise TypeError(
            "wrong input: run_shock_standoff expects a ShockStandoffConfig instance"
        )

    # read the complete freestream state
    flow_state = read_json(config.flow_conditions)

    # compute the requested standoff estimate
    result = compute_shock_standoff(
        mach=flow_state.mach,
        nose_radius=config.nose_radius,
        geometry=config.geometry,
        method=config.method,
        gamma=flow_state.gamma,
    )

    # report and optionally write the result
    write_shock_standoff(result, config.output)
