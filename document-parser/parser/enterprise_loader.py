"""Enterprise document loader — unified text extraction pipeline for all formats.

For every supported file type the pipeline is:
  1. Validate file size and extension.
  2. Extract native text (no rendering / OCR):
       - PDF     → pdfplumber (embedded font text)
       - DOCX / PPTX / TXT  → python-docx / python-pptx / raw decode
       - Image   → no native text (empty string)
  3. If native text is shorter than ``MIN_NATIVE_CHARS``:
       Extract renderable / embedded images and run Tesseract OCR.
       Append OCR output to whatever native text was found.
  4. Return ``(combined_text, file_type)``.

This module is the single integration point used by the parse pipeline
(``parser.service``) and the debug API endpoint (``app.main``).
"""

from __future__ import annotations

import io
import logging
import zipfile
from pathlib import Path

from PIL import Image

from app.config import settings
from parser.ocr_engine import OCRProcessingError, extract_text_from_images
from parser.office_loader import TEXT_NATIVE_FILE_TYPES, extract_text_from_office_file
from utils.file_utils import ensure_supported_extension, validate_file_size

logger = logging.getLogger(__name__)

# Minimum native-text length before the OCR fallback is triggered.
MIN_NATIVE_CHARS: int = 30

# Image extensions recognised when scanning Office ZIP archives.
_IMAGE_SUFFIXES: frozenset[str] = frozenset(
    {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".tif", ".webp"}
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_document_text(file_bytes: bytes, file_name: str) -> tuple[str, str]:
    """Load a document and return ``(extracted_text, file_type)``.

    Pipeline:
      1. Validate size + extension.
      2. Extract native text (no OCR).
      3. If native text < ``MIN_NATIVE_CHARS`` run OCR on images and append.

    Args:
        file_bytes: Raw uploaded file bytes.
        file_name:  Original filename (used only for extension detection).

    Returns:
        Tuple of ``(text, file_type)`` where *file_type* is one of
        ``"pdf"``, ``"docx"``, ``"doc"``, ``"pptx"``, ``"ppt"``, ``"txt"``,
        or ``"image"``.
    """
    validate_file_size(file_bytes)
    extension = ensure_supported_extension(file_name)
    file_type = _normalise_file_type(extension)

    native_text = _extract_native_text(file_bytes, file_type)

    if len(native_text.strip()) < MIN_NATIVE_CHARS:
        logger.info(
            "Native text too short (%d chars) for %s — running OCR fallback",
            len(native_text.strip()),
            file_type,
        )
        ocr_text = _extract_ocr_text(file_bytes, file_type)
        if ocr_text:
            return (native_text.strip() + "\n" + ocr_text).strip(), file_type

    return native_text, file_type


# ---------------------------------------------------------------------------
# Extension → file_type normalisation
# ---------------------------------------------------------------------------

def _normalise_file_type(extension: str) -> str:
    """Map a dotted extension to a canonical file_type token.

    All raster image extensions collapse to ``"image"`` to match the
    convention used throughout the rest of the codebase.
    """
    ext = extension.lstrip(".").lower()
    if ext in {"jpg", "jpeg", "png", "tif", "tiff"}:
        return "image"
    return ext  # pdf, docx, doc, pptx, ppt, txt


# ---------------------------------------------------------------------------
# Native text extraction (no OCR)
# ---------------------------------------------------------------------------

def _extract_native_text(file_bytes: bytes, file_type: str) -> str:
    """Extract text without invoking OCR.  Returns empty string when unavailable."""
    if file_type in TEXT_NATIVE_FILE_TYPES:
        # Delegates to python-docx / python-pptx / raw decode as appropriate.
        return extract_text_from_office_file(file_bytes, file_type)

    if file_type == "pdf":
        return _extract_pdf_native_text(file_bytes)

    # Raw image files carry no native text layer.
    return ""


def _extract_pdf_native_text(file_bytes: bytes) -> str:
    """Extract embedded font text from a PDF using pdfplumber (no rendering)."""
    import pdfplumber  # local import — only required on the PDF path

    lines: list[str] = []
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages[: settings.pdf_max_pages]:
                page_text = page.extract_text() or ""
                if page_text.strip():
                    lines.append(page_text.strip())
    except Exception as exc:
        logger.warning("pdfplumber native text extraction failed: %s", exc)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# OCR fallback — render / extract images then Tesseract
# ---------------------------------------------------------------------------

def _extract_ocr_text(file_bytes: bytes, file_type: str) -> str:
    """Run OCR on images extracted from *file_bytes*.  Returns empty string on failure."""
    images = _get_images_for_ocr(file_bytes, file_type)
    if not images:
        logger.info("No images available for OCR fallback (file_type=%s)", file_type)
        return ""
    try:
        return extract_text_from_images(images)
    except OCRProcessingError as exc:
        logger.warning("OCR fallback failed: %s", exc)
        return ""


def _get_images_for_ocr(file_bytes: bytes, file_type: str) -> list[Image.Image]:
    """Return PIL images ready for OCR, selecting the correct strategy per type."""
    if file_type == "pdf":
        return _render_pdf_pages(file_bytes)
    if file_type in ("docx", "doc"):
        return _extract_zip_images(file_bytes, prefix="word/media/")
    if file_type in ("pptx", "ppt"):
        return _extract_zip_images(file_bytes, prefix="ppt/media/")
    if file_type == "txt":
        return []
    # Raw image file — treat the file bytes themselves as the OCR source.
    return _load_single_image(file_bytes)


def _render_pdf_pages(file_bytes: bytes) -> list[Image.Image]:
    """Rasterise PDF pages for OCR using pdf2image / poppler."""
    from pdf2image import convert_from_bytes
    from pdf2image.exceptions import PDFInfoNotInstalledError, PDFPageCountError, PDFSyntaxError
    from parser.file_loader import DocumentLoadingError

    if not file_bytes.startswith(b"%PDF"):
        raise DocumentLoadingError("Uploaded file is not a valid PDF")

    try:
        pages = convert_from_bytes(
            file_bytes,
            dpi=settings.pdf_dpi,
            first_page=1,
            last_page=settings.pdf_max_pages,
        )
    except (PDFInfoNotInstalledError, PDFPageCountError, PDFSyntaxError) as exc:
        raise DocumentLoadingError(f"PDF rendering failed: {exc}") from exc

    if not pages:
        raise DocumentLoadingError("PDF did not contain any pages")

    logger.info("Rendered %d PDF page(s) for OCR", len(pages))
    return pages


def _extract_zip_images(file_bytes: bytes, prefix: str) -> list[Image.Image]:
    """Extract images stored under *prefix* inside a ZIP-based Office file."""
    images: list[Image.Image] = []
    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
            media_names = sorted(
                name for name in zf.namelist()
                if name.startswith(prefix)
                and Path(name).suffix.lower() in _IMAGE_SUFFIXES
            )
            for name in media_names:
                try:
                    img = Image.open(io.BytesIO(zf.read(name))).convert("RGB")
                    images.append(img)
                except Exception as exc:
                    logger.debug("Skipping media entry %r: %s", name, exc)
    except zipfile.BadZipFile as exc:
        logger.warning("Office file is not a valid ZIP archive: %s", exc)
    logger.info(
        "Extracted %d image(s) from Office archive (prefix=%r)", len(images), prefix
    )
    return images


def _load_single_image(file_bytes: bytes) -> list[Image.Image]:
    """Load a raw image file as a single-element list for OCR."""
    try:
        img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        return [img]
    except Exception as exc:
        logger.warning("Could not open image for OCR: %s", exc)
        return []
