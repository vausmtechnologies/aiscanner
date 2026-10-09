"""Generic file helper functions."""

from __future__ import annotations

from pathlib import Path

from app.config import settings


class UnsupportedFileTypeError(ValueError):
	"""Raised when a file extension is not supported by the parser."""


class FileValidationError(ValueError):
	"""Raised when a file fails generic validation checks."""


def get_extension(file_name: str) -> str:
	"""Extract normalized file extension from a filename."""
	if not file_name:
		raise FileValidationError("Uploaded file name is missing")
	return Path(file_name).suffix.lower()


def ensure_supported_extension(file_name: str) -> str:
	"""Return extension if supported, otherwise raise a validation error."""
	extension = get_extension(file_name)
	if extension not in settings.supported_extensions:
		supported = ", ".join(settings.supported_extensions)
		raise UnsupportedFileTypeError(
			f"Unsupported file type '{extension}'. Supported types: {supported}"
		)
	return extension


def validate_file_size(file_bytes: bytes) -> None:
	"""Validate that incoming payload size is within configured limits."""
	if not file_bytes:
		raise FileValidationError("Uploaded file is empty")

	if len(file_bytes) > settings.max_file_size_bytes:
		raise FileValidationError(
			f"File size exceeds {settings.max_file_size_mb}MB limit"
		)
