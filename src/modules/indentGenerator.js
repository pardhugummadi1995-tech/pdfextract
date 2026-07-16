/**
 * Indent Generator module.
 *
 * Groups the inventory requirement into an ERP-ready Material Indent. Items with
 * the same description + unit are summed across all cabinets/rooms, auto item
 * codes (AUTO-001, ...) are assigned, and the contributing rooms/cabinets are
 * recorded as the source. Pure module.
 */

function keyFor(item, uom) {
  return `${item.toLowerCase()}||${(uom || "").toLowerCase()}`;
}

function pad(n) {
  return String(n).padStart(3, "0");
}

/**
 * @param {Array} requirement output of buildInventoryRequirement
 * @returns {{indent: Array, duplicatesMerged: number}}
 */
export function generateIndent(requirement) {
  const groups = new Map();
  const order = [];

  for (const row of requirement) {
    const k = keyFor(row.item, row.uom);
    if (!groups.has(k)) {
      groups.set(k, {
        description: row.item,
        category: row.category,
        totalQty: 0,
        uom: row.uom,
        sourceRooms: new Set(),
        sourceCabinets: new Set(),
        flags: new Set(),
        qtyKnown: false,
      });
      order.push(k);
    }
    const g = groups.get(k);
    if (row.qty !== null && row.qty !== undefined) {
      g.totalQty += row.qty;
      g.qtyKnown = true;
    }
    if (row.room) g.sourceRooms.add(row.room);
    if (row.cabinet) g.sourceCabinets.add(row.cabinet);
    (row.flags || []).forEach((f) => g.flags.add(f));
  }

  const indent = order.map((k, i) => {
    const g = groups.get(k);
    return {
      itemCode: `AUTO-${pad(i + 1)}`,
      description: g.description,
      totalQty: g.qtyKnown ? g.totalQty : null,
      uom: g.uom,
      category: g.category,
      sourceRooms: [...g.sourceRooms],
      sourceCabinets: [...g.sourceCabinets],
      flags: [...g.flags],
    };
  });

  const duplicatesMerged = Math.max(0, requirement.length - indent.length);
  return { indent, duplicatesMerged };
}
