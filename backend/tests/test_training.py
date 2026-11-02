"""Tests for UI-driven category training."""

import pytest

from classification.dynamic_categories import DynamicCategoryStore
from classification.hybrid_classifier import HybridClassifier
from classification.trained_categories import TrainedCategoryStore, mine_keywords, normalise_name
from metadata.metadata_router import extract_metadata
from parser.service import DocumentParserService
from parser.text_cleaner import clean_text

PRESCRIPTIONS = [
    "Medical Prescription\nPatient: John Doe\nDoctor prescribed amoxicillin tablets twice daily. Pharmacy dispense dosage instructions.",
    "Medical Prescription\nPatient: Jane Roe\nDoctor prescribed paracetamol tablets thrice daily. Pharmacy dispense dosage instructions.",
    "Medical Prescription\nPatient: Sam Lee\nDoctor prescribed ibuprofen tablets daily. Pharmacy dispense dosage instructions.",
]


@pytest.fixture
def service(tmp_path):
    svc = DocumentParserService()
    store = TrainedCategoryStore(path=tmp_path / "trained.json")
    svc.hybrid_classifier.trained_store = store
    svc.hybrid_classifier.reload_trained()
    svc.dynamic_categories = DynamicCategoryStore(path=tmp_path / "dyn.json")
    return svc


def _files(texts):
    return [(text.encode(), f"rx{i}.txt") for i, text in enumerate(texts)]


def test_mine_keywords_prefers_distinctive_terms():
    own = [clean_text(t) for t in PRESCRIPTIONS]
    others = [clean_text("vehicle registration number engine chassis owner"), clean_text("company certificate gst tax")]
    keywords = mine_keywords(own, others)
    assert any("prescription" in k or "pharmacy" in k or "dosage" in k for k in keywords)
    assert "vehicle" not in keywords


def test_name_validation():
    assert normalise_name("  Medical   Prescription ") == "Medical Prescription"
    with pytest.raises(ValueError):
        normalise_name("<script>")


def test_trained_category_is_used_immediately(service):
    clean = clean_text(PRESCRIPTIONS[0])
    assert service.hybrid_classifier.classify_document(clean).document_type != "Medical Prescription"

    result = service.train_category("Medical Prescription", _files(PRESCRIPTIONS))

    assert result["trained_documents"] == 3
    assert result["details"]["trained_keywords"]
    outcome = service.hybrid_classifier.classify_document(clean_text("Medical Prescription Patient: Ann Doctor prescribed aspirin tablets. Pharmacy dispense dosage instructions."))
    assert outcome.document_type == "Medical Prescription"


def test_other_process_sees_training_without_restart(service, tmp_path):
    other = HybridClassifier()
    other.trained_store = TrainedCategoryStore(path=tmp_path / "trained.json")
    other.reload_trained()
    service.train_category("Medical Prescription", _files(PRESCRIPTIONS))
    text = clean_text("Medical Prescription Patient Doctor prescribed tablets. Pharmacy dispense dosage instructions.")
    assert other.classify_document(text).document_type == "Medical Prescription"


def test_unreadable_files_are_reported(service):
    result = service.train_category("Medical Prescription", [(b"hi", "tiny.txt"), (b"x", "bad.exe")])
    assert result["trained_documents"] == 0
    assert [f["ok"] for f in result["files"]] == [False, False]


def test_training_existing_category_keeps_its_name_and_defaults(service):
    result = service.train_category("vehicles", _files(["Vehicle Registration Certificate\nRegistration No: MH12AB1234\nChassis number engine number owner name"]))
    assert result["category"] == "Vehicles"
    assert result["details"]["kind"] == "built-in"
    assert len(result["details"]["keywords"]) > len(result["details"]["trained_keywords"])


def test_delete_and_list(service):
    service.train_category("Medical Prescription", _files(PRESCRIPTIONS))
    assert any(c["name"] == "Medical Prescription" and c["kind"] == "trained" for c in service.list_categories())
    assert service.delete_category("Medical Prescription")
    assert not any(c["name"] == "Medical Prescription" for c in service.list_categories())
    assert not service.delete_category("Medical Prescription")


def test_promote_auto_category(service):
    text = "Residential Lease Agreement\nThe landlord leases the apartment to the tenant for twelve months at monthly rent."
    service.dynamic_categories.assign(clean_text(text), text, "lease.pdf")
    auto_name = service.dynamic_categories.names()[0]

    details = service.promote_auto_category(auto_name, "Lease")

    assert details["name"] == "Lease" and details["kind"] == "trained"
    assert service.dynamic_categories.names() == []


def test_generic_metadata_for_trained_category():
    meta = extract_metadata("Medical Prescription", "Patient: John Doe\nDoctor: Dr. Smith\nsome free text")
    assert meta == {"patient": "John Doe", "doctor": "Dr. Smith"}
