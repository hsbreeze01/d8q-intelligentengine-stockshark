# Delta Spec: K线数据采集（Sina 数据源 + 增量采集）

## ADDED Requirements

### Requirement: Sina 数据源 K线采集

StockShark 的数据采集层 SHALL 支持通过 akshare `stock_zh_a_daily` 接口获取新浪数据源的 A 股日 K 线数据，作为东财数据源（`stock_zh_a_hist`）的降级备选。

#### Scenario: 使用 Sina 数据源采集单只股票 K 线

- Given 一只股票代码 `sh600000`
- And 调用 K 线采集函数并指定数据源为 `sina`
- When 系统执行采集
- Then 系统 SHALL 通过 `stock_zh_a_daily(symbol="sh600000", adjust="qfq")` 获取前复权日 K 线
- And 返回的数据 SHALL 包含字段: `date`, `open`, `high`, `low`, `close`, `volume`
- And 数据 SHALL 写入 `stock_data_daily` 表

#### Scenario: 数据源自动降级

- Given 股票代码 `600000`
- And 东财数据源（`stock_zh_a_hist`）采集失败抛出异常
- When 系统执行 K 线采集
- Then 系统 SHALL 自动切换到 Sina 数据源重试
- And Sina 采集成功后 SHALL 正常返回数据
- And 系统 SHALL 记录一条 WARNING 级别日志说明发生了降级

#### Scenario: 所有数据源均不可用

- Given 股票代码 `600000`
- And 东财数据源和 Sina 数据源均采集失败
- When 系统执行 K 线采集
- Then 系统 SHALL 返回错误信息，包含两条数据源的失败原因
- And 系统 SHALL 记录 ERROR 级别日志

### Requirement: 增量 K 线采集

StockShark SHALL 支持增量采集模式，仅获取数据库中最新日期之后的新数据。

#### Scenario: 首次采集全量数据

- Given 股票代码 `600000`
- And `stock_data_daily` 表中无该股票的任何记录
- When 系统执行增量采集
- Then 系统 SHALL 获取该股票近 N 个交易日的日 K 线数据（N 由配置决定，默认 120）
- And 所有数据 SHALL 写入 `stock_data_daily` 表

#### Scenario: 增量追加新数据

- Given 股票代码 `600000`
- And `stock_data_daily` 表中最新记录日期为 `2025-01-10`
- When 系统执行增量采集
- Then 系统 SHALL 仅获取 `2025-01-10` 之后的 K 线数据
- And 新获取的数据 SHALL 追加写入 `stock_data_daily` 表
- And 系统 SHALL 不覆盖已有数据

#### Scenario: 批量增量采集多只股票

- Given 关注列表中有 5 只股票
- When 系统执行批量增量采集
- Then 系统 SHALL 依次对每只股票执行增量采集
- And 每只股票采集失败 SHALL 不影响其余股票的采集
- And 系统 SHALL 返回汇总报告（成功数、失败数、失败股票列表）

### Requirement: stock_data_daily 表结构

系统 SHALL 使用以下结构的 `stock_data_daily` 表存储 K 线数据：

- `id` INT AUTO_INCREMENT PRIMARY KEY
- `stock_code` VARCHAR(10) NOT NULL — 股票代码
- `trade_date` DATE NOT NULL — 交易日期
- `open` DECIMAL(10,3) — 开盘价
- `high` DECIMAL(10,3) — 最高价
- `low` DECIMAL(10,3) — 最低价
- `close` DECIMAL(10,3) — 收盘价
- `volume` BIGINT — 成交量
- `amount` DECIMAL(20,3) — 成交额（可选）
- `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP

UNIQUE KEY SHALL 为 `(stock_code, trade_date)`，确保同一股票同一日期只有一条记录。
