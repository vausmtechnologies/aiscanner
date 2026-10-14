"""Evaluate parser classification accuracy on labeled text samples."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from classification.keyword_classifier import KeywordClassifier
from classification.similarity_classifier import SimilarityClassifier
from parser.text_cleaner import clean_text


def load_samples(file_path: Path) -> list[dict[str, str]]:
    data = json.loads(file_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Evaluation file must be a list of samples")
    return data


def classify_text(
    text: str, keyword_classifier: KeywordClassifier, similarity_classifier: SimilarityClassifier
) -> tuple[str | None, float]:
    cleaned = clean_text(text)
    keyword_result = keyword_classifier.classify(cleaned)
    if keyword_result.document_type:
        return keyword_result.document_type, keyword_result.confidence

    similarity_result = similarity_classifier.classify(cleaned)
    return similarity_result.document_type, similarity_result.confidence


def evaluate(samples: list[dict[str, str]]) -> None:
    keyword_classifier = KeywordClassifier()
    similarity_classifier = SimilarityClassifier()

    total = len(samples)
    correct = 0

    print("category_expected | category_predicted | confidence")
    print("-" * 56)

    for sample in samples:
        expected = str(sample.get("category", "")).strip()
        text = str(sample.get("text", "")).strip()

        predicted, confidence = classify_text(text, keyword_classifier, similarity_classifier)
        if predicted == expected:
            correct += 1

        print(f"{expected:16} | {str(predicted):18} | {confidence:.3f}")

    accuracy = (correct / total) if total else 0.0
    print("-" * 56)
    print(f"samples={total} correct={correct} accuracy={accuracy:.2%}")


if __name__ == "__main__":
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else PROJECT_ROOT / "data" / "evaluation_samples.json"
    sample_items = load_samples(input_path)
    evaluate(sample_items)
