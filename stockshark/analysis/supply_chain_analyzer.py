"""
供应链分析引擎
用于基于场景或新闻分析相关供应链企业
"""

import re
from typing import Dict, List, Any, Optional, Set
from collections import defaultdict
import jieba
import jieba.analyse


class SupplyChainAnalyzer:
    """供应链分析引擎"""
    
    def __init__(self, akshare_data):
        """
        初始化供应链分析引擎
        :param akshare_data: AkShareData实例
        """
        self.ak_data = akshare_data
        
        # 初始化供应链知识库
        self.supply_chain_kb = self._init_supply_chain_kb()
        
        # 初始化公司关键词映射
        self.company_keywords = self._init_company_keywords()
        
        # 初始化jieba分词器
        jieba.initialize()
        
    def _init_supply_chain_kb(self) -> Dict[str, Dict[str, Any]]:
        """
        初始化供应链知识库
        :return: 供应链知识库字典
        """
        kb = {
            # NVIDIA供应链
            'nvidia': {
                'name': '英伟达',
                'aliases': ['NVIDIA', '英伟达', '英伟达公司'],
                'suppliers': {
                    'direct': [
                        {
                            'name': '台积电',
                            'symbol': '2330.TW',
                            'relationship': '芯片代工',
                            'is_listed': True,
                            'market': 'TW'
                        },
                        {
                            'name': 'SK海力士',
                            'symbol': '000660.KS',
                            'relationship': '存储芯片',
                            'is_listed': True,
                            'market': 'KS'
                        },
                        {
                            'name': '三星电子',
                            'symbol': '005930.KS',
                            'relationship': '存储芯片',
                            'is_listed': True,
                            'market': 'KS'
                        },
                        {
                            'name': '美光科技',
                            'symbol': 'MU.US',
                            'relationship': '存储芯片',
                            'is_listed': True,
                            'market': 'US'
                        },
                        {
                            'name': '科沃',
                            'symbol': 'COHR.US',
                            'relationship': '光学组件',
                            'is_listed': True,
                            'market': 'US'
                        },
                        {
                            'name': '新思科技',
                            'symbol': 'SNPS.US',
                            'relationship': 'EDA工具',
                            'is_listed': True,
                            'market': 'US'
                        },
                        {
                            'name': '铿腾电子',
                            'symbol': 'CDNS.US',
                            'relationship': 'EDA工具',
                            'is_listed': True,
                            'market': 'US'
                        }
                    ],
                    'indirect': [
                        {
                            'name': '中芯国际',
                            'symbol': '00981.HK',
                            'relationship': '芯片代工(间接)',
                            'is_listed': True,
                            'market': 'HK'
                        },
                        {
                            'name': '华虹半导体',
                            'symbol': '01347.HK',
                            'relationship': '芯片代工(间接)',
                            'is_listed': True,
                            'market': 'HK'
                        },
                        {
                            'name': '长电科技',
                            'symbol': '600584.SH',
                            'relationship': '封装测试',
                            'is_listed': True,
                            'market': 'SH'
                        },
                        {
                            'name': '通富微电',
                            'symbol': '002156.SZ',
                            'relationship': '封装测试',
                            'is_listed': True,
                            'market': 'SZ'
                        },
                        {
                            'name': '华天科技',
                            'symbol': '002185.SZ',
                            'relationship': '封装测试',
                            'is_listed': True,
                            'market': 'SZ'
                        },
                        {
                            'name': '晶方科技',
                            'symbol': '603005.SH',
                            'relationship': '封装测试',
                            'is_listed': True,
                            'market': 'SH'
                        }
                    ]
                },
                'customers': [
                    {
                        'name': '戴尔',
                        'symbol': 'DELL.US',
                        'relationship': 'GPU客户',
                        'is_listed': True,
                        'market': 'US'
                    },
                    {
                        'name': '惠普',
                        'symbol': 'HPQ.US',
                        'relationship': 'GPU客户',
                        'is_listed': True,
                        'market': 'US'
                    },
                    {
                        'name': '联想',
                        'symbol': '00992.HK',
                        'relationship': 'GPU客户',
                        'is_listed': True,
                        'market': 'HK'
                    }
                ]
            },
            
            # Google TPU供应链
            'google': {
                'name': '谷歌',
                'aliases': ['Google', '谷歌', 'Alphabet', 'Alphabet Inc.'],
                'suppliers': {
                    'direct': [
                        {
                            'name': '台积电',
                            'symbol': '2330.TW',
                            'relationship': '芯片代工',
                            'is_listed': True,
                            'market': 'TW'
                        },
                        {
                            'name': '英特尔',
                            'symbol': 'INTC.US',
                            'relationship': '芯片制造',
                            'is_listed': True,
                            'market': 'US'
                        },
                        {
                            'name': '博通',
                            'symbol': 'AVGO.US',
                            'relationship': '网络芯片',
                            'is_listed': True,
                            'market': 'US'
                        },
                        {
                            'name': '美满电子',
                            'symbol': 'MRVL.US',
                            'relationship': '网络芯片',
                            'is_listed': True,
                            'market': 'US'
                        }
                    ],
                    'indirect': [
                        {
                            'name': '中芯国际',
                            'symbol': '00981.HK',
                            'relationship': '芯片代工(间接)',
                            'is_listed': True,
                            'market': 'HK'
                        },
                        {
                            'name': '长电科技',
                            'symbol': '600584.SH',
                            'relationship': '封装测试',
                            'is_listed': True,
                            'market': 'SH'
                        }
                    ]
                },
                'customers': [
                    {
                        'name': '各类云服务商',
                        'symbol': None,
                        'relationship': 'TPU客户',
                        'is_listed': False,
                        'market': None
                    }
                ]
            },
            
            # 苹果供应链
            'apple': {
                'name': '苹果',
                'aliases': ['Apple', '苹果', '苹果公司'],
                'suppliers': {
                    'direct': [
                        {
                            'name': '台积电',
                            'symbol': '2330.TW',
                            'relationship': '芯片代工',
                            'is_listed': True,
                            'market': 'TW'
                        },
                        {
                            'name': '三星电子',
                            'symbol': '005930.KS',
                            'relationship': '显示屏/存储',
                            'is_listed': True,
                            'market': 'KS'
                        },
                        {
                            'name': 'LG Display',
                            'symbol': '034220.KS',
                            'relationship': '显示屏',
                            'is_listed': True,
                            'market': 'KS'
                        },
                        {
                            'name': '索尼',
                            'symbol': '6758.T',
                            'relationship': '摄像头传感器',
                            'is_listed': True,
                            'market': 'T'
                        },
                        {
                            'name': '博通',
                            'symbol': 'AVGO.US',
                            'relationship': '射频芯片',
                            'is_listed': True,
                            'market': 'US'
                        },
                        {
                            'name': '高通',
                            'symbol': 'QCOM.US',
                            'relationship': '基带芯片',
                            'is_listed': True,
                            'market': 'US'
                        },
                        {
                            'name': '村田制作所',
                            'symbol': '6981.T',
                            'relationship': '电子元件',
                            'is_listed': True,
                            'market': 'T'
                        }
                    ],
                    'indirect': [
                        {
                            'name': '立讯精密',
                            'symbol': '002475.SZ',
                            'relationship': '连接器/组装',
                            'is_listed': True,
                            'market': 'SZ'
                        },
                        {
                            'name': '歌尔股份',
                            'symbol': '002241.SZ',
                            'relationship': '声学组件',
                            'is_listed': True,
                            'market': 'SZ'
                        },
                        {
                            'name': '蓝思科技',
                            'symbol': '300433.SZ',
                            'relationship': '玻璃盖板',
                            'is_listed': True,
                            'market': 'SZ'
                        },
                        {
                            'name': '京东方A',
                            'symbol': '000725.SZ',
                            'relationship': '显示屏(间接)',
                            'is_listed': True,
                            'market': 'SZ'
                        },
                        {
                            'name': '欧菲光',
                            'symbol': '002456.SZ',
                            'relationship': '摄像头模组',
                            'is_listed': True,
                            'market': 'SZ'
                        },
                        {
                            'name': '水晶光电',
                            'symbol': '002273.SZ',
                            'relationship': '光学元件',
                            'is_listed': True,
                            'market': 'SZ'
                        }
                    ]
                },
                'customers': [
                    {
                        'name': '全球消费者',
                        'symbol': None,
                        'relationship': '终端用户',
                        'is_listed': False,
                        'market': None
                    }
                ]
            },
            
            # 特斯拉供应链
            'tesla': {
                'name': '特斯拉',
                'aliases': ['Tesla', '特斯拉', '特斯拉汽车'],
                'suppliers': {
                    'direct': [
                        {
                            'name': '松下',
                            'symbol': '6752.T',
                            'relationship': '电池',
                            'is_listed': True,
                            'market': 'T'
                        },
                        {
                            'name': '宁德时代',
                            'symbol': '300750.SZ',
                            'relationship': '电池',
                            'is_listed': True,
                            'market': 'SZ'
                        },
                        {
                            'name': 'LG新能源',
                            'symbol': '373220.KS',
                            'relationship': '电池',
                            'is_listed': True,
                            'market': 'KS'
                        },
                        {
                            'name': '英伟达',
                            'symbol': 'NVDA.US',
                            'relationship': '自动驾驶芯片',
                            'is_listed': True,
                            'market': 'US'
                        }
                    ],
                    'indirect': [
                        {
                            'name': '比亚迪',
                            'symbol': '002594.SZ',
                            'relationship': '电池(间接)',
                            'is_listed': True,
                            'market': 'SZ'
                        },
                        {
                            'name': '恩捷股份',
                            'symbol': '002812.SZ',
                            'relationship': '隔膜',
                            'is_listed': True,
                            'market': 'SZ'
                        },
                        {
                            'name': '天赐材料',
                            'symbol': '002709.SZ',
                            'relationship': '电解液',
                            'is_listed': True,
                            'market': 'SZ'
                        },
                        {
                            'name': '华友钴业',
                            'symbol': '603799.SH',
                            'relationship': '钴材料',
                            'is_listed': True,
                            'market': 'SH'
                        },
                        {
                            'name': '赣锋锂业',
                            'symbol': '002460.SZ',
                            'relationship': '锂材料',
                            'is_listed': True,
                            'market': 'SZ'
                        },
                        {
                            'name': '三花智控',
                            'symbol': '002050.SZ',
                            'relationship': '热管理',
                            'is_listed': True,
                            'market': 'SZ'
                        }
                    ]
                },
                'customers': [
                    {
                        'name': '全球消费者',
                        'symbol': None,
                        'relationship': '终端用户',
                        'is_listed': False,
                        'market': None
                    }
                ]
            }
        }
        
        return kb
    
    def _init_company_keywords(self) -> Dict[str, str]:
        """
        初始化公司关键词映射
        :return: 关键词到公司ID的映射
        """
        keywords = {}
        
        for company_id, company_info in self.supply_chain_kb.items():
            keywords[company_info['name']] = company_id
            for alias in company_info['aliases']:
                keywords[alias] = company_id
        
        return keywords
    
    def analyze_scenario(self, scenario: str) -> Dict[str, Any]:
        """
        分析场景或新闻，找出相关供应链企业
        :param scenario: 场景或新闻文本
        :return: 分析结果
        """
        result = {
            'scenario': scenario,
            'detected_companies': [],
            'supply_chain_analysis': []
        }
        
        try:
            # 提取场景中的关键词
            keywords = self._extract_keywords(scenario)
            
            # 识别场景中的公司
            detected_companies = self._identify_companies(scenario, keywords)
            result['detected_companies'] = detected_companies
            
            # 对每个识别的公司进行供应链分析
            for company in detected_companies:
                company_id = company['company_id']
                if company_id in self.supply_chain_kb:
                    supply_chain = self._analyze_company_supply_chain(company_id)
                    result['supply_chain_analysis'].append(supply_chain)
            
            # 如果没有识别到公司，尝试基于关键词推荐
            if not detected_companies:
                result['suggestions'] = self._suggest_companies_by_keywords(keywords)
            
            return result
            
        except Exception as e:
            result['error'] = str(e)
            return result
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        从文本中提取关键词
        :param text: 输入文本
        :return: 关键词列表
        """
        # 使用jieba进行关键词提取
        keywords = jieba.analyse.extract_tags(text, topK=20, withWeight=True)
        
        # 提取技术相关关键词
        tech_keywords = []
        tech_patterns = [
            r'GPU|TPU|芯片|半导体|人工智能|AI|深度学习|机器学习',
            r'自动驾驶|电动汽车|新能源|电池',
            r'显示屏|摄像头|传感器|光学',
            r'云计算|数据中心|服务器',
            r'5G|6G|通信|网络'
        ]
        
        for pattern in tech_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            tech_keywords.extend(matches)
        
        # 合并关键词并去重
        all_keywords = [kw[0] for kw in keywords] + tech_keywords
        
        # 添加文本中出现的公司名称
        for company_id, company_info in self.supply_chain_kb.items():
            for alias in company_info['aliases']:
                if alias in text:
                    all_keywords.append(alias)
        
        return list(set(all_keywords))
    
    def _identify_companies(self, text: str, keywords: List[str]) -> List[Dict[str, Any]]:
        """
        识别文本中的公司
        :param text: 输入文本
        :param keywords: 关键词列表
        :return: 识别到的公司列表
        """
        detected = []
        
        # 直接检查文本中是否包含公司别名
        for company_id, company_info in self.supply_chain_kb.items():
            for alias in company_info['aliases']:
                if alias in text:
                    # 检查是否已经识别过该公司
                    if not any(d['company_id'] == company_id for d in detected):
                        detected.append({
                            'company_id': company_id,
                            'name': company_info['name'],
                            'matched_keyword': alias,
                            'confidence': self._calculate_confidence(text, company_info)
                        })
        
        # 基于关键词匹配识别公司（补充）
        for keyword in keywords:
            if keyword in self.company_keywords:
                company_id = self.company_keywords[keyword]
                company_info = self.supply_chain_kb[company_id]
                
                # 检查是否已经识别过该公司
                if not any(d['company_id'] == company_id for d in detected):
                    detected.append({
                        'company_id': company_id,
                        'name': company_info['name'],
                        'matched_keyword': keyword,
                        'confidence': self._calculate_confidence(text, company_info)
                    })
        
        # 按置信度排序
        detected.sort(key=lambda x: x['confidence'], reverse=True)
        
        return detected
    
    def _calculate_confidence(self, text: str, company_info: Dict[str, Any]) -> float:
        """
        计算识别置信度
        :param text: 输入文本
        :param company_info: 公司信息
        :return: 置信度分数
        """
        confidence = 0.0
        
        # 检查公司名称出现次数
        for alias in company_info['aliases']:
            count = text.lower().count(alias.lower())
            confidence += count * 0.3
        
        # 限制最大置信度为1.0
        return min(confidence, 1.0)
    
    def _analyze_company_supply_chain(self, company_id: str) -> Dict[str, Any]:
        """
        分析公司的供应链
        :param company_id: 公司ID
        :return: 供应链分析结果
        """
        company_info = self.supply_chain_kb[company_id]
        
        result = {
            'company_id': company_id,
            'company_name': company_info['name'],
            'direct_suppliers': [],
            'indirect_suppliers': [],
            'customers': [],
            'listed_companies': [],
            'unlisted_companies': [],
            'holding_relationships': []
        }
        
        # 处理直接供应商
        for supplier in company_info['suppliers'].get('direct', []):
            supplier_info = self._enrich_supplier_info(supplier)
            result['direct_suppliers'].append(supplier_info)
            
            # 分类上市和非上市公司
            if supplier_info['is_listed']:
                result['listed_companies'].append(supplier_info)
            else:
                result['unlisted_companies'].append(supplier_info)
        
        # 处理间接供应商
        for supplier in company_info['suppliers'].get('indirect', []):
            supplier_info = self._enrich_supplier_info(supplier)
            result['indirect_suppliers'].append(supplier_info)
            
            if supplier_info['is_listed']:
                result['listed_companies'].append(supplier_info)
            else:
                result['unlisted_companies'].append(supplier_info)
        
        # 处理客户
        for customer in company_info.get('customers', []):
            customer_info = self._enrich_supplier_info(customer)
            result['customers'].append(customer_info)
        
        # 分析控股关系（对于非上市公司）
        for company in result['unlisted_companies']:
            holding_info = self._analyze_holding_relationship(company)
            if holding_info:
                result['holding_relationships'].append(holding_info)
        
        return result
    
    def _enrich_supplier_info(self, supplier: Dict[str, Any]) -> Dict[str, Any]:
        """
        丰富供应商信息
        :param supplier: 基础供应商信息
        :return: 丰富后的供应商信息
        """
        enriched = supplier.copy()
        
        # 如果有股票代码，尝试获取更多信息
        if supplier.get('symbol') and supplier.get('is_listed'):
            try:
                # 获取股票基本信息
                basic_info = self.ak_data.get_stock_basic_info(supplier['symbol'])
                if basic_info:
                    enriched['market_cap'] = basic_info.get('总市值')
                    enriched['industry'] = basic_info.get('所属行业')
                    enriched['pe_ratio'] = basic_info.get('市盈率-动态')
                
                # 获取实时行情
                quote_data = self.ak_data.get_stock_quote(supplier['symbol'])
                if quote_data:
                    enriched['current_price'] = quote_data.get('最新价')
                    enriched['change_pct'] = quote_data.get('涨跌幅')
                    enriched['volume'] = quote_data.get('成交量')
                    
            except Exception as e:
                enriched['data_error'] = str(e)
        
        return enriched
    
    def _analyze_holding_relationship(self, company: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        分析控股关系（对于非上市公司）
        :param company: 公司信息
        :return: 控股关系信息
        """
        # 这里可以集成实际的股权关系数据库或API
        # 目前返回示例数据
        
        holding_info = {
            'company_name': company['name'],
            'is_listed': False,
            'listed_holders': []
        }
        
        # 示例：某些非上市公司可能有上市公司控股
        # 这里可以根据实际业务需求实现
        
        return holding_info if holding_info['listed_holders'] else None
    
    def _suggest_companies_by_keywords(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """
        基于关键词推荐相关公司
        :param keywords: 关键词列表
        :return: 推荐的公司列表
        """
        suggestions = []
        
        # 关键词到公司的映射
        keyword_to_companies = {
            'GPU': ['nvidia'],
            'TPU': ['google'],
            '芯片': ['nvidia', 'google', 'apple'],
            '半导体': ['nvidia', 'google', 'apple'],
            '人工智能': ['nvidia', 'google'],
            'AI': ['nvidia', 'google'],
            '自动驾驶': ['tesla', 'nvidia'],
            '电动汽车': ['tesla'],
            '新能源': ['tesla'],
            '电池': ['tesla'],
            '手机': ['apple'],
            '显示屏': ['apple', 'google'],
            '摄像头': ['apple'],
            '传感器': ['apple']
        }
        
        # 基于关键词查找相关公司
        for keyword in keywords:
            if keyword in keyword_to_companies:
                for company_id in keyword_to_companies[keyword]:
                    if company_id in self.supply_chain_kb:
                        company_info = self.supply_chain_kb[company_id]
                        if not any(s['company_id'] == company_id for s in suggestions):
                            suggestions.append({
                                'company_id': company_id,
                                'name': company_info['name'],
                                'matched_keyword': keyword
                            })
        
        return suggestions
    
    def get_company_supply_chain(self, company_name: str) -> Dict[str, Any]:
        """
        获取指定公司的供应链信息
        :param company_name: 公司名称
        :return: 供应链信息
        """
        result = {
            'company_name': company_name,
            'found': False,
            'supply_chain': None
        }
        
        # 查找公司
        company_id = None
        for cid, cinfo in self.supply_chain_kb.items():
            if company_name.lower() in [name.lower() for name in cinfo['aliases']]:
                company_id = cid
                break
        
        if company_id:
            result['found'] = True
            result['supply_chain'] = self._analyze_company_supply_chain(company_id)
        else:
            result['error'] = f"未找到公司：{company_name}"
        
        return result
    
    def search_supplier_by_keyword(self, keyword: str) -> Dict[str, Any]:
        """
        根据关键词搜索供应商
        :param keyword: 搜索关键词
        :return: 搜索结果
        """
        result = {
            'keyword': keyword,
            'suppliers': []
        }
        
        # 在所有供应链中搜索
        for company_id, company_info in self.supply_chain_kb.items():
            for supplier_type in ['direct', 'indirect']:
                for supplier in company_info['suppliers'].get(supplier_type, []):
                    # 搜索供应商名称或关系描述
                    if (keyword.lower() in supplier['name'].lower() or 
                        keyword.lower() in supplier['relationship'].lower()):
                        supplier_info = self._enrich_supplier_info(supplier)
                        supplier_info['supply_chain_of'] = company_info['name']
                        supplier_info['relationship_type'] = supplier_type
                        result['suppliers'].append(supplier_info)
        
        return result
