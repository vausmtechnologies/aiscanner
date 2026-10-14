"""Evaluate hybrid classifier accuracy against labeled evaluation samples.

Run as a pytest test:
    pytest tests/test_classifier.py -v -s

Run standalone:
    python tests/test_classifier.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from classification.hybrid_classifier import HybridClassifier
from parser.text_cleaner import clean_text

EVAL_SAMPLES_PATH = PROJECT_ROOT / "data" / "evaluation_samples.json"


def _run_evaluation(classifier: HybridClassifier) -> tuple[int, int]:
    """Run classifier over evaluation_samples.json and return (correct, total)."""
    samples: list[dict[str, str]] = json.loads(EVAL_SAMPLES_PATH.read_text(encoding="utf-8"))
    total = len(samples)
    correct = 0

    print(f"\n{'expected':16} | {'predicted':18} | {'method':10} | conf")
    print("-" * 62)

    for sample in samples:
        expected = str(sample.get("category", "")).strip()
        text = clean_text(str(sample.get("text", "")).strip())
        result = classifier.classify_document(text)
        match = "✓" if result.document_type == expected else "✗"
        if result.document_type == expected:
            correct += 1
        print(
            f"{expected:16} | {str(result.document_type):18} | "
            f"{result.method:10} | {result.confidence:.3f}  {match}"
        )

    accuracy = correct / total if total else 0.0
    print("-" * 62)
    print(f"samples={total}  correct={correct}  accuracy={accuracy:.2%}")
    return correct, total


def test_classifier_accuracy_above_80_percent() -> None:
    """Integration test: hybrid classifier must reach ≥ 80 % on evaluation samples."""
    classifier = HybridClassifier()
    correct, total = _run_evaluation(classifier)
    accuracy = correct / total if total else 0.0
    assert accuracy >= 0.8, f"Classifier accuracy {accuracy:.2%} is below required 80 %"


if __name__ == "__main__":
    _run_evaluation(HybridClassifier())
