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

# 获取应用程序根目录
if getattr(sys, 'frozen', False):
    # 如果是打包后的可执行文件
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # 如果是直接运行脚本
    # 从src/utils到项目根目录需要向上两级
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 创建日志目录
LOG_DIR = os.path.join(BASE_DIR, 'log')
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
console_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> [<level>{level}</level>] <cyan>{name}</cyan>:[<yellow>{line}</yellow>] - {message}"
file_format = "{time:YYYY-MM-DD HH:mm:ss} [{level}] {name}:[{line}] - {message}"

# 获取处理器ID以便后续更新
CONSOLE_HANDLER_ID = None
FILE_HANDLER_ID = None
ERROR_HANDLER_ID = None

# 从settings模块获取日志级别
try:
    from src.config import settings
    CURRENT_LOG_LEVEL = settings.get_setting("log_level", "info")
except ImportError:
    # 如果无法导入settings模块，使用默认值
    CURRENT_LOG_LEVEL = "info"

# 添加控制台处理器 (INFO级别及以上)
try:
    CONSOLE_HANDLER_ID = loguru_logger.add(
        sys.stdout,
        level=LOG_LEVELS.get(CURRENT_LOG_LEVEL, "INFO"),
        format=console_format,
        colorize=True
    )
except Exception as e:
    print(f"无法初始化控制台日志: {str(e)}")

# 添加文件处理器 (DEBUG级别及以上，自动轮转)
try:
    # 确保日志目录存在
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    
    FILE_HANDLER_ID = loguru_logger.add(
        LOG_FILE,
        level="DEBUG",
        format=file_format,
        rotation="5 MB",  # 当日志达到5MB时轮转
        retention="10 days",  # 保留最近10天的日志
        compression="zip",  # 压缩旧日志
        encoding="utf-8",
        mode="w",  # 使用覆盖模式
        backtrace=True,  # 启用回溯
        diagnose=True,  # 启用诊断
        catch=True  # 捕获异常
    )
except Exception as e:
    print(f"无法初始化文件日志: {str(e)}")

# 添加错误日志处理器 (ERROR级别及以上，自动轮转)
def add_error_handler():
    """按需添加错误日志处理器"""
    global ERROR_HANDLER_ID
    try:
        # 确保错误日志目录存在
        os.makedirs(os.path.dirname(ERROR_LOG_FILE), exist_ok=True)
        
        ERROR_HANDLER_ID = loguru_logger.add(
            ERROR_LOG_FILE,
            level="ERROR",
            format=file_format,
            rotation="1 MB",  # 当错误日志达到1MB时轮转
            retention="30 days",  # 保留最近30天的错误日志
            compression="zip",  # 压缩旧日志
            encoding="utf-8",
            mode="w",  # 使用覆盖模式，每次启动都会创建新文件
            backtrace=True,  # 启用回溯
            diagnose=True,  # 启用诊断
            catch=True  # 捕获异常
        )
        return True
    except Exception as e:
        print(f"无法初始化错误日志: {str(e)}")
        return False


def set_level(level):
    """设置日志级别
    :param level: 日志级别，可以是'debug', 'info', 'warning', 'error', 'critical'
    """
    global CURRENT_LOG_LEVEL
    
    if level.lower() in LOG_LEVELS:
        # 更新当前日志级别
        CURRENT_LOG_LEVEL = level.lower()
        
        try:
            # 保存到settings模块
            from src.config import settings
            settings.set_setting("log_level", level.lower())
        except ImportError:
            # 如果无法导入settings模块，忽略
            pass
        
        try:
            # 移除并重新添加控制台处理器
            if CONSOLE_HANDLER_ID is not None:
                try:
                    loguru_logger.remove(CONSOLE_HANDLER_ID)
                except:
                    pass
                
                # 重新添加控制台处理器，使用新的日志级别
                loguru_logger.add(
                    sys.stdout,
                    level=LOG_LEVELS[level.lower()],
                    format=console_format,
                    colorize=True
                )
            
            # 移除并重新添加主文件处理器
            if FILE_HANDLER_ID is not None:
                try:
                    loguru_logger.remove(FILE_HANDLER_ID)
                except:
                    pass
                
                # 确保日志目录存在
                os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
                
                # 重新添加文件处理器，使用新的日志级别
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
            

            return True
        except Exception as e:
            try:
                loguru_logger.warning(f"Failed to set log level: {str(e)}")
            except:
                loguru_logger.error(f"Failed to set log level: {str(e)}")
                print(f"Failed to set log level: {str(e)}")
            return False
    else:
        try:
            loguru_logger.warning(f"Invalid log level: {level}")
        except:
            print(f"Invalid log level: {level}")
        return False

def get_current_level():
    """获取当前日志级别"""
    return CURRENT_LOG_LEVEL

# 修改异常处理函数
def handle_exception(exc_type, exc_value, exc_traceback):
    """处理未捕获的异常，记录到日志"""
    if issubclass(exc_type, KeyboardInterrupt):
        # 不处理键盘中断
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    # 如果错误日志处理器未初始化，则初始化
    if ERROR_HANDLER_ID is None:
        add_error_handler()
        
    # 获取完整的异常信息
    tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    tb_text = ''.join(tb_lines)
    
    # 记录异常到主日志文件和错误日志文件
    try:
        # 使用 opt 方法记录完整的异常堆栈信息
        loguru_logger.opt(exception=(exc_type, exc_value, exc_traceback)).critical(
            f"未捕获的异常:\n{tb_text}"
        )
    except Exception as e:
        print(f"无法记录未捕获的异常: {str(e)}")
        print(f"原始异常: {tb_text}")

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
        try:
            loguru_logger.debug(message, *args, **kwargs)
        except Exception as e:
            print(f"DEBUG: {message}")
    
    def info(self, message, *args, **kwargs):
        """记录INFO级别日志"""
        try:
            loguru_logger.info(message, *args, **kwargs)
        except Exception as e:
            print(f"INFO: {message}")
    
    def warning(self, message, *args, **kwargs):
        """记录WARNING级别日志"""
        try:
            loguru_logger.warning(message, *args, **kwargs)
        except Exception as e:
            print(f"WARNING: {message}")
    
    def error(self, message, *args, **kwargs):
        """记录ERROR级别日志"""
        try:
            # 同时记录到主日志和错误日志
            loguru_logger.error(message, *args, **kwargs)
        except Exception as e:
            print(f"ERROR: {message}")
    
    def critical(self, message, *args, **kwargs):
        """记录CRITICAL级别日志"""
        try:
            # 同时记录到主日志和错误日志
            loguru_logger.critical(message, *args, **kwargs)
        except Exception as e:
            print(f"CRITICAL: {message}")
    
    def set_level(self, level):
        """设置日志级别"""
        return set_level(level)
    
    def get_current_level(self):
        """获取当前日志级别"""
        return CURRENT_LOG_LEVEL

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
loguru_logger.get_current_level = get_current_level  # 使用实际的函数而不是lambda

# 创建全局日志实例供其他模块导入使用
# 为了向后兼容，维持原有API
logger = loguru_logger