"""Command line interface built on Typer."""

from __future__ import annotations

import difflib
import sys
from enum import Enum
from pathlib import Path
from typing import List, Optional

import typer

from . import __version__
from .beautifier import Beautifier
from .dialects import DEFAULT_DIALECT, Dialect, detect_dialect, get_dialect

__all__ = ["DialectChoice", "app", "main"]


class DialectChoice(str, Enum):
    """``--dialect`` values; ``auto`` inspects the shebang and file name."""

    auto = "auto"
    bash = "bash"
    zsh = "zsh"


app = typer.Typer(
    add_completion=True,
    context_settings={"help_option_names": ["-h", "--help"]},
    help="Re-indent bash and zsh scripts.",
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"beautify-bash {__version__}")
        raise typer.Exit


def _resolve_dialect(choice: DialectChoice, data: str, name: str) -> Dialect:
    if choice is DialectChoice.auto:
        return detect_dialect(data, name, DEFAULT_DIALECT)
    return get_dialect(choice.value)


def _diff(before: str, after: str, name: str) -> str:
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"a/{name}",
            tofile=f"b/{name}",
        )
    )


@app.command(no_args_is_help=True)
def main(
    files: List[str] = typer.Argument(
        ...,
        metavar="FILES...",
        help='Scripts to format; "-" reads standard input.',
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        metavar="PATH",
        help='Write the result to PATH ("-" for stdout) instead of stdout.',
    ),
    write: bool = typer.Option(
        False,
        "--write",
        "-w",
        help="Rewrite each input file in place instead of printing.",
    ),
    indent_size: int = typer.Option(
        2, "--indent", "-i", min=0, help="Indentation width per level."
    ),
    use_tabs: bool = typer.Option(
        False, "--tabs/--spaces", help="Indent with tab characters."
    ),
    dialect: DialectChoice = typer.Option(
        DialectChoice.auto, "--dialect", "-d", help="Shell dialect to assume."
    ),
    check: bool = typer.Option(
        False, "--check", help="Write nothing; exit 1 if a file would change."
    ),
    show_diff: bool = typer.Option(
        False, "--diff", help="Print a unified diff instead of the result."
    ),
    backup: bool = typer.Option(
        True, "--backup/--no-backup", help='With -w, keep the original as "FILE~".'
    ),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress progress notes."),
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-V",
        callback=_version_callback,
        is_eager=True,
        help="Show the version and exit.",
    ),
) -> None:
    """Print each formatted FILE to standard output.

    Use ``-w`` to rewrite the files in place, or ``-o PATH`` to collect the
    result in one file.  ``--check`` and ``--diff`` never write anything.
    """
    _reject_conflicting_modes(files, output, write, check, show_diff)

    exit_code = 0
    collected: List[str] = []

    for name in files:
        try:
            data = sys.stdin.read() if name == "-" else Path(name).read_text("utf-8")
        except OSError as exc:
            typer.echo(f"beautify-bash: {name}: {exc.strerror}", err=True)
            exit_code = 2
            continue

        label = "(stdin)" if name == "-" else name
        beautifier = Beautifier(
            indent_char="\t" if use_tabs else " ",
            indent_size=1 if use_tabs else indent_size,
            backup=backup,
        )
        result = beautifier.format(data, _resolve_dialect(dialect, data, label))

        for error in result.errors:
            typer.echo(error.render(label), err=True)
            exit_code = max(exit_code, 1)

        changed = result.text != data
        if changed and (check or show_diff):
            exit_code = max(exit_code, 1)

        if show_diff:
            typer.echo(_diff(data, result.text, label), nl=False)
        elif check:
            if changed and not quiet:
                typer.echo(f"would reformat {label}", err=True)
        elif write:
            if changed:
                if backup:
                    Path(f"{name}~").write_text(data, encoding="utf-8")
                Path(name).write_text(result.text, encoding="utf-8")
                if not quiet:
                    typer.echo(f"reformatted {name}", err=True)
        elif output is not None and output != "-":
            collected.append(result.text)
        else:
            typer.echo(result.text, nl=False)

    if collected:
        assert output is not None  # guaranteed by the branch that filled `collected`
        try:
            Path(output).write_text("".join(collected), encoding="utf-8")
        except OSError as exc:
            typer.echo(f"beautify-bash: {output}: {exc.strerror}", err=True)
            exit_code = max(exit_code, 2)

    raise typer.Exit(exit_code)


def _reject_conflicting_modes(
    files: List[str],
    output: Optional[str],
    write: bool,
    check: bool,
    show_diff: bool,
) -> None:
    """Fail early on option combinations that cannot all be honoured."""
    if write and output is not None:
        raise typer.BadParameter("--write cannot be combined with --output.")
    if write and "-" in files:
        raise typer.BadParameter("--write cannot rewrite standard input.")
    if check and show_diff:
        raise typer.BadParameter("--check cannot be combined with --diff.")
    for flag, name in ((check, "--check"), (show_diff, "--diff")):
        if flag and write:
            raise typer.BadParameter(f"{name} cannot be combined with --write.")
        if flag and output is not None:
            raise typer.BadParameter(f"{name} cannot be combined with --output.")


if __name__ == "__main__":  # pragma: no cover
    app()
