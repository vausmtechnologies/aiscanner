"""Extract people-specific metadata from OCR text using compiled regex patterns."""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Compiled patterns
# --------------------------------------------------------------------------- #

# Passport number: one letter followed by 7 digits  e.g. A1234567
_PASSPORT  = re.compile(r'\b([A-Z]\d{7})\b')

# Aadhaar: three groups of 4 digits separated by spaces  e.g. 1234 5678 9012
_AADHAAR   = re.compile(r'\b(\d{4}\s\d{4}\s\d{4})\b')

# Employee ID: EMP followed by 3-6 digits  e.g. EMP001234
_EMP_ID    = re.compile(r'\b(EMP\d{3,6})\b', re.IGNORECASE)

# Date of birth: ISO  YYYY-MM-DD  or  DD/MM/YYYY  or  DD-MM-YYYY
_DOB       = re.compile(
    r'(?:date\s*of\s*birth|d\.?o\.?b\.?)[:\s]*'
    r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}|\d{4}[\/\-]\d{2}[\/\-]\d{2})',
    re.IGNORECASE,
)


def extract_people_metadata(text: str) -> dict[str, str | None]:
    """Extract people document fields from cleaned OCR text.

    Returns a dict with keys: employee_id, passport_number, aadhaar_number,
    date_of_birth. Absent fields are None.
    """
    m_emp      = _EMP_ID.search(text)
    m_passport = _PASSPORT.search(text)
    m_aadhaar  = _AADHAAR.search(text)
    m_dob      = _DOB.search(text)

    result: dict[str, str | None] = {
        "employee_id":     _clean(m_emp,      group=1),
        "passport_number": _clean(m_passport, group=1),
        "aadhaar_number":  _clean(m_aadhaar,  group=1),
        "date_of_birth":   _clean(m_dob,      group=1),
    }
    logger.debug("People metadata extracted: %s", result)
    return result


def _clean(match: re.Match | None, group: int = 0) -> str | None:
    if match is None:
        return None
    value = match.group(group).strip()
    return re.sub(r'\s+', ' ', value) or None
