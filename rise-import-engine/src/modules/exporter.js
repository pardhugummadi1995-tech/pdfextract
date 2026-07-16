/**
 * Exporter module.
 *
 * Serializes the generated outputs to JSON, CSV and Excel and triggers a
 * download in the browser. The Excel export is a self-contained,
 * spreadsheet-compatible HTML workbook (opens directly in Excel / LibreOffice)
 * so the app stays 100% offline with no third-party libraries.
 *
 * The serialization helpers are pure and exported for unit testing; the
 * download helpers are browser-only.
 */

function csvCell(value) {
  const s = value === null || value === undefined ? "" : String(value);
  if (/[",\n]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
  return s;
}

export function toCsv(rows) {
  return rows.map((row) => row.map(csvCell).join(",")).join("\n");
}

/** Material Indent as CSV rows (Output 2). */
export function indentToCsv(materialIndent) {
  const header = [
    "Item Code",
    "Description",
    "Total Qty",
    "UOM",
    "Category",
    "Source Rooms",
    "Source Cabinets",
    "Flags",
  ];
  const rows = materialIndent.map((i) => [
    i.itemCode,
    i.description,
    i.totalQty === null ? "" : i.totalQty,
    i.uom,
    i.category,
    i.sourceRooms.join("; "),
    i.sourceCabinets.join("; "),
    i.flags.join("; "),
  ]);
  return toCsv([header, ...rows]);
}

function htmlTable(headers, rows) {
  const head = headers.map((h) => `<th>${escapeHtml(h)}</th>`).join("");
  const body = rows
    .map((r) => `<tr>${r.map((c) => `<td>${escapeHtml(c)}</td>`).join("")}</tr>`)
    .join("");
  return `<table border="1"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
}

function escapeHtml(value) {
  const s = value === null || value === undefined ? "" : String(value);
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

/** Excel-compatible HTML workbook for the material indent. */
export function indentToExcelHtml(materialIndent) {
  const headers = [
    "Item Code",
    "Description",
    "Total Qty",
    "UOM",
    "Category",
    "Source Rooms",
    "Source Cabinets",
    "Flags",
  ];
  const rows = materialIndent.map((i) => [
    i.itemCode,
    i.description,
    i.totalQty === null ? "" : i.totalQty,
    i.uom,
    i.category,
    i.sourceRooms.join(", "),
    i.sourceCabinets.join(", "),
    i.flags.join(", "),
  ]);
  return (
    `<html xmlns:o="urn:schemas-microsoft-com:office:office" ` +
    `xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">` +
    `<head><meta charset="utf-8"></head><body>${htmlTable(headers, rows)}</body></html>`
  );
}

// ---- Browser download helpers ----------------------------------------------

export function download(filename, content, mime) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export function exportJson(model, filename = "project-import.json") {
  download(filename, JSON.stringify(model, null, 2), "application/json");
}

export function exportIndentCsv(materialIndent, filename = "material-indent.csv") {
  download(filename, indentToCsv(materialIndent), "text/csv");
}

export function exportIndentExcel(materialIndent, filename = "material-indent.xls") {
  download(filename, indentToExcelHtml(materialIndent), "application/vnd.ms-excel");
}
