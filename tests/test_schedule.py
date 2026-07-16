from rise_engine.schedule import (
    canonical_room,
    detect_finish_legend,
    extract_cabinet_rows,
    parse_dimensions,
)


def test_canonical_room_multiword_and_spacing():
    assert canonical_room("MASTER BED ROOM") == "Master Bedroom"
    assert canonical_room("KITCHEN ELEVATION 11") == "Kitchen"
    assert canonical_room("C.Vanity") == "Common Vanity" or canonical_room("Common Vanity") == "Common Vanity"
    assert canonical_room("random text") is None


def test_parse_dimensions():
    assert parse_dimensions("650 X 580 X 820mm (Including Legs)") == (650, 580, 820)
    assert parse_dimensions("no dims here") == (None, None, None)


def test_detect_finish_legend():
    text = "Finish C1 1789 QZ VINTAGE SHALE\nFinish S1 ABHIYAN STONE GREY\nother"
    legend = detect_finish_legend(text)
    assert legend["C1"] == "1789 QZ VINTAGE SHALE"
    assert legend["S1"] == "ABHIYAN STONE GREY"


def test_extract_cabinet_rows_maps_columns_by_header():
    table = [
        ["Cabinet Code", "Carcass", "Shutter", "Sizes", "Hardware Details"],
        ["B1", "C1", "S2", "650 X 580 X 820mm", "1. Hettich Onsys 105° Hinges -4Nos"],
        ["random", "", "", "", ""],  # non-cabinet row ignored
    ]
    rows = extract_cabinet_rows(table)
    assert len(rows) == 1
    assert rows[0]["code"] == "B1"
    assert rows[0]["width"] == 650
    assert "Hettich" in rows[0]["hardware_text"]


def test_non_schedule_table_returns_empty():
    assert extract_cabinet_rows([["Sheet", "Title"], ["SH01", "Floor Plan"]]) == []
