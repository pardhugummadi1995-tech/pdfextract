# AGENTS.md

## Cursor Cloud specific instructions

This repository contains two independent deliverables:

1. **`pdfextract`** — a Python package (PDF tables → CSV/TSV/JSON/Markdown, plus
   an inventory breakdown by floor/room).
2. **`rise-import-engine/`** — a standalone, offline browser app (SOD PDF →
   Material Indent for RISE ERP).

### pdfextract (Python package)

`pdfextract` is a Python package (src layout under `src/pdfextract/`) that
extracts tables from PDFs and converts them to CSV/TSV/JSON/Markdown. It exposes
a plugin registry, a bundled `PdfTableExtractor` (uses `pdfplumber`), a
`pdfextract` CLI, and a Python API (`pdfextract.extract` / `format_result`).

#### Environment

- The update script creates a `.venv` and installs the package editable with dev
  extras (`pip install -e ".[dev]"`). Activate it before running anything:
  `source .venv/bin/activate`.
- On a bare VM, the system package `python3.12-venv` is required to create
  virtualenvs (already handled during initial setup; reinstall with
  `sudo apt-get install -y python3.12-venv` if venv creation fails).

#### Common commands (run inside the venv)

- Lint: `ruff check .`
- Tests: `pytest -q`
- Build: `python -m build`
- Run CLI: `pdfextract path/to/file.pdf --format csv`

#### Non-obvious notes

- Tests do **not** commit binary PDF fixtures. `tests/conftest.py` generates a
  sample PDF at runtime with `reportlab` (a dev dependency), so `reportlab` must
  be installed (it is, via the `dev` extra) for the test suite to run.
- `pdfplumber` extracts each cell with intra-cell newlines; `PdfTableExtractor`
  collapses whitespace per cell. Keep that in mind when asserting exact strings.
- The reference plugin only claims `*.pdf` sources (`can_handle`). Registering a
  second plugin with the same `name` raises `ValueError` by design.

#### Inventory breakdown

- `pdfextract <pdf> --inventory` aggregates extracted rows into a
  project → floor → room → item quantity hierarchy (see `inventory.py` and
  `inventory_report.py`). Programmatic entry points: `build_inventory()` /
  `format_inventory()`.
- Columns are auto-detected from the header via `FIELD_KEYWORDS` in
  `inventory.py`; add synonyms there if a document uses unusual header names, or
  pass `--floor-col/--room-col/--item-col/--qty-col/--unit-col` (name or index).
- Inventory output formats are `text` (default), `csv`, `json` — distinct from
  the table-mode formats (`csv`/`tsv`/`json`/`markdown`). The CLI validates the
  `--format` value against the active mode.
- Rows with a blank floor/room inherit the last non-blank value above them, so
  "section header" style layouts (label only on the first row) aggregate
  correctly. Items are summed per (name, unit); differing units stay separate.

### RISE Project Import Engine (`rise-import-engine/`)

Standalone, offline browser app (HTML/CSS/JS + PDF.js) that imports an Interior
Shop Order Drawing (SOD) PDF and generates a Material Indent. No backend, no
build step, no npm dependencies (PDF.js is vendored in `vendor/`, tests use
Node's built-in runner).

- **Run it:** serve the folder over HTTP and open in a browser — it uses ES
  modules and a PDF.js web worker, so `file://` will NOT work.
  `cd rise-import-engine && python3 -m http.server 8080` → `http://localhost:8080/`.
- **Tests:** `cd rise-import-engine && node --test` (or `npm test`). The
  detector/builder modules are intentionally pure (no DOM, no PDF.js) so they run
  in Node; `pdfReader.js`, `uploader.js`, `exporter.js`, `ui/` are browser-only.
- **Sample fixture:** `samples/sample-sod.pdf` (regenerate with
  `python samples/generate_sample.py`, needs `reportlab`). It exercises multi-room
  / multi-cabinet detection, duplicate merging, a missing dimension, a
  qty-verification case, an unknown item, and the `POM40` edge case.
- **Non-obvious gotcha:** a cabinet code regex (`^[A-Z]{1,3}\d{1,2}[A-Z]?$`) also
  matches hardware tokens like `POM40`; `cabinetDetector` deliberately skips lines
  that contain a `qty + unit` so hardware is not misread as a cabinet. Keep that
  guard if you touch detection.
- **Adding hardware/room vocabulary:** extend the keyword lists / patterns in
  `src/constants.js` (single source of truth for all detectors).
