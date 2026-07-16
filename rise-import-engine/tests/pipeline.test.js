import assert from "node:assert/strict";
import { test } from "node:test";

import { runPipeline, renderStructureTree } from "../src/pipeline.js";
import { mkParsed } from "./helpers.js";

function buildModel() {
  const parsed = mkParsed([
    "Project Name: Aurora Residence",
    "Client: Prestige Group",
    "Drawing No: SOD-2024-017",
    "Revision: R2",
    "Date: 2026-07-10",
    "Kitchen",
    "B1 Base Unit 600 x 580 x 850",
    "Hettich 105 Hinge 8 Nos",
    "Handle SS 128mm 2 Nos",
    "Carcass Finish: PLPL 18mm",
    "B2 Base Unit 900 x 580 x 850",
    "Hettich 105 Hinge 6 Nos",
    "Master Bedroom",
    "WR1 Wardrobe 2100 x 600 x 2400",
    "Hettich 105 Hinge 10 Nos",
    "Multipurpose Lock 1 No",
    "WR2 Wardrobe",
    "Mystery Gadget X 2 Nos",
    "Soft Close Mechanism",
  ]);
  return runPipeline(parsed);
}

test("pipeline detects rooms and cabinets", () => {
  const m = buildModel();
  assert.deepEqual(m.rooms.map((r) => r.name), ["Kitchen", "Master Bedroom"]);
  assert.deepEqual(
    m.rooms[0].cabinets.map((c) => c.code),
    ["B1", "B2"],
  );
  assert.deepEqual(
    m.rooms[1].cabinets.map((c) => c.code),
    ["WR1", "WR2"],
  );
});

test("pipeline extracts dimensions and flags missing ones", () => {
  const m = buildModel();
  const b1 = m.rooms[0].cabinets[0];
  assert.equal(b1.dimensions.raw, "600 x 580 x 850");
  const wr2 = m.rooms[1].cabinets[1];
  assert.equal(wr2.dimensions, null);
  assert.ok(wr2.flags.includes("Dimension Missing"));
});

test("cabinet inherits finishes and captures room association", () => {
  const m = buildModel();
  const b1 = m.rooms[0].cabinets[0];
  assert.equal(b1.finishes.carcassFinish, "PLPL 18mm");
  assert.equal(b1.room, "Kitchen");
});

test("material indent sums duplicate hardware across cabinets/rooms", () => {
  const m = buildModel();
  const hinge = m.materialIndent.find((i) => i.description === "Hettich 105 Hinge");
  assert.equal(hinge.totalQty, 24); // 8 + 6 + 10
  assert.equal(hinge.uom, "Nos");
  assert.deepEqual(hinge.sourceRooms.sort(), ["Kitchen", "Master Bedroom"]);
  assert.deepEqual(hinge.sourceCabinets.sort(), ["B1", "B2", "WR1"]);
  assert.match(hinge.itemCode, /^AUTO-\d{3}$/);
});

test("unknown items and qty-verification are surfaced", () => {
  const m = buildModel();
  const unknown = m.materialIndent.find((i) => i.description === "Mystery Gadget X");
  assert.equal(unknown.category, "Unknown");
  const soft = m.materialIndent.find((i) => i.description === "Soft Close Mechanism");
  assert.equal(soft.totalQty, null);
  assert.ok(soft.flags.includes("Quantity Verification Required"));
});

test("validation counts are consistent", () => {
  const m = buildModel();
  const v = m.validation;
  assert.equal(v.roomsDetected, 2);
  assert.equal(v.cabinetsDetected, 4);
  assert.equal(v.duplicatesMerged, m.inventoryRequirement.length - m.materialIndent.length);
  assert.ok(v.unknownItems.length >= 1);
  assert.ok(v.warnings.some((w) => w.includes("Dimension missing")));
});

test("project structure tree renders rooms and cabinets", () => {
  const m = buildModel();
  const tree = renderStructureTree(m.projectStructure);
  assert.match(tree, /Aurora Residence/);
  assert.match(tree, /Kitchen/);
  assert.match(tree, /WR1/);
});
