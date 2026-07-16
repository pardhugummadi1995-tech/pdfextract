"""Apply a human-reviewed CSV back onto the model before final export.

Workflow:
  1. ``--review``        -> writes ``<base>-review.csv`` (Approved Qty column).
  2. a human edits Approved Qty / Reviewer Notes and fixes any flagged rows.
  3. ``--apply-review``  -> reads the edited CSV, overrides quantities, clears
     resolved flags, marks lines reviewed, and writes the final outputs.
"""

from __future__ import annotations

import csv

from .hardware import FLAG_CLIENT_SCOPE, FLAG_QTY_VERIFY
from .model import CategoryCounts, ProjectModel


def _num(value: str):
    value = (value or "").strip()
    if value == "":
        return None
    try:
        f = float(value)
        return int(f) if f == int(f) else f
    except ValueError:
        return None


def apply_review(model: ProjectModel, csv_path: str) -> ProjectModel:
    """Apply an edited review CSV (keyed by SKU Code) to ``model`` in place."""
    with open(csv_path, encoding="utf-8-sig", newline="") as fh:
        rows = {r["SKU Code"].strip(): r for r in csv.DictReader(fh) if r.get("SKU Code")}

    for line in model.material_indent:
        row = rows.get(line.sku_code)
        if not row:
            continue
        approved = _num(row.get("Approved Qty", ""))
        notes = (row.get("Reviewer Notes", "") or "").strip()
        desc = (row.get("Item Description", "") or "").strip()
        if desc:
            line.description = desc
        if approved is not None:
            line.total_qty = approved
            # An approved quantity resolves the "needs a number" flags.
            line.flags = [f for f in line.flags if f not in (FLAG_QTY_VERIFY, FLAG_CLIENT_SCOPE)]
        line.review_notes = notes
        line.reviewed = True

    # Recompute quantity-derived counts from the reviewed indent.
    counts = model.category_counts
    if counts:
        model.category_counts = CategoryCounts(
            rooms=counts.rooms,
            cabinets=counts.cabinets,
            hardware_types=counts.hardware_types,
            hardware_qty=sum(
                (m.total_qty or 0) for m in model.material_indent if m.category == "Hardware"
            ),
            finish_codes=counts.finish_codes,
            electrical_points=counts.electrical_points,
            plumbing_points=counts.plumbing_points,
        )
    model.unknown_items = [m for m in model.material_indent if FLAG_QTY_VERIFY in m.flags]
    model.reviewed = True
    return model
