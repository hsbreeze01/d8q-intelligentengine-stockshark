import re
from datetime import datetime
from stockshark.utils.exceptions import ValidationError


def validate_stock_symbol(symbol):
    """
    验证股票代码格式
    
    Args:
        symbol: 股票代码
    
    Returns:
        验证通过的股票代码
    
    Raises:
        ValidationError: 股票代码格式不正确
    """
    if not symbol or not isinstance(symbol, str):
        raise ValidationError("股票代码不能为空")
    
    symbol = symbol.strip()
    
    if not re.match(r'^\d{6}$', symbol):
        raise ValidationError("股票代码格式不正确，应为6位数字")
    
    return symbol


def validate_date_range(start_date, end_date):
    """
    验证日期范围
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
    
    Returns:
        (start_date, end_date) 元组
    
    Raises:
        ValidationError: 日期格式不正确或范围无效
    """
    date_format = '%Y-%m-%d'
    
    try:
        if start_date:
            start_date = datetime.strptime(start_date, date_format)
        if end_date:
            end_date = datetime.strptime(end_date, date_format)
    except ValueError:
        raise ValidationError("日期格式不正确，应为 YYYY-MM-DD")
    
    if start_date and end_date and start_date > end_date:
        raise ValidationError("开始日期不能晚于结束日期")
    
    return start_date, end_date


def validate_pagination(page, page_size):
    """
    验证分页参数
    
    Args:
        page: 页码
        page_size: 每页数量
    
    Returns:
        (page, page_size) 元组
    
    Raises:
        ValidationError: 分页参数不正确
    """
    try:
        page = int(page) if page else 1
        page_size = int(page_size) if page_size else 20
    except ValueError:
        raise ValidationError("分页参数必须为整数")
    
    if page < 1:
        raise ValidationError("页码必须大于0")
    
    if page_size < 1 or page_size > 100:
        raise ValidationError("每页数量必须在1-100之间")
    
    return page, page_size
