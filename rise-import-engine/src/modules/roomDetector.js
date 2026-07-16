/**
 * Room Detector module.
 *
 * Identifies room headers among the parsed lines. A line is treated as a room
 * header when it is short and either equals a known room keyword, is prefixed
 * with "Room:", or begins with a known room keyword. Pure module.
 */

import { ROOM_KEYWORDS } from "../constants.js";

function matchRoomKeyword(text) {
  const cleaned = text.replace(/^room\s*[:\-–]\s*/i, "").trim();
  const lower = cleaned.toLowerCase();
  for (const kw of ROOM_KEYWORDS) {
    const k = kw.toLowerCase();
    if (lower === k) return kw;
  }
  for (const kw of ROOM_KEYWORDS) {
    const k = kw.toLowerCase();
    if (lower.startsWith(k + " ") || lower.startsWith(k + " -")) return kw;
  }
  return null;
}

/**
 * @param {Array} lines parsed lines (reading order)
 * @returns {Array<{name, page, lineIndex, y}>}
 */
export function detectRooms(lines) {
  const rooms = [];
  lines.forEach((line, lineIndex) => {
    const text = line.text.trim();
    // Room headers are short labels, not long sentences / table rows.
    if (text.length === 0 || text.length > 40) return;
    const explicit = /^room\s*[:\-–]/i.test(text);
    const name = matchRoomKeyword(text);
    if (name && (explicit || text.split(/\s+/).length <= 4)) {
      rooms.push({ name, page: line.page, lineIndex, y: line.y });
    }
  });
  return rooms;
}
