/**
 * PDF Reader module.
 *
 * Wraps PDF.js to read a PDF ArrayBuffer and return low-level text items with
 * their coordinates, font size, page number and bounding boxes. This is the only
 * module that depends on PDF.js; everything downstream works on plain data.
 *
 * Browser-only (relies on the global `pdfjsLib` provided by the vendored build).
 */

const WORKER_SRC = new URL("../../vendor/pdf.worker.min.js", import.meta.url).href;

function ensureConfigured() {
  if (typeof window === "undefined" || !window.pdfjsLib) {
    throw new Error("PDF.js is not loaded. Include vendor/pdf.min.js before the app.");
  }
  window.pdfjsLib.GlobalWorkerOptions.workerSrc = WORKER_SRC;
  return window.pdfjsLib;
}

/**
 * @param {ArrayBuffer} arrayBuffer
 * @param {{onProgress?: (info:{page:number,total:number})=>void}} [opts]
 * @returns {Promise<{pages: Array, numPages: number}>}
 */
export async function readPdf(arrayBuffer, opts = {}) {
  const pdfjsLib = ensureConfigured();
  const loadingTask = pdfjsLib.getDocument({ data: arrayBuffer });
  const pdf = await loadingTask.promise;
  const pages = [];

  for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber += 1) {
    const page = await pdf.getPage(pageNumber);
    const viewport = page.getViewport({ scale: 1 });
    const content = await page.getTextContent();

    const items = content.items
      .filter((it) => typeof it.str === "string")
      .map((it) => {
        const [a, b, , d, e, f] = it.transform;
        const fontSize = Math.hypot(a, b) || Math.abs(d) || 0;
        return {
          str: it.str,
          x: e,
          y: f,
          width: it.width || 0,
          height: it.height || fontSize,
          fontSize,
          fontName: it.fontName || "",
        };
      });

    pages.push({ pageNumber, viewport: { width: viewport.width, height: viewport.height }, items });
    if (opts.onProgress) opts.onProgress({ page: pageNumber, total: pdf.numPages });
  }

  return { pages, numPages: pdf.numPages };
}
