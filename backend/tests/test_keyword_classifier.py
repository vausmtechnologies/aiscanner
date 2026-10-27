from pathlib import Path

from classification.hybrid_classifier import HybridClassifier
from classification.keyword_classifier import KeywordClassifier
from parser.text_cleaner import clean_text


FIXTURE_EXPECTED = {
    "vehicle_rc.txt": "Vehicles",
    "employee_id.txt": "People",
    "equipment_invoice.txt": "Equipments",
    "company_certificate.txt": "Company",
    "company_gst_certificate.txt": "Company",
    "uk_driving_licence.txt": "People",
}


def _load_fixture_text(file_name: str) -> str:
    fixture_path = Path(__file__).parent / "fixtures" / file_name
    return fixture_path.read_text(encoding="utf-8")


def test_hybrid_classifier_detects_expected_category() -> None:
    classifier = HybridClassifier()

    for fixture_file, expected_category in FIXTURE_EXPECTED.items():
        cleaned = clean_text(_load_fixture_text(fixture_file))
        result = classifier.classify_document(cleaned)

        assert result.document_type == expected_category, (
            f"{fixture_file}: expected={expected_category} "
            f"got={result.document_type} method={result.method} conf={result.confidence}"
        )
        assert result.confidence > 0.0
        assert result.method in {"keyword", "embedding"}


PAT_LOG_SHEET_TEXT = """
EQUIPMENT UNIQUE NUMBER EQUIPMENT DESCRIPTION EQUIPMENT CLASS FUSE SIZE
SERIAL NUMBER I II ELV
EARTH CONTINUITY INSULATION RESISTANCE POLARITY CURRENT LEAKAGE FUNCTION OVERALL RESULT
PASS FAIL
Log Sheet Control Sheet Number : Test Date : Inspector :
Remove old PAT Test labels before applying the new label
Failed Equipment EQUIPMENT DESCRIPTION VISUAL INSPECTION
Log Sheet - Priory - 2023 - Type 1
"""


def test_hybrid_classifier_detects_pat_log_sheet_as_equipments() -> None:
    classifier = HybridClassifier()
    result = classifier.classify_document(clean_text(PAT_LOG_SHEET_TEXT))
    assert result.document_type == "Equipments"
    assert result.confidence > 0.0
    assert result.method in {"keyword", "embedding"}


def test_pat_report_is_equipments_document() -> None:
    classifier = HybridClassifier()
    result = classifier.classify_document(clean_text("PAT Report for site appliances"))
    assert result.document_type == "Equipments"
    assert "pat report" in result.keywords_detected


def test_pat_test_phrase_is_equipments_document() -> None:
    classifier = HybridClassifier()
    result = classifier.classify_document(clean_text("This PAT test was completed on site"))
    assert result.document_type == "Equipments"
    assert "pat test" in result.keywords_detected


def test_filename_hint_matches_pat_report() -> None:
    from parser.service import DocumentParserService

    category, confidence = DocumentParserService._classify_from_filename("PAT-Report-Site-A.pdf")
    assert category == "Equipments"
    assert confidence > 0.0


def test_filename_hint_matches_priory_log_sheet() -> None:
    from parser.service import DocumentParserService

    category, confidence = DocumentParserService._classify_from_filename(
        "Log-Sheet-Priory-2023-Type-5.pdf"
    )
    assert category == "Equipments"
    assert confidence > 0.0


def test_hybrid_classifier_accuracy_above_80_percent() -> None:
    classifier = HybridClassifier()
    total = len(FIXTURE_EXPECTED)
    correct = 0

    for fixture_file, expected_category in FIXTURE_EXPECTED.items():
        cleaned = clean_text(_load_fixture_text(fixture_file))
        result = classifier.classify_document(cleaned)
        if result.document_type == expected_category:
            correct += 1

    accuracy = correct / total
    assert accuracy >= 0.8


def test_keyword_must_match_a_whole_word() -> None:
    classifier = KeywordClassifier(keyword_map={"Vehicles": ["rto", "registration date"]})
    result = classifier.classify("copy paper cartons registration date")
    assert result.keywords_detected == ["registration date"]
