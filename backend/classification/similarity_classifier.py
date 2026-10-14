"""Embedding similarity classifier fallback.

Uses per-category precomputed embeddings from the global training dataset.
Classification is by max cosine similarity against each category's sample pool,
matching the architecture in Step 3–5 of the global classifier spec.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from app.config import settings
from models.embeddings import embed_texts

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SimilarityClassificationResult:
	"""Represents fallback similarity classification output."""

	document_type: str | None
	confidence: float


class SimilarityClassifier:
	"""Classifier using per-category embedding pools from global training data.

	At init: encodes all training samples per category and caches them.
	At classify time: takes the max cosine similarity across each category's
	pool, then returns the best category above the confidence threshold.
	"""

	def __init__(self, training_samples: dict[str, list[str]] | None = None) -> None:
		self.training_samples = training_samples or self._load_training_samples()
		# category_embeddings: {category: np.ndarray shape (n_samples, dim)}
		self.category_embeddings: dict[str, np.ndarray] = {}
		for category, samples in self.training_samples.items():
			clean_samples = [str(s).strip().lower() for s in samples if str(s).strip()]
			if clean_samples:
				vecs = np.array(embed_texts(clean_samples))
				self.category_embeddings[category] = vecs

		if not self.category_embeddings:
			raise RuntimeError("No valid training samples available for similarity classification")

		logger.info(
			"SimilarityClassifier ready: %d categories, global dataset",
			len(self.category_embeddings),
		)

	def classify(self, cleaned_text: str) -> SimilarityClassificationResult:
		"""Classify text by max cosine similarity against each category pool."""
		if not cleaned_text:
			return SimilarityClassificationResult(document_type=None, confidence=0.0)

		query_vec = np.array(embed_texts([cleaned_text.lower()]))  # (1, dim)

		best_category: str | None = None
		best_score = 0.0

		for category, embeddings in self.category_embeddings.items():
			scores = cosine_similarity(query_vec, embeddings)[0]
			score = float(scores.max())
			if score > best_score:
				best_score = score
				best_category = category

		if best_score < settings.similarity_min_confidence:
			logger.info(
				"Similarity below threshold: score=%.3f threshold=%.3f",
				best_score,
				settings.similarity_min_confidence,
			)
			return SimilarityClassificationResult(document_type=None, confidence=best_score)

		return SimilarityClassificationResult(document_type=best_category, confidence=best_score)

	@staticmethod
	def _load_training_samples() -> dict[str, list[str]]:
		"""Load training samples from global JSON file."""
		path = settings.training_samples_global_path
		try:
			with path.open("r", encoding="utf-8") as json_file:
				raw_data = json.load(json_file)
		except FileNotFoundError as exc:
			raise RuntimeError(f"Training samples file not found: {path}") from exc
		except json.JSONDecodeError as exc:
			raise RuntimeError("Training samples file contains invalid JSON") from exc

		sample_map: dict[str, list[str]] = {}
		for category, samples in raw_data.items():
			if not isinstance(samples, list):
				logger.warning("Skipping category '%s' with invalid samples format", category)
				continue
			valid_samples = [str(item).strip() for item in samples if str(item).strip()]
			if valid_samples:
				sample_map[category] = valid_samples

		if not sample_map:
			raise RuntimeError("Training samples file does not define any valid samples")

		return sample_map
