"""Shared pytest fixtures.

A small PDF containing a known table is generated on the fly with reportlab so
the extraction tests are fully self-contained (no binary fixtures committed).
"""

from __future__ import annotations

import pytest

SAMPLE_HEADER = ["Name", "Department", "Salary"]
SAMPLE_ROWS = [
    ["Alice", "Engineering", "120000"],
    ["Bob", "Marketing", "95000"],
    ["Carol", "Finance", "110000"],
]


def _write_sample_pdf(path: str) -> None:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

    doc = SimpleDocTemplate(path, pagesize=letter)
    data = [SAMPLE_HEADER, *SAMPLE_ROWS]
    table = Table(data)
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("FONTSIZE", (0, 0), (-1, -1), 12),
            ]
        )
    )
    doc.build([table])


@pytest.fixture()
def sample_pdf(tmp_path):
    """Path to a freshly generated single-table PDF."""
    path = tmp_path / "sample.pdf"
    _write_sample_pdf(str(path))
    return str(path)


@pytest.fixture()
def sample_header():
    return list(SAMPLE_HEADER)


@pytest.fixture()
def sample_rows():
    return [list(r) for r in SAMPLE_ROWS]
