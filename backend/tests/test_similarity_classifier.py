from classification.similarity_classifier import SimilarityClassifier


def test_similarity_classifier_returns_best_category(monkeypatch) -> None:
    def fake_embed_texts(texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            lower = text.lower()
            if "vehicle" in lower:
                vectors.append([1.0, 0.0, 0.0, 0.0])
            elif "employee" in lower or "passport" in lower:
                vectors.append([0.0, 1.0, 0.0, 0.0])
            elif "invoice" in lower or "equipment" in lower:
                vectors.append([0.0, 0.0, 1.0, 0.0])
            elif "incorporation" in lower or "business" in lower:
                vectors.append([0.0, 0.0, 0.0, 1.0])
            else:
                vectors.append([0.0, 0.0, 0.0, 0.0])
        return vectors

    monkeypatch.setattr("classification.similarity_classifier.embed_texts", fake_embed_texts)

    classifier = SimilarityClassifier(
        training_samples={
            "Vehicles": ["registration certificate vehicle number"],
            "People": ["employee passport aadhaar"],
        }
    )
    result = classifier.classify("vehicle number and registration certificate")

    assert result.document_type == "Vehicles"
    assert result.confidence > 0.8
