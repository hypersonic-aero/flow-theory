"""Configuration model for the [entropy_layer_estimate] section."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

from pathlib import Path

from .section import Gamma, NonNegativeSweep, PositiveSweep, SectionConfig


# --------------------------------------------------
# typed configuration
# --------------------------------------------------
class EntropyLayerEstimateConfig(SectionConfig):
    """Validated inputs for an entropy-layer thickness estimate.

    Attributes:
        x: Streamwise station [m] (one value or a sweep).
        mach: Freestream Mach number (one value or a sweep).
        nose_radius: Nose radius [m] (one value or a sweep).
        gamma: Ratio of specific heats.
        output: Optional Tecplot output path.
    """

    section_name = "entropy_layer_estimate"

    x: NonNegativeSweep
    mach: PositiveSweep
    nose_radius: PositiveSweep
    gamma: Gamma = 1.4
    output: Path | None = None
