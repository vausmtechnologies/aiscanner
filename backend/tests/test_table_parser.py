"""Tests for the table-aware parsing engine: detector, parser, mapper."""

from __future__ import annotations

import io
import time

import pytest

from layout.table_mapper import map_fields
from layout.table_parser import merge_tables, parse_table_rows

# ---------------------------------------------------------------------------
# Fixtures — raw table data as pdfplumber would return it
# ---------------------------------------------------------------------------

VEHICLE_TABLE: list[list[str | None]] = [
    ["Registration No.", "PB 65 BC 7888"],
    ["Engine No.", "G4LAMM088619"],
    ["VIN/Chassis No.", "MALB251CLNM312124"],
    ["Fuel Type", "Petrol"],
    ["Model", "Swift VXI"],
    ["Owner Name", "Rajesh Kumar"],
]

INSURANCE_TABLE: list[list[str | None]] = [
    ["Policy No.", "INS-2024-001122"],
    ["Valid Till", "05-JUN-2025"],
    ["Insured Name", "Rajesh Kumar"],
    ["Risk Expiry Date", "05-JUN-2025"],
]

GST_TABLE: list[list[str | None]] = [
    ["GSTIN", "27AAPFU0939F1ZV"],
    ["Legal Name", "ACME Private Limited"],
    ["CIN", "U12345MH2010PLC123456"],
    ["PAN", "AAPFU0939F"],
    ["Principal Place of Business", "Mumbai, Maharashtra"],
]

EQUIPMENT_TABLE: list[list[str | None]] = [
    ["Invoice No.", "INV-20230456"],
    ["Serial No.", "SN-EQ445566"],
    ["Model No.", "DM-X200"],
    ["Purchase Order", "PO-987654"],
    ["Warranty Period", "24 months"],
]

EMPLOYEE_TABLE: list[list[str | None]] = [
    ["Employee ID", "EMP004567"],
    ["Employee Name", "Priya Singh"],
    ["Date of Birth", "1992-08-14"],
    ["Designation", "Senior Engineer"],
    ["Department", "Technology"],
    ["Joining Date", "2018-03-01"],
]


# ---------------------------------------------------------------------------
# table_parser — parse_table_rows
# ---------------------------------------------------------------------------

def test_parse_vehicle_table_keys_lowercased() -> None:
    parsed = parse_table_rows(VEHICLE_TABLE)
    assert "registration no." in parsed
    assert "engine no." in parsed


def test_parse_vehicle_table_values_preserved() -> None:
    parsed = parse_table_rows(VEHICLE_TABLE)
    assert parsed["registration no."] == "PB 65 BC 7888"
    assert parsed["engine no."] == "G4LAMM088619"
    assert parsed["vin/chassis no."] == "MALB251CLNM312124"


def test_parse_table_skips_empty_rows() -> None:
    table = [
        [None, None],
        ["Key", "Value"],
        ["", ""],
    ]
    parsed = parse_table_rows(table)
    assert len(parsed) == 1
    assert parsed["key"] == "Value"


def test_parse_table_skips_single_cell_rows() -> None:
    table = [["Header only"], ["Key", "Val"]]
    parsed = parse_table_rows(table)
    assert "key" in parsed
    assert "header only" not in parsed


def test_parse_table_multicolumn_value_joined() -> None:
    table = [["Key", "Part1", "Part2"]]
    parsed = parse_table_rows(table)
    assert parsed["key"] == "Part1 Part2"


# ---------------------------------------------------------------------------
# table_parser — merge_tables
# ---------------------------------------------------------------------------

def test_merge_tables_combines_dicts() -> None:
    t1 = parse_table_rows(VEHICLE_TABLE)
    t2 = parse_table_rows(INSURANCE_TABLE)
    merged = merge_tables([t1, t2])
    assert "registration no." in merged
    assert "policy no." in merged


def test_merge_tables_later_wins_on_conflict() -> None:
    t1 = {"key": "first"}
    t2 = {"key": "second"}
    merged = merge_tables([t1, t2])
    assert merged["key"] == "second"


