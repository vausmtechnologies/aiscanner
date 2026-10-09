"""Unit tests for category-specific metadata extractors and the metadata router."""

from __future__ import annotations

import time

import pytest

from metadata.company_extractor import extract_company_metadata
from metadata.equipment_extractor import extract_equipment_metadata
from metadata.metadata_router import extract_metadata
from metadata.people_extractor import extract_people_metadata
from metadata.vehicle_extractor import extract_vehicle_metadata


# ---------------------------------------------------------------------------
# Vehicle extractor
# ---------------------------------------------------------------------------

RC_TEXT = (
    "RC Book  State: Delhi  "
    "Vehicle Registration Number: DL01AB1234  "
    "Engine Number: EN998877  "
    "Chassis Number: CH112233445566  "
    "Registration Date: 15/06/2021  "
    "Owner's Name: Rajesh Kumar"
)


def test_vehicle_number_extracted() -> None:
    meta = extract_vehicle_metadata(RC_TEXT)
    assert meta["vehicle_number"] == "DL01AB1234"


def test_engine_number_extracted() -> None:
    meta = extract_vehicle_metadata(RC_TEXT)
    assert meta["engine_number"] == "EN998877"


def test_chassis_number_extracted() -> None:
    meta = extract_vehicle_metadata(RC_TEXT)
    assert meta["chassis_number"] == "CH112233445566"


def test_registration_date_extracted() -> None:
    meta = extract_vehicle_metadata(RC_TEXT)
    assert meta["registration_date"] == "15/06/2021"


def test_owner_name_extracted() -> None:
    meta = extract_vehicle_metadata(RC_TEXT)
    assert meta["owner_name"] is not None
    assert "Rajesh" in meta["owner_name"]


def test_vehicle_missing_fields_are_none() -> None:
    meta = extract_vehicle_metadata("some random text with no vehicle info")
    assert meta["vehicle_number"] is None
    assert meta["engine_number"] is None
    assert meta["chassis_number"] is None


# ---------------------------------------------------------------------------
# Company extractor
# ---------------------------------------------------------------------------

GST_TEXT = (
    "Form GST REG-06  "
    "GSTIN: 27AAPFU0939F1ZV  "
    "Legal Name: ACME Private Limited  "
    "CIN: U12345MH2010PLC123456  "
    "Permanent Account Number: AAPFU0939F"
)


def test_gstin_extracted() -> None:
    meta = extract_company_metadata(GST_TEXT)
    assert meta["gstin"] == "27AAPFU0939F1ZV"


def test_company_name_extracted() -> None:
    meta = extract_company_metadata(GST_TEXT)
    assert meta["company_name"] is not None
    assert "ACME" in meta["company_name"]


def test_cin_extracted() -> None:
    meta = extract_company_metadata(GST_TEXT)
    assert meta["cin"] == "U12345MH2010PLC123456"


def test_pan_extracted() -> None:
    meta = extract_company_metadata(GST_TEXT)
    assert meta["pan_number"] == "AAPFU0939F"


def test_company_missing_fields_are_none() -> None:
    meta = extract_company_metadata("some random company text")
    assert meta["gstin"] is None
    assert meta["cin"] is None
    assert meta["pan_number"] is None


# ---------------------------------------------------------------------------
# Equipment extractor
# ---------------------------------------------------------------------------

INVOICE_TEXT = (
    "Purchase Invoice  "
    "Invoice Number: INV-20230456  "
    "Serial Number: SN-EQ445566  "
    "Model Number: DM-X200  "
    "Purchase Order: PO-987654"
)


def test_invoice_number_extracted() -> None:
    meta = extract_equipment_metadata(INVOICE_TEXT)
    assert meta["invoice_number"] == "INV-20230456"


def test_serial_number_extracted() -> None:
    meta = extract_equipment_metadata(INVOICE_TEXT)
    assert meta["serial_number"] == "SN-EQ445566"


def test_model_number_extracted() -> None:
    meta = extract_equipment_metadata(INVOICE_TEXT)
    assert meta["model_number"] is not None


def test_purchase_order_extracted() -> None:
    meta = extract_equipment_metadata(INVOICE_TEXT)
    assert meta["purchase_order"] == "PO-987654"


def test_equipment_missing_fields_are_none() -> None:
    meta = extract_equipment_metadata("warranty period 24 months general text")
    assert meta["invoice_number"] is None
    assert meta["serial_number"] is None


# ---------------------------------------------------------------------------
# People extractor
# ---------------------------------------------------------------------------

PASSPORT_TEXT = (
    "Passport Number: A1234567  "
    "Employee ID: EMP004567  "
    "Aadhaar Number: 1234 5678 9012  "
    "Date of Birth: 1990-05-22"
)


def test_passport_number_extracted() -> None:
    meta = extract_people_metadata(PASSPORT_TEXT)
    assert meta["passport_number"] == "A1234567"


def test_employee_id_extracted() -> None:
    meta = extract_people_metadata(PASSPORT_TEXT)
    assert meta["employee_id"] == "EMP004567"


def test_aadhaar_number_extracted() -> None:
    meta = extract_people_metadata(PASSPORT_TEXT)
    assert meta["aadhaar_number"] == "1234 5678 9012"


def test_date_of_birth_extracted() -> None:
    meta = extract_people_metadata(PASSPORT_TEXT)
    assert meta["date_of_birth"] == "1990-05-22"


def test_people_missing_fields_are_none() -> None:
    meta = extract_people_metadata("employee details form general text")
    assert meta["passport_number"] is None
    assert meta["aadhaar_number"] is None


# ---------------------------------------------------------------------------
# Metadata router
# ---------------------------------------------------------------------------

def test_router_dispatches_vehicles() -> None:
    meta = extract_metadata("Vehicles", RC_TEXT)
    assert "vehicle_number" in meta


def test_router_dispatches_company() -> None:
    meta = extract_metadata("Company", GST_TEXT)
    assert "gstin" in meta


def test_router_dispatches_equipments() -> None:
    meta = extract_metadata("Equipments", INVOICE_TEXT)
    assert "invoice_number" in meta


def test_router_dispatches_people() -> None:
    meta = extract_metadata("People", PASSPORT_TEXT)
    assert "employee_id" in meta


def test_router_returns_empty_for_unknown_category() -> None:
    assert extract_metadata("Unknown", "some text") == {}


def test_router_returns_empty_for_none_category() -> None:
    assert extract_metadata(None, "some text") == {}


# ---------------------------------------------------------------------------
# Performance: each extractor must run in < 20 ms
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("fn,text,label", [
    (extract_vehicle_metadata,   RC_TEXT,       "vehicle"),
    (extract_company_metadata,   GST_TEXT,      "company"),
    (extract_equipment_metadata, INVOICE_TEXT,  "equipment"),
    (extract_people_metadata,    PASSPORT_TEXT, "people"),
])
def test_extraction_under_20ms(fn, text, label) -> None:
    start = time.perf_counter()
    fn(text)
    elapsed_ms = (time.perf_counter() - start) * 1000
    assert elapsed_ms < 20, f"{label} extractor took {elapsed_ms:.1f} ms (limit 20 ms)"
