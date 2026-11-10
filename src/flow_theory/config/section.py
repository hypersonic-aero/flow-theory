"""Base model and shared field types for flow-theory config sections.

Every calculator reads one [section] of a TOML file (or the same values from
direct CLI options) into a frozen pydantic model. The model rejects unknown
keys, checks types and ranges, and reports every problem at once as one
``key: message`` line each.

Paths in a config file (flow_conditions, output, a geometry file) are relative to
the config file's folder, so `flow-theory <calculator> run -c case/<file>.toml`
reads and writes the case's files from any folder. Paths given as direct CLI
options are relative to the folder the command runs in.
"""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

import math
from pathlib import Path
from typing import Annotated, Any, ClassVar, Self

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    PlainValidator,
    ValidationError,
)

from .read_config import read_config


# --------------------------------------------------
# helpers for the shared field types
# --------------------------------------------------
def _normalize_name(value: Any) -> Any:
    """Selector names: lowercase without surrounding spaces; empty means not given."""

    # normalize strings, leave everything else to the type check
    if isinstance(value, str):
        cleaned = value.strip().lower()
        return cleaned or None

    return value


def _parse_sweep(value: Any, allow_zero: bool) -> float | list[float]:
    """A finite value or a non-empty list of them, positive (or zero, if allowed).

    Args:
        value: One number, or a list of numbers swept case by case.
        allow_zero: Whether zero is a valid value.

    Returns:
        The value as a float, or the list as a list of floats.

    Raises:
        ValueError: If the value isn't a number or list of numbers, or out of range.
    """

    # check the shape: one number, or a non-empty list of numbers (bools aren't numbers)
    is_number = isinstance(value, (int, float)) and not isinstance(value, bool)
    if is_number:
        items = [value]
    elif isinstance(value, list) and value:
        items = value
    else:
        raise ValueError("must be a number or a non-empty list of numbers")

    # check every value
    checked: list[float] = []
    for item in items:
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise ValueError(f"must be a number or a list of numbers, got {item!r}")
        number = float(item)
        if not math.isfinite(number):
            raise ValueError(f"must be finite, got {item}")
        if number < 0.0 or (number == 0.0 and not allow_zero):
            bound = "non-negative" if allow_zero else "positive"
            raise ValueError(f"must be {bound}, got {item}")
        checked.append(number)

    # a scalar stays a scalar
    if is_number:
        return checked[0]

    return checked


def _parse_positive_sweep(value: Any) -> float | list[float]:
    """A positive, finite value, or a non-empty list of them."""
    return _parse_sweep(value, allow_zero=False)


def _parse_non_negative_sweep(value: Any) -> float | list[float]:
    """A non-negative, finite value, or a non-empty list of them."""
    return _parse_sweep(value, allow_zero=True)


# --------------------------------------------------
# shared field types
# --------------------------------------------------

# a positive, finite number (lengths, Reynolds numbers, ratios)
Positive = Annotated[float, Field(gt=0.0, allow_inf_nan=False)]

# a ratio of specific heats
Gamma = Annotated[float, Field(gt=1.0, allow_inf_nan=False)]

# sweepable inputs: one value, or a list swept case by case (the runners
# broadcast all sweeps of a section to a common length); one plain validator
# instead of a float | list union, so a wrong type gives one message, not one per branch
PositiveSweep = Annotated[float | list[float], PlainValidator(_parse_positive_sweep)]
NonNegativeSweep = Annotated[
    float | list[float], PlainValidator(_parse_non_negative_sweep)
]

# selector names (method, mode, ...) compared in lowercase, e.g. " Blasius " -> "blasius"
NormalizedName = BeforeValidator(_normalize_name)


# --------------------------------------------------
# base model for one config section
# --------------------------------------------------
class SectionConfig(BaseModel):
    """One [section] of a flow-theory config: unknown keys rejected, frozen after parsing."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    # TOML section name, e.g. "shock_shape" for [shock_shape]
    section_name: ClassVar[str]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Validate the section's values (TOML table or direct CLI options).

        Args:
            data: Keys and values of the section.

        Returns:
            The validated section.

        Raises:
            ValueError: Listing every invalid key, one per line.
        """

        # validate (pydantic's ValidationError reworded as one line per key)
        try:
            section = cls.model_validate(data)
        except ValidationError as error:
            raise ValueError(
                _format_validation_error(cls.section_name, error)
            ) from None

        return section

    @classmethod
    def from_file(cls, path: str | Path) -> Self:
        """Read and validate the section from a TOML config file.

        Every path in the section (also in a nested table, e.g. a geometry file) is
        resolved against the config file's folder; an absolute path stays as it is.

        Args:
            path: Config file path.

        Returns:
            The validated section, its paths resolved.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            ValueError: If the section is missing or invalid.
        """

        # read the file and pick this calculator's section
        cfg = read_config(path)
        if cls.section_name not in cfg:
            raise ValueError(f"{path} has no [{cls.section_name}] section")

        section = cls.from_dict(cfg[cls.section_name])

        # paths in the file are relative to the file's folder
        config_folder = Path(path).parent
        resolved = _resolve_paths(section, config_folder)

        return resolved


# --------------------------------------------------
# helper: paths relative to the config file
# --------------------------------------------------
def _resolve_paths(model: BaseModel, folder: Path) -> Any:
    """The model with every Path field (also in nested models) joined to folder.

    Joining keeps an absolute path as it is (folder / "/abs/x" is "/abs/x"), and
    fields that aren't paths (numbers, names, None) are left alone.

    Args:
        model: A validated section, or a model nested in one.
        folder: The config file's folder.

    Returns:
        A copy of the model with its paths resolved (the model is frozen).
    """

    # collect the fields to change: paths, and nested models with paths inside
    updates: dict[str, Any] = {}
    for name in type(model).model_fields:
        value = getattr(model, name)
        if isinstance(value, Path):
            updates[name] = folder / value
        elif isinstance(value, BaseModel):
            updates[name] = _resolve_paths(value, folder)

    # copy with the resolved values
    resolved = model.model_copy(update=updates)

    return resolved


# --------------------------------------------------
# helper: readable validation errors
# --------------------------------------------------
def _format_validation_error(section_name: str, error: ValidationError) -> str:
    """One ``key: message`` line per problem, without pydantic's URLs."""

    # collect a line per error, located by its (dotted) key; section-wide errors
    # (from cross-field checks) have no key
    lines = [f"invalid [{section_name}]:"]
    for item in error.errors():
        location = ".".join(str(part) for part in item["loc"])
        message = item["msg"].removeprefix("Value error, ")
        if location:
            lines.append(f"  {location}: {message}")
        else:
            lines.append(f"  {message}")

    return "\n".join(lines)
