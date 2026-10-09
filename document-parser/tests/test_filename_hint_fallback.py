from parser.service import DocumentParserService


def test_filename_hint_fallback_for_equipment() -> None:
    category, confidence = DocumentParserService._classify_from_filename("Lights (1).png")
    assert category == "Equipments"
    assert confidence > 0.0


def test_filename_hint_fallback_no_match() -> None:
    category, confidence = DocumentParserService._classify_from_filename("unknown_document.png")
    assert category is None
    assert confidence == 0.0
