"""Top-level expiry detection engine.

Pipeline:
  1. For Vehicles — check "To DATE" period pattern first (insurance policy end).
  2. Context-aware expiry candidates (dates near expiry / valid-until / valid-thru).
  3. If context candidates exist → choose latest future date among them.
     If none are future → choose latest context candidate overall.
  4. Fallback → latest future date from all dates extracted in the document.
  5. Start date from valid-from / period-from phrases (never later than expiry).
  6. Compute days_remaining and status from the expiry date.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date

from expiry.date_extractor import extract_dates
from expiry.expiry_context import detect_expiry_context, detect_start_context

logger = logging.getLogger(__name__)

_EXPIRING_SOON_DAYS = 30


@dataclass(frozen=True)
class ExpiryResult:
    """Structured expiry detection result."""

    expiry_date: str | None       # ISO YYYY-MM-DD or None
    days_remaining: int | None    # negative if expired
    status: str                   # "valid" | "expiring_soon" | "expired" | "unknown"
    start_date: str | None = None  # ISO YYYY-MM-DD from valid from / valid start


def detect_expiry(text: str, category: str | None = None) -> ExpiryResult:
    """Detect start-of-validity and expiry dates in *text*.

    Args:
        text:     Document text (prefer raw extracted text so date separators survive).
        category: Document category for context-aware keyword matching.

    Returns:
        ExpiryResult with start_date, expiry_date, days_remaining, and status.
    """
    today = date.today()

    context_dates = detect_expiry_context(text, category)
    start_dates = detect_start_context(text, category)
    all_dates = extract_dates(text)

    logger.debug(
        "Expiry detection: start_dates=%s context_dates=%s all_dates=%s",
        start_dates, context_dates, all_dates,
    )

    expiry: date | None = None
    if context_dates:
        future = [d for d in context_dates if d >= today]
        expiry = max(future) if future else max(context_dates)
    elif all_dates:
        future = [d for d in all_dates if d > today]
        expiry = max(future) if future else None

    start: date | None = None
    if start_dates:
        if expiry:
            before_or_on = [d for d in start_dates if d <= expiry]
            start = max(before_or_on) if before_or_on else min(start_dates)
        else:
            start = max(start_dates)

    if expiry is None and start is None:
        return ExpiryResult(
            expiry_date=None, days_remaining=None, status="unknown", start_date=None
        )

    days_remaining: int | None = None
    status = "unknown"
    if expiry is not None:
        days_remaining = (expiry - today).days
        if days_remaining < 0:
            status = "expired"
        elif days_remaining <= _EXPIRING_SOON_DAYS:
            status = "expiring_soon"
        else:
            status = "valid"

    return ExpiryResult(
        expiry_date=expiry.isoformat() if expiry else None,
        days_remaining=days_remaining,
        status=status,
        start_date=start.isoformat() if start else None,
    )
