"""Sentence embedding model loading and inference."""

from __future__ import annotations

import logging
from threading import Lock

from sentence_transformers import SentenceTransformer

from app.config import settings

logger = logging.getLogger(__name__)

_model_lock = Lock()
_model_instance: SentenceTransformer | None = None


def get_embedding_model() -> SentenceTransformer:
	"""Load and cache the embedding model for similarity classification."""
	global _model_instance

	if _model_instance is not None:
		return _model_instance

	with _model_lock:
		if _model_instance is None:
			logger.info("Loading embedding model: %s", settings.embedding_model_name)
			_model_instance = SentenceTransformer(settings.embedding_model_name)

	return _model_instance


def embed_texts(texts: list[str]) -> list[list[float]]:
	"""Create embedding vectors for one or more texts."""
	model = get_embedding_model()
	vectors = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
	return vectors.tolist()
