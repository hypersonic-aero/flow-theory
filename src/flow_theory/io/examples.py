"""Bundled example cases for the flow-theory calculators.

Each example is a folder under ``flow_theory/examples/<calculator>/`` holding
the files of one case: the calculator's config (named like run's default, e.g.
``shock_shape.toml``) and the files it reads (e.g. ``flow_conditions.json``).
The folder name is the example's name and the first text line of the config is
its description, so the folders are the registry: adding an example means
adding a folder.
"""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path


# --------------------------------------------------
# helpers
# --------------------------------------------------
def _calculator_root(calculator: str) -> Traversable:
    """Folder of one calculator's examples inside the installed package."""
    return files("flow_theory") / "examples" / calculator


def _description(config_text: str) -> str:
    """First text line of a config's header comment (dividers skipped)."""

    # walk the leading comment block
    for line in config_text.splitlines():
        stripped = line.strip()

        # the header ends at the first line that isn't a comment
        if stripped and not stripped.startswith("#"):
            break

        # skip blank comment lines and dividers like "# -----"
        text = stripped.lstrip("#").strip()
        if text and set(text) - set("-=#"):
            return text

    return ""


# --------------------------------------------------
# public API
# --------------------------------------------------
def list_examples(calculator: str) -> dict[str, str]:
    """Return a name -> description mapping of one calculator's examples.

    Args:
        calculator: Config section name of the calculator, e.g. "shock_shape".

    Returns:
        Dict of {name: description}, sorted by name (empty without examples).
    """

    # a calculator without examples has no folder
    root = _calculator_root(calculator)
    if not root.is_dir():
        return {}

    # every folder with the calculator's config is an example
    examples: dict[str, str] = {}
    config_name = f"{calculator}.toml"
    for folder in sorted(root.iterdir(), key=lambda item: item.name):
        config = folder / config_name
        if folder.is_dir() and config.is_file():
            examples[folder.name] = _description(config.read_text(encoding="utf-8"))

    return examples


def copy_example(
    calculator: str, name: str, destination: str | Path, force: bool = False
) -> list[Path]:
    """Copy one example's files into a folder (e.g. the current one).

    Args:
        calculator: Config section name of the calculator, e.g. "shock_shape".
        name: Example name (see list_examples).
        destination: Folder to copy the files into (created if missing).
        force: Overwrite files of the same name in the folder.

    Returns:
        The paths of the written files.

    Raises:
        KeyError: If the calculator has no example of that name.
        FileExistsError: If a file of the example already exists there and force
            is False (nothing is written then).
    """

    # check: a known example
    if name not in list_examples(calculator):
        raise KeyError(name)

    # the example's files
    source = _calculator_root(calculator) / name
    items = sorted(
        (entry for entry in source.iterdir() if entry.is_file()),
        key=lambda entry: entry.name,
    )

    # check: don't overwrite the user's files unless asked to (before writing any)
    destination = Path(destination)
    existing = [item.name for item in items if (destination / item.name).exists()]
    if existing and not force:
        raise FileExistsError(
            f"would overwrite {', '.join(existing)} (use --force to overwrite)"
        )

    # copy every file of the example folder
    destination.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for item in items:
        target = destination / item.name
        target.write_bytes(item.read_bytes())
        written.append(target)

    return written
