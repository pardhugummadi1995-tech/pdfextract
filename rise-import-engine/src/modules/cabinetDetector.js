/**
 * Cabinet Detector module.
 *
 * Finds cabinet codes (WR1, B2, TV1, ...) among the parsed lines. A cabinet is
 * recognised either as a standalone code, an explicit "Cabinet: <code>" label,
 * or a code that begins a header line (optionally followed by a description
 * and/or dimensions). Pure module.
 */

import { CABINET_CODE_RE, QTY_UNIT_RE } from "../constants.js";

/**
 * @param {Array} lines parsed lines (reading order)
 * @returns {Array<{code, page, lineIndex, y, headerText}>}
 */
export function detectCabinets(lines) {
  const cabinets = [];
  lines.forEach((line, lineIndex) => {
    const text = line.text.trim();
    if (!text) return;

    const explicit = text.match(/^cabinet\s*[:\-–]\s*([A-Z]{1,3}\d{1,2}[A-Z]?)\b/i);
    if (explicit) {
      cabinets.push({
        code: explicit[1].toUpperCase(),
        page: line.page,
        lineIndex,
        y: line.y,
        headerText: text,
      });
      return;
    }

    // A hardware line can start with a token that looks like a cabinet code
    // (e.g. "POM40 4 Nos"). Cabinet headers never carry a quantity + unit, so
    // skip anything that reads as a hardware line.
    if (QTY_UNIT_RE.test(text)) return;

    const first = text.split(/\s+/)[0];
    if (CABINET_CODE_RE.test(first)) {
      // Avoid matching very long paragraphs that merely start with a code-like token.
      if (text.length <= 60) {
        cabinets.push({
          code: first.toUpperCase(),
          page: line.page,
          lineIndex,
          y: line.y,
          headerText: text,
        });
      }
    }
  });
  return cabinets;
}
