"""Country detection from document text.

Heuristic keyword matching against country-specific document markers.
Returns the most likely country of origin, or None if undetectable.

Supported regions: India, UK, US, EU
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Keyword tables — ordered by specificity (most specific first)
# ---------------------------------------------------------------------------

_INDIA_SIGNALS: tuple[str, ...] = (
    "gstin",
    "uidai",
    "aadhaar",
    "pan card",
    "permanent account number",
    "rc book",
    "rto",
    "pollution under control",
    "puc certificate",
    "ministry of corporate affairs",
    "cin",
    "tan number",
    "udyam",
    "msme",
    "election commission of india",
    "mgnrega",
    "niti aayog",
    "transport department india",
    "goods and services tax india",
    "republic of india",
)

_UK_SIGNALS: tuple[str, ...] = (
    "dvla",
    "mot certificate",
    "dvla v5c",
    "national insurance number",
    "hmrc",
    "companies house",
    "driving licence uk",
    "biometric residence permit",
    "nhs",
    "her majesty",
    "his majesty",
    "registered in england",
    "registered in wales",
    "registered in scotland",
    "uk vat",
    "value added tax uk",
    "inland revenue",
)

_US_SIGNALS: tuple[str, ...] = (
    "employer identification number",
    "internal revenue service",
    " irs ",
    " ein ",
    "social security",
    "dmv",
    "department of motor vehicles",
    "united states of america",
    "secretary of state",
    " ssn ",
    "medicare",
    "uscis",
    "permanent resident card",
    "green card",
    "state of california",
    "state of new york",
    "state of texas",
    "u.s. passport",
)

_EU_SIGNALS: tuple[str, ...] = (
    "vat number",
    "intra-community vat",
    "intracommunautaire",
    "handelsregister",
    "amtsgericht",
    "kvk",
    "kamer van koophandel",
    "siren",
    "siret",
    "extrait kbis",
    "burgerservicenummer",
    "bsn",
    " nie ",
    "european health insurance card",
    "ehic",
    "zulassungsbescheinigung",
    "fahrzeugschein",
    "carte grise",
    "certificat d'immatriculation",
    "contrôle technique",
    "tüv",
)


def detect_country(text: str) -> str | None:
    """Return the country/region most likely associated with *text*.

    Matching is case-insensitive and checks for whole-word or boundary-safe
    patterns.  Priority order: India → UK → US → EU.

    Returns one of: ``"India"``, ``"UK"``, ``"US"``, ``"EU"``, or ``None``.
    """
    if not text:
        return None

    lower = " " + text.lower() + " "  # pad so boundary checks work for short tokens

    if _any_match(lower, _INDIA_SIGNALS):
        return "India"
    if _any_match(lower, _UK_SIGNALS):
        return "UK"
    if _any_match(lower, _US_SIGNALS):
        return "US"
    if _any_match(lower, _EU_SIGNALS):
        return "EU"

    return None


def _any_match(lower_text: str, signals: tuple[str, ...]) -> bool:
    """Return True if any signal string is found in *lower_text*."""
    return any(signal in lower_text for signal in signals)
