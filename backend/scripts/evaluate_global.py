"""Evaluate hybrid classifier accuracy against the global evaluation dataset.

Run standalone:
    python scripts/evaluate_global.py

Or via pytest:
    pytest tests/test_classifier_global.py -v -s
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

EVAL_PATH = PROJECT_ROOT / "data" / "evaluation_samples_global.json"
TARGET_ACCURACY = 0.90


def run_evaluation(classifier: HybridClassifier, verbose: bool = True) -> tuple[int, int]:
    """Classify every sample in the global evaluation set.

    Returns (correct, total).
    """
    samples: list[dict[str, str]] = json.loads(EVAL_PATH.read_text(encoding="utf-8"))
    total = len(samples)
    correct = 0

    if verbose:
        print(f"\n{'expected':16} | {'predicted':18} | {'method':10} | {'conf':6} | ok?")
        print("-" * 70)

    for sample in samples:
        expected = str(sample.get("category", "")).strip()
        text = clean_text(str(sample.get("text", "")).strip())
        result = classifier.classify_document(text)
        ok = result.document_type == expected
        if ok:
            correct += 1
        if verbose:
            mark = "✓" if ok else "✗"
            print(
                f"{expected:16} | {str(result.document_type):18} | "
                f"{result.method:10} | {result.confidence:.3f} | {mark}"
            )

    accuracy = correct / total if total else 0.0
    if verbose:
        print("-" * 70)
        print(
            f"samples={total}  correct={correct}  accuracy={accuracy:.2%}  "
            f"target={TARGET_ACCURACY:.0%}"
        )
    return correct, total


if __name__ == "__main__":
    clf = HybridClassifier()
    correct, total = run_evaluation(clf, verbose=True)
    accuracy = correct / total if total else 0.0
    sys.exit(0 if accuracy >= TARGET_ACCURACY else 1)
