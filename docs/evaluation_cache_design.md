# 股票评估结论缓存与智能重新评估方案

> 版本: v1.0  
> 日期: 2026-04-10  
> 状态: 实施中

## 1. 背景与问题

`llm_analyzer.py` 的 `analyze_stock_comprehensive()` 每次调用都会：
1. 重新采集所有数据源（AkShare行情/财务 + 巨潮公告 + 洞见研报）
2. 重新调用 DeepSeek LLM 分析
3. 无任何缓存机制

导致：重复请求浪费 LLM API 调用费用和响应时间；同一股票短时间内多次请求得到的结论可能不一致。

## 2. 核心设计

### 2.1 评估结论存储

MongoDB `stock_evaluations` 集合，文档结构：

```json
{
  "stock_code": "603009",
  "scope": "all",
  "result": { /* LLM 分析结论完整 JSON */ },
  "data_fingerprint": {
    "price": 25.30,
    "change_pct": -1.2,
    "pe_ttm": 18.5,
    "pb": 2.1,
    "latest_announcement_date": "2026-04-08",
    "announcement_count": 5,
    "latest_report_date": "2026-04-05",
    "report_count": 3
  },
  "evaluated_at": "2026-04-10T15:30:00",
  "trigger_reason": "initial",
  "cached": false
}
```

索引：`(stock_code, scope)` 唯一索引，确保每个股票每个 scope 只保留最新评估。

### 2.2 重新评估触发条件

基于股票分析师经验设定，任一条件满足即触发重新评估：

| # | 触发条件 | 阈值 | 分析师依据 |
|---|---------|------|-----------|
| 1 | 价格大幅波动 | 日涨跌幅 ≥ 5% 或相对缓存价格变化 ≥ 8% | 短期技术面剧变，需重新评估风险 |
| 2 | 重大公告发布 | 新增公告含关键词：重组、增减持、业绩预告/快报、停复牌、分红、回购、诉讼、处罚 | 事件驱动型催化/风险 |
| 3 | 新研报发布 | 缓存后有新的券商研报发布 | 机构观点更新可能改变预期 |
| 4 | 估值指标异动 | PE 或 PB 相对缓存值变化 ≥ 15% | 估值面显著变化 |
| 5 | 财报更新 | 新财报期数据发布 | 基本面数据更新 |
| 6 | 时间过期（兜底） | short: 3天, mid: 7天, long: 30天, all: 7天 | 保证结论时效性 |

### 2.3 触发检测流程

```
请求评估(stock_code, scope)
  → 查询 MongoDB 最近一次评估
  → 无记录 → 全量评估 (trigger_reason="initial")
  → 有记录 → 轻量级触发检测:
      1. 时间过期检查
      2. 获取当前行情 → 对比价格/涨跌幅
      3. 获取最新公告标题 → 对比是否有新的重大公告
      4. 获取最新研报标题 → 对比日期
      5. 获取估值数据 → 对比 PE/PB
    → 任一触发 → 全量重新评估 → 存储新结论 (cached=false)
    → 均未触发 → 返回缓存结论 (cached=true)
```

### 2.4 关键设计决策

1. **触发检测轻量化**：只获取行情+公告标题+研报标题，不调用 LLM，成本极低
2. **触发后全量重评估**：一旦触发，重新执行完整的 `_gather_data` + `_build_prompt` + `_llm_call`，确保结论基于最新全量数据
3. **结果透明标注**：返回 `cached: true/false` 和 `trigger_reason`，调用方可感知
4. **数据指纹**：存储评估时的关键数据快照，用于精确判断数据是否真正变化

## 3. 涉及文件

| 文件 | 改动说明 |
|------|---------|
| `stockshark/analysis/evaluation_cache.py` | **新增** - 触发条件检测 + 缓存读写逻辑 |
| `stockshark/analysis/llm_analyzer.py` | 改造入口函数，集成缓存逻辑 |
| `stockshark/api/routes/analysis.py` | 响应增加 cached/trigger_reason 字段 |

## 4. 后续改进方向

- [ ] 触发阈值可配置化（通过 config 或数据库动态调整）
- [ ] 评估历史记录（保留历史版本，支持结论变化追踪）
- [ ] 分级触发：不同触发条件对应不同 scope 的重评估（如价格波动只触发 short 重评估）
- [ ] 批量预评估：定时任务在收盘后批量检测并预刷新热门股票的评估缓存
- [ ] 触发条件权重化：多个弱触发条件组合也可触发重评估

---

# 多源研报聚合与慧博投研接入方案

> 版本: v1.0
> 日期: 2026-04-13
> 状态: 已实施

## 1. 背景

原系统仅有洞见研报(djyanbao)和巨潮公告(cninfo)两个数据源。新增慧博投研(hibor.com.cn)作为第三个研报数据源，并提供按股票聚合查询能力。

## 2. 数据源

| 数据源 | 类型 | 获取方式 | 特点 |
|--------|------|---------|------|
| 洞见研报 djyanbao | 券商研报/机构调研 | REST API | 支持关键词搜索，数据全 |
| 慧博投研 hibor | 公司调研/券商研报 | HTML页面解析 | 搜索需登录，通过分类页面抓取+本地过滤 |
| 巨潮资讯 cninfo | 上市公司公告 | REST API | 官方公告源，最权威 |

## 3. 新增能力：按股票聚合查询研报

API: `GET /api/report/stock/<stock_code>?days=7&stock_name=xxx`

返回指定股票在过去N天内的所有研报和公告，来自三个数据源，去重后按日期排序。

返回结构:
```json
{
  "stock_code": "603019",
  "stock_name": "中科曙光",
  "period_days": 7,
  "reports": [{"title","org","date","summary","detail_url","source","category"}],
  "announcements": [{"title","date","detail_url","source"}],
  "sources_summary": {"djyanbao": 0, "hibor": 1, "cninfo": 2}
}
```

## 4. 涉及文件

| 文件 | 说明 |
|------|------|
| `stockshark/data/hibor_report.py` | **新增** - 慧博投研数据获取 |
| `stockshark/data/report_aggregator.py` | **新增** - 三源研报聚合器 |
| `stockshark/api/routes/report.py` | 新增 `/stock/<code>` 路由 |
| `stockshark/analysis/llm_analyzer.py` | 数据采集加入慧博源，Prompt加入慧博研报 |

## 5. 慧博接入限制与后续改进

- 慧博搜索功能需要登录，当前通过分类页面抓取+本地关键词过滤实现
- 分类页面只展示最新研报，冷门股票可能匹配不到
- [ ] 后续可接入慧博账号登录，使用搜索功能提高匹配率
- [ ] 可增加更多分类页面抓取（行业分析等）
- [ ] 可增加研报内容摘要提取（当前只有标题级信息）
