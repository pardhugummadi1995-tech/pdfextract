"""Inventory Builder + Indent Generator.

Aggregate the per-page schedule rows into the RISE outputs:
Material Indent, cabinet list, room summary and category counts.
"""

from __future__ import annotations

from .hardware import FLAG_QTY_VERIFY, parse_hardware_cell
from .model import (
    Cabinet,
    CategoryCounts,
    IndentLine,
    ProjectModel,
    RoomSummaryRow,
)

FLAG_DIMENSION_MISSING = "Dimension Missing"


def _score(cab: Cabinet) -> int:
    return (1000 if cab.dimensions else 0) + len(cab.hardware)


def build_project(pages, source: str | None = None) -> ProjectModel:
    """Build the full project model from per-page extracts."""
    finish_legend: dict = {}
    raw: list[Cabinet] = []
    for page in pages:
        finish_legend.update(page.finish_legend or {})
        room = page.room or "Unassigned"
        for row in page.cabinet_rows:
            cab = Cabinet(
                code=row["code"],
                room=room,
                carcass=row.get("carcass", ""),
                shutter=row.get("shutter", ""),
                width=row.get("width"),
                depth=row.get("depth"),
                height=row.get("height"),
                page=page.page_number,
                hardware=parse_hardware_cell(row.get("hardware_text", "")),
            )
            raw.append(cab)

    # De-duplicate a cabinet repeated across internal/external elevations.
    by_key: dict[str, Cabinet] = {}
    for cab in raw:
        key = f"{cab.room}||{cab.code}"
        if key not in by_key or _score(cab) > _score(by_key[key]):
            by_key[key] = cab
    cabinets = sorted(by_key.values(), key=lambda c: (c.page or 0, c.code))
    for cab in cabinets:
        if not cab.dimensions:
            cab.flags.append(FLAG_DIMENSION_MISSING)

    material_indent = _build_indent(cabinets)
    material_indent += _build_finish_indent(cabinets, finish_legend)

    room_summary = _build_room_summary(cabinets)
    hardware_qty = sum(
        (line.total_qty or 0) for line in material_indent if line.category == "Hardware"
    )
    category_counts = CategoryCounts(
        rooms=len(room_summary),
        cabinets=len(cabinets),
        hardware_types=len([m for m in material_indent if m.category == "Hardware"]),
        hardware_qty=hardware_qty,
        finish_codes=len([m for m in material_indent if m.category == "Finish"]),
    )

    warnings = []
    for cab in cabinets:
        if FLAG_DIMENSION_MISSING in cab.flags:
            warnings.append(f"Dimension missing for {cab.code} ({cab.room}).")
    unknown = [m for m in material_indent if FLAG_QTY_VERIFY in m.flags]
    for m in unknown:
        warnings.append(f"Quantity verification required: {m.description}.")

    return ProjectModel(
        source=source,
        page_count=len(pages),
        cabinets=cabinets,
        material_indent=material_indent,
        room_summary=room_summary,
        category_counts=category_counts,
        finish_legend=finish_legend,
        warnings=warnings,
        unknown_items=unknown,
    )


def _build_indent(cabinets) -> list[IndentLine]:
    groups: dict[str, dict] = {}
    order: list[str] = []
    for cab in cabinets:
        for hw in cab.hardware:
            key = f"{hw.name.lower()}||{hw.unit or ''}"
            if key not in groups:
                groups[key] = {
                    "description": hw.name,
                    "qty": 0.0,
                    "qty_known": False,
                    "uom": hw.unit,
                    "rooms": set(),
                    "cabinets": set(),
                    "pages": set(),
                    "flags": set(),
                }
                order.append(key)
            g = groups[key]
            if hw.qty is not None:
                g["qty"] += hw.qty
                g["qty_known"] = True
            g["rooms"].add(cab.room)
            g["cabinets"].add(cab.code)
            if cab.page:
                g["pages"].add(cab.page)
            g["flags"].update(hw.flags)

    indent = []
    for i, key in enumerate(order, start=1):
        g = groups[key]
        indent.append(
            IndentLine(
                sku_code=f"HW-{i:03d}",
                description=g["description"],
                category="Hardware",
                total_qty=g["qty"] if g["qty_known"] else None,
                uom=g["uom"],
                rooms=sorted(g["rooms"]),
                cabinets=sorted(g["cabinets"]),
                pages=sorted(g["pages"]),
                flags=sorted(g["flags"]),
            )
        )
    return indent


def _build_finish_indent(cabinets, finish_legend) -> list[IndentLine]:
    use: dict[str, set] = {}
    for cab in cabinets:
        for code in (cab.carcass, cab.shutter):
            code = (code or "").strip()
            if len(code) == 2 and code[0] in "CS" and code[1].isdigit():
                use.setdefault(code, set()).add(f"{cab.room}||{cab.code}")
    out = []
    for code in sorted(use):
        desc = finish_legend.get(code)
        out.append(
            IndentLine(
                sku_code=f"FIN-{code}",
                description=f"{code} - {desc}" if desc else f"Finish {code}",
                category="Finish",
                total_qty=len(use[code]),
                uom="Set",
            )
        )
    return out


def _build_room_summary(cabinets) -> list[RoomSummaryRow]:
    rooms: dict[str, RoomSummaryRow] = {}
    for cab in cabinets:
        r = rooms.get(cab.room)
        if r is None:
            r = RoomSummaryRow(room=cab.room, cabinets=0, hardware_lines=0, estimated_inventory=0)
            rooms[cab.room] = r
        r.cabinets += 1
        r.hardware_lines += len(cab.hardware)
        r.estimated_inventory += sum((h.qty or 0) for h in cab.hardware)
    return sorted(rooms.values(), key=lambda x: x.room)
