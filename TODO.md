# TODO

## Make the API frontend-agnostic (React / mobile / any client)

Today the Laravel app is both the UI and the product logic (zip handling, batch
tracking, document storage, search). The goal is a clean JSON API so any
frontend can plug in.

- [ ] Laravel: add `routes/api.php` with JSON-only endpoints
  - [ ] `POST /api/scan` — accepts file/zip, returns `{ batch_id }` (no redirect/flash)
  - [ ] `GET /api/scan/{batch}/status` — `{ done, finished, total }`
  - [ ] `GET /api/scan/{batch}/result` — returns result JSON instead of redirecting
  - [ ] `GET /api/search` — reuse the existing `search()` logic
- [ ] Laravel: move shared logic out of `ScanController` into a service class so Blade and API both use it
- [ ] Laravel: keep Blade UI as optional; point it at the same service/API
- [ ] Laravel: batch state currently lives in Cache (expires after 1 hour) — decide if it should be persisted
- [ ] FastAPI: add `CORSMiddleware` (verify whether it is already configured)
- [ ] FastAPI / Laravel API: add auth (API key or token) before production
- [ ] Docs: publish API reference (FastAPI `/docs` + OpenAPI file for the Laravel API)

## React integration (when ready)

- [ ] Upload form (single file + zip)
- [ ] Waiting/progress page polling `/status`
- [ ] Result page (single and batch)
- [ ] Search UI with type/status filters
