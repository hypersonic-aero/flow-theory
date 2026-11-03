"""Configuration model for the [entropy_layer_swallowing] section."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

from pathlib import Path

from .section import Gamma, PositiveSweep, SectionConfig


# --------------------------------------------------
# typed configuration
# --------------------------------------------------
class EntropyLayerSwallowingConfig(SectionConfig):
    """Validated inputs for an entropy-layer swallowing calculation.

    Attributes:
        mach: Freestream Mach number (one value or a sweep).
        re1: Unit Reynolds number [1/m] (one value or a sweep).
        nose_radius: Nose radius [m] (one value or a sweep).
        tw_t0: Wall-to-stagnation temperature ratio (one value or a sweep).
        gamma: Ratio of specific heats.
        output: Optional Tecplot output path.
    """

    section_name = "entropy_layer_swallowing"

    mach: PositiveSweep
    re1: PositiveSweep
    nose_radius: PositiveSweep
    tw_t0: PositiveSweep
    gamma: Gamma = 1.4
    output: Path | None = None
