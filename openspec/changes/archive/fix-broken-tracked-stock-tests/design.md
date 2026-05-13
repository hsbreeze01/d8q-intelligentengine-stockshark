# Design: Fix Broken Tracked Stock Tests

## Problem Analysis

Two tests in `tests/unit/test_tracked_stock_service.py` fail because their mock setup doesn't account for the fact that `add()` calls `get_mysql_connection()` **multiple times** (once in `_is_duplicate`, optionally once in `_auto_fill_stock_name`, and once for the INSERT+SELECT block).

Both tests set `mock_get_conn.return_value = conn` with a single `fetchone_result`, which causes every connection to return the same `fetchone` value. This makes `_is_duplicate` see a non-None result and incorrectly raise `ValueError("该股票已在关注列表中")`.

### Call flow for `add()` when `stock_name` is provided

```
add(stock_code, stock_name, ...)
  ├─ _is_duplicate(stock_code)
  │    └─ conn1 = get_mysql_connection()  ← fetchone must return None
  ├─ _auto_fill_stock_name(stock_code, stock_name)
  │    └─ returns immediately (stock_name is truthy, no DB call)
  └─ conn2 = get_mysql_connection()       ← fetchone must return new_row
       INSERT + SELECT
```

### Call flow for `add()` when `stock_name` is NOT provided

```
add(stock_code, None, ...)
  ├─ _is_duplicate(stock_code)
  │    └─ conn1 = get_mysql_connection()  ← fetchone must return None
  ├─ _auto_fill_stock_name(stock_code, None)
  │    └─ conn2 = get_mysql_connection()  ← fetchone returns name or None
  └─ conn3 = get_mysql_connection()       ← fetchone must return new_row
       INSERT + SELECT
```

## Solution

Use `mock_get_conn.side_effect` with a factory function (the same pattern already used by `test_add_auto_fill_name`, `test_update_success`, etc.) to return a distinct mock connection for each `get_mysql_connection()` call, with the correct `fetchone` value.

### For `test_add_success`

Change from `return_value` to `side_effect`:
- Connection 1 (for `_is_duplicate`): `fetchone` returns `None`
- Connection 2 (for INSERT + SELECT): `fetchone` returns `new_row`

Since `stock_name="北特科技"` is provided, `_auto_fill_stock_name` short-circuits — only 2 connections needed.

### For `test_batch_add_mixed`

Build a flat queue of `(fetchone_result, lastrowid)` tuples and consume one per `get_mysql_connection()` call:

| # | Stock    | Method called by       | fetchone result                          |
|---|----------|------------------------|------------------------------------------|
| 1 | 000001   | `_is_duplicate`        | `{"id": 1}` → duplicate, skip            |
| 2 | 000002   | `_is_duplicate`        | `None`                                   |
| 3 | 000002   | `_auto_fill_stock_name`| `None` → fallback to code                |
| 4 | 000002   | INSERT + SELECT        | `{"id": 2, "stock_code": "000002", ...}` |
| 5 | 603009   | `_is_duplicate`        | `None`                                   |
| 6 | 603009   | `_auto_fill_stock_name`| `None` → fallback to code                |
| 7 | 603009   | INSERT + SELECT        | `{"id": 3, "stock_code": "603009", ...}` |

The factory function pops from this queue for each call.

## Files to Modify

| File | Change |
|------|--------|
| `tests/unit/test_tracked_stock_service.py` | Fix mock in `test_add_success` and `test_batch_add_mixed` |

No production code changes.
