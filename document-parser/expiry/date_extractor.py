"""Extract all date strings from OCR text using compiled regex patterns.

Supported formats:
  YYYY-MM-DD          2026-05-09
  DD/MM/YYYY          09/05/2026
  DD-MM-YYYY          09-05-2026
  DD-MMM-YYYY         05-JUN-2025  (insurance / vehicle docs)
  DD MMM YYYY         06 Jun 2025
  MMM DD YYYY         Jun 06 2025
  DD Month YYYY       09 May 2026
  Month DD YYYY       May 09 2026
  DD Month, YYYY      09 May, 2026  (trailing comma variant)
"""

from __future__ import annotations

import re
from datetime import date, datetime

# ---------------------------------------------------------------------------
# Compiled patterns — one capture group each, in priority order.
# ---------------------------------------------------------------------------

_MONTHS = (
    "january|february|march|april|may|june|july|august|september|"
    "october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec"
)

_DATE_PATTERNS: list[re.Pattern[str]] = [
    # ISO: 2026-05-09
    re.compile(r'\b(\d{4}-\d{2}-\d{2})\b'),
    # DD/MM/YYYY
    re.compile(r'\b(\d{1,2}/\d{1,2}/\d{4})\b'),
    # DD-MMM-YYYY  e.g. 05-JUN-2025  (must come before plain DD-MM-YYYY)
    re.compile(r'\b(\d{1,2}-[A-Za-z]{3}-\d{4})\b'),
    # DD-MM-YYYY  (day-first numeric)
    re.compile(r'\b(\d{1,2}-\d{1,2}-\d{4})\b'),
    # DD MMM YYYY  e.g. 06 Jun 2025  (abbreviated month, no comma)
    re.compile(rf'\b(\d{{1,2}}\s+[A-Za-z]{{3}}\s+\d{{4}})\b'),
    # MMM DD YYYY  e.g. Jun 06 2025
    re.compile(rf'\b([A-Za-z]{{3}}\s+\d{{1,2}}\s+\d{{4}})\b'),
    # DD Month YYYY  or  DD Month, YYYY  (full month name)
    re.compile(rf'\b(\d{{1,2}}\s+(?:{_MONTHS}),?\s+\d{{4}})\b', re.IGNORECASE),
    # Month DD YYYY  or  Month DD, YYYY  (full month name)
    re.compile(rf'\b((?:{_MONTHS})\s+\d{{1,2}},?\s+\d{{4}})\b', re.IGNORECASE),
]

# ---------------------------------------------------------------------------
# strptime format strings tried in order inside _parse_date
# ---------------------------------------------------------------------------

_PARSE_FORMATS = [
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%d-%b-%Y",   # 05-JUN-2025
    "%d-%m-%Y",
    "%d %b %Y",   # 06 Jun 2025
    "%b %d %Y",   # Jun 06 2025
    "%d %B %Y",
    "%B %d %Y",
]


def extract_dates(text: str) -> list[date]:
    """Return a deduplicated, sorted list of date objects found in *text*.

    Strings that cannot be parsed into a valid calendar date are silently
    skipped (e.g. 30/02/2026).
    """
    raw_strings: list[str] = []
    for pattern in _DATE_PATTERNS:
        for m in pattern.finditer(text):
            raw_strings.append(m.group(1))

    parsed: list[date] = []
    seen: set[date] = set()
    for raw in raw_strings:
        d = _parse_date(raw)
        if d and d not in seen:
            seen.add(d)
            parsed.append(d)

    return sorted(parsed)


def normalize_date(date_string: str) -> str | None:
    """Convert any supported date string to ISO YYYY-MM-DD, or return None."""
    d = _parse_date(date_string.strip())
    return d.isoformat() if d else None


def _parse_date(raw: str) -> date | None:
    """Attempt to convert a raw date string to a date object."""
    raw = raw.strip().rstrip(",")
    for fmt in _PARSE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None
