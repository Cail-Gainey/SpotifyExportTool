"""
播放列表视图模块 - 导入新的模块化实现
"""
from .playlist_module import PlaylistView

# 为了向后兼容保留原始类的别名
__all__ = ["PlaylistView"]
