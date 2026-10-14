"""Map normalised table keys to the canonical metadata field schema.

Each category has its own mapping dictionary.  The top-level
``map_fields(table_data, category)`` function dispatches to the
right mapping and returns a clean metadata dict.

Key design choices:
- All table keys are already lower-cased by table_parser.parse_table_rows.
- Partial / fuzzy matching is done via ``_starts_with`` so that keys like
  "registration no." or "registration no" both map to "vehicle_number".
- Unknown keys are silently ignored.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Per-category field mappings  {table_key_prefix: canonical_field_name}
# ---------------------------------------------------------------------------

_VEHICLE_MAPPING: dict[str, str] = {
    "registration no":        "vehicle_number",
    "registration number":    "vehicle_number",
    "reg no":                 "vehicle_number",
    "vehicle no":             "vehicle_number",
    "vehicle number":         "vehicle_number",
    "engine no":              "engine_number",
    "engine number":          "engine_number",
    "vin/chassis no":         "chassis_number",
    "vin / chassis no":       "chassis_number",
    "chassis no":             "chassis_number",
    "chassis number":         "chassis_number",
    "vehicle identification": "chassis_number",
    "model":                  "vehicle_model",
    "make":                   "vehicle_make",
    "manufacturer":           "vehicle_make",
    "fuel type":              "fuel_type",
    "fuel":                   "fuel_type",
    "colour":                 "color",
    "color":                  "color",
    "owner":                  "owner_name",
    "owner name":             "owner_name",
    "name of owner":          "owner_name",
    "insured name":           "owner_name",
    "date of registration":   "registration_date",
    "registration date":      "registration_date",
    "policy no":              "policy_number",
    "policy number":          "policy_number",
    "insurance expiry":       "insurance_expiry",
    "valid till":             "insurance_expiry",
    "risk expiry date":       "insurance_expiry",
}

_COMPANY_MAPPING: dict[str, str] = {
    "gstin":                  "gstin",
    "gst no":                 "gstin",
    "gst number":             "gstin",
    "legal name":             "company_name",
    "trade name":             "company_name",
    "name of business":       "company_name",
    "company name":           "company_name",
    "cin":                    "cin",
    "corporate identity":     "cin",
    "pan":                    "pan_number",
    "pan number":             "pan_number",
    "permanent account":      "pan_number",
    "registration number":    "registration_number",
    "date of registration":   "registration_date",
    "address":                "registered_address",
    "principal place":        "registered_address",
}

_EQUIPMENT_MAPPING: dict[str, str] = {
    "invoice no":             "invoice_number",
    "invoice number":         "invoice_number",
    "serial no":              "serial_number",
    "serial number":          "serial_number",
    "model no":               "model_number",
    "model number":           "model_number",
    "model":                  "model_number",
    "purchase order":         "purchase_order",
    "p.o. no":                "purchase_order",
    "po no":                  "purchase_order",
    "amc expiry":             "amc_expiry",
    "warranty":               "warranty_period",
    "warranty period":        "warranty_period",
    "warranty expiry":        "warranty_expiry",
    "asset tag":              "asset_tag",
    "asset id":               "asset_id",
    "supplier":               "supplier_name",
    "vendor":                 "supplier_name",
}

_PEOPLE_MAPPING: dict[str, str] = {
    "employee id":            "employee_id",
    "employee no":            "employee_id",
    "emp id":                 "employee_id",
    "emp no":                 "employee_id",
    "name":                   "employee_name",
    "employee name":          "employee_name",
    "full name":              "employee_name",
    "passport no":            "passport_number",
    "passport number":        "passport_number",
    "aadhaar":                "aadhaar_number",
    "aadhaar no":             "aadhaar_number",
    "date of birth":          "date_of_birth",
    "dob":                    "date_of_birth",
    "designation":            "designation",
    "department":             "department",
    "joining date":           "joining_date",
    "policy no":              "policy_number",
    "policy number":          "policy_number",
    "sum insured":            "sum_insured",
    "insured name":           "insured_name",
    "member id":              "member_id",
}

_CATEGORY_MAPS: dict[str, dict[str, str]] = {
    "Vehicles":   _VEHICLE_MAPPING,
    "Company":    _COMPANY_MAPPING,
    "Equipments": _EQUIPMENT_MAPPING,
    "People":     _PEOPLE_MAPPING,
}


def map_fields(
    table_data: dict[str, str],
    category: str | None = None,
) -> dict[str, str]:
    """Map normalised table keys to canonical metadata field names.

    Args:
        table_data: Flat {lower_key: value} dict from table_parser.
        category:   Document category used to select the right mapping.
                    Falls back to checking all mappings if None.

    Returns:
        Dict of {canonical_field: value} with known fields only.
    """
    if not table_data:
        return {}

    # Determine which mapping(s) to try
    if category and category in _CATEGORY_MAPS:
        mappings = [_CATEGORY_MAPS[category]]
    else:
        mappings = list(_CATEGORY_MAPS.values())

    metadata: dict[str, str] = {}

    for mapping in mappings:
        for raw_key, value in table_data.items():
            canonical = _lookup(raw_key, mapping)
            if canonical and canonical not in metadata:
                metadata[canonical] = value

    logger.debug("Table field mapping: %d fields resolved from %d table keys",
                 len(metadata), len(table_data))
    return metadata


def _lookup(raw_key: str, mapping: dict[str, str]) -> str | None:
    """Find the canonical field name for *raw_key* using prefix matching."""
    # Exact match first
    if raw_key in mapping:
        return mapping[raw_key]
    # Prefix match — handles trailing punctuation like "registration no."
    for map_key, canonical in mapping.items():
        if raw_key.startswith(map_key) or map_key.startswith(raw_key):
            return canonical
    return None
