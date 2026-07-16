/**
 * Project Detector module.
 *
 * Scans the parsed lines for project metadata (name, client, drawing number,
 * revision, date) using label matching. Pure module.
 */

import { PROJECT_LABELS } from "../constants.js";

function valueAfterLabel(text, label) {
  const lower = text.toLowerCase();
  const idx = lower.indexOf(label);
  if (idx === -1) return null;
  let rest = text.slice(idx + label.length);
  // Strip a leading separator (: - – etc.) and whitespace.
  rest = rest.replace(/^\s*[:\-–]\s*/, "").trim();
  return rest || null;
}

/**
 * @param {Array} lines parsed lines (reading order)
 * @returns {{projectName,clientName,drawingNumber,revision,date}}
 */
export function detectProject(lines) {
  const result = {
    projectName: null,
    clientName: null,
    drawingNumber: null,
    revision: null,
    date: null,
  };

  for (const line of lines) {
    for (const { field, labels } of PROJECT_LABELS) {
      if (result[field]) continue;
      for (const label of labels) {
        // Require the label to appear near the start of the line so a stray
        // occurrence in body text does not get mistaken for a field.
        const lower = line.text.toLowerCase();
        if (lower.startsWith(label) || lower.indexOf(label) <= 2) {
          const value = valueAfterLabel(line.text, label);
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
