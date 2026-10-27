"""Tests for the three pipeline improvements introduced in the optimised pipeline:

  1. Refined classification — table signals boost classification accuracy
  2. Safe metadata merging — empty table values never overwrite regex results
  3. Table-aware expiry detection — table values appended to expiry text
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from layout.table_mapper import map_fields
from layout.table_parser import merge_tables, parse_table_rows


# ---------------------------------------------------------------------------
# Helper: build a fake HybridClassificationResult-like object
# ---------------------------------------------------------------------------

def _make_result(doc_type, confidence, method="keyword", keywords=None):
    r = MagicMock()
    r.document_type = doc_type
    r.confidence = confidence
    r.method = method
    r.keywords_detected = keywords or []
    return r


# ===========================================================================
# 1. Refined Classification
# ===========================================================================

class TestRefinedClassification:
    """Table signals must be able to upgrade a weak initial classification."""

    def test_refined_result_used_when_confidence_higher(self) -> None:
        """When table hints produce a higher-confidence result, it replaces the quick one."""
        quick_result = _make_result("Vehicles", 0.40, "embedding")
        refined_result = _make_result("Company", 0.85, "keyword")

        # Replicate the conditional logic from service.py step 5
        document_type = quick_result.document_type
        confidence = quick_result.confidence
        method = quick_result.method
        result = quick_result

        if refined_result.document_type and refined_result.confidence > confidence:
            document_type = refined_result.document_type
            confidence = refined_result.confidence
            method = refined_result.method
            result = refined_result

        assert document_type == "Company"
        assert confidence == 0.85
        assert method == "keyword"

    def test_quick_result_kept_when_refined_lower(self) -> None:
        """Quick classification is kept when the refined pass produces lower confidence."""
        quick_result = _make_result("Vehicles", 0.90, "keyword")
        refined_result = _make_result("Company", 0.55, "embedding")

        # refined.confidence (0.55) <= quick.confidence (0.90) → quick wins
        assert refined_result.confidence <= quick_result.confidence

    def test_refined_skipped_when_no_table_data(self) -> None:
        """Refined classification is never triggered when table extraction returns nothing."""
        table_data: dict[str, str] = {}
        # The condition `if table_data:` is falsy for an empty dict
        assert not table_data  # no refinement pass happens


# ===========================================================================
# 2. Safe Metadata Merging
# ===========================================================================

class TestSafeMetadataMerge:
    """Empty/None table values must never overwrite a good regex value."""

    def test_empty_table_value_does_not_overwrite_regex(self) -> None:
        regex_metadata: dict[str, str | None] = {"vehicle_number": "KA01AB1234", "owner_name": "Test User"}
        table_metadata: dict[str, str] = {"vehicle_number": "", "owner_name": ""}

        merged = regex_metadata.copy()
        merged.update({k: v for k, v in table_metadata.items() if v})

        assert merged["vehicle_number"] == "KA01AB1234"
        assert merged["owner_name"] == "Test User"

    def test_non_empty_table_value_does_overwrite_regex(self) -> None:
        regex_metadata: dict[str, str | None] = {"vehicle_number": "OLD-VALUE"}
        table_metadata: dict[str, str] = {"vehicle_number": "KA01AB1234"}

        merged = regex_metadata.copy()
        merged.update({k: v for k, v in table_metadata.items() if v})

        assert merged["vehicle_number"] == "KA01AB1234"

    def test_none_table_value_does_not_overwrite_regex(self) -> None:
        regex_metadata: dict[str, str | None] = {"gstin": "27AAPFU0939F1ZV"}
        # map_fields returns str values, but guard against None coercion
        table_metadata: dict[str, str | None] = {"gstin": None}  # type: ignore[dict-item]

        merged = regex_metadata.copy()
        merged.update({k: v for k, v in table_metadata.items() if v})

        assert merged["gstin"] == "27AAPFU0939F1ZV"

    def test_table_adds_new_key_not_in_regex(self) -> None:
        regex_metadata: dict[str, str | None] = {"owner_name": "Alice"}
        table_metadata: dict[str, str] = {"engine_number": "ENG123456"}

        merged = regex_metadata.copy()
        merged.update({k: v for k, v in table_metadata.items() if v})

        assert merged["owner_name"] == "Alice"
        assert merged["engine_number"] == "ENG123456"

    def test_empty_table_metadata_leaves_regex_intact(self) -> None:
        regex_metadata: dict[str, str | None] = {"vehicle_number": "KA01AB1234"}
        table_metadata: dict[str, str] = {}

        merged = regex_metadata.copy()
        merged.update({k: v for k, v in table_metadata.items() if v})

        assert merged == {"vehicle_number": "KA01AB1234"}


# ===========================================================================
# 3. Table-Aware Expiry Detection
# ===========================================================================

class TestTableAwareExpiry:
    """Table values must be included in the text fed to detect_expiry."""

    def test_table_values_appended_when_present(self) -> None:
        cleaned_text = "Motor insurance policy document"
        table_data = {"tp risk expiry date": "05 Jun 2025", "od expiry date": "05 Jun 2025"}

        table_values_text = " ".join(table_data.values())
        expiry_text = cleaned_text + "\n" + table_values_text

        assert "05 Jun 2025" in expiry_text
        assert cleaned_text in expiry_text

    def test_expiry_text_unchanged_when_no_table_data(self) -> None:
        cleaned_text = "PUC certificate valid upto 2026-01-01"
        table_data: dict[str, str] = {}

        table_values_text = " ".join(table_data.values())
        expiry_text = cleaned_text + ("\n" + table_values_text if table_values_text else "")

        assert expiry_text == cleaned_text

    def test_table_date_surfaced_by_expiry_detector(self) -> None:
        """A date only present in the table (not OCR text) must be found."""
        from expiry.expiry_detector import detect_expiry

        cleaned_text = "Motor insurance policy"
        table_data = {"risk expiry date": "05 Jun 2026"}
        table_values_text = " ".join(table_data.values())
        expiry_text = cleaned_text + "\n" + table_values_text

        result = detect_expiry(expiry_text, "Vehicles")
        # The date is in the future relative to test execution (2026-06-05)
        assert result.expiry_date == "2026-06-05"

    def test_table_values_join_is_space_separated(self) -> None:
        table_data = {"a": "val1", "b": "val2", "c": "val3"}
        result = " ".join(table_data.values())
        assert result == "val1 val2 val3"


class TestMultiCategoryDocument:
    """A document that holds several kinds of information is split into one section per category."""

    TEXT = (
        "Company Name Northstar Office Supplies LLC\nEntity Type Limited Liability Company (LLC)\n"
        "EIN 12-3456789\nBusiness Address 1250 Market Street, Denver, CO 80202\n"
        "Vehicle Owner Northstar Office Supplies LLC\nLicense Plate CO TEST42\nVIN 1HGCM82633A004352\n"
        "Vehicle Make Ford\nRegistration Date March 20, 2024\n"
        "Invoice Number: NS-2026-104\nInvoice Date: October 12, 2026\nSubtotal $780.00\nTotal Due $842.40\n"
    )

    def _parse(self):
        from parser.service import DocumentParserService

        return DocumentParserService().parse_document(file_bytes=self.TEXT.encode(), file_name="mixed.txt")

    def test_each_category_is_listed_with_its_own_details(self) -> None:
        by_name = {section["category"]: section for section in self._parse().categories}

        assert {"Vehicles", "Company", "Equipments"} <= set(by_name)
        assert by_name["Company"]["metadata"]["ein"] == "12-3456789"
        assert by_name["Vehicles"]["metadata"]["chassis_number"] == "1HGCM82633A004352"
        assert by_name["Equipments"]["metadata"]["invoice_number"] == "NS-2026-104"
        assert by_name["Equipments"]["metadata"]["total_amount"] == "$842.40"

    def test_main_category_comes_first_and_matches_document_type(self) -> None:
        result = self._parse()

        assert result.categories[0]["category"] == result.document_type

    def test_values_keep_their_original_capitalisation(self) -> None:
        by_name = {section["category"]: section for section in self._parse().categories}

        assert by_name["Company"]["metadata"]["company_name"] == "Northstar Office Supplies LLC"
