"""
播放列表视图的主模块
整合所有播放列表功能的主类
"""

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QTime
from PyQt5.QtGui import QPixmap
from src.utils.logger import logger
from src.utils.thread_manager import thread_manager  # 引入线程管理器

# 导入其他模块的功能
from .thread_loaders import SongLoader, ImageLoader
from .ui_components import (
    init_ui,
    adjust_responsive_ui,
    update_song_item_widths,
    _apply_button_styles,
    update_ui_texts,
)
from .song_list_manager import (
    create_song_item,
    create_song_list,
    _add_songs_batch,
    _add_next_songs_batch,
    _clear_song_list,
    filter_songs,
    sort_songs,
    select_all_songs,
    clear_song_selection,
    get_selected_song_ids,
    update_song_selection,
    on_select_all_changed,
    load_visible_song_images,
    on_search_changed,
    update_song_image,
    _process_track_data,
    update_song_labels_text,
)

# 将export_manager的导入移到函数内部，避免循环导入
def import_export_functions(self):
    """
    导入导出相关函数并绑定到self实例
    
    Args:
        self: PlaylistView实例
        
    Returns:
        tuple: 绑定到self的导出相关函数
    """
    from .export_manager import (
        toggle_export_mode,
        export_selected,
        _show_save_file_dialog,
        _on_export_finished,
    )
    
    # 将函数绑定到self实例
    def bound_toggle_export_mode():
        return toggle_export_mode(self)
        
    def bound_export_selected():
        return export_selected(self)
        
    def bound_show_save_file_dialog(export_format):
        try:
            return _show_save_file_dialog(self, export_format)
        except KeyboardInterrupt:
            logger.warning("文件保存对话框被用户中断")
            return ""
        except Exception as e:
            logger.error(f"调用文件保存对话框时发生错误: {str(e)}", exc_info=True)
            return ""
        
    def bound_on_export_finished(dialog, success, error, file_path):
        return _on_export_finished(self, dialog, success, error, file_path)
    
    return (
        bound_toggle_export_mode,
        bound_export_selected,
        bound_show_save_file_dialog,
        bound_on_export_finished,
    )


