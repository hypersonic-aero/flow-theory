"""Configuration model for the [boundary_layer_thickness] section."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal

from pydantic import model_validator

from flow_theory.boundary_layer import BOUNDARY_LAYER_THICKNESS_METHODS

from .section import (
    Gamma,
    NonNegativeSweep,
    NormalizedName,
    PositiveSweep,
    SectionConfig,
)


# --------------------------------------------------
# typed configuration
# --------------------------------------------------
class BoundaryLayerThicknessConfig(SectionConfig):
    """Validated inputs for a boundary-layer thickness calculation.

    Attributes:
        x: Streamwise station [m] (one value or a sweep).
        re1: Unit Reynolds number [1/m] (one value or a sweep).
        method: Thickness correlation.
        mach: Edge Mach number (eckert_reference only).
        tw_t0: Wall-to-stagnation temperature ratio (eckert_reference only).
        gamma: Ratio of specific heats.
        output: Optional Tecplot output path.
    """

    section_name = "boundary_layer_thickness"

    x: NonNegativeSweep
    re1: PositiveSweep
    method: Annotated[Literal[BOUNDARY_LAYER_THICKNESS_METHODS], NormalizedName] = (
        "blasius"
    )
    mach: PositiveSweep | None = None
    tw_t0: PositiveSweep | None = None
    gamma: Gamma = 1.4
    output: Path | None = None

    @model_validator(mode="after")
    def _check_reference_temperature_inputs(self) -> BoundaryLayerThicknessConfig:
        """The reference-temperature method needs mach and tw_t0."""

        # check inputs required by the reference-temperature method
        if self.method == "eckert_reference":
            if self.mach is None:
                raise ValueError("mach is required for method='eckert_reference'")
            if self.tw_t0 is None:
                raise ValueError("tw_t0 is required for method='eckert_reference'")

        return self
