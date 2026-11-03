"""Configuration model for the [transition] section."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal

from .section import NormalizedName, PositiveSweep, SectionConfig


# --------------------------------------------------
# typed configuration
# --------------------------------------------------
class TransitionConfig(SectionConfig):
    """Validated inputs for a transition-location calculation.

    Attributes:
        mach: Edge Mach number (one value or a sweep).
        re1: Unit Reynolds number [1/m] (one value or a sweep).
        tw_te: Wall-to-edge temperature ratio (one value or a sweep).
        method: Transition-onset criterion.
        output: Optional Tecplot output path.
    """

    section_name = "transition"

    mach: PositiveSweep
    re1: PositiveSweep
    tw_te: PositiveSweep
    method: Annotated[Literal["van_driest_blumer"], NormalizedName] = (
        "van_driest_blumer"
    )
    output: Path | None = None
