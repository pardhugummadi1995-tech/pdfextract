"""Locate and interpret the hardware-schedule tables inside a SOD page.

Real SODs render the per-cabinet schedule as a bordered table with columns:
``Cabinet Code | Carcass | Shutter | Sizes | Hardware Details``. We rely on the
table's ruling lines (via pdfplumber) and map columns by their header text so
the parser is robust to layout differences between sheets.
"""

from __future__ import annotations

import re

CABINET_CODE_RE = re.compile(r"^[A-Z]{1,3}\d{1,2}[A-Z]?$")
_DIM_RE = re.compile(r"(\d{2,4})\s*[xX×]\s*(\d{2,4})\s*[xX×]\s*(\d{2,4})")
_FINISH_RE = re.compile(r"Finish\s+([CS]\d)\b[:\s]+(.+)", re.IGNORECASE)

ROOM_KEYWORDS = [
    "Master Bedroom",
    "Guest Bedroom",
    "Kids Bedroom",
    "Children Bedroom",
    "Living Room",
    "Living",
    "Dining",
    "Kitchen",
    "Utility",
    "Common Vanity",
    "Vanity",
    "Balcony",
    "Foyer",
    "Pooja",
    "Study",
    "Bedroom",
    "Bathroom",
    "Toilet",
    "Store",
]


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (text or "").lower())


def canonical_room(value: str):
    """Map an arbitrary room label to a canonical keyword (longest match)."""
    key = _norm(value)
    if not key:
        return None
    best = None
    for kw in ROOM_KEYWORDS:
        k = _norm(kw)
        if key == k or k in key:
            if best is None or len(k) > len(_norm(best)):
                best = kw
    return best


def parse_dimensions(sizes: str):
    m = _DIM_RE.search(sizes or "")
    if not m:
        return (None, None, None)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)))


def _cell(row, idx):
    if idx is None or idx < 0 or idx >= len(row):
        return ""
    return (row[idx] or "").strip()


def _find_header(table):
    """Return the row index and column mapping of the schedule header, or None."""
    for ri, row in enumerate(table):
        joined = " ".join((c or "") for c in row)
        if "Hardware Details" not in joined or "Cabinet" not in joined:
            continue
        cols = {"code": None, "carcass": None, "shutter": None, "sizes": None, "hardware": None}
        for ci, cell in enumerate(row):
            text = (cell or "").lower()
            if not text:
                continue
            if cols["code"] is None and ("cabinet" in text or "code" in text):
                cols["code"] = ci
            elif cols["carcass"] is None and "carcass" in text:
                cols["carcass"] = ci
            elif cols["shutter"] is None and "shutter" in text:
                cols["shutter"] = ci
            elif cols["sizes"] is None and "size" in text:
                cols["sizes"] = ci
            elif cols["hardware"] is None and "hardware" in text:
                cols["hardware"] = ci
        if cols["code"] is not None and cols["hardware"] is not None:
            return ri, cols
    return None


def extract_cabinet_rows(table):
    """Yield raw cabinet dicts from a schedule table, or [] if not a schedule."""
    header = _find_header(table)
    if not header:
        return []
    header_ri, cols = header
    rows = []
    for row in table[header_ri + 1 :]:
        code = _cell(row, cols["code"]).replace("\n", " ").strip()
        code = code.split()[0] if code else ""
        if not CABINET_CODE_RE.match(code):
            continue
        sizes = _cell(row, cols["sizes"])
        w, d, h = parse_dimensions(sizes)
        rows.append(
            {
                "code": code.upper(),
                "carcass": _cell(row, cols["carcass"]),
                "shutter": _cell(row, cols["shutter"]),
                "sizes": sizes,
                "width": w,
                "depth": d,
                "height": h,
                "hardware_text": _cell(row, cols["hardware"]),
            }
        )
    return rows


def detect_room(tables, page_text: str):
    """Determine the room for a page from its "DRAWING NAME" title block."""
    for table in tables:
        for row in table:
            for cell in row:
                if cell and "DRAWING NAME" in cell:
                    parts = [p.strip() for p in cell.split("\n") if p.strip()]
                    for p in parts[1:]:
                        room = canonical_room(p)
                        if room:
                            return room
    # Fallback: scan text lines.
    for line in (page_text or "").splitlines():
        room = canonical_room(line)
        if room and len(line.strip()) <= 30:
            return room
    return None


def detect_finish_legend(page_text: str) -> dict:
    legend = {}
    for line in (page_text or "").splitlines():
        m = _FINISH_RE.search(line)
        if m:
            legend.setdefault(m.group(1).upper(), m.group(2).strip())
    return legend
