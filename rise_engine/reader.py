"""PDF Reader: open a SOD PDF with pdfplumber and extract, per page, the
hardware-schedule cabinet rows, the room, and the finish legend.

This is the only module that depends on pdfplumber; everything downstream works
on plain dicts/dataclasses.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

import pdfplumber

from .schedule import detect_finish_legend, detect_room, extract_cabinet_rows
from .services import detect_service_points


@dataclass
class PageExtract:
    page_number: int
    room: str | None = None
    finish_legend: dict = field(default_factory=dict)
    cabinet_rows: list[dict] = field(default_factory=list)
    electrical_points: set = field(default_factory=set)
    plumbing_points: set = field(default_factory=set)
    text_len: int = 0


def read_sod(path: str) -> list[PageExtract]:
    """Read every page and return the extracted schedule data per page."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"PDF not found: {path}")

    pages: list[PageExtract] = []
    with pdfplumber.open(path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            tables = page.extract_tables() or []
            cabinet_rows = []
            for table in tables:
                cabinet_rows.extend(extract_cabinet_rows(table))
            electrical, plumbing = detect_service_points(text)
            pages.append(
                PageExtract(
                    page_number=page_number,
                    room=detect_room(tables, text),
                    finish_legend=detect_finish_legend(text),
                    cabinet_rows=cabinet_rows,
                    electrical_points=electrical,
                    plumbing_points=plumbing,
                    text_len=len(text.strip()),
                )
            )
    return pages
