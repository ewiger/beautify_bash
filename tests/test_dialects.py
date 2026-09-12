"""Unit tests for dialect selection and zsh-specific syntax."""

from __future__ import annotations

import pytest

from beautify_bash import BASH, ZSH, Beautifier, Dialect, detect_dialect, get_dialect


class TestLookup:
    @pytest.mark.parametrize(("name", "expected"), [("bash", BASH), ("ZSH", ZSH)])
    def test_get_dialect(self, name: str, expected: Dialect) -> None:
        assert get_dialect(name) is expected

    def test_unknown_dialect(self) -> None:
        with pytest.raises(KeyError, match="unknown dialect"):
            get_dialect("fish")

    def test_dialects_are_hashable_and_frozen(self) -> None:
        assert {BASH, ZSH}
        with pytest.raises(AttributeError):
            BASH.name = "other"  # type: ignore[misc]


class TestDetection:
    @pytest.mark.parametrize(
        ("shebang", "expected"),
        [
            ("#!/bin/bash", BASH),
            ("#!/bin/sh", BASH),
            ("#!/usr/bin/env bash", BASH),
            ("#!/bin/zsh", ZSH),
            ("#!/usr/bin/env zsh", ZSH),
            ("#! /usr/bin/env  zsh", ZSH),
            ("#!/usr/bin/env -S zsh -f", ZSH),
        ],
    )
    def test_shebang(self, shebang: str, expected: Dialect) -> None:
        assert detect_dialect(f"{shebang}\necho hi\n") is expected

    @pytest.mark.parametrize(
        ("filename", "expected"),
        [
            ("script.sh", BASH),
            ("script.bash", BASH),
            ("script.zsh", ZSH),
            ("/home/u/.zshrc", ZSH),
            (".zshenv", ZSH),
        ],
    )
    def test_filename(self, filename: str, expected: Dialect) -> None:
        assert detect_dialect("echo hi\n", filename) is expected

    def test_shebang_beats_filename(self) -> None:
        assert detect_dialect("#!/bin/zsh\n", "script.sh") is ZSH

    def test_falls_back_to_default(self) -> None:
        assert detect_dialect("echo hi\n") is BASH
        assert detect_dialect("echo hi\n", "notes.txt", default=ZSH) is ZSH

    def test_non_shebang_comment_is_not_a_shebang(self) -> None:
        assert detect_dialect("# !/bin/zsh\n", "x.sh") is BASH


class TestZshSyntax:
    def test_foreach_end(self) -> None:
        source = "foreach f (a b c)\nprint $f\nend"
        result = Beautifier(dialect=ZSH).format(source)
        assert result.text == "foreach f (a b c)\n  print $f\nend"
        assert result.ok

    def test_nested_foreach(self) -> None:
        source = "foreach a (1)\nforeach b (2)\nprint $a$b\nend\nend"
        result = Beautifier(dialect=ZSH).format(source)
        assert result.text.split("\n")[2] == "    print $a$b"

    def test_always_block(self) -> None:
        source = "{\nrisky\n} always {\ncleanup\n}"
        result = Beautifier(dialect=ZSH).format(source)
        assert result.text == "{\n  risky\n} always {\n  cleanup\n}"

    def test_bash_does_not_know_foreach(self) -> None:
        """`end` is an ordinary word in bash, so nothing is indented."""
        result = Beautifier(dialect=BASH).format("foreach f (a b c)\nprint $f\nend")
        assert result.text.split("\n")[1] == "print $f"

    def test_bash_constructs_still_work_in_zsh(self) -> None:
        source = "if true; then\necho hi\nfi"
        assert Beautifier(dialect=ZSH).format(source).text == (
            "if true; then\n  echo hi\nfi"
        )


class TestDialectHelpers:
    def test_count_open_and_close(self) -> None:
        assert BASH.count_open("if x; then") == 1
        assert BASH.count_close("done") == 1
        assert BASH.count_close("echo done") == 0

    def test_is_hanging(self) -> None:
        assert BASH.is_hanging("else")
        assert BASH.is_hanging("elif x; then")
        assert not BASH.is_hanging("echo else")
