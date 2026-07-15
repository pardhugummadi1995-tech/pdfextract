"""pdfextract: a plugin that extracts data from PDFs into tabular formats.

Public API::

    from pdfextract import PdfTableExtractor, extract, format_result

    result = extract("report.pdf")
    print(format_result(result, "csv"))
"""

from __future__ import annotations

from .core import ExtractionResult, Table
from .extractor import PdfTableExtractor
from .formatters import FORMATS, format_result, format_table
from .plugin import (
    ExtractionPlugin,
    PluginRegistry,
    default_registry,
    register,
)

__version__ = "0.1.0"

# Register the bundled reference plugin on import so the default registry is
# immediately usable by the host application.
if "pdf_table" not in {p.name for p in default_registry.plugins()}:
    default_registry.register(PdfTableExtractor())


def extract(source: str, *, plugin: str | None = None, **options) -> ExtractionResult:
    """Convenience wrapper that extracts ``source`` via the default registry."""
    return default_registry.extract(source, plugin=plugin, **options)


__all__ = [
    "ExtractionPlugin",
    "ExtractionResult",
    "FORMATS",
    "PdfTableExtractor",
    "PluginRegistry",
    "Table",
    "__version__",
    "default_registry",
    "extract",
    "format_result",
    "format_table",
    "register",
]
