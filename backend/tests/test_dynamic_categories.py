"""Tests for automatic category creation."""

import json

from classification.dynamic_categories import DynamicCategoryStore, _derive_name

MEDICAL = "Medical Prescription\nPatient: John Doe\nDoctor prescribed amoxicillin tablets twice daily for infection treatment."
MEDICAL_2 = "Medical Prescription\nPatient: Jane Roe\nDoctor prescribed paracetamol tablets thrice daily for fever treatment."
LEASE = "Residential Lease Agreement\nThe landlord leases the apartment to the tenant for twelve months at monthly rent."


def test_new_category_created_then_reused(tmp_path):
    store = DynamicCategoryStore(path=tmp_path / "dyn.json")

    first = store.assign(MEDICAL.lower(), MEDICAL, "a.pdf")
    second = store.assign(MEDICAL_2.lower(), MEDICAL_2, "b.pdf")

    assert first.created and first.category == "Medical Prescription"
    assert not second.created and second.category == first.category
    assert json.loads((tmp_path / "dyn.json").read_text())[first.category]["count"] == 2


def test_different_document_gets_own_category(tmp_path):
    store = DynamicCategoryStore(path=tmp_path / "dyn.json")
    store.assign(MEDICAL.lower(), MEDICAL, "a.pdf")
    lease = store.assign(LEASE.lower(), LEASE, "c.pdf")

    assert lease.created and lease.category == "Residential Lease Agreement"
    assert len(store.names()) == 2


def test_too_little_text_is_not_categorised(tmp_path):
    assert DynamicCategoryStore(path=tmp_path / "dyn.json").assign("hi", "hi", "x.pdf") is None


def test_name_falls_back_to_filename():
    assert _derive_name("1234 5678 ###", "gas_safety-cert.pdf") == "Gas Safety Cert"
