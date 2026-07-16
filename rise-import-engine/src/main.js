/**
 * Application entry point. Wires the Uploader -> PDF Reader -> Parser ->
 * Pipeline -> Preview/Validation -> Exporter flow together.
 * Browser-only.
 */

import { createUploader } from "./modules/uploader.js";
import { readPdf } from "./modules/pdfReader.js";
import { parseDocument } from "./modules/parser.js";
import { runPipeline } from "./pipeline.js";
import {
  exportIndentCsv,
  exportIndentExcel,
  exportJson,
} from "./modules/exporter.js";
import { renderResults, renderValidation } from "./ui/render.js";

const $ = (id) => document.getElementById(id);

let currentModel = null;

function setStatus(message, kind = "info") {
  const status = $("status");
  status.textContent = message;
  status.className = `status ${kind}`;
}

function setProgress(pct, label) {
  const wrap = $("progress-wrap");
  const bar = $("progress-bar");
  const text = $("progress-text");
  wrap.style.display = pct === null ? "none" : "block";
  if (pct !== null) {
    bar.style.width = `${pct}%`;
    text.textContent = label || `${pct}%`;
  }
}

async function processFile({ file, arrayBuffer }) {
  try {
    $("results").innerHTML = "";
    $("validation").innerHTML = "";
    $("export-bar").style.display = "none";
    setStatus(`Reading "${file.name}"…`, "info");
    setProgress(5, "Opening PDF…");

    const rawDoc = await readPdf(arrayBuffer, {
      onProgress: ({ page, total }) => {
        const pct = Math.round((page / total) * 80) + 10;
        setProgress(pct, `Parsing page ${page} of ${total}…`);
      },
    });

    setProgress(92, "Detecting structure…");
    const parsed = parseDocument(rawDoc);
    const model = runPipeline(parsed);
    currentModel = model;

    setProgress(100, "Done");
    renderResults($("results"), model);
    renderValidation($("validation"), model.validation);
    $("export-bar").style.display = "flex";

    const v = model.validation;
    setStatus(
      `Imported "${file.name}": ${v.roomsDetected} rooms, ${v.cabinetsDetected} cabinets, ` +
        `${v.materialIndentLines} indent items.`,
      v.errors.length ? "error" : "success",
    );
    setTimeout(() => setProgress(null), 800);
  } catch (err) {
    console.error(err);
    setProgress(null);
    setStatus(`Failed to import PDF: ${err.message}`, "error");
  }
}

function init() {
  createUploader({
    dropzone: $("dropzone"),
    fileInput: $("file-input"),
    browseButton: $("browse-btn"),
    onFile: processFile,
    onError: (msg) => setStatus(msg, "error"),
  });

  $("export-json").addEventListener("click", () => currentModel && exportJson(currentModel));
  $("export-csv").addEventListener(
    "click",
    () => currentModel && exportIndentCsv(currentModel.materialIndent),
  );
  $("export-excel").addEventListener(
    "click",
    () => currentModel && exportIndentExcel(currentModel.materialIndent),
  );
}

document.addEventListener("DOMContentLoaded", init);
