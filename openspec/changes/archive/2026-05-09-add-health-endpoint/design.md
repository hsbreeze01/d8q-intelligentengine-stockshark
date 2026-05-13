# Design: Add /api/health endpoint

## Architecture Decision

Create a new route module `stockshark/api/routes/health.py` following the existing blueprint pattern used by all other route modules (analysis, search, supply_chain, etc.). Register the blueprint in `stockshark/api/app.py` under `{API_PREFIX}/health`.

**Rationale:** Consistency with existing project structure. All API routes live in `stockshark/api/routes/` as Blueprint modules and are registered in `create_app()`.

## Data Flow

1. Client → `GET /api/health`
2. Flask routes to `health_bp` handler
3. Handler returns `{"status": "ok", "timestamp": "<ISO 8601 UTC>"}`
4. No database or external service calls — purely in-process response.

## Files to Create

- `stockshark/api/routes/health.py` — new blueprint with single `GET /` handler returning status + timestamp

## Files to Modify

- `stockshark/api/app.py` — import and register `health_bp` at `{API_PREFIX}/health`

## Notes

- The existing `/health` route (defined inline in `app.py`) returns `timestamp` from query params. The new `/api/health` endpoint generates the timestamp server-side using `datetime.utcnow().isoformat() + "Z"`.
- The two endpoints serve different purposes: `/health` is a legacy root-level check; `/api/health` follows the versioned API convention.
