#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试股票概念和行业信息获取的数据库优先逻辑"""
import sys
import os

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 直接导入需要的模块，避免导入整个 Flask 应用
import importlib.util

def import_module_from_path(module_name, file_path):
    """从文件路径导入模块"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# 导入配置
config_module = import_module_from_path('config', os.path.join(project_root, 'stockshark', 'config.py'))

# 导入数据库工具
database_module = import_module_from_path('database', os.path.join(project_root, 'stockshark', 'utils', 'database.py'))

# 导入日志工具
logger_module = import_module_from_path('logger', os.path.join(project_root, 'stockshark', 'utils', 'logger.py'))
get_logger = logger_module.get_logger

logger = get_logger(__name__)

# 导入模型
stock_basic_info_module = import_module_from_path('stock_basic_info', os.path.join(project_root, 'stockshark', 'models', 'stock_basic_info.py'))
StockBasicInfo = stock_basic_info_module.StockBasicInfo

# 导入数据获取模块
akshare_data_module = import_module_from_path('akshare_data', os.path.join(project_root, 'stockshark', 'data', 'akshare_data.py'))
AkShareData = akshare_data_module.AkShareData


class TestStockService:
    """简化的股票服务类用于测试"""
    
    def __init__(self):
        self.ak_data = AkShareData()
    
    def get_stock_sectors(self, symbol):
        """
        获取股票所属的行业和概念信息（优先从数据库查询）
        
        Args:
            symbol: 股票代码
        
        Returns:
            dict: 行业和概念信息
        """
        # 1. 先从数据库查询基本信息
        db_info = StockBasicInfo.get_by_symbol(symbol)
        
        industry_name = ''
        concept_str = ''
        stock_name = ''
        
        if db_info:
            industry_name = db_info.get('industry', '')
            concept_str = db_info.get('concept', '')
            stock_name = db_info.get('name', '')
            logger.info(f"从数据库获取股票 {symbol} 行业和概念信息")
        else:
            # 2. 数据库中没有，从akshare获取
            logger.info(f"数据库中没有股票 {symbol}，从akshare获取...")
            api_info = self.ak_data.get_stock_basic_info(symbol)
            
            if api_info:
                industry_name = api_info.get('industry', '')
                concept_str = api_info.get('concept', '')
                stock_name = api_info.get('name', '')
                
                # 3. 保存到数据库
                try:
                    stock_basic = StockBasicInfo(
                        symbol=api_info['code'],
                        name=api_info['name'],
                        full_name=api_info.get('full_name', ''),
                        industry=industry_name,
                        concept=concept_str,
                        region=api_info.get('region', ''),
                        market=api_info.get('market', ''),
                        list_date=api_info.get('list_date')
                    )
                    stock_basic.save()
                    logger.info(f"股票 {symbol} 基本信息已保存到数据库")
                except Exception as e:
                    logger.error(f"保存股票 {symbol} 基本信息到数据库失败: {e}")
        
        # 获取行业详细信息
        industry_stocks = []
        if industry_name:
            industry_stocks = self.ak_data.get_industry_stocks(industry_name)
        
        # 获取概念详细信息
        concepts = []
        if concept_str:
            concept_list = [c.strip() for c in concept_str.split('、') if c.strip()]
            for concept_name in concept_list[:5]:
                concept_stocks = self.ak_data.get_concept_stocks(concept_name)
                if concept_stocks:
                    concepts.append({
                        'name': concept_name,
                        'stock_count': len(concept_stocks)
                    })
        
        return {
            'symbol': symbol,
            'name': stock_name,
            'industry': {
                'name': industry_name,
                'stock_count': len(industry_stocks)
            },
            'concepts': concepts
        }


def test_database_first_logic():
    """测试数据库优先的逻辑"""
    
    # 创建测试服务实例
    test_service = TestStockService()
    
    print("=" * 80)
    print("测试股票概念和行业信息获取 - 数据库优先逻辑")
    print("=" * 80)
    
    # 测试用例1: 数据库中已存在的股票
    print("\n【测试1】数据库中已存在的股票")
    print("-" * 80)
    
    # 先查询数据库中是否有数据
    existing_symbol = "000001"
    db_info = StockBasicInfo.get_by_symbol(existing_symbol)
    
    if db_info:
        print(f"✓ 数据库中存在股票 {existing_symbol}: {db_info.get('name', '')}")
        print(f"  行业: {db_info.get('industry', '无')}")
        print(f"  概念: {db_info.get('concept', '无')[:50]}...")
        
        # 测试获取行业和概念信息
        result = test_service.get_stock_sectors(existing_symbol)
        print(f"\n✓ 获取行业和概念信息成功:")
        print(f"  股票名称: {result.get('name', '')}")
        print(f"  行业: {result['industry']['name']} ({result['industry']['stock_count']}只股票)")
        print(f"  概念数量: {len(result['concepts'])}")
        for concept in result['concepts'][:3]:
            print(f"    - {concept['name']}: {concept['stock_count']}只")
    else:
        print(f"✗ 数据库中没有股票 {existing_symbol}，跳过此测试")
    
    # 测试用例2: 数据库中不存在的股票（需要远程获取）
    print("\n【测试2】数据库中不存在的股票（需要远程获取）")
    print("-" * 80)
    
    # 使用一个可能不在数据库中的股票代码
    test_symbol = "688981"  # 一个科创板股票
    
    # 先检查数据库中是否存在
    db_info = StockBasicInfo.get_by_symbol(test_symbol)
    
    if db_info:
        print(f"✓ 数据库中已存在股票 {test_symbol}，跳过此测试")
        print(f"  股票名称: {db_info.get('name', '')}")
        print(f"  行业: {db_info.get('industry', '无')}")
        print(f"  概念: {db_info.get('concept', '无')[:50]}...")
    else:
        print(f"✓ 数据库中没有股票 {test_symbol}，将测试远程获取")
        
        # 测试远程获取
        print(f"\n正在从远程获取股票 {test_symbol} 的信息...")
        result = test_service.get_stock_sectors(test_symbol)
        
        if result:
            print(f"✓ 远程获取成功:")
            print(f"  股票名称: {result.get('name', '')}")
            print(f"  行业: {result['industry']['name']} ({result['industry']['stock_count']}只股票)")
            print(f"  概念数量: {len(result['concepts'])}")
            for concept in result['concepts'][:3]:
                print(f"    - {concept['name']}: {concept['stock_count']}只")
            
            # 验证数据是否已保存到数据库
            db_info = StockBasicInfo.get_by_symbol(test_symbol)
            if db_info:
                print(f"\n✓ 数据已成功保存到数据库")
                print(f"  数据库中的行业: {db_info.get('industry', '无')}")
                print(f"  数据库中的概念: {db_info.get('concept', '无')[:50]}...")
            else:
                print(f"\n✗ 数据未保存到数据库")
        else:
            print(f"✗ 远程获取失败")
    
    # 测试用例3: 验证第二次访问同一只股票从数据库读取
    print("\n【测试3】验证第二次访问同一只股票从数据库读取")
    print("-" * 80)
    
    # 检查刚才测试的股票是否在数据库中
    db_info = StockBasicInfo.get_by_symbol(test_symbol)
    
    if db_info:
        print(f"再次获取股票 {test_symbol} 的信息（应该从数据库读取）...")
        result2 = test_service.get_stock_sectors(test_symbol)
        
        if result2:
            print(f"✓ 第二次获取成功（从数据库）:")
            print(f"  股票名称: {result2.get('name', '')}")
            print(f"  行业: {result2['industry']['name']}")
            print(f"  概念数量: {len(result2['concepts'])}")
        else:
            print(f"✗ 第二次获取失败")
    else:
        print(f"✗ 股票 {test_symbol} 不在数据库中，跳过此测试")
    
    # 测试用例4: 测试不存在的股票
    print("\n【测试4】测试不存在的股票")
    print("-" * 80)
    
    invalid_symbol = "999999"
    print(f"尝试获取不存在的股票 {invalid_symbol}...")
    result = test_service.get_stock_sectors(invalid_symbol)
    
    if result:
        print(f"✓ 返回结果（可能为空）:")
        print(f"  股票名称: {result.get('name', '无')}")
        print(f"  行业: {result['industry']['name']}")
        print(f"  概念数量: {len(result['concepts'])}")
    else:
        print(f"✗ 返回 None")
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == "__main__":
    test_database_first_logic()
