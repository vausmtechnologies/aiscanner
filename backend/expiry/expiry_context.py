"""Detect expiry-context keywords and find the date that appears nearby.

Each entry in EXPIRY_CONTEXT_PATTERNS is a compiled regex that captures a
date string immediately adjacent to an expiry keyword phrase. The captured
text is later parsed by date_extractor._parse_date.

Special patterns:
  PERIOD_PATTERN  — matches "To DD-MMM-YYYY" (vehicle insurance policy period)
"""

from __future__ import annotations

import re
from datetime import date

from expiry.date_extractor import _parse_date

# ---------------------------------------------------------------------------
# Generic expiry keyword phrases (category-agnostic)
# ---------------------------------------------------------------------------

_GENERIC_PHRASES = [
    r"expir(?:y|ation|es?(?:\s*on)?)",
    r"valid\s*(?:until|upto|up\s*to|till|thru|through|to)",
    r"validity",
    r"renewal\s*date",
    r"certificate\s*valid(?:\s*until|\s*till|thru|through)?",
    r"expiry\s*date",
    r"expiration\s*date",
    r"risk\s*expiry(?:\s*date)?",
    r"policy\s*(?:expiry|valid(?:\s*till|thru|through)?)",
    r"period\s*of\s*insurance",
    r"period\s*of\s*own\s*damage",
    r"insurance\s*valid",
    r"policy\s*period",
]

# Start-of-validity phrases — mapped to expiry.start_date
_START_PHRASES = [
    r"valid\s*from",
    r"valid\s*start",
    r"effective\s*(?:from|date)",
    r"commenc(?:ing|ement)(?:\s*(?:from|on|date))?",
    r"start\s*date",
    r"period\s*from",
    r"date\s*of\s*commencement",
]

# ---------------------------------------------------------------------------
# Category-specific phrases  (document_type → additional phrases)
# ---------------------------------------------------------------------------

CATEGORY_PHRASES: dict[str, list[str]] = {
    "Vehicles": [
        r"insurance\s*(?:expiry|valid|expiration)",
        r"fitness\s*(?:expiry|valid(?:\s*till)?|certificate)",
        r"puc\s*(?:expiry|valid(?:\s*till)?)",
        r"road\s*tax\s*(?:valid|expiry)",
        r"risk\s*expiry(?:\s*date)?",
        r"period\s*of\s*own\s*damage",
        r"period\s*of\s*(?:third\s*party\s*)?insurance",
    ],
    "Company": [
        r"licen[sc]e\s*(?:expiry|valid(?:\s*till)?|expiration)",
        r"registration\s*valid(?:\s*until|\s*till)?",
        r"gst\s*(?:valid|expiry)",
    ],
    "Equipments": [
        r"amc\s*(?:expiry|valid(?:\s*till|thru|through)?|expiration)",
        r"warranty\s*(?:expiry|valid(?:\s*till|thru|through)?|expiration|period)",
        r"service\s*validity",
        r"maintenance\s*(?:due|expiry)",
        r"retest",
        r"next\s*(?:test|inspection)\s*date",
    ],
    "People": [
        r"passport\s*(?:expiry|expiration|valid(?:\s*till)?)",
        r"contract\s*(?:expiry|expiration|valid(?:\s*till)?)",
        r"visa\s*(?:expiry|valid(?:\s*till)?)",
        r"employment\s*(?:contract\s*)?(?:valid|expiry)",
        r"policy\s*(?:expiry|valid(?:\s*till)?)",   # health insurance
        r"insurance\s*valid",
    ],
}

# ---------------------------------------------------------------------------
# Period pattern: "To DD-MMM-YYYY"  or  "To DD/MM/YYYY"  etc.
# Used for vehicle insurance policy period lines.
# ---------------------------------------------------------------------------

_DATE_TOKEN_RAW = (
    r"\d{4}-\d{2}-\d{2}"
    r"|\d{1,2}/\d{1,2}/\d{4}"
    r"|\d{1,2}-[A-Za-z]{3}-\d{4}"   # DD-MMM-YYYY  ← NEW
    r"|\d{1,2}-\d{1,2}-\d{4}"
    r"|\d{1,2}\s+[A-Za-z]{3}\s+\d{4}"   # DD MMM YYYY
    r"|[A-Za-z]{3}\s+\d{1,2}\s+\d{4}"   # MMM DD YYYY
    r"|\d{1,2}\s+(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|"
    r"jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|"
    r"nov(?:ember)?|dec(?:ember)?),?\s+\d{4}"
    r"|(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|"
    r"jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|"
    r"nov(?:ember)?|dec(?:ember)?)\s+\d{1,2},?\s+\d{4}"
)
_DATE_TOKEN = f"({_DATE_TOKEN_RAW})"

