# Tasks: Add /api/health endpoint

## 1. Health Endpoint Implementation

- [x] Create `stockshark/api/routes/health.py` — Flask blueprint with `GET /` returning `{"status": "ok", "timestamp": "<UTC ISO 8601>"}` and HTTP 200
- [x] Register `health_bp` in `stockshark/api/app.py` — import the blueprint and register it at `{API_PREFIX}/health`

## 2. Verification

- [x] Run tests to confirm existing routes still pass and no regressions introduced
