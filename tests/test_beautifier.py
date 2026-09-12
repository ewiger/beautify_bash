"""Unit tests for the indenting core."""

from __future__ import annotations

from pathlib import Path

import pytest

from beautify_bash import BASH, ZSH, Beautifier, FormatError, beautify_string


def fmt(source: str, **kwargs: object) -> str:
    return Beautifier(**kwargs).format(source).text  # type: ignore[arg-type]


class TestBasicIndentation:
    def test_if_then_fi(self) -> None:
        assert fmt("if true; then\necho hi\nfi") == "if true; then\n  echo hi\nfi"

    def test_else_hangs_one_level_left(self) -> None:
        source = "if true; then\na\nelse\nb\nfi"
        assert fmt(source) == "if true; then\n  a\nelse\n  b\nfi"

    def test_elif_closes_and_reopens(self) -> None:
        source = "if a; then\nx\nelif b; then\ny\nfi"
        assert fmt(source) == "if a; then\n  x\nelif b; then\n  y\nfi"

    def test_nested_blocks_accumulate(self) -> None:
        source = "for i in 1; do\nif true; then\necho $i\nfi\ndone"
        expected = "for i in 1; do\n  if true; then\n    echo $i\n  fi\ndone"
        assert fmt(source) == expected

    def test_braces_and_brackets(self) -> None:
        assert fmt("f() {\necho hi\n}") == "f() {\n  echo hi\n}"

    def test_single_line_block_is_balanced(self) -> None:
        source = "if true; then echo hi; fi\necho after"
        assert fmt(source) == source

    @pytest.mark.parametrize(
        ("indent_char", "indent_size", "expected"),
        [
            (" ", 2, "  echo hi"),
            (" ", 4, "    echo hi"),
            ("\t", 1, "\techo hi"),
            (" ", 0, "echo hi"),
        ],
    )
    def test_indent_options(
        self, indent_char: str, indent_size: int, expected: str
    ) -> None:
        source = "if true; then\necho hi\nfi"
        result = fmt(source, indent_char=indent_char, indent_size=indent_size)
        assert result.split("\n")[1] == expected

    def test_blank_lines_stay_empty(self) -> None:
        assert fmt("if true; then\n\necho hi\nfi").split("\n")[1] == ""

    def test_already_formatted_is_idempotent(self, data_dir: Path) -> None:
        expected = (data_dir / "messy.expected.sh").read_text(encoding="utf-8")
        assert fmt(expected) == expected

    def test_fixture_round_trip(self, data_dir: Path) -> None:
        source = (data_dir / "messy.sh").read_text(encoding="utf-8")
        expected = (data_dir / "messy.expected.sh").read_text(encoding="utf-8")
        assert fmt(source) == expected


class TestKeywordsInCommandPosition:
    """Reserved words are only keywords at the start of a command."""

    @pytest.mark.parametrize(
        "line",
        [
            "echo done",
            "echo fi",
            'printf "%s" esac',
            "grep -q done file",
            "x=done",
        ],
    )
    def test_reserved_word_as_argument_does_not_dedent(self, line: str) -> None:
        source = f"if true; then\n{line}\nfi"
        assert fmt(source) == f"if true; then\n  {line}\nfi"

    def test_keyword_after_semicolon_counts(self) -> None:
        assert fmt("for i in 1; do\nx\ndone") == "for i in 1; do\n  x\ndone"


class TestQuotingAndComments:
    def test_keyword_inside_single_quotes_ignored(self) -> None:
        source = "if true; then\necho 'fi done esac'\nfi"
        assert fmt(source) == "if true; then\n  echo 'fi done esac'\nfi"

    def test_keyword_inside_double_quotes_ignored(self) -> None:
        source = 'if true; then\necho "} ) ]"\nfi'
        assert fmt(source) == 'if true; then\n  echo "} ) ]"\nfi'

    def test_keyword_in_comment_ignored(self) -> None:
        source = "if true; then\necho hi # fi done\nfi"
        assert fmt(source) == "if true; then\n  echo hi # fi done\nfi"

    def test_multiline_single_quote_passes_through(self) -> None:
        source = "echo 'line one\n     line two'\necho after"
        assert fmt(source) == source


