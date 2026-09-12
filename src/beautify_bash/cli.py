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
        help='Scripts to format; "-" reads stdin and writes stdout.',
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
        False, "--check", help="Do not write; exit 1 if a file would change."
    ),
    show_diff: bool = typer.Option(
        False, "--diff", help="Print a unified diff instead of writing."
    ),
    backup: bool = typer.Option(
        True, "--backup/--no-backup", help='Keep the original as "FILE~".'
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
    """Format each FILE in place, or stream stdin to stdout for ``-``."""
    dry_run = check or show_diff
    exit_code = 0

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
        if name == "-":
            if show_diff:
                typer.echo(_diff(data, result.text, label), nl=False)
            elif not check:
                typer.echo(result.text, nl=False)
            if check and changed:
                exit_code = max(exit_code, 1)
            continue

        if show_diff:
            typer.echo(_diff(data, result.text, label), nl=False)
        elif check:
            if changed and not quiet:
                typer.echo(f"would reformat {name}")
        elif changed:
            if backup:
                Path(f"{name}~").write_text(data, encoding="utf-8")
            Path(name).write_text(result.text, encoding="utf-8")
            if not quiet:
                typer.echo(f"reformatted {name}")

        if dry_run and changed:
            exit_code = max(exit_code, 1)

    raise typer.Exit(exit_code)


if __name__ == "__main__":  # pragma: no cover
    app()
