# AI Scanner

```
AiScanner/
├── backend/    Python FastAPI document parser (OCR, classification, metadata, expiry)
│   ├── samples/  Sample documents for testing
│   └── docs/     Architecture diagram and build instructions
└── frontend/   Laravel web UI (uploads files to the backend and shows the result)
```

## Run

Terminal 1 - backend (port 8000):

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --port 8000
```

Terminal 2 - frontend (port 8001):

```bash
cd frontend
php artisan serve --port=8001
```

Open http://127.0.0.1:8001. The backend URL is set by `PARSER_URL` in `frontend/.env`.
