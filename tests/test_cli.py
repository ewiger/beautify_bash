"""End-to-end tests for the Typer command line interface."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from beautify_bash import __version__
from beautify_bash.cli import app

runner = CliRunner()

MESSY = "#!/bin/bash\nif true; then\necho hi\nfi\n"
TIDY = "#!/bin/bash\nif true; then\n  echo hi\nfi\n"


class TestInvocation:
    def test_version(self) -> None:
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert __version__ in result.stdout

    def test_no_arguments_shows_help(self) -> None:
        result = runner.invoke(app, [])
        assert "FILES" in result.stdout

    def test_help(self) -> None:
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "--dialect" in result.stdout


class TestFormattingFiles:
    def test_rewrites_file_and_keeps_backup(self, script: Path) -> None:
        result = runner.invoke(app, [str(script)])
        assert result.exit_code == 0
        assert script.read_text() == TIDY
        assert script.with_name("script.sh~").read_text() == MESSY

    def test_no_backup(self, script: Path) -> None:
        runner.invoke(app, ["--no-backup", str(script)])
        assert script.read_text() == TIDY
        assert not script.with_name("script.sh~").exists()

    def test_unchanged_file_is_not_rewritten(self, tmp_path: Path) -> None:
        path = tmp_path / "tidy.sh"
        path.write_text(TIDY)
        result = runner.invoke(app, [str(path)])
        assert result.exit_code == 0
        assert not path.with_name("tidy.sh~").exists()

    def test_multiple_files(self, tmp_path: Path) -> None:
        paths = []
        for name in ("a.sh", "b.sh"):
            path = tmp_path / name
            path.write_text(MESSY)
            paths.append(str(path))
        assert runner.invoke(app, paths).exit_code == 0
        assert all(Path(p).read_text() == TIDY for p in paths)

    def test_missing_file_exits_two(self, tmp_path: Path) -> None:
        result = runner.invoke(app, [str(tmp_path / "nope.sh")])
        assert result.exit_code == 2

    @pytest.mark.parametrize(
        ("args", "expected_line"),
        [
            ([], "  echo hi"),
            (["--indent", "4"], "    echo hi"),
            (["--tabs"], "\techo hi"),
        ],
    )
    def test_indent_options(self, script: Path, args: list, expected_line: str) -> None:
        runner.invoke(app, [*args, str(script)])
        assert script.read_text().split("\n")[2] == expected_line


class TestCheckAndDiff:
    def test_check_reports_without_writing(self, script: Path) -> None:
        result = runner.invoke(app, ["--check", str(script)])
        assert result.exit_code == 1
        assert "would reformat" in result.stdout
        assert script.read_text() == MESSY

    def test_check_passes_on_tidy_file(self, tmp_path: Path) -> None:
        path = tmp_path / "tidy.sh"
        path.write_text(TIDY)
        assert runner.invoke(app, ["--check", str(path)]).exit_code == 0

    def test_check_quiet(self, script: Path) -> None:
        result = runner.invoke(app, ["--check", "--quiet", str(script)])
        assert result.exit_code == 1
        assert result.stdout.strip() == ""

    def test_diff_does_not_write(self, script: Path) -> None:
        result = runner.invoke(app, ["--diff", str(script)])
        assert result.exit_code == 1
        assert "+  echo hi" in result.stdout
        assert script.read_text() == MESSY


class TestStdin:
    def test_stdin_to_stdout(self) -> None:
        result = runner.invoke(app, ["-"], input=MESSY)
        assert result.exit_code == 0
        assert result.stdout == TIDY

    def test_stdin_check(self) -> None:
        assert runner.invoke(app, ["--check", "-"], input=MESSY).exit_code == 1
        assert runner.invoke(app, ["--check", "-"], input=TIDY).exit_code == 0

    def test_stdin_diff(self) -> None:
        result = runner.invoke(app, ["--diff", "-"], input=MESSY)
        assert "--- a/(stdin)" in result.stdout


class TestDialectOption:
    ZSH_SOURCE = "foreach f (a b)\nprint $f\nend\n"

    def test_explicit_zsh(self, tmp_path: Path) -> None:
        path = tmp_path / "loop.txt"
        path.write_text(self.ZSH_SOURCE)
        runner.invoke(app, ["--dialect", "zsh", str(path)])
        assert path.read_text().split("\n")[1] == "  print $f"

    def test_auto_detects_from_extension(self, tmp_path: Path) -> None:
        path = tmp_path / "loop.zsh"
        path.write_text(self.ZSH_SOURCE)
        runner.invoke(app, [str(path)])
        assert path.read_text().split("\n")[1] == "  print $f"

    def test_explicit_bash_ignores_foreach(self, tmp_path: Path) -> None:
        path = tmp_path / "loop.zsh"
        path.write_text(self.ZSH_SOURCE)
        runner.invoke(app, ["-d", "bash", str(path)])
        assert path.read_text().split("\n")[1] == "print $f"

    def test_rejects_unknown_dialect(self, script: Path) -> None:
        result = runner.invoke(app, ["--dialect", "fish", str(script)])
        assert result.exit_code != 0


class TestErrorReporting:
    def test_unbalanced_script_exits_one(self, tmp_path: Path) -> None:
        path = tmp_path / "broken.sh"
        path.write_text("if true; then\necho hi\n")
        result = runner.invoke(app, [str(path)])
        assert result.exit_code == 1
        assert "indent/outdent mismatch" in result.output
