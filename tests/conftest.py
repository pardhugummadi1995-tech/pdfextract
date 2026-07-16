"""Shared fixtures. The sample SOD PDF is generated at runtime with reportlab
so no binary fixture is committed."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "samples"))


@pytest.fixture()
def sample_sod_pdf(tmp_path):
    from generate_sample_sod import build

    path = tmp_path / "sample-sod.pdf"
    build(str(path))
    return str(path)
