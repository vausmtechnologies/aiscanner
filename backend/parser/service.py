"""Orchestrates document parsing and classification pipeline."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from app.config import settings
from classification.country_detector import detect_country
from classification.dynamic_categories import DynamicCategoryStore
from classification.hybrid_classifier import HybridClassifier
from classification.trained_categories import mine_keywords, normalise_name, sample_chunks
from expiry.expiry_detector import ExpiryResult, detect_expiry
from layout.table_detector import detect_tables
from layout.table_mapper import map_fields
from layout.table_parser import merge_tables, parse_table_rows
from metadata.metadata_router import extract_metadata
from parser.enterprise_loader import load_document_text
from parser.text_cleaner import clean_text, normalize_text
from utils.timer import elapsed_timer


@dataclass(frozen=True)
class ParsePipelineResult:
    """Structured result produced by the parser pipeline."""

    document_type: str | None
    confidence: float
    keywords_detected: list[str]
    text_length: int
    processing_time_ms: int
    method: str = "none"  # "keyword" | "embedding" | "filename" | "auto" | "none"
    country: str | None = None  # "India" | "UK" | "US" | "EU" | None
    metadata: dict[str, str | None] = None  # type: ignore[assignment]
    expiry: ExpiryResult = None  # type: ignore[assignment]
    # One entry per category found in the document: {category, confidence, keywords_detected, metadata}.
    categories: list[dict] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.categories is None:
            object.__setattr__(self, "categories", [])
        # dataclass is frozen; use object.__setattr__ to set mutable default
        if self.metadata is None:
            object.__setattr__(self, "metadata", {})
        if self.expiry is None:
            object.__setattr__(self, "expiry", ExpiryResult(expiry_date=None, days_remaining=None, status="unknown", start_date=None))


class DocumentParserService:
    """Coordinates loading, OCR, cleaning, and classification stages."""

    def __init__(self) -> None:
        self.hybrid_classifier = HybridClassifier()  # precomputes embeddings at startup
        self.dynamic_categories = DynamicCategoryStore()

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

            table_hint_text = " ".join(f"{k} {v}" for k, v in table_data.items())

            # --- 5. Refined classification — table signals feed back into classifier ---
            if table_data:
                refined = self.hybrid_classifier.classify_document(cleaned_text + " " + table_hint_text)
                if refined.document_type and refined.confidence > confidence:
                    document_type = refined.document_type
                    confidence = refined.confidence
                    method = refined.method
                    result = refined  # carry updated keywords_detected forward

            # --- 5b. Nothing matched — group into (or create) an automatic category ---
            if not document_type:
                auto = self.dynamic_categories.assign(cleaned_text, extracted_text, file_name)
                if auto:
                    document_type = auto.category
                    confidence = auto.confidence
                    method = "auto"
                    result = replace(result, keywords_detected=auto.keywords_detected)

            # --- 6. Regex-based metadata (baseline) — on case-preserving text, cleaned_text is lowercase ---
            regex_text = normalize_text(extracted_text)
            regex_metadata = extract_metadata(document_type, regex_text)

            # --- 7. Table metadata + safe merge (empty values never overwrite regex) ---
            table_metadata: dict[str, str] = map_fields(table_data, document_type) if table_data else {}
            metadata: dict[str, str | None] = regex_metadata.copy()
            metadata.update({k: v for k, v in table_metadata.items() if v})

            # --- 7b. Every category present in the document, each with its own details ---
            categories = self._build_categories(
                scoring_text=cleaned_text + (" " + table_hint_text if table_data else ""),
                regex_text=regex_text,
                table_data=table_data,
                primary=(document_type, confidence, result.keywords_detected, metadata),
            )

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
                categories=categories,
            )

    def _build_categories(
        self,
        scoring_text: str,
        regex_text: str,
        table_data: dict[str, str],
        primary: tuple[str | None, float, list[str], dict[str, str | None]],
    ) -> list[dict]:
        """List every category found in the document (the main one first) with the details extracted for it."""
        primary_type, primary_confidence, primary_keywords, primary_metadata = primary
        sections: list[dict] = []
        if primary_type:
            sections.append({
                "category": primary_type,
                "confidence": primary_confidence,
                "keywords_detected": primary_keywords,
                "metadata": primary_metadata,
            })

        for category, category_confidence, keywords in self.hybrid_classifier.matching_categories(scoring_text):
            if category == primary_type:
                continue
            details: dict[str, str | None] = extract_metadata(category, regex_text)
            details.update({k: v for k, v in map_fields(table_data, category).items() if v} if table_data else {})
            sections.append({
                "category": category,
                "confidence": category_confidence,
                "keywords_detected": keywords,
                "metadata": details,
            })
        return sections

    # ------------------------------------------------------------------
    # Training (driven by the training UI)
    # ------------------------------------------------------------------

    def train_category(self, category: str, files: list[tuple[bytes, str]]) -> dict:
        """Teach a category (new or existing) from sample documents; takes effect immediately.

        Raises ValueError for an invalid name. Per-file problems are reported in ``files``.
        """
        name = self._canonical_name(normalise_name(category))
        store = self.hybrid_classifier.trained_store

        report: list[dict] = []
        texts: list[str] = []
        for file_bytes, file_name in files:
            try:
                extracted, _ = load_document_text(file_bytes=file_bytes, file_name=file_name)
            except Exception as exc:  # unreadable files are reported, not fatal for the batch
                report.append({"filename": file_name, "ok": False, "error": str(exc)})
                continue
            cleaned = clean_text(extracted)
            if len(cleaned) < 30:
                report.append({"filename": file_name, "ok": False, "error": "No readable text found."})
                continue
            texts.append(cleaned)
            report.append({"filename": file_name, "ok": True, "text_length": len(cleaned)})

        if texts:
            keywords = mine_keywords(texts, self._other_category_texts(name))
            samples = [chunk for text in texts for chunk in sample_chunks(text)]
            store.add(name, keywords, samples, documents=len(texts), sources=[r["filename"] for r in report if r["ok"]])
            self.hybrid_classifier.reload_trained()

        return {"category": name, "trained_documents": len(texts), "files": report, "details": self._category_details(name)}

    def list_categories(self) -> list[dict]:
        """Every category the scanner knows: built-in, trained (new or extended) and auto-created."""
        trained = self.hybrid_classifier.trained_store.all()
        static = self.hybrid_classifier._static_keywords
        rows = [self._category_details(name) for name in static]
        rows += [self._category_details(name) for name in trained if name not in static]
        rows += [
            {"name": name, "kind": "auto", "documents": e["count"], "keywords": e["keywords"], "trained_documents": 0}
            for name, e in self.dynamic_categories.entries().items()
        ]
        return rows

    def delete_category(self, name: str) -> bool:
        """Forget trained data (a built-in category keeps its defaults) or an auto category."""
        removed = self.hybrid_classifier.trained_store.remove(name)
        removed = self.dynamic_categories.remove(name) is not None or removed
        if removed:
            self.hybrid_classifier.reload_trained()
        return removed

    def promote_auto_category(self, auto_name: str, new_name: str | None = None) -> dict:
        """Turn an auto-created category into a trained one (optionally renaming it)."""
        entry = self.dynamic_categories.remove(auto_name)
        if entry is None:
            raise KeyError(auto_name)
        name = self._canonical_name(normalise_name(new_name or auto_name))
        self.hybrid_classifier.trained_store.add(name, entry["keywords"], [" ".join(entry["keywords"])], documents=entry["count"])
        self.hybrid_classifier.reload_trained()
        return self._category_details(name)

    def _canonical_name(self, name: str) -> str:
        """Reuse the stored spelling when the name matches an existing category ignoring case."""
        known = [*self.hybrid_classifier._static_keywords, *self.hybrid_classifier.trained_store.names()]
        return next((existing for existing in known if existing.lower() == name.lower()), name)

    def _other_category_texts(self, name: str) -> list[str]:
        """One cleaned text per other category (keywords + samples), to find what makes this one distinctive."""
        classifier = self.hybrid_classifier
        trained = classifier.trained_store.all()
        texts: list[str] = []
        for category in {*classifier.keyword_classifier.keyword_map, *classifier.similarity_classifier.training_samples}:
            if category == name:
                continue
            parts = list(classifier.keyword_classifier.keyword_map.get(category, []))
            parts += classifier.similarity_classifier.training_samples.get(category, [])
            parts += trained.get(category, {}).get("samples", [])
            texts.append(clean_text(" ".join(parts)))
        return texts

    def _category_details(self, name: str) -> dict:
        classifier = self.hybrid_classifier
        entry = classifier.trained_store.all().get(name)
        builtin = name in classifier._static_keywords
        return {
            "name": name,
            "kind": "built-in" if builtin else "trained",
            "documents": entry["documents"] if entry else 0,
            "trained_documents": entry["documents"] if entry else 0,
            "keywords": classifier.keyword_classifier.keyword_map.get(name, []),
            "trained_keywords": entry["keywords"] if entry else [],
            "updated_at": entry.get("updated_at") if entry else None,
        }

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
