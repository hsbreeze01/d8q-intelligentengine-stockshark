#!/bin/bash

# 股票分析系统API测试脚本
# 验证三个核心功能：
# 1. 单个股票分析 - 投资价值和风险评估
# 2. 主题/行业股票筛选 - 多条件过滤和排序
# 3. 场景/新闻驱动分析 - 供应链企业识别

API_BASE="http://localhost:5000/api"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=========================================="
echo "股票分析系统API测试"
echo "=========================================="
echo ""

# ========================================
# 需求1: 单个股票分析
# 提供一个股票，可以按照设定的规则来做分析，给出投资价值和风险
# ========================================
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}需求1: 单个股票分析${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo -e "${YELLOW}[测试1.1] 健康检查${NC}"
curl -s "$API_BASE/../health" | python3 -m json.tool
echo ""

echo -e "${YELLOW}[测试1.2] 股票分析 - 平安银行(000001)${NC}"
echo "命令: POST $API_BASE/analysis/stock/analyze"
curl -s -X POST "$API_BASE/analysis/stock/analyze" \
    -H "Content-Type: application/json" \
    -d '{
        "symbol": "000001",
        "analysis_type": "comprehensive"
    }' | python3 -m json.tool
echo ""

echo -e "${YELLOW}[测试1.3] 获取股票行情 - 平安银行(000001)${NC}"
echo "命令: GET $API_BASE/analysis/stock/quote?symbol=000001"
curl -s "$API_BASE/analysis/stock/quote?symbol=000001" | python3 -m json.tool
echo ""

# ========================================
# 需求2: 主题/行业股票筛选
# 能够基于某个主题/行业等查找到相关联的股票信息，并按照指定的规则做筛选排序
# ========================================
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}需求2: 主题/行业股票筛选${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo -e "${YELLOW}[测试2.1] 获取所有行业列表${NC}"
echo "命令: GET $API_BASE/search/industries"
curl -s "$API_BASE/search/industries" | python3 -m json.tool
echo ""

echo -e "${YELLOW}[测试2.2] 获取所有概念列表${NC}"
echo "命令: GET $API_BASE/search/concepts"
curl -s "$API_BASE/search/concepts" | python3 -m json.tool
echo ""

echo -e "${YELLOW}[测试2.3] 按行业搜索股票（银行业）${NC}"
echo "命令: GET $API_BASE/search/stock/by-industry?industry_name=银行&limit=5"
curl -s "$API_BASE/search/stock/by-industry?industry_name=银行&limit=5" | python3 -m json.tool
echo ""

echo -e "${YELLOW}[测试2.4] 按概念搜索股票（人工智能）${NC}"
echo "命令: GET $API_BASE/search/stock/by-concept?concept_name=人工智能&limit=5"
curl -s "$API_BASE/search/stock/by-concept?concept_name=人工智能&limit=5" | python3 -m json.tool
echo ""

echo -e "${YELLOW}[测试2.5] 按主题搜索股票（芯片）${NC}"
echo "命令: GET $API_BASE/search/stock/by-theme?theme_name=芯片&limit=5"
curl -s "$API_BASE/search/stock/by-theme?theme_name=芯片&limit=5" | python3 -m json.tool
echo ""

echo -e "${YELLOW}[测试2.6] 按关键词搜索股票（平安）${NC}"
echo "命令: GET $API_BASE/search/stock/by-keyword?keyword=平安&limit=5"
curl -s "$API_BASE/search/stock/by-keyword?keyword=平安&limit=5" | python3 -m json.tool
echo ""

# ========================================
# 需求3: 场景/新闻驱动分析
# 提供一个场景或新闻，给出相关股票，列举出相关联的供应链企业
# 涵盖直接供应或间接供应，标记上市状态和控股关系
# ========================================
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}需求3: 场景/新闻驱动分析${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo -e "${YELLOW}[测试3.1] 场景分析 - 英伟达GPU最新消息${NC}"
echo "命令: POST $API_BASE/supply-chain/analyze-scenario"
curl -s -X POST "$API_BASE/supply-chain/analyze-scenario" \
    -H "Content-Type: application/json" \
    -d '{
        "scenario": "英伟达GPU最新消息",
        "include_indirect": true
    }' | python3 -m json.tool
echo ""

echo -e "${YELLOW}[测试3.2] 场景分析 - 谷歌TPU最新消息${NC}"
echo "命令: POST $API_BASE/supply-chain/analyze-scenario"
curl -s -X POST "$API_BASE/supply-chain/analyze-scenario" \
    -H "Content-Type: application/json" \
    -d '{
        "scenario": "谷歌TPU最新消息",
        "include_indirect": true
    }' | python3 -m json.tool
echo ""

echo -e "${YELLOW}[测试3.3] 查询公司供应链（英伟达）${NC}"
echo "命令: GET $API_BASE/supply-chain/company/supply-chain?company_name=英伟达"
curl -s "$API_BASE/supply-chain/company/supply-chain?company_name=英伟达" | python3 -m json.tool
echo ""

echo -e "${YELLOW}[测试3.4] 搜索供应商（芯片）${NC}"
echo "命令: GET $API_BASE/supply-chain/supplier/search?keyword=芯片"
curl -s "$API_BASE/supply-chain/supplier/search?keyword=芯片" | python3 -m json.tool
echo ""

echo "=========================================="
echo "测试完成"
echo "=========================================="
