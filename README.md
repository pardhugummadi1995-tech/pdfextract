# RISE Project Import Engine (Phase 1)

A **standalone, fully-offline** browser application that imports an Interior
**Shop Order Drawing (SOD) PDF**, understands the project structure, extracts the
inventory (hardware) requirements, and generates an ERP-ready **Material Indent**
for RISE.

- **No backend. No OCR. No AI/LLM.** Pure `HTML` + `CSS` + `JavaScript` + `PDF.js`.
- PDF.js is **vendored locally** (`vendor/`) so the app runs with zero network access.

> Phase 1 scope: read the PDF → understand the project → extract inventory →
> generate a structured Material Indent. It does **not** integrate with
> Procurement, Inventory Master, Finance or AI. The output is clean structured
> data designed to feed those later phases.

## Run it

Because the app uses ES modules and a PDF.js web worker, serve it over HTTP
(opening `index.html` via `file://` will not work). Any static server works:

```bash
python3 -m http.server 8080
# then open http://localhost:8080/
```

Upload a SOD PDF (drag & drop or Browse). A sample is provided at
`samples/sample-sod.pdf` (regenerate with `python samples/generate_sample.py`).

## Two outputs

1. **Project Structure** — the digital representation of the design:

   ```
   Aurora Residence
   ├── Kitchen
   │   ├── B1  (600 x 580 x 850)
   │   ├── B2  (900 x 580 x 850)
   │   └── W1  (600 x 320 x 700)
   ├── Living
   │   └── TV1 (1800 x 450 x 600)
   └── Master Bedroom
       ├── WR1 (2100 x 600 x 2400)
       └── WR2
   ```

2. **Material Indent** — the operational document (grouped, duplicates summed):

   | Item Code | Description | Total Qty | UOM | Source Rooms | Source Cabinets |
   | --------- | ----------- | --------- | --- | ------------ | --------------- |
   | AUTO-001  | Hettich 105 Hinge | 34 | Nos | Kitchen, Master Bedroom | B1, B2, W1, WR1, WR2 |

Export as **JSON**, **CSV**, or **Excel**.

## Workflow

Upload → Parse (PDF.js: text, coordinates, page, font size, bounding boxes) →
Detect project info → Detect rooms → Detect cabinets → Extract dimensions →
Extract hardware → Extract finish codes → Build inventory requirement →
Generate Material Indent → Preview → Export.

## Module structure

Each module is independent and reusable. The detectors/builders are **pure**
(no DOM, no PDF.js) so they can be unit-tested in Node.

| Module | File | Responsibility |
| ------ | ---- | -------------- |
| Uploader | `src/modules/uploader.js` | drag & drop / browse / read file |
| PDF Reader | `src/modules/pdfReader.js` | PDF.js text + coordinates (only PDF.js dependency) |
| Parser | `src/modules/parser.js` | reconstruct positioned lines |
| Project Detector | `src/modules/projectDetector.js` | project/client/drawing/rev/date |
| Room Detector | `src/modules/roomDetector.js` | room headers |
| Cabinet Detector | `src/modules/cabinetDetector.js` | cabinet codes |
| Dimension Detector | `src/modules/dimensionDetector.js` | W×D×H |
| Hardware Extractor | `src/modules/hardwareExtractor.js` | items, qty, unit, flags |
| Finish Detector | `src/modules/finishDetector.js` | carcass/shutter/laminate |
| Inventory Builder | `src/modules/inventoryBuilder.js` | per-cabinet inventory rows |
| Indent Generator | `src/modules/indentGenerator.js` | grouped indent + AUTO codes |
| Exporter | `src/modules/exporter.js` | JSON / CSV / Excel |
| Pipeline | `src/pipeline.js` | composes detectors into the full model |

## Validation & error handling

The sidebar reports Rooms/Cabinets/Inventory detected, Duplicates merged,
Unknown items, plus warnings and errors:

- Missing dimensions → cabinet flagged **Dimension Missing**.
- Missing quantity → item flagged **Quantity Verification Required**.
- Unidentifiable hardware → categorised as **Unknown**.

## Tests

Pure modules are covered by Node's built-in test runner:

```bash
npm test          # node --test
```

## Future integration (not implemented)

The Material Indent is intentionally clean/structured so later phases can
validate against Inventory Master, create missing SKUs, compare stock, raise
Purchase Requisitions, and sync with Procurement/Finance/AI.
