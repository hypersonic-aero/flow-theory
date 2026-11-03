"""Runner for the [cf_ch] section."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

from flow_state.io import read_json
from flow_state.transport import transport_model_from_spec

from flow_theory.cf_ch import compute_cf_ch
from flow_theory.config import CfChConfig
from flow_theory.io import write_cf_ch


# --------------------------------------------------
# runner for cf/ch calculations
#
# orchestrates the cf/ch calculation and output for a given config
# --------------------------------------------------
def run_cf_ch(config: CfChConfig) -> None:
    """Execute a cf/ch calculation."""

    # --------------------------------------------------
    # validate runner input type at the boundary
    # --------------------------------------------------
    if not isinstance(config, CfChConfig):
        raise TypeError("wrong input: run_cf_ch expects a CfChConfig instance")

    # --------------------------------------------------
    # get the complete flow state from the input JSON file
    # note: read_json and transport_model_from_spec are from the flow-state package
    # --------------------------------------------------
    flow_state = read_json(config.flow_conditions)

    # reconstruct the exact viscosity law from the flow-state specification
    visc_model = transport_model_from_spec(flow_state.transport_model)

    # --------------------------------------------------
    # compute cf/ch estimates
    # --------------------------------------------------
    cf_ch_data = compute_cf_ch(
        config.x,
        flow_state.re1,
        flow_state.mach,
        flow_state.temp,
        config.temp_wall,
        config.wall_type,
        mode=config.mode,
        method=config.method,
        gamma=flow_state.gamma,
        pr=flow_state.pr,
        visc_model=visc_model,
    )

    # print and optionally write results
    write_cf_ch(cf_ch_data, config.output)
