from rise_engine.pipeline import build_project
from rise_engine.reader import PageExtract


def _page(n, room, rows, finishes=None):
    return PageExtract(page_number=n, room=room, finish_legend=finishes or {}, cabinet_rows=rows)


def _row(code, hw, w=600, d=580, h=820, carcass="C1", shutter="S2"):
    return {
        "code": code,
        "carcass": carcass,
        "shutter": shutter,
        "sizes": f"{w} X {d} X {h}mm",
        "width": w,
        "depth": d,
        "height": h,
        "hardware_text": hw,
    }


def test_indent_groups_and_sums_across_cabinets():
    pages = [
        _page(9, "Kitchen", [
            _row("B1", "1. Hettich Onsys 105° Hinges -4Nos 2. Ebco Cylindrical Legs -6Nos"),
            _row("B2", "1. Hettich Onsys 105° Hinges -6Nos"),
        ]),
        _page(23, "Master Bedroom", [
            _row("WR1", "1. Hettich Onsys 105° Hinges -10Nos 2. Hafele Multipurpose Lock -1Pc",
                 w=900, d=580, h=2150, shutter="S1"),
        ], finishes={"C1": "VINTAGE SHALE", "S1": "STONE GREY"}),
    ]
    model = build_project(pages, source="x.pdf")

    hinge = next(m for m in model.material_indent if m.description == "Hettich Onsys 105° Hinges")
    assert hinge.total_qty == 20  # 4 + 6 + 10
    assert hinge.uom == "Nos"
    assert hinge.rooms == ["Kitchen", "Master Bedroom"]
    assert hinge.cabinets == ["B1", "B2", "WR1"]
    assert hinge.pages == [9, 23]

    assert model.category_counts.rooms == 2
    assert model.category_counts.cabinets == 3
    assert model.category_counts.hardware_qty == 27  # 20 hinges + 6 legs + 1 lock


def test_dedup_same_cabinet_across_pages_keeps_richer():
    wr1 = _row("WR1", "1. Hettich Onsys 105° Hinges -10Nos", w=900, d=580, h=2150)
    pages = [
        _page(23, "Master Bedroom", [wr1]),
        _page(24, "Master Bedroom", [{
            "code": "WR1", "carcass": "", "shutter": "", "sizes": "",
            "width": None, "depth": None, "height": None, "hardware_text": "",
        }]),
    ]
    model = build_project(pages)
    assert len(model.cabinets) == 1
    assert model.cabinets[0].dimensions == "900 x 580 x 2150"
    hinge = next(m for m in model.material_indent if "Hinges" in m.description)
    assert hinge.total_qty == 10  # not double counted


def test_unrecognized_scanned_pdf():
    # No text and no schedules -> looks scanned.
    model = build_project([PageExtract(page_number=1, text_len=0)], source="scan.pdf")
    assert model.recognized is False
    assert "scanned" in model.recognition_note.lower()
    assert model.warnings and model.warnings[0] == model.recognition_note


def test_unrecognized_wrong_template():
    # Plenty of text but no schedule table -> unsupported template.
    model = build_project([PageExtract(page_number=1, text_len=5000)], source="other.pdf")
    assert model.recognized is False
    assert "template" in model.recognition_note.lower()


def test_recognized_when_schedule_present():
    model = build_project(
        [_page(9, "Kitchen", [_row("B1", "1. Hettich Onsys 105° Hinges -4Nos")])],
    )
    assert model.recognized is True
    assert model.recognition_note == ""


def test_finish_indent_and_dimension_warning():
    pages = [
        _page(1, "Kitchen", [
            _row("B1", "1. Hettich Onsys 105° Hinges -4Nos"),
            {"code": "B9", "carcass": "C1", "shutter": "S2", "sizes": "", "width": None,
             "depth": None, "height": None, "hardware_text": "1. Open Unit"},
        ], finishes={"C1": "VINTAGE SHALE", "S2": "CADET GREY"}),
    ]
    model = build_project(pages)
    fin = {m.sku_code: m for m in model.material_indent if m.category == "Finish"}
    assert "FIN-C1" in fin and "VINTAGE SHALE" in fin["FIN-C1"].description
    assert any("Dimension missing for B9" in w for w in model.warnings)
    assert any(m.flags for m in model.material_indent if m.description == "Open Unit")