# Highest-priority: "To <date>" — the end-date of a policy period
# e.g. "Period of Own Damage : 06-JUN-2024 To 05-JUN-2025"
_PERIOD_TO_PATTERN: re.Pattern[str] = re.compile(
    rf"\bTo\s+{_DATE_TOKEN}",
    re.IGNORECASE,
)

# Start of a From/To validity period: "Valid From 01/01/2024 To 01/01/2026"
_PERIOD_FROM_PATTERN: re.Pattern[str] = re.compile(
    rf"\bFrom\s+{_DATE_TOKEN}",
    re.IGNORECASE,
)

# "06-JUN-2024 To 05-JUN-2025" — first date is the period start
_PERIOD_RANGE_PATTERN: re.Pattern[str] = re.compile(
    rf"{_DATE_TOKEN}\s+To\s+{_DATE_TOKEN}",
    re.IGNORECASE,
)

# Keyword + date patterns, up to 50 chars between them
def _build_patterns(phrases: list[str]) -> list[re.Pattern[str]]:
    """Compile keyword + date patterns with up to 50 chars between them."""
    compiled = []
    for phrase in phrases:
        # keyword … date
        compiled.append(re.compile(
            rf"(?:{phrase})\W{{1,50}}{_DATE_TOKEN}",
            re.IGNORECASE,
        ))
        # date … keyword
        compiled.append(re.compile(
            rf"{_DATE_TOKEN}\W{{1,50}}(?:{phrase})",
            re.IGNORECASE,
        ))
    return compiled


_GENERIC_COMPILED = _build_patterns(_GENERIC_PHRASES)
_START_COMPILED = _build_patterns(_START_PHRASES)
_CATEGORY_COMPILED: dict[str, list[re.Pattern[str]]] = {
    cat: _build_patterns(phrases)
    for cat, phrases in CATEGORY_PHRASES.items()
}


def detect_expiry_context(text: str, category: str | None = None) -> list[date]:
    """Return dates that appear adjacent to expiry keyword phrases.

    For Vehicles, the "To DATE" period pattern is checked first (highest
    precision for insurance policy period lines). Then category-specific
    patterns, then generic phrases.
    """
    found: list[date] = []
    seen: set[date] = set()

    def _add(raw: str) -> None:
        d = _parse_date(raw.strip().rstrip(","))
        if d and d not in seen:
            seen.add(d)
            found.append(d)

    # 1. "To DATE" period pattern (highest priority for insurance end-dates)
    if category == "Vehicles" or category is None:
        for m in _PERIOD_TO_PATTERN.finditer(text):
            _add(m.group(1))

    # 2. Category-specific keyword patterns
    patterns: list[re.Pattern[str]] = []
    if category and category in _CATEGORY_COMPILED:
        patterns.extend(_CATEGORY_COMPILED[category])
    patterns.extend(_GENERIC_COMPILED)

    for pattern in patterns:
        for m in pattern.finditer(text):
            _add(m.group(1))

    return sorted(found)


def detect_start_context(text: str, category: str | None = None) -> list[date]:
    """Return dates adjacent to start-of-validity phrases (valid from, effective from).

    Also captures ``From <date>`` period starts so Valid From / Valid Thru pairs
    populate ``start_date`` in the API response.
    """
    found: list[date] = []
    seen: set[date] = set()

    def _add(raw: str) -> None:
        d = _parse_date(raw.strip().rstrip(","))
        if d and d not in seen:
            seen.add(d)
            found.append(d)

    for m in _PERIOD_FROM_PATTERN.finditer(text):
        _add(m.group(1))

    for m in _PERIOD_RANGE_PATTERN.finditer(text):
        _add(m.group(1))

    for pattern in _START_COMPILED:
        for m in pattern.finditer(text):
            _add(m.group(1))

    return sorted(found)
