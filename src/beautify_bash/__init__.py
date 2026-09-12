"""beautify_bash - a code formatter for bash and zsh scripts.

Originally written by Paul Lutus; revived with a package layout, a Typer
command line interface and dialect support.
"""

from __future__ import annotations

from .beautifier import (
    Beautifier,
    BeautifyBash,
    FormatError,
    FormatResult,
    beautify_string,
)
from .dialects import BASH, DIALECTS, ZSH, Dialect, detect_dialect, get_dialect

__version__ = "2.0.0"
#: Historical spelling of the version constant.
PVERSION = __version__

__all__ = [
    "BASH",
    "DIALECTS",
    "PVERSION",
    "ZSH",
    "Beautifier",
    "BeautifyBash",
    "Dialect",
    "FormatError",
    "FormatResult",
    "__version__",
    "beautify_string",
    "detect_dialect",
    "get_dialect",
]
