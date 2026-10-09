"""Tests for the expiry detection engine: date_extractor, expiry_context, expiry_detector."""

from __future__ import annotations

import time
from datetime import date, timedelta

import pytest

from expiry.date_extractor import extract_dates
from expiry.expiry_context import detect_expiry_context, detect_start_context
from expiry.expiry_detector import detect_expiry

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TODAY = date.today()
_FUTURE_1 = (_TODAY + timedelta(days=400)).isoformat()   # well in the future
_FUTURE_2 = (_TODAY + timedelta(days=600)).isoformat()   # even further
_SOON     = (_TODAY + timedelta(days=15)).isoformat()    # expiring soon
_PAST     = (_TODAY - timedelta(days=10)).isoformat()    # expired


# ---------------------------------------------------------------------------
# date_extractor
# ---------------------------------------------------------------------------

def test_iso_date_extracted() -> None:
    dates = extract_dates(f"Registration date {_FUTURE_1} issued today")
    assert date.fromisoformat(_FUTURE_1) in dates


def test_dd_slash_mm_yyyy_extracted() -> None:
    dates = extract_dates("Valid until 09/05/2028")
    assert date(2028, 5, 9) in dates


def test_dd_dash_mm_yyyy_extracted() -> None:
    dates = extract_dates("Expiry 09-05-2028")
    assert date(2028, 5, 9) in dates


def test_dd_month_yyyy_extracted() -> None:
    dates = extract_dates("Valid till 15 June 2029")
    assert date(2029, 6, 15) in dates


def test_month_dd_yyyy_extracted() -> None:
    dates = extract_dates("Expires on June 15 2029")
    assert date(2029, 6, 15) in dates


def test_invalid_date_skipped() -> None:
    dates = extract_dates("Ref no 99-99-9999 and some text")
    assert not any(d.year == 9999 for d in dates)


def test_duplicate_dates_deduplicated() -> None:
    text = f"Date: {_FUTURE_1}. Also recorded: {_FUTURE_1}."
    dates = extract_dates(text)
    assert dates.count(date.fromisoformat(_FUTURE_1)) == 1


def test_multiple_dates_returned_sorted() -> None:
    dates = extract_dates(f"Start {_PAST}. End {_FUTURE_1}.")
    assert dates == sorted(dates)


# ---------------------------------------------------------------------------
# expiry_context
# ---------------------------------------------------------------------------

def test_context_detects_valid_until() -> None:
    text = f"Insurance valid until {_FUTURE_1}"
    result = detect_expiry_context(text)
    assert date.fromisoformat(_FUTURE_1) in result


def test_context_detects_expires_on() -> None:
    text = f"Policy expires on {_FUTURE_1}"
    result = detect_expiry_context(text)
    assert date.fromisoformat(_FUTURE_1) in result


def test_context_detects_fitness_valid_till() -> None:
    text = f"Fitness valid till {_FUTURE_2}"
    result = detect_expiry_context(text, category="Vehicles")
    assert date.fromisoformat(_FUTURE_2) in result


def test_context_detects_amc_expiry() -> None:
    text = f"AMC expiry {_FUTURE_1}"
    result = detect_expiry_context(text, category="Equipments")
    assert date.fromisoformat(_FUTURE_1) in result


def test_context_detects_passport_expiry() -> None:
    text = f"Passport expiry {_FUTURE_1}"
    result = detect_expiry_context(text, category="People")
    assert date.fromisoformat(_FUTURE_1) in result


def test_context_returns_empty_when_no_keywords() -> None:
    result = detect_expiry_context("Some random text without keywords")
    assert result == []


# ---------------------------------------------------------------------------
# expiry_detector – status and date selection
# ---------------------------------------------------------------------------

RC_TEXT = (
    f"Vehicle registration certificate  "
    f"Registration date {_PAST}  "
    f"Insurance valid until {_FUTURE_1}  "
    f"Fitness certificate valid till {_FUTURE_2}"
)


def test_detect_expiry_chooses_latest_future_date() -> None:
    result = detect_expiry(RC_TEXT, category="Vehicles")
    assert result.expiry_date == _FUTURE_2


def test_detect_expiry_status_valid() -> None:
    text = f"Valid until {_FUTURE_1}"
    result = detect_expiry(text)
    assert result.status == "valid"
    assert result.days_remaining is not None
    assert result.days_remaining > _TODAY_PLUS_30


def test_detect_expiry_status_expiring_soon() -> None:
    text = f"Valid until {_SOON}"
    result = detect_expiry(text)
    assert result.status == "expiring_soon"
    assert 0 <= result.days_remaining <= 30


def test_detect_expiry_status_expired() -> None:
    text = f"Policy expires on {_PAST}"
    result = detect_expiry(text)
    assert result.status == "expired"
    assert result.days_remaining < 0


def test_detect_expiry_unknown_when_no_dates() -> None:
    result = detect_expiry("some document with no dates at all")
    assert result.status == "unknown"
    assert result.expiry_date is None
    assert result.days_remaining is None


def test_detect_expiry_days_remaining_correct() -> None:
    future = _TODAY + timedelta(days=100)
    text = f"AMC expiry {future.isoformat()}"
    result = detect_expiry(text, category="Equipments")
    assert result.expiry_date == future.isoformat()
    assert result.days_remaining == 100


