"""Generate a self-contained, offline HTML preview report of the results."""

from __future__ import annotations

import html

from .model import ProjectModel


def _esc(value) -> str:
    return html.escape("" if value is None else str(value))


def _table(headers, rows) -> str:
    head = "".join(f"<th>{_esc(h)}</th>" for h in headers)
    body = "".join(
        "<tr>" + "".join(f"<td>{_esc(c)}</td>" for c in row) + "</tr>" for row in rows
    )
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def render_html(model: ProjectModel) -> str:
    counts = model.category_counts
    stat_cards = ""
    if counts:
        for label, value in [
            ("Rooms", counts.rooms),
            ("Cabinets", counts.cabinets),
            ("Hardware Types", counts.hardware_types),
            ("Hardware Qty", counts.hardware_qty),
            ("Finish Codes", counts.finish_codes),
            ("Electrical Points", counts.electrical_points),
            ("Plumbing Points", counts.plumbing_points),
        ]:
            stat_cards += f'<div class="stat"><div class="n">{_esc(value)}</div><div class="l">{_esc(label)}</div></div>'

    indent_rows = [
        [
            line.sku_code,
            line.description,
            line.category,
            ", ".join(line.rooms),
            ", ".join(line.cabinets),
            "" if line.total_qty is None else line.total_qty,
            line.uom,
            ", ".join(str(p) for p in line.pages),
            ", ".join(line.flags),
        ]
        for line in model.material_indent
    ]
    cab_rows = [
        [c.code, c.room, c.dimensions or "Dimension Missing", c.carcass, c.shutter, c.page]
        for c in model.cabinets
    ]
    room_rows = [
        [r.room, r.cabinets, r.hardware_lines, r.estimated_inventory, r.electrical_points, r.plumbing_points]
        for r in model.room_summary
    ]
    warn_list = "".join(f"<li>{_esc(w)}</li>" for w in model.warnings) or "<li>None</li>"

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>RISE Material Indent — {_esc(model.source or '')}</title>
<style>
 body{{font-family:Segoe UI,system-ui,Arial,sans-serif;margin:0;background:#f1f5f9;color:#0f172a}}
 header{{background:linear-gradient(120deg,#0f172a,#1e3a8a);color:#fff;padding:20px 28px}}
 h1{{margin:0;font-size:20px}} .sub{{color:#cbd5e1;font-size:13px}}
 main{{max-width:1100px;margin:0 auto;padding:24px 20px 60px}}
 .stats{{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:20px}}
 .stat{{background:#fff;border-radius:10px;box-shadow:0 1px 3px rgba(15,23,42,.1);padding:12px 18px;text-align:center;min-width:110px}}
 .stat .n{{font-size:24px;font-weight:800;color:#1d4ed8}} .stat .l{{font-size:12px;color:#64748b}}
 section{{background:#fff;border-radius:12px;box-shadow:0 1px 3px rgba(15,23,42,.1);margin-bottom:18px;padding:16px 18px}}
 h2{{font-size:15px;margin:0 0 12px}}
 table{{width:100%;border-collapse:collapse;font-size:13px}}
 th,td{{text-align:left;padding:7px 9px;border-bottom:1px solid #e2e8f0;vertical-align:top}}
 th{{background:#f8fafc;color:#64748b;font-size:11px;text-transform:uppercase}}
 .warn li{{color:#b45309}}
</style></head><body>
<header><h1>RISE Project Import Engine — Material Indent</h1>
<div class="sub">{_esc(model.source or '')} · {model.page_count} pages · Phase 1 (offline)</div></header>
<main>
 <div class="stats">{stat_cards}</div>
 <section><h2>Material Indent</h2>{_table(
    ["SKU","Description","Category","Room(s)","Cabinet(s)","Total Qty","UOM","Pages","Flags"], indent_rows)}</section>
 <section><h2>Cabinets &amp; Dimensions</h2>{_table(
    ["Cabinet","Room","W x D x H","Carcass","Shutter","Page"], cab_rows)}</section>
 <section><h2>Room Summary</h2>{_table(
    ["Room","No. of Cabinets","Hardware Items","Estimated Inventory","Electrical Pts","Plumbing Pts"], room_rows)}</section>
 <section class="warn"><h2>Validation &amp; Warnings ({len(model.warnings)})</h2><ul>{warn_list}</ul></section>
</main></body></html>"""


def write_html(model: ProjectModel, path: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(render_html(model))
