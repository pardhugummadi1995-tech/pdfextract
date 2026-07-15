"""Command-line interface for the pdfextract plugin.

Usage examples::

    pdfextract report.pdf                     # print all tables as CSV
    pdfextract report.pdf --format json       # print as JSON
    pdfextract report.pdf -o out.csv          # write to a file
    pdfextract report.pdf --pages 1 2         # only pages 1 and 2
    pdfextract report.pdf --no-header         # do not treat row 1 as header
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from . import __version__
from .extractor import PdfTableExtractor
from .formatters import FORMATS, format_result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pdfextract",
        description="Extract tabular data from a PDF and convert it to a tabular format.",
    )
    parser.add_argument("pdf", help="Path to the input PDF file")
    parser.add_argument(
        "-f",
        "--format",
        choices=FORMATS,
        default="csv",
        help="Output format (default: csv)",
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
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

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

    rendered = format_result(result, args.format)

    if args.output:
        with open(args.output, "w", encoding="utf-8", newline="") as handle:
            handle.write(rendered)
        print(
            f"Wrote {len(result.tables)} table(s) to {args.output} as {args.format}.",
            file=sys.stderr,
        )
    else:
        sys.stdout.write(rendered)
        if not rendered.endswith("\n"):
            sys.stdout.write("\n")

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
