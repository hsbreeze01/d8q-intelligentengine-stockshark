# Tasks: Pipeline-StockShark 融合

## 1. 基础设施

- [x] 1.1 新增 `stockshark/pipeline/__init__.py` 和 `stockshark/pipeline/tables.py`，定义 `stock_data_daily`、`indicators_daily` 表的 CREATE TABLE 和基础 DAO 操作（upsert、query_latest、query_range）
- [x] 1.2 在 `stockshark/config.py` 中增加 daemon 相关配置项（`DAEMON_ENABLED`、`COLLECT_CRON_HOUR`、`COLLECT_CRON_MINUTE`、`INDICATOR_CRON_OFFSET_MINUTES`、`INITIAL_KLINE_DAYS`）
- [x] 1.3 在 `requirements.txt` 和 `pyproject.toml` 中新增 `apscheduler>=3.10.0` 和 `pandas-ta>=0.3.14` 依赖

## 2. K 线采集模块

- [x] 2.1 新增 `stockshark/pipeline/kline_fetcher.py`，实现 `AkshareEastmoneyFetcher`（封装 `stock_zh_a_hist`）和 `AkshareSinaFetcher`（封装 `stock_zh_a_daily`），统一返回 DataFrame 格式（列: date/open/high/low/close/volume）
- [x] 2.2 新增 `stockshark/pipeline/kline_collector.py`，实现 `KLineCollector` 类：从 `tracked_stock` 获取股票列表 → 查询每只股票最新日期 → 调用 fetcher 增量采集 → upsert 到 `stock_data_daily`；包含东财→Sina 自动降级逻辑和批量采集汇总报告

## 3. 技术指标计算模块

- [x] 3.1 新增 `stockshark/pipeline/indicator_calculator.py`，使用 pandas-ta 计算 MA(5/10/20/60)、MACD(DIF/DEA/bar)、KDJ(K/D/J)、RSI(6/12/24)、BOLL(upper/middle/lower)，支持数据不足时降级计算，结果 upsert 到 `indicators_daily`

## 4. Daemon 调度模块

- [x] 4.1 新增 `stockshark/pipeline/daemon.py`，实现 `PipelineDaemon` 类（基于 APScheduler BackgroundScheduler），注册增量采集任务（读取 tracked_stock → KLineCollector）和增量指标计算任务（KLineCollector 完成 → IndicatorCalculator），支持启动/停止/状态查询
- [x] 4.2 修改 `stockshark/api/app.py`，在 `create_app()` 中根据 `DAEMON_ENABLED` 配置初始化 `PipelineDaemon`；注册 `pipeline_bp` blueprint 到 `/api/v1/pipeline`

## 5. Pipeline API 路由

- [x] 5.1 新增 `stockshark/api/routes/pipeline.py`，实现以下端点：
  - `GET /api/v1/pipeline/kline` — 查询 K 线数据（stock_code 必填，limit/start_date/end_date 可选）
  - `GET /api/v1/pipeline/indicators` — 查询技术指标（同上参数）
  - `GET /api/v1/pipeline/stock-data` — K 线 + 指标合并查询
  - `POST /api/v1/pipeline/collect` — 手动触发增量采集
  - `POST /api/v1/pipeline/run-indicators` — 手动触发指标计算
  - `GET /api/v1/pipeline/status` — daemon 状态查询

## 6. 测试

- [x] 6.1 新增 `tests/unit/test_kline_fetcher.py` 和 `tests/unit/test_kline_collector.py`，覆盖数据源降级、增量采集、批量汇总等核心逻辑（mock akshare 和数据库调用）
- [x] 6.2 新增 `tests/unit/test_indicator_calculator.py`，覆盖全量计算、数据不足降级、增量计算场景
- [x] 6.3 新增 `tests/unit/test_pipeline_api.py`，覆盖所有 pipeline API 端点的参数校验和数据返回
