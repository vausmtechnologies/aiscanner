"""FastAPI entry point for the document parser service."""

from __future__ import annotations

import hmac
import logging
import os
from pathlib import Path

from fastapi import FastAPI, File, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.job_queue import enqueue_parse, fetch_job
from parser.enterprise_loader import load_document_text
from parser.file_loader import DocumentLoadingError
from parser.ocr_engine import OCRProcessingError
from parser.text_cleaner import clean_text
from parser.service import DocumentParserService
from utils.file_utils import FileValidationError, UnsupportedFileTypeError

class ExpiryResponse(BaseModel):
	"""Expiry sub-object embedded in the parse response."""

	start_date: str | None = None
	expiry_date: str | None = None
	days_remaining: int | None = None
	status: str = "unknown"  # "valid" | "expiring_soon" | "expired" | "unknown"
logger = logging.getLogger(__name__)


def _load_env_file(path: Path) -> None:
	"""Load KEY=VALUE lines from backend/.env without overriding real environment variables."""
	if not path.is_file():
		return
	for line in path.read_text().splitlines():
		line = line.strip()
		if line and not line.startswith("#") and "=" in line:
			key, _, value = line.partition("=")
			os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


_load_env_file(Path(__file__).resolve().parent.parent / ".env")

_OPEN_PATHS = {"/health", "/docs", "/redoc", "/openapi.json"}

app = FastAPI(title="AI Document Parser Service", version="1.0.0")

@app.middleware("http")
async def require_api_key(request: Request, call_next):
	"""Reject every call that lacks the PARSER_API_KEY, so nobody can parse documents without it."""
	if request.method == "OPTIONS" or request.url.path in _OPEN_PATHS:
		return await call_next(request)

	expected = os.getenv("PARSER_API_KEY", "")
	if not expected:
		return JSONResponse(status_code=503, content={"message": "PARSER_API_KEY is not configured on the server."})
	if not hmac.compare_digest(request.headers.get("x-api-key", ""), expected):
		return JSONResponse(status_code=401, content={"message": "Invalid or missing API key."})
	return await call_next(request)


# Let any browser frontend call the API; set CORS_ALLOWED_ORIGINS="https://a.com,https://b.com" to restrict it.
app.add_middleware(
	CORSMiddleware,
	allow_origins=[o.strip() for o in os.getenv("CORS_ALLOWED_ORIGINS", "*").split(",") if o.strip()],
	allow_methods=["*"],
	allow_headers=["*"],
)

parser_service = DocumentParserService()


class CategorySection(BaseModel):
	"""One category found in a document, with the details extracted for it."""

	category: str
	confidence: float = Field(ge=0.0, le=1.0)
	keywords_detected: list[str] = Field(default_factory=list)
	metadata: dict[str, str | None] = Field(default_factory=dict)


class ParseSuccessResponse(BaseModel):
	"""Response schema for successful document parsing."""

	success: bool = True
	document_type: str | None
	confidence: float = Field(ge=0.0, le=1.0)
	keywords_detected: list[str]
	text_length: int
	processing_time_ms: int
	method: str = "none"  # "keyword" | "embedding" | "filename" | "none"
	country: str | None = None  # "India" | "UK" | "US" | "EU" | None
	metadata: dict[str, str | None] = Field(default_factory=dict)
	expiry: ExpiryResponse = Field(default_factory=ExpiryResponse)
	categories: list[CategorySection] = Field(default_factory=list)  # every category found, main one first


class ParseErrorResponse(BaseModel):
	"""Response schema for parser failures."""

	success: bool = False
	error_code: str
	message: str


class KeywordCategoryScore(BaseModel):
	"""Category-level keyword matching details for diagnostics."""

	category: str
	confidence: float = Field(ge=0.0, le=1.0)
	matched_count: int
	total_keywords: int
	keywords_detected: list[str]


class DebugKeywordsResponse(BaseModel):
	"""Response schema for debug keywords endpoint."""

	success: bool = True
	text_length: int
	top_category: str | None
	top_confidence: float = Field(ge=0.0, le=1.0)
	category_scores: list[KeywordCategoryScore]


@app.get("/health")
def health() -> dict[str, str]:
	"""Basic health endpoint for integration checks."""
	return {"status": "ok"}


@app.get("/")
def root() -> dict[str, str]:
	"""Root endpoint with basic API usage details."""
	return {
		"service": "AI Document Parser Service",
		"status": "running",
		"health": "/health",
		"parse_endpoint": "/parse-document",
		"jobs_endpoint": "/jobs",
		"debug_keywords_endpoint": "/debug-keywords",
		"docs": "/docs",
	}


