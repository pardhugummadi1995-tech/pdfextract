"""Turn extracted PDF tables into a project inventory broken down by area.

Interior / architectural documents (customer requirement sheets, room schedules,
BOQs, furniture & fixture lists) typically contain rows describing *which item*
appears, *how many* (quantity), and *where* (floor / room). This module converts
the raw :class:`~pdfextract.core.Table` rows produced by an extraction plugin
into a normalized inventory and aggregates the quantities into a hierarchy::

    Project
      └─ Floor
           └─ Room
                └─ Item  ->  total quantity (+ unit)

Column layouts vary between documents, so columns are auto-detected from header
keywords and can be overridden explicitly via :class:`ColumnMapping`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .core import ExtractionResult, Table

DEFAULT_FLOOR = "Unspecified floor"
DEFAULT_ROOM = "Unspecified room"

# Header keywords used to auto-detect the meaning of each column. Order within a
# list encodes preference when several columns could match.
FIELD_KEYWORDS: dict[str, list[str]] = {
    "floor": ["floor", "level", "storey", "story"],
    "room": ["room", "space", "area", "zone", "location", "unit type"],
    "item": [
        "item",
        "material",
        "product",
        "description",
        "furniture",
        "fixture",
        "component",
        "element",
        "name",
    ],
    "quantity": ["quantity", "qty", "count", "nos", "no.", "number", "units"],
    "unit": ["uom", "unit", "measure"],
}

_NUMBER_RE = re.compile(r"-?\d+(?:\.\d+)?")


def parse_quantity(raw: object) -> float:
    """Parse a quantity from a messy cell value.

    Handles values such as ``"3"``, ``"x2"``, ``"2 pcs"``, ``"1,200"`` and
    returns ``0.0`` when no number is present.
    """
    if raw is None:
        return 0.0
    if isinstance(raw, (int, float)):
        return float(raw)
    match = _NUMBER_RE.search(str(raw).replace(",", ""))
    return float(match.group()) if match else 0.0


def format_quantity(value: float) -> str:
    """Render a quantity without a trailing ``.0`` for whole numbers."""
    if value == int(value):
        return str(int(value))
    return f"{value:g}"


@dataclass
class ColumnMapping:
    """Explicit column selection for inventory parsing.

    Each field may be a column *name* (matched case-insensitively against the
    table header, exact match preferred over substring) or a 0-based integer
    *index*. Any field left as ``None`` is auto-detected from the header.
    """

    floor: object | None = None
    room: object | None = None
    item: object | None = None
    quantity: object | None = None
    unit: object | None = None

    def resolve(self, header: list[str] | None) -> dict[str, int | None]:
        """Resolve each logical field to a concrete column index for ``header``."""
        resolved: dict[str, int | None] = {}
        lowered = [h.strip().lower() for h in header] if header else []
        for logical in ("floor", "room", "item", "quantity", "unit"):
            override = getattr(self, logical)
            if override is not None:
                resolved[logical] = _resolve_override(override, lowered)
            else:
                resolved[logical] = _auto_detect(logical, lowered)
        return resolved


def _resolve_override(override: object, lowered: list[str]) -> int | None:
    if isinstance(override, int):
        return override
    text = str(override).strip()
    if text.isdigit():
        return int(text)
    key = text.lower()
    for i, name in enumerate(lowered):
        if name == key:
            return i
    for i, name in enumerate(lowered):
        if key in name:
            return i
    return None


def _auto_detect(logical: str, lowered: list[str]) -> int | None:
    if not lowered:
        return None
    for keyword in FIELD_KEYWORDS[logical]:
        for i, name in enumerate(lowered):
            if name == keyword:
                return i
    for keyword in FIELD_KEYWORDS[logical]:
        for i, name in enumerate(lowered):
            if keyword in name:
                return i
    return None


@dataclass
class InventoryItem:
    """A single inventory line item extracted from a document row."""

    name: str
    quantity: float
    unit: str | None = None
    room: str = DEFAULT_ROOM
    floor: str = DEFAULT_FLOOR
    page: int | None = None


@dataclass
class ItemTotal:
    name: str
    quantity: float
    unit: str | None = None

    @property
    def display_quantity(self) -> str:
        return format_quantity(self.quantity)


@dataclass
class RoomInventory:
    room: str
    items: list[ItemTotal] = field(default_factory=list)

    @property
    def total_quantity(self) -> float:
        return sum(i.quantity for i in self.items)


@dataclass
class FloorInventory:
    floor: str
    rooms: list[RoomInventory] = field(default_factory=list)

    @property
    def total_quantity(self) -> float:
        return sum(r.total_quantity for r in self.rooms)

    def item_totals(self) -> list[ItemTotal]:
        return _sum_items(item for room in self.rooms for item in room.items)


@dataclass
class ProjectInventory:
    """The full aggregated breakdown plus the flat source line items."""

    floors: list[FloorInventory] = field(default_factory=list)
    items: list[InventoryItem] = field(default_factory=list)

    @property
    def total_quantity(self) -> float:
        return sum(f.total_quantity for f in self.floors)

    def item_totals(self) -> list[ItemTotal]:
        return _sum_items(
            ItemTotal(i.name, i.quantity, i.unit) for i in self.items
        )


def _sum_items(items) -> list[ItemTotal]:
    """Sum quantities for items sharing the same (name, unit), keep first-seen order."""
    order: list[tuple[str, str | None]] = []
    bucket: dict[tuple[str, str | None], ItemTotal] = {}
    for it in items:
        key = (it.name, it.unit)
        if key not in bucket:
            bucket[key] = ItemTotal(it.name, 0.0, it.unit)
            order.append(key)
        bucket[key].quantity += it.quantity
    return [bucket[k] for k in order]


def build_line_items(
    result: ExtractionResult,
    mapping: ColumnMapping | None = None,
) -> list[InventoryItem]:
    """Flatten every table in ``result`` into inventory line items."""
    mapping = mapping or ColumnMapping()
    line_items: list[InventoryItem] = []
    for table in result.tables:
        line_items.extend(_line_items_from_table(table, mapping))
    return line_items


def _cell(row: list[str], idx: int | None) -> str:
    if idx is None or idx < 0 or idx >= len(row):
        return ""
    return row[idx].strip()


def _line_items_from_table(table: Table, mapping: ColumnMapping) -> list[InventoryItem]:
    cols = mapping.resolve(table.header)
    if cols["item"] is None:
        # Without an item column there is nothing meaningful to inventory.
        return []

    items: list[InventoryItem] = []
    # Track last seen floor/room so grouped layouts (value only on first row of a
    # section, blank thereafter) carry the label down subsequent rows.
    last_floor = DEFAULT_FLOOR
    last_room = DEFAULT_ROOM
    for row in table.normalized_rows():
        name = _cell(row, cols["item"])
        floor = _cell(row, cols["floor"]) or last_floor
        room = _cell(row, cols["room"]) or last_room
        last_floor, last_room = floor, room
        if not name:
            continue
        unit = _cell(row, cols["unit"]) or None
        if cols["quantity"] is not None:
            quantity = parse_quantity(_cell(row, cols["quantity"]))
        else:
            quantity = 1.0
        items.append(
            InventoryItem(
                name=name,
                quantity=quantity,
                unit=unit,
                room=room,
                floor=floor,
                page=table.page,
            )
        )
    return items


def build_inventory(
    result: ExtractionResult,
    mapping: ColumnMapping | None = None,
) -> ProjectInventory:
    """Build the aggregated project → floor → room → item breakdown."""
    line_items = build_line_items(result, mapping)
    return aggregate(line_items)


def aggregate(line_items: list[InventoryItem]) -> ProjectInventory:
    """Aggregate flat line items into the floor/room hierarchy."""
    floor_order: list[str] = []
    room_order: dict[str, list[str]] = {}
    # (floor, room, item, unit) -> summed quantity
    grouped: dict[tuple[str, str, str, str | None], float] = {}

    for it in line_items:
        if it.floor not in room_order:
            room_order[it.floor] = []
            floor_order.append(it.floor)
        if it.room not in room_order[it.floor]:
            room_order[it.floor].append(it.room)
        key = (it.floor, it.room, it.name, it.unit)
        grouped[key] = grouped.get(key, 0.0) + it.quantity

    floors: list[FloorInventory] = []
    for floor in floor_order:
        rooms: list[RoomInventory] = []
        for room in room_order[floor]:
            item_totals = [
                ItemTotal(name=name, quantity=qty, unit=unit)
                for (f, r, name, unit), qty in grouped.items()
                if f == floor and r == room
            ]
            rooms.append(RoomInventory(room=room, items=item_totals))
        floors.append(FloorInventory(floor=floor, rooms=rooms))

    return ProjectInventory(floors=floors, items=list(line_items))
