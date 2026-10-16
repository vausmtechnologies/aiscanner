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

Terminal 2 - worker (Redis queue; Redis must be running: `brew services start redis`):

```bash
cd backend
source venv/bin/activate
rq worker parse --worker-class rq.SimpleWorker
```

Run more workers (more terminals) to process more documents in parallel.
Redis URL is set by `REDIS_URL` (default `redis://127.0.0.1:6379/0`).

Terminal 3 - frontend (port 8001):

```bash
cd frontend
./serve.sh 8001   # like `php artisan serve`, but allows 50 MB uploads
```

Open http://127.0.0.1:8001. The backend URL is set by `PARSER_URL` in `frontend/.env`.
