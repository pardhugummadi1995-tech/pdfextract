"""Command-line interface for the RISE Project Import Engine.

    python -m rise_engine INPUT.pdf                 # summary + JSON/CSV/HTML in ./out
    python -m rise_engine INPUT.pdf -o build        # choose output dir
    python -m rise_engine INPUT.pdf --formats json csv xlsx html
"""

from __future__ import annotations

import argparse
import os
import sys

from . import __version__
from .exporter import (
    indent_to_csv,
    write_csv,
    write_excel,
    write_json,
    write_review_csv,
)
from .pipeline import build_project
from .reader import read_sod
from .report import write_html
from .review import apply_review

ALL_FORMATS = ("json", "csv", "xlsx", "html")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="rise_engine",
        description="Import an Interior Shop Order Drawing (SOD) PDF and generate a Material Indent.",
    )
    p.add_argument("pdf", help="Path to the SOD PDF")
    p.add_argument("-o", "--out", default="out", help="Output directory (default: ./out)")
    p.add_argument(
        "--formats",
        nargs="+",
        choices=ALL_FORMATS,
        default=list(ALL_FORMATS),
        help="Which outputs to write (default: all)",
    )
    p.add_argument("--print", action="store_true", help="Print the Material Indent CSV to stdout")
    p.add_argument(
        "--review",
        action="store_true",
        help="Write an editable review CSV (Approved Qty column) + HTML report, then stop",
    )
    p.add_argument(
        "--apply-review",
        metavar="REVIEW.csv",
        help="Apply an edited review CSV, then write the final outputs",
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        pages = read_sod(args.pdf)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    model = build_project(pages, source=os.path.basename(args.pdf))
    os.makedirs(args.out, exist_ok=True)
    base = os.path.splitext(os.path.basename(args.pdf))[0]

    if not model.recognized:
        print(
            f"WARNING: could not extract a Material Indent from '{model.source}'.\n"
            f"  {model.recognition_note}",
            file=sys.stderr,
        )
        return 3

    # --- Review-before-export workflow ---
    if args.apply_review:
        if not os.path.exists(args.apply_review):
            print(f"error: review file not found: {args.apply_review}", file=sys.stderr)
            return 2
        apply_review(model, args.apply_review)
        print(f"Applied review from {args.apply_review}.", file=sys.stderr)
    elif args.review:
        review_path = os.path.join(args.out, f"{base}-review.csv")
        write_review_csv(model, review_path)
        report_path = os.path.join(args.out, f"{base}-report.html")
        write_html(model, report_path)
        counts = model.category_counts
        print(
            f"Review needed for '{model.source}': {counts.cabinets} cabinets, "
            f"{counts.hardware_types} hardware types, {len(model.warnings)} warning(s).",
            file=sys.stderr,
        )
        print(f"  1. Edit the 'Approved Qty' column in: {review_path}", file=sys.stderr)
        print(f"  2. Preview: {report_path}", file=sys.stderr)
        print(
            f"  3. Finalise: python -m rise_engine {args.pdf} --apply-review {review_path}",
            file=sys.stderr,
        )
        return 0

    counts = model.category_counts
    written = []
    if "json" in args.formats:
        path = os.path.join(args.out, f"{base}.json")
        write_json(model, path)
        written.append(path)
    if "csv" in args.formats:
        path = os.path.join(args.out, f"{base}-material-indent.csv")
        write_csv(model, path)
        written.append(path)
    if "xlsx" in args.formats:
        path = os.path.join(args.out, f"{base}.xlsx")
        try:
            write_excel(model, path)
            written.append(path)
        except ImportError:
            print("warning: openpyxl not installed; skipping xlsx export", file=sys.stderr)
    if "html" in args.formats:
        path = os.path.join(args.out, f"{base}-report.html")
        write_html(model, path)
        written.append(path)

    if args.print:
        sys.stdout.write(indent_to_csv(model))

    tag = " (reviewed)" if model.reviewed else ""
    print(
        f"Imported '{model.source}'{tag}: {counts.rooms} rooms, {counts.cabinets} cabinets, "
        f"{counts.hardware_types} hardware types, {counts.hardware_qty:g} total hardware qty, "
        f"{counts.electrical_points} electrical / {counts.plumbing_points} plumbing points.",
        file=sys.stderr,
    )
    if model.warnings:
        print(f"{len(model.warnings)} warning(s).", file=sys.stderr)
    for path in written:
        print(f"  wrote {path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
