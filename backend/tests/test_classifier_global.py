"""Integration test: hybrid classifier accuracy on global evaluation dataset.

Run:
    pytest tests/test_classifier_global.py -v -s
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from classification.hybrid_classifier import HybridClassifier
from scripts.evaluate_global import run_evaluation

TARGET_ACCURACY = 0.90


def test_global_classifier_accuracy_above_90_percent() -> None:
    """Hybrid classifier must reach ≥ 90 % on the global evaluation dataset."""
    classifier = HybridClassifier()
    correct, total = run_evaluation(classifier, verbose=True)
    accuracy = correct / total if total else 0.0
    assert accuracy >= TARGET_ACCURACY, (
        f"Global classifier accuracy {accuracy:.2%} is below required {TARGET_ACCURACY:.0%} "
        f"(correct={correct}/{total})"
    )
