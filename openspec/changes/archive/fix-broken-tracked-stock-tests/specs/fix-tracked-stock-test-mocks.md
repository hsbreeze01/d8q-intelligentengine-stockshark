# Spec: Fix Tracked Stock Test Mock Configurations

## MODIFIED Requirements

### Requirement: test_add_success mock SHALL return per-connection fetchone results

The `test_add_success` test mock MUST provide distinct `get_mysql_connection` return values
for each DB connection opened during `add()`, so that the `_is_duplicate` check sees `None`
(no duplicate) while the final INSERT-then-SELECT sees the newly inserted row.

#### Scenario: add with provided stock_name opens 2 connections

- **Given** a `TrackedStockService` instance
- **And** `get_mysql_connection` is mocked with a `side_effect` function
- **When** `svc.add("603009", "北特科技", "科技", 1, "关注中")` is called
- **Then** connection 1 (opened by `_is_duplicate`) SHALL have `cursor.fetchone()` return `None`
- **And** connection 2 (opened by the INSERT + SELECT block) SHALL have `cursor.fetchone()` return the new row dict
- **And** the test SHALL pass without raising `ValueError`

### Requirement: test_batch_add_mixed mock SHALL sequence connections per stock operation

The `test_batch_add_mixed` test mock MUST provide the correct `fetchone` result for each
`get_mysql_connection` call across all three stocks in the batch, accounting for the fact
that each new-stock `add()` opens up to 3 connections (duplicate check, auto-fill, INSERT).

#### Scenario: batch add with 1 duplicate and 2 new stocks

- **Given** a `TrackedStockService` instance
- **And** `get_mysql_connection` is mocked with a `side_effect` function that returns a queue of connections
- **When** `svc.batch_add([{"stock_code":"000001"}, {"stock_code":"000002"}, {"stock_code":"603009"}])` is called
- **Then** the mock SHALL provide connections in this order:
  1. Connection for stock 000001 `_is_duplicate`: `fetchone` returns `{"id": 1}` → duplicate, ValueError caught, skip
  2. Connection for stock 000002 `_is_duplicate`: `fetchone` returns `None` → not duplicate
  3. Connection for stock 000002 `_auto_fill_stock_name`: `fetchone` returns `None` → fallback to stock code
  4. Connection for stock 000002 INSERT + SELECT: `fetchone` returns the new row → added
  5. Connection for stock 603009 `_is_duplicate`: `fetchone` returns `None` → not duplicate
  6. Connection for stock 603009 `_auto_fill_stock_name`: `fetchone` returns `None` → fallback to stock code
  7. Connection for stock 603009 INSERT + SELECT: `fetchone` returns the new row → added
- **And** `result["added"]` SHALL equal `2`
- **And** `result["skipped"]` SHALL equal `1`
