"""Route metadata extraction to the correct category-specific extractor."""

from __future__ import annotations

import logging

from metadata.company_extractor import extract_company_metadata
from metadata.equipment_extractor import extract_equipment_metadata
from metadata.people_extractor import extract_people_metadata
from metadata.vehicle_extractor import extract_vehicle_metadata

logger = logging.getLogger(__name__)

# Map category names to extractor callables.
_EXTRACTORS = {
    "Vehicles":   extract_vehicle_metadata,
    "Company":    extract_company_metadata,
    "Equipments": extract_equipment_metadata,
    "People":     extract_people_metadata,
}


def extract_metadata(category: str | None, text: str) -> dict[str, str | None]:
    """Dispatch text to the correct extractor based on document category.

    If the category is unknown or None, returns an empty dict.
    All extractor functions return None for fields that are not found.
    """
    if not category:
        logger.debug("No category provided — skipping metadata extraction")
        return {}

    extractor = _EXTRACTORS.get(category)
    if extractor is None:
        logger.warning("No metadata extractor registered for category=%r", category)
        return {}

    return extractor(text)
