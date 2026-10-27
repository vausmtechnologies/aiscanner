"""Text normalization utilities for OCR output."""

from __future__ import annotations

import re


_NON_WORD_PATTERN = re.compile(r"[^a-z0-9\s]")
_WHITESPACE_PATTERN = re.compile(r"\s+")


def clean_text(raw_text: str) -> str:
	"""Normalize OCR text for downstream classification.

	Steps:
	- lowercase
	- remove special characters
	- collapse duplicate whitespace
	"""
	if not raw_text:
		return ""

	normalized = raw_text.lower()
	normalized = _NON_WORD_PATTERN.sub(" ", normalized)
	normalized = _WHITESPACE_PATTERN.sub(" ", normalized).strip()
	return normalized


_INLINE_SPACE_PATTERN = re.compile(r"[ \t\u00a0]+")
_BLANK_LINES_PATTERN = re.compile(r"\n\s*\n+")


def normalize_text(raw_text: str) -> str:
	"""Tidy OCR text for the metadata extractors: keeps case and line breaks, collapses extra spaces."""
	if not raw_text:
		return ""

	normalized = raw_text.replace("\r", "\n")
	normalized = _INLINE_SPACE_PATTERN.sub(" ", normalized)
	normalized = _BLANK_LINES_PATTERN.sub("\n", normalized)
	return normalized.strip()
