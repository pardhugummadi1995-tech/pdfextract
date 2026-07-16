"""Data model for the extracted project and generated Material Indent."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class HardwareItem:
    """A single hardware line parsed from a cabinet's schedule cell."""

    name: str
    qty: float | None
    unit: str | None
    flags: list[str] = field(default_factory=list)


@dataclass
class Cabinet:
    """A cabinet detected in a hardware-schedule table."""

    code: str
    room: str
    carcass: str = ""
    shutter: str = ""
    width: int | None = None
    depth: int | None = None
    height: int | None = None
    page: int | None = None
    hardware: list[HardwareItem] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)

    @property
    def dimensions(self) -> str | None:
        if self.width and self.depth and self.height:
            return f"{self.width} x {self.depth} x {self.height}"
        return None


@dataclass
class IndentLine:
    """One row of the Material Indent (grouped across cabinets/rooms)."""

    sku_code: str
    description: str
    category: str
    total_qty: float | None
    uom: str | None
    rooms: list[str] = field(default_factory=list)
    cabinets: list[str] = field(default_factory=list)
    pages: list[int] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)
    reviewed: bool = False
    review_notes: str = ""


@dataclass
class RoomSummaryRow:
    room: str
    cabinets: int
    hardware_lines: int
    estimated_inventory: float
    electrical_points: int = 0
    plumbing_points: int = 0


@dataclass
class CategoryCounts:
    rooms: int
    cabinets: int
    hardware_types: int
    hardware_qty: float
    finish_codes: int
    electrical_points: int = 0
    plumbing_points: int = 0


@dataclass
class ProjectModel:
    """The full extracted project + generated outputs."""

    source: str | None = None
    page_count: int = 0
    cabinets: list[Cabinet] = field(default_factory=list)
    material_indent: list[IndentLine] = field(default_factory=list)
    room_summary: list[RoomSummaryRow] = field(default_factory=list)
    category_counts: CategoryCounts | None = None
    finish_legend: dict = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    unknown_items: list[IndentLine] = field(default_factory=list)
    reviewed: bool = False
