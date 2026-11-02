"""Automatic category creation for documents no configured category matches.

When the keyword/embedding classifiers return nothing, the document is grouped with
a previously auto-created category (cosine similarity of document embeddings) or a
new category is created, named from the document's title line (or filename).
Categories persist in data/dynamic_categories.json, so later uploads of the same
kind of document land in the same category without any code or config change.
"""

from __future__ import annotations

import fcntl
import json
import logging
import re
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Iterator

import numpy as np

from app.config import settings
from classification.trained_categories import TrainedCategoryStore
from models.embeddings import embed_texts

logger = logging.getLogger(__name__)

MIN_TEXT_LENGTH = 40
MAX_NAME_WORDS = 4
MAX_KEYWORDS = 10
EMBED_CHARS = 2000

_STOPWORDS = frozenset(
	"the a an and or of for to in on at by with from this that is are was were be as it its your you we our "
	"date no number page name address phone email dear sir madam thank regards".split()
)


@dataclass(frozen=True)
class DynamicCategoryResult:
	"""Category chosen for a document, and whether it was created by this call."""

	category: str
	confidence: float
	keywords_detected: list[str]
	created: bool


class DynamicCategoryStore:
	"""JSON-file backed registry of auto-created categories (safe across worker processes)."""

	def __init__(self, path: Path | None = None) -> None:
		self.path = path or settings.dynamic_categories_path
		self._lock = Lock()

	def assign(self, cleaned_text: str, raw_text: str, file_name: str) -> DynamicCategoryResult | None:
		"""Place the document in the closest auto category, or create a new one."""
		if len(cleaned_text.strip()) < MIN_TEXT_LENGTH:
			return None

		vector = np.array(embed_texts([cleaned_text[:EMBED_CHARS]])[0], dtype=float)
		keywords = _top_keywords(cleaned_text)

		with self._locked():
			categories = self._read()
			best_name, best_score = None, 0.0
			for name, entry in categories.items():
				centroid = np.array(entry["centroid"], dtype=float)
				score = _cosine(vector, centroid)
				if score > best_score:
					best_name, best_score = name, score

			if best_name is not None and best_score >= settings.dynamic_category_similarity:
				entry = categories[best_name]
				count = entry["count"]
				entry["centroid"] = ((np.array(entry["centroid"]) * count + vector) / (count + 1)).tolist()
				entry["count"] = count + 1
				entry["keywords"] = list(dict.fromkeys([*entry["keywords"], *keywords]))[: MAX_KEYWORDS * 2]
				self._write(categories)
				return DynamicCategoryResult(best_name, round(best_score, 4), keywords, created=False)

			name = _unique_name(_derive_name(raw_text, file_name), categories)
			categories[name] = {"centroid": vector.tolist(), "count": 1, "keywords": keywords}
			self._write(categories)
			logger.info("Created new document category %r", name)
			return DynamicCategoryResult(name, round(settings.dynamic_category_similarity, 4), keywords, created=True)

	def entries(self) -> dict[str, dict]:
		"""Name -> {count, keywords} for every auto category (centroids left out)."""
		with self._locked():
			return {name: {"count": e["count"], "keywords": e["keywords"]} for name, e in self._read().items()}

	def remove(self, name: str) -> dict | None:
		"""Delete an auto category, returning what it held."""
		with self._locked():
			categories = self._read()
			entry = categories.pop(name, None)
			if entry is not None:
				self._write(categories)
			return entry

	def names(self) -> list[str]:
		"""Names of all auto-created categories."""
		with self._locked():
			return list(self._read())

	@contextmanager
	def _locked(self) -> Iterator[None]:
		"""Thread lock plus an exclusive file lock so RQ workers don't overwrite each other."""
		self.path.parent.mkdir(parents=True, exist_ok=True)
		lock_path = self.path.with_suffix(".lock")
		with self._lock, lock_path.open("w") as lock_file:
			fcntl.flock(lock_file, fcntl.LOCK_EX)
			try:
				yield
			finally:
				fcntl.flock(lock_file, fcntl.LOCK_UN)

	def _read(self) -> dict[str, dict]:
		try:
			with self.path.open("r", encoding="utf-8") as json_file:
				data = json.load(json_file)
		except (FileNotFoundError, json.JSONDecodeError):
			return {}
		return data if isinstance(data, dict) else {}

	def _write(self, categories: dict[str, dict]) -> None:
		tmp_path = self.path.with_suffix(".tmp")
		with tmp_path.open("w", encoding="utf-8") as json_file:
			json.dump(categories, json_file)
		tmp_path.replace(self.path)


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
	denom = float(np.linalg.norm(a) * np.linalg.norm(b))
	return float(np.dot(a, b) / denom) if denom else 0.0


def _top_keywords(text: str) -> list[str]:
	words = [w for w in re.findall(r"[a-z]{4,}", text.lower()) if w not in _STOPWORDS]
	return [word for word, _ in Counter(words).most_common(MAX_KEYWORDS)]


def _derive_name(raw_text: str, file_name: str) -> str:
	"""Title-case name from the first title-like line, falling back to the filename."""
	for line in raw_text.splitlines()[:15]:
		words = re.findall(r"[A-Za-z]+", line)
		if 1 <= len(words) <= 8 and len(words) >= len(line.split()) * 0.8 and len(" ".join(words)) >= 4:
			meaningful = [w for w in words if w.lower() not in _STOPWORDS] or words
			return " ".join(w.capitalize() for w in meaningful[:MAX_NAME_WORDS])

	stem_words = re.findall(r"[A-Za-z]+", Path(file_name).stem)
	if stem_words:
		return " ".join(w.capitalize() for w in stem_words[:MAX_NAME_WORDS])
	return "Uncategorized"


def _unique_name(name: str, existing: dict[str, dict]) -> str:
	taken = {n.lower() for n in existing} | {n.lower() for n in _static_names()}
	if name.lower() not in taken:
		return name
	suffix = 2
	while f"{name} {suffix}".lower() in taken:
		suffix += 1
	return f"{name} {suffix}"


def _static_names() -> list[str]:
	try:
		with settings.category_keywords_path.open("r", encoding="utf-8") as json_file:
			names = list(json.load(json_file))
	except (FileNotFoundError, json.JSONDecodeError):
		names = []
	return names + TrainedCategoryStore().names()
