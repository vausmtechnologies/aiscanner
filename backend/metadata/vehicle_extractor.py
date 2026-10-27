"""Extract vehicle-specific metadata from OCR text using compiled regex patterns."""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Compiled patterns — compiled once at import time for < 20 ms per call.
# --------------------------------------------------------------------------- #

_VEHICLE_NUMBER = re.compile(r'\b([A-Z]{2}[\s-]?\d{1,2}[\s-]?[A-Z]{1,2}[\s-]?\d{4})\b')
_ENGINE_NUMBER  = re.compile(r'engine\s*(?:no|number)[:\s]*([A-Z0-9]{4,20})', re.IGNORECASE)
_CHASSIS_NUMBER = re.compile(r'chassis\s*(?:no|number)[:\s]*([A-Z0-9]{4,20})', re.IGNORECASE)
_REG_DATE       = re.compile(
    r'(?:registration\s*date|reg(?:istration)?\.?\s*dt\.?)[:\s]*'
    r'(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}|\d{4}[\/\-\.]\d{2}[\/\-\.]\d{2}|[A-Za-z]{3,9}\.?\s+\d{1,2},?\s+\d{4})',
    re.IGNORECASE,
)
# US / international labels: VIN is the chassis number, a licence plate is the vehicle number.
_LABEL_NOTE     = r'(?:\s*\([^)\n]*\)|\s+(?:fictional\s+)?test\s+value)?'  # "(sample)" or text left after the cleaner drops brackets
_VIN            = re.compile(r'\bVIN\b' + _LABEL_NOTE + r'[:\s]*([A-Z0-9]{11,30})\b', re.IGNORECASE)
_LICENSE_PLATE  = re.compile(
    r'licen[cs]e\s*plate(?:\s*(?:no|number))?' + _LABEL_NOTE + r'[:\s]*([A-Z0-9]{2,3}[ -]?[A-Z0-9]{3,6})\b',
    re.IGNORECASE,
)
_OWNER_NAME     = re.compile(
    r'(?:owner(?:\'?s)?\s*name|name\s*of\s*owner)[:\s]*([A-Z][A-Za-z\s]{2,50})',
    re.IGNORECASE,
)
_VEHICLE_TYPE  = re.compile(r'vehicle\s*type[:\s]*([A-Za-z][A-Za-z \-]{1,30}?)(?=\s*(?:\n|\(|licen|model|state|$))', re.IGNORECASE)
_VEHICLE_OWNER = re.compile(
    r"vehicle\s*owner[:\s]*([A-Z][A-Za-z&.,' \-]{2,50}?)(?=\s*(?:\n|\(|vehicle\b|$))",
    re.IGNORECASE,
)


def extract_vehicle_metadata(text: str) -> dict[str, str | None]:
    """Extract vehicle document fields from cleaned OCR text.

    Returns a dict with keys: vehicle_number, engine_number, chassis_number,
    registration_date, owner_name. Absent fields are None.
    """
    m_veh   = _VEHICLE_NUMBER.search(text)
    m_eng   = _ENGINE_NUMBER.search(text)
    m_chas  = _CHASSIS_NUMBER.search(text)
    m_date  = _REG_DATE.search(text)
    m_owner = _OWNER_NAME.search(text)
    m_vowner = _VEHICLE_OWNER.search(text)
    m_vin   = _VIN.search(text)
    m_plate = _LICENSE_PLATE.search(text)

    result: dict[str, str | None] = {
        "vehicle_number":    _clean(m_veh,   group=1) or _clean(m_plate, group=1),
        "engine_number":     _clean(m_eng,   group=1),
        "chassis_number":    _clean(m_chas,  group=1) or _clean(m_vin, group=1),
        "registration_date": _clean(m_date,  group=1),
        "owner_name":        _clean(m_owner, group=1) or _clean(m_vowner, group=1),
    }
    vehicle_type = _clean(_VEHICLE_TYPE.search(text), group=1)
    if vehicle_type:
        result["vehicle_type"] = vehicle_type
    logger.debug("Vehicle metadata extracted: %s", result)
    return result


def _clean(match: re.Match | None, group: int = 0) -> str | None:
    if match is None:
        return None
    value = match.group(group).strip()
    # Collapse internal whitespace runs
    return re.sub(r'\s+', ' ', value) or None
