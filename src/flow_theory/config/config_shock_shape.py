"""Configuration model for the [shock_shape] section."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any, Literal, Self

from canonical_geometries.config import GeometryConfig
from pydantic import BaseModel, ConfigDict, Discriminator, Field, Tag, field_validator

from flow_theory.shock.shape import SHOCK_SHAPE_METHODS

from .section import NormalizedName, Positive, SectionConfig


# --------------------------------------------------
# the body: a geometry file, or the body's keys
# --------------------------------------------------
class GeometryFile(BaseModel):
    """[shock_shape.geometry] naming a geometry file: the body is read from it.

    Attributes:
        file: Geometry file (canonical-geometries' geometry.toml, written by
            `geometry <type> init`; grid-generator reads the same file). From a
            config file, a relative path is resolved against its folder.
    """

    # reject misspelled keys
    model_config = ConfigDict(extra="forbid", frozen=True)

    file: Path


def _geometry_form(value: Any) -> str:
    """Which form a [shock_shape.geometry] table has: "file", or "body" (the body's keys)."""

    # a table: with a file key it names a geometry file, otherwise it is the body itself
    if isinstance(value, dict):
        if "file" in value:
            return "file"
        return "body"

    # an already validated model (e.g. a config built in Python)
    if isinstance(value, GeometryFile):
        return "file"

    return "body"


# [shock_shape.geometry]: a geometry file (file = "geometry.toml"), or the body's keys
# right in the table (canonical-geometries' [geometry] contract, length included, the
# same keys as in geometry.toml); the table's form picks the model it is checked against
GeometrySource = Annotated[
    Annotated[GeometryFile, Tag("file")] | Annotated[GeometryConfig, Tag("body")],
    Discriminator(_geometry_form),
]

# without a [shock_shape.geometry] table: the geometry file next to the config
DEFAULT_GEOMETRY = GeometryFile(file=Path("geometry.toml"))


# --------------------------------------------------
# typed configuration
# --------------------------------------------------
class ShockShapeConfig(SectionConfig):
    """Validated inputs for a shock-shape calculation.

    Attributes:
        flow_conditions: FlowState JSON with the freestream (Mach number, gamma).
        geometry: The body: a geometry file (GeometryFile; canonical-geometries'
            geometry.toml, the file grid-generator reads too), or the body itself
            (canonical-geometries' [geometry] contract, length included). Default:
            geometry.toml next to the config.
        x_e: Streamwise end of the shock [m], measured from the nose tip; at most the
            body's end. None (left out): the body's end.
        method: Shock-shape correlation name (billig, billig_blended).
        n_points: Number of points on the shock and on the body.
        blend_nose_radii: billig_blended only: blend length [nose radii].
        output: Output file: .csv (shock x, y) or Tecplot ASCII (any other extension).
    """

    section_name = "shock_shape"

    flow_conditions: Path
    geometry: GeometrySource = DEFAULT_GEOMETRY
    x_e: Positive | None = None
    method: Annotated[Literal[SHOCK_SHAPE_METHODS], NormalizedName] = "billig"
    n_points: int = Field(default=100, ge=2)
    blend_nose_radii: Positive | None = None
    output: Path | None = None

    @field_validator("geometry", mode="before")
    @classmethod
    def _geometry_has_one_form(cls, value: Any) -> Any:
        """A [shock_shape.geometry] table names a geometry file or holds the body, not both."""

        # models built in Python pass on to the type check
        if isinstance(value, BaseModel):
            return value

        # check: a table
        if not isinstance(value, dict):
            raise ValueError(
                'must be a [shock_shape.geometry] table: file = "geometry.toml", or the '
                "body's keys (type, nose_radius, length, ...)"
            )

        # check: one form, the file or the body's keys
        body_keys = [key for key in value if key != "file"]
        if "file" in value and body_keys:
            raise ValueError(
                f"give either file or the body's keys, not both (got file and "
                f"{', '.join(body_keys)})"
            )

        return value

    @classmethod
    def from_file(cls, path: str | Path) -> Self:
        """Read the section from a config file; a geometry file is relative to its folder.

        Args:
            path: Config file path.

        Returns:
            The validated section, its geometry file (if it names one) resolved.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            ValueError: If the section is missing or invalid.
        """

        # read and validate the section
        section = super().from_file(path)

        # resolve a geometry file next to the config file (an absolute path stays); a
        # body given by its keys needs nothing
        resolved = section
        if isinstance(section.geometry, GeometryFile):
            geometry_file = GeometryFile(file=Path(path).parent / section.geometry.file)
            resolved = section.model_copy(update={"geometry": geometry_file})

        return resolved
