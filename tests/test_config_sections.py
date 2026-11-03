"""Tests for the pydantic config sections shared by every calculator."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

from flow_theory.config import (
    BoundaryLayerThicknessConfig,
    CfChConfig,
    EntropyLayerEstimateConfig,
    EntropyLayerSwallowingConfig,
    ShockShapeConfig,
    ShockStandoffConfig,
    TransitionConfig,
)
from flow_theory.templates import render_templates

# every section model, keyed by its section name (also the init template preset)
SECTION_MODELS = {
    model.section_name: model
    for model in (
        BoundaryLayerThicknessConfig,
        CfChConfig,
        EntropyLayerEstimateConfig,
        EntropyLayerSwallowingConfig,
        ShockShapeConfig,
        ShockStandoffConfig,
        TransitionConfig,
    )
}


# --------------------------------------------------
# init templates
# --------------------------------------------------
@pytest.mark.parametrize("section_name", list(SECTION_MODELS))
def test_init_templates_validate(section_name: str) -> None:
    """The file each `init` writes is a valid config for its own `run`."""

    # render and parse the template
    template = tomllib.loads(render_templates(section_name))

    # check: validates against the section model
    SECTION_MODELS[section_name].from_dict(template[section_name])


# --------------------------------------------------
# error reporting
# --------------------------------------------------
def test_errors_list_every_bad_key_on_its_own_line() -> None:
    """Typos, out-of-range values and bad selectors are reported together, by key."""

    # a section with three problems
    data = {
        "mach": -5.0,
        "re1": 3.0e6,
        "tw_te": [0.5, 0.0],
        "methd": "van_driest_blumer",
    }

    # check: one line per problem, no pydantic URLs
    with pytest.raises(ValueError) as error:
        TransitionConfig.from_dict(data)
    message = str(error.value)
    assert message.splitlines()[0] == "invalid [transition]:"
    assert "  mach: must be positive, got -5.0" in message
    assert "  tw_te: must be positive, got 0.0" in message
    assert "  methd: Extra inputs are not permitted" in message
    assert "errors.pydantic.dev" not in message


@pytest.mark.parametrize(
    ("model", "data", "key"),
    [
        # sections that used to accept any value
        (
            EntropyLayerEstimateConfig,
            {"x": 0.1, "mach": -8.0, "nose_radius": 0.01},
            "mach",
        ),
        (
            EntropyLayerSwallowingConfig,
            {
                "mach": 8.0,
                "re1": 3.0e6,
                "nose_radius": 0.01,
                "tw_t0": 0.4,
                "gamma": 0.9,
            },
            "gamma",
        ),
        (TransitionConfig, {"mach": "six", "re1": 3.0e6, "tw_te": 0.5}, "mach"),
        # selectors are checked against the calculator's methods
        (
            CfChConfig,
            {"flow_conditions": "f.json", "x": 1.0, "method": "blasus"},
            "method",
        ),
        (
            ShockStandoffConfig,
            {"flow_conditions": "f.json", "nose_radius": 0.01, "geometry": "cone"},
            "geometry",
        ),
    ],
)
def test_invalid_values_name_the_key(model, data: dict, key: str) -> None:
    """Each section rejects invalid values and names the key."""

    # check
    with pytest.raises(ValueError, match=rf"\n  {key}: "):
        model.from_dict(data)


def test_selectors_are_normalized() -> None:
    """Selector names are compared in lowercase, without surrounding spaces."""

    # parse a section with untidy selector names
    config = ShockStandoffConfig.from_dict(
        {
            "flow_conditions": "f.json",
            "nose_radius": 0.01,
            "geometry": " Cylinder ",
            "method": "SERBIN",
        }
    )

    # check
    assert config.geometry == "cylinder"
    assert config.method == "serbin"


def test_from_file_reports_a_missing_section(tmp_path: Path) -> None:
    """A config file without the calculator's section says which one is missing."""

    # a file with another calculator's section only
    path = tmp_path / "transition.toml"
    path.write_text("[cf_ch]\nx = 1.0\n", encoding="utf-8")

    # check
    with pytest.raises(ValueError, match=r"has no \[transition\] section"):
        TransitionConfig.from_file(path)
