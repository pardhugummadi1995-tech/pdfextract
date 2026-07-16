"""RISE Project Import Engine (Phase 1).

Import an Interior Shop Order Drawing (SOD) PDF, understand the project
structure, extract the inventory requirement, and generate a structured
Material Indent ready for RISE ERP.

Fully offline: no cloud, no OCR, no AI/LLM. Uses ``pdfplumber`` to read the
ruled hardware-schedule tables that real SODs use.
"""

from .model import (
    Cabinet,
    CategoryCounts,
    HardwareItem,
    IndentLine,
    ProjectModel,
    RoomSummaryRow,
)
from .pipeline import build_project
from .reader import read_sod

__version__ = "1.0.0"

__all__ = [
    "Cabinet",
    "CategoryCounts",
    "HardwareItem",
    "IndentLine",
    "ProjectModel",
    "RoomSummaryRow",
    "build_project",
    "read_sod",
    "__version__",
]
