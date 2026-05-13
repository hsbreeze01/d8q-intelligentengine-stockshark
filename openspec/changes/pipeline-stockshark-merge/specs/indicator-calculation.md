# Delta Spec: 技术指标计算

## ADDED Requirements

### Requirement: TA-Lib 技术指标批量计算

StockShark SHALL 内置技术指标计算模块，基于已采集的 K 线数据计算常用技术指标并持久化。

#### Scenario: 计算单只股票的全部技术指标

- Given 股票代码 `600000` 在 `stock_data_daily` 表中有至少 60 条 K 线记录
- When 系统对该股票执行指标计算
- Then 系统 SHALL 计算以下指标：
  - MA（5, 10, 20, 60 日均线）
  - MACD（DIF, DEA, MACD 柱）
  - KDJ（K, D, J 值）
  - RSI（6, 12, 24 日）
  - BOLL（上轨、中轨、下轨）
- And 计算结果 SHALL 写入 `indicators_daily` 表
- And 写入时 SHALL 使用 `ON DUPLICATE KEY UPDATE` 保证幂等

#### Scenario: K 线数据不足时降级计算

- Given 股票代码 `600038` 在 `stock_data_daily` 表中仅有 25 条记录
- When 系统对该股票执行指标计算
- Then 系统 SHALL 跳过需要 60 日数据的指标（MA60、BOLL）
- And 系统 SHALL 正常计算仅需短期数据的指标（MA5, MA10, KDJ, RSI6）
- And 系统 SHALL 记录 WARNING 日志说明部分指标因数据不足被跳过

#### Scenario: 无 K 线数据时跳过

- Given 股票代码 `688001` 在 `stock_data_daily` 表中无任何记录
- When 系统对该股票执行指标计算
- Then 系统 SHALL 跳过该股票
- And 系统 SHALL 记录 WARNING 日志

### Requirement: indicators_daily 表结构

系统 SHALL 使用以下结构的 `indicators_daily` 表存储技术指标：

- `id` INT AUTO_INCREMENT PRIMARY KEY
- `stock_code` VARCHAR(10) NOT NULL
- `trade_date` DATE NOT NULL
- `ma5` DECIMAL(10,3), `ma10` DECIMAL(10,3), `ma20` DECIMAL(10,3), `ma60` DECIMAL(10,3)
- `macd_dif` DECIMAL(10,4), `macd_dea` DECIMAL(10,4), `macd_bar` DECIMAL(10,4)
- `kdj_k` DECIMAL(10,3), `kdj_d` DECIMAL(10,3), `kdj_j` DECIMAL(10,3)
- `rsi6` DECIMAL(10,3), `rsi12` DECIMAL(10,3), `rsi24` DECIMAL(10,3)
- `boll_upper` DECIMAL(10,3), `boll_middle` DECIMAL(10,3), `boll_lower` DECIMAL(10,3)
- `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP

UNIQUE KEY SHALL 为 `(stock_code, trade_date)`。

### Requirement: 增量指标计算

系统 SHALL 支持增量模式：仅计算 `stock_data_daily` 中新增日期的指标行，不重新计算全量历史。

#### Scenario: 增量指标计算

- Given 股票 `600000` 在 `indicators_daily` 中最新日期为 `2025-01-10`
- And `stock_data_daily` 中有 `2025-01-13` 到 `2025-01-17` 的新增 K 线
- When 系统对该股票执行增量指标计算
- Then 系统 SHALL 仅读取计算所需的历史窗口数据
- And 仅新增 `2025-01-13` 到 `2025-01-17` 的指标行
- And 不修改已有的指标数据
