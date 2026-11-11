# flow_theory

Theoretical estimates for high-speed aerodynamics.

[![Test](https://github.com/hypersonic-aero/flow-theory/actions/workflows/test.yml/badge.svg)](https://github.com/hypersonic-aero/flow-theory/actions/workflows/test.yml)
[![PyPI](https://img.shields.io/pypi/v/flow-theory)](https://pypi.org/project/flow-theory/)
[![Docs](https://img.shields.io/badge/docs-zensical-blue)](https://hypersonic-aero.github.io/flow-theory/)
[![License](https://img.shields.io/badge/license-GPL--3.0--or--later-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-≥3.11-blue.svg)](https://www.python.org/downloads/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

## Install

```bash
pip install flow-theory
```

## Quick Start

```python
import flow_theory
```

## Documentation

Full documentation: https://hypersonic-aero.github.io/flow-theory

## Citation

If you use `flow_theory` in your research, please cite it:

```bibtex
@software{flow_theory,
  author = {Hader, Christoph},
  title = {flow\_theory: Theoretical Estimates for High-Speed Aerodynamics},
  url = {https://github.com/hypersonic-aero/flow-theory},
  year = {2026}
}
```

## Code Style

This project follows established Python community conventions so that
contributors can focus on the physics rather than inventing formatting rules.

| Convention | What it covers | Reference |
|---|---|---|
| [PEP 8](https://peps.python.org/pep-0008/) | Code formatting, naming, whitespace | Python standard style guide |
| [PEP 257](https://peps.python.org/pep-0257/) | Docstring structure (triple-quoted, imperative mood) | Python standard docstring conventions |
| [Google style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) | Docstring sections (`Args`, `Returns`, `Raises`) | Google Python style guide |
| [Ruff](https://docs.astral.sh/ruff/) | Automated linting and formatting | Enforces PEP 8 compliance automatically |
| [typing / TYPE_CHECKING](https://docs.python.org/3/library/typing.html#typing.TYPE_CHECKING) | Type hints for IDE support and static analysis | Python standard library |

## Releasing

This project uses [Semantic Versioning](https://semver.org/) (`vMAJOR.MINOR.PATCH`):

- **MAJOR** (`v1.0.0`, `v2.0.0`): Breaking API changes
- **MINOR** (`v0.3.0`, `v0.4.0`): New features, backward-compatible
- **PATCH** (`v0.3.1`, `v0.3.2`): Bug fixes, minor corrections

To publish a new version to [PyPI](https://pypi.org/project/flow-theory/):

1. Commit and push to `main`
2. Tag and push:
   ```bash
   git tag -a vMAJOR.MINOR.PATCH -m "Release vMAJOR.MINOR.PATCH"
   git push origin vMAJOR.MINOR.PATCH
   ```

