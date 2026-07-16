# pdfextract

> This repository contains two independent deliverables:
>
> 1. **`pdfextract`** (below) — a Python package/CLI that extracts tabular data
>    from PDFs into CSV/TSV/JSON/Markdown, with an inventory breakdown by
>    floor/room.
> 2. **[`rise-import-engine/`](rise-import-engine/README.md)** — a standalone,
>    fully-offline browser app (HTML/CSS/JS + PDF.js) that imports an Interior
>    Shop Order Drawing (SOD) PDF and generates an ERP-ready Material Indent
>    (RISE Project Import Engine, Phase 1).

---

## pdfextract (Python package)

A plugin that **extracts tabular data from PDF files** and converts it into a
specific tabular format (CSV, TSV, JSON, or Markdown).

It ships as:

- a small **plugin architecture** (`ExtractionPlugin` + `PluginRegistry`) so a
  host application can register/select extraction backends, and
- a bundled reference plugin, `PdfTableExtractor`, built on
  [`pdfplumber`](https://github.com/jsvine/pdfplumber), plus
- a **CLI** (`pdfextract`) and a small **Python API**.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"     # dev extras: pytest, reportlab, ruff, build
# runtime-only: pip install -e .   (or: pip install -r requirements.txt)
```

## CLI usage

```bash
pdfextract report.pdf                  # print all tables as CSV (default)
pdfextract report.pdf --format json    # convert to JSON
pdfextract report.pdf --format markdown
pdfextract report.pdf -o out.csv       # write to a file
pdfextract report.pdf --pages 1 2      # only pages 1 and 2
pdfextract report.pdf --no-header      # do not treat row 1 as a header
pdfextract report.pdf --password secret
```

Example:

```text
$ pdfextract invoice.pdf
Item,Qty,Unit Price,Total
Widget A,3,$10.00,$30.00
Widget B,5,$7.50,$37.50
```

## Inventory breakdown (by floor & room)

For interior / architectural documents (customer requirement sheets, room
schedules, furniture & fixture lists), `--inventory` interprets the extracted
rows as *item quantities* and aggregates them into a hierarchy:

```
Project
  └─ Floor
       └─ Room
            └─ Item -> total quantity (+ unit)
```

```bash
pdfextract schedule.pdf --inventory              # indented summary (default)
pdfextract schedule.pdf --inventory -f csv       # flat, spreadsheet-friendly
pdfextract schedule.pdf --inventory -f json      # nested hierarchy
```

Columns (floor / room / item / quantity / unit) are **auto-detected** from the
header using keyword synonyms (e.g. `Level`→floor, `Space`→room, `Material`→item,
`Nos`→quantity, `UOM`→unit). Override any of them explicitly:

```bash
pdfextract schedule.pdf --inventory \
    --floor-col Level --room-col Space --item-col Material --qty-col Nos --unit-col UOM
```

You also get per-room subtotals, per-floor subtotals, and project-wide totals
(items with the same name are summed across rooms/floors; different units are
kept separate). Programmatic use:

```python
from pdfextract import extract, build_inventory, format_inventory

project = build_inventory(extract("schedule.pdf"))
print(format_inventory(project, "text"))     # text | csv | json
for floor in project.floors:
    for room in floor.rooms:
        for item in room.items:
            print(floor.floor, room.room, item.name, item.quantity, item.unit)
```

## Python API

```python
from pdfextract import extract, format_result

result = extract("invoice.pdf")          # uses the default plugin registry
print(format_result(result, "csv"))      # csv | tsv | json | markdown

for table in result.tables:
    print(table.header, table.rows)
```

### Adding your own plugin

```python
from pdfextract import ExtractionPlugin, ExtractionResult, default_registry

class MyPlugin(ExtractionPlugin):
    name = "my_plugin"
    def can_handle(self, source): return source.endswith(".myext")
    def extract(self, source, **opts): return ExtractionResult(...)

default_registry.register(MyPlugin())
```

## Development

```bash
ruff check .      # lint
pytest -q         # tests (generate their own sample PDF via reportlab)
python -m build   # build wheel/sdist
```
