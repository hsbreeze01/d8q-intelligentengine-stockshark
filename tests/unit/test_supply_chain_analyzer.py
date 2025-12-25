"""
供应链分析器测试脚本
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from stockshark.data.akshare_data import AkShareData
from stockshark.analysis.supply_chain_analyzer import SupplyChainAnalyzer


def test_supply_chain_analyzer():
    """测试供应链分析器"""
    print("=" * 80)
    print("供应链分析器测试")
    print("=" * 80)
    
    # 初始化数据源
    print("\n1. 初始化数据源...")
    ak_data = AkShareData()
    print("✓ 数据源初始化成功")
    
    # 初始化供应链分析器
    print("\n2. 初始化供应链分析器...")
    analyzer = SupplyChainAnalyzer(ak_data)
    print("✓ 供应链分析器初始化成功")
    
    # 测试1: 分析NVIDIA相关场景
    print("\n" + "=" * 80)
    print("测试1: 分析NVIDIA GPU相关场景")
    print("=" * 80)
    scenario1 = "英伟达发布最新的GPU芯片，性能提升50%，将用于数据中心和AI训练"
    print(f"\n场景文本: {scenario1}")
    
    result1 = analyzer.analyze_scenario(scenario1)
    print("\n分析结果:")
    print(f"  识别到的公司: {[c['name'] for c in result1['detected_companies']]}")
    
    if result1['supply_chain_analysis']:
        for sc in result1['supply_chain_analysis']:
            print(f"\n  {sc['company_name']} 供应链分析:")
            print(f"    直接供应商数量: {len(sc['direct_suppliers'])}")
            print(f"    间接供应商数量: {len(sc['indirect_suppliers'])}")
            print(f"    上市公司数量: {len(sc['listed_companies'])}")
            print(f"    非上市公司数量: {len(sc['unlisted_companies'])}")
            
            print("\n    主要直接供应商:")
            for supplier in sc['direct_suppliers'][:3]:
                print(f"      - {supplier['name']} ({supplier['relationship']})")
                if supplier.get('current_price'):
                    print(f"        当前价格: {supplier['current_price']}")
                    print(f"        涨跌幅: {supplier.get('change_pct', 'N/A')}%")
    
    # 测试2: 分析Google TPU相关场景
    print("\n" + "=" * 80)
    print("测试2: 分析Google TPU相关场景")
    print("=" * 80)
    scenario2 = "谷歌宣布推出新一代TPU芯片，将大幅提升机器学习训练效率"
    print(f"\n场景文本: {scenario2}")
    
    result2 = analyzer.analyze_scenario(scenario2)
    print("\n分析结果:")
    print(f"  识别到的公司: {[c['name'] for c in result2['detected_companies']]}")
    
    if result2['supply_chain_analysis']:
        for sc in result2['supply_chain_analysis']:
            print(f"\n  {sc['company_name']} 供应链分析:")
            print(f"    直接供应商数量: {len(sc['direct_suppliers'])}")
            print(f"    间接供应商数量: {len(sc['indirect_suppliers'])}")
            
            print("\n    主要直接供应商:")
            for supplier in sc['direct_suppliers'][:3]:
                print(f"      - {supplier['name']} ({supplier['relationship']})")
    
    # 测试3: 获取指定公司的供应链
    print("\n" + "=" * 80)
    print("测试3: 获取苹果公司的供应链")
    print("=" * 80)
    
    result3 = analyzer.get_company_supply_chain('苹果')
    print("\n分析结果:")
    if result3['found']:
        sc = result3['supply_chain']
        print(f"  公司名称: {sc['company_name']}")
        print(f"  直接供应商数量: {len(sc['direct_suppliers'])}")
        print(f"  间接供应商数量: {len(sc['indirect_suppliers'])}")
        print(f"  上市公司数量: {len(sc['listed_companies'])}")
        
        print("\n  直接供应商列表:")
        for supplier in sc['direct_suppliers']:
            listed_status = "已上市" if supplier['is_listed'] else "未上市"
            print(f"    - {supplier['name']} ({supplier['relationship']}) - {listed_status}")
            if supplier.get('market'):
                print(f"      市场: {supplier['market']}")
                print(f"      代码: {supplier['symbol']}")
    else:
        print(f"  错误: {result3.get('error')}")
    
    # 测试4: 根据关键词搜索供应商
    print("\n" + "=" * 80)
    print("测试4: 根据关键词搜索供应商")
    print("=" * 80)
    
    keyword = "芯片"
    print(f"\n搜索关键词: {keyword}")
    
    result4 = analyzer.search_supplier_by_keyword(keyword)
    print(f"\n找到 {len(result4['suppliers'])} 个相关供应商:")
    
    for supplier in result4['suppliers'][:5]:
        print(f"  - {supplier['name']} ({supplier['relationship']})")
        print(f"    供应链所属: {supplier['supply_chain_of']}")
        print(f"    关系类型: {supplier['relationship_type']}")
        if supplier.get('is_listed'):
            print(f"    已上市 - 市场: {supplier.get('market')}, 代码: {supplier.get('symbol')}")
        else:
            print(f"    未上市")
    
    # 测试5: 分析特斯拉相关场景
    print("\n" + "=" * 80)
    print("测试5: 分析特斯拉相关场景")
    print("=" * 80)
    scenario5 = "特斯拉发布新款电动汽车，搭载最新的自动驾驶芯片和电池技术"
    print(f"\n场景文本: {scenario5}")
    
    result5 = analyzer.analyze_scenario(scenario5)
    print("\n分析结果:")
    print(f"  识别到的公司: {[c['name'] for c in result5['detected_companies']]}")
    
    if result5['supply_chain_analysis']:
        for sc in result5['supply_chain_analysis']:
            print(f"\n  {sc['company_name']} 供应链分析:")
            print(f"    直接供应商数量: {len(sc['direct_suppliers'])}")
            print(f"    间接供应商数量: {len(sc['indirect_suppliers'])}")
            print(f"    上市公司数量: {len(sc['listed_companies'])}")
            
            print("\n    主要直接供应商:")
            for supplier in sc['direct_suppliers'][:3]:
                print(f"      - {supplier['name']} ({supplier['relationship']})")
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == '__main__':
    try:
        test_supply_chain_analyzer()
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
