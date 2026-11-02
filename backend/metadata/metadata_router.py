"""Route metadata extraction to the correct category-specific extractor."""

from __future__ import annotations

import logging

from metadata.company_extractor import extract_company_metadata
from metadata.equipment_extractor import extract_equipment_metadata
from metadata.generic_extractor import extract_generic_metadata
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

    Categories without a dedicated extractor (trained / auto-created ones) fall back to
    generic "Label: value" extraction. A missing category returns an empty dict.
    All extractor functions return None for fields that are not found.
    """
    if not category:
        logger.debug("No category provided — skipping metadata extraction")
        return {}

    extractor = _EXTRACTORS.get(category)
    if extractor is None:
        logger.debug("No dedicated extractor for category=%r — using generic extraction", category)
        return extract_generic_metadata(text)

    return extractor(text)
