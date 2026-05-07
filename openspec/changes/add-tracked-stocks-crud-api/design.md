# Design: Add Tracked Stocks CRUD API

## Overview

Add a "tracked stocks" (自选股/关注股票) CRUD feature so users can maintain a personal watchlist of A-share stocks, grouped and ordered. This follows the existing project patterns: Flask Blueprint routes → service layer → MySQL via `pymysql` / `get_mysql_connection()`.

## Architecture Decisions

| Decision | Rationale |
|---|---|
| New MySQL table `tracked_stock` | Consistent with existing `stock_basic`, `theme`, `stock_theme` tables already created in `DatabaseManager._init_mysql()`. No new DB technology. |
| Dedicated service class `TrackedStockService` | Mirrors `StockService` pattern; keeps route handlers thin, logic testable. |
| New Blueprint `tracked_stocks_bp` at `/api/tracked-stocks` | Follows the existing convention: each domain has its own Blueprint file under `stockshark/api/routes/`. |
| Auto-fill `stock_name` from `stock_basic_info` table | Avoids requiring the caller to know the name; falls back gracefully. |
| `sort_order` as explicit integer | Simpler than positional re-ordering; client can assign arbitrary integers. |

## Data Flow

```
Client
  │
  ▼
Flask Blueprint (stockshark/api/routes/tracked_stocks.py)
  │  validates request JSON / query params
  ▼
TrackedStockService (stockshark/services/tracked_stock_service.py)
  │  business logic: duplicate check, auto-fill name, batch dedup
  ▼
MySQL (tracked_stock table, stock_basic_info table for name lookup)
```

## Database Schema

```sql
CREATE TABLE IF NOT EXISTS tracked_stock (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    stock_code    VARCHAR(20)  NOT NULL UNIQUE COMMENT '股票代码',
    stock_name    VARCHAR(50)  NOT NULL COMMENT '股票名称',
    group_name    VARCHAR(50)  DEFAULT NULL COMMENT '分组名称',
    sort_order    INT          NOT NULL DEFAULT 0 COMMENT '排序权重',
    notes         TEXT         DEFAULT NULL COMMENT '备注',
    created_at    DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_group_name (group_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='关注股票表';
```

Added to the `tables` list in `DatabaseManager._init_mysql()`.

## Files to Create / Modify

| Action | File | Description |
|--------|------|-------------|
| **CREATE** | `stockshark/api/routes/tracked_stocks.py` | Blueprint with 6 route handlers: list, add, update, delete, batch-add, groups |
| **CREATE** | `stockshark/services/tracked_stock_service.py` | Service class with DB operations for tracked_stock table |
| **MODIFY** | `stockshark/api/app.py` | Import and register `tracked_stocks_bp` at `/api/tracked-stocks` |
| **MODIFY** | `stockshark/data/database.py` | Add `tracked_stock` table DDL to `_init_mysql()` table list |
| **CREATE** | `tests/unit/test_tracked_stock_service.py` | Unit tests for service layer (mock DB) |
| **CREATE** | `tests/unit/test_tracked_stocks_api.py` | Unit tests for API routes using Flask test client (mock service) |

## API Endpoints Summary

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/tracked-stocks` | List all tracked stocks (optional `?group_name=` filter) |
| POST | `/api/tracked-stocks` | Add single tracked stock |
| POST | `/api/tracked-stocks/batch` | Batch add tracked stocks |
| PUT | `/api/tracked-stocks/<id>` | Update tracked stock |
| DELETE | `/api/tracked-stocks/<id>` | Delete tracked stock |
| GET | `/api/tracked-stocks/groups` | List distinct group names |

## Error Handling

Follows existing project convention: all errors return `{ "success": false, "error": "<message>" }` with appropriate HTTP status codes (400, 404, 409, 500).
