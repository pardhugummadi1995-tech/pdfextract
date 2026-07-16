"""Parse a "Hardware Details" schedule cell into structured line items.

Real SOD schedules put hardware in a numbered list inside a single cell, e.g.::

    1. Hettich Onsys 105° Hinges -10Nos
    2. Handles In Client Scope
    3. Hafele Multipurpose Lock -1Pc
    4. Ebco Preminum Tower Bolt -2Nos

Quantities are written as ``-<n><Unit>`` (Nos/No/Pc/Pcs/Set). Items with no
quantity are flagged for verification (or as client scope).
"""

from __future__ import annotations

import re

from .model import HardwareItem

FLAG_QTY_VERIFY = "Quantity Verification Required"
FLAG_CLIENT_SCOPE = "Client Scope"

_QTY_RE = re.compile(r"-\s*(\d+)\s*(Nos|No|Pcs|Pc|Sets|Set)\b", re.IGNORECASE)
_UNIT = {
    "no": "No",
    "nos": "Nos",
    "pc": "Pcs",
    "pcs": "Pcs",
    "set": "Set",
    "sets": "Set",
}


def parse_hardware_cell(cell: str) -> list[HardwareItem]:
    """Return the hardware line items contained in a schedule cell."""
    items: list[HardwareItem] = []
    if not cell:
        return items
    # Split into numbered entries ("1. ...", "2. ...").
    for entry in re.split(r"\s*\d+\.\s+", cell):
        text = " ".join(entry.split())
        if not text:
            continue
        matches = list(_QTY_RE.finditer(text))
        if not matches:
            client = bool(re.search(r"client scope", text, re.IGNORECASE))
            items.append(
                HardwareItem(
                    name=text.strip(" -"),
                    qty=None,
                    unit=None,
                    flags=[FLAG_CLIENT_SCOPE if client else FLAG_QTY_VERIFY],
                )
            )
            continue
        name = text[: matches[0].start()].strip(" -") or text
        for m in matches:
            items.append(
                HardwareItem(name=name, qty=int(m.group(1)), unit=_UNIT[m.group(2).lower()])
            )
    return items
