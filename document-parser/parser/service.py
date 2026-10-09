"""Orchestrates document parsing and classification pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.config import settings
from classification.country_detector import detect_country
from classification.hybrid_classifier import HybridClassifier
from expiry.expiry_detector import ExpiryResult, detect_expiry
from layout.table_detector import detect_tables
from layout.table_mapper import map_fields
from layout.table_parser import merge_tables, parse_table_rows
from metadata.metadata_router import extract_metadata
from parser.enterprise_loader import load_document_text
from parser.text_cleaner import clean_text
from utils.timer import elapsed_timer


@dataclass(frozen=True)
class ParsePipelineResult:
    """Structured result produced by the parser pipeline."""

    document_type: str | None
    confidence: float
    keywords_detected: list[str]
    text_length: int
    processing_time_ms: int
    method: str = "none"  # "keyword" | "embedding" | "filename" | "none"
    country: str | None = None  # "India" | "UK" | "US" | "EU" | None
    metadata: dict[str, str | None] = None  # type: ignore[assignment]
    expiry: ExpiryResult = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        # dataclass is frozen; use object.__setattr__ to set mutable default
        if self.metadata is None:
            object.__setattr__(self, "metadata", {})
        if self.expiry is None:
            object.__setattr__(self, "expiry", ExpiryResult(expiry_date=None, days_remaining=None, status="unknown", start_date=None))


class DocumentParserService:
    """Coordinates loading, OCR, cleaning, and classification stages."""

    def __init__(self) -> None:
        self.hybrid_classifier = HybridClassifier()  # precomputes embeddings at startup

    def parse_document(self, file_bytes: bytes, file_name: str) -> ParsePipelineResult:
        """Parse a single uploaded document and return classification metadata.

        Pipeline:
          1. Load + OCR
          2. Text cleaning
          3. Quick classification (OCR text only)
          4. Table extraction (PDFs only)
          5. Refined classification — re-classify with table signals added
          6. Metadata extraction (regex baseline)
          7. Table metadata mapping + safe merge (empty table values never overwrite)
          8. Expiry detection on OCR text + table values combined
          9. Return JSON
        """
        with elapsed_timer() as elapsed_ms:
            # --- 1–2. Load, extract text, clean ---
            extracted_text, file_type = load_document_text(file_bytes=file_bytes, file_name=file_name)
            cleaned_text = clean_text(extracted_text)

            # --- 3. Quick classification (OCR text only) ---
            result = self.hybrid_classifier.classify_document(cleaned_text)
            document_type = result.document_type
            confidence = result.confidence
            method = result.method

            if not document_type:
                hint_category, hint_confidence = self._classify_from_filename(file_name)
                document_type = hint_category
                confidence = hint_confidence
                method = "filename" if hint_category else "none"

            # --- 4. Table extraction (PDFs only) ---
            table_data: dict[str, str] = {}
            if file_type == "pdf":
                raw_tables = detect_tables(file_bytes, max_pages=settings.pdf_max_pages)
                parsed = [parse_table_rows(t) for t in raw_tables]
                table_data = merge_tables(parsed)

            # --- 5. Refined classification — table signals feed back into classifier ---
            if table_data:
                table_hint_text = " ".join(f"{k} {v}" for k, v in table_data.items())
                refined = self.hybrid_classifier.classify_document(cleaned_text + " " + table_hint_text)
                if refined.document_type and refined.confidence > confidence:
                    document_type = refined.document_type
                    confidence = refined.confidence
                    method = refined.method
                    result = refined  # carry updated keywords_detected forward

            # --- 6. Regex-based metadata (baseline) ---
            regex_metadata = extract_metadata(document_type, cleaned_text)

            # --- 7. Table metadata + safe merge (empty values never overwrite regex) ---
            table_metadata: dict[str, str] = map_fields(table_data, document_type) if table_data else {}
            metadata: dict[str, str | None] = regex_metadata.copy()
            metadata.update({k: v for k, v in table_metadata.items() if v})

            # --- 8. Expiry / start dates — use raw text so / and - in dates survive ---
            table_text = " ".join(f"{k} {v}" for k, v in table_data.items()) if table_data else ""
            expiry_text = extracted_text + ("\n" + table_text if table_text else "")
            expiry = detect_expiry(expiry_text, document_type)

            # --- 9. Country detection ---
            country = detect_country(expiry_text)

            return ParsePipelineResult(
                document_type=document_type,
                confidence=confidence,
                keywords_detected=result.keywords_detected,
                text_length=len(cleaned_text),
                processing_time_ms=elapsed_ms(),
                method=method,
                country=country,
                metadata=metadata,
                expiry=expiry,
            )

    def parse_batch(self, files: list[tuple[bytes, str]]) -> list[ParsePipelineResult]:
        """Parse multiple documents sequentially using the same service instance."""
        return [self.parse_document(file_bytes=data, file_name=name) for data, name in files]

    @staticmethod
    def _classify_from_filename(file_name: str) -> tuple[str | None, float]:
        """Apply low-risk filename hints when OCR text is not informative enough."""
        base_name = clean_text(Path(file_name).stem)
        if not base_name:
            return None, 0.0

        for hint in settings.equipment_filename_hints:
            if hint.replace("-", " ") in base_name:
                return "Equipments", settings.filename_hint_min_confidence

        return None, 0.0
