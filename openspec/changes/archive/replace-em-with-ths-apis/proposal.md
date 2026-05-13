# Proposal: Replace Blocked Eastmoney APIs with THS/Sina Alternatives

## Summary
Replace all `stock_board_*_em` and `stock_zh_a_spot_em` calls in `stockshark/data/akshare_data.py` and `stockshark/analysis/search_engine.py` with working THS and Sina alternatives. Add rate-limited data fetcher with in-memory cache.

## Motivation
The ECS server (47.99.57.152) cannot reach `push2.eastmoney.com` (TCP RST at network level). ALL akshare functions using eastmoney push2 API fail with RemoteDisconnected/timeout:
- `stock_board_industry_name_em` — BLOCKED
- `stock_board_industry_cons_em` — BLOCKED
- `stock_board_concept_name_em` — BLOCKED
- `stock_board_concept_cons_em` — BLOCKED
- `stock_zh_a_spot_em` — BLOCKED

This causes the recommend page 行业板块 tab to show 加载失败, and the 热门板块 sidebar to be empty.

All THS and Sina alternatives have been tested and confirmed working on this server:
- `stock_board_industry_summary_ths` — 0.2s, 90 rows
- `stock_board_concept_summary_ths` — 4.0s, 50 rows
- `stock_board_industry_name_ths` — 0.3s, 90 rows
- `stock_board_concept_name_ths` — 6.3s, 375 rows
- `stock_fund_flow_industry` — 0.3s, 90 rows
- `stock_sector_spot` — 0.1s, 49 rows

## Expected Behavior

### 1. AkShareData methods replaced
- `get_all_industries` — use `stock_board_industry_name_ths`
  - Returns list of industry names from THS (90 industries)
  - Columns: name, code

- `get_all_concepts` — use `stock_board_concept_name_ths`
  - Returns list of concept names from THS (375 concepts)
  - Columns: name, code

- `get_industry_stocks(industry_name)` — use `stock_board_industry_name_ths` for lookup, then `stock_board_industry_info_ths(symbol=name)` for detail
  - Returns industry detail with 10 KPIs
  - NOTE: Cannot return constituent stock list (no THS equivalent for cons_em). Return industry summary instead.

- `get_concept_stocks(concept_name)` — use `stock_board_concept_name_ths` for lookup, then `stock_board_concept_summary_ths` for matching concept detail
  - NOTE: Same limitation — no constituent stock list available via THS.

- `get_stock_quote(symbol)` — use `stock_zh_a_spot` (Sina) with code filtering
  - This fetches ALL stocks (~15s) but is the only working alternative
  - Cache the full result for 30 minutes

- `get_stock_concepts(symbol)` — mark as DEPRECATED, return empty list
  - Reverse lookup requires iterating all 375 concepts — impractical without EM

### 2. SearchEngine methods replaced
- `get_industries_summary(limit)` — use `stock_board_industry_summary_ths`
  - Returns rich data: 序号, 板块, 涨跌幅, 总成交量, 总成交额, 净流入, 上涨家数, 下跌家数, 均价, 领涨股, 领涨股-最新价, 领涨股-涨跌幅
  - Map to existing output format: name, change_pct, up_count, down_count, leading_stock, leading_change
  - Add new fields: volume, amount, net_flow, avg_price

- `get_concepts_summary(limit)` — use `stock_board_concept_summary_ths`
  - Returns: 日期, 概念名称, 驱动事件, 龙头股, 成分股数量
  - Map to: name, leading_stock, driver_event, stock_count

### 3. Rate-limited data fetcher
- Add `DataFetcher` class in `stockshark/data/fetcher.py`
- In-memory cache with configurable TTL (default: industry/concept lists 24h, summaries 30min, individual quotes 30min)
- Rate limit: minimum 1 second between API calls to same source
- Thread-safe (threading.Lock)
- On cache miss + rate limit wait: return stale cache if available, else wait
- Logging: cache hit/miss, API call duration

### 4. Column name mapping
THS columns use Chinese names that differ from EM. All replacement methods must:
- Map THS column names to the existing output dict format expected by SearchEngine and API routes
- Handle missing columns gracefully (default to 0 or empty string or None)
- Log column mapping warnings for debugging

## Out of Scope
- `stock_individual_info_em` in `get_stock_basic_info` — this still works (different EM endpoint)
- `stock_financial_analysis_indicator` in `get_stock_financial_data` — not push2
- `stock_zh_a_hist` in `get_stock_history_data` — not push2
- `stock_zh_valuation_baidu` in `get_stock_valuation_data` — Baidu source
- Constituent stock list — no working replacement available yet
- Frontend changes (factory templates) — not in scope for this change
- Database schema changes — not needed

## Files to Modify
1. `stockshark/data/akshare_data.py` — Replace EM calls with THS/Sina equivalents
2. `stockshark/analysis/search_engine.py` — Update summary methods to use THS
3. `stockshark/data/fetcher.py` — NEW: Rate-limited data fetcher with cache
4. `tests/test_akshare_ths.py` — NEW: Unit tests for replacement methods

## Constraints
- akshare version on server: 1.18.54 — all THS functions confirmed available
- Must not break existing API routes (factory to shark proxy chain)
- Output dict format must match what factory frontend expects (name, change_pct, leading_stock, etc.)
- All THS functions use `data.10jqka.com.cn` source (not blocked)
- `stock_zh_a_spot` (Sina) takes ~15s — must cache aggressively