# GST / Company
def test_detect_expiry_company_license() -> None:
    text = f"License valid until {_FUTURE_1}"
    result = detect_expiry(text, category="Company")
    assert result.expiry_date == _FUTURE_1
    assert result.status == "valid"


# Passport
def test_detect_expiry_passport() -> None:
    text = f"Passport expiry {_FUTURE_1}"
    result = detect_expiry(text, category="People")
    assert result.expiry_date == _FUTURE_1


# Invoice / warranty
def test_detect_expiry_warranty() -> None:
    text = f"Warranty expiry {_FUTURE_1}"
    result = detect_expiry(text, category="Equipments")
    assert result.expiry_date == _FUTURE_1


def test_context_detects_valid_from_as_start() -> None:
    text = f"Policy Valid From {_PAST} Valid Till {_FUTURE_1}"
    starts = detect_start_context(text)
    assert date.fromisoformat(_PAST) in starts


def test_detect_expiry_valid_from_and_valid_thru() -> None:
    text = "Certificate Valid From 01/03/2024 Valid Thru 01/03/2027"
    result = detect_expiry(text, category="Equipments")
    assert result.start_date == "2024-03-01"
    assert result.expiry_date == "2027-03-01"
    assert result.status == "valid"


def test_detect_expiry_valid_up_to() -> None:
    text = "AMC valid up to 15 June 2029"
    result = detect_expiry(text, category="Equipments")
    assert result.expiry_date == "2029-06-15"


def test_detect_expiry_expiration_date() -> None:
    text = "Expiration date 10-Mar-2027"
    result = detect_expiry(text)
    assert result.expiry_date == "2027-03-10"


def test_detect_expiry_start_only_leaves_status_unknown() -> None:
    text = f"Valid From {_PAST}"
    result = detect_expiry(text)
    assert result.start_date == _PAST
    assert result.expiry_date is None
    assert result.status == "unknown"


def test_start_date_not_after_expiry() -> None:
    text = f"Valid From {_PAST} Valid From {_FUTURE_1} Valid Till {_FUTURE_2}"
    result = detect_expiry(text)
    assert result.expiry_date == _FUTURE_2
    assert result.start_date == _FUTURE_1
    assert date.fromisoformat(result.start_date) <= date.fromisoformat(result.expiry_date)


# ---------------------------------------------------------------------------
# New format: DD-MMM-YYYY  (insurance / vehicle documents)
# ---------------------------------------------------------------------------

def test_dd_mmm_yyyy_extracted() -> None:
    dates = extract_dates("Policy period 06-JUN-2024 To 05-JUN-2025")
    assert date(2025, 6, 5) in dates
    assert date(2024, 6, 6) in dates


def test_dd_mmm_yyyy_lowercase_extracted() -> None:
    dates = extract_dates("Risk expiry date 10-Mar-2027")
    assert date(2027, 3, 10) in dates


def test_period_to_pattern_extracts_end_date() -> None:
    """'To DD-MMM-YYYY' must be detected as an expiry context candidate."""
    text = "Period of Own Damage : 06-JUN-2024 To 05-JUN-2025"
    result = detect_expiry_context(text, category="Vehicles")
    assert date(2025, 6, 5) in result


def test_normalize_date_dd_mmm_yyyy() -> None:
    from expiry.date_extractor import normalize_date
    assert normalize_date("05-JUN-2025") == "2025-06-05"
    assert normalize_date("10-Mar-2027") == "2027-03-10"


# ---------------------------------------------------------------------------
# Spec example test cases
# ---------------------------------------------------------------------------

def test_spec_example_1_period_of_own_damage() -> None:
    """Period of Own Damage : 06-JUN-2024 To 05-JUN-2025 → start 2024-06-06, expiry 2025-06-05."""
    text = "Period of Own Damage : 06-JUN-2024 To 05-JUN-2025"
    result = detect_expiry(text, category="Vehicles")
    assert result.start_date == "2024-06-06"
    assert result.expiry_date == "2025-06-05"


def test_spec_example_2_valid_till() -> None:
    """Policy Valid From 01/01/2024 Valid Till 01/01/2026 → start 2024-01-01, expiry 2026-01-01."""
    text = "Policy Valid From 01/01/2024 Valid Till 01/01/2026"
    result = detect_expiry(text, category="Vehicles")
    assert result.start_date == "2024-01-01"
    assert result.expiry_date == "2026-01-01"


def test_spec_example_3_risk_expiry_date() -> None:
    """Insurance Risk Expiry Date 10-Mar-2027 → expiry 2027-03-10."""
    text = "Insurance Risk Expiry Date 10-Mar-2027"
    result = detect_expiry(text, category="Vehicles")
    assert result.expiry_date == "2027-03-10"


# ---------------------------------------------------------------------------
# Performance: must run in < 10 ms
# ---------------------------------------------------------------------------

def test_detect_expiry_under_10ms() -> None:
    text = (
        f"Vehicle registration certificate  "
        f"Registration date {_PAST}  "
        f"Insurance valid until {_FUTURE_1}  "
        f"Fitness certificate valid till {_FUTURE_2}"
    )
    start = time.perf_counter()
    detect_expiry(text, category="Vehicles")
    elapsed_ms = (time.perf_counter() - start) * 1000
    assert elapsed_ms < 10, f"detect_expiry took {elapsed_ms:.2f} ms (limit 10 ms)"


# ---------------------------------------------------------------------------
# Module-level constant needed by one assertion above
# ---------------------------------------------------------------------------

_TODAY_PLUS_30 = 30