@app.post("/parse-document", response_model=ParseSuccessResponse)
async def parse_document(file: UploadFile = File(...)) -> ParseSuccessResponse | JSONResponse:
	"""Parse an uploaded document and return classification metadata."""
	try:
		file_bytes = await file.read()
		result = parser_service.parse_document(file_bytes=file_bytes, file_name=file.filename or "")

		return ParseSuccessResponse(
			success=True,
			document_type=result.document_type,
			confidence=result.confidence,
			keywords_detected=result.keywords_detected,
			text_length=result.text_length,
			processing_time_ms=result.processing_time_ms,
			method=result.method,
			country=result.country,
			metadata=result.metadata,
			expiry=ExpiryResponse(
				start_date=result.expiry.start_date,
				expiry_date=result.expiry.expiry_date,
				days_remaining=result.expiry.days_remaining,
				status=result.expiry.status,
			),
			categories=[CategorySection(**section) for section in result.categories],
		)

	except UnsupportedFileTypeError as exc:
		return _error_response("unsupported_file_type", str(exc), 400)
	except FileValidationError as exc:
		return _error_response("invalid_file", str(exc), 400)
	except DocumentLoadingError as exc:
		return _error_response("corrupt_or_unreadable_file", str(exc), 422)
	except OCRProcessingError as exc:
		return _error_response("ocr_failure", str(exc), 422)
	except Exception as exc:  # pragma: no cover - top-level API safety net
		logger.exception("Unexpected parse pipeline failure")
		return _error_response("internal_error", str(exc), 500)


@app.post("/jobs", status_code=202)
async def create_job(file: UploadFile = File(...)) -> JSONResponse:
	"""Queue a document for background parsing and return its job id."""
	try:
		job_id = enqueue_parse(await file.read(), file.filename or "")
	except Exception as exc:
		logger.exception("Could not enqueue job")
		return _error_response("queue_unavailable", f"Job queue is not available: {exc}", 503)
	return JSONResponse(status_code=202, content={"job_id": job_id, "status": "queued"})


@app.get("/jobs/{job_id}")
def get_job(job_id: str) -> JSONResponse:
	"""Return job status: queued | started | finished | failed (+ result when finished)."""
	job = fetch_job(job_id)
	if job is None:
		return _error_response("job_not_found", "Job not found or expired.", 404)
	status = job.get_status()
	if status == "finished":
		return JSONResponse(content={"job_id": job_id, "status": "finished", "result": job.result})
	if status == "failed":
		return JSONResponse(content={"job_id": job_id, "status": "failed", "message": "Worker failed or timed out."})
	return JSONResponse(content={"job_id": job_id, "status": "started" if status == "started" else "queued"})


@app.post("/debug-keywords", response_model=DebugKeywordsResponse)
async def debug_keywords(file: UploadFile = File(...)) -> DebugKeywordsResponse | JSONResponse:
	"""Inspect category keyword matches for a given uploaded document."""
	try:
		file_bytes = await file.read()
		extracted_text, _ = load_document_text(file_bytes=file_bytes, file_name=file.filename or "")
		cleaned_text = clean_text(extracted_text)

		category_scores = parser_service.hybrid_classifier.keyword_classifier.score_categories(cleaned_text)
		top_category = str(category_scores[0]["category"]) if category_scores else None
		top_confidence = float(category_scores[0]["confidence"]) if category_scores else 0.0

		return DebugKeywordsResponse(
			success=True,
			text_length=len(cleaned_text),
			top_category=top_category,
			top_confidence=top_confidence,
			category_scores=[KeywordCategoryScore(**item) for item in category_scores],
		)

	except UnsupportedFileTypeError as exc:
		return _error_response("unsupported_file_type", str(exc), 400)
	except FileValidationError as exc:
		return _error_response("invalid_file", str(exc), 400)
	except DocumentLoadingError as exc:
		return _error_response("corrupt_or_unreadable_file", str(exc), 422)
	except OCRProcessingError as exc:
		return _error_response("ocr_failure", str(exc), 422)
	except Exception as exc:  # pragma: no cover - top-level API safety net
		logger.exception("Unexpected debug keyword failure")
		return _error_response("internal_error", str(exc), 500)


def _error_response(error_code: str, message: str, status_code: int) -> JSONResponse:
	"""Create standardized JSON errors for parser API responses."""
	payload = ParseErrorResponse(error_code=error_code, message=message)
	return JSONResponse(status_code=status_code, content=payload.model_dump())
