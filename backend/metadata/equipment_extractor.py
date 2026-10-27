"""Extract equipment-specific metadata from OCR text using compiled regex patterns."""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Compiled patterns
# --------------------------------------------------------------------------- #

_INVOICE_NUMBER = re.compile(
    r'invoice\s*(?:no|number|#)[:\s]*([A-Z0-9][A-Z0-9\-\/]{1,20})',
    re.IGNORECASE,
)
_SERIAL_NUMBER  = re.compile(
    r'serial\s*(?:no|number|#)[:\s]*([A-Z0-9][A-Z0-9\-\/]{1,20})',
    re.IGNORECASE,
)
_MODEL_NUMBER   = re.compile(
    r'model\s*(?:no|number|#)[:\s]*([A-Z0-9][A-Z0-9\-\/\s]{1,20})',
    re.IGNORECASE,
)
_PURCHASE_ORDER = re.compile(
    r'(?:purchase\s*order|p\.?o\.?\s*(?:no|number|#)?)[:\s]*([A-Z0-9][A-Z0-9\-\/]{1,20})',
    re.IGNORECASE,
)
_INVOICE_DATE   = re.compile(
    r'invoice\s*date[:\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}|\d{4}[\/\-\.]\d{2}[\/\-\.]\d{2}|[A-Za-z]{3,9}\.?\s+\d{1,2},?\s+\d{4})',
    re.IGNORECASE,
)
_TOTAL_AMOUNT   = re.compile(r'(?:total\s*due|grand\s*total|total\s*amount)[:\s]*([$€£₹]?\s?\d[\d,]*(?:\.\d{2})?)', re.IGNORECASE)


def extract_equipment_metadata(text: str) -> dict[str, str | None]:
    """Extract equipment document fields from cleaned OCR text.

    Returns a dict with keys: invoice_number, serial_number, model_number,
    purchase_order. Absent fields are None.
    """
    m_inv  = _INVOICE_NUMBER.search(text)
    m_ser  = _SERIAL_NUMBER.search(text)
    m_mod  = _MODEL_NUMBER.search(text)
    m_po   = _PURCHASE_ORDER.search(text)

    result: dict[str, str | None] = {
        "invoice_number": _clean(m_inv,  group=1),
        "serial_number":  _clean(m_ser,  group=1),
        "model_number":   _clean(m_mod,  group=1),
        "purchase_order": _clean(m_po,   group=1),
    }
    for field, pattern in (("invoice_date", _INVOICE_DATE), ("total_amount", _TOTAL_AMOUNT)):
        value = _clean(pattern.search(text), group=1)
        if value:
            result[field] = value
    logger.debug("Equipment metadata extracted: %s", result)
    return result


def _clean(match: re.Match | None, group: int = 0) -> str | None:
    if match is None:
        return None
    value = match.group(group).strip()
    return re.sub(r'\s+', ' ', value) or None
