/**
 * Parser module.
 *
 * Turns the low-level text items emitted by the PDF Reader into ordered,
 * reconstructed *lines* with positional metadata (x, y, font size, page,
 * bounding box). This is the structured foundation every detector consumes.
 *
 * Pure module: no DOM, no PDF.js. Safe to unit-test in Node.
 */

const Y_TOLERANCE = 3; // points; items within this vertical distance = same line

/**
 * Group a single page's text items into lines.
 * @param {Array<{str,x,y,width,height,fontSize,fontName}>} items
 * @param {number} pageNumber
 * @returns {Array<Line>}
 */
export function buildLines(items, pageNumber = 1) {
  const usable = items.filter((it) => it.str && it.str.trim() !== "");
  // Sort top-to-bottom (PDF y grows upward, so descending y), then left-to-right.
  usable.sort((a, b) => (Math.abs(b.y - a.y) > Y_TOLERANCE ? b.y - a.y : a.x - b.x));

  const lines = [];
  let current = null;
  for (const it of usable) {
    if (current && Math.abs(current.y - it.y) <= Y_TOLERANCE) {
      current.items.push(it);
    } else {
      current = { y: it.y, items: [it] };
      lines.push(current);
    }
  }

  return lines.map((line) => finalizeLine(line, pageNumber));
}

function finalizeLine(line, pageNumber) {
  const items = line.items.slice().sort((a, b) => a.x - b.x);
  let text = "";
  let prevEnd = null;
  for (const it of items) {
    const piece = it.str;
    if (prevEnd !== null) {
      const gap = it.x - prevEnd;
      const needsSpace = gap > (it.fontSize || 10) * 0.25;
      if (needsSpace && !text.endsWith(" ") && !piece.startsWith(" ")) {
        text += " ";
      }
    }
    text += piece;
    prevEnd = it.x + (it.width || 0);
  }

  const xs = items.map((i) => i.x);
  const fontSizes = items.map((i) => i.fontSize || 0);
  const heights = items.map((i) => i.height || i.fontSize || 0);
  return {
    text: text.replace(/\s+/g, " ").trim(),
    page: pageNumber,
    x: Math.min(...xs),
    y: line.y,
    fontSize: Math.max(...fontSizes),
    bbox: {
      x: Math.min(...xs),
      y: line.y,
      width: Math.max(...items.map((i) => i.x + (i.width || 0))) - Math.min(...xs),
      height: Math.max(...heights),
    },
    tokens: items,
  };
}

/**
 * Build the full document model from the raw reader output.
 * @param {{pages: Array<{pageNumber, viewport, items}>}} rawDoc
 * @returns {{pages: Array, lines: Array<Line>}} lines are in reading order.
 */
export function parseDocument(rawDoc) {
  const pages = rawDoc.pages.map((p) => ({
    pageNumber: p.pageNumber,
    viewport: p.viewport,
    lines: buildLines(p.items, p.pageNumber),
  }));

  const lines = [];
  for (const page of pages) {
    for (const line of page.lines) lines.push(line);
  }
  return { pages, lines };
}

/**
 * @typedef {Object} Line
 * @property {string} text
 * @property {number} page
 * @property {number} x
 * @property {number} y
 * @property {number} fontSize
 * @property {{x,y,width,height}} bbox
 * @property {Array} tokens
 */
