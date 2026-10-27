"""Hybrid document classification: keyword count scoring + embedding similarity fallback.

Pipeline:
  1. keyword_score per category (raw count, not ratio)
  2. If best count >= KEYWORD_COUNT_THRESHOLD → return with method="keyword"
  3. If text contains PAT test/report phrases → Equipments (single-phrase rule)
  4. Otherwise → cosine similarity against precomputed category embeddings → method="embedding"

Category embeddings are precomputed at initialisation so per-request latency is minimal.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.config import settings
from classification.keyword_classifier import KeywordClassifier
from classification.similarity_classifier import SimilarityClassifier
from utils.text_match import contains_term

logger = logging.getLogger(__name__)

KEYWORD_COUNT_THRESHOLD = 2

# A single PAT phrase is enough to treat the file as an equipment document.
PAT_EQUIPMENT_PHRASES: tuple[str, ...] = (
    "pat test",
    "pat report",
    "pat testing",
    "pat certificate",
    "portable appliance test",
    "portable appliance testing",
)


@dataclass(frozen=True)
class HybridClassificationResult:
    """Result produced by the hybrid classification engine."""

    document_type: str | None
    confidence: float
    method: str  # "keyword" | "embedding" | "none"
    keywords_detected: list[str]


def keyword_score(text: str, keywords: list[str]) -> int:
    """Count how many of the given keywords appear in text."""
    return sum(1 for kw in keywords if contains_term(text, kw))


class HybridClassifier:
    """Classifies documents using keyword count first, then embedding similarity.

    Embedding model and category embeddings are precomputed on __init__ so
    classify_document() runs well within the 200 ms per-document target.
    """

    def __init__(self) -> None:
        self.keyword_classifier = KeywordClassifier()
        self.similarity_classifier = SimilarityClassifier()  # precomputes embeddings here
        logger.info("HybridClassifier ready (category embeddings precomputed)")

    def classify_document(self, cleaned_text: str) -> HybridClassificationResult:
        """Run hybrid pipeline and return structured classification result."""
        category, count, matched = self._classify_by_keywords(cleaned_text)

        if count >= KEYWORD_COUNT_THRESHOLD:
            total = len(self.keyword_classifier.keyword_map.get(category, []) or [1])
            confidence = round(min(1.0, count / max(total, 1)), 4)
            return HybridClassificationResult(
                document_type=category,
                confidence=confidence,
                method="keyword",
                keywords_detected=matched,
            )

        pat_hits = [phrase for phrase in PAT_EQUIPMENT_PHRASES if contains_term(cleaned_text, phrase)]
        if pat_hits:
            keywords = list(dict.fromkeys([*matched, *pat_hits]))
            return HybridClassificationResult(
                document_type="Equipments",
                confidence=settings.filename_hint_min_confidence,
                method="keyword",
                keywords_detected=keywords,
            )

        sim_result = self._classify_by_embedding(cleaned_text)
        return HybridClassificationResult(
            document_type=sim_result.document_type,
            confidence=round(float(sim_result.confidence), 4),
            method="embedding" if sim_result.document_type else "none",
            keywords_detected=matched,
        )

    def matching_categories(self, cleaned_text: str) -> list[tuple[str, float, list[str]]]:
        """Return (category, confidence, matched_keywords) for every category with enough keyword hits, best first."""
        found: list[tuple[str, int, float, list[str]]] = []
        for category, keywords in self.keyword_classifier.keyword_map.items():
            matched = [kw for kw in keywords if contains_term(cleaned_text, kw)]
            if len(matched) >= KEYWORD_COUNT_THRESHOLD:
                found.append((category, len(matched), round(min(1.0, len(matched) / len(keywords)), 4), matched))
        found.sort(key=lambda item: item[1], reverse=True)
        return [(category, confidence, matched) for category, _, confidence, matched in found]

    def _classify_by_keywords(self, cleaned_text: str) -> tuple[str | None, int, list[str]]:
        """Return (best_category, best_count, matched_keywords) using raw count scoring."""
        if not cleaned_text:
            return None, 0, []

        best_category: str | None = None
        best_count = 0
        best_matched: list[str] = []

        for category, keywords in self.keyword_classifier.keyword_map.items():
            if not keywords:
                continue
            count = keyword_score(cleaned_text, keywords)
            if count > best_count:
                best_category = category
                best_count = count
                best_matched = [kw for kw in keywords if contains_term(cleaned_text, kw)]

        logger.debug(
            "Keyword scores: best=%s count=%d threshold=%d",
            best_category,
            best_count,
            KEYWORD_COUNT_THRESHOLD,
        )
        return best_category, best_count, best_matched

    def _classify_by_embedding(self, cleaned_text: str):
        """Delegate to embedding similarity classifier."""
        return self.similarity_classifier.classify(cleaned_text)
