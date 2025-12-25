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
NC='\033[0m' # No Color

echo "=========================================="
echo "股票分析系统API测试"
echo "=========================================="
echo ""

# 测试计数器
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 测试函数
run_test() {
    local test_name="$1"
    local command="$2"
    local expected_status="$3"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -n "测试 $TOTAL_TESTS: $test_name ... "
    
    response=$(eval "$command" 2>&1)
    success=$(echo "$response" | grep -o '"success":[^,}]*' | head -1 | cut -d':' -f2 | tr -d ' ')
    
    if [ "$success" = "$expected_status" ]; then
        echo -e "${GREEN}通过${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        echo -e "${RED}失败${NC}"
        echo "  预期状态: $expected_status, 实际状态: $status"
        echo "  响应: $response"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

# ========================================
# 需求1: 单个股票分析
# 提供一个股票，可以按照设定的规则来做分析，给出投资价值和风险
# ========================================
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}需求1: 单个股票分析${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# 1.1 健康检查
echo -n "测试 1: 健康检查 ... "
response=$(curl -s "$API_BASE/../health")
status=$(echo "$response" | grep -o '"status":[^,}]*' | head -1 | cut -d':' -f2 | tr -d '"')
if [ "$status" = "ok" ]; then
    echo -e "${GREEN}通过${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}失败${NC}"
    echo "  预期状态: ok, 实际状态: $status"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# 1.2 股票分析 - 平安银行(000001)
echo ""
echo "测试股票分析功能（平安银行 000001）:"
curl -s -X POST "$API_BASE/analysis/stock/analyze" \
    -H "Content-Type: application/json" \
    -d '{
        "symbol": "000001",
        "analysis_type": "comprehensive"
    }' | python3 -m json.tool

echo ""
echo ""

# 1.3 获取股票行情
run_test "获取股票行情" \
    "curl -s '$API_BASE/analysis/stock/quote?symbol=000001'" \
    "success"

# 1.4 获取股票基本信息
run_test "获取股票基本信息" \
    "curl -s '$API_BASE/analysis/stock/basic-info?symbol=000001'" \
    "success"

# ========================================
# 需求2: 主题/行业股票筛选
# 能够基于某个主题/行业等查找到相关联的股票信息，并按照指定的规则做筛选排序
# ========================================
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}需求2: 主题/行业股票筛选${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# 2.1 获取所有行业列表
echo "获取所有行业列表:"
curl -s "$API_BASE/search/industries" | python3 -m json.tool
echo ""

# 2.2 获取所有概念列表
echo "获取所有概念列表:"
curl -s "$API_BASE/search/concepts" | python3 -m json.tool
echo ""

# 2.3 按行业搜索股票（银行业）
echo "测试按行业搜索股票（银行业）:"
curl -s "$API_BASE/search/stock/by-industry?industry_name=银行&limit=5" | python3 -m json.tool
echo ""

# 2.4 按概念搜索股票（人工智能）
echo "测试按概念搜索股票（人工智能）:"
curl -s "$API_BASE/search/stock/by-concept?concept_name=人工智能&limit=5" | python3 -m json.tool
echo ""

# 2.5 按主题搜索股票（芯片）
echo "测试按主题搜索股票（芯片）:"
curl -s "$API_BASE/search/stock/by-theme?theme_name=芯片&limit=5" | python3 -m json.tool
echo ""

# 2.6 按关键词搜索股票（平安）
echo "测试按关键词搜索股票（平安）:"
curl -s "$API_BASE/search/stock/by-keyword?keyword=平安&limit=5" | python3 -m json.tool
echo ""

# ========================================
# 需求3: 场景/新闻驱动分析
# 提供一个场景或新闻，给出相关股票，列举出相关联的供应链企业
# 涵盖直接供应或间接供应，标记上市状态和控股关系
# ========================================
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}需求3: 场景/新闻驱动分析${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# 3.1 场景分析 - 英伟达GPU最新消息
echo "测试场景分析（英伟达GPU最新消息）:"
curl -s -X POST "$API_BASE/supply-chain/analyze-scenario" \
    -H "Content-Type: application/json" \
    -d '{
        "scenario": "英伟达GPU最新消息",
        "include_indirect": true
    }' | python3 -m json.tool
echo ""

# 3.2 场景分析 - 谷歌TPU最新消息
echo "测试场景分析（谷歌TPU最新消息）:"
curl -s -X POST "$API_BASE/supply-chain/analyze-scenario" \
    -H "Content-Type: application/json" \
    -d '{
        "scenario": "谷歌TPU最新消息",
        "include_indirect": true
    }' | python3 -m json.tool
echo ""

# 3.3 查询公司供应链（英伟达）
echo "测试查询公司供应链（英伟达）:"
curl -s "$API_BASE/supply-chain/company/supply-chain?company_name=英伟达" | python3 -m json.tool
echo ""

# 3.4 搜索供应商（芯片）
echo "测试搜索供应商（芯片）:"
curl -s "$API_BASE/supply-chain/supplier/search?keyword=芯片" | python3 -m json.tool
echo ""

# ========================================
# 测试结果汇总
# ========================================
echo ""
echo "=========================================="
echo "测试结果汇总"
echo "=========================================="
echo -e "总测试数: $TOTAL_TESTS"
echo -e "${GREEN}通过: $PASSED_TESTS${NC}"
echo -e "${RED}失败: $FAILED_TESTS${NC}"
echo "=========================================="

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}所有测试通过！${NC}"
    exit 0
else
    echo -e "${RED}部分测试失败，请检查错误信息${NC}"
    exit 1
fi
