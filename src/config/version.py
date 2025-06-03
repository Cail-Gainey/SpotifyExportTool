"""
版本号管理模块
"""
import os
import sys

# 获取程序运行目录
if getattr(sys, 'frozen', False):
    # 如果是打包后的可执行文件
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # 如果是直接运行脚本
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 默认版本信息
DEFAULT_VERSION_INFO = {
    'version': '1.1.0',
    'build_date': '2025-06-03',
    'release_notes': '修复已知问题'
}

def get_version():
    """
    获取当前版本号
    :return: 版本号字符串
    """
    return DEFAULT_VERSION_INFO['version']

def get_build_date():
    """
    获取构建日期
    :return: 构建日期字符串
    """
    return DEFAULT_VERSION_INFO['build_date']

def get_release_notes():
    """
    获取发布说明
    :return: 发布说明字符串
    """
    return DEFAULT_VERSION_INFO['release_notes'] 