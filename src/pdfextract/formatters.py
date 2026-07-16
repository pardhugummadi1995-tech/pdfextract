"""Convert extracted :class:`~pdfextract.core.Table` objects into tabular text.

Supported output formats: ``csv``, ``tsv``, ``json`` and ``markdown``.
"""

from __future__ import annotations

import csv
import io
import json

from .core import ExtractionResult, Table

FORMATS = ("csv", "tsv", "json", "markdown")


def to_delimited(table: Table, delimiter: str = ",") -> str:
    """Render a table as delimiter-separated values (CSV/TSV)."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=delimiter, lineterminator="\n")
    for row in table.as_matrix():
        writer.writerow(row)
    return buffer.getvalue()


def to_csv(table: Table) -> str:
    return to_delimited(table, delimiter=",")


def to_tsv(table: Table) -> str:
    return to_delimited(table, delimiter="\t")


def _rows_as_records(table: Table) -> list:
    """Return rows as list-of-dicts when a header exists, else list-of-lists."""
    if table.header is not None:
        keys = table.header
        records = []
        for row in table.normalized_rows():
            records.append({key: row[i] if i < len(row) else "" for i, key in enumerate(keys)})
        return records
    return table.normalized_rows()


def to_json(table: Table, *, indent: int = 2) -> str:
    payload = {
        "page": table.page,
        "index": table.index,
        "header": table.header,
        "rows": _rows_as_records(table),
    }
    return json.dumps(payload, indent=indent, ensure_ascii=False)


def _escape_md(cell: str) -> str:
    return cell.replace("|", "\\|")


def to_markdown(table: Table) -> str:
    matrix = table.as_matrix()
    if not matrix:
        return ""
    width = table.n_cols
    header = matrix[0]
    body = matrix[1:] if table.header is not None else matrix
    lines = []
    if table.header is not None:
        lines.append("| " + " | ".join(_escape_md(c) for c in header) + " |")
        lines.append("| " + " | ".join(["---"] * width) + " |")
    else:
        lines.append("| " + " | ".join([f"col{i + 1}" for i in range(width)]) + " |")
        lines.append("| " + " | ".join(["---"] * width) + " |")
    for row in body:
        lines.append("| " + " | ".join(_escape_md(c) for c in row) + " |")
    return "\n".join(lines) + "\n"


_TABLE_FORMATTERS = {
    "csv": to_csv,
    "tsv": to_tsv,
    "json": to_json,
    "markdown": to_markdown,
}


def format_table(table: Table, fmt: str) -> str:
    """Format a single table using ``fmt`` (one of :data:`FORMATS`)."""
    try:
        formatter = _TABLE_FORMATTERS[fmt]
    except KeyError as exc:
        raise ValueError(f"unknown format {fmt!r}; choose from {FORMATS}") from exc
    return formatter(table)


def format_result(result: ExtractionResult, fmt: str) -> str:
    """Format every table in ``result`` into a single string.

    For ``json`` the tables are combined into one JSON array. For the text
    formats they are concatenated with a blank line between each table.
    """
    if fmt not in FORMATS:
        raise ValueError(f"unknown format {fmt!r}; choose from {FORMATS}")

    if fmt == "json":
        payload = {
            "source": result.source,
            "plugin": result.plugin,
            "metadata": result.metadata,
            "tables": [
                {
                    "page": t.page,
                    "index": t.index,
                    "header": t.header,
                    "rows": _rows_as_records(t),
                }
                for t in result.tables
            ],
        }
        return json.dumps(payload, indent=2, ensure_ascii=False)

    return "\n".join(format_table(t, fmt) for t in result.tables)
