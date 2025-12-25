import logging
import sys
from stockshark.config import Config


def get_logger(name=None):
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称，默认为当前模块名
    
    Returns:
        logging.Logger 实例
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logger.setLevel(getattr(logging, Config.LOG_LEVEL.upper()))
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger
