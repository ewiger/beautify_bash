"""The line-based shell script indenter.

The algorithm walks the script one line at a time, keeps a running indentation
level, and re-emits each line stripped and re-indented.  Regions where
re-indenting would change the meaning of the script (here-documents and
multi-line quotes) are passed through verbatim.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import IO, List, Optional, Tuple, Union

from .dialects import (
    DEFAULT_DIALECT,
    Dialect,
    command_position_pattern,
    detect_dialect,
)

__all__ = [
    "Beautifier",
    "BeautifyBash",
    "FormatError",
    "FormatResult",
    "beautify_string",
]

PathLike = Union[str, "Path"]

# Quoted spans are blanked out before keyword counting so that a `done` inside
# a string cannot dedent the script.
_SINGLE_QUOTED = re.compile(r"'.*?'")
_DOUBLE_QUOTED = re.compile(r'".*?"')
_BACKTICKED = re.compile(r"`.*?`")
_ESCAPED_BACKTICK_QUOTE = re.compile(r"\\`.*?'")
_ESCAPED_CHAR = re.compile(r"\\.")
_COMMENT = re.compile(r"(\A|\s)(#.*)")
_HERE_DOC_START = re.compile(r"(?<!<)<<(?!<)-?")
# The tag may be quoted with '…', "…" or a leading backslash (`<<\EOF`), each
# of which suppresses expansion inside the body.  The lookarounds keep the
# here-string operator `<<<` and the arithmetic left shift `1 << 2` out.
_HERE_DOC_TAG = re.compile(
    r""".*(?<!<)<<(?!<)(?P<dash>-?)\s*(?:\\)?['"]?(?P<tag>[A-Za-z_][\w.-]*)['"]?.*"""
)
_OPEN_BRACKETS = re.compile(r"[{(\[]")
_CLOSE_BRACKETS = re.compile(r"[})\]]")
_CASE_KEYWORD = command_position_pattern("case")
_ESAC_KEYWORD = command_position_pattern("esac")
_CASE_PATTERN = re.compile(r"\A[^(]*\)")
_CASE_BREAK = re.compile(r";;")
_QUOTE_START = re.compile(r"""(\A|\s)('|")""")


@dataclass(frozen=True)
class FormatError:
    """A syntax problem noticed while indenting."""

    line: int
    message: str

    def render(self, path: str = "") -> str:
        where = f"File {path}: " if path else ""
        return f"{where}error: {self.message} in line {self.line}."


@dataclass
class FormatResult:
    """Outcome of formatting one script."""

    text: str
    errors: List[FormatError] = field(default_factory=list)
    dialect: Dialect = DEFAULT_DIALECT

    @property
    def ok(self) -> bool:
        return not self.errors

    def __str__(self) -> str:  # pragma: no cover - convenience only
        return self.text


