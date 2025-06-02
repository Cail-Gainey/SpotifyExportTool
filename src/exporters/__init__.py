"""
导出器包
用于管理音乐导出功能
"""
from .file_exporter import FileExporter

# 导出器实例
_file_exporter = None

def get_file_exporter():
    """
    获取文件导出器实例
    
    Returns:
        FileExporter: 文件导出器实例
    """
    global _file_exporter
    if _file_exporter is None:
        _file_exporter = FileExporter()
    return _file_exporter