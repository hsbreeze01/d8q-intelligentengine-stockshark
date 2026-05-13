# Tasks: Fix Broken Tracked Stock Tests

## 1. Fix mock configurations in test_tracked_stock_service.py

- [ ] **Fix `test_add_success` mock** — Replace `mock_get_conn.return_value = conn` with a `side_effect` factory that returns 2 connections: first with `fetchone=None` (for `_is_duplicate`), second with `fetchone=new_row` (for INSERT + SELECT). This follows the existing pattern in `test_add_auto_fill_name`.

- [ ] **Fix `test_batch_add_mixed` mock** — Replace the current `make_conn` with a queue-based factory that returns 7 connections in sequence: 1 for the duplicate stock's `_is_duplicate`, then 3 per new stock (duplicate check → auto-fill → INSERT+SELECT). Verify `result["added"] == 2` and `result["skipped"] == 1`.

- [ ] **Run full test suite and verify** — Execute `pytest tests/unit/test_tracked_stock_service.py -v` and confirm all 17 tests pass. Then run `ruff check tests/unit/test_tracked_stock_service.py` to confirm no lint issues.
