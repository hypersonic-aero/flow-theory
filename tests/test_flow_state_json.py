"""Tests for consuming the flow-state JSON contract."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

import importlib

import pytest
from flow_state.gas import PerfectGas
from flow_state.io import write_json
from flow_state.solvers import solve
from flow_state.transport import Keyes

from flow_theory.config import CfChConfig
from flow_theory.runners import run_cf_ch

run_cf_ch_module = importlib.import_module("flow_theory.runners.run_cf_ch")


# --------------------------------------------------
# flow-state JSON contract tests
# --------------------------------------------------
def test_run_cf_ch_uses_reconstructed_flow_state(tmp_path, monkeypatch) -> None:
    """The runner should consume a complete FlowState reconstructed by flow-state."""

    # build and write a nitrogen flow state using the Keyes viscosity law
    transport_model = Keyes.nitrogen()
    state = solve(
        mach=4.0,
        pres=101325.0,
        temp=300.0,
        gas=PerfectGas.nitrogen(),
        transport=transport_model,
    )
    flow_state_path = tmp_path / "flow_state.json"
    write_json(state, flow_state_path)

    config = CfChConfig(
        flow_conditions=flow_state_path,
        x=1.0,
        mode="turbulent",
        method="van_driest_ii",
    )

    captured: dict[str, object] = {}

    def capture_compute(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return {}

    monkeypatch.setattr(run_cf_ch_module, "compute_cf_ch", capture_compute)
    monkeypatch.setattr(run_cf_ch_module, "write_cf_ch", lambda data, output: None)

    # run through the public workflow boundary
    run_cf_ch(config)

    args = captured["args"]
    kwargs = captured["kwargs"]
    visc_model = kwargs["visc_model"]

    # check scalar state values and exact transport coefficients reach compute_cf_ch
    assert args[1] == state.re1
    assert args[2] == state.mach
    assert args[3] == state.temp
    assert kwargs["gamma"] == state.gamma
    assert kwargs["pr"] == state.pr
    assert visc_model == transport_model


def test_cf_ch_config_requires_flow_conditions_path() -> None:
    """The workflow should never discover a flow-state file implicitly."""

    with pytest.raises(ValueError, match="flow_conditions"):
        CfChConfig(
            flow_conditions=None,
            x=1.0,
            mode="turbulent",
            method="van_driest_ii",
        )
