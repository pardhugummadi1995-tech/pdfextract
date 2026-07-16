/**
 * Inventory Builder module.
 *
 * Flattens the detected project structure (rooms -> cabinets -> hardware) into a
 * structured inventory requirement. Duplicate items *within the same cabinet*
 * are merged (their quantities summed). Pure module.
 */

function keyFor(description, unit) {
  return `${description.toLowerCase()}||${(unit || "").toLowerCase()}`;
}

/**
 * @param {Object} structure output of the pipeline (rooms with cabinets/hardware)
 * @returns {Array<{item, category, qty, uom, room, cabinet, flags: string[]}>}
 */
export function buildInventoryRequirement(structure) {
  const rows = [];
  const allCabinets = [
    ...structure.rooms.flatMap((r) => r.cabinets),
    ...(structure.unassignedCabinets || []),
  ];

  for (const cabinet of allCabinets) {
    const merged = new Map();
    for (const hw of cabinet.hardware) {
      const k = keyFor(hw.description, hw.unit);
      if (!merged.has(k)) {
        merged.set(k, {
          item: hw.description,
          category: hw.category,
          qty: hw.qty === null ? null : 0,
          uom: hw.unit,
          room: cabinet.room,
          cabinet: cabinet.code,
          flags: new Set(hw.flags),
        });
      }
      const entry = merged.get(k);
      if (hw.qty === null) {
        hw.flags.forEach((f) => entry.flags.add(f));
      } else {
        entry.qty = (entry.qty || 0) + hw.qty;
      }
      hw.flags.forEach((f) => entry.flags.add(f));
    }
    for (const entry of merged.values()) {
      rows.push({ ...entry, flags: [...entry.flags] });
    }
  }

  return rows;
}
