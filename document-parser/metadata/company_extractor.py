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
    r'(?:legal\s*name|trade\s*name|name\s*of\s*(?:the\s*)?(?:company|business|firm))[:\s]+'
    r'([A-Za-z0-9\s&.,\'\-]{3,80})',
    re.IGNORECASE,
)


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
    logger.debug("Company metadata extracted: %s", result)
    return result


def _clean(match: re.Match | None, group: int = 0) -> str | None:
    if match is None:
        return None
    value = match.group(group).strip()
    return re.sub(r'\s+', ' ', value) or None
