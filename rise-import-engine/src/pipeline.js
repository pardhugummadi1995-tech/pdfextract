/**
 * Pipeline: composes the independent detector modules into the full project
 * model. Pure module (no DOM / PDF.js), so the whole extraction flow can be
 * unit-tested in Node by feeding it a parsed-document object.
 */

import { detectCabinets } from "./modules/cabinetDetector.js";
import { detectDimensions } from "./modules/dimensionDetector.js";
import { detectFinishes } from "./modules/finishDetector.js";
import { extractHardware } from "./modules/hardwareExtractor.js";
import { buildInventoryRequirement } from "./modules/inventoryBuilder.js";
import { generateIndent } from "./modules/indentGenerator.js";
import { detectProject } from "./modules/projectDetector.js";
import { detectRooms } from "./modules/roomDetector.js";

export const FLAG_DIMENSION_MISSING = "Dimension Missing";
const UNASSIGNED_ROOM = "Unassigned";

/**
 * Segment the ordered lines into rooms and cabinets, attaching each cabinet's
 * block of lines so per-cabinet detectors can run.
 */
function segment(lines, roomHeaders, cabinetHeaders) {
  const roomAt = new Map(roomHeaders.map((r) => [r.lineIndex, r]));
  const cabAt = new Map(cabinetHeaders.map((c) => [c.lineIndex, c]));

  const rooms = [];
  const unassignedCabinets = [];
  let currentRoom = null;
  let currentCabinet = null;

  const pushCabinet = (cab) => {
    if (currentRoom) currentRoom.cabinets.push(cab);
    else unassignedCabinets.push(cab);
  };

  lines.forEach((line, i) => {
    if (roomAt.has(i)) {
      currentRoom = { name: roomAt.get(i).name, page: line.page, cabinets: [], lines: [] };
      rooms.push(currentRoom);
      currentCabinet = null;
      return;
    }
    if (cabAt.has(i)) {
      const header = cabAt.get(i);
      currentCabinet = {
        code: header.code,
        room: currentRoom ? currentRoom.name : UNASSIGNED_ROOM,
        page: line.page,
        lines: [line],
      };
      pushCabinet(currentCabinet);
      return;
    }
    if (currentCabinet) currentCabinet.lines.push(line);
    else if (currentRoom) currentRoom.lines.push(line);
  });

  return { rooms, unassignedCabinets };
}

function enrichCabinet(cabinet, roomFinishes) {
  const dimensions = detectDimensions(cabinet.lines);
  const finishes = detectFinishes(cabinet.lines);
  // Fall back to room-level finishes when the cabinet block omits them.
  for (const key of ["carcassFinish", "shutterFinish", "laminateCode"]) {
    if (!finishes[key] && roomFinishes && roomFinishes[key]) {
      finishes[key] = roomFinishes[key];
    }
  }
  const hardware = extractHardware(cabinet.lines);
  const flags = [];
  if (!dimensions) flags.push(FLAG_DIMENSION_MISSING);
  return { ...cabinet, dimensions, finishes, hardware, flags };
}

/**
 * Build the full model from a parsed document ({lines, pages}).
 */
export function runPipeline(parsed) {
  const lines = parsed.lines;
  const project = detectProject(lines);
  const roomHeaders = detectRooms(lines);
  const cabinetHeaders = detectCabinets(lines);

  // Room headers must not also be treated as cabinets and vice versa.
  const roomIdx = new Set(roomHeaders.map((r) => r.lineIndex));
  const cabinetHeadersFiltered = cabinetHeaders.filter((c) => !roomIdx.has(c.lineIndex));

  const { rooms: rawRooms, unassignedCabinets: rawUnassigned } = segment(
    lines,
    roomHeaders,
    cabinetHeadersFiltered,
  );

  const rooms = rawRooms.map((room) => {
    const roomFinishes = detectFinishes(room.lines);
    return {
      name: room.name,
      page: room.page,
      cabinets: room.cabinets.map((c) => enrichCabinet(c, roomFinishes)),
    };
  });
  const unassignedCabinets = rawUnassigned.map((c) => enrichCabinet(c, null));

  const structure = { project, rooms, unassignedCabinets };

  const inventoryRequirement = buildInventoryRequirement(structure);
  const { indent: materialIndent, duplicatesMerged } =
    generateIndent(inventoryRequirement);

  const projectStructure = buildProjectStructure(project, rooms, unassignedCabinets);
  const validation = buildValidation({
    rooms,
    unassignedCabinets,
    inventoryRequirement,
    materialIndent,
    duplicatesMerged,
  });

  return {
    project,
    rooms,
    unassignedCabinets,
    inventoryRequirement,
    materialIndent,
    projectStructure,
    validation,
    pageCount: parsed.pages.length,
  };
}

function buildProjectStructure(project, rooms, unassignedCabinets) {
  const node = {
    name: project.projectName || "Project",
    rooms: rooms.map((r) => ({
      name: r.name,
      cabinets: r.cabinets.map((c) => ({
        code: c.code,
        dimensions: c.dimensions ? c.dimensions.raw : null,
      })),
    })),
  };
  if (unassignedCabinets.length) {
    node.rooms.push({
      name: UNASSIGNED_ROOM,
      cabinets: unassignedCabinets.map((c) => ({
        code: c.code,
        dimensions: c.dimensions ? c.dimensions.raw : null,
      })),
    });
  }
  return node;
}

/** Render the project structure as an ASCII tree (Output 1). */
export function renderStructureTree(structure) {
  const lines = [structure.name];
  structure.rooms.forEach((room, ri) => {
    const lastRoom = ri === structure.rooms.length - 1;
    lines.push(`${lastRoom ? "└──" : "├──"} ${room.name}`);
    const roomPrefix = lastRoom ? "    " : "│   ";
    room.cabinets.forEach((cab, ci) => {
      const lastCab = ci === room.cabinets.length - 1;
      const dim = cab.dimensions ? `  (${cab.dimensions})` : "";
      lines.push(`${roomPrefix}${lastCab ? "└──" : "├──"} ${cab.code}${dim}`);
    });
  });
  return lines.join("\n");
}

function buildValidation({
  rooms,
  unassignedCabinets,
  inventoryRequirement,
  materialIndent,
  duplicatesMerged,
}) {
  const allCabinets = [...rooms.flatMap((r) => r.cabinets), ...unassignedCabinets];
  const warnings = [];
  const errors = [];

  for (const cab of allCabinets) {
    if (cab.flags.includes(FLAG_DIMENSION_MISSING)) {
      warnings.push(`Dimension missing for cabinet ${cab.code} (${cab.room}).`);
    }
  }
  for (const row of inventoryRequirement) {
    if (row.flags.includes("Quantity Verification Required")) {
      warnings.push(
        `Quantity verification required: ${row.item} in ${row.cabinet} (${row.room}).`,
      );
    }
  }

  const unknownItems = inventoryRequirement.filter((r) => r.category === "Unknown");
  if (unassignedCabinets.length) {
    warnings.push(
      `${unassignedCabinets.length} cabinet(s) could not be linked to a room.`,
    );
  }

  const roomsDetected = rooms.length;
  const cabinetsDetected = allCabinets.length;
  if (roomsDetected === 0) errors.push("No rooms detected in the drawing.");
  if (cabinetsDetected === 0) errors.push("No cabinets detected in the drawing.");

  return {
    roomsDetected,
    cabinetsDetected,
    inventoryItemsDetected: inventoryRequirement.length,
    materialIndentLines: materialIndent.length,
    duplicatesMerged,
    unknownItems,
    warnings,
    errors,
  };
}
