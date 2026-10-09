"""Detect and extract tables from PDF bytes using pdfplumber.

Works directly on in-memory bytes — no temp file needed.
Returns raw table data as lists of rows for downstream normalisation.
"""

from __future__ import annotations

import io
import logging

logger = logging.getLogger(__name__)

# pdfplumber is an optional dependency; raise a clear error if missing.
try:
    import pdfplumber
    _PDFPLUMBER_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PDFPLUMBER_AVAILABLE = False


def detect_tables(pdf_bytes: bytes, max_pages: int | None = None) -> list[list[list[str | None]]]:
    """Extract all tables from *pdf_bytes*, up to *max_pages* pages.

    Args:
        pdf_bytes:  Raw PDF content.
        max_pages:  Page limit (None = all pages).  Keeps performance bounded.

    Returns:
        List of tables, where each table is a list of rows and each row is a
        list of cell strings (or None for empty cells).
    """
    if not _PDFPLUMBER_AVAILABLE:
        logger.warning("pdfplumber not installed — table detection skipped")
        return []

    if not pdf_bytes.startswith(b"%PDF"):
        logger.debug("Bytes do not appear to be a PDF — skipping table detection")
        return []

    tables: list[list[list[str | None]]] = []

    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            pages = pdf.pages[:max_pages] if max_pages else pdf.pages
            for page_num, page in enumerate(pages, start=1):
                extracted = page.extract_tables()
                for table in extracted:
                    if table:
                        tables.append(table)
                        logger.debug(
                            "Page %d: found table with %d rows", page_num, len(table)
                        )
    except Exception:
        logger.exception("pdfplumber table extraction failed — continuing without tables")
        return []

    logger.info("Table detection: found %d table(s)", len(tables))
    return tables
