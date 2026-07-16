# RISE Project Import Engine (Phase 1)

Import an Interior **Shop Order Drawing (SOD) PDF**, understand the project
structure, extract the inventory requirement, and generate a structured
**Material Indent** ready for RISE ERP.

**Fully offline — no cloud, no OCR, no AI/LLM.** Real SODs store the per-cabinet
requirement inside **ruled "Hardware Details" schedule tables**, so the engine
uses [`pdfplumber`](https://github.com/jsvine/pdfplumber) lattice table
extraction (the PDF's own border lines) to read them reliably.

> **Note on Phase 1 technology.** The original brief targeted a pure
> browser/PDF.js tool. Real customer SODs turned out to be CAD-exported drawing
> sets whose data lives in bordered tables mixed with heavy line-art; robust
> extraction requires true lattice table detection, which `pdfplumber` does
> reliably and a hand-rolled browser parser did not. The engine therefore runs
> as a small **local, offline Python tool** (no server, no network). It still
> produces a browsable **HTML report** plus JSON/CSV/Excel exports.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt      # runtime + test deps
# runtime only: pip install -r requirements.txt   (or: pip install -e .)
```

## Use

```bash
python -m rise_engine path/to/SOD.pdf                 # writes JSON/CSV/XLSX/HTML to ./out
python -m rise_engine path/to/SOD.pdf -o build        # choose output dir
python -m rise_engine path/to/SOD.pdf --formats csv html
python -m rise_engine path/to/SOD.pdf --print         # also print indent CSV to stdout
```

Open the generated `*-report.html` in any browser for the preview.

## Outputs (the expected schema)

1. **Material Indent** — `SKU Code, Item Description, Category, Room(s),
   Cabinet(s), Total Qty, UOM, Source Page(s), Flags`. Duplicate hardware is
   grouped and summed across cabinets/rooms; auto SKU codes (`HW-001`, `FIN-C1`).
2. **Cabinets & dimensions** — code, room, W×D×H, carcass/shutter finish, page.
3. **Room summary** — cabinets, hardware lines, estimated inventory per room.
4. **Category counts** — rooms, cabinets, hardware types, hardware qty, finishes.

## When it works

The engine reads **only the inventory** — it never interprets the sketches. It
works when the PDF is **text-based** (not scanned) and uses the ruled
`Cabinet Code | Carcass | Shutter | Sizes | Hardware Details` schedule tables.
For a different firm's template or a scanned/image PDF it will not extract; in
that case it does **not** emit a misleading empty indent — it reports
`recognized = False`, prints a clear reason, and the CLI exits with code `3`.
Keep uploads on a consistent SOD template for consistent results.

## Error handling / flags

- Unsupported/scanned PDF → **not recognised** (clear message, CLI exit code 3).
- Missing dimensions → cabinet flagged **Dimension Missing**.
- Missing quantity → item flagged **Quantity Verification Required**.
- Handles/appliances noted "In Client Scope" → flagged **Client Scope**.

## Modules (independent & reusable)

| Module | Responsibility |
| ------ | -------------- |
| `rise_engine/reader.py` | PDF Reader — pdfplumber tables/text per page |
| `rise_engine/schedule.py` | locate schedule table, map columns, room & finishes |
| `rise_engine/hardware.py` | parse the numbered hardware cell → items + qty/unit |
| `rise_engine/pipeline.py` | Inventory Builder + Indent Generator (aggregation) |
| `rise_engine/exporter.py` | JSON / CSV / Excel export |
| `rise_engine/report.py` | offline HTML preview report |
| `rise_engine/cli.py` | command-line entry point |

## Tests

```bash
pytest -q     # generates a synthetic ruled-table SOD fixture via reportlab
ruff check rise_engine tests
```

## Future integration (not implemented — Phase 1)

The Material Indent is clean/structured so later phases can validate against
Inventory Master, create missing SKUs, compare stock, raise Purchase
Requisitions, and sync with Procurement/Finance/AI.
