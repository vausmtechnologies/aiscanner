import asyncio
import json
from io import BytesIO

import app.main as api_main
from starlette.datastructures import UploadFile
from starlette.responses import JSONResponse


def test_parse_document_rejects_unsupported_file_type() -> None:
    upload = UploadFile(filename="spreadsheet.xlsx", file=BytesIO(b"fake-binary-content"))
    response = asyncio.run(api_main.parse_document(upload))

    assert isinstance(response, JSONResponse)
    assert response.status_code == 400

    payload = json.loads(response.body.decode("utf-8"))
    assert payload["success"] is False
    assert payload["error_code"] == "unsupported_file_type"
