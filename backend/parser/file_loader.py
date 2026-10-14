"""File loading and file-type detection utilities."""

from __future__ import annotations

import io
import logging

from PIL import Image, UnidentifiedImageError
from pdf2image import convert_from_bytes
from pdf2image.exceptions import PDFInfoNotInstalledError, PDFPageCountError, PDFSyntaxError

from app.config import settings
from utils.file_utils import ensure_supported_extension, validate_file_size

logger = logging.getLogger(__name__)

# Extensions whose text is extracted directly without OCR
_TEXT_NATIVE_EXTENSIONS: frozenset[str] = frozenset({".docx", ".doc", ".pptx", ".ppt", ".txt"})


class DocumentLoadingError(RuntimeError):
	"""Raised when a valid file cannot be converted into OCR-ready images."""


def load_document_as_images(file_bytes: bytes, file_name: str) -> tuple[list[Image.Image], str]:
	"""Convert an uploaded file into a list of PIL images for OCR.

	Returns:
		Tuple of (images, file_type) where:
		  - file_type is ``'pdf'`` or ``'image'`` for raster-based inputs
		  - file_type is ``'docx'``, ``'pptx'``, ``'txt'``, etc. for text-native
		    formats; in these cases the images list is always empty and text
		    extraction is handled by ``office_loader``.
	"""
	validate_file_size(file_bytes)
	extension = ensure_supported_extension(file_name)

	if extension in _TEXT_NATIVE_EXTENSIONS:
		# Text extracted natively — no image conversion needed
		return [], extension.lstrip(".")

	if extension == ".pdf":
		return _load_pdf(file_bytes), "pdf"

	return [_load_image(file_bytes)], "image"


def _load_pdf(file_bytes: bytes) -> list[Image.Image]:
	if not file_bytes.startswith(b"%PDF"):
		raise DocumentLoadingError("Uploaded file is not a valid PDF")

	try:
		pages = convert_from_bytes(
			file_bytes,
			dpi=settings.pdf_dpi,
			first_page=1,
			last_page=settings.pdf_max_pages,
		)
	except PDFInfoNotInstalledError as exc:
		logger.exception("Poppler is not installed or not available in PATH")
		raise DocumentLoadingError(
			"Poppler is required for PDF parsing. Install with: brew install poppler"
		) from exc
	except PDFPageCountError as exc:
		logger.exception("Unable to read PDF page count; file may be corrupt")
		raise DocumentLoadingError("PDF appears to be corrupt or unreadable") from exc
	except PDFSyntaxError as exc:
		logger.exception("Invalid PDF syntax")
		raise DocumentLoadingError("PDF syntax is invalid or file is corrupt") from exc
	except Exception as exc:  # pragma: no cover - depends on poppler runtime state
		logger.exception("Failed converting PDF to images")
		raise DocumentLoadingError("Unable to load PDF file") from exc

	if not pages:
		raise DocumentLoadingError("PDF did not contain any pages")

	logger.info("Loaded %s page(s) from PDF", len(pages))
	return pages


def _load_image(file_bytes: bytes) -> Image.Image:
	try:
		image = Image.open(io.BytesIO(file_bytes))
		image.load()
	except UnidentifiedImageError as exc:
		logger.exception("Image file format is invalid or corrupt")
		raise DocumentLoadingError("Unable to read image file") from exc
	except Exception as exc:  # pragma: no cover - defensive catch for PIL internals
		logger.exception("Unexpected image loading failure")
		raise DocumentLoadingError("Unable to load image file") from exc

	logger.info("Loaded image for OCR with mode=%s size=%s", image.mode, image.size)
	return image
