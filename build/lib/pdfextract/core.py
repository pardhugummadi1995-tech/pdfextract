"""Core data structures shared across the pdfextract plugin.

These models provide a normalized, format-agnostic representation of tabular
data extracted from a document. Extraction plugins produce :class:`Table`
objects, and formatters (see :mod:`pdfextract.formatters`) turn them into a
concrete tabular representation such as CSV or JSON.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Table:
    """A single rectangular table of string cells.

    Attributes:
        rows: The full grid of cells. Each inner list is one row.
        header: Optional column headers. When ``None`` the first row of
            ``rows`` is treated as data (i.e. the table is header-less).
        page: 1-based page number the table was extracted from, if known.
        index: 0-based position of the table on its page, if known.
    """

    rows: list[list[str]] = field(default_factory=list)
    header: list[str] | None = None
    page: int | None = None
    index: int | None = None

    @property
    def n_rows(self) -> int:
        return len(self.rows)

    @property
    def n_cols(self) -> int:
        widths = [len(r) for r in self.rows]
        if self.header is not None:
            widths.append(len(self.header))
        return max(widths) if widths else 0

    def normalized_rows(self) -> list[list[str]]:
        """Return rows padded to a uniform column count with empty strings."""
        width = self.n_cols
        return [list(row) + [""] * (width - len(row)) for row in self.rows]

    def as_matrix(self) -> list[list[str]]:
        """Return the table as a matrix including the header row (if any)."""
        matrix = self.normalized_rows()
        if self.header is not None:
            width = self.n_cols
            header = list(self.header) + [""] * (width - len(self.header))
            return [header, *matrix]
        return matrix


@dataclass
class ExtractionResult:
    """The outcome of running an extraction plugin over a source document.

    Attributes:
        tables: All tables discovered in the document, in reading order.
        source: Identifier of the source document (e.g. a file path).
        plugin: Name of the plugin that produced this result.
        metadata: Free-form extra information (page count, options, etc.).
    """

    tables: list[Table] = field(default_factory=list)
    source: str | None = None
    plugin: str | None = None
    metadata: dict = field(default_factory=dict)

    @property
    def is_empty(self) -> bool:
        return all(t.n_rows == 0 for t in self.tables) if self.tables else True
