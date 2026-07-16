"""Electrical & plumbing point detection.

SOD electrical/plumbing sheets tag each point on the drawing with a code and
list a legend::

    Existing Electrical - EE    Existing Plumbing - EP
    New Electrical - NE         New Plumbing - NP
    Shifted Electrical - SE     Shifted Plumbing - SP

So electrical points look like EE1/NE2/SE1 and plumbing like EP1/NP1/SP2. We
only parse pages that carry the legend (true service sheets), and count distinct
codes per page (a code may appear both as a marker and in the notes table).
"""

from __future__ import annotations

import re

_ELEC_RE = re.compile(r"\b((?:EE|NE|SE)\d+)\b")
_PLUMB_RE = re.compile(r"\b((?:EP|NP|SP)\d+)\b")
_LEGEND_RE = re.compile(r"(Electrical|Plumbing)\s*-\s*(EE|NE|SE|EP|NP|SP)\b", re.IGNORECASE)


def is_service_sheet(text: str) -> bool:
    """True if the page is an electrical/plumbing sheet (has the legend)."""
    return bool(_LEGEND_RE.search(text or ""))


def detect_service_points(text: str):
    """Return (electrical_codes, plumbing_codes) as sets, or empty if not a
    service sheet."""
    if not is_service_sheet(text):
        return set(), set()
    return set(_ELEC_RE.findall(text)), set(_PLUMB_RE.findall(text))
