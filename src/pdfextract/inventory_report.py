"""Render a :class:`~pdfextract.inventory.ProjectInventory` for output.

Three representations are supported:

* ``text``  – an indented tree with per-room / per-floor / project subtotals.
* ``csv``   – a flat, spreadsheet-friendly breakdown (one row per item per room)
              plus a ``Level`` column so subtotal rows are distinguishable.
* ``json``  – the full nested hierarchy.
"""

from __future__ import annotations

import csv
import io
import json

from .inventory import ProjectInventory, format_quantity

INVENTORY_FORMATS = ("text", "csv", "json")


def to_text(project: ProjectInventory) -> str:
    lines: list[str] = []
    lines.append("Project inventory breakdown")
    lines.append(f"Total items (all quantities): {format_quantity(project.total_quantity)}")
    lines.append("")
    for floor in project.floors:
        lines.append(f"Floor: {floor.floor}  (total qty: {format_quantity(floor.total_quantity)})")
        for room in floor.rooms:
            lines.append(
                f"  Room: {room.room}  (total qty: {format_quantity(room.total_quantity)})"
            )
            for item in room.items:
                unit = f" {item.unit}" if item.unit else ""
                lines.append(f"    - {item.name}: {item.display_quantity}{unit}")
        totals = floor.item_totals()
        if totals:
            lines.append(f"  Floor subtotal by item ({floor.floor}):")
            for item in totals:
                unit = f" {item.unit}" if item.unit else ""
                lines.append(f"    * {item.name}: {item.display_quantity}{unit}")
        lines.append("")
    project_totals = project.item_totals()
    if project_totals:
        lines.append("Project totals by item:")
        for item in project_totals:
            unit = f" {item.unit}" if item.unit else ""
            lines.append(f"  * {item.name}: {item.display_quantity}{unit}")
    return "\n".join(lines).rstrip() + "\n"


def to_csv(project: ProjectInventory) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["Level", "Floor", "Room", "Item", "Unit", "Quantity"])
    for floor in project.floors:
        for room in floor.rooms:
            for item in room.items:
                writer.writerow(
                    [
                        "item",
                        floor.floor,
                        room.room,
                        item.name,
                        item.unit or "",
                        item.display_quantity,
                    ]
                )
    # Floor subtotals per item.
    for floor in project.floors:
        for item in floor.item_totals():
            writer.writerow(
                ["floor_total", floor.floor, "", item.name, item.unit or "", item.display_quantity]
            )
    # Project subtotals per item.
    for item in project.item_totals():
        writer.writerow(
            ["project_total", "", "", item.name, item.unit or "", item.display_quantity]
        )
    return buffer.getvalue()


def to_json(project: ProjectInventory) -> str:
    payload = {
        "total_quantity": project.total_quantity,
        "project_totals_by_item": [
            {"item": i.name, "unit": i.unit, "quantity": i.quantity}
            for i in project.item_totals()
        ],
        "floors": [
            {
                "floor": floor.floor,
                "total_quantity": floor.total_quantity,
                "floor_totals_by_item": [
                    {"item": i.name, "unit": i.unit, "quantity": i.quantity}
                    for i in floor.item_totals()
                ],
                "rooms": [
                    {
                        "room": room.room,
                        "total_quantity": room.total_quantity,
                        "items": [
                            {"item": i.name, "unit": i.unit, "quantity": i.quantity}
                            for i in room.items
                        ],
                    }
                    for room in floor.rooms
                ],
            }
            for floor in project.floors
        ],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


_FORMATTERS = {"text": to_text, "csv": to_csv, "json": to_json}


def format_inventory(project: ProjectInventory, fmt: str) -> str:
    try:
        formatter = _FORMATTERS[fmt]
    except KeyError as exc:
        raise ValueError(
            f"unknown inventory format {fmt!r}; choose from {INVENTORY_FORMATS}"
        ) from exc
    return formatter(project)
