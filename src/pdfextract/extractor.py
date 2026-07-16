"""PDF table extraction plugin built on top of ``pdfplumber``.

This is the reference plugin bundled with the application. It reads a PDF file,
detects tables page by page, and returns them as normalized
:class:`~pdfextract.core.Table` objects.
"""

from __future__ import annotations

import os

import pdfplumber

from .core import ExtractionResult, Table
from .plugin import ExtractionPlugin


def _clean_cell(value: str | None) -> str:
    """Normalize a raw pdfplumber cell into a trimmed single-line string."""
    if value is None:
        return ""
    # pdfplumber keeps intra-cell newlines; collapse them for tabular output.
    return " ".join(str(value).split())


class PdfTableExtractor(ExtractionPlugin):
    """Extract tables from PDF documents using ``pdfplumber``."""

    name = "pdf_table"

    def can_handle(self, source: str) -> bool:
        return isinstance(source, str) and source.lower().endswith(".pdf")

    def extract(
        self,
        source: str,
        *,
        pages: list[int] | None = None,
        header: bool = True,
        password: str | None = None,
        **_ignored,
    ) -> ExtractionResult:
        """Extract tables from ``source``.

        Args:
            source: Path to the PDF file.
            pages: Optional list of 1-based page numbers to restrict extraction
                to. When ``None`` all pages are scanned.
            header: When ``True`` the first row of each table becomes its header.
            password: Optional password for encrypted PDFs.
        """
        if not os.path.exists(source):
            raise FileNotFoundError(f"PDF not found: {source}")

        wanted = set(pages) if pages else None
        tables: list[Table] = []

        open_kwargs = {"password": password} if password else {}
        with pdfplumber.open(source, **open_kwargs) as pdf:
            page_count = len(pdf.pages)
            for page_number, page in enumerate(pdf.pages, start=1):
                if wanted is not None and page_number not in wanted:
                    continue
                for table_index, raw in enumerate(page.extract_tables()):
                    cleaned = [[_clean_cell(cell) for cell in row] for row in raw]
                    if not cleaned:
                        continue
                    if header:
                        head, *body = cleaned
                        table = Table(
                            rows=body,
                            header=head,
                            page=page_number,
                            index=table_index,
                        )
                    else:
                        table = Table(rows=cleaned, page=page_number, index=table_index)
                    tables.append(table)

        return ExtractionResult(
            tables=tables,
            source=source,
            plugin=self.name,
            metadata={"page_count": page_count, "header": header},
        )
