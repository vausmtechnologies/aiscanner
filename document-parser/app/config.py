"""Centralized configuration for parser service."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Settings:
	"""Application settings shared across parser modules."""

	project_root: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent)
	data_dir: Path = field(init=False)
	max_file_size_mb: int = 10
	supported_extensions: tuple[str, ...] = (
		".pdf",
		".jpg", ".jpeg",
		".png",
		".tif", ".tiff",
		".docx", ".doc",
		".pptx", ".ppt",
		".txt",
	)
	tesseract_language: str = "eng"
	pdf_dpi: int = 200
	# Max pages to OCR per PDF — limits processing time on long documents.
	# Classification + metadata are reliably found in the first few pages.
	pdf_max_pages: int = 5
	embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
	keyword_min_confidence: float = 0.5
	similarity_min_confidence: float = 0.55
	filename_hint_min_confidence: float = 0.55
	equipment_filename_hints: tuple[str, ...] = (
		"light",
		"lights",
		"emergency-light",
		"extinguisher",
		"fire-safety",
		"sprinkler",
		"alarm",
		"log-sheet",
		"log sheet",
		"pat-test",
		"pat test",
		"pat-report",
		"pat report",
	)

	def __post_init__(self) -> None:
		object.__setattr__(self, "data_dir", self.project_root / "data")

	@property
	def max_file_size_bytes(self) -> int:
		"""Maximum allowed file size in bytes."""
		return self.max_file_size_mb * 1024 * 1024

	@property
	def category_keywords_path(self) -> Path:
		"""Path to category keyword definitions."""
		return self.data_dir / "category_keywords.json"

	@property
	def training_samples_path(self) -> Path:
		"""Path to training sample text definitions."""
		return self.data_dir / "training_samples.json"

	@property
	def training_samples_global_path(self) -> Path:
		"""Path to global (multi-region) training sample text definitions."""
		return self.data_dir / "training_samples_global.json"

	@property
	def evaluation_samples_global_path(self) -> Path:
		"""Path to global evaluation samples for accuracy benchmarking."""
		return self.data_dir / "evaluation_samples_global.json"


settings = Settings()
