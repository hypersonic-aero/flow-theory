from pathlib import Path

import numpy as np
import pytest
from pydantic import ValidationError

from flow_theory.config import CfChConfig
from flow_theory.runners import run_cf_ch


def test_cf_ch_config_resolves_scalar_x() -> None:
    config = CfChConfig(
        flow_conditions=Path("flow_conditions.json"),
        x=1.5,
    )
    values = config.x

    assert values.shape == (1,)
    assert np.allclose(values, np.array([1.5], dtype=float))


def test_cf_ch_config_resolves_count_based_x() -> None:
    config = CfChConfig(
        flow_conditions=Path("flow_conditions.json"),
        x=[0.1, 1.0, 5],
    )
    values = config.x

    assert np.allclose(values, np.linspace(0.1, 1.0, 5, dtype=float))


def test_cf_ch_config_resolves_step_based_x() -> None:
    config = CfChConfig(
        flow_conditions=Path("flow_conditions.json"),
        x=[0.1, 1.0, 0.2],
    )
    values = config.x

    assert np.allclose(values, np.array([0.1, 0.3, 0.5, 0.7, 0.9, 1.0]))


def test_cf_ch_config_rejects_invalid_x_values() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        CfChConfig(
            flow_conditions=Path("flow_conditions.json"),
            x=-0.1,
        )

    with pytest.raises(ValueError, match="greater than start"):
        CfChConfig(
            flow_conditions=Path("flow_conditions.json"),
            x=[1.0, 1.0, 2],
        )


def test_cf_ch_config_is_frozen_after_init() -> None:
    config = CfChConfig(
        flow_conditions=Path("flow_conditions.json"),
        x=1.0,
        wall_type="adiabatic",
    )

    with pytest.raises(ValidationError, match="frozen"):
        config.mode = "laminar"


def test_cf_ch_config_normalizes_values_in_post_init() -> None:
    config = CfChConfig(
        flow_conditions=Path("flow_conditions.json"),
        x=1.0,
        mode=" LAMINAR ",
        method=" Similarity ",
        wall_type=" ISOTHERMAL ",
        temp_wall=300.0,
    )

    assert config.mode == "laminar"
    assert config.method == "similarity"
    assert config.wall_type == "isothermal"


def test_run_cf_ch_requires_cf_ch_config_instance() -> None:
    with pytest.raises(TypeError, match="CfChConfig"):
        run_cf_ch(object())
