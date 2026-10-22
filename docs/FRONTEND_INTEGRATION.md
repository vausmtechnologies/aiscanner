# AI Scanner – Frontend Integration Guide

Koi bhi frontend (React, Vue, Angular, Flutter, mobile, plain JS) AI Scanner se HTTP/JSON ke through connect ho sakta hai.

## 1. Architecture

```
Your Frontend  ──►  Laravel API (frontend/, /api/*)  ──►  FastAPI Parser (backend/)  ──►  Redis/RQ worker
   X-API-Key              X-API-Key (API_KEY)                X-API-Key (PARSER_API_KEY)
```

Aapke paas 2 options hain:

| Option | Kab use kare | Base URL |
|---|---|---|
| **A. Laravel API (recommended)** | Zip upload, batch status, search chahiye | `http://<laravel-host>/api` |
| **B. FastAPI direct** | Sirf single document parse, simple setup | `http://<parser-host>:8000` |

> Production mein browser se seedha FastAPI call mat karo – API key frontend code mein leak ho jayegi. Apne backend/proxy ke through call karo.

## 2. Setup (ek baar)

**backend/.env**
```
PARSER_API_KEY=<secret>
CORS_ALLOWED_ORIGINS=https://your-frontend.com   # dev ke liye *
```

**frontend/.env** (Laravel)
```
PARSER_URL=http://127.0.0.1:8000
PARSER_API_KEY=<same secret as backend>
API_KEY=<key jo aapka frontend bhejega>
CORS_ALLOWED_ORIGINS=https://your-frontend.com   # dev ke liye *
```

Har request mein header: `X-API-Key: <API_KEY>`. Key empty ho to API sab calls reject karti hai.
Supported files: `pdf, jpg, jpeg, png, tif, tiff, docx, doc, pptx, ppt, txt` (aur `.zip` Laravel API par). Max 50 MB (zip ke andar har file max 10 MB).

## 3. Option A – Laravel API

### POST `/api/scan` – upload
`multipart/form-data`, field `file` (single document ya zip).

Response `202`:
```json
{ "batch_id": "abc123" }
```

### GET `/api/scan/{batch_id}/status` – polling
```json
{ "done": false, "finished": 1, "total": 3 }
```
`404` agar batch expire ho gaya. Har 1–2 sec mein poll karo jab tak `done: true`.

### GET `/api/scan/{batch_id}/result` – final result
**Single-use**: ek baar lene ke baad batch clear ho jata hai. `409` agar abhi done nahi.
```json
{
  "zip": null,
  "filename": "passport.pdf",
  "skipped": 0,
  "items": [
    {
      "filename": "passport.pdf",
      "result": {
        "success": true,
        "document_type": "passport",
        "confidence": 0.93,
        "keywords_detected": ["passport", "nationality"],
        "text_length": 1450,
        "processing_time_ms": 820,
        "method": "keyword",
        "country": "India",
        "metadata": { "name": "…", "document_number": "…" },
        "expiry": { "start_date": "2020-01-01", "expiry_date": "2030-01-01", "days_remaining": 1200, "status": "valid" }
      }
    },
    { "filename": "bad.pdf", "error": "Parser returned an error." }
  ]
}
```
`expiry.status`: `valid | expiring_soon | expired | unknown`. `method`: `keyword | embedding | filename | none`.

### GET `/api/search?q=&type=&status=`
Ab tak scan hue documents mein search (max 50). `type=unknown` = unclassified; `status` = expiry status.
Response: `{ query, count, types: {passport: 3, …}, documents: [{ id, filename, document_type, country, confidence, expiry_status, expiry_date, metadata, scanned_at }] }`

## 4. Option B – FastAPI direct

| Method | Path | Kaam |
|---|---|---|
| POST | `/parse-document` | Turant parse (sync), field `file` |
| POST | `/jobs` | Background queue, returns `{job_id, status:"queued"}` (202) |
| GET | `/jobs/{job_id}` | `queued / started / finished (+result) / failed` |
| POST | `/debug-keywords` | Keyword match diagnostics |
| GET | `/health` | Health check (no key needed) |
| GET | `/docs` | Swagger UI (no key needed) |

Errors: `{ "success": false, "error_code": "...", "message": "..." }` – codes: `unsupported_file_type`, `invalid_file` (400), `corrupt_or_unreadable_file`, `ocr_failure` (422), `queue_unavailable` (503), `job_not_found` (404), `internal_error` (500). Galat/missing key → `401`.

## 5. Code examples

### JavaScript (React/Vue/vanilla) – Laravel API
```js
const API = "http://localhost:8001/api";
const headers = { "X-API-Key": import.meta.env.VITE_API_KEY };

export async function scan(file) {
  const form = new FormData();
  form.append("file", file);

  const { batch_id } = await (await fetch(`${API}/scan`, { method: "POST", headers, body: form })).json();

  while (true) {
    const s = await (await fetch(`${API}/scan/${batch_id}/status`, { headers })).json();
    if (s.done) break;
    await new Promise(r => setTimeout(r, 1500));
  }
  return (await fetch(`${API}/scan/${batch_id}/result`, { headers })).json();
}
```
(Header ko Content-Type mat set karo – browser `multipart` boundary khud lagata hai.)

### cURL
```bash
curl -X POST http://localhost:8001/api/scan -H "X-API-Key: $KEY" -F "file=@passport.pdf"
curl http://localhost:8001/api/scan/abc123/status -H "X-API-Key: $KEY"
curl http://localhost:8001/api/scan/abc123/result -H "X-API-Key: $KEY"
```

### Python
```python
import requests, time
H = {"X-API-Key": KEY}; API = "http://localhost:8001/api"
b = requests.post(f"{API}/scan", headers=H, files={"file": open("passport.pdf", "rb")}).json()["batch_id"]
while not requests.get(f"{API}/scan/{b}/status", headers=H).json()["done"]:
    time.sleep(1.5)
print(requests.get(f"{API}/scan/{b}/result", headers=H).json())
```

### Flutter / mobile
`http.MultipartRequest('POST', Uri.parse('$api/scan'))` + `request.headers['X-API-Key'] = key` + `MultipartFile.fromPath('file', path)`, phir wahi poll → result flow. Mobile apps CORS se affect nahi hoti.

## 6. Checklist / common problems

- **CORS error**: dono `.env` mein `CORS_ALLOWED_ORIGINS` mein frontend ka origin daalo, server restart karo.
- **401**: `X-API-Key` header missing/galat. **503** "not configured": `.env` mein key empty hai.
- **503 queue_unavailable**: Redis aur RQ worker chalu hone chahiye.
- **404 on result/status**: batch expire ho gaya ya result pehle hi le liya (single-use) – dobara upload karo.
- **Secret keys**: browser app mein key public hoti hai; production mein apne server se proxy karo.
- Interactive reference: `http://<parser-host>:8000/docs` (Swagger).
