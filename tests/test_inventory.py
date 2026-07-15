import json

import pytest

from pdfextract import build_inventory, extract, format_inventory
from pdfextract.core import ExtractionResult, Table
from pdfextract.inventory import (
    ColumnMapping,
    aggregate,
    build_line_items,
    format_quantity,
    parse_quantity,
)


def _result(header, rows, page=1):
    return ExtractionResult(tables=[Table(header=header, rows=rows, page=page)])


@pytest.mark.parametrize(
    "raw,expected",
    [("3", 3.0), ("x2", 2.0), ("2 pcs", 2.0), ("1,200", 1200.0), ("", 0.0), (None, 0.0), (5, 5.0)],
)
def test_parse_quantity(raw, expected):
    assert parse_quantity(raw) == expected


def test_format_quantity():
    assert format_quantity(3.0) == "3"
    assert format_quantity(2.5) == "2.5"


def test_column_auto_detection():
    mapping = ColumnMapping()
    cols = mapping.resolve(["Floor", "Room", "Item", "Quantity", "Unit"])
    assert cols == {"floor": 0, "room": 1, "item": 2, "quantity": 3, "unit": 4}


def test_column_detection_with_synonyms():
    cols = ColumnMapping().resolve(["Level", "Space", "Material", "Nos", "UOM"])
    assert cols == {"floor": 0, "room": 1, "item": 2, "quantity": 3, "unit": 4}


def test_column_override_by_name_and_index():
    mapping = ColumnMapping(item="Widget", quantity=2)
    cols = mapping.resolve(["Zone", "Widget", "Count"])
    assert cols["item"] == 1
    assert cols["quantity"] == 2


def test_build_line_items_basic():
    result = _result(
        ["Floor", "Room", "Item", "Quantity", "Unit"],
        [["G", "Kitchen", "Cabinet", "6", "nos"]],
    )
    items = build_line_items(result)
    assert len(items) == 1
    it = items[0]
    assert (it.floor, it.room, it.name, it.quantity, it.unit) == (
        "G",
        "Kitchen",
        "Cabinet",
        6.0,
        "nos",
    )


def test_grouped_layout_carries_floor_and_room_down():
    # Floor/room only present on first row of a section, blank thereafter.
    result = _result(
        ["Floor", "Room", "Item", "Quantity"],
        [
            ["Ground", "Living", "Sofa", "2"],
            ["", "", "Table", "1"],
            ["", "Kitchen", "Cabinet", "6"],
        ],
    )
    items = build_line_items(result)
    assert [(i.floor, i.room, i.name) for i in items] == [
        ("Ground", "Living", "Sofa"),
        ("Ground", "Living", "Table"),
        ("Ground", "Kitchen", "Cabinet"),
    ]


def test_aggregate_sums_within_room_and_totals():
    result = _result(
        ["Floor", "Room", "Item", "Quantity"],
        [
            ["G", "Kitchen", "Cabinet", "6"],
            ["G", "Kitchen", "Cabinet", "2"],  # same item in same room -> summed
            ["G", "Living", "Sofa", "1"],
            ["F1", "Bedroom", "Sofa", "3"],
        ],
    )
    project = build_inventory(result)

    floors = {f.floor: f for f in project.floors}
    assert set(floors) == {"G", "F1"}

    kitchen = next(r for r in floors["G"].rooms if r.room == "Kitchen")
    cabinet = next(i for i in kitchen.items if i.name == "Cabinet")
    assert cabinet.quantity == 8.0

    # Project-wide total for Sofa spans two floors.
    project_totals = {i.name: i.quantity for i in project.item_totals()}
    assert project_totals["Sofa"] == 4.0
    assert project.total_quantity == 12.0

    # Floor subtotal.
    assert floors["G"].total_quantity == 9.0


def test_no_item_column_yields_empty():
    result = _result(["Floor", "Room"], [["G", "Kitchen"]])
    assert build_line_items(result) == []


def test_missing_quantity_column_defaults_to_one():
    result = _result(["Room", "Item"], [["Kitchen", "Cabinet"], ["Kitchen", "Sink"]])
    project = build_inventory(result)
    assert project.total_quantity == 2.0


def test_default_floor_and_room_labels():
    result = _result(["Item", "Quantity"], [["Cabinet", "3"]])
    project = build_inventory(result)
    assert project.floors[0].floor == "Unspecified floor"
    assert project.floors[0].rooms[0].room == "Unspecified room"


def test_format_inventory_text_json_csv():
    result = _result(
        ["Floor", "Room", "Item", "Quantity"],
        [["G", "Kitchen", "Cabinet", "6"], ["G", "Living", "Sofa", "2"]],
    )
    project = build_inventory(result)

    text = format_inventory(project, "text")
    assert "Floor: G" in text
    assert "Room: Kitchen" in text
    assert "Cabinet: 6" in text

    payload = json.loads(format_inventory(project, "json"))
    assert payload["floors"][0]["floor"] == "G"
    rooms = {r["room"]: r for r in payload["floors"][0]["rooms"]}
    assert rooms["Kitchen"]["items"][0]["quantity"] == 6.0

    csv_out = format_inventory(project, "csv")
    assert "Level,Floor,Room,Item,Unit,Quantity" in csv_out
    assert "item,G,Kitchen,Cabinet,,6" in csv_out
    assert "project_total,,,Cabinet,,6" in csv_out


def test_format_inventory_unknown_format():
    project = build_inventory(_result(["Item"], [["X"]]))
    with pytest.raises(ValueError):
        format_inventory(project, "markdown")


def test_end_to_end_pdf_inventory(inventory_pdf):
    result = extract(inventory_pdf)
    project = build_inventory(result)

    floors = {f.floor: f for f in project.floors}
    assert set(floors) == {"Ground Floor", "First Floor"}

    # Sofa appears in 3 rooms across 2 floors: 2 + 1 + 1 = 4.
    totals = {i.name: i.quantity for i in project.item_totals()}
    assert totals["Sofa"] == 4.0
    assert totals["Cabinet"] == 6.0

    ground = floors["Ground Floor"]
    kitchen = next(r for r in ground.rooms if r.room == "Kitchen")
    assert {i.name: i.quantity for i in kitchen.items} == {"Cabinet": 6.0, "Sofa": 1.0}


def test_aggregate_direct_keeps_units_separate():
    from pdfextract.inventory import InventoryItem

    items = [
        InventoryItem("Tile", 10, "sqm", "Bath", "G"),
        InventoryItem("Tile", 5, "box", "Bath", "G"),
    ]
    project = aggregate(items)
    room = project.floors[0].rooms[0]
    names_units = {(i.name, i.unit): i.quantity for i in room.items}
    assert names_units == {("Tile", "sqm"): 10.0, ("Tile", "box"): 5.0}
