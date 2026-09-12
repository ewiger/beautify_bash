"""Worked examples of mocking with ``unittest.mock``.

These tests double as documentation: each class shows one mocking technique
applied to this codebase.  Nothing here touches the real file system beyond
``tmp_path``.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any
from unittest import mock

import pytest

from beautify_bash import Beautifier, dialects
from beautify_bash.beautifier import FormatError, FormatResult

MESSY = "if true; then\necho hi\nfi\n"
TIDY = "if true; then\n  echo hi\nfi\n"


class TestPatchingMethods:
    """`mock.patch.object` replaces one method on the class under test."""

    def test_beautify_file_reads_and_writes_through_the_helpers(self) -> None:
        beautifier = Beautifier()
        with (
            mock.patch.object(Beautifier, "read_file", return_value=MESSY) as read,
            mock.patch.object(Beautifier, "write_file") as write,
        ):
            error = beautifier.beautify_file("script.sh")

        assert error is False
        read.assert_called_once_with("script.sh")
        # The backup is written before the formatted file.
        assert write.call_args_list == [
            mock.call("script.sh~", MESSY),
            mock.call("script.sh", TIDY),
        ]

    def test_no_write_when_already_formatted(self) -> None:
        beautifier = Beautifier()
        with (
            mock.patch.object(Beautifier, "read_file", return_value=TIDY),
            mock.patch.object(Beautifier, "write_file") as write,
        ):
            beautifier.beautify_file("script.sh")
        write.assert_not_called()

    def test_backup_disabled_writes_only_the_target(self) -> None:
        beautifier = Beautifier(backup=False)
        with (
            mock.patch.object(Beautifier, "read_file", return_value=MESSY),
            mock.patch.object(Beautifier, "write_file") as write,
        ):
            beautifier.beautify_file("script.sh")
        write.assert_called_once_with("script.sh", TIDY)


class TestPatchingBuiltins:
    """`mock.mock_open` stands in for ``open`` inside ``pathlib``."""

    def test_read_file_uses_utf8(self) -> None:
        opener = mock.mock_open(read_data=MESSY)
        with mock.patch("pathlib.Path.open", opener):
            assert Beautifier().read_file("script.sh") == MESSY

    def test_write_file_round_trip(self, tmp_path: Path) -> None:
        path = tmp_path / "out.sh"
        Beautifier().write_file(path, TIDY)
        assert path.read_text(encoding="utf-8") == TIDY


class TestFakeStreams:
    """Injected streams replace ``sys.stdin`` / ``sys.stdout``."""

    def test_stdin_is_formatted_to_stdout(self) -> None:
        stdout = io.StringIO()
        error = Beautifier().beautify_file("-", stdin=io.StringIO(MESSY), stdout=stdout)
        assert stdout.getvalue() == TIDY
        assert error is False

    def test_falls_back_to_sys_streams(self, monkeypatch: pytest.MonkeyPatch) -> None:
        stdout = io.StringIO()
        monkeypatch.setattr("sys.stdin", io.StringIO(MESSY))
        monkeypatch.setattr("sys.stdout", stdout)
        Beautifier().beautify_file("-")
        assert stdout.getvalue() == TIDY


class TestSpyingOnCollaborators:
    """`wraps=` keeps the real behaviour while recording the calls."""

    def test_detect_dialect_is_consulted_once_per_file(self) -> None:
        seen = []

        def record(*args: Any, **kwargs: Any) -> dialects.Dialect:
            result = dialects.detect_dialect(*args, **kwargs)
            seen.append(result)
            return result

        spy = mock.Mock(side_effect=record)
        with mock.patch("beautify_bash.beautifier.detect_dialect", spy):
            Beautifier().beautify_string("#!/bin/zsh\necho hi\n", "x.sh")

        spy.assert_called_once()
        assert spy.call_args.args[1] == "x.sh"
        assert seen == [dialects.ZSH]

    def test_dialect_counters_are_used(self) -> None:
        dialect = mock.Mock(wraps=dialects.BASH)
        Beautifier().format(MESSY, dialect=dialect)
        # One call per line, including the empty one after the trailing newline.
        assert dialect.count_open.call_count == len(MESSY.split("\n"))
        assert dialect.count_close.call_count == len(MESSY.split("\n"))


class TestStubbingResults:
    """A stub lets a caller be tested without running the real algorithm."""

    def test_caller_reports_stubbed_errors(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        stub = FormatResult("output", [FormatError(3, "synthetic failure")])
        with mock.patch.object(Beautifier, "format", return_value=stub):
            text, error = Beautifier().beautify_string("anything", "fake.sh")

        assert text == "output"
        assert error is True
        assert "File fake.sh: error: synthetic failure in line 3." in (
            capsys.readouterr().err
        )

    def test_side_effect_raises(self) -> None:
        with (
            mock.patch.object(
                Beautifier, "read_file", side_effect=OSError("disk on fire")
            ),
            pytest.raises(OSError, match="disk on fire"),
        ):
            Beautifier().beautify_file("script.sh")


class TestAutospec:
    """`autospec` keeps the replacement honest about the real signature."""

    def test_wrong_call_is_rejected(self) -> None:
        with mock.patch.object(Beautifier, "format", autospec=True) as formatter:
            formatter.return_value = FormatResult(TIDY)
            Beautifier().beautify_string(MESSY)
            formatter.assert_called_once()

        with (
            mock.patch.object(Beautifier, "write_file", autospec=True) as write,
            pytest.raises(TypeError),
        ):
            write()  # missing `self`, `path` and `data`

    def test_patched_object_still_type_checks(self) -> None:
        fake: Any = mock.create_autospec(Beautifier, instance=True)
        fake.format.return_value = FormatResult(TIDY)
        assert fake.format("x").text == TIDY
        with pytest.raises(AttributeError):
            fake.no_such_method()
