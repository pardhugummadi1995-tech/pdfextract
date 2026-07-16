/**
 * Hardware Extractor module.
 *
 * Given the lines of a cabinet block, extract hardware line items with a
 * description, quantity, unit and validation flags. Lines that clearly belong
 * to other detectors (finish codes, dimensions, headers) are ignored.
 *
 * Classification:
 *  - a line with qty+unit and a known hardware keyword  -> category "Hardware"
 *  - a line with qty+unit but no known keyword          -> category "Unknown"
 *  - a line with a known keyword but no qty/unit         -> flagged
 *    "Quantity Verification Required"
 *
 * Pure module.
 */

import {
  DIMENSION_RE,
  FINISH_LABELS,
  HARDWARE_KEYWORDS,
  QTY_UNIT_RE,
  UNIT_CANONICAL,
} from "../constants.js";

export const FLAG_QTY_VERIFY = "Quantity Verification Required";

function canonicalUnit(raw) {
  return UNIT_CANONICAL[raw.toLowerCase()] || raw;
}

function isKnownHardware(text) {
  const lower = text.toLowerCase();
  return HARDWARE_KEYWORDS.some((kw) => lower.includes(kw));
}

function isFinishLine(text) {
  const lower = text.toLowerCase();
  return FINISH_LABELS.some(({ labels }) =>
    labels.some((label) => lower.startsWith(label)),
  );
}

function cleanDescription(desc) {
  return desc
    .replace(/[:\-–|]+$/g, "")
    .replace(/\s{2,}/g, " ")
    .trim();
}

/**
 * @param {Array} lines cabinet block lines
 * @param {{skipLineIndexes?: Set<number>}} [opts]
 * @returns {Array<{description, qty, unit, category, flags: string[]}>}
 */
export function extractHardware(lines, opts = {}) {
  const skip = opts.skipLineIndexes || new Set();
  const items = [];

  lines.forEach((line, idx) => {
    if (skip.has(idx)) return;
    const text = line.text.trim();
    if (!text) return;
    if (isFinishLine(text)) return;

    const qtyMatch = text.match(QTY_UNIT_RE);
    // A dimension line (three numbers) should never be read as a quantity.
    const isDimension = DIMENSION_RE.test(text);

    if (qtyMatch && !isDimension) {
      const qty = Number(qtyMatch[1]);
      const unit = canonicalUnit(qtyMatch[2]);
      let description = cleanDescription(text.slice(0, qtyMatch.index));
      if (!description) description = "Unnamed item";
      const known = isKnownHardware(description) || isKnownHardware(text);
      items.push({
        description,
        qty,
        unit,
        category: known ? "Hardware" : "Unknown",
        flags: [],
      });
      return;
    }

    // No qty/unit, but the line names a hardware item -> needs verification.
    if (isKnownHardware(text) && !isDimension) {
      items.push({
        description: cleanDescription(text),
        qty: null,
        unit: "Nos",
        category: "Hardware",
        flags: [FLAG_QTY_VERIFY],
      });
    }
  });

  return items;
}
