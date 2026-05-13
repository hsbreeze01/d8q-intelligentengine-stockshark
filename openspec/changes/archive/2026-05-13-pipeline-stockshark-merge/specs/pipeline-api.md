# Delta Spec: Pipeline 数据 API

## ADDED Requirements

### Requirement: K 线数据查询 API

StockShark SHALL 提供 API 端点供外部服务（如 compass）查询 `stock_data_daily` 表中的 K 线数据。

#### Scenario: 查询单只股票 K 线

- Given `stock_data_daily` 表中有 `600000` 的 K 线数据
- When 通过 `GET /api/v1/pipeline/kline?stock_code=600000&limit=60` 查询
- Then 系统 SHALL 返回最近 60 个交易日的 K 线数据
- And 返回格式为 JSON 数组，每个元素包含: `trade_date`, `open`, `high`, `low`, `close`, `volume`
- And 数据 SHALL 按 `trade_date` 升序排列

#### Scenario: 查询指定日期范围的 K 线

- Given `stock_data_daily` 表中有 `600000` 的 K 线数据
- When 通过 `GET /api/v1/pipeline/kline?stock_code=600000&start_date=2025-01-01&end_date=2025-01-31` 查询
- Then 系统 SHALL 返回指定日期范围内的 K 线数据
- And `start_date` 和 `end_date` 均为可选参数

#### Scenario: 股票无数据

- Given `stock_data_daily` 表中无 `688999` 的任何记录
- When 通过 `GET /api/v1/pipeline/kline?stock_code=688999` 查询
- Then 系统 SHALL 返回 HTTP 200，`data` 为空数组

### Requirement: 技术指标查询 API

#### Scenario: 查询单只股票技术指标

- Given `indicators_daily` 表中有 `600000` 的指标数据
- When 通过 `GET /api/v1/pipeline/indicators?stock_code=600000&limit=60` 查询
- Then 系统 SHALL 返回最近 60 个交易日的全部技术指标
- And 返回格式为 JSON 数组，按 `trade_date` 升序排列

### Requirement: 综合 Data API

#### Scenario: 查询单只股票 K 线 + 指标合并数据

- When 通过 `GET /api/v1/pipeline/stock-data?stock_code=600000&limit=120` 查询
- Then 系统 SHALL 返回 K 线和技术指标的合并结果
- And 每个交易日为一个 JSON 对象，包含 K 线字段和所有指标字段
- And 若某日无指标数据，指标字段 SHALL 为 `null`
