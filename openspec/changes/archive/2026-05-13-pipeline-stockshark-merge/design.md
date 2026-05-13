# Design: Pipeline-StockShark 融合方案

## 架构决策

### 1. 新增 pipeline 模块（而非分散到现有模块）

**决策**：在 `stockshark/` 下新增 `pipeline/` 子包，集中管理 K 线采集、指标计算、daemon 调度的逻辑。

**理由**：
- pipeline 职责与现有 `data/crawler.py`（东财单次采集）不同，pipeline 需要增量逻辑、降级、批量调度
- 与现有 `analysis/` 模块解耦，analysis 负责 LLM 分析，pipeline 负责数值计算
- 便于独立测试和后续可能的再次拆分

### 2. 数据源抽象（策略模式）

**决策**：K 线采集通过 `KLineFetcher` 基类 + `AkshareEastmoneyFetcher` / `AkshareSinaFetcher` 两个实现，外部调用不关心数据源。

**理由**：
- akshare 的东财接口 `stock_zh_a_hist` 和新浪接口 `stock_zh_a_daily` 参数和返回格式不同，需要适配层
- 策略模式支持未来扩展其他数据源（如 tuShare）

### 3. TA-Lib vs pandas-ta

**决策**：优先使用 `pandas-ta`（纯 Python），不依赖 TA-Lib C 库。

**理由**：
- TA-Lib C 库需要系统级安装（`libta-lib-dev`），在目标服务器上增加部署复杂度
- `pandas-ta` 纯 Python，pip install 即可，且覆盖全部所需指标
- 对性能影响可忽略（计算量不大）

### 4. APScheduler 集成到 Flask

**决策**：使用 `APScheduler` 的 `BackgroundScheduler`，在 `create_app()` 中初始化，与 Flask 共享进程。

**理由**：
- 无需额外进程，不增加内存占用
- 共享 Flask 应用上下文（数据库连接等）
- 与 proposal 中"不增实体"原则一致

### 5. 数据表复用

**决策**：直接使用 compass-data-pipeline 已创建的 `stock_data_daily` 和 `indicators_daily` 表，不新建表。

**理由**：
- compass 已经在读取这两个表，表结构不变可无缝切换
- 避免数据迁移

## 数据流

```
                     ┌─────────────────────┐
                     │   APScheduler       │
                     │  (Flask 内置)        │
                     └─────────┬───────────┘
                               │ cron 15:30
                               ▼
                     ┌─────────────────────┐
                     │ tracked_stock 表    │
                     │ (采集股票列表)       │
                     └─────────┬───────────┘
                               │
                               ▼
              ┌────────────────────────────────┐
              │      KLineCollector             │
              │  1. 查询 stock_data_daily 最新日│
              │  2. 东财采集 → Sina 降级         │
              │  3. 写入 stock_data_daily        │
              └────────────────┬───────────────┘
                               │ cron 15:45
                               ▼
              ┌────────────────────────────────┐
              │    IndicatorCalculator          │
              │  1. 读取 K 线数据               │
              │  2. pandas-ta 计算 MA/MACD/KDJ  │
              │  3. 写入 indicators_daily        │
              └────────────────┬───────────────┘
                               │
                               ▼
              ┌────────────────────────────────┐
              │    Pipeline API Routes          │
              │  /pipeline/kline                │
              │  /pipeline/indicators            │
              │  /pipeline/stock-data            │
              │  /pipeline/collect (手动触发)    │
              │  /pipeline/status                │
              └────────────────────────────────┘
                               │
                               ▼
                      外部消费者 (compass)
```

## 需要新增的文件

| 文件路径 | 职责 |
|---------|------|
| `stockshark/pipeline/__init__.py` | pipeline 包初始化 |
| `stockshark/pipeline/kline_fetcher.py` | K 线数据源抽象（东财 + Sina） |
| `stockshark/pipeline/kline_collector.py` | K 线增量采集（读取关注列表、降级逻辑） |
| `stockshark/pipeline/indicator_calculator.py` | 技术指标计算（MA/MACD/KDJ/RSI/BOLL） |
| `stockshark/pipeline/daemon.py` | APScheduler daemon 管理 |
| `stockshark/pipeline/tables.py` | stock_data_daily / indicators_daily 建表和 DAO |
| `stockshark/api/routes/pipeline.py` | pipeline 相关 API 路由 |

## 需要修改的文件

| 文件路径 | 修改内容 |
|---------|---------|
| `stockshark/api/app.py` | 注册 pipeline_bp blueprint；create_app 中初始化 daemon |
| `stockshark/config.py` | 新增 DAEMON_ENABLED、COLLECT_CRON_HOUR/MINUTE 等配置项 |
| `requirements.txt` | 新增 `apscheduler`、`pandas-ta` 依赖 |
| `pyproject.toml` | 同步新增依赖 |

## 不修改的文件

- `stockshark/data/` 下现有文件 — 保持东财采集能力不变
- `stockshark/analysis/` — LLM 分析逻辑不变
- `stockshark/web/templates/` — 无前端变更
- 现有 API 路由 — 不破坏现有接口
