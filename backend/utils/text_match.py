"""Whole-word term matching shared by the classifiers."""

from __future__ import annotations

import re
from functools import lru_cache


@lru_cache(maxsize=None)
def _term_pattern(term: str) -> re.Pattern[str]:
	return re.compile(r"(?<!\w)" + re.escape(term.strip()) + r"(?!\w)")


def contains_term(text: str, term: str) -> bool:
	"""Return True if *term* appears in *text* as a whole word/phrase (so "rto" does not match "cartons")."""
	return _term_pattern(term).search(text) is not None
