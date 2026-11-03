"""Configuration model for the [shock_standoff] section."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal

from flow_theory.shock.standoff import (
    SHOCK_STANDOFF_GEOMETRIES,
    SHOCK_STANDOFF_METHODS,
)

from .section import NormalizedName, Positive, SectionConfig


# --------------------------------------------------
# typed configuration
# --------------------------------------------------
class ShockStandoffConfig(SectionConfig):
    """Validated inputs for a shock-standoff calculation.

    Attributes:
        flow_conditions: FlowState JSON with the freestream.
        nose_radius: Nose radius [m].
        geometry: Nose shape (sphere or cylinder).
        method: Standoff correlation.
        output: Optional Tecplot output path.
    """

    section_name = "shock_standoff"

    # flow conditions input file path
    flow_conditions: Path
    # nose radius (m)
    nose_radius: Positive
    # geometry flag
    geometry: Annotated[Literal[SHOCK_STANDOFF_GEOMETRIES], NormalizedName] = "sphere"
    # method flag
    method: Annotated[Literal[SHOCK_STANDOFF_METHODS], NormalizedName] = (
        "ambrosio_wortman"
    )
    output: Path | None = None
