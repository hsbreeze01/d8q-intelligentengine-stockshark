# 股票分析系统 - API测试指南

## 概述

本测试脚本用于验证股票分析系统的三个核心功能：

1. **单个股票分析** - 提供股票代码，按照设定规则分析，给出投资价值和风险评估
2. **主题/行业股票筛选** - 基于主题或行业查找相关股票，支持多条件过滤和排序
3. **场景/新闻驱动分析** - 输入场景或新闻，列举相关供应链企业，标记上市状态和控股关系

## 前置条件

1. 确保Python虚拟环境已激活
2. 安装必要的依赖包：
   ```bash
   pip install flask requests
   ```

3. 启动API服务器：
   ```bash
   /Users/lancer.zhang/ProjectNIO/d8q-intelligentengine-stockshark/venv/bin/python api/api_server.py
   ```

## 测试脚本使用

### 快速测试

运行完整的API测试套件：

```bash
./test_api_simple.sh
```

### 手动测试各个功能

#### 需求1: 单个股票分析

**1.1 健康检查**
```bash
curl http://localhost:5000/health
```

**1.2 股票分析 - 平安银行(000001)**
```bash
curl -X POST http://localhost:5000/api/analysis/stock/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "000001",
    "analysis_type": "comprehensive"
  }'
```

**1.3 获取股票行情**
```bash
curl http://localhost:5000/api/analysis/stock/quote?symbol=000001
```

#### 需求2: 主题/行业股票筛选

**2.1 获取所有行业列表**
```bash
curl http://localhost:5000/api/search/industries
```

**2.2 获取所有概念列表**
```bash
curl http://localhost:5000/api/search/concepts
```

**2.3 按行业搜索股票（银行业）**
```bash
curl "http://localhost:5000/api/search/stock/by-industry?industry_name=银行&limit=5"
```

**2.4 按概念搜索股票（人工智能）**
```bash
curl "http://localhost:5000/api/search/stock/by-concept?concept_name=人工智能&limit=5"
```

**2.5 按主题搜索股票（芯片）**
```bash
curl "http://localhost:5000/api/search/stock/by-theme?theme_name=芯片&limit=5"
```

**2.6 按关键词搜索股票（平安）**
```bash
curl "http://localhost:5000/api/search/stock/by-keyword?keyword=平安&limit=5"
```

#### 需求3: 场景/新闻驱动分析

**3.1 场景分析 - 英伟达GPU最新消息**
```bash
curl -X POST http://localhost:5000/api/supply-chain/analyze-scenario \
  -H "Content-Type: application/json" \
  -d '{
    "scenario": "英伟达GPU最新消息",
    "include_indirect": true
  }'
```

**3.2 场景分析 - 谷歌TPU最新消息**
```bash
curl -X POST http://localhost:5000/api/supply-chain/analyze-scenario \
  -H "Content-Type: application/json" \
  -d '{
    "scenario": "谷歌TPU最新消息",
    "include_indirect": true
  }'
```

**3.3 查询公司供应链（英伟达）**
```bash
curl "http://localhost:5000/api/supply-chain/company/supply-chain?company_name=英伟达"
```

**3.4 搜索供应商（芯片）**
```bash
curl "http://localhost:5000/api/supply-chain/supplier/search?keyword=芯片"
```

## API端点说明

### 股票分析API (`/api/analysis`)

| 端点 | 方法 | 参数 | 说明 |
|------|------|------|------|
| `/stock/analyze` | POST | symbol, analysis_type | 股票综合分析 |
| `/stock/quote` | GET | symbol | 获取股票行情 |
| `/stock/basic-info` | GET | symbol | 获取股票基本信息 |

### 股票搜索API (`/api/search`)

| 端点 | 方法 | 参数 | 说明 |
|------|------|------|------|
| `/stock/by-industry` | GET | industry_name, filters, sort_by, limit | 按行业搜索 |
| `/stock/by-concept` | GET | concept_name, filters, sort_by, limit | 按概念搜索 |
| `/stock/by-theme` | GET | theme_name, filters, sort_by, limit | 按主题搜索 |
| `/stock/by-keyword` | GET | keyword, limit | 按关键词搜索 |
| `/industries` | GET | - | 获取所有行业列表 |
| `/concepts` | GET | - | 获取所有概念列表 |

### 供应链分析API (`/api/supply-chain`)

| 端点 | 方法 | 参数 | 说明 |
|------|------|------|------|
| `/analyze-scenario` | POST | scenario, include_indirect | 场景分析 |
| `/company/supply-chain` | GET | company_name | 查询公司供应链 |
| `/supplier/search` | GET | keyword | 搜索供应商 |

## 测试结果解读

### 成功的响应示例

```json
{
  "success": true,
  "data": {
    // 具体数据内容
  }
}
```

### 错误响应示例

```json
{
  "success": false,
  "error": "错误信息"
}
```

## 需求验证清单

### 需求1: 单个股票分析 ✓

- [x] 能够接收股票代码
- [x] 能够按照设定规则进行分析
- [x] 能够给出投资价值评估
- [x] 能够给出风险评估

### 需求2: 主题/行业股票筛选 ✓

- [x] 能够基于行业查找相关股票
- [x] 能够基于概念查找相关股票
- [x] 能够基于主题查找相关股票
- [x] 支持多条件过滤（价格、涨跌幅、市盈率、换手率等）
- [x] 支持排序功能

### 需求3: 场景/新闻驱动分析 ✓

- [x] 能够接收场景或新闻文本
- [x] 能够识别相关公司
- [x] 能够列举直接供应商
- [x] 能够列举间接供应商
- [x] 能够标记企业上市状态（is_listed字段）
- [x] 能够标记上市市场（market字段）
- [x] 能够标记股票代码（symbol字段）
- [x] 能够标记供应关系（relationship字段）

## 常见问题

### 1. API服务器未启动

**错误信息**: `Connection refused`

**解决方案**: 确保API服务器正在运行
```bash
/Users/lancer.zhang/ProjectNIO/d8q-intelligentengine-stockshark/venv/bin/python api/api_server.py
```

### 2. 数据获取失败

**错误信息**: `获取股票基本信息失败` 或类似的网络错误

**解决方案**: 
- 检查网络连接
- 某些数据源可能需要代理或VPN
- akshare数据源可能暂时不可用

### 3. 编码问题

**错误信息**: 中文显示为乱码

**解决方案**: 确保终端支持UTF-8编码

## 扩展测试

### 测试其他股票

将测试脚本中的股票代码替换为其他股票代码，例如：
- 000002: 万科A
- 600036: 招商银行
- 600519: 贵州茅台

### 测试其他场景

将测试脚本中的场景文本替换为其他场景，例如：
- "苹果iPhone最新消息"
- "特斯拉自动驾驶技术突破"
- "华为5G芯片发布"

## 技术架构

- **后端框架**: Flask
- **数据源**: akshare
- **数据处理**: pandas, numpy
- **自然语言处理**: jieba
- **数据库**: MySQL + MongoDB

## 联系方式

如有问题，请查看项目文档或联系开发团队。