class Beautifier:
    """Re-indent shell scripts.

    Args:
        indent_char: the character used for one unit of indentation.
        indent_size: how many ``indent_char`` per level.
        dialect: the shell dialect to assume when none is detected.
        backup: whether :meth:`beautify_file` keeps a ``file~`` copy.
    """

    def __init__(
        self,
        indent_char: str = " ",
        indent_size: int = 2,
        dialect: Dialect = DEFAULT_DIALECT,
        backup: bool = True,
    ) -> None:
        if indent_size < 0:
            raise ValueError("indent_size must not be negative")
        if len(indent_char) != 1:
            raise ValueError("indent_char must be exactly one character")
        self.indent_char = indent_char
        self.indent_size = indent_size
        self.dialect = dialect
        self.backup = backup

    # -- backwards compatible aliases for the 1.x attribute names ----------
    @property
    def tab_str(self) -> str:
        return self.indent_char

    @tab_str.setter
    def tab_str(self, value: str) -> None:
        self.indent_char = value

    @property
    def tab_size(self) -> int:
        return self.indent_size

    @tab_size.setter
    def tab_size(self, value: int) -> None:
        self.indent_size = value

    # -- file helpers ------------------------------------------------------
    def read_file(self, path: PathLike) -> str:
        return Path(path).read_text(encoding="utf-8")

    def write_file(self, path: PathLike, data: str) -> None:
        Path(path).write_text(data, encoding="utf-8")

    # -- core --------------------------------------------------------------
    def format(
        self,
        data: str,
        dialect: Optional[Dialect] = None,
    ) -> FormatResult:
        """Indent ``data`` and report any syntax problems found on the way."""
        active = dialect or self.dialect
        indent_unit = self.indent_char * self.indent_size
        level = 0
        case_stack: List[int] = []
        errors: List[FormatError] = []
        output: List[str] = []

        in_here_doc = False
        here_tag = ""
        here_doc_dash = False
        in_ext_quote = False
        defer_ext_quote = False
        ext_quote_char = ""

        line_no = 0
        for line_no, raw in enumerate(data.split("\n"), start=1):
            record = raw.rstrip()
            stripped = record.strip()
            test = self._strip_literals(stripped)

            if in_here_doc:
                # Here-doc bodies are data: emit them byte for byte.
                output.append(raw)
                # A `<<-` terminator may be indented, a plain `<<` one may not.
                terminator = raw.strip() if here_doc_dash else raw
                if terminator == here_tag:
                    in_here_doc = False
                continue

            # The line that *opens* a here-doc is still ordinary code, so note
            # the tag now and switch over once the line has been emitted.
            opens_here_doc = False
            if _HERE_DOC_START.search(test):
                match = _HERE_DOC_TAG.match(stripped)
                if match is not None and match.group("tag"):
                    here_tag = match.group("tag")
                    here_doc_dash = bool(match.group("dash"))
                    opens_here_doc = True

            # A quote left open on a previous line makes this line string data.
            closes_ext_quote = False
            if in_ext_quote:
                if ext_quote_char in test:
                    # Keep whatever follows the closing quote for counting.
                    test = test.split(ext_quote_char, 1)[1]
                    in_ext_quote = False
                    closes_ext_quote = True
            elif _QUOTE_START.search(test):
                # The quote only takes effect after this line is emitted.
                defer_ext_quote = True
                ext_quote_char = re.sub(r""".*(['"]).*""", r"\1", test, count=1)
                test = test.split(ext_quote_char, 1)[0]

            if in_ext_quote:
                # Wholly inside a multi-line string: emit byte for byte.
                output.append(raw)
            else:
                opened = active.count_open(test) + len(_OPEN_BRACKETS.findall(test))
                closed = active.count_close(test) + len(_CLOSE_BRACKETS.findall(test))

                if _ESAC_KEYWORD.search(test):
                    if case_stack:
                        closed += case_stack.pop()
                    else:
                        errors.append(FormatError(line_no, '"esac" before "case"'))

                if case_stack:
                    # `pattern)` inside a case opens a branch; `;;` closes it.
                    if _CASE_PATTERN.search(test):
                        closed -= 2  # undo the `)` counted above
                        case_stack[-1] += 1
                    if _CASE_BREAK.search(test):
                        closed += 1
                        case_stack[-1] -= 1
                    hanging = 0
                    net = opened - closed
                else:
                    net = opened - closed
                    hangs = active.is_hanging(test) or (
                        net == 0 and active.starts_with_close(test)
                    )
                    hanging = -1 if hangs else 0

                level += min(net, 0)
                if closes_ext_quote:
                    # The leading whitespace of this line is string content.
                    output.append(record)
                elif stripped:
                    output.append((indent_unit * max(0, level + hanging)) + stripped)
                else:
                    output.append("")
                level += max(net, 0)

            if defer_ext_quote:
                in_ext_quote = True
                defer_ext_quote = False
            if _CASE_KEYWORD.search(test):
                case_stack.append(0)
            if opens_here_doc:
                in_here_doc = True

        if level != 0:
            errors.append(FormatError(line_no, f"indent/outdent mismatch: {level}"))
        return FormatResult("\n".join(output), errors, active)

    @staticmethod
    def _strip_literals(stripped_record: str) -> str:
        """Blank out quotes, escapes and comments before keyword counting."""
        test = _SINGLE_QUOTED.sub("", stripped_record)
        test = _DOUBLE_QUOTED.sub("", test)
        test = _BACKTICKED.sub("", test)
        test = _ESCAPED_BACKTICK_QUOTE.sub("", test)
        test = _ESCAPED_CHAR.sub("", test)
        return _COMMENT.sub("", test, count=1)

    # -- 1.x compatible entry points --------------------------------------
    def beautify_string(self, data: str, path: str = "") -> Tuple[str, bool]:
        """Format ``data``; return ``(text, had_error)`` as version 1.x did."""
        result = self.format(data, detect_dialect(data, path, self.dialect))
        for error in result.errors:
            sys.stderr.write(error.render(path) + "\n")
        return result.text, not result.ok

    def beautify_file(
        self,
        path: PathLike,
        stdin: Optional[IO[str]] = None,
        stdout: Optional[IO[str]] = None,
    ) -> bool:
        """Format a file in place (or stdin to stdout for ``-``).

        Returns ``True`` when a syntax problem was reported.
        """
        if str(path) == "-":
            data = (stdin or sys.stdin).read()
            text, error = self.beautify_string(data, "(stdin)")
            (stdout or sys.stdout).write(text)
            return error
        data = self.read_file(path)
        text, error = self.beautify_string(data, str(path))
        if data != text:
            if self.backup:
                self.write_file(f"{path}~", data)
            self.write_file(path, text)
        return error


#: Historical name kept so ``from beautify_bash import BeautifyBash`` keeps working.
BeautifyBash = Beautifier


def beautify_string(
    data: str,
    dialect: Optional[Dialect] = None,
    indent_char: str = " ",
    indent_size: int = 2,
) -> FormatResult:
    """Format ``data`` in one call.

    When ``dialect`` is omitted it is detected from the script's shebang.
    """
    beautifier = Beautifier(indent_char=indent_char, indent_size=indent_size)
    return beautifier.format(data, dialect or detect_dialect(data))