class TestHereDocuments:
    def test_body_is_preserved_verbatim(self) -> None:
        source = "if true; then\ncat <<EOF\n    indented   body   \nEOF\nfi"
        expected = "if true; then\n  cat <<EOF\n    indented   body   \nEOF\nfi"
        assert fmt(source) == expected

    def test_opening_line_is_still_indented(self) -> None:
        result = fmt("if true; then\ncat <<EOF\nbody\nEOF\nfi")
        assert result.split("\n")[1] == "  cat <<EOF"

    def test_dash_form_allows_indented_terminator(self) -> None:
        source = "if true; then\ncat <<-EOF\nbody\n\tEOF\nfi"
        assert fmt(source).split("\n")[-1] == "fi"

    def test_quoted_tag(self) -> None:
        source = 'cat <<"END"\n$not_expanded\nEND\necho after'
        assert fmt(source) == source

    def test_backslash_quoted_tag(self) -> None:
        source = "if true; then\ncat <<\\EOF ||\n$literal\nEOF\nfi"
        assert fmt(source).split("\n")[-1] == "fi"

    def test_here_string_is_not_a_here_doc(self) -> None:
        source = 'if true; then\ngrep x <<< "$var"\nfi'
        assert fmt(source) == 'if true; then\n  grep x <<< "$var"\nfi'

    def test_arithmetic_left_shift_is_not_a_here_doc(self) -> None:
        source = "if true; then\nx=$(( 1 << 2 ))\nfi"
        assert fmt(source) == "if true; then\n  x=$(( 1 << 2 ))\nfi"

    def test_keyword_inside_body_does_not_dedent(self) -> None:
        source = "if true; then\ncat <<EOF\nfi\ndone\nEOF\nfi"
        assert fmt(source).split("\n")[-1] == "fi"


class TestCaseStatements:
    def test_case_branches(self) -> None:
        source = "case $x in\na)\nfoo\n;;\nesac"
        expected = "case $x in\n  a)\n    foo\n  ;;\nesac"
        assert fmt(source) == expected

    def test_nested_case(self) -> None:
        source = "case $a in\n1)\ncase $b in\n2)\nx\n;;\nesac\n;;\nesac"
        result = fmt(source)
        assert result.split("\n")[-1] == "esac"
        assert result.split("\n")[4] == "        x"


class TestErrors:
    def test_unbalanced_block_reports_mismatch(self) -> None:
        result = Beautifier().format("if true; then\necho hi")
        assert not result.ok
        assert "indent/outdent mismatch" in result.errors[0].message
        assert result.errors[0].line == 2

    def test_esac_without_case(self) -> None:
        result = Beautifier().format("esac")
        assert any('"esac" before "case"' in e.message for e in result.errors)

    def test_error_render_includes_path(self) -> None:
        rendered = FormatError(7, "boom").render("a.sh")
        assert rendered == "File a.sh: error: boom in line 7."

    def test_error_render_without_path(self) -> None:
        assert FormatError(7, "boom").render() == "error: boom in line 7."

    @pytest.mark.parametrize(
        ("kwargs", "message"),
        [
            ({"indent_size": -1}, "indent_size"),
            ({"indent_char": "xy"}, "indent_char"),
        ],
    )
    def test_invalid_construction(self, kwargs: dict, message: str) -> None:
        with pytest.raises(ValueError, match=message):
            Beautifier(**kwargs)


class TestConvenienceApi:
    def test_beautify_string_detects_dialect(self) -> None:
        result = beautify_string("#!/usr/bin/env zsh\nfoo\n")
        assert result.dialect is ZSH

    def test_beautify_string_honours_explicit_dialect(self) -> None:
        result = beautify_string("foo\n", dialect=BASH)
        assert result.dialect is BASH

    def test_format_result_is_truthy_on_success(self) -> None:
        assert beautify_string("echo hi").ok


class TestLegacyApi:
    """The 1.x surface still works."""

    def test_beautify_string_tuple(self, beautifier: Beautifier) -> None:
        text, error = beautifier.beautify_string("if true; then\nx\nfi")
        assert text == "if true; then\n  x\nfi"
        assert error is False

    def test_tab_attributes_alias_new_names(self, beautifier: Beautifier) -> None:
        beautifier.tab_str = "\t"
        beautifier.tab_size = 1
        assert beautifier.indent_char == "\t"
        assert beautifier.indent_size == 1
        assert beautifier.tab_str == "\t"
        assert beautifier.tab_size == 1

    def test_beautify_string_writes_errors_to_stderr(
        self, beautifier: Beautifier, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _, error = beautifier.beautify_string("if true; then\nx", "bad.sh")
        assert error is True
        assert "File bad.sh: error:" in capsys.readouterr().err
