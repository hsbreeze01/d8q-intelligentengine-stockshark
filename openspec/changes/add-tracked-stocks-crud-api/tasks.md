# Tasks: Add Tracked Stocks CRUD API

## 1. Database Schema

- [x] 1.1 Add `tracked_stock` table DDL to `stockshark/data/database.py` (`_init_mysql` tables list)
  - Files: `stockshark/data/database.py`

## 2. Service Layer

- [x] 2.1 Create `stockshark/services/tracked_stock_service.py` with `TrackedStockService` class
  - Methods: `list_all`, `list_by_group`, `get_by_id`, `add`, `update`, `delete`, `batch_add`, `get_groups`
  - Use `stockshark/utils/database.py::get_mysql_connection()` for DB access
  - Auto-fill `stock_name` from `stock_basic_info` table when omitted
  - Files: `stockshark/services/tracked_stock_service.py`

## 3. API Routes

- [x] 3.1 Create `stockshark/api/routes/tracked_stocks.py` with `tracked_stocks_bp` Blueprint
  - Endpoints: list, add, update, delete, batch-add, groups
  - Follow existing route patterns (try/except, `{ "success": ..., "data": ... }`)
  - Files: `stockshark/api/routes/tracked_stocks.py`

- [ ] 3.2 Register `tracked_stocks_bp` in `stockshark/api/app.py`
  - Files: `stockshark/api/app.py`

## 4. Tests

- [ ] 4.1 Create `tests/unit/test_tracked_stock_service.py`
  - Mock `get_mysql_connection`; test all service methods including duplicate check, auto-fill, batch skip
  - Files: `tests/unit/test_tracked_stock_service.py`

- [ ] 4.2 Create `tests/unit/test_tracked_stocks_api.py`
  - Use Flask test client with mocked service; test all 6 endpoints + error cases
  - Files: `tests/unit/test_tracked_stocks_api.py`

## 5. Verification

- [ ] 5.1 Run `pytest` and `ruff check` on changed files; fix any failures
