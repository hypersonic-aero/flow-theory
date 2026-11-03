"""Shared helpers for the section runners."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

import numpy as np


# --------------------------------------------------
# public helpers
# --------------------------------------------------
def as_float_list(value, key_name: str) -> list[float]:
    """Coerce scalar/list config values to list[float] for sweep broadcasting."""

    if isinstance(value, list):
        return [float(v) for v in value]
    if value is None:
        raise ValueError(f"Missing required key: {key_name}")
    return [float(value)]


def broadcast_sweep(**params: list[float]) -> dict[str, np.ndarray]:
    """Broadcast config sweep lists to a common length.

    Every parameter must be a non-empty list of length 1 or length N,
    for a single common N. Length-1 parameters are repeated to length N.

    Args:
        **params: One list of float values per config key.

    Returns:
        Dict mapping parameter names to length-N numpy arrays.

    Raises:
        ValueError: If parameter lengths are incompatible.
    """

    # determine the common sweep length from the longest input list
    n_cases = max(len(values) for values in params.values())

    # validate that every input list is length 1 or length n_cases
    for name, values in params.items():
        if len(values) not in (1, n_cases):
            raise ValueError(
                f"[{name}] has {len(values)} values, expected 1 or {n_cases} "
                "to match the sweep length"
            )

    # build aligned arrays for all keys
    swept: dict[str, np.ndarray] = {}
    for name, values in params.items():
        if len(values) == 1:
            swept[name] = np.full(n_cases, values[0], dtype=float)
        else:
            swept[name] = np.asarray(values, dtype=float)

    return swept
