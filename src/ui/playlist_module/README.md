# 播放列表模块

## 简介
这个模块包含了Spotify播放列表视图的所有功能组件，通过模块化的方式组织代码，使其更容易维护和扩展。

## 目录结构
- `__init__.py`: 模块初始化文件，导出主要类
- `playlist_view.py`: 播放列表视图的主类，整合所有功能
- `thread_loaders.py`: 线程加载器类，包括SongLoader和ImageLoader
- `ui_components.py`: UI组件和布局相关功能
- `song_list_manager.py`: 歌曲列表管理相关功能
- `export_manager.py`: 歌曲导出相关功能

## 模块职责

### playlist_view.py
主类`PlaylistView`整合了所有功能模块，提供播放列表视图的主要功能。它通过组合方式引入其他模块的功能，并处理核心流程如初始化、加载播放列表和处理交互事件。

### thread_loaders.py
包含异步加载数据的线程类：
- `SongLoader`: 负责从Spotify API或缓存中加载歌曲
- `ImageLoader`: 负责从网络或缓存中加载图片

### ui_components.py
包含UI初始化和响应式布局相关功能：
- `init_ui()`: 创建和初始化用户界面
- `adjust_responsive_ui()`: 根据窗口大小调整UI组件
- `update_song_item_widths()`: 更新歌曲项的宽度比例

### song_list_manager.py
处理歌曲列表的创建、过滤、排序和选择：
- 创建和管理歌曲项
- 批量添加歌曲功能
- 过滤和排序功能
- 选择和取消选择歌曲

### export_manager.py
处理歌曲导出相关功能：
- 导出模式切换
- 导出格式选择
- 文件保存对话框
- 导出线程处理

## 使用方法
只需导入主类即可使用完整功能：
```python
from src.ui.playlist_module import PlaylistView

# 创建播放列表视图
playlist_view = PlaylistView(
    spotify_client=client,
    playlist_id="playlist_id",
    playlist_name="My Playlist",
    cache_manager=cache_manager,
    config=config,
    locale_manager=locale_manager
)
```

## 优化内容

此模块化重构主要实现了以下优化：

1. **代码组织**: 将单个大文件拆分为多个功能模块，使代码更易于维护和理解
2. **关注点分离**: 每个模块专注于一个特定功能领域
3. **可扩展性**: 可以更容易地扩展和修改特定功能而不影响其他部分
4. **代码复用**: 公共功能可以在多个地方重用
5. **性能优化**: 包含了图片懒加载、分批渲染、限流等优化技术
6. **响应式布局**: 针对不同窗口大小进行了布局优化

## 维护者
- 作者: Cail Gainey
- 邮箱: cailgainey@foxmail.com