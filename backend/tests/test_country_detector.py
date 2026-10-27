"""Tests for country_detector.py — Step 7 of global classifier spec."""

from __future__ import annotations

import pytest

from classification.country_detector import detect_country


# ---------------------------------------------------------------------------
# India
# ---------------------------------------------------------------------------

def test_india_gstin() -> None:
    assert detect_country("GSTIN 27AAPFU0939F1ZV taxpayer details") == "India"

def test_india_aadhaar() -> None:
    assert detect_country("aadhaar card uidai resident name date of birth") == "India"

def test_india_pan() -> None:
    assert detect_country("PAN card permanent account number income tax department") == "India"

def test_india_rc_book() -> None:
    assert detect_country("rc book vehicle registration rto authority") == "India"

def test_india_puc() -> None:
    assert detect_country("pollution under control puc certificate valid vehicle") == "India"

def test_india_mcafairs() -> None:
    assert detect_country("certificate of incorporation ministry of corporate affairs cin") == "India"


# ---------------------------------------------------------------------------
# UK
# ---------------------------------------------------------------------------

def test_uk_dvla() -> None:
    assert detect_country("dvla v5c logbook registered keeper uk vehicle") == "UK"

def test_uk_mot() -> None:
    assert detect_country("mot certificate ministry of transport pass vehicle uk") == "UK"

def test_uk_hmrc() -> None:
    assert detect_country("hmrc value added tax registration number uk business") == "UK"

def test_uk_national_insurance() -> None:
    assert detect_country("national insurance number hmrc ni contributions uk") == "UK"

def test_uk_companies_house() -> None:
    assert detect_country("companies house certificate of incorporation registered in england") == "UK"

def test_uk_nhs() -> None:
    assert detect_country("nhs medical card national health service patient gp uk") == "UK"


# ---------------------------------------------------------------------------
# US
# ---------------------------------------------------------------------------

def test_us_ein() -> None:
    assert detect_country("employer identification number irs letter federal tax") == "US"

def test_us_ssn() -> None:
    assert detect_country("social security card ssn united states of america") == "US"

def test_us_dmv() -> None:
    assert detect_country("dmv vehicle registration california department of motor vehicles") == "US"

def test_us_irs() -> None:
    assert detect_country("internal revenue service ein tax identification us") == "US"

def test_us_passport() -> None:
    assert detect_country("u.s. passport united states of america holder name") == "US"

def test_us_uscis() -> None:
    assert detect_country("uscis permanent resident card green card expiry holder") == "US"


# ---------------------------------------------------------------------------
# EU
# ---------------------------------------------------------------------------

def test_eu_vat_number() -> None:
    assert detect_country("vat number intra-community supply goods services eu") == "EU"

def test_eu_handelsregister() -> None:
    assert detect_country("handelsregister amtsgericht germany commercial register") == "EU"

def test_eu_kvk() -> None:
    assert detect_country("kvk kamer van koophandel netherlands chamber of commerce") == "EU"

def test_eu_tüv() -> None:
    assert detect_country("tüv hauptuntersuchung vehicle inspection pass german") == "EU"

def test_eu_ehic() -> None:
    assert detect_country("european health insurance card ehic member state holder") == "EU"

def test_eu_zulassung() -> None:
    assert detect_country("zulassungsbescheinigung german vehicle registration fahrzeughalter") == "EU"


# ---------------------------------------------------------------------------
# None / ambiguous
# ---------------------------------------------------------------------------

def test_no_country_empty_text() -> None:
    assert detect_country("") is None

def test_no_country_generic_text() -> None:
    assert detect_country("some generic document with no regional markers") is None


# ---------------------------------------------------------------------------
# Priority: India wins over EU when both signals present
# ---------------------------------------------------------------------------

def test_india_priority_over_eu() -> None:
    # Both "gstin" (India) and "vat number" (EU) present — India detected first
    text = "gstin registration certificate vat number mentioned"
    assert detect_country(text) == "India"

def test_uk_priority_over_us() -> None:
    # "dvla" (UK) and "dmv" (US) both present — UK detected first
    text = "dvla vehicle document dmv registration mentioned"
    assert detect_country(text) == "UK"


def test_signal_inside_a_longer_word_is_not_a_match() -> None:
    # "rto" hides inside "cartons"; it must not make the document Indian.
    assert detect_country("copy paper cartons and printer toner") is None


def test_india_government_of_india_and_rupee_amounts() -> None:
    assert detect_country("Government of India registration certificate") == "India"
    assert detect_country("Sum insured (INR) 500000") == "India"