class PlaylistView(QWidget):
    """播放列表视图类

    用于显示Spotify播放列表，并提供歌曲浏览、搜索、排序和导出功能
    """

    # 定义信号
    loaded_signal = pyqtSignal(bool, str)

    def __init__(
        self,
        parent=None,
        spotify_client=None,
        playlist_id=None,
        playlist_name=None,
        cache_manager=None,
        config=None,
        locale_manager=None,
    ):
        """初始化播放列表视图

        Args:
            parent: 父窗口
            spotify_client: Spotify客户端
            playlist_id: 播放列表ID
            playlist_name: 播放列表名称
            cache_manager: 缓存管理器
            config: 配置管理器
            locale_manager: 语言管理器
        """
        super().__init__(parent)
        self.spotify_client = spotify_client
        self.playlist_id = playlist_id
        self.playlist_name = playlist_name or "未知播放列表"
        self.cache_manager = cache_manager
        self.config = config
        self.locale_manager = locale_manager

        # 初始化属性
        self.current_songs = []  # 当前显示的歌曲列表
        self.song_items = {}  # 所有歌曲项的引用
        self.image_cache = {}  # 图片缓存
        self.is_loading = False  # 是否正在加载歌曲
        self.is_creating_list = False  # 是否正在创建歌曲列表
        self.is_redrawing = False  # 是否正在重绘UI
        self.export_mode = False  # 是否处于导出模式
        self.width_factor = 1.0  # 宽度因子，用于响应式布局

        # 添加滚动相关属性
        self.last_scroll_time = 0  # 上次滚动的时间
        self.scroll_throttle = 100  # 滚动节流时间间隔（毫秒）

        # 导入导出相关函数 - 在初始化UI之前导入
        (
            self.toggle_export_mode,
            self.export_selected,
            self._show_save_file_dialog,
            self._on_export_finished,
        ) = import_export_functions(self)

        # 初始化UI
        self.init_ui()

        # 加载播放列表
        if self.playlist_id:
            self.load_playlist()

        # 监听窗口大小变化
        self.resizeEvent = self.on_resize

    # 导入UI组件模块的方法
    init_ui = init_ui
    adjust_responsive_ui = adjust_responsive_ui
    update_song_item_widths = update_song_item_widths
    _apply_button_styles = _apply_button_styles
    update_ui_texts = update_ui_texts

    # 导入歌曲列表管理模块的方法
    create_song_item = create_song_item
    create_song_list = create_song_list
    _add_songs_batch = _add_songs_batch
    _add_next_songs_batch = _add_next_songs_batch
    _clear_song_list = _clear_song_list
    filter_songs = filter_songs
    sort_songs = sort_songs
    select_all_songs = select_all_songs
    clear_song_selection = clear_song_selection
    get_selected_song_ids = get_selected_song_ids
    update_song_selection = update_song_selection
    on_select_all_changed = on_select_all_changed
    load_visible_song_images = load_visible_song_images
    on_search_changed = on_search_changed
    update_song_image = update_song_image
    _process_track_data = _process_track_data
    update_song_labels_text = update_song_labels_text

    def load_playlist(self, force_refresh=False):
        """加载播放列表

        Args:
            force_refresh: 是否强制刷新
        """
        # 如果已经加载过这个播放列表，且歌曲列表不为空，则直接返回
        if (not force_refresh and 
            self.current_songs and 
            len(self.current_songs) > 0):
            logger.debug(f"播放列表 {self.playlist_name} 已加载，歌曲数量: {len(self.current_songs)}")
            # 重新创建歌曲列表，确保UI正确显示
            self.create_song_list(self.current_songs)
            return

        if self.is_loading:
            logger.debug("已有播放列表加载任务在执行中，跳过")
            return

        self.is_loading = True

        # 显示加载状态
        self.status_label.setText(self.get_text("playlist.loading", "加载中..."))

        # 显示加载指示器
        if hasattr(self, "loading_indicator") and hasattr(self, "loading_container"):
            # 调整加载容器位置到播放列表图片位置
            if hasattr(self, "playlist_image"):
                rect = self.playlist_image.geometry()
                self.loading_container.setGeometry(rect)
                
            # 设置加载文本
            if hasattr(self, "loading_text"):
                self.loading_text.setText(self.get_text("playlist.loading", "加载中..."))
                
            # 启动加载动画并显示容器
            self.loading_indicator.start()
            self.loading_container.show()
            self.loading_container.raise_()  # 确保显示在最上层

        # 清空歌曲列表
        self._clear_song_list()

        # 创建加载线程
        self.song_loader = SongLoader(
            sp=self.spotify_client,
            playlist_id=self.playlist_id,
            cache_manager=self.cache_manager,
            force_refresh=force_refresh,
        )

        # 连接信号
        self.song_loader.songs_loaded.connect(self.on_songs_loaded)
        self.song_loader.load_error.connect(self.on_load_error)
        
        # 使用线程管理器注册线程
        thread_manager.register_thread(self.song_loader, 'playlist_loader')

        # 开始加载
        self.song_loader.start()

    def on_songs_loaded(self, songs, from_cache=False):
        """歌曲加载完成回调

        Args:
            songs: 加载的歌曲列表
            from_cache: 是否从缓存加载
        """
        # 停止加载指示器
        if hasattr(self, "loading_indicator"):
            self.loading_indicator.stop()
        
        if hasattr(self, "loading_container"):
            self.loading_container.hide()

        # 保存歌曲列表
        self.current_songs = songs

        # 创建歌曲列表
        self.create_song_list(songs)

        # 更新状态标签
        if from_cache:
            self.status_label.setText(self.get_text("playlist.loaded_from_cache", "从缓存加载"))
        else:
            self.status_label.setText(self.get_text("playlist.loaded", "加载完成"))

        # 加载播放列表封面
        self.load_playlist_image()

        # 加载可见歌曲的图片
        self.load_visible_song_images()

        # 重置加载状态
        self.is_loading = False

        # 发送加载完成信号
        self.loaded_signal.emit(True, self.playlist_name)

    def on_load_error(self, error):
        """加载错误回调

        Args:
            error: 错误信息
        """
        # 停止加载指示器
        if hasattr(self, "loading_indicator"):
            self.loading_indicator.stop()
            self.loading_container.hide()

        # 显示错误信息
        self.status_label.setText(self.get_text("playlist.load_error", "加载失败"))
        logger.error(f"加载播放列表时发生错误: {error}")

        # 重置加载状态
        self.is_loading = False

        # 发射加载失败信号
        self.loaded_signal.emit(False, str(error))

    def load_playlist_image(self):
        """加载播放列表封面图片"""
        # 显示加载指示器（如果还没显示）
        if hasattr(self, "loading_indicator") and hasattr(self, "loading_container"):
            if not self.loading_container.isVisible():
                # 调整加载容器位置
                if hasattr(self, "playlist_image"):
                    rect = self.playlist_image.geometry()
                    self.loading_container.setGeometry(rect)
                    
                # 设置加载文本
                if hasattr(self, "loading_text"):
                    self.loading_text.setText(self.get_text("playlist.loading_image", "加载封面..."))
                    
                # 启动加载动画
                self.loading_indicator.start()
                self.loading_container.show()
                self.loading_container.raise_()

        # 获取播放列表封面URL
        playlist_image_url = ""
        try:
            # 先从API获取
            playlist_data = self.spotify_client.playlist(self.playlist_id)
            if playlist_data and "images" in playlist_data and playlist_data["images"]:
                playlist_image_url = playlist_data["images"][0]["url"]
                logger.debug(f"从API获取到播放列表封面: {playlist_image_url}")

        except Exception as e:
            logger.error(f"获取播放列表封面时发生错误: {str(e)}")

        # 如果获取到封面URL，则加载图片
        if playlist_image_url:
            self.image_loader = ImageLoader(
                playlist_image_url, "playlist_cover", self.cache_manager
            )
            self.image_loader.image_loaded.connect(self.on_playlist_image_loaded)
            
            # 使用线程管理器注册线程
            thread_manager.register_thread(self.image_loader, 'image_loader')
            
            self.image_loader.start()
        else:
            # 如果没有获取到封面URL，隐藏加载指示器
            if hasattr(self, "loading_indicator"):
                self.loading_indicator.stop()
                
            if hasattr(self, "loading_container"):
                self.loading_container.hide()

    def on_playlist_image_loaded(self, image, track_id):
        """播放列表封面加载完成回调

        Args:
            image: QImage对象
            track_id: 标识符
        """
        if track_id != "playlist_cover":
            return

        # 隐藏加载指示器
        if hasattr(self, "loading_indicator"):
            self.loading_indicator.stop()
        
        if hasattr(self, "loading_container"):
            self.loading_container.hide()

        # 创建QPixmap
        pixmap = QPixmap.fromImage(image)

        # 设置图片
        if hasattr(self, "playlist_image"):
            self.playlist_image.setPixmap(
                pixmap.scaled(192, 192, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )

    def request_song_image(self, image_url, track_id):
        """请求加载歌曲封面图片

        Args:
            image_url: 图片URL
            track_id: 歌曲ID
        """
        # 检查是否已加载
        if track_id in self.image_cache:
            # 直接使用缓存的图片
            self.update_song_image(track_id, self.image_cache[track_id])
            return

        # 创建图片加载线程
        image_loader = ImageLoader(image_url, track_id, self.cache_manager)
        image_loader.image_loaded.connect(self.on_song_image_loaded)
        
        # 使用线程管理器注册线程
        thread_manager.register_thread(image_loader, 'image_loader')
        
        image_loader.start()

    def on_song_image_loaded(self, image, track_id):
        """歌曲封面加载完成回调

        Args:
            image: QImage对象
            track_id: 歌曲ID
        """
        # 创建QPixmap
        pixmap = QPixmap.fromImage(image)

        # 缓存图片
        self.image_cache[track_id] = pixmap

        # 更新UI
        self.update_song_image(track_id, pixmap)

    def refresh_songs(self):
        """刷新当前播放列表的歌曲"""
        # 如果正在加载，直接返回
        if self.is_loading:
            logger.debug("正在加载歌曲，跳过刷新")
            return
        
        # 强制从API刷新
        self.load_playlist(force_refresh=True)

    def on_scroll(self, value):
        """滚动事件回调

        Args:
            value: 滚动条值
        """
        try:
            # 确保属性存在
            if not hasattr(self, 'last_scroll_time'):
                self.last_scroll_time = 0
            if not hasattr(self, 'scroll_throttle'):
                self.scroll_throttle = 100

            # 限流处理
            current_time = QTime.currentTime().msecsSinceStartOfDay()
            if current_time - self.last_scroll_time < self.scroll_throttle:
                return

            self.last_scroll_time = current_time

            # 加载可见的歌曲图片
            self.load_visible_song_images()

            # 检查是否需要加载更多歌曲
            self.load_more_songs(value)
        except Exception as e:
            logger.error(f"滚动事件处理失败: {str(e)}")

    def load_more_songs(self, scroll_value):
        """根据滚动位置加载更多歌曲

        Args:
            scroll_value: 滚动条位置
        """
        # 此方法预留，用于实现虚拟滚动或延迟加载
        pass

    def on_resize(self, event):
        """窗口大小变化事件

        Args:
            event: 事件对象
        """
        # 设置节流标志，避免频繁更新
        if not hasattr(self, '_resize_timer'):
            self._resize_timer = QTimer()
            self._resize_timer.setSingleShot(True)
            self._resize_timer.timeout.connect(self._do_resize_update)
        
        # 如果正在调整，重置计时器
        if self._resize_timer.isActive():
            self._resize_timer.stop()
        
        # 延迟执行更新
        self._resize_timer.start(100)  # 100毫秒延迟
        
        # 调用父类方法
        super().resizeEvent(event)

    def _do_resize_update(self):
        """执行调整大小后的更新操作"""
        # 调整响应式布局
        self.adjust_responsive_ui()
        
        # 更新歌曲项宽度
        self.update_song_item_widths()
        
        # 短暂延迟后更新标签文本（处理省略号），确保布局已完成更新
        QTimer.singleShot(50, self.update_song_labels_text)
        
        # 再延迟一些时间加载可见的歌曲图片
        QTimer.singleShot(150, self.load_visible_song_images)
        
        logger.debug(f"窗口大小更新完成：宽度={self.width()}, 高度={self.height()}")

    def get_text(self, key, default=""):
        """获取本地化文本

        Args:
            key: 文本键
            default: 默认文本

        Returns:
            str: 本地化文本
        """
        if self.locale_manager:
            try:
                result = self.locale_manager.get_text(key, default)
                # 确保返回的是字符串
                if isinstance(result, dict):
                    logger.warning(f"get_text返回了字典而不是字符串: {key} -> {result}")
                    return default
                return result
            except Exception as e:
                logger.error(f"获取本地化文本时出错: {str(e)}")
                return default
        return default

    def _process_track_data(self, track_item):
        """
        处理Spotify API返回的track数据，提取出需要的信息
        
        Args:
            track_item: Spotify API返回的track数据项
            
        Returns:
            dict: 处理后的track数据，包含id, name, album, artist等字段
        """
        try:
            # 从track_item中提取track信息
            track = track_item.get('track', {})
            if not track:
                # 如果没有track字段，尝试直接使用track_item
                track = track_item
                
            # 提取基本信息
            track_id = track.get('id', f"unknown_{hash(str(track))}")
            track_name = track.get('name', '未知歌曲')
            
            # 提取专辑信息
            album = track.get('album', {})
            album_name = album.get('name', '未知专辑')
            
            # 提取艺术家信息
            artists = track.get('artists', [])
            artist_names = []
            for artist in artists:
                artist_names.append(artist.get('name', '未知艺术家'))
            artist_name = ', '.join(artist_names) if artist_names else '未知艺术家'
            
            # 提取图片信息
            album_images = album.get('images', [])
            image_url = album_images[0].get('url') if album_images else ''
            
            # 构造我们需要的数据结构
            processed_track = {
                'id': track_id,
                'name': track_name,
                'album': album_name,
                'artist': artist_name,
                'image_url': image_url,
                'raw_data': track  # 保留原始数据，以防后续需要
            }
            
            # 如果有original_index，保留它
            if 'original_index' in track_item:
                processed_track['original_index'] = track_item['original_index']
                
            return processed_track
        except Exception as e:
            logger.error(f"处理歌曲数据失败: {str(e)}")
            # 返回一个默认的数据结构
            return {
                'id': f"error_{hash(str(track_item))}",
                'name': '处理错误',
                'album': '未知专辑',
                'artist': '未知艺术家',
                'image_url': ''
            }

    def __del__(self):
        """析构函数，确保所有线程都安全停止"""
        # 使用线程管理器停止相关线程
        thread_manager.stop_threads('playlist_loader')
        thread_manager.stop_threads('image_loader')

    def closeEvent(self, event):
        """处理窗口关闭事件

        Args:
            event: 事件对象
        """
        # 停止相关线程
        thread_manager.stop_threads('playlist_loader')
        thread_manager.stop_threads('image_loader')
        
        # 接受关闭事件
        event.accept()
