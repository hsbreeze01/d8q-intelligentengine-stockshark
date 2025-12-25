"""
StockShark - 股票分析系统

一个基于 Flask 的股票分析系统，提供以下核心功能：
- 单个股票分析：投资价值和风险评估
- 主题/行业股票筛选：多条件过滤和排序
- 场景/新闻驱动分析：供应链企业识别
"""

__version__ = '0.1.0'
__author__ = 'StockShark Team'

from stockshark.api import create_app
from stockshark.config import Config

__all__ = ['create_app', 'Config', '__version__']
