"""Categories taught through the training UI (no JSON editing, no restart).

Each entry holds keywords mined from the uploaded sample documents plus short text
samples used by the embedding classifier. Entries may extend a built-in category
(e.g. more Vehicles samples) or define a brand new one. Persisted in
data/trained_categories.json; the classifier reloads it whenever the file changes.
"""

from __future__ import annotations

import fcntl
import json
import math
import re
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Iterator

from app.config import settings

MAX_KEYWORDS = 15
SAMPLE_CHARS = 1000  # roughly what the embedding model reads
SAMPLES_PER_DOCUMENT = 2
MAX_SAMPLES = 60  # per category, oldest dropped first

_STOPWORDS = frozenset(
	"the a an and or of for to in on at by with from this that these those is are was were be been as it its your you "
	"we our they their his her has have had not but also all any can will may shall per into than then there here "
	"date page name no number".split()
)
_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 &_\-]{1,59}$")


def normalise_name(raw: str) -> str:
	"""Collapse whitespace and validate a category name; raises ValueError when unusable."""
	name = " ".join((raw or "").split())
	if not _NAME_PATTERN.match(name):
		raise ValueError("Category name must be 2-60 characters: letters, numbers, spaces, - _ &")
	return name


def mine_keywords(texts: list[str], other_texts: list[str], limit: int = MAX_KEYWORDS) -> list[str]:
	"""Terms that recur in this category's documents but are rare in every other category."""
	if not texts:
		return []

	own = [_terms(text) for text in texts]
	others = [_terms(text) for text in other_texts]
	own_total: Counter[str] = Counter()
	own_docs: Counter[str] = Counter()
	for terms in own:
		own_total.update(terms)
		own_docs.update(set(terms))

	min_ratio = 0.5 if len(texts) >= 3 else 0.0
	scored: list[tuple[float, str]] = []
	for term, docs in own_docs.items():
		ratio = docs / len(texts)
		if ratio < min_ratio:
			continue
		others_with = sum(1 for terms in others if term in terms)
		idf = math.log((1 + len(others)) / (1 + others_with)) + 0.1
		weight = 1.3 if " " in term else 1.0
		scored.append((ratio * idf * weight + 0.01 * min(own_total[term], 10), term))

	scored.sort(key=lambda item: (-item[0], item[1]))
	chosen: list[str] = []
	for _, term in scored:
		if len(chosen) >= limit:
			break
		if " " not in term and any(term in picked.split() for picked in chosen):
			continue  # already covered by a chosen phrase
		chosen.append(term)
	return chosen


def _terms(cleaned_text: str) -> Counter[str]:
	words = cleaned_text.split()
	terms: Counter[str] = Counter()
	for index, word in enumerate(words):
		if len(word) >= 4 and word.isalpha() and word not in _STOPWORDS:
			terms[word] += 1
		if index + 1 < len(words):
			nxt = words[index + 1]
			if (
				len(word) >= 3 and len(nxt) >= 3 and word.isalpha() and nxt.isalpha()
				and word not in _STOPWORDS and nxt not in _STOPWORDS
			):
				terms[f"{word} {nxt}"] += 1
	return terms


def sample_chunks(cleaned_text: str) -> list[str]:
	"""Short text samples taken from the start of a document."""
	chunks = [cleaned_text[i : i + SAMPLE_CHARS] for i in range(0, len(cleaned_text), SAMPLE_CHARS)]
	return [chunk for chunk in chunks[:SAMPLES_PER_DOCUMENT] if len(chunk.strip()) >= 30]


class TrainedCategoryStore:
	"""JSON-file backed registry of trained categories (safe across worker processes)."""

	def __init__(self, path: Path | None = None) -> None:
		self.path = path or settings.trained_categories_path
		self._lock = Lock()

	def version(self) -> float:
		"""Changes whenever the file changes; lets other processes notice new training."""
		try:
			return self.path.stat().st_mtime_ns
		except FileNotFoundError:
			return 0

	def all(self) -> dict[str, dict]:
		with self._locked():
			return self._read()

	def names(self) -> list[str]:
		return list(self.all())

	def add(
		self,
		category: str,
		keywords: list[str],
		samples: list[str],
		documents: int,
		sources: list[str] | None = None,
	) -> dict:
		"""Merge new keywords/samples into a category, creating it when needed."""
		with self._locked():
			data = self._read()
			entry = data.setdefault(category, {"keywords": [], "samples": [], "documents": 0, "sources": []})
			entry["keywords"] = list(dict.fromkeys([*entry["keywords"], *keywords]))
			entry["samples"] = list(dict.fromkeys([*entry["samples"], *samples]))[-MAX_SAMPLES:]
			entry["documents"] += documents
			entry["sources"] = list(dict.fromkeys([*entry.get("sources", []), *(sources or [])]))[-200:]
			entry["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
			self._write(data)
			return entry

	def remove(self, category: str) -> bool:
		with self._locked():
			data = self._read()
			if category not in data:
				return False
			del data[category]
			self._write(data)
			return True

	@contextmanager
	def _locked(self) -> Iterator[None]:
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

	def _write(self, data: dict[str, dict]) -> None:
		tmp_path = self.path.with_suffix(".tmp")
		with tmp_path.open("w", encoding="utf-8") as json_file:
			json.dump(data, json_file, indent=1)
		tmp_path.replace(self.path)
