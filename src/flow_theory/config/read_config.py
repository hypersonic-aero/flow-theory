"""Read a flow-theory TOML configuration file."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any


# --------------------------------------------------
# public API
# --------------------------------------------------
def read_config(path: str | Path) -> dict[str, Any]:
    """Load a TOML config file into a plain dict of sections.

    Args:
        path: Config file path.

    Returns:
        The parsed TOML, one table per section.

    Raises:
        FileNotFoundError: If the config file doesn't exist.
    """

    # convert to Path object
    cfg_path = Path(path)

    # check: the file exists
    if not cfg_path.exists():
        raise FileNotFoundError(f"Config file not found: {cfg_path}")

    # read and parse config file as TOML
    with cfg_path.open("rb") as stream:
        cfg = tomllib.load(stream)

    return cfg
