# Delta Spec: Tracked Stocks CRUD API

## ADDED Requirements

### Requirement: Tracked Stock Data Model

The system SHALL persist a `tracked_stock` entity in MySQL with the following fields:
- `id` — auto-increment primary key
- `stock_code` — non-null VARCHAR(20), the A-share code
- `stock_name` — non-null VARCHAR(50), the display name
- `group_name` — nullable VARCHAR(50), for logical grouping (e.g. "科技", "银行")
- `sort_order` — non-null INT default 0, controlling display ordering
- `notes` — nullable TEXT, free-form user notes
- `created_at` / `updated_at` — timestamps

A unique constraint MUST exist on `stock_code` so that a code can only be tracked once.

The system SHALL create this table during `DatabaseManager.init_database()` alongside existing tables.

#### Scenario: table created on app startup

- **Given** the MySQL database is reachable
- **When** the application starts and `init_database()` runs
- **Then** the `tracked_stock` table exists with the columns, types and unique constraint described above

#### Scenario: duplicate stock_code rejected by DB

- **Given** a stock with code `000001` is already tracked
- **When** another insert for code `000001` is attempted at the raw SQL level
- **Then** the database rejects the insert with a duplicate-key error

---

### Requirement: List Tracked Stocks

The system SHALL expose `GET /api/tracked-stocks` that returns all tracked stocks ordered by `sort_order` ascending, then `created_at` ascending.

The response JSON MUST follow the project convention `{ "success": true, "data": [...] }`.

Each item in `data` SHALL contain: `id`, `stock_code`, `stock_name`, `group_name`, `sort_order`, `notes`, `created_at`, `updated_at`.

Optional query parameters:
- `group_name` — filter by group (exact match)

#### Scenario: list all tracked stocks

- **Given** the database contains 3 tracked stocks
- **When** a client sends `GET /api/tracked-stocks`
- **Then** the response status is 200, `success` is `true`, and `data` is an array of 3 items sorted by `sort_order`

#### Scenario: filter by group

- **Given** 2 tracked stocks belong to group "科技" and 1 belongs to "银行"
- **When** a client sends `GET /api/tracked-stocks?group_name=科技`
- **Then** the response `data` array contains exactly 2 items whose `group_name` is "科技"

#### Scenario: empty list

- **Given** no tracked stocks exist
- **When** a client sends `GET /api/tracked-stocks`
- **Then** the response status is 200, `success` is `true`, and `data` is an empty array

---

### Requirement: Add Tracked Stock

The system SHALL expose `POST /api/tracked-stocks` with JSON body containing `stock_code` (required) and optionally `stock_name`, `group_name`, `sort_order`, `notes`.

If `stock_name` is omitted, the system SHOULD auto-fill it from `stock_basic_info` table (by `symbol`); if not found, it MUST use `stock_code` as fallback.

If the `stock_code` is already tracked, the API SHALL return 409 with `{ "success": false, "error": "该股票已在关注列表中" }`.

On success the response SHALL be 201 with `{ "success": true, "data": { ...new record } }`.

#### Scenario: add a new tracked stock with full fields

- **Given** no tracked stock with code `603009` exists
- **When** a client sends `POST /api/tracked-stocks` with body `{ "stock_code": "603009", "stock_name": "北特科技", "group_name": "科技", "sort_order": 1, "notes": "关注中" }`
- **Then** the response status is 201, `success` is `true`, and `data.stock_code` is `"603009"`

#### Scenario: add tracked stock auto-filling name from DB

- **Given** `stock_basic_info` contains symbol `000001` with name `平安银行`, and `000001` is not yet tracked
- **When** a client sends `POST /api/tracked-stocks` with body `{ "stock_code": "000001" }`
- **Then** the response status is 201 and `data.stock_name` is `"平安银行"`

#### Scenario: add duplicate tracked stock

- **Given** stock code `000001` is already tracked
- **When** a client sends `POST /api/tracked-stocks` with body `{ "stock_code": "000001" }`
- **Then** the response status is 409, `success` is `false`, and `error` indicates duplicate

#### Scenario: missing required stock_code

- **Given** any state
- **When** a client sends `POST /api/tracked-stocks` with body `{}`
- **Then** the response status is 400, `success` is `false`, and `error` indicates missing parameter

---

### Requirement: Update Tracked Stock

The system SHALL expose `PUT /api/tracked-stocks/<id>` with JSON body containing any subset of `stock_name`, `group_name`, `sort_order`, `notes`.

The `stock_code` field MUST NOT be updatable.

If the tracked stock with given `id` does not exist, the API SHALL return 404 with `{ "success": false, "error": "关注股票不存在" }`.

On success the response SHALL be 200 with `{ "success": true, "data": { ...updated record } }`.

#### Scenario: update group and notes

- **Given** a tracked stock with id 5 exists
- **When** a client sends `PUT /api/tracked-stocks/5` with body `{ "group_name": "金融", "notes": "重点关注" }`
- **Then** the response status is 200, `data.group_name` is `"金融"`, and `data.notes` is `"重点关注"`

#### Scenario: update non-existent tracked stock

- **Given** no tracked stock with id 999 exists
- **When** a client sends `PUT /api/tracked-stocks/999` with body `{ "notes": "test" }`
- **Then** the response status is 404, `success` is `false`

---

### Requirement: Delete Tracked Stock

The system SHALL expose `DELETE /api/tracked-stocks/<id>`.

If the tracked stock with given `id` does not exist, the API SHALL return 404.

On success the response SHALL be 200 with `{ "success": true, "message": "删除成功" }`.

#### Scenario: delete existing tracked stock

- **Given** a tracked stock with id 3 exists
- **When** a client sends `DELETE /api/tracked-stocks/3`
- **Then** the response status is 200, `success` is `true`, and subsequent `GET /api/tracked-stocks` no longer contains id 3

#### Scenario: delete non-existent tracked stock

- **Given** no tracked stock with id 999 exists
- **When** a client sends `DELETE /api/tracked-stocks/999`
- **Then** the response status is 404, `success` is `false`

---

### Requirement: Batch Add Tracked Stocks

The system SHALL expose `POST /api/tracked-stocks/batch` with JSON body `{ "stocks": [ {"stock_code": "...", ...}, ... ] }`.

For each item, the same validation and auto-fill rules apply as the single add endpoint.

Already-tracked codes SHALL be silently skipped (not treated as errors).

The response SHALL be 200 with `{ "success": true, "data": { "added": <count>, "skipped": <count> } }`.

#### Scenario: batch add with mixed new and duplicate codes

- **Given** stock `000001` is already tracked, and `000002` and `603009` are not
- **When** a client sends `POST /api/tracked-stocks/batch` with body `{ "stocks": [ {"stock_code": "000001"}, {"stock_code": "000002"}, {"stock_code": "603009"} ] }`
- **Then** the response status is 200, `data.added` is 2, `data.skipped` is 1

#### Scenario: batch add with missing stocks array

- **Given** any state
- **When** a client sends `POST /api/tracked-stocks/batch` with body `{}`
- **Then** the response status is 400, `success` is `false`

---

### Requirement: Get Distinct Group Names

The system SHALL expose `GET /api/tracked-stocks/groups` that returns all distinct `group_name` values (non-null) from tracked stocks.

The response SHALL be 200 with `{ "success": true, "data": ["科技", "银行", ...] }`.

#### Scenario: list groups

- **Given** tracked stocks have groups "科技", "银行", "科技" (duplicate), and one with null group
- **When** a client sends `GET /api/tracked-stocks/groups`
- **Then** the response status is 200 and `data` is `["科技", "银行"]` (deduplicated, null excluded)
