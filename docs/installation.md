# Installation

## From PyPI

```bash
pip install flow-theory
```

To upgrade an existing installation:

```bash
pip install --upgrade flow-theory
```

## From Source

```bash
git clone https://github.com/hypersonic-aero/flow-theory.git
cd flow-theory
pip install -e .
```

## Optional Extras

For development (tests, linting, and docs):

```bash
pip install -e ".[dev]"
```

Includes:

- [pytest](https://docs.pytest.org/) and [pytest-cov](https://pytest-cov.readthedocs.io/) for testing
- [ruff](https://docs.astral.sh/ruff/) for linting
- [mkdocstrings](https://mkdocstrings.github.io/) for API reference generation
- [zensical](https://zensical.org/) for building the documentation

## Verify Installation

```bash
flow-theory --version
```

Or in Python:

```python
import flow_theory
print(flow_theory.__version__)
```
