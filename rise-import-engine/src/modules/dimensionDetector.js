/**
 * Dimension Detector module.
 *
 * Extracts Width x Depth x Height from a block of lines. Pure module.
 */

import { DIMENSION_RE } from "../constants.js";

/**
 * @param {Array} lines lines belonging to a single cabinet block
 * @returns {{width, depth, height, raw}|null}
 */
export function detectDimensions(lines) {
  for (const line of lines) {
    const m = line.text.match(DIMENSION_RE);
    if (m) {
      return {
        width: Number(m[1]),
        depth: Number(m[2]),
        height: Number(m[3]),
        raw: `${m[1]} x ${m[2]} x ${m[3]}`,
      };
    }
  }
  return null;
}
