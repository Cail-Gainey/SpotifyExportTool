"""
日志工具模块 - 使用loguru实现
提供统一的日志记录功能，支持将日志输出到控制台和文件，
自动轮转日志文件，捕获未处理异常
"""
import os
import sys
import traceback
from loguru import logger as loguru_logger

# 清除默认处理器
loguru_logger.remove()

# 创建日志目录
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'log')
os.makedirs(LOG_DIR, exist_ok=True)

# 日志文件路径
LOG_FILE = os.path.join(LOG_DIR, 'last.log')
# 异常日志文件路径
ERROR_LOG_FILE = os.path.join(LOG_DIR, 'error.log')

# 日志级别映射
LOG_LEVELS = {
    'debug': 'DEBUG',
    'info': 'INFO',
    'warning': 'WARNING',
    'error': 'ERROR',
    'critical': 'CRITICAL'
}

# 配置格式化器
console_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> [<level>{level}</level>] <cyan>{name}:{function}:{line}</cyan> - {message}"
file_format = "{time:YYYY-MM-DD HH:mm:ss} [{level}] {name}:{function}:{line} - {message}"

# 添加控制台处理器 (INFO级别及以上)
loguru_logger.add(
    sys.stdout,
    level="INFO",
    format=console_format,
    colorize=True
)

# 添加文件处理器 (DEBUG级别及以上，自动轮转)
loguru_logger.add(
    LOG_FILE,
    level="DEBUG",
    format=file_format,
    rotation="5 MB",  # 当日志达到5MB时轮转
    retention="10 days",  # 保留最近10天的日志
    compression="zip",  # 压缩旧日志
    encoding="utf-8",
    mode="w"  # 使用覆盖模式
)

# 添加错误日志处理器 (ERROR级别及以上，自动轮转)
loguru_logger.add(
    ERROR_LOG_FILE,
    level="ERROR",
    format=file_format,
    rotation="1 MB",  # 当错误日志达到1MB时轮转
    retention="30 days",  # 保留最近30天的错误日志
    compression="zip",  # 压缩旧日志
    encoding="utf-8",
    mode="a"  # 使用追加模式
)

# 记录初始化信息
loguru_logger.info(f"Logger initialized, logging to {LOG_FILE}")
loguru_logger.info(f"Error logs will be saved to {ERROR_LOG_FILE}")

# 获取处理器ID以便后续更新
CONSOLE_HANDLER_ID = 0
FILE_HANDLER_ID = 1
ERROR_HANDLER_ID = 2

def set_level(level):
    """设置日志级别
    :param level: 日志级别，可以是'debug', 'info', 'warning', 'error', 'critical'
    """
    if level.lower() in LOG_LEVELS:
        # 更新文件处理器的级别
        try:
            # 移除并重新添加主文件处理器
            loguru_logger.remove(FILE_HANDLER_ID)
            loguru_logger.add(
                LOG_FILE,
                level=LOG_LEVELS[level.lower()],
                format=file_format,
                rotation="5 MB", 
                retention="10 days",
                compression="zip",
                encoding="utf-8",
                mode="a"  # 追加模式
            )
            loguru_logger.info(f"Log level set to {level.upper()}")
            return True
        except Exception as e:
            loguru_logger.warning(f"Failed to set log level: {str(e)}")
            return False
    else:
        loguru_logger.warning(f"Invalid log level: {level}")
        return False

# 用于处理未捕获的异常
def handle_exception(exc_type, exc_value, exc_traceback):
    """处理未捕获的异常，记录到日志"""
    if issubclass(exc_type, KeyboardInterrupt):
        # 不处理键盘中断
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
        
    # 获取完整的异常信息
    tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    tb_text = ''.join(tb_lines)
    
    # 记录异常
    loguru_logger.opt(exception=(exc_type, exc_value, exc_traceback)).critical(
        f"Uncaught exception:\n{tb_text}"
    )

# 设置异常处理器
sys.excepthook = handle_exception

# 为了维持与原有代码的兼容性，我们提供一个与原有Logger类似的API
class Logger:
    """兼容旧API的日志工具类，实际使用loguru实现"""
    
    @classmethod
    def get_instance(cls):
        """获取Logger单例实例"""
        return cls()
    
    def __init__(self):
        """初始化日志工具"""
        self.log_dir = LOG_DIR
        self.log_file = LOG_FILE
        self.error_log_file = ERROR_LOG_FILE
    
    def debug(self, message, *args, **kwargs):
        """记录DEBUG级别日志"""
        loguru_logger.debug(message, *args, **kwargs)
    
    def info(self, message, *args, **kwargs):
        """记录INFO级别日志"""
        loguru_logger.info(message, *args, **kwargs)
    
    def warning(self, message, *args, **kwargs):
        """记录WARNING级别日志"""
        loguru_logger.warning(message, *args, **kwargs)
    
    def error(self, message, *args, **kwargs):
        """记录ERROR级别日志"""
        loguru_logger.error(message, *args, **kwargs)
    
    def critical(self, message, *args, **kwargs):
        """记录CRITICAL级别日志"""
        loguru_logger.critical(message, *args, **kwargs)
    
    def set_level(self, level):
        """设置日志级别"""
        return set_level(level)
    
    def get_current_level(self):
        """获取当前日志级别"""
        # 由于loguru的处理方式，我们只能返回常量值
        return "DEBUG"  # 文件处理器的默认级别

    def get_log_path(self):
        """获取日志文件路径"""
        return self.log_file
    
    def get_error_log_path(self):
        """获取错误日志文件路径"""
        return self.error_log_file

# 为loguru_logger添加set_level方法
loguru_logger.set_level = set_level
loguru_logger.get_log_path = lambda: LOG_FILE
loguru_logger.get_error_log_path = lambda: ERROR_LOG_FILE
loguru_logger.get_current_level = lambda: "DEBUG"  # 简化实现

# 创建全局日志实例供其他模块导入使用
# 为了向后兼容，维持原有API
logger = loguru_logger