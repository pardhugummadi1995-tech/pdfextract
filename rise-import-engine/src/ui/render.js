/**
 * UI rendering helpers for the preview screen. Browser-only (DOM).
 * Kept separate from the pipeline so the extraction logic stays testable.
 */

import { renderStructureTree } from "../pipeline.js";

function el(tag, attrs = {}, children = []) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") node.className = v;
    else if (k === "text") node.textContent = v;
    else node.setAttribute(k, v);
  }
  for (const child of [].concat(children)) {
    if (child) node.appendChild(typeof child === "string" ? document.createTextNode(child) : child);
  }
  return node;
}

function table(headers, rows) {
  const thead = el("thead", {}, el("tr", {}, headers.map((h) => el("th", { text: h }))));
  const tbody = el(
    "tbody",
    {},
    rows.map((r) =>
      el(
        "tr",
        {},
        r.map((c) => el("td", { text: c === null || c === undefined ? "" : String(c) })),
      ),
    ),
  );
  return el("table", { class: "data" }, [thead, tbody]);
}

function section(title, subtitle, bodyNode, open = true) {
  const details = el("details", { class: "panel" });
  if (open) details.setAttribute("open", "");
  const summary = el("summary", {}, [
    el("span", { class: "panel-title", text: title }),
    subtitle ? el("span", { class: "panel-badge", text: subtitle }) : null,
  ]);
  details.appendChild(summary);
  details.appendChild(el("div", { class: "panel-body" }, bodyNode));
  return details;
}

export function renderResults(container, model) {
  container.innerHTML = "";

  // --- Project summary
  const p = model.project;
  const summaryRows = [
    ["Project Name", p.projectName || "—"],
    ["Client", p.clientName || "—"],
    ["Drawing No.", p.drawingNumber || "—"],
    ["Revision", p.revision || "—"],
    ["Date", p.date || "—"],
    ["Pages", model.pageCount],
  ];
  container.appendChild(
    section(
      "Project Summary",
      null,
      el(
        "div",
        { class: "summary-grid" },
        summaryRows.map(([k, v]) =>
          el("div", { class: "summary-cell" }, [
            el("div", { class: "summary-key", text: k }),
            el("div", { class: "summary-val", text: String(v) }),
          ]),
        ),
      ),
    ),
  );

  // --- Project structure tree (Output 1)
  container.appendChild(
    section(
      "Project Structure",
      `${model.rooms.length} rooms`,
      el("pre", { class: "tree", text: renderStructureTree(model.projectStructure) }),
    ),
  );

  // --- Rooms & cabinets
  const roomNodes = model.rooms.concat(
    model.unassignedCabinets.length
      ? [{ name: "Unassigned", cabinets: model.unassignedCabinets }]
      : [],
  );
  const roomsBody = el(
    "div",
    {},
    roomNodes.map((room) => {
      const cabRows = room.cabinets.map((c) => [
        c.code,
        c.dimensions ? c.dimensions.raw : "Dimension Missing",
        c.finishes?.carcassFinish || "—",
        c.finishes?.shutterFinish || "—",
        c.finishes?.laminateCode || "—",
        c.hardware.length,
      ]);
      return el("div", { class: "room-block" }, [
        el("h4", { text: `${room.name} (${room.cabinets.length} cabinets)` }),
        table(["Cabinet", "Dimensions (W×D×H)", "Carcass", "Shutter", "Laminate", "HW lines"], cabRows),
      ]);
    }),
  );
  container.appendChild(section("Rooms & Cabinets", `${model.rooms.length}`, roomsBody, false));

  // --- Inventory requirement (Step 9)
  const invRows = model.inventoryRequirement.map((r) => [
    r.item,
    r.category,
    r.qty === null ? "?" : r.qty,
    r.uom,
    r.room,
    r.cabinet,
    r.flags.join("; "),
  ]);
  container.appendChild(
    section(
      "Inventory Requirement",
      `${model.inventoryRequirement.length} rows`,
      table(["Item", "Category", "Qty", "UOM", "Room", "Cabinet", "Flags"], invRows),
      false,
    ),
  );

  // --- Material indent (Output 2 / Step 10)
  const indentRows = model.materialIndent.map((i) => [
    i.itemCode,
    i.description,
    i.totalQty === null ? "?" : i.totalQty,
    i.uom,
    i.category,
    i.sourceRooms.join(", "),
    i.sourceCabinets.join(", "),
  ]);
  container.appendChild(
    section(
      "Material Indent",
      `${model.materialIndent.length} items`,
      table(
        ["Item Code", "Description", "Total Qty", "UOM", "Category", "Source Rooms", "Source Cabinets"],
        indentRows,
      ),
    ),
  );
}

export function renderValidation(container, validation) {
  container.innerHTML = "";
  const stats = [
    ["Rooms Detected", validation.roomsDetected],
    ["Cabinets Detected", validation.cabinetsDetected],
    ["Inventory Items", validation.inventoryItemsDetected],
    ["Indent Lines", validation.materialIndentLines],
    ["Duplicates Merged", validation.duplicatesMerged],
    ["Unknown Items", validation.unknownItems.length],
  ];
  container.appendChild(
    el(
      "div",
      { class: "stat-grid" },
      stats.map(([k, v]) =>
        el("div", { class: "stat" }, [
          el("div", { class: "stat-num", text: String(v) }),
          el("div", { class: "stat-label", text: k }),
        ]),
      ),
    ),
  );

  const messages = el("div", { class: "messages" });
  if (validation.errors.length) {
    messages.appendChild(el("h4", { class: "msg-err", text: `Errors (${validation.errors.length})` }));
    messages.appendChild(el("ul", {}, validation.errors.map((m) => el("li", { class: "msg-err", text: m }))));
  }
  if (validation.warnings.length) {
    messages.appendChild(
      el("h4", { class: "msg-warn", text: `Warnings (${validation.warnings.length})` }),
    );
    messages.appendChild(
      el("ul", {}, validation.warnings.map((m) => el("li", { class: "msg-warn", text: m }))),
    );
  }
  if (!validation.errors.length && !validation.warnings.length) {
    messages.appendChild(el("p", { class: "msg-ok", text: "No warnings or errors. " }));
  }
  container.appendChild(messages);
}
