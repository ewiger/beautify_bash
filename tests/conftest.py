"""Shared fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from beautify_bash import Beautifier


@pytest.fixture
def beautifier() -> Beautifier:
    """A beautifier with the default two-space indentation."""
    return Beautifier()


@pytest.fixture
def script(tmp_path: Path) -> Path:
    """A small, badly indented bash script on disk."""
    path = tmp_path / "script.sh"
    path.write_text("#!/bin/bash\nif true; then\necho hi\nfi\n", encoding="utf-8")
    return path


@pytest.fixture
def data_dir() -> Path:
    return Path(__file__).parent / "data"
