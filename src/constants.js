/**
 * Shared vocabulary and patterns used by the detector modules.
 *
 * Everything here is data-only so it can be imported both in the browser and in
 * Node (for the unit tests) without pulling in any DOM or PDF.js dependency.
 */

// Room names commonly found on interior Shop Order Drawings. Longer / more
// specific names are listed first so they win over generic ones (e.g. we want
// "Master Bedroom" to match before "Bedroom").
export const ROOM_KEYWORDS = [
  "Master Bedroom",
  "Guest Bedroom",
  "Children Bedroom",
  "Kids Bedroom",
  "Living Room",
  "Living",
  "Dining",
  "Kitchen",
  "Utility",
  "Vanity",
  "Balcony",
  "Foyer",
  "Pooja",
  "Study",
  "Wardrobe Room",
  "Bedroom",
  "Bathroom",
  "Toilet",
  "Store",
];

// A cabinet code such as WR1, B2, TV1, W12. 1-3 leading letters + 1-2 digits,
// optionally suffixed with a letter (e.g. B2A).
export const CABINET_CODE_RE = /^[A-Z]{1,3}\d{1,2}[A-Z]?$/;

// Dimensions like "900 x 580 x 2150" (accepts x, ×, X or *).
export const DIMENSION_RE =
  /(\d{2,4})\s*[x×X*]\s*(\d{2,4})\s*[x×X*]\s*(\d{2,4})/;

// Quantity + unit at (or near) the end of a line, e.g. "... 10 Nos".
export const QTY_UNIT_RE =
  /(\d+(?:\.\d+)?)\s*(Nos|No|Pairs|Pair|Sets|Set|Pcs|Pc|Units|Unit|Mtr|Mtrs|Kg|Ltr)\b/i;

// Canonical unit spellings.
export const UNIT_CANONICAL = {
  no: "No",
  nos: "Nos",
  pair: "Pair",
  pairs: "Pair",
  set: "Set",
  sets: "Set",
  pc: "Pcs",
  pcs: "Pcs",
  unit: "Nos",
  units: "Nos",
  mtr: "Mtr",
  mtrs: "Mtr",
  kg: "Kg",
  ltr: "Ltr",
};

// Keywords that identify a line as a hardware item.
export const HARDWARE_KEYWORDS = [
  "hinge",
  "handle",
  "lock",
  "tower bolt",
  "bolt",
  "leg",
  "drawer runner",
  "runner",
  "telescopic channel",
  "channel",
  "shelf support",
  "hanger rod",
  "rod",
  "door buffer",
  "buffer",
  "pom",
  "minifix",
  "dowel",
  "screw",
  "magnet",
  "catcher",
  "bracket",
  "bush",
  "soft close",
  "gas lift",
  "flap stay",
  "hettich",
  "hafele",
  "ebco",
];

// Label -> logical field for project metadata detection.
export const PROJECT_LABELS = [
  { field: "projectName", labels: ["project name", "project"] },
  { field: "clientName", labels: ["client name", "client", "customer"] },
  {
    field: "drawingNumber",
    labels: ["drawing number", "drawing no", "dwg no", "dwg", "drawing"],
  },
  { field: "revision", labels: ["revision", "rev"] },
  { field: "date", labels: ["date"] },
];

// Label -> logical field for finish codes.
export const FINISH_LABELS = [
  { field: "carcassFinish", labels: ["carcass finish", "carcass"] },
  { field: "shutterFinish", labels: ["shutter finish", "shutter"] },
  { field: "laminateCode", labels: ["laminate code", "laminate", "lam code"] },
];
