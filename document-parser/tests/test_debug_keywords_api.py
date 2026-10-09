import asyncio
from io import BytesIO

import app.main as api_main
from starlette.datastructures import UploadFile


def test_debug_keywords_returns_category_breakdown(monkeypatch) -> None:
    gst_text = (
        "form gst reg 06 goods and services tax network "
        "legal name private limited company principal place of business"
    )

    # Patch the name as imported into app.main (not on the source module)
    monkeypatch.setattr(
        api_main,
        "load_document_text",
        lambda file_bytes, file_name: (gst_text, "pdf"),
    )

    upload = UploadFile(filename="gst-certificate.pdf", file=BytesIO(b"fake-binary-content"))
    payload = asyncio.run(api_main.debug_keywords(upload)).model_dump()

    assert payload["success"] is True
    assert payload["top_category"] == "Company"
    assert payload["top_confidence"] > 0.0
    assert payload["text_length"] > 0
    assert isinstance(payload["category_scores"], list)
    assert len(payload["category_scores"]) > 0
    assert payload["category_scores"][0]["category"] == "Company"
