import assert from "node:assert/strict";
import { test } from "node:test";

import { detectProject } from "../src/modules/projectDetector.js";
import { detectRooms } from "../src/modules/roomDetector.js";
import { detectCabinets } from "../src/modules/cabinetDetector.js";
import { detectDimensions } from "../src/modules/dimensionDetector.js";
import { detectFinishes } from "../src/modules/finishDetector.js";
import { extractHardware, FLAG_QTY_VERIFY } from "../src/modules/hardwareExtractor.js";
import { mkLines } from "./helpers.js";

test("detectProject reads title block", () => {
  const lines = mkLines([
    "Project Name: Aurora Residence",
    "Client: Prestige Group",
    "Drawing No: SOD-2024-017",
    "Revision: R2",
    "Date: 2026-07-10",
  ]);
  const p = detectProject(lines);
  assert.equal(p.projectName, "Aurora Residence");
  assert.equal(p.clientName, "Prestige Group");
  assert.equal(p.drawingNumber, "SOD-2024-017");
  assert.equal(p.revision, "R2");
  assert.equal(p.date, "2026-07-10");
});

test("detectRooms finds known rooms and ignores body text", () => {
  const lines = mkLines([
    "Kitchen",
    "Master Bedroom",
    "Hettich 105 Hinge 8 Nos",
    "Room: Utility",
  ]);
  const rooms = detectRooms(lines).map((r) => r.name);
  assert.deepEqual(rooms, ["Kitchen", "Master Bedroom", "Utility"]);
});

test("detectCabinets matches codes and explicit labels", () => {
  const lines = mkLines([
    "B1 Base Unit 600 x 580 x 850",
    "WR1 Wardrobe 2100 x 600 x 2400",
    "Cabinet: TV1",
    "Hettich 105 Hinge 8 Nos",
    "Kitchen",
  ]);
  const codes = detectCabinets(lines).map((c) => c.code);
  assert.deepEqual(codes, ["B1", "WR1", "TV1"]);
});

test("detectDimensions parses WxDxH", () => {
  const dim = detectDimensions(mkLines(["B1 Base Unit 600 x 580 x 850"]));
  assert.deepEqual(dim, { width: 600, depth: 580, height: 850, raw: "600 x 580 x 850" });
});

test("detectDimensions returns null when absent", () => {
  assert.equal(detectDimensions(mkLines(["WR2 Wardrobe"])), null);
});

test("detectFinishes reads finish codes", () => {
  const f = detectFinishes(
    mkLines(["Carcass Finish: PLPL 18mm", "Shutter Finish: Acrylic White", "Laminate Code: LAM-101"]),
  );
  assert.equal(f.carcassFinish, "PLPL 18mm");
  assert.equal(f.shutterFinish, "Acrylic White");
  assert.equal(f.laminateCode, "LAM-101");
});

test("extractHardware classifies known, unknown and qty-missing items", () => {
  const items = extractHardware(
    mkLines([
      "B1 Base Unit 600 x 580 x 850", // dimension header -> ignored
      "Hettich 105 Hinge 8 Nos",
      "Handle SS 128mm 2 Nos",
      "Multipurpose Lock 1 No",
      "Mystery Gadget X 2 Nos", // unknown
      "Soft Close Mechanism", // known keyword, no qty
      "Carcass Finish: PLPL 18mm", // finish -> ignored
    ]),
  );
  const byDesc = Object.fromEntries(items.map((i) => [i.description, i]));
  assert.equal(byDesc["Hettich 105 Hinge"].qty, 8);
  assert.equal(byDesc["Hettich 105 Hinge"].unit, "Nos");
  assert.equal(byDesc["Multipurpose Lock"].unit, "No");
  assert.equal(byDesc["Mystery Gadget X"].category, "Unknown");
  assert.equal(byDesc["Soft Close Mechanism"].qty, null);
  assert.ok(byDesc["Soft Close Mechanism"].flags.includes(FLAG_QTY_VERIFY));
  // Dimension and finish lines must not become hardware.
  assert.ok(!items.some((i) => i.description.includes("Base Unit")));
  assert.ok(!items.some((i) => i.description.includes("Carcass")));
});
