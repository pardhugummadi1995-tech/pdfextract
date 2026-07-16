"""Generate a synthetic, ruled-table Shop Order Drawing (SOD) PDF fixture.

This mirrors the structure of a real SOD hardware schedule (a bordered table
with columns Cabinet Code / Carcass / Shutter / Sizes / Hardware Details, a
DRAWING NAME title block, and a FINISHES legend) so the engine can be tested
end to end without shipping any customer document.

Usage:  python samples/generate_sample_sod.py [output.pdf]
"""

from __future__ import annotations

import sys

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

styles = getSampleStyleSheet()
CELL = styles["BodyText"]
CELL.fontSize = 8
CELL.leading = 10

# room -> (finishes legend lines, schedule rows)
# each schedule row: [code, carcass, shutter, sizes, hardware_paragraph_html]
PROJECT = {
    "KITCHEN": {
        "finishes": ["Finish C1 1789 QZ VINTAGE SHALE", "Finish S2 ABHIYAN CADET GREY"],
        "rows": [
            [
                "B1",
                "C1",
                "S2",
                "650 X 580 X 820mm",
                "1. Hettich Onsys 105° Hinges -4Nos<br/>2. Shelf Supports -4Pc<br/>"
                "3. Ebco Cylindrical Legs -6Nos<br/>4. Ebco Door Buffers -4Pc",
            ],
            [
                "B2",
                "C1",
                "S2",
                "900 X 580 X 820mm",
                "1. Hettich Onsys 105° Hinges -6Nos<br/>2. Ebco Cylindrical Legs -6Nos<br/>"
                "3. Handles In Client Scope",
            ],
            [
                "W1",
                "C1",
                "S2",
                "610 X 360 X 750mm",
                "1. Hettich Sensys Profile Hinges -4Nos<br/>2. Concealed Wall Brackets",
            ],
        ],
    },
    "MASTER BED ROOM": {
        "finishes": ["Finish C1 1789 QZ VINTAGE SHALE", "Finish S1 ABHIYAN STONE GREY"],
        "rows": [
            [
                "WR1",
                "C1",
                "S1",
                "900 X 580 X 2150mm",
                "1. Hettich Onsys 105° Hinges -10Nos<br/>2. Hafele Multipurpose Lock -1Pc<br/>"
                "3. Ebco Preminum Tower Bolt -2Nos<br/>4. Ebco Cylindrical Legs -6Nos",
            ],
            [
                "L1",
                "No",
                "S1",
                "900 X 100 X 680mm",
                "1. Hettich Unspring 105° Hinges -4Nos<br/>2. Ebco POM40 (Push to Open) -2Pc",
            ],
        ],
    },
}


LEGEND_LINES = [
    "Existing Electrical - EE    Existing Plumbing - EP",
    "New Electrical - NE    New Plumbing - NP",
    "Shifted Electrical - SE    Shifted Plumbing - SP",
]


def _add_electrical_sheet(flow, room, elec_codes, plumb_codes):
    """A minimal electrical/plumbing sheet: title block, point markers, legend."""
    title = Table([[f"DRAWING NAME:\n{room}\nELECTRICAL"]], colWidths=[520])
    title.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.5, colors.grey), ("FONTSIZE", (0, 0), (-1, -1), 9)]))
    flow.append(title)
    flow.append(Spacer(1, 6))
    flow.append(Paragraph(" ".join(elec_codes + plumb_codes), CELL))
    flow.append(Spacer(1, 6))
    for line in LEGEND_LINES:
        flow.append(Paragraph(line, CELL))


def build(path: str) -> None:
    doc = SimpleDocTemplate(path, pagesize=A4, title="Shop Order Drawing")
    flow = []
    for i, (room, data) in enumerate(PROJECT.items()):
        if i:
            flow.append(PageBreak())
        # Title block (holds the DRAWING NAME the room detector reads).
        title = Table([[f"DRAWING NAME:\n{room}\nELEVATION"]], colWidths=[520])
        title.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.5, colors.grey), ("FONTSIZE", (0, 0), (-1, -1), 9)]))
        flow.append(title)
        flow.append(Spacer(1, 6))
        for line in data["finishes"]:
            flow.append(Paragraph(line, CELL))
        flow.append(Spacer(1, 6))

        table_data = [["Cabinet Code", "Carcass", "Shutter", "Sizes", "Hardware Details"]]
        for row in data["rows"]:
            table_data.append([row[0], row[1], row[2], row[3], Paragraph(row[4], CELL)])
        t = Table(table_data, colWidths=[45, 35, 35, 100, 220])
        t.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        flow.append(t)

    # A Kitchen electrical/plumbing sheet: 3 electrical + 2 plumbing points.
    flow.append(PageBreak())
    _add_electrical_sheet(flow, "KITCHEN", ["EE1", "EE2", "NE1"], ["EP1", "NP1"])

    doc.build(flow)
    print(f"wrote {path}")


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "sample-sod.pdf")
