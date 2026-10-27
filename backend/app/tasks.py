"""Background tasks executed by the RQ worker (see `rq worker` in README)."""

from __future__ import annotations

import logging
from dataclasses import asdict

from parser.file_loader import DocumentLoadingError
from parser.ocr_engine import OCRProcessingError
from parser.service import DocumentParserService
from utils.file_utils import FileValidationError, UnsupportedFileTypeError

logger = logging.getLogger(__name__)

_service: DocumentParserService | None = None


def _get_service() -> DocumentParserService:
	"""Load the models once per worker process, on first job."""
	global _service
	if _service is None:
		_service = DocumentParserService()
	return _service


def parse_job(file_bytes: bytes, file_name: str) -> dict:
	"""Parse one document; always returns a JSON-safe dict (never raises for bad files)."""
	try:
		result = _get_service().parse_document(file_bytes=file_bytes, file_name=file_name)
	except UnsupportedFileTypeError as exc:
		return _error("unsupported_file_type", exc)
	except FileValidationError as exc:
		return _error("invalid_file", exc)
	except DocumentLoadingError as exc:
		return _error("corrupt_or_unreadable_file", exc)
	except OCRProcessingError as exc:
		return _error("ocr_failure", exc)
	except Exception as exc:  # pragma: no cover - worker safety net
		logger.exception("Unexpected parse pipeline failure")
		return _error("internal_error", exc)

	return {
		"success": True,
		"document_type": result.document_type,
		"confidence": result.confidence,
		"keywords_detected": result.keywords_detected,
		"text_length": result.text_length,
		"processing_time_ms": result.processing_time_ms,
		"method": result.method,
		"country": result.country,
		"metadata": result.metadata,
		"expiry": asdict(result.expiry),
		"categories": result.categories,
	}


def _error(error_code: str, exc: Exception) -> dict:
	return {"success": False, "error_code": error_code, "message": str(exc)}
