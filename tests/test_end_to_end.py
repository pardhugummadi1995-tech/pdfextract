"""End-to-end test: read a generated ruled-table SOD PDF and build the project.

This exercises the real pdfplumber lattice extraction path (the reader), not
just the pure aggregation logic.
"""

from rise_engine import build_project, read_sod
from rise_engine.exporter import indent_to_csv, to_json


def test_end_to_end_sample(sample_sod_pdf):
    pages = read_sod(sample_sod_pdf)
    model = build_project(pages, source="sample-sod.pdf")

    rooms = {r.room for r in model.room_summary}
    assert "Kitchen" in rooms
    assert "Master Bedroom" in rooms

    codes = {c.code for c in model.cabinets}
    assert {"B1", "B2", "W1", "WR1", "L1"} <= codes

    # Hinges summed across cabinets/rooms (B1 4 + B2 6 + WR1 10 + L1 4 ... Onsys vs Unspring differ).
    onsys = next(m for m in model.material_indent if m.description == "Hettich Onsys 105° Hinges")
    assert onsys.total_qty == 20  # B1 4 + B2 6 + WR1 10
    assert "Kitchen" in onsys.rooms and "Master Bedroom" in onsys.rooms

    # WR1 dimensions correctly extracted.
    wr1 = next(c for c in model.cabinets if c.code == "WR1")
    assert wr1.dimensions == "900 x 580 x 2150"

    # Client-scope handle is captured and flagged.
    handles = next(m for m in model.material_indent if "Handles" in m.description)
    assert handles.total_qty is None and handles.flags

    # Exports render without error.
    assert "SKU Code" in indent_to_csv(model)
    assert '"category": "Hardware"' in to_json(model) or '"category":"Hardware"' in to_json(model)
