class StockSharkError(Exception):
    """基础异常类"""
    pass


class DataError(StockSharkError):
    """数据相关异常"""
    pass


class AnalysisError(StockSharkError):
    """分析相关异常"""
    pass


class ValidationError(StockSharkError):
    """验证相关异常"""
    pass


class DatabaseError(StockSharkError):
    """数据库相关异常"""
    pass
