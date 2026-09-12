"""beautify_bash - a code formatter for bash and zsh scripts.

Originally written by Paul Lutus; revived with a package layout, a Typer
command line interface and dialect support.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _version

from .beautifier import (
    Beautifier,
    BeautifyBash,
    FormatError,
    FormatResult,
    beautify_string,
)
from .dialects import BASH, DIALECTS, ZSH, Dialect, detect_dialect, get_dialect

try:
    #: Single source of truth: the ``version`` field in ``pyproject.toml``.
    __version__ = _version("beautify-bash")
except PackageNotFoundError:  # pragma: no cover - running from an unbuilt tree
    __version__ = "0.0.0+unknown"
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
