"""Shell dialect definitions.

A :class:`Dialect` describes the keywords that open and close an indentation
block for a given shell.  The beautifier is otherwise dialect agnostic, so
adding a new shell is a matter of adding a :class:`Dialect` instance here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Optional, Pattern, Tuple

__all__ = [
    "BASH",
    "DIALECTS",
    "ZSH",
    "Dialect",
    "command_position_pattern",
    "detect_dialect",
    "get_dialect",
]


#: A shell reserved word only acts as a keyword in *command position*: at the
#: start of the line or right after one of these separators.  Without this,
#: ``echo done`` would dedent the script.
_COMMAND_POSITION = r"(?:\A|[;&|(){}])\s*"


def _keyword_pattern(keywords: Tuple[str, ...], trailer: str) -> Pattern[str]:
    """Build a regex matching any of ``keywords`` used as a reserved word."""
    alternation = "|".join(re.escape(word) for word in keywords)
    return re.compile(rf"{_COMMAND_POSITION}(?:{alternation})(?:{trailer})")


def command_position_pattern(keyword: str) -> Pattern[str]:
    """Regex matching a single ``keyword`` used as a reserved word."""
    return _keyword_pattern((keyword,), r";|\)|\||\Z|\s")


@dataclass(frozen=True)
class Dialect:
    """Indentation rules for one shell dialect."""

    name: str
    #: Keywords that open a block (``then``, ``do``, ...).
    open_keywords: Tuple[str, ...]
    #: Keywords that close a block (``fi``, ``done``, ...).
    close_keywords: Tuple[str, ...]
    #: Keywords printed one level to the left without changing the running
    #: level (``else``, ``elif``).
    hanging_keywords: Tuple[str, ...] = ("else", "elif")
    #: File extensions that imply this dialect.
    extensions: Tuple[str, ...] = ()
    #: Interpreter basenames that imply this dialect via the shebang line.
    interpreters: Tuple[str, ...] = ()

    open_re: Pattern[str] = field(init=False, repr=False, compare=False)
    close_re: Pattern[str] = field(init=False, repr=False, compare=False)
    hanging_re: Pattern[str] = field(init=False, repr=False, compare=False)
    starts_close_re: Pattern[str] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        # ``frozen=True`` blocks normal assignment; go through object.__setattr__.
        object.__setattr__(
            self, "open_re", _keyword_pattern(self.open_keywords, r";|\Z|\s")
        )
        object.__setattr__(
            self, "close_re", _keyword_pattern(self.close_keywords, r";|\)|\||\Z|\s")
        )
        alternation = "|".join(re.escape(word) for word in self.hanging_keywords)
        object.__setattr__(self, "hanging_re", re.compile(rf"^({alternation})\b"))
        closers = "|".join(re.escape(word) for word in self.close_keywords)
        object.__setattr__(
            self, "starts_close_re", re.compile(rf"^(?:[)}}\]]|(?:{closers})\b)")
        )

    def count_open(self, text: str) -> int:
        """Number of block-opening keywords in ``text``."""
        return len(self.open_re.findall(text))

    def count_close(self, text: str) -> int:
        """Number of block-closing keywords in ``text``."""
        return len(self.close_re.findall(text))

    def is_hanging(self, text: str) -> bool:
        """True when ``text`` starts with a keyword such as ``else``.

        Such a line is printed one level to the left without changing the
        running indentation level.
        """
        return self.hanging_re.search(text) is not None

    def starts_with_close(self, text: str) -> bool:
        """True when ``text`` opens with a closing bracket or keyword.

        Combined with a net indentation change of zero this identifies
        "close then reopen" lines such as ``} else {`` or zsh's
        ``} always {``, which belong one level to the left.
        """
        return self.starts_close_re.search(text) is not None


#: POSIX-ish bash.  ``elif`` closes the previous branch and the ``then`` that
#: follows on the same line reopens it, so it is listed as a close keyword.
BASH = Dialect(
    name="bash",
    open_keywords=("case", "then", "do"),
    close_keywords=("esac", "fi", "done", "elif"),
    extensions=(".sh", ".bash", ".bashrc", ".ksh"),
    interpreters=("sh", "bash", "ksh", "dash"),
)

#: zsh understands everything bash does plus the csh-flavoured ``foreach ...
#: end`` and ``while ... end`` loop forms.
ZSH = Dialect(
    name="zsh",
    open_keywords=("case", "then", "do", "foreach"),
    close_keywords=("esac", "fi", "done", "elif", "end"),
    extensions=(".zsh", ".zshrc", ".zshenv", ".zprofile", ".zlogin", ".zlogout"),
    interpreters=("zsh",),
)

DIALECTS: Dict[str, Dialect] = {d.name: d for d in (BASH, ZSH)}

DEFAULT_DIALECT = BASH

_SHEBANG_RE = re.compile(r"^#!\s*(?P<path>\S+)(?P<rest>.*)$")


def get_dialect(name: str) -> Dialect:
    """Look up a dialect by name.

    Raises:
        KeyError: if ``name`` is not a known dialect.
    """
    try:
        return DIALECTS[name.lower()]
    except KeyError:
        known = ", ".join(sorted(DIALECTS))
        raise KeyError(f"unknown dialect {name!r}; known dialects: {known}") from None


def detect_dialect(
    data: str = "",
    filename: str = "",
    default: Dialect = DEFAULT_DIALECT,
) -> Dialect:
    """Guess the dialect from a shebang line, falling back to the file name.

    The shebang wins over the extension because it is what actually runs the
    script.  ``env`` wrappers (``#!/usr/bin/env zsh``) are unwrapped.
    """
    dialect = _from_shebang(data)
    if dialect is not None:
        return dialect
    dialect = _from_filename(filename)
    if dialect is not None:
        return dialect
    return default


def _from_shebang(data: str) -> Optional[Dialect]:
    first_line = data.split("\n", 1)[0].strip()
    match = _SHEBANG_RE.match(first_line)
    if match is None:
        return None
    words = [match.group("path"), *match.group("rest").split()]
    # Skip `env` and any VAR=value / -flag arguments it may carry.
    interpreter = ""
    for word in words:
        base = word.rsplit("/", 1)[-1]
        if base == "env" or base.startswith("-") or "=" in base:
            continue
        interpreter = base
        break
    for dialect in DIALECTS.values():
        if interpreter in dialect.interpreters:
            return dialect
    return None


def _from_filename(filename: str) -> Optional[Dialect]:
    if not filename:
        return None
    base = filename.rsplit("/", 1)[-1]
    suffix = base[base.rindex(".") :].lower() if "." in base[1:] else ""
    name = base.lower()
    for dialect in DIALECTS.values():
        if suffix and suffix in dialect.extensions:
            return dialect
        # Dotfiles such as `.zshrc` have no suffix in the usual sense.
        if f".{name.lstrip('.')}" in dialect.extensions:
            return dialect
    return None
