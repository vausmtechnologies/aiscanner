"""Keyword-based document classifier."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class KeywordClassificationResult:
	"""Represents keyword classification output."""

	document_type: str | None
	confidence: float
	keywords_detected: list[str]
	matched_count: int
	total_keywords: int


class KeywordClassifier:
	"""Classifier that detects document type using configured keyword dictionaries."""

	def __init__(self, keyword_map: dict[str, list[str]] | None = None) -> None:
		self.keyword_map = keyword_map or self._load_keywords()

	def classify(self, cleaned_text: str) -> KeywordClassificationResult:
		"""Classify cleaned text against known category keywords."""
		if not cleaned_text:
			return KeywordClassificationResult(
				document_type=None,
				confidence=0.0,
				keywords_detected=[],
				matched_count=0,
				total_keywords=0,
			)

		best_category: str | None = None
		best_keywords: list[str] = []
		best_confidence = 0.0
		best_total_keywords = 0

		for category, keywords in self.keyword_map.items():
			if not keywords:
				continue

			matched = [keyword for keyword in keywords if keyword in cleaned_text]
			confidence = len(matched) / len(keywords)

			if confidence > best_confidence:
				best_category = category
				best_keywords = matched
				best_confidence = confidence
				best_total_keywords = len(keywords)

		if best_confidence < settings.keyword_min_confidence:
			logger.info(
				"Keyword classification below threshold: score=%.3f threshold=%.3f",
				best_confidence,
				settings.keyword_min_confidence,
			)
			return KeywordClassificationResult(
				document_type=None,
				confidence=best_confidence,
				keywords_detected=best_keywords,
				matched_count=len(best_keywords),
				total_keywords=best_total_keywords,
			)

		return KeywordClassificationResult(
			document_type=best_category,
			confidence=best_confidence,
			keywords_detected=best_keywords,
			matched_count=len(best_keywords),
			total_keywords=best_total_keywords,
		)

	def score_categories(self, cleaned_text: str) -> list[dict[str, object]]:
		"""Return per-category keyword match diagnostics sorted by confidence."""
		if not cleaned_text:
			return []

		scored_categories: list[dict[str, object]] = []
		for category, keywords in self.keyword_map.items():
			if not keywords:
				continue

			matched = [keyword for keyword in keywords if keyword in cleaned_text]
			confidence = len(matched) / len(keywords)
			scored_categories.append(
				{
					"category": category,
					"confidence": round(float(confidence), 4),
					"matched_count": len(matched),
					"total_keywords": len(keywords),
					"keywords_detected": matched,
				}
			)

		return sorted(scored_categories, key=lambda item: float(item["confidence"]), reverse=True)

	@staticmethod
	def _load_keywords() -> dict[str, list[str]]:
		"""Load category keywords from configured JSON file."""
		try:
			with settings.category_keywords_path.open("r", encoding="utf-8") as json_file:
				raw_data = json.load(json_file)
		except FileNotFoundError as exc:
			raise RuntimeError("Keyword file not found") from exc
		except json.JSONDecodeError as exc:
			raise RuntimeError("Keyword file contains invalid JSON") from exc

		keyword_map: dict[str, list[str]] = {}
		for category, keywords in raw_data.items():
			if not isinstance(keywords, list):
				logger.warning("Skipping category '%s' with invalid keyword format", category)
				continue
			keyword_map[category] = [str(item).strip().lower() for item in keywords if str(item).strip()]

		if not keyword_map:
			raise RuntimeError("Keyword file does not define any valid category keywords")

		return keyword_map
