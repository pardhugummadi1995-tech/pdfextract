# AGENTS.md

## Cursor Cloud specific instructions

This repository is the **RISE Project Import Engine** — an offline Python tool
that reads an Interior Shop Order Drawing (SOD) PDF and generates a Material
Indent for RISE ERP. No cloud, no OCR, no AI.

### Environment / run / test

- The update script creates `.venv` and installs `requirements-dev.txt`. Activate
  it first: `source .venv/bin/activate`. (`python3.12-venv` is required to build
  the venv on a bare VM.)
- Run: `python -m rise_engine <SOD.pdf> -o out` → writes JSON/CSV/XLSX + an HTML
  report. See README for flags.
- Tests: `pytest -q`. Lint: `ruff check rise_engine tests`.

### Non-obvious notes (important)

- **Why Python, not the browser.** Real SODs are CAD-exported drawing sets whose
  data lives in bordered "Hardware Details" schedule tables surrounded by heavy
  vector line-art. Reliable extraction needs true lattice (ruled-cell) table
  detection — `pdfplumber` does this well; a hand-rolled PDF.js/text-flow parser
  produced scrambled rows. Do not "revert" to text-flow heuristics.
- The data the product needs (per-cabinet hardware + quantities + dimensions) is
  **only** in those schedule tables (on the elevation/base/wall-unit sheets),
  not on the floor-plan pages. Quantities are written as `-<n><Unit>`
  (Nos/No/Pc/Pcs/Set) inside a numbered list in one cell.
- Columns are mapped by header text in `schedule.py` (`Cabinet Code / Carcass /
  Shutter / Sizes / Hardware Details`) — robust to differing column counts. Add
  new room names to `ROOM_KEYWORDS` there.
- A cabinet that repeats on internal + external elevations is de-duplicated in
  `pipeline.py` (keep the richer instance) so quantities are not double-counted.
- Tests generate their own ruled-table SOD via `samples/generate_sample_sod.py`
  (needs `reportlab`); keep table `colWidths` within the page text area or
  pdfplumber will interleave adjacent cells.
- Do **not** commit customer SOD PDFs.
