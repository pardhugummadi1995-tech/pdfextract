/**
 * Finish Detector module.
 *
 * Extracts finish codes (carcass finish, shutter finish, laminate code) from a
 * block of lines. Pure module.
 */

import { FINISH_LABELS } from "../constants.js";

/**
 * @param {Array} lines lines belonging to a cabinet (or room) block
 * @returns {{carcassFinish, shutterFinish, laminateCode}}
 */
export function detectFinishes(lines) {
  const result = { carcassFinish: null, shutterFinish: null, laminateCode: null };
  for (const line of lines) {
    const lower = line.text.toLowerCase();
    for (const { field, labels } of FINISH_LABELS) {
      if (result[field]) continue;
      for (const label of labels) {
        const idx = lower.indexOf(label);
        if (idx !== -1) {
          const value = line.text
            .slice(idx + label.length)
            .replace(/^\s*[:\-–]\s*/, "")
            .trim();
          if (value) {
            result[field] = value;
            break;
          }
        }
      }
    }
  }
  return result;
}
