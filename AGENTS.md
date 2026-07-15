# AGENTS.md

## Cursor Cloud specific instructions

`pdfextract` is a Python package (src layout under `src/pdfextract/`) that
extracts tables from PDFs and converts them to CSV/TSV/JSON/Markdown. It exposes
a plugin registry, a bundled `PdfTableExtractor` (uses `pdfplumber`), a
`pdfextract` CLI, and a Python API (`pdfextract.extract` / `format_result`).

### Environment

- The update script creates a `.venv` and installs the package editable with dev
  extras (`pip install -e ".[dev]"`). Activate it before running anything:
  `source .venv/bin/activate`.
- On a bare VM, the system package `python3.12-venv` is required to create
  virtualenvs (already handled during initial setup; reinstall with
  `sudo apt-get install -y python3.12-venv` if venv creation fails).

### Common commands (run inside the venv)

- Lint: `ruff check .`
- Tests: `pytest -q`
- Build: `python -m build`
- Run CLI: `pdfextract path/to/file.pdf --format csv`

### Non-obvious notes

- Tests do **not** commit binary PDF fixtures. `tests/conftest.py` generates a
  sample PDF at runtime with `reportlab` (a dev dependency), so `reportlab` must
  be installed (it is, via the `dev` extra) for the test suite to run.
- `pdfplumber` extracts each cell with intra-cell newlines; `PdfTableExtractor`
  collapses whitespace per cell. Keep that in mind when asserting exact strings.
- The reference plugin only claims `*.pdf` sources (`can_handle`). Registering a
  second plugin with the same `name` raises `ValueError` by design.
