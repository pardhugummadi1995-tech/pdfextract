/** Build minimal parsed "lines" for detector/pipeline tests. */
export function mkLines(texts) {
  return texts.map((text, i) => ({
    text,
    page: 1,
    x: 50,
    y: 800 - i * 16,
    fontSize: 11,
    bbox: { x: 50, y: 800 - i * 16, width: 200, height: 11 },
    tokens: [],
  }));
}

export function mkParsed(texts, pageCount = 1) {
  return { lines: mkLines(texts), pages: Array.from({ length: pageCount }, (_, i) => ({ pageNumber: i + 1 })) };
}
