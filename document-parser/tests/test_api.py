import asyncio
from io import BytesIO

import app.main as api_main
from expiry.expiry_detector import ExpiryResult
from parser.service import ParsePipelineResult
from starlette.datastructures import UploadFile


def test_parse_document_returns_structured_response(monkeypatch) -> None:
    def fake_parse_document(file_bytes: bytes, file_name: str) -> ParsePipelineResult:
        return ParsePipelineResult(
            document_type="Vehicles",
            confidence=0.9,
            keywords_detected=["registration certificate", "vehicle number"],
            text_length=64,
            processing_time_ms=8,
            method="keyword",
            metadata={"vehicle_number": "DL01AB1234", "engine_number": None,
                      "chassis_number": None, "registration_date": None, "owner_name": None},
            expiry=ExpiryResult(
                expiry_date="2027-04-01",
                days_remaining=400,
                status="valid",
                start_date="2026-04-01",
            ),
        )

    monkeypatch.setattr(api_main.parser_service, "parse_document", fake_parse_document)

    upload = UploadFile(filename="vehicle_rc.jpg", file=BytesIO(b"fake-binary-content"))
    payload = asyncio.run(api_main.parse_document(upload)).model_dump()

    assert payload["success"] is True
    assert payload["document_type"] == "Vehicles"
    assert payload["confidence"] > 0
    assert isinstance(payload["keywords_detected"], list)
    assert payload["text_length"] > 0
    assert payload["processing_time_ms"] >= 0
    assert "method" in payload
    assert isinstance(payload["metadata"], dict)
    assert "expiry" in payload
    assert payload["expiry"]["status"] == "valid"
    assert payload["expiry"]["expiry_date"] == "2027-04-01"
    assert payload["expiry"]["start_date"] == "2026-04-01"
