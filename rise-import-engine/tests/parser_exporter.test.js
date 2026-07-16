import assert from "node:assert/strict";
import { test } from "node:test";

import { buildLines } from "../src/modules/parser.js";
import { indentToCsv, indentToExcelHtml, toCsv } from "../src/modules/exporter.js";

test("buildLines groups items by row and orders by x", () => {
  // Two rows; item order intentionally shuffled.
  const items = [
    { str: "Nos", x: 200, y: 700, width: 20, height: 10, fontSize: 10 },
    { str: "Hinge", x: 60, y: 700, width: 40, height: 10, fontSize: 10 },
    { str: "8", x: 160, y: 700, width: 8, height: 10, fontSize: 10 },
    { str: "Kitchen", x: 50, y: 740, width: 60, height: 12, fontSize: 12 },
  ];
  const lines = buildLines(items, 1);
  assert.equal(lines.length, 2);
  assert.equal(lines[0].text, "Kitchen"); // higher y first
  assert.equal(lines[1].text, "Hinge 8 Nos");
  assert.equal(lines[1].page, 1);
});

test("toCsv escapes commas and quotes", () => {
  const out = toCsv([["a", "b,c", 'quote"d']]);
  assert.equal(out, 'a,"b,c","quote""d"');
});

test("indentToCsv includes header and sources", () => {
  const indent = [
    {
      itemCode: "AUTO-001",
      description: "Hettich 105 Hinge",
      totalQty: 24,
      uom: "Nos",
      category: "Hardware",
      sourceRooms: ["Kitchen", "Master Bedroom"],
      sourceCabinets: ["B1", "B2", "WR1"],
      flags: [],
    },
  ];
  const csv = indentToCsv(indent);
  assert.match(csv, /Item Code,Description,Total Qty,UOM,Category,Source Rooms,Source Cabinets,Flags/);
  assert.match(csv, /AUTO-001,Hettich 105 Hinge,24,Nos,Hardware,/);
  assert.match(csv, /Kitchen; Master Bedroom/);
});

test("indentToExcelHtml produces an Excel-openable workbook", () => {
  const html = indentToExcelHtml([
    {
      itemCode: "AUTO-001",
      description: "Tower Bolt",
      totalQty: 3,
      uom: "Nos",
      category: "Hardware",
      sourceRooms: ["Kitchen"],
      sourceCabinets: ["B2"],
      flags: [],
    },
  ]);
  assert.match(html, /urn:schemas-microsoft-com:office:excel/);
  assert.match(html, /<table/);
  assert.match(html, /Tower Bolt/);
});
