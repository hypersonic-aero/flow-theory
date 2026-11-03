"""The `examples` subcommand shared by the calculators that ship examples."""

# --------------------------------------------------
# load necessary modules
# --------------------------------------------------
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Annotated

import typer

from flow_theory.io.examples import copy_example, list_examples


# --------------------------------------------------
# public API
# --------------------------------------------------
def build_examples_command(calculator: str, command_name: str) -> Callable[..., None]:
    """Build the `examples` subcommand of one calculator.

    Args:
        calculator: Config section name, e.g. "shock_shape" (the examples folder).
        command_name: CLI name, e.g. "shock-shape" (for the printed next steps).

    Returns:
        The command function to register as ``<calculator_app>.command("examples")``.
    """

    def cmd_examples(
        name: Annotated[
            str | None,
            typer.Argument(
                help="Example to copy into the current folder. Omit to list the examples."
            ),
        ] = None,
        force: Annotated[
            bool,
            typer.Option(
                "--force", "-f", help="Overwrite files of the same name in this folder."
            ),
        ] = False,
    ) -> None:
        """List the bundled examples, or copy one into the current folder to run."""

        # list: name and description of every example
        examples = list_examples(calculator)
        if name is None:
            width = max(len(example_name) for example_name in [*examples, "<name>"])
            typer.echo("")
            typer.echo(f"  {'<name>':<{width}}  description")
            typer.echo(f"  {'-' * width}  {'-' * 11}")
            for example_name, description in examples.items():
                typer.echo(f"  {example_name:<{width}}  {description}")
            typer.echo("")
            typer.echo("command sequence:")
            typer.echo("  - check out the example")
            typer.echo(f"     flow-theory {command_name} examples <name>")
            typer.echo("  - run the example")
            typer.echo(f"     flow-theory {command_name} run")
            typer.echo("")
            return

        # copy the example into the current folder
        try:
            written = copy_example(calculator, name, Path("."), force=force)
        except KeyError:
            known = ", ".join(examples)
            typer.echo(f"error: unknown example {name!r}; available: {known}", err=True)
            raise typer.Exit(1) from None
        except FileExistsError as error:
            typer.echo(f"error: {error}", err=True)
            raise typer.Exit(1) from None

        # report the files and the next step
        for path in written:
            typer.echo(f"wrote {path}")
        typer.echo(f"then: flow-theory {command_name} run")

    return cmd_examples
