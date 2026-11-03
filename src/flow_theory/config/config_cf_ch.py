"""Configuration model for the [cf_ch] section."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

import math
from pathlib import Path
from typing import Annotated, Literal

import numpy as np
from pydantic import BeforeValidator, ConfigDict, model_validator

from ..cf_ch import VALID_MODES
from ..cf_ch.cf_laminar import LAMINAR_METHODS
from ..cf_ch.cf_turbulent import TURBULENT_METHODS
from .section import NormalizedName, Positive, SectionConfig


# --------------------------------------------------
# private helpers
# --------------------------------------------------
def _resolve_x_points(spec: object) -> np.ndarray:
    """Turn a scalar or sweep specification into a 1D point array.

    Supported forms:
    - 1.0 -> single point
    - [xs, xe, nx] -> linear sweep with count
    - [xs, xe, dx] -> linear sweep with spacing

    Args:
        spec: Scalar or item sequence describing the x locations.

    Returns:
        1D numpy array of x locations.

    Raises:
        ValueError: If the specification is invalid.
    """

    # validate that the required x specification was provided
    if spec is None:
        raise ValueError("Missing required key: [cf_ch] x")

    # build the final value array and return once at the end
    values: np.ndarray

    # convert a scalar specification to a single-point array
    if isinstance(spec, (int, float)):
        value = float(spec)

        # ensure that the single point is non-negative
        if value < 0.0:
            raise ValueError("[cf_ch] x must be non-negative")

        values = np.asarray([value], dtype=float)
    else:
        # validate that a sweep specification is a three-item sequence
        if not isinstance(spec, (list, tuple)):
            raise ValueError(
                "Invalid [cf_ch] x type. Use a scalar value, "
                "[xs, xe, nx], or [xs, xe, dx]"
            )

        if len(spec) != 3:
            raise ValueError(
                "[cf_ch] x list must have exactly 3 entries: "
                "[xs, xe, nx] or [xs, xe, dx]"
            )

        # convert the start, end, and sweep arguments to numeric values
        try:
            start = float(spec[0])
        except (TypeError, ValueError):
            raise ValueError("[cf_ch] x[0] (start) must be a numeric value")

        try:
            end = float(spec[1])
        except (TypeError, ValueError):
            raise ValueError("[cf_ch] x[1] (end) must be a numeric value")

        try:
            sweep_arg = float(spec[2])
        except (TypeError, ValueError):
            raise ValueError("[cf_ch] x[2] must be a numeric value")

        # validate the sweep bounds and third argument
        if start < 0.0:
            raise ValueError("[cf_ch] x[0] (start) must be non-negative")

        if end <= start:
            raise ValueError("[cf_ch] x[1] (end) must be greater than start")

        if sweep_arg <= 0.0:
            raise ValueError("[cf_ch] x[2] must be positive")

        # interpret an integer-valued third argument as a point count
        sweep_arg_rounded = int(round(sweep_arg))
        is_count = abs(sweep_arg - sweep_arg_rounded) < 1e-12

        if is_count:
            if sweep_arg_rounded < 2:
                raise ValueError(
                    "[cf_ch] x interpreted as [start, stop, count], "
                    "and count must be at least 2"
                )

            values = np.linspace(start, end, sweep_arg_rounded, dtype=float)
        else:
            # generate points using the requested spacing
            step = sweep_arg
            count = int(math.floor((end - start) / step))
            values = start + step * np.arange(count + 1, dtype=float)

            # append the exact endpoint when the spacing does not land on it
            endpoint_tolerance = max(1e-14, 1e-12 * end)
            endpoint_is_present = np.isclose(
                values[-1],
                end,
                rtol=0.0,
                atol=endpoint_tolerance,
            )
            if not endpoint_is_present:
                values = np.append(values, end)

    return values


# --------------------------------------------------
# typed configuration
# --------------------------------------------------
class CfChConfig(SectionConfig):
    """Validated inputs for a cf/ch calculation.

    Attributes:
        flow_conditions: FlowState JSON with the edge conditions.
        x: Streamwise stations [m]: given as one value, [xs, xe, nx] or [xs, xe, dx],
            stored as the resolved point array.
        mode: "laminar", "turbulent", or None for both.
        method: Correlation name, or None for all methods of the selected mode(s).
        wall_type: "adiabatic" or "isothermal".
        temp_wall: Wall temperature [K] (isothermal walls).
        output: Optional Tecplot output path.
    """

    # the resolved x stations are a numpy array
    model_config = ConfigDict(arbitrary_types_allowed=True)

    section_name = "cf_ch"

    flow_conditions: Path
    x: Annotated[np.ndarray, BeforeValidator(_resolve_x_points)]
    mode: Annotated[Literal[VALID_MODES] | None, NormalizedName] = None
    method: Annotated[
        Literal[LAMINAR_METHODS + TURBULENT_METHODS] | None, NormalizedName
    ] = None
    wall_type: Annotated[Literal["adiabatic", "isothermal"], NormalizedName] = (
        "adiabatic"
    )
    temp_wall: Positive | None = None
    output: Path | None = None

    @model_validator(mode="after")
    def _check_wall_temperature(self) -> CfChConfig:
        """An isothermal wall needs its temperature."""

        # ensure temp_wall is set when wall_type is isothermal
        if self.wall_type == "isothermal" and self.temp_wall is None:
            raise ValueError("temp_wall is required when wall_type='isothermal'")

        return self
