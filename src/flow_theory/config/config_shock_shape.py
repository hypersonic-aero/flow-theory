"""Configuration model for the [shock_shape] section."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

import math
from pathlib import Path
from typing import Annotated, Any, Literal

from canonical_geometries.config import GeometryConfig
from pydantic import Field, model_validator

from flow_theory.geometry import fill_geometry_extent
from flow_theory.shock.shape import SHOCK_SHAPE_METHODS

from .section import NormalizedName, Positive, SectionConfig


# --------------------------------------------------
# typed configuration
# --------------------------------------------------
class ShockShapeConfig(SectionConfig):
    """Validated inputs for a shock-shape calculation.

    Attributes:
        flow_conditions: FlowState JSON with the freestream (Mach number, gamma).
        geometry: Body geometry, ending at x_e (see flow_theory.geometry.parse_geometry).
        x_e: Streamwise end of the shock and body [m], measured from the nose tip.
        method: Shock-shape correlation name (billig, billig_blended).
        n_points: Number of points on the shock and on the body.
        blend_nose_radii: billig_blended only: blend length [nose radii].
        output: Output file: .csv (shock x, y) or Tecplot ASCII (any other extension).
    """

    section_name = "shock_shape"

    flow_conditions: Path
    geometry: GeometryConfig
    x_e: Positive
    method: Annotated[Literal[SHOCK_SHAPE_METHODS], NormalizedName] = "billig"
    n_points: int = Field(default=100, ge=2)
    blend_nose_radii: Positive | None = None
    output: Path | None = None

    @model_validator(mode="before")
    @classmethod
    def _fill_geometry_extent(cls, data: Any) -> Any:
        """The body ends at x_e: fill the geometry table's extent before it is validated."""

        # only raw dicts (TOML tables, direct options) need filling
        if not isinstance(data, dict):
            return data
        table = data.get("geometry")
        x_e = data.get("x_e")

        # read the body: a [shock_shape.geometry] table that ends at x_e
        if isinstance(table, str):
            raise ValueError(
                "geometry must be a [shock_shape.geometry] table "
                "(canonical-geometries' [geometry] contract; x_e sets the body's extent)"
            )

        # fill in the extent once x_e is a usable number (otherwise x_e's own error is reported)
        x_e_is_number = isinstance(x_e, (int, float)) and not isinstance(x_e, bool)
        x_e_is_usable = x_e_is_number and math.isfinite(x_e) and x_e > 0.0
        if isinstance(table, dict) and x_e_is_usable:
            filled = dict(data)
            filled["geometry"] = fill_geometry_extent(
                table, float(x_e), label="shock_shape.geometry"
            )
            return filled

        return data
