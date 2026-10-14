"""OCR extraction logic using Tesseract."""

from __future__ import annotations

import logging

import pytesseract
from PIL import Image

from app.config import settings

logger = logging.getLogger(__name__)


class OCRProcessingError(RuntimeError):
	"""Raised when OCR execution fails for one or more pages."""


def extract_text_from_images(images: list[Image.Image], language: str | None = None) -> str:
	"""Extract and combine OCR text from one or more images."""
	if not images:
		raise OCRProcessingError("No images were supplied for OCR")

	ocr_language = language or settings.tesseract_language
	page_texts: list[str] = []

	for index, image in enumerate(images, start=1):
		try:
			text = pytesseract.image_to_string(image, lang=ocr_language)
		except Exception as exc:  # pragma: no cover - runtime dependencies vary by host
			logger.exception("OCR failed on page %s", index)
			raise OCRProcessingError(f"OCR processing failed on page {index}") from exc

		if text:
			page_texts.append(text.strip())
		logger.debug("Extracted OCR text for page %s (%s characters)", index, len(text or ""))

	combined_text = "\n".join(page_texts).strip()
	if not combined_text:
		raise OCRProcessingError("OCR did not extract readable text")

	logger.info("OCR completed for %s page(s) with %s total characters", len(images), len(combined_text))
	return combined_text
