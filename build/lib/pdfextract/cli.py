"""Command-line interface for the pdfextract plugin.

Usage examples::

    pdfextract report.pdf                     # print all tables as CSV
    pdfextract report.pdf --format json       # print as JSON
    pdfextract report.pdf -o out.csv          # write to a file
    pdfextract report.pdf --pages 1 2         # only pages 1 and 2
    pdfextract report.pdf --no-header         # do not treat row 1 as header

    # Inventory breakdown (project -> floor -> room -> item quantities):
    pdfextract schedule.pdf --inventory                 # indented summary
    pdfextract schedule.pdf --inventory -f csv          # flat breakdown
    pdfextract schedule.pdf --inventory --room-col Space --qty-col Nos
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from . import __version__
from .extractor import PdfTableExtractor
from .formatters import FORMATS, format_result
from .inventory import ColumnMapping, build_inventory
from .inventory_report import INVENTORY_FORMATS, format_inventory

ALL_FORMATS = tuple(sorted(set(FORMATS) | set(INVENTORY_FORMATS)))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pdfextract",
        description="Extract tabular data from a PDF and convert it to a tabular format.",
    )
    parser.add_argument("pdf", help="Path to the input PDF file")
    parser.add_argument(
        "-f",
        "--format",
        choices=ALL_FORMATS,
        default=None,
        help=(
            "Output format. Table mode: csv (default), tsv, json, markdown. "
            "Inventory mode: text (default), csv, json."
        ),
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Write output to this file instead of stdout",
    )
    parser.add_argument(
        "--pages",
        type=int,
        nargs="+",
        metavar="N",
        help="1-based page numbers to extract (default: all pages)",
    )
    parser.add_argument(
        "--no-header",
        dest="header",
        action="store_false",
        help="Do not treat the first row of each table as a header",
    )
    parser.add_argument(
        "--password",
        help="Password for an encrypted PDF",
    )

    inv = parser.add_argument_group("inventory mode")
    inv.add_argument(
        "--inventory",
        action="store_true",
        help="Aggregate rows into an item-quantity breakdown by floor and room",
    )
    inv.add_argument("--floor-col", help="Column name or 0-based index for the floor/level")
    inv.add_argument("--room-col", help="Column name or 0-based index for the room/space")
    inv.add_argument("--item-col", help="Column name or 0-based index for the item/material")
    inv.add_argument("--qty-col", help="Column name or 0-based index for the quantity")
    inv.add_argument("--unit-col", help="Column name or 0-based index for the unit of measure")

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def _resolve_format(
    requested: str | None, inventory: bool, parser: argparse.ArgumentParser
) -> str:
    valid = INVENTORY_FORMATS if inventory else FORMATS
    default = "text" if inventory else "csv"
    if requested is None:
        return default
    if requested not in valid:
        mode = "inventory" if inventory else "table"
        parser.error(f"format {requested!r} is not valid in {mode} mode; choose from {valid}")
    return requested


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    fmt = _resolve_format(args.format, args.inventory, parser)

    extractor = PdfTableExtractor()
    try:
        result = extractor.extract(
            args.pdf,
            pages=args.pages,
            header=args.header,
            password=args.password,
        )
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001 - surface a clean message to the CLI user
        print(f"error: failed to extract {args.pdf!r}: {exc}", file=sys.stderr)
        return 1

    if result.is_empty:
        print(f"warning: no tables found in {args.pdf!r}", file=sys.stderr)

    if args.inventory:
        mapping = ColumnMapping(
            floor=args.floor_col,
            room=args.room_col,
            item=args.item_col,
            quantity=args.qty_col,
            unit=args.unit_col,
        )
        project = build_inventory(result, mapping)
        rendered = format_inventory(project, fmt)
        n_written = len(project.items)
        unit_label = "line item(s)"
    else:
        rendered = format_result(result, fmt)
        n_written = len(result.tables)
        unit_label = "table(s)"

    if args.output:
        with open(args.output, "w", encoding="utf-8", newline="") as handle:
            handle.write(rendered)
        print(
            f"Wrote {n_written} {unit_label} to {args.output} as {fmt}.",
            file=sys.stderr,
        )
    else:
        sys.stdout.write(rendered)
        if not rendered.endswith("\n"):
            sys.stdout.write("\n")

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
