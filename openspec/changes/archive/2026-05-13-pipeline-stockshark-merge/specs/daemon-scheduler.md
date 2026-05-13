# Delta Spec: Daemon 调度模式

## ADDED Requirements

### Requirement: Daemon 定时调度

StockShark SHALL 支持 daemon 模式，通过 APScheduler 在 Flask 应用内运行定时任务，完成增量 K 线采集和技术指标计算。

#### Scenario: 启动 daemon 模式

- Given StockShark 配置中 `DAEMON_ENABLED=True`
- When Flask 应用启动
- Then 系统 SHALL 初始化 APScheduler
- And 注册以下定时任务：
  - 增量 K 线采集（cron: 周一至周五 15:30）
  - 增量指标计算（cron: 周一至周五 15:45，在 K 线采集完成后）
- And Scheduler SHALL 使用 `BackgroundScheduler` 不阻塞 Flask 主线程

#### Scenario: daemon 模式未启用

- Given StockShark 配置中 `DAEMON_ENABLED=False`（或未设置）
- When Flask 应用启动
- Then 系统 SHALL 不初始化 APScheduler
- And Flask 应用正常运行 API 服务

#### Scenario: 单次手动触发采集

- Given daemon 模式已启动
- When 通过 API 端点 `POST /api/v1/pipeline/collect` 触发手动采集
- Then 系统 SHALL 立即执行一次全量关注列表的增量 K 线采集
- And 返回采集结果汇总（成功数、失败数）

#### Scenario: 单次手动触发指标计算

- Given daemon 模式已启动
- When 通过 API 端点 `POST /api/v1/pipeline/indicators` 触发手动计算
- Then 系统 SHALL 立即执行一次全量关注列表的增量指标计算
- And 返回计算结果汇总

### Requirement: 采集任务使用关注列表

定时采集任务 SHALL 从 `tracked_stock` 表获取股票列表作为采集范围。

#### Scenario: 从关注列表获取采集范围

- Given `tracked_stock` 表中有 15 只股票
- When 定时采集任务触发
- Then 系统 SHALL 读取 `tracked_stock` 表的全部股票代码
- And 对每只股票执行增量 K 线采集
- And 采集过程中单只股票失败 SHALL 不中断其余股票

### Requirement: Daemon 状态查询 API

#### Scenario: 查询 daemon 状态

- When 通过 `GET /api/v1/pipeline/status` 查询
- Then 系统 SHALL 返回：
  - `daemon_enabled`: daemon 是否启用
  - `scheduler_running`: scheduler 是否运行中
  - `last_collect_time`: 上次采集完成时间（ISO 8601）
  - `last_indicator_time`: 上次指标计算完成时间
  - `tracked_stock_count`: 当前关注列表股票数量