def test_merge_empty_list_returns_empty() -> None:
    assert merge_tables([]) == {}


# ---------------------------------------------------------------------------
# table_mapper — map_fields
# ---------------------------------------------------------------------------

def test_map_vehicle_fields() -> None:
    parsed = parse_table_rows(VEHICLE_TABLE)
    metadata = map_fields(parsed, category="Vehicles")
    assert metadata.get("vehicle_number") == "PB 65 BC 7888"
    assert metadata.get("engine_number") == "G4LAMM088619"
    assert metadata.get("chassis_number") == "MALB251CLNM312124"
    assert metadata.get("fuel_type") == "Petrol"
    assert metadata.get("vehicle_model") == "Swift VXI"
    assert metadata.get("owner_name") == "Rajesh Kumar"


def test_map_company_fields() -> None:
    parsed = parse_table_rows(GST_TABLE)
    metadata = map_fields(parsed, category="Company")
    assert metadata.get("gstin") == "27AAPFU0939F1ZV"
    assert metadata.get("company_name") == "ACME Private Limited"
    assert metadata.get("cin") == "U12345MH2010PLC123456"
    assert metadata.get("pan_number") == "AAPFU0939F"


def test_map_equipment_fields() -> None:
    parsed = parse_table_rows(EQUIPMENT_TABLE)
    metadata = map_fields(parsed, category="Equipments")
    assert metadata.get("invoice_number") == "INV-20230456"
    assert metadata.get("serial_number") == "SN-EQ445566"
    assert metadata.get("model_number") == "DM-X200"
    assert metadata.get("purchase_order") == "PO-987654"
    assert metadata.get("warranty_period") == "24 months"


def test_map_people_fields() -> None:
    parsed = parse_table_rows(EMPLOYEE_TABLE)
    metadata = map_fields(parsed, category="People")
    assert metadata.get("employee_id") == "EMP004567"
    assert metadata.get("employee_name") == "Priya Singh"
    assert metadata.get("date_of_birth") == "1992-08-14"
    assert metadata.get("designation") == "Senior Engineer"
    assert metadata.get("department") == "Technology"


def test_map_fields_returns_empty_for_empty_input() -> None:
    assert map_fields({}, category="Vehicles") == {}


def test_map_fields_unknown_category_tries_all_maps() -> None:
    parsed = parse_table_rows(GST_TABLE)
    metadata = map_fields(parsed, category=None)
    assert metadata.get("gstin") == "27AAPFU0939F1ZV"


def test_map_fields_unknown_keys_silently_ignored() -> None:
    data = {"completely unknown key xyz": "some value"}
    assert map_fields(data, category="Vehicles") == {}


# ---------------------------------------------------------------------------
# table_detector — smoke test (no real PDF needed for unit tests)
# ---------------------------------------------------------------------------

def test_detect_tables_non_pdf_bytes_returns_empty() -> None:
    from layout.table_detector import detect_tables
    result = detect_tables(b"not a pdf at all")
    assert result == []


def test_detect_tables_on_minimal_pdf_does_not_raise() -> None:
    from layout.table_detector import detect_tables
    # A trivially minimal valid PDF with no tables — should return [] gracefully
    minimal_pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n"
        b"xref\n0 4\n0000000000 65535 f \n"
        b"trailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n0\n%%EOF\n"
    )
    result = detect_tables(minimal_pdf)
    assert isinstance(result, list)


# ---------------------------------------------------------------------------
# Performance
# ---------------------------------------------------------------------------

def test_parse_and_map_under_10ms() -> None:
    tables = [VEHICLE_TABLE, INSURANCE_TABLE, GST_TABLE, EQUIPMENT_TABLE, EMPLOYEE_TABLE]
    start = time.perf_counter()
    parsed = [parse_table_rows(t) for t in tables]
    merged = merge_tables(parsed)
    map_fields(merged, category="Vehicles")
    elapsed_ms = (time.perf_counter() - start) * 1000
    assert elapsed_ms < 10, f"Table parse+map took {elapsed_ms:.2f} ms (limit 10 ms)"
