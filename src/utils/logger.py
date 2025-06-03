"""
日志工具模块 - 使用loguru实现
提供统一的日志记录功能，支持将日志输出到控制台和文件，
自动轮转日志文件，捕获未处理异常
"""
import os
import sys
import traceback
from loguru import logger as loguru_logger
import threading

# 判断打包环境，获取BASE_DIR
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

log_dir = os.path.join(BASE_DIR, 'log')
os.makedirs(log_dir, exist_ok=True)
log_path = os.path.abspath(os.path.join(log_dir, 'last.log'))

# 打印日志文件路径，便于调试
print(f"[Logger] Log file will be written to: {log_path}")

# 移除所有默认handler，防止重复
loguru_logger.remove()

LOG_FORMAT = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level:<8}</level> | <cyan>{module}</cyan>:[<yellow>{line}</yellow>] - {message}"

# 全局保存 handler id
log_file_handler_id = loguru_logger.add(
    log_path,
    level="DEBUG",
    encoding="utf-8",
    rotation="10 MB",
    retention="10 days",
    enqueue=True,
    backtrace=True,
    diagnose=True,
    format=LOG_FORMAT
)
console_handler_id = None
try:
    if sys.stderr is not None:
        console_handler_id = loguru_logger.add(sys.stderr, level="DEBUG", format=LOG_FORMAT)
    elif sys.stdout is not None:
        console_handler_id = loguru_logger.add(sys.stdout, level="DEBUG", format=LOG_FORMAT)
except Exception as e:
    print(f"[Logger] Failed to add console log handler: {e}")

def set_log_level(level):
    global log_file_handler_id, console_handler_id
    loguru_logger.remove(log_file_handler_id)
    if console_handler_id is not None:
        loguru_logger.remove(console_handler_id)
    log_file_handler_id = loguru_logger.add(
        log_path,
        level=level.upper(),
        encoding="utf-8",
        rotation="10 MB",
        retention="10 days",
        enqueue=True,
        backtrace=True,
        diagnose=True,
        format=LOG_FORMAT
    )
    if sys.stderr is not None:
        console_handler_id = loguru_logger.add(sys.stderr, level=level.upper(), format=LOG_FORMAT)
    elif sys.stdout is not None:
        console_handler_id = loguru_logger.add(sys.stdout, level=level.upper(), format=LOG_FORMAT)
    return log_file_handler_id, console_handler_id

# 捕获未处理异常并写入日志

def handle_exception(exc_type, exc_value, exc_traceback):
    """处理未捕获的异常，记录到日志"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    tb_text = ''.join(tb_lines)
    try:
        loguru_logger.opt(exception=(exc_type, exc_value, exc_traceback)).critical(
            f"未捕获的异常:\n{tb_text}"
        )
    except Exception as e:
        print(f"无法记录未捕获的异常: {str(e)}")
        print(f"原始异常: {tb_text}")

sys.excepthook = handle_exception

# 直接导出loguru_logger为logger，并导出set_log_level
logger = loguru_logger