from rise_engine.hardware import (
    FLAG_CLIENT_SCOPE,
    FLAG_QTY_VERIFY,
    parse_hardware_cell,
)


def test_parse_numbered_hardware():
    cell = (
        "1. Hettich Onsys 105° Hinges -4Nos "
        "2. Ebco Cylindrical Legs -6Nos "
        "3. Ebco Door Buffers -4Pc"
    )
    items = parse_hardware_cell(cell)
    by = {i.name: i for i in items}
    assert by["Hettich Onsys 105° Hinges"].qty == 4
    assert by["Hettich Onsys 105° Hinges"].unit == "Nos"
    assert by["Ebco Cylindrical Legs"].qty == 6
    assert by["Ebco Door Buffers"].unit == "Pcs"


def test_client_scope_and_missing_qty_flags():
    items = parse_hardware_cell("1. Handles In Client Scope 2. Concealed Wall Brackets")
    by = {i.name: i for i in items}
    assert by["Handles In Client Scope"].qty is None
    assert FLAG_CLIENT_SCOPE in by["Handles In Client Scope"].flags
    assert FLAG_QTY_VERIFY in by["Concealed Wall Brackets"].flags


def test_multiple_quantities_in_one_entry():
    items = parse_hardware_cell("1. Designer Drawers Medium -2Nos & Large -1No")
    qtys = sorted((i.qty, i.unit) for i in items)
    assert qtys == [(1, "No"), (2, "Nos")]


def test_empty_cell():
    assert parse_hardware_cell("") == []
