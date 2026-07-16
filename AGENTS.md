# AGENTS.md

## Cursor Cloud specific instructions

This repository is the **RISE Project Import Engine** — a standalone, offline
browser app (HTML/CSS/JS + PDF.js) that imports an Interior Shop Order Drawing
(SOD) PDF and generates a Material Indent for RISE ERP. No backend, no build
step, no npm dependencies (PDF.js is vendored in `vendor/`, tests use Node's
built-in runner).

- **Run it:** serve the repo root over HTTP and open in a browser — it uses ES
  modules and a PDF.js web worker, so `file://` will NOT work.
  `python3 -m http.server 8080` → `http://localhost:8080/`.
- **Tests:** `node --test` (or `npm test`) from the repo root. The
  detector/builder modules are intentionally pure (no DOM, no PDF.js) so they run
  in Node; `pdfReader.js`, `uploader.js`, `exporter.js`, `ui/` are browser-only.
- **Sample fixture:** `samples/sample-sod.pdf` (regenerate with
  `python samples/generate_sample.py`, which needs `reportlab` — the update
  script installs it into `.venv`). It exercises multi-room / multi-cabinet
  detection, duplicate merging, a missing dimension, a qty-verification case, an
  unknown item, and the `POM40` edge case.
- **Non-obvious gotcha:** a cabinet code regex (`^[A-Z]{1,3}\d{1,2}[A-Z]?$`) also
  matches hardware tokens like `POM40`; `cabinetDetector` deliberately skips lines
  that contain a `qty + unit` so hardware is not misread as a cabinet. Keep that
  guard if you touch detection.
- **Adding hardware/room vocabulary:** extend the keyword lists / patterns in
  `src/constants.js` (single source of truth for all detectors).
