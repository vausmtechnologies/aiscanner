"""Extract company-specific metadata from OCR text using compiled regex patterns."""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Compiled patterns
# --------------------------------------------------------------------------- #

# GSTIN: 15-char format  e.g. 27AAPFU0939F1ZV
_GSTIN        = re.compile(r'\b(\d{2}[A-Z]{5}\d{4}[A-Z]\d[Z][A-Z0-9])\b')

# CIN: U12345AB1234ABC123456
_CIN          = re.compile(r'\b(U\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6})\b')

# PAN: ABCDE1234F
_PAN          = re.compile(r'\b([A-Z]{5}\d{4}[A-Z])\b')

# Company / trade name — the line that follows "legal name" or "trade name" labels
_COMPANY_NAME = re.compile(
    r'(?:legal\s*name|trade\s*name|company\s*name|name\s*of\s*(?:the\s*)?(?:company|business|firm))[:\s]+'
    r'([A-Za-z0-9 &.,\'\-]{3,80})',
    re.IGNORECASE,
)

# US Employer Identification Number: 12-3456789 (the label may carry a note, e.g. "EIN (sample)")
_EIN          = re.compile(r'\bEIN\b(?:\s*\([^)\n]*\)|\s+(?:fictional\s+)?test\s+value)?[:\s]*(\d{2}-\d{7})\b', re.IGNORECASE)
_ENTITY_TYPE  = re.compile(r'entity\s*type[:\s]+([A-Za-z][A-Za-z ().,\-]{2,60}?)(?=\s*(?:\n|ein\b|business\b|$))', re.IGNORECASE)
_BUSINESS_ADDRESS = re.compile(r'business\s*address[:\s]+([A-Za-z0-9 ,.#\-]{5,120})', re.IGNORECASE)


def extract_company_metadata(text: str) -> dict[str, str | None]:
    """Extract company document fields from cleaned OCR text.

    Returns a dict with keys: gstin, company_name, cin, pan_number.
    Absent fields are None.
    """
    m_gstin   = _GSTIN.search(text)
    m_cin     = _CIN.search(text)
    m_pan     = _PAN.search(text)
    m_company = _COMPANY_NAME.search(text)

    result: dict[str, str | None] = {
        "gstin":        _clean(m_gstin),
        "company_name": _clean(m_company, group=1),
        "cin":          _clean(m_cin),
        "pan_number":   _clean(m_pan),
    }
    for field, pattern in (("ein", _EIN), ("entity_type", _ENTITY_TYPE), ("business_address", _BUSINESS_ADDRESS)):
        value = _clean(pattern.search(text), group=1)
        if value:
            result[field] = value
    logger.debug("Company metadata extracted: %s", result)
    return result


def _clean(match: re.Match | None, group: int = 0) -> str | None:
    if match is None:
        return None
    value = match.group(group).strip()
    return re.sub(r'\s+', ' ', value) or None
