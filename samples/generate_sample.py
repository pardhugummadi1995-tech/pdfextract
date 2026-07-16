"""Generate a representative Interior Shop Order Drawing (SOD) PDF.

This is a *test fixture generator*, not part of the app. It produces a
text-based PDF whose layout mirrors a typical interior SOD (project title block,
room sections, cabinet headers with dimensions, hardware schedules and finish
codes) so the browser app's detectors can be demonstrated end to end.

Usage:  python generate_sample.py [output.pdf]
"""

from __future__ import annotations

import sys

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

styles = getSampleStyleSheet()
H_ROOM = ParagraphStyle("Room", parent=styles["Heading2"], textColor=colors.HexColor("#1d4ed8"))
H_CAB = ParagraphStyle("Cab", parent=styles["Heading4"], spaceBefore=6)
BODY = styles["BodyText"]

# room -> list of (cabinet header, finishes dict, hardware rows[(desc, qty, unit)])
PROJECT = [
    (
        "Kitchen",
        [
            (
                "B1 Base Unit 600 x 580 x 850",
                {"Carcass Finish": "PLPL 18mm", "Shutter Finish": "Acrylic White", "Laminate Code": "LAM-101"},
                [
                    ("Hettich 105 Hinge", "8", "Nos"),
                    ("Handle SS 128mm", "2", "Nos"),
                    ("Drawer Runner 450mm", "2", "Pair"),
                    ("Leg PVC Adjustable", "4", "Nos"),
                ],
            ),
            (
                "B2 Base Unit 900 x 580 x 850",
                {"Carcass Finish": "PLPL 18mm", "Shutter Finish": "Acrylic White", "Laminate Code": "LAM-101"},
                [
                    ("Hettich 105 Hinge", "6", "Nos"),
                    ("Tower Bolt 4inch", "1", "Nos"),
                    ("Handle SS 128mm", "2", "Nos"),
                ],
            ),
            (
                "W1 Wall Unit 600 x 320 x 700",
                {"Carcass Finish": "PLPL 18mm", "Shutter Finish": "Acrylic White", "Laminate Code": "LAM-101"},
                [
                    ("Hettich 105 Hinge", "4", "Nos"),
                    ("Door Buffer", "4", "Nos"),
                ],
            ),
        ],
    ),
    (
        "Living",
        [
            (
                "TV1 TV Unit 1800 x 450 x 600",
                {"Carcass Finish": "PLPL 18mm", "Shutter Finish": "Veneer Teak", "Laminate Code": "LAM-220"},
                [
                    ("Handle SS 128mm", "3", "Nos"),
                    ("Drawer Runner 450mm", "2", "Pair"),
                    ("Shelf Support", "8", "Nos"),
                ],
            ),
        ],
    ),
    (
        "Master Bedroom",
        [
            (
                "WR1 Wardrobe 2100 x 600 x 2400",
                {"Carcass Finish": "PLPL 18mm", "Shutter Finish": "Membrane Ivory", "Laminate Code": "LAM-330"},
                [
                    ("Hettich 105 Hinge", "10", "Nos"),
                    ("Hanger Rod", "2", "Nos"),
                    ("Multipurpose Lock", "1", "No"),
                    ("Tower Bolt 4inch", "2", "Nos"),
                    ("Soft Close Mechanism", "", ""),  # missing qty -> verification required
                ],
            ),
            (
                "WR2 Wardrobe",  # no dimensions -> Dimension Missing
                {"Carcass Finish": "PLPL 18mm", "Shutter Finish": "Membrane Ivory", "Laminate Code": "LAM-330"},
                [
                    ("Hettich 105 Hinge", "6", "Nos"),
                    ("POM40", "4", "Nos"),
                    ("Mystery Gadget X", "2", "Nos"),  # unknown item
                ],
            ),
        ],
    ),
]


def build(path: str) -> None:
    doc = SimpleDocTemplate(path, pagesize=A4, title="Shop Order Drawing")
    flow = []

    flow.append(Paragraph("INTERIOR SHOP ORDER DRAWING", styles["Title"]))
    for label in [
        "Project Name: Aurora Residence",
        "Client: Prestige Group",
        "Drawing No: SOD-2024-017",
        "Revision: R2",
        "Date: 2026-07-10",
    ]:
        flow.append(Paragraph(label, BODY))
    flow.append(Spacer(1, 10))

    for room, cabinets in PROJECT:
        flow.append(Paragraph(room, H_ROOM))
        for header, finishes, hardware in cabinets:
            flow.append(Paragraph(header, H_CAB))
            data = [["Description", "Qty", "Unit"]]
            data.extend([[d, q, u] for (d, q, u) in hardware])
            t = Table(data, colWidths=[300, 60, 60])
            t.setStyle(
                TableStyle(
                    [
                        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ]
                )
            )
            flow.append(t)
            for key, val in finishes.items():
                flow.append(Paragraph(f"{key}: {val}", BODY))
            flow.append(Spacer(1, 8))

    doc.build(flow)
    print(f"wrote {path}")


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "sample-sod.pdf")
