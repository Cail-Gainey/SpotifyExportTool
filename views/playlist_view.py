"""
歌单页面视图
"""
import csv
from datetime import datetime
import os
from PyQt5.QtWidgets import (QWidget, QLabel, QPushButton, QVBoxLayout, 
                           QHBoxLayout, QFileDialog, QMessageBox, 
                           QScrollArea, QCheckBox,
                           QLineEdit, QMenu, QAction)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QTimer, QSettings, QTime
import requests
from io import BytesIO
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from utils.cache_manager import CacheManager
from utils.language_manager import LanguageManager
from utils.loading_indicator import LoadingIndicator
from utils.logger import logger

class SongLoader(QThread):
    """歌曲加载线程"""
    songs_loaded = pyqtSignal(list, bool)  # 第二个参数表示是否是从缓存加载的
    load_error = pyqtSignal(str)
    
    def __init__(self, sp, playlist_id, cache_manager, force_refresh=False):
        super().__init__()
        self.sp = sp
        self.playlist_id = playlist_id
        self.cache_manager = cache_manager
        self.force_refresh = force_refresh  # 是否强制刷新，不使用缓存
    
    def run(self):
        try:
            logger.info(f"开始加载播放列表: {self.playlist_id}，强制刷新: {self.force_refresh}")
            
            # 如果不是强制刷新，首先尝试从缓存加载
            if not self.force_refresh:
                logger.info(f"尝试从缓存加载播放列表: {self.playlist_id}")
                cached_tracks = self.cache_manager.get_cached_tracks(self.playlist_id)
                if cached_tracks:
                    logger.info(f"成功从缓存加载播放列表: {self.playlist_id}, 共{len(cached_tracks)}首歌曲")
                    # 发送加载完成信号，并标记为从缓存加载
                    self.songs_loaded.emit(cached_tracks, True)
                    return
                logger.info(f"缓存中未找到播放列表或缓存已过期: {self.playlist_id}")
            else:
                logger.info(f"强制从API刷新播放列表: {self.playlist_id}")
            
            # 如果没有缓存或强制刷新，从API加载
            tracks = []
            logger.info(f"开始从API加载播放列表: {self.playlist_id}")
            results = self.sp.playlist_tracks(self.playlist_id)
            
            # 添加原始索引
            for i, item in enumerate(results['items']):
                item['original_index'] = i + 1
                tracks.append(item)
            
            while results['next']:
                logger.info(f"加载更多播放列表歌曲，当前已加载: {len(tracks)}首")
                results = self.sp.next(results)
                for i, item in enumerate(results['items'], len(tracks) + 1):
                    item['original_index'] = i
                    tracks.append(item)
            
            # 缓存歌曲列表
            logger.info(f"播放列表加载完成，准备缓存: {self.playlist_id}, 共{len(tracks)}首歌曲")
            self.cache_manager.cache_tracks(self.playlist_id, tracks)
            
            # 发送加载完成信号，并标记为从API加载
            logger.info(f"从API加载播放列表完成: {self.playlist_id}")
            self.songs_loaded.emit(tracks, False)
            
        except Exception as e:
            logger.error(f"加载歌曲失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            self.load_error.emit(str(e))

class ImageLoader(QThread):
    """图像加载线程"""
    image_loaded = pyqtSignal(QImage, str)  # 发送图片和track ID
    
    def __init__(self, url, track_id, cache_manager):
        super().__init__()
        self.url = url
        self.track_id = track_id
        self.cache_manager = cache_manager
    
    def run(self):
        try:
            # 输出详细日志，帮助调试
            print(f"正在加载图片: {self.url} 类型: {'playlist' if self.track_id == 'playlist_cover' else 'track'}")
            
            # 确定图片类型
            image_type = 'playlist' if self.track_id == 'playlist_cover' else 'track'
            
            # 首先尝试从缓存加载
            cached_image = self.cache_manager.get_cached_image(self.url, image_type)
            if cached_image and not cached_image.isNull():
                print(f"图片已从缓存加载: {self.url}")
                self.image_loaded.emit(cached_image, self.track_id)
                return
            
            # 如果没有缓存，从网络加载
            print(f"从网络加载图片: {self.url}")
            session = requests.Session()
            retries = Retry(total=3, backoff_factor=0.5)
            session.mount('https://', HTTPAdapter(max_retries=retries))
            
            response = session.get(self.url, timeout=10)
            response.raise_for_status()
            
            # 加载图片
            img_data = BytesIO(response.content)
            image = QImage()
            image.loadFromData(img_data.getvalue())
            
            # 检查图片是否有效
            if image.isNull():
                print(f"加载的图片无效: {self.url}")
                return
                
            print(f"图片加载成功: {self.url}, 大小: {image.width()}x{image.height()}")
            
            # 缓存图片
            try:
                self.cache_manager.cache_image(self.url, image, image_type)
                print(f"图片已缓存: {self.url}")
            except Exception as cache_err:
                print(f"缓存图片失败: {str(cache_err)}")
                # 缓存失败不影响继续使用图片
            
            # 发送信号
            self.image_loaded.emit(image, self.track_id)
            
        except Exception as e:
            import traceback
            print(f"加载图片失败: {self.url} - {str(e)}")
            print(traceback.format_exc())  # 打印更详细的错误信息

class PlaylistView(QWidget):
    def __init__(self, sp, playlist, parent=None, language_manager=None, cache_manager=None):
        super().__init__(parent)
        
        # 设置最小尺寸
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        # 存储spotify客户端
        self.sp = sp
        self.playlist = playlist
        
        # 如果传入的是字典，则创建新的LanguageManager实例
        if isinstance(language_manager, dict):
            self.language_manager = LanguageManager()
        else:
            self.language_manager = language_manager or LanguageManager()
            
        self.cache_manager = cache_manager or CacheManager()
        
        # 初始化线程列表
        self.threads = []
        
        # 从QSettings中获取排序设置
        self.settings = QSettings("Spotify", "SpotifyExport")
        
        # 获取用户设置的导出格式，如果是custom则改为name-artists
        self.export_format = self.settings.value("export_format", "name-artists")
        if self.export_format == "custom":
            self.export_format = "name-artists"
            self.settings.setValue("export_format", self.export_format)
            
        # 导出字段
        self.export_fields = {
            "name": self.get_text("playlist.field_name", "歌曲名"),
            "artists": self.get_text("playlist.field_artists", "歌手"),
            "album": self.get_text("playlist.field_album", "专辑"),
            "release_date": self.get_text("playlist.field_release_date", "发行日期"),
            "duration": self.get_text("playlist.field_duration", "时长"),
            "url": self.get_text("playlist.field_url", "URL")
        }
        
        # 存储播放列表基本信息
        self.playlist_id = playlist["id"]
        self.playlist_name = playlist["name"]
        self.playlist_image_url = self._get_best_playlist_image(playlist)
        
        # 状态变量
        self.songs = []  # 存储所有歌曲
        self.visible_songs = []  # 存储过滤后的可见歌曲
        self.loaded = False  # 初始化状态
        self.is_loading = False  # 是否正在加载中
        self.is_loading_more = False  # 是否正在加载更多歌曲
        self.remaining_tracks = []  # 剩余待加载的歌曲
        self.scroll_position = 0  # 当前滚动位置
        self.sort_key = self.settings.value("playlist_sort_key", "order")  # 默认按照原始顺序排序
        self.sort_reverse = self.settings.value("playlist_sort_reverse", "false") == "true"  # 默认升序
        self.search_text = ""  # 搜索文本
        self.export_mode = False  # 是否处于导出模式
        self.width_factor = 1.0  # 宽度缩放比例
        
        # 存储歌曲选择状态（用于导出）
        self.song_checkboxes = []  # 改为列表存储复选框
        
        # UI刷新计时器
        self.update_timer = QTimer(self)
        self.update_timer.setInterval(500)  # 0.5秒
        self.update_timer.timeout.connect(self.update_ui)
        
        # 滚动优化计时器
        self.scroll_timer = QTimer(self)
        self.scroll_timer.setSingleShot(True)
        self.scroll_timer.setInterval(100)  # 0.1秒
        self.scroll_timer.timeout.connect(self.on_scroll_end)
        
        # 初始化界面
        self.init_ui()
        
        # 加载封面和歌曲
        self.load_playlist_image()
        self.load_songs()
    
        # 窗口大小变化初始值
        self.last_width = self.width()
        
        # 初始化重绘时间
        self.last_redraw_time = QTime.currentTime().msecsSinceStartOfDay()
        self.is_redrawing = False
    

        
    def init_ui(self):
        """初始化用户界面"""
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建顶部容器
        top_container = QWidget()
        top_container.setStyleSheet("background-color: #121212;")
        top_layout = QVBoxLayout(top_container)
        top_layout.setContentsMargins(30, 30, 30, 20)
        top_layout.setSpacing(20)
        
        # 创建图片容器
        image_container = QWidget()
        image_layout = QHBoxLayout(image_container)
        image_layout.setContentsMargins(0, 0, 0, 0)
        image_layout.setSpacing(20)
        
        # 创建播放列表图片标签
        self.playlist_image = QLabel()
        self.playlist_image.setFixedSize(192, 192)
        self.playlist_image.setStyleSheet("background-color: #282828; border-radius: 4px;")
        self.playlist_image.setAlignment(Qt.AlignCenter)
        
        # 创建加载指示器
        self.loading_indicator = LoadingIndicator(self)
        self.loading_indicator.setFixedSize(48, 48)
        self.loading_container = QWidget()
        loading_layout = QVBoxLayout(self.loading_container)
        loading_layout.addWidget(self.loading_indicator)
        loading_layout.setAlignment(Qt.AlignCenter)
        self.loading_container.hide()
        
        # 将加载指示器添加到图片标签
        image_layout.addWidget(self.playlist_image)
        
        # 创建信息容器
        info_container = QWidget()
        info_layout = QVBoxLayout(info_container)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(10)
        
        # 创建标题标签
        self.title_label = QLabel(self.playlist_name)
        self.title_label.setStyleSheet("color: white; font-size: 28px; font-weight: bold;")
        info_layout.addWidget(self.title_label)
        
        # 创建状态标签
        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: #b3b3b3; font-size: 14px;")
        info_layout.addWidget(self.status_label)
        
        # 创建按钮容器
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)
        button_layout.setAlignment(Qt.AlignLeft)
        
        # 创建导出按钮
        self.export_button = QPushButton(self.get_text("playlist.export_button", "导出"))
        self.export_button.setStyleSheet("""
            QPushButton {
                background-color: #1DB954;
                color: white;
                border-radius: 4px;
                padding: 5px 15px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1ED760;
            }
        """)
        self.export_button.clicked.connect(self.export_selected)
        button_layout.addWidget(self.export_button)
        
        # 创建取消导出按钮（默认隐藏）
        self.cancel_export_button = QPushButton(self.get_text("common.cancel", "取消"))
        self.cancel_export_button.setStyleSheet("""
            QPushButton {
                background-color: #333;
                color: white;
                border-radius: 4px;
                padding: 5px 15px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #444;
            }
        """)
        self.cancel_export_button.clicked.connect(self.toggle_export_mode)
        self.cancel_export_button.hide()
        button_layout.addWidget(self.cancel_export_button)
        
        # 创建全选按钮（默认隐藏）
        self.select_all_button = QPushButton(self.get_text("playlist.select_all", "全选"))
        self.select_all_button.setStyleSheet("""
            QPushButton {
                background-color: #333;
                color: white;
                border-radius: 4px;
                padding: 5px 15px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #444;
            }
        """)
        self.select_all_button.clicked.connect(self.select_all_songs)
        self.select_all_button.hide()
        button_layout.addWidget(self.select_all_button)
        
        # 创建清除选择按钮（默认隐藏）
        self.clear_selection_button = QPushButton(self.get_text("playlist.clear", "清空"))
        self.clear_selection_button.setStyleSheet("""
            QPushButton {
                background-color: #333;
                color: white;
                border-radius: 4px;
                padding: 5px 15px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #444;
            }
        """)
        self.clear_selection_button.clicked.connect(self.clear_song_selection)
        self.clear_selection_button.hide()
        button_layout.addWidget(self.clear_selection_button)
        
        # 创建全选复选框容器（默认隐藏）
        self.select_all_container = QWidget()
        select_all_layout = QHBoxLayout(self.select_all_container)
        select_all_layout.setContentsMargins(10, 0, 0, 0)
        select_all_layout.setSpacing(5)
        
        # 创建全选复选框
        self.select_all_checkbox = QCheckBox(self.get_text("playlist.select_all", "全选"))
        self.select_all_checkbox.setStyleSheet("""
            QCheckBox {
                color: white;
                font-size: 14px;
                background-color: transparent;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #b3b3b3;
                border-radius: 4px;
                background-color: transparent;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #1DB954;
                border-radius: 4px;
                background-color: #1DB954;
                image: url(./assets/check.png);
            }
        """)
        self.select_all_checkbox.stateChanged.connect(self.on_select_all_changed)
        self.select_all_checkbox.hide()
        select_all_layout.addWidget(self.select_all_checkbox)
        
        # 添加全选容器到按钮布局中
        button_layout.addWidget(self.select_all_container)
        
        # 创建刷新按钮
        self.refresh_button = QPushButton(self.get_text("playlist.refresh", "刷新"))
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #333;
                color: white;
                border-radius: 4px;
                padding: 5px 15px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #444;
            }
        """)
        self.refresh_button.clicked.connect(self.refresh_songs)
        button_layout.addWidget(self.refresh_button)
        
        # 添加按钮容器到信息布局
        info_layout.addWidget(button_container)
        
        # 添加搜索框
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText(self.get_text("playlist.search", "搜索歌曲名称..."))
        self.search_box.setStyleSheet("""
            QLineEdit {
                background-color: #333;
                color: white;
                border-radius: 4px;
                padding: 5px;
                min-width: 200px;
                max-width: 300px;
                font-size: 14px;
            }
        """)
        self.search_box.textChanged.connect(self.on_search_changed)
        info_layout.addWidget(self.search_box)
        
        # 将信息容器添加到图片布局
        image_layout.addWidget(info_container, 1)  # 1表示伸展因子
        
        # 将图片容器添加到顶部布局
        top_layout.addWidget(image_container)
        
        # 将顶部容器添加到主布局
        main_layout.addWidget(top_container)
        
        # 创建滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #121212;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #121212;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #535353;
                min-height: 30px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #636363;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background-color: #121212;
            }
        """)
        
        # 创建歌曲列表容器
        songs_container = QWidget()
        songs_container.setObjectName("songs_container")
        self.songs_layout = QVBoxLayout(songs_container)
        self.songs_layout.setContentsMargins(20, 10, 20, 10)
        self.songs_layout.setSpacing(5)
        self.songs_layout.addStretch()  # 添加弹性空间
        
        # 设置滚动区域的内容
        self.scroll_area.setWidget(songs_container)
        
        # 连接滚动信号
        self.scroll_area.verticalScrollBar().valueChanged.connect(self.on_scroll)
        
        # 将滚动区域添加到主布局
        main_layout.addWidget(self.scroll_area)
        
        # 设置窗口大小变化事件
        self.resizeEvent = self.on_resize
    
    def on_resize(self, event):
        """处理窗口大小变化事件
        :param event: 大小变化事件
        """
        # 调用父类的 resizeEvent
        super().resizeEvent(event)
        
        # 检查宽度是否发生变化
        current_width = self.width()
        if current_width != self.last_width:
            self.last_width = current_width
            
            # 避免频繁重绘
            current_time = QTime.currentTime().msecsSinceStartOfDay()
            if current_time - self.last_redraw_time > 100 and not self.is_redrawing:  # 100ms防抖
                self.is_redrawing = True
                self.adjust_responsive_ui()
                self.last_redraw_time = current_time
                self.is_redrawing = False
    
    def adjust_responsive_ui(self):
        """根据当前宽度调整UI组件大小"""
        current_width = self.width()
        
        # 根据窗口宽度动态调整组件大小
        if current_width < 800:
            # 窄屏适配
            self.width_factor = 0.8
            # 调整标题字体大小
            if hasattr(self, 'title_label') and self.title_label:
                self.title_label.setStyleSheet("color: white; font-size: 22px; font-weight: bold;")
                
            # 调整按钮字体和大小
            button_style = """
                QPushButton {
                    background-color: #333;
                    color: white;
                    border-radius: 4px;
                    padding: 4px 10px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #444;
                }
            """
            export_button_style = """
            QPushButton {
                background-color: #1DB954;
                    color: white;
                    border-radius: 4px;
                    padding: 4px 10px;
                    font-weight: bold;
                    font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1ED760;
                }
            """
            
            # 调整搜索框宽度
            if hasattr(self, 'search_box'):
                self.search_box.setStyleSheet("""
                    QLineEdit {
                        background-color: #333;
                        color: white;
                        border-radius: 4px;
                        padding: 4px;
                        min-width: 150px;
                        max-width: 200px;
                        font-size: 12px;
            }
        """)
            
            # 调整播放列表封面(顶部大封面)图片大小
            if hasattr(self, 'playlist_image') and self.playlist_image:
                self.playlist_image.setFixedSize(150, 150)
            
        elif current_width < 1000:
            # 中等宽度适配
            self.width_factor = 0.9
            # 调整播放列表封面(顶部大封面)图片大小
            if hasattr(self, 'playlist_image') and self.playlist_image:
                self.playlist_image.setFixedSize(180, 180)
                
            # 调整标题字体大小
            if hasattr(self, 'title_label') and self.title_label:
                self.title_label.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
                
            # 调整按钮字体和大小
            button_style = """
            QPushButton {
                    background-color: #333;
                color: white;
                border-radius: 4px;
                    padding: 5px 12px;
                    font-size: 13px;
            }
            QPushButton:hover {
                    background-color: #444;
                }
            """
            export_button_style = """
            QPushButton {
                    background-color: #1DB954;
                color: white;
                border-radius: 4px;
                    padding: 5px 12px;
                    font-weight: bold;
                    font-size: 13px;
            }
            QPushButton:hover {
                    background-color: #1ED760;
                }
            """
            
            # 调整搜索框宽度
            if hasattr(self, 'search_box'):
                self.search_box.setStyleSheet("""
                    QLineEdit {
                        background-color: #333;
                        color: white;
                        border-radius: 4px;
                        padding: 5px;
                        min-width: 180px;
                        max-width: 250px;
                        font-size: 13px;
            }
        """)
                
        else:
            # 宽屏适配
            self.width_factor = 1.0
            # 恢复默认播放列表封面(顶部大封面)图片大小
            if hasattr(self, 'playlist_image') and self.playlist_image:
                self.playlist_image.setFixedSize(192, 192)
                
            # 恢复标题字体大小
            if hasattr(self, 'title_label') and self.title_label:
                self.title_label.setStyleSheet("color: white; font-size: 28px; font-weight: bold;")
                
            # 标准按钮样式
            button_style = """
            QPushButton {
                    background-color: #333;
                color: white;
                border-radius: 4px;
                    padding: 5px 15px;
                    font-size: 14px;
            }
            QPushButton:hover {
                    background-color: #444;
                }
            """
            export_button_style = """
            QPushButton {
                background-color: #1DB954;
                color: white;
                border-radius: 4px;
                    padding: 5px 15px;
                    font-weight: bold;
                    font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1ED760;
                }
            """
            
            # 恢复搜索框默认样式
            if hasattr(self, 'search_box'):
                self.search_box.setStyleSheet("""
                    QLineEdit {
                        background-color: #333;
                        color: white;
                        border-radius: 4px;
                        padding: 5px;
                        min-width: 200px;
                        max-width: 300px;
                        font-size: 14px;
            }
        """)
                
        # 应用按钮样式
        if hasattr(self, 'refresh_button'):
            self.refresh_button.setStyleSheet(button_style)
        if hasattr(self, 'sort_button'):
            self.sort_button.setStyleSheet(button_style)
        if hasattr(self, 'export_button'):
            self.export_button.setStyleSheet(export_button_style)
        if hasattr(self, 'confirm_export_button'):
            self.confirm_export_button.setStyleSheet(export_button_style)
        if hasattr(self, 'cancel_export_button'):
            self.cancel_export_button.setStyleSheet(button_style)
        if hasattr(self, 'select_all_button'):
            self.select_all_button.setStyleSheet(button_style)
        if hasattr(self, 'clear_selection_button'):
            self.clear_selection_button.setStyleSheet(button_style)
        
        # 更新歌曲列表中的项目宽度 - 只调整标题和专辑列
        self.update_song_item_widths()
    
    def update_song_item_widths(self):
        """根据当前窗口宽度更新歌曲项的宽度比例"""
        # 遍历所有歌曲项，调整其内部控件的宽度
        for i in range(self.songs_layout.count() - 1):  # 减1是因为有一个stretch在最后
            item = self.songs_layout.itemAt(i)
            if item and item.widget():
                song_item = item.widget()
                
                # 更新歌曲项的布局比例
                if hasattr(song_item, 'layout') and song_item.layout():
                    layout = song_item.layout()
                    
                    # 根据宽度因子调整各列宽度
                    title_width = int(0.4 * self.width_factor * self.width())
                    album_width = int(0.3 * self.width_factor * self.width())
                    
                    # 查找标题和专辑列，调整其大小
                    for j in range(layout.count()):
                        layout_item = layout.itemAt(j)
                        if layout_item and layout_item.widget():
                            widget = layout_item.widget()
                            
                            # 确保图片容器固定大小不变，只调整标题和专辑列
                            if j == 2 and widget.objectName().startswith("artwork_"):  # 图片容器
                                # 确保保持固定大小
                                widget.setFixedSize(50, 50)
                            elif j == 3:  # 标题列
                                widget.setMinimumWidth(title_width)
                            elif j == 4:  # 专辑列
                                widget.setMinimumWidth(album_width)

    def load_playlist_info(self):
        """加载播放列表信息"""
        try:
            # 设置封面标签为"加载中"状态
            self.playlist_image.setText(self.get_text('playlist.loading', '加载中...'))
            self.playlist_image.setStyleSheet("background-color: #282828; border-radius: 4px; color: white;")
            
            playlist_info = self.sp.playlist(self.playlist_id)
            self.playlist_name = playlist_info['name']
            self.playlist_description = playlist_info.get('description', '')
            self.playlist_owner = playlist_info['owner']['display_name']
            self.playlist_track_count = playlist_info['tracks']['total']
            
            # 更新UI文本
            self.title_label.setText(self.playlist_name)
            self.status_label.setText(self.playlist_description)
            
            # 加载播放列表封面
            if playlist_info['images']:
                image_url = playlist_info['images'][0]['url']
                # 首先尝试从缓存加载
                cached_image = self.cache_manager.get_cached_image(image_url, 'playlist')
                if cached_image:
                    # 如果有缓存，直接设置
                    self.on_cover_loaded(cached_image, image_url)
                else:
                    # 否则异步加载
                    loader = ImageLoader(image_url, 'playlist_cover', self.cache_manager)
                    loader.image_loaded.connect(lambda image_id, image: self.on_cover_loaded(image, image_url))
                    self.threads.append(loader)
                    loader.start()
            else:
                # 没有图片，设置默认样式
                self.playlist_image.setText(self.get_text('playlist.no_image', '无封面'))
                
        except Exception as e:
            print(f"加载播放列表信息失败: {str(e)}")
            self.playlist_name = self.get_text('playlist.unknown_playlist', '未知播放列表')
            self.playlist_description = ''
            self.playlist_owner = self.get_text('playlist.unknown_owner', '未知创建者')
            self.playlist_track_count = 0
            # 更新UI
            self.title_label.setText(self.playlist_name)
            self.status_label.setText(self.playlist_description)
            # 设置错误状态
            self.playlist_image.setText(self.get_text('playlist.load_failed', '加载失败'))
    
    def on_cover_loaded(self, image, url):
        """封面加载完成回调"""
        try:
            # 详细日志输出
            print(f"封面加载完成: {url}")
            
            # 检查图片是否有效
            if image is None or image.isNull():
                print(f"封面图片无效: {url}")
                self.playlist_image.setText(self.get_text('playlist.load_failed', "加载失败"))
                self.playlist_image.setStyleSheet("""
                    background-color: #333;
                    color: white;
                    font-size: 14px;
                    border-radius: 4px;
                    text-align: center;
                """)
                return
                
            # 图片有效，继续处理
            print(f"封面图片有效，大小: {image.width()}x{image.height()}")
            
            # 保持矩形封面，不再创建圆形封面
            target_size = 192
            scaled_image = image.scaled(target_size, target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            # 缓存封面
            try:
                self.cache_manager.cache_image(url, scaled_image, 'playlist')
                print(f"封面图片已缓存: {url}")
            except Exception as cache_err:
                print(f"缓存封面图片失败: {str(cache_err)}")
                # 缓存失败不影响继续使用图片
            
            # 设置封面图片
            pixmap = QPixmap.fromImage(scaled_image)
            if not pixmap.isNull():
                self.playlist_image.setPixmap(pixmap)
                print(f"封面图片已设置到UI, 大小: {pixmap.width()}x{pixmap.height()}")
            else:
                print(f"从QImage创建QPixmap失败")
                self.playlist_image.setText(self.get_text('playlist.load_failed', "加载失败"))
        except Exception as e:
            import traceback
            print(f"设置封面图片时出错: {str(e)}")
            print(traceback.format_exc())
            self.playlist_image.setText(self.get_text('playlist.load_failed', "加载失败"))

    def paintEvent(self, event):
        """绘制事件处理"""
        # 如果主窗口正在调整布局，延迟绘制
        if hasattr(self.window(), 'is_adjusting_layout') and self.window().is_adjusting_layout:
            event.accept()
            return
            
        # 如果两次重绘时间间隔太短，跳过这次重绘
        current_time = QTime.currentTime().msecsSinceStartOfDay()
        if current_time - self.last_redraw_time < 50:  # 50毫秒内不重复重绘
            event.accept()
            return
            
        # 设置标志，防止在重绘过程中触发其他更新
        self.is_redrawing = True
        
        # 暂停子控件更新以减少重绘次数
        self.setUpdatesEnabled(False)
        
        try:
            # 调用父类的绘制方法
            super().paintEvent(event)
        finally:
            # 无论是否成功都要重置标志
            self.is_redrawing = False
            self.last_redraw_time = QTime.currentTime().msecsSinceStartOfDay()
            
            # 恢复更新
            self.setUpdatesEnabled(True)
            
    def update(self):
        """重写更新方法，避免过于频繁的刷新"""
        # 如果主窗口正在调整布局，延迟更新
        if hasattr(self.window(), 'is_adjusting_layout') and self.window().is_adjusting_layout:
            QTimer.singleShot(150, self._delayed_update)
            return
            
        # 避免过于频繁的更新
        current_time = QTime.currentTime().msecsSinceStartOfDay()
        if self.is_redrawing or (current_time - self.last_redraw_time < 100):
            # 如果正在重绘或者距离上次重绘时间太短，则延迟更新
            QTimer.singleShot(100, self._delayed_update)
            return
            
        # 执行实际更新
        self.last_redraw_time = QTime.currentTime().msecsSinceStartOfDay()
        super().update() 

    def _delayed_update(self):
        """延迟执行的更新"""
        # 如果主窗口仍在调整布局，再次延迟
        if hasattr(self.window(), 'is_adjusting_layout') and self.window().is_adjusting_layout:
            QTimer.singleShot(100, self._delayed_update)
            return
            
        if not self.is_redrawing:
            self.last_redraw_time = QTime.currentTime().msecsSinceStartOfDay()
            super().update()

    def load_more_songs(self):
        """加载更多歌曲，优化批量加载性能"""
        if not self.remaining_tracks or self.is_loading_more:
            return
            
        # 标记为正在加载中
        self.is_loading_more = True
            
        # 获取当前歌曲容器
        songs_container = self.findChild(QWidget, "songs_container")
        if not songs_container:
            self.is_loading_more = False
            return
        
        # 暂停UI更新以提高性能
        songs_container.setUpdatesEnabled(False)
            
        # 获取当前已加载的歌曲数量
        songs_container_layout = songs_container.layout()
        current_count = songs_container_layout.count()
        
        # 加载下一批歌曲（每次加载30首，对大播放列表更友好）
        next_batch = self.remaining_tracks[:30]
        self.remaining_tracks = self.remaining_tracks[30:]
        
        logger.debug(f"加载下一批歌曲: {len(next_batch)}首, 剩余: {len(self.remaining_tracks)}首")
        
        # 添加下一批歌曲
        for i, item in enumerate(next_batch):
            track = item['track']
            if track:
                row = self.create_song_row(i, item)
                songs_container_layout.addWidget(row)
        
        # 恢复UI更新
        songs_container.setUpdatesEnabled(True)
        
        # 延迟加载可见图片
        QTimer.singleShot(100, self.lazy_load_visible_images)
        
        # 检查是否还有剩余歌曲需要加载
        if not self.remaining_tracks:
            # 直接调用清理方法，避免重复清理
            logger.info("所有歌曲加载完成，清理底部加载指示器")
            self._cleanup_bottom_loading_indicators()
            # 设置已清理标志为True
            self._bottom_indicators_cleaned = True
        
        # 标记加载完成
        self.is_loading_more = False

    def showEvent(self, event):
        """显示事件处理，当视图变为可见时优化性能"""
        super().showEvent(event)
        # 延迟加载图片，避免一次性加载太多图片导致卡顿
        QTimer.singleShot(100, self.lazy_load_visible_images)
        
    def hideEvent(self, event):
        """隐藏事件处理，优化资源使用"""
        super().hideEvent(event)
        # 停止不必要的线程
        self.stop_background_threads()
        
    def lazy_load_visible_images(self):
        """延迟加载当前可见的图片"""
        # 仅在页面可见时加载
        if not self.isVisible():
            return

        # 遍历所有可见的歌曲行，加载所有图片
        for i in range(self.songs_layout.count()):
            widget_item = self.songs_layout.itemAt(i)
            if widget_item and widget_item.widget():
                songs_container = widget_item.widget()
                if isinstance(songs_container, QWidget) and songs_container.objectName() == "songs_container":
                    # 遍历歌曲容器中的所有行
                    container_layout = songs_container.layout()
                    if container_layout:
                        for j in range(container_layout.count()):
                            item = container_layout.itemAt(j)
                            if item and item.widget():
                                row_widget = item.widget()
                                
                                # 跳过加载更多按钮和其他非歌曲行小部件
                                if not row_widget.findChild(QWidget, f"checkbox_container_{j}"):
                                    continue
                                
                                # 获取歌曲封面
                                cover_label = row_widget.findChild(QLabel, "cover_label")
                                if cover_label and j < len(self.tracks):
                                    # 根据索引从 tracks 中获取歌曲信息
                                    track = self.tracks[j]['track']
                                    if track and track['album']['images']:
                                        image_url = track['album']['images'][-1]['url']
                                        image_id = f"track_{track['id']}"
                                        # 仅当封面未加载过时加载图片
                                        if cover_label.text() == "...":
                                            self.load_image(image_url, image_id, cover_label, 50, 50)

    def stop_background_threads(self):
        """停止所有后台线程"""
        for thread in self.threads:
            thread.quit()
            thread.wait()

        self.threads.clear() 

    def on_select_all_changed(self, state):
        """处理全选复选框状态变化"""
        for checkbox in self.song_checkboxes:
            if checkbox and checkbox.parent() is not None:
                checkbox.setChecked(state == Qt.Checked)
    
    def select_all_songs(self):
        """选择所有歌曲"""
        if hasattr(self, 'select_all_checkbox'):
            self.select_all_checkbox.setChecked(True)
    
    def clear_song_selection(self):
        """清除所有歌曲选择"""
        if hasattr(self, 'select_all_checkbox'):
            self.select_all_checkbox.setChecked(False)
            for checkbox in self.song_checkboxes:
                if checkbox and checkbox.parent() is not None:
                    checkbox.setChecked(False)
    
    def export_selected(self):
        """导出选中的歌曲"""
        if not hasattr(self, 'export_mode'):
            self.export_mode = False
            
        if not self.export_mode:
            self.toggle_export_mode()
            return

        # 获取所选歌曲索引
        selected_indices = []
        for i, checkbox in enumerate(self.song_checkboxes):
            if checkbox and checkbox.parent() is not None and checkbox.isChecked():
                selected_indices.append(i)

        # 如果没有选中任何歌曲
        if not selected_indices:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle(self.get_text('common.warning', '警告'))
            msg_box.setText(self.get_text('playlist.no_selection', '请至少选择一首歌曲'))
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: #1E1E1E;
                }
                QMessageBox QLabel {
                    color: #FFFFFF;
                    font-size: 14px;
                    padding: 10px;
                    min-width: 300px;
                }
                QPushButton {
                    background-color: #333;
                    color: #FFFFFF;
                    border: none;
                    border-radius: 4px;
                    padding: 5px 15px;
                    font-size: 13px;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #404040;
                }
            """)
            msg_box.exec_()
            return

        # 询问保存路径
        dir_path = QFileDialog.getExistingDirectory(
            self,
            self.get_text('playlist.select_dir', '选择保存目录'),
            options=QFileDialog.ShowDirsOnly
        )

        if not dir_path:
            return

        try:
            # 从设置中获取导出格式和文件类型
            # 使用成员变量中的 export_format 而不是重新读取设置
            export_format = self.export_format
            export_as_txt = self.settings.value("export_use_txt", "true") == "true"

            # 准备要导出的歌曲
            selected_tracks = []
            for idx in selected_indices:
                try:
                    if idx < len(self.visible_songs):
                        track_data = self.visible_songs[idx]
                        if not isinstance(track_data, dict):
                            continue
                        track = track_data.get('track')
                        if not isinstance(track, dict):
                            continue
                            
                        # 获取艺术家名称
                        artists = []
                        for artist in track.get('artists', []):
                            if isinstance(artist, dict):
                                artist_name = artist.get('name')
                                if artist_name:
                                    artists.append(artist_name)
                        artists_str = ', '.join(artists)
                        
                        # 获取专辑信息
                        album = track.get('album', {})
                        album_name = album.get('name', '') if isinstance(album, dict) else ''
                        album_date = album.get('release_date', '') if isinstance(album, dict) else ''
                        
                        # 获取时长
                        duration_ms = track.get('duration_ms', 0)
                        minutes = duration_ms // 60000
                        seconds = (duration_ms % 60000) // 1000
                        duration = f'{minutes}:{seconds:02d}'
                        
                        # 获取歌曲名称和URL
                        name = track.get('name', '')
                        url = track.get('external_urls', {}).get('spotify', '')
                        
                        if name:  # 只添加有名称的歌曲
                            track_info = {
                                'name': name,
                                'artists': artists_str,
                                'album': album_name,
                                'release_date': album_date,
                                'duration': duration,
                                'url': url
                            }
                            selected_tracks.append(track_info)
                except Exception as e:
                    print(f"处理歌曲数据时出错: {str(e)}")
                    continue

            # 如果有选中的歌曲，写入文件
            if selected_tracks:
                current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
                safe_playlist_name = self.playlist_name.replace('/', '_').replace('\\', '_')
                file_name = f"SpotifyExport-{safe_playlist_name}-{current_time}"

                if export_as_txt:
                    # 导出为txt文件
                    file_path = os.path.join(dir_path, f"{file_name}.txt")
                    with open(file_path, 'w', encoding='utf-8') as txtfile:
                        for track in selected_tracks:
                            formatted_name = self.format_track_name(track)
                            if formatted_name:  # 只写入有效的歌曲名称
                                txtfile.write(f"{formatted_name}\n")
                else:
                    # 导出为CSV文件
                    file_path = os.path.join(dir_path, f"{file_name}.csv")
                    
                    # 根据导出格式动态确定CSV字段
                    if export_format == "name":
                        fieldnames = ['name']
                    elif export_format == "name-artists":
                        fieldnames = ['name', 'artists']
                    elif export_format == "artists-name":
                        fieldnames = ['artists', 'name']
                    elif export_format == "name-artists-album":
                        fieldnames = ['name', 'artists', 'album']
                    elif export_format == "full":
                        fieldnames = ['name', 'artists', 'album', 'release_date', 'duration', 'url']
                    else:
                        # 默认使用名称和艺术家
                        fieldnames = ['name', 'artists']
                    
                    with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
                        
                        # 检查是否需要写入标题行 (默认不写入)
                        show_header = self.settings.value("export_show_header", "false") == "true"
                        if show_header:
                            # 使用本地化的标题
                            localized_headers = {}
                            for field in fieldnames:
                                localized_headers[field] = self.export_fields.get(field, field)
                            writer.writerow(localized_headers)
                            
                        # 写入数据行
                        for track in selected_tracks:
                            writer.writerow(track)

                # 显示成功消息
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle(self.get_text('common.success', '成功'))
                msg_box.setText(self.get_text('playlist.export_success', '已成功导出 {0} 首歌曲到 {1}').format(
                    len(selected_tracks), file_path))
                msg_box.setIcon(QMessageBox.Information)
                msg_box.setStyleSheet("""
                    QMessageBox {
                        background-color: #1E1E1E;
                    }
                    QMessageBox QLabel {
                        color: #FFFFFF;
                        font-size: 14px;
                        padding: 10px;
                        min-width: 300px;
                    }
                    QPushButton {
                        background-color: #1DB954;
                        color: #FFFFFF;
                        border: none;
                        border-radius: 4px;
                        padding: 5px 15px;
                        font-size: 13px;
                        min-width: 80px;
                    }
                    QPushButton:hover {
                        background-color: #1ED760;
                    }
                """)
                msg_box.exec_()
            else:
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle(self.get_text('common.warning', '警告'))
                msg_box.setText(self.get_text('playlist.no_valid_tracks', '没有有效的歌曲数据'))
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.setStyleSheet("""
                    QMessageBox {
                        background-color: #1E1E1E;
                    }
                    QMessageBox QLabel {
                        color: #FFFFFF;
                        font-size: 14px;
                        padding: 10px;
                        min-width: 300px;
                    }
                    QPushButton {
                        background-color: #333;
                        color: #FFFFFF;
                        border: none;
                        border-radius: 4px;
                        padding: 5px 15px;
                        font-size: 13px;
                        min-width: 80px;
                    }
                    QPushButton:hover {
                        background-color: #404040;
                    }
                """)
                msg_box.exec_()

        except Exception as e:
            # 显示错误消息
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle(self.get_text('common.error', '错误'))
            msg_box.setText(self.get_text('playlist.export_error', '导出失败: {0}').format(str(e)))
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: #1E1E1E;
                }
                QMessageBox QLabel {
                    color: #FFFFFF;
                    font-size: 14px;
                    padding: 10px;
                    min-width: 300px;
                }
                QPushButton {
                    background-color: #333;
                    color: #FFFFFF;
                    border: none;
                    border-radius: 4px;
                    padding: 5px 15px;
                    font-size: 13px;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #404040;
                }
            """)
            msg_box.exec_()

        # 导出完成后，返回正常模式
        self.toggle_export_mode()
    
    def format_track_name(self, track_info):
        """根据设置的导出格式格式化歌曲名称
        :param track_info: 歌曲信息字典
        :return: 格式化后的歌曲名称
        """
        try:
            # 确保所有必需的字段都存在
            name = track_info.get('name', '')
            artists = track_info.get('artists', '')
            album = track_info.get('album', '')
            
            # 每次在使用前刷新导出格式设置，确保使用最新设置
            self.refresh_export_format()
            export_format = self.export_format
            
            if not name:  # 如果没有歌曲名称，返回空字符串
                return ''
                
            if export_format == "name-artists":
                return f"{name} - {artists}" if artists else name
            elif export_format == "artists-name":
                return f"{artists} - {name}" if artists else name
            elif export_format == "name":
                return name
            elif export_format == "name-artists-album":
                if artists and album:
                    return f"{name} - {artists} - {album}"
                elif artists:
                    return f"{name} - {artists}"
                else:
                    return name
            elif export_format == "full":
                if artists and album:
                    return f"{name} - {artists} ({album})"
                elif artists:
                    return f"{name} - {artists}"
                else:
                    return name
            else:
                # 默认使用 name-artists 格式
                return f"{name} - {artists}" if artists else name
            
        except Exception as e:
            print(f"格式化歌曲名称时出错: {str(e)}")
            # 发生错误时返回歌曲名称或空字符串
            if isinstance(track_info, dict) and 'name' in track_info:
                return track_info['name']
            elif isinstance(track_info, str):
                return track_info
            return ''
    
    def toggle_export_mode(self):
        """切换导出模式"""
        self.export_mode = not self.export_mode
        
        # 更新按钮文本
        if self.export_mode:
            # 在切换到导出模式时刷新导出格式设置
            self.refresh_export_format()
            
            # 更改主导出按钮文本
            self.export_button.setText(self.get_text("playlist.export_confirm", "确认导出"))
            
            # 显示导出相关控件
            if hasattr(self, 'cancel_export_button'):
                self.cancel_export_button.show()
            if hasattr(self, 'select_all_button'):
                self.select_all_button.show()
            if hasattr(self, 'clear_selection_button'):
                self.clear_selection_button.show()
            if hasattr(self, 'select_all_container'):
                self.select_all_container.show()
                
            # 隐藏非导出相关控件
            if hasattr(self, 'refresh_button'):
                self.refresh_button.hide()
                
            # 移除显示导出模式提示信息的代码
                
        else:
            # 恢复主导出按钮文本
            self.export_button.setText(self.get_text("playlist.export_button", "导出"))
            
            # 隐藏导出相关控件
            if hasattr(self, 'cancel_export_button'):
                self.cancel_export_button.hide()
            if hasattr(self, 'select_all_button'):
                self.select_all_button.hide()
            if hasattr(self, 'clear_selection_button'):
                self.clear_selection_button.hide()
            if hasattr(self, 'select_all_container'):
                self.select_all_container.hide()
                
            # 显示非导出相关控件
            if hasattr(self, 'refresh_button'):
                self.refresh_button.show()
        
        # 更新复选框可见性
        self.update_checkbox_visibility(self.export_mode)
        
        # 清除所有选择
        if not self.export_mode:
            for checkbox in self.song_checkboxes:
                if checkbox and checkbox.parent() is not None:
                    checkbox.setChecked(False)
            if hasattr(self, 'select_all_checkbox'):
                self.select_all_checkbox.setChecked(False)
                
    def refresh_export_format(self):
        """刷新导出格式设置"""
        export_format = self.settings.value("export_format", "name-artists")
        # 如果是自定义格式，改为默认格式
        if export_format == "custom":
            export_format = "name-artists"
            self.settings.setValue("export_format", export_format)
        self.export_format = export_format
    
    def update_checkbox_visibility(self, visible):
        """更新所有复选框容器的可见性"""
        songs_container = self.findChild(QWidget, "songs_container")
        if songs_container and songs_container.layout():
            container_layout = songs_container.layout()
            for i in range(container_layout.count()):
                item = container_layout.itemAt(i)
                if item and item.widget():
                    row_widget = item.widget()
                    # 查找checkbox_container
                    checkbox_container = row_widget.findChild(QWidget, f"checkbox_container_{i}")
                    if checkbox_container:
                        checkbox_container.setVisible(visible)
    
    def on_sort_changed(self, index):
        """排序方式改变事件"""
        sort_key = self.sort_combo.itemData(index)
        if sort_key == self.sort_key:
            return
        
        self.sort_key = sort_key
        self.settings.setValue("playlist_sort_key", sort_key)
        self.reload_songs()
    
    def on_sort_order_changed(self):
        """排序顺序改变事件"""
        self.sort_reverse = not self.sort_reverse
        self.sort_order.setText("↓" if self.sort_reverse else "↑")
        self.settings.setValue("playlist_sort_reverse", "true" if self.sort_reverse else "false")
        self.reload_songs()
    
    def reload_songs(self):
        """重新加载歌曲列表"""
        # 清空现有布局
        for i in reversed(range(self.songs_layout.count())):
            item = self.songs_layout.itemAt(i)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
        
        # 重新创建歌曲列表
        self.create_song_list()
    
    def sort_tracks_by_key(self, tracks, key, reverse):
        """根据指定键排序歌曲列表"""
        def get_sort_value(item):
            track = item.get('track', {})
            if not track:
                return ""
                
            if key == "name":
                return track.get('name', "").lower()
            elif key == "artist":
                artists = track.get('artists', [])
                return artists[0].get('name', "").lower() if artists else ""
            elif key == "album":
                album = track.get('album', {})
                return album.get('name', "").lower() if album else ""
            elif key == "duration":
                return track.get('duration_ms', 0)
            elif key == "added_at":
                return item.get('added_at', "")
            else:
                return ""
                
        return sorted(tracks, key=get_sort_value, reverse=reverse) 

    def check_for_load_more(self):
        """检查是否需要加载更多歌曲，并加载可见图片"""
        # 加载可见图片
        self.lazy_load_visible_images()
        
        # 如果没有更多歌曲，清理所有底部加载动画并返回
        if not self.remaining_tracks:
            # 定义一个静态属性，用于跟踪指示器清理状态，避免重复清理
            if not hasattr(self, '_bottom_indicators_cleaned'):
                self._bottom_indicators_cleaned = False
                
            if not self._bottom_indicators_cleaned:
                # 直接调用清理方法并根据返回结果设置标志
                if self._cleanup_bottom_loading_indicators():
                    logger.info("底部加载指示器已清理完成")
                    self._bottom_indicators_cleaned = True
            return
        else:
            # 如果有更多歌曲要加载，重置清理标志
            self._bottom_indicators_cleaned = False
            
        # 如果已经在加载中，直接返回
        if self.is_loading_more:
            return
            
        # 获取滚动区域和滚动条
        scrollbar = self.scroll_area.verticalScrollBar()
        
        # 计算滚动区域底部位置
        max_value = scrollbar.maximum()
        current_value = scrollbar.value()
        
        # 如果滚动到接近底部(在底部90%的区域)，自动加载更多歌曲
        if max_value > 0 and current_value > max_value * 0.9:
            logger.info(f"滚动到底部区域，准备加载更多歌曲")
            self.load_more_songs()

    def validate_custom_format(self, format_string):
        """验证自定义格式是否有效
        :param format_string: 自定义格式字符串
        :return: 是否有效
        """
        # 如果自定义格式为空，则无效
        if not format_string:
            return False
            
        # 检查格式字符串中是否包含至少一个有效的字段
        valid_fields = False
        for field in self.export_fields.keys():
            if "{" + field + "}" in format_string:
                valid_fields = True
                break
                
        return valid_fields
        
    def update_song_count(self):
        """更新歌曲计数标签"""
        # 更新状态标签，显示当前显示的歌曲数量和总歌曲数量
        if self.loaded:
            if self.search_text:
                # 当用户搜索时，显示搜索结果数量
                self.status_label.setText(
                    self.language_manager.get_text(
                        'playlist.search_results', 
                        "显示 {0}/{1} 首歌曲"
                    ).format(len(self.visible_songs), len(self.songs))
                )
            else:
                # 当没有搜索条件时，显示总歌曲数量
                self.status_label.setText(
                    self.language_manager.get_text(
                        'playlist.song_count', 
                        "{0} 首歌曲"
                    ).format(len(self.songs))
                )

    def create_song_row(self, index, song):
        """创建歌曲行
        :param index: 歌曲在当前视图中的索引
        :param song: 歌曲数据
        :return: 歌曲行控件
        """
        track = song.get('track', {})
        if not track:
            return None
            
        # 创建歌曲行容器
        song_container = QWidget()
        song_container.setFixedHeight(60)  # 统一高度
        song_container.setStyleSheet("""
            QWidget {
                background-color: #121212;
                border-radius: 4px;
            }
            QWidget:hover {
                background-color: #282828;
            }
        """)
        
        # 歌曲行布局
        song_layout = QHBoxLayout(song_container)
        song_layout.setContentsMargins(20, 5, 20, 5)
        song_layout.setSpacing(10)
        
        # 歌曲选择复选框（导出模式下）
        checkbox_container = QWidget()
        checkbox_container.setObjectName(f"checkbox_container_{index}")
        checkbox_container.setFixedWidth(40)
        checkbox_container.setStyleSheet("background-color: transparent;")
        checkbox_layout = QHBoxLayout(checkbox_container)
        checkbox_layout.setContentsMargins(0, 0, 0, 0)
        checkbox_layout.setAlignment(Qt.AlignCenter)
        
        # 创建复选框
        checkbox = QCheckBox()
        checkbox.setStyleSheet("""
            QCheckBox {
                background-color: transparent;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #b3b3b3;
                border-radius: 4px;
                background-color: transparent;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #1DB954;
                border-radius: 4px;
                background-color: #1DB954;
                image: url(./assets/check.png);
            }
        """)
        
        # 存储复选框引用
        if track.get('id'):
            self.song_checkboxes.append(checkbox)
        
        # 将复选框添加到容器中
        checkbox_layout.addWidget(checkbox)
        
        # 默认隐藏复选框容器
        checkbox_container.setVisible(self.export_mode)
        
        # 将复选框容器添加到布局的最左侧
        song_layout.addWidget(checkbox_container)
        
        # 创建一个透明背景的序号容器
        number_container = QWidget()
        number_container.setStyleSheet("background-color: transparent;")
        number_container.setFixedWidth(30)
        number_layout = QHBoxLayout(number_container)
        number_layout.setContentsMargins(0, 0, 0, 0)
        number_layout.setSpacing(0)
        
        # 歌曲序号添加到容器中
        number_label = QLabel(str(song.get('original_index', index + 1)))
        number_label.setStyleSheet("color: #b3b3b3; font-size: 14px; background-color: transparent;")
        number_label.setAlignment(Qt.AlignCenter)
        number_layout.addWidget(number_label)
        
        # 添加序号容器到主布局
        song_layout.addWidget(number_container)
        
        # 根据用户设置决定是否显示专辑封面
        if self.settings.value("playlist_show_artwork", True, type=bool):
            # 创建固定大小的封面图片容器
            artwork_container = QLabel()
            artwork_container.setObjectName(f"artwork_{track.get('id', '')}")
            # 固定大小，不随窗口自适应改变
            artwork_container.setFixedSize(50, 50)
            artwork_container.setAlignment(Qt.AlignCenter)
            artwork_container.setStyleSheet("background-color: #333; border-radius: 4px;")
            
            # 获取专辑封面URL
            album = track.get('album', {})
            if album and album.get('images'):
                image_url = album['images'][-1]['url']  # 使用最小的图片
                
                # 尝试从缓存加载
                cached_image = self.cache_manager.get_cached_image(image_url, 'track')
                if cached_image:
                    pixmap = QPixmap.fromImage(cached_image)
                    # 使用固定大小缩放
                    scaled_pixmap = pixmap.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    artwork_container.setPixmap(scaled_pixmap)
                else:
                    # 设置占位符
                    artwork_container.setText("...")
                    
                    # 创建加载线程
                    loader = ImageLoader(image_url, track.get('id', ''), self.cache_manager)
                    loader.image_loaded.connect(self.on_track_image_loaded)
                    self.threads.append(loader)
                    loader.start()
            else:
                # 没有图片时显示默认图标
                artwork_container.setText("🎵")
            
            # 添加固定大小的封面容器
            song_layout.addWidget(artwork_container)
        
        # 歌曲标题和艺术家信息
        title_container = QWidget()
        title_container.setStyleSheet("background-color: transparent;")
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(2)
        
        # 歌曲标题
        title_label = QLabel(track.get('name', '未知歌曲'))
        title_label.setStyleSheet("color: white; font-size: 14px; background-color: transparent;")
        title_label.setWordWrap(True)
        title_label.setTextFormat(Qt.PlainText)  # 使用纯文本格式，避免HTML注入
        title_layout.addWidget(title_label)
        
        # 艺术家
        artist_names = []
        for artist in track.get('artists', []):
            artist_names.append(artist.get('name', ''))
        
        artists_label = QLabel(', '.join(artist_names) if artist_names else '未知艺术家')
        artists_label.setStyleSheet("color: #b3b3b3; font-size: 12px; background-color: transparent;")
        artists_label.setWordWrap(True)
        artists_label.setTextFormat(Qt.PlainText)  # 使用纯文本格式，避免HTML注入
        title_layout.addWidget(artists_label)
        
        # 根据宽度因子计算标题容器的宽度
        title_width = int(0.4 * self.width_factor * self.width())
        title_container.setMinimumWidth(title_width)
        
        song_layout.addWidget(title_container, 1)
        
        # 专辑
        album_container = QWidget()
        album_container.setStyleSheet("background-color: transparent;")
        album_layout = QVBoxLayout(album_container)
        album_layout.setContentsMargins(0, 0, 0, 0)
        album_layout.setSpacing(2)
        
        # 专辑名称
        album_name = track.get('album', {}).get('name', '未知专辑')
        album_label = QLabel(album_name)
        album_label.setStyleSheet("color: #b3b3b3; font-size: 14px; background-color: transparent;")
        album_label.setWordWrap(True)
        album_label.setTextFormat(Qt.PlainText)  # 使用纯文本格式，避免HTML注入
        album_layout.addWidget(album_label)
        
        # 专辑发行年份
        release_date = track.get('album', {}).get('release_date', '')
        if release_date:
            try:
                # 尝试提取年份
                year = release_date.split('-')[0]
                release_label = QLabel(year)
                release_label.setStyleSheet("color: #b3b3b3; font-size: 12px; background-color: transparent;")
                album_layout.addWidget(release_label)
            except:
                # 如果格式不是YYYY-MM-DD，则直接显示原始日期
                release_label = QLabel(release_date)
                release_label.setStyleSheet("color: #b3b3b3; font-size: 12px; background-color: transparent;")
                album_layout.addWidget(release_label)
        
        # 根据宽度因子计算专辑容器的宽度
        album_width = int(0.3 * self.width_factor * self.width())
        album_container.setMinimumWidth(album_width)
        
        song_layout.addWidget(album_container, 1)
        
        # 创建一个透明背景的时长容器
        duration_container = QWidget()
        duration_container.setStyleSheet("background-color: transparent;")
        duration_container.setFixedWidth(80)
        duration_layout = QHBoxLayout(duration_container)
        duration_layout.setContentsMargins(0, 0, 0, 0)
        duration_layout.setSpacing(0)
        duration_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        # 歌曲时长
        duration_ms = track.get('duration_ms', 0)
        minutes = duration_ms // 60000
        seconds = (duration_ms % 60000) // 1000
        duration_str = f"{minutes}:{seconds:02d}"
        
        duration_label = QLabel(duration_str)
        duration_label.setStyleSheet("color: #b3b3b3; font-size: 14px; background-color: transparent;")
        duration_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        duration_layout.addWidget(duration_label)
        
        # 添加时长容器到主布局
        song_layout.addWidget(duration_container)
        
        return song_container

    def on_track_image_loaded(self, image, track_id):
        """歌曲图片加载完成回调
        :param image: 加载的图片
        :param track_id: 歌曲ID
        """
        try:
            # 详细日志
            print(f"歌曲封面加载完成: track_id={track_id}")
            
            # 检查图片是否有效
            if not image or image.isNull():
                print(f"歌曲封面无效: track_id={track_id}")
                return
            
            # 查找对应的图片容器
            artwork_container = self.findChild(QLabel, f"artwork_{track_id}")
            if not artwork_container:
                print(f"找不到图片容器: artwork_{track_id}")
                return
                
            # 缩放图片并设置 - 使用固定大小
            try:
                pixmap = QPixmap.fromImage(image)
                if pixmap.isNull():
                    print(f"创建QPixmap失败: track_id={track_id}")
                    artwork_container.setText("🎵")
                    return
                    
                # 始终缩放为50x50，不受窗口大小影响
                scaled_pixmap = pixmap.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                artwork_container.setPixmap(scaled_pixmap)
                print(f"设置歌曲封面成功: track_id={track_id}")
            except Exception as pixmap_err:
                print(f"处理图片时出错: {str(pixmap_err)}")
                artwork_container.setText("🎵")
                
            # 确保画面尺寸始终保持固定
            artwork_container.setFixedSize(50, 50)
        except Exception as e:
            import traceback
            print(f"处理歌曲封面时出错: {str(e)}")
            print(traceback.format_exc())

    def create_song_list(self):
        """创建歌曲列表，支持自适应布局"""
        # 确保歌曲容器布局存在
        if not hasattr(self, 'songs_layout') or not self.songs_layout:
            return
            
        # 清空布局中的所有项（保留最后的stretch）
        logger.info(f"创建歌曲列表: 共{len(self.visible_songs)}首歌曲")
        while self.songs_layout.count() > 1:
            item = self.songs_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        # 重置图片加载队列
        self.image_queue = []
                
        # 根据搜索文本过滤歌曲列表
        if self.search_text:
            # 如果有搜索条件，筛选匹配的歌曲
            search_text = self.search_text.lower()
            self.visible_songs = []
            
            for song in self.songs:
                track = song.get('track', {})
                if not track:
                    continue
                    
                # 匹配歌曲名、专辑名、艺术家名
                song_name = track.get('name', '').lower()
                album_name = track.get('album', {}).get('name', '').lower()
                
                artists = []
                for artist in track.get('artists', []):
                    artists.append(artist.get('name', '').lower())
                
                # 如果任一字段包含搜索文本，添加到可见列表
                if (search_text in song_name or 
                    search_text in album_name or 
                    any(search_text in artist for artist in artists)):
                    self.visible_songs.append(song)
        else:
            # 如果没有搜索条件，所有歌曲可见
            self.visible_songs = self.songs
            
        # 根据排序设置排序歌曲
        sorted_songs = self.sort_tracks_by_key(self.visible_songs, self.sort_key, self.sort_reverse)
            
        # 更新歌曲计数
        self.update_song_count()
            
        # 添加歌曲行
        for i, song in enumerate(sorted_songs):
            # 创建歌曲行
            row = self.create_song_row(i, song)
            if row:
                self.songs_layout.insertWidget(i, row)
                
                # 应用当前的自适应缩放设置
                if self.width_factor != 1.0:
                    # 获取行中的标题和专辑容器，调整其宽度
                    for j in range(row.layout().count()):
                        item = row.layout().itemAt(j)
                        if item and item.widget():
                            widget = item.widget()
                            
                            # 根据位置判断是图片容器、标题容器还是专辑容器
                            if j == 2 and widget.objectName().startswith("artwork_"):  # 图片容器
                                # 确保保持固定大小
                                widget.setFixedSize(50, 50)
                            elif j == 3:  # 标题容器
                                title_width = int(0.4 * self.width_factor * self.width())
                                widget.setMinimumWidth(title_width)
                            elif j == 4:  # 专辑容器
                                album_width = int(0.3 * self.width_factor * self.width())
                                widget.setMinimumWidth(album_width)
                
                # 控制选择框的可见性
                checkbox_container = row.findChild(QWidget, f"checkbox_container_{i}")
                if checkbox_container:
                    checkbox_container.setVisible(self.export_mode)
        
        # 加载完成后，强制刷新UI以确保正确显示
        QTimer.singleShot(50, self.update_song_item_widths)
        
        # 停止加载指示器
        if hasattr(self, 'loading_indicator') and self.loading_indicator:
            self.loading_indicator.stop()
            if hasattr(self, 'loading_container') and self.loading_container:
                self.loading_container.hide()
        
        # 确保定义_bottom_indicators_cleaned属性
        if not hasattr(self, '_bottom_indicators_cleaned'):
            self._bottom_indicators_cleaned = False
        
        # 清理底部加载指示器并设置标志
        if self._cleanup_bottom_loading_indicators():
            logger.debug("歌曲列表创建完成：底部加载指示器已清理")
            self._bottom_indicators_cleaned = True
        
        # 标记没有剩余歌曲要加载
        if not self.remaining_tracks:
            logger.debug("没有剩余歌曲需要加载")
            self._bottom_indicators_cleaned = True

    def _cleanup_bottom_loading_indicators(self):
        """清理底部加载指示器"""
        # 查找底部加载指示器
        songs_container = self.findChild(QWidget, "songs_container")
        if not songs_container or not songs_container.layout():
            logger.debug("未找到歌曲容器，无法清理底部加载指示器")
            return False
            
        cleaned = False
        # 收集需要删除的widget，避免在迭代时修改布局
        widgets_to_remove = []
        
        for i in range(songs_container.layout().count()):
            item = songs_container.layout().itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if widget.objectName() == "loading_song_list_widget" or widget.objectName() == "bottom_loading_indicator":
                    logger.debug(f"找到底部加载指示器: {widget.objectName()}")
                    # 停止加载动画
                    for child in widget.findChildren(LoadingIndicator):
                        if child:
                            child.stop()
                    # 隐藏部件
                    widget.hide()
                    # 添加到待删除列表
                    widgets_to_remove.append(widget)
                    cleaned = True
        
        # 从布局中移除收集到的widget
        for widget in widgets_to_remove:
            songs_container.layout().removeWidget(widget)
            widget.deleteLater()
            
        if cleaned:
            logger.debug("底部加载指示器清理完成")
            
        return cleaned

    def load_songs(self, force_refresh=False):
        """加载歌曲列表
        :param force_refresh: 是否强制刷新（忽略缓存）
        """
        # 避免重复加载
        if self.is_loading:
            logger.info(f"歌曲正在加载中，忽略重复的加载请求: {self.playlist_id}")
            return
        
        # 设置加载状态
        self.is_loading = True
        self.loaded = False
        
        if force_refresh:
            # 强制刷新时显示特定提示
            self.status_label.setText(self.get_text('playlist.refreshing', "正在刷新歌曲..."))
            logger.info(f"强制刷新播放列表: {self.playlist_id} - {self.playlist_name}")
        else:
            self.status_label.setText(self.get_text('playlist.loading', "加载中..."))
            logger.info(f"开始加载播放列表: {self.playlist_id} - {self.playlist_name}")
        
        # 显示加载指示器并隐藏歌曲列表
        if hasattr(self, 'songs_layout'):
            # 清空现有歌曲列表
            while self.songs_layout.count() > 0:
                item = self.songs_layout.takeAt(0)
                if item and item.widget():
                    item.widget().deleteLater()
                    
            # 添加加载中提示
            loading_widget = QWidget()
            loading_layout = QVBoxLayout(loading_widget)
            
            # 创建加载指示器
            loading_indicator = LoadingIndicator(self)
            loading_indicator.setFixedSize(48, 48)
            loading_layout.addWidget(loading_indicator, 0, Qt.AlignCenter)
            
            # 创建加载文本
            loading_text = QLabel(
                self.get_text('playlist.refreshing_songs', "刷新歌曲中...") if force_refresh 
                else self.get_text('playlist.loading_songs', "加载歌曲中...")
            )
            loading_text.setStyleSheet("color: white; font-size: 16px; margin-top: 10px;")
            loading_text.setAlignment(Qt.AlignCenter)
            loading_layout.addWidget(loading_text, 0, Qt.AlignCenter)
            
            # 开始动画
            loading_indicator.start()
            
            # 添加到歌曲布局
            self.songs_layout.addWidget(loading_widget, 0, Qt.AlignCenter)
                
        # 清空现有数据
        self.songs = []
        self.visible_songs = []
        
        # 创建加载线程
        self.threads = []
        loader = SongLoader(self.sp, self.playlist_id, self.cache_manager, force_refresh)
        loader.songs_loaded.connect(self.load_songs_completed)
        loader.load_error.connect(self.on_load_error)
        
        # 添加线程并启动
        self.threads.append(loader)
        loader.start()

    def on_load_error(self, error_message):
        """歌曲加载错误回调
        :param error_message: 错误信息
        """
        self.is_loading = False
                
        # 显示错误信息
        self.status_label.setText(self.get_text('playlist.load_songs_failed', "加载歌曲失败"))
        
        logger.error(f"加载歌曲失败: {error_message}")
        
        # 显示错误消息框
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(self.get_text('common.error', '错误'))
        msg_box.setText(self.get_text('playlist.load_songs_failed', '加载歌曲失败') + f": {error_message}")
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #1E1E1E;
            }
            QMessageBox QLabel {
                color: #FFFFFF;
                font-size: 14px;
                padding: 10px;
                min-width: 300px;
            }
            QPushButton {
                background-color: #333;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 5px 15px;
                font-size: 13px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #404040;
            }
        """)
        msg_box.exec_()

    def load_songs_completed(self, tracks, from_cache):
        """歌曲加载完成回调"""
        self.is_loading = False
        self.loaded = True
        
        # 存储歌曲数据
        self.songs = tracks
        
        # 记录加载完成
        logger.info(f"歌曲加载完成: 共{len(tracks)}首歌曲, 数据来源: {'缓存' if from_cache else 'API'}")
        
        # 初始化底部加载指示器清理标志
        if not hasattr(self, '_bottom_indicators_cleaned'):
            self._bottom_indicators_cleaned = False
        
        # 创建歌曲列表
        self.create_song_list()
        
        # 更新加载状态
        self.status_label.setText(self.get_text('playlist.song_count', "{0} 首歌曲").format(len(tracks)))
        
        # 在加载完成后自动应用自适应布局设置
        self.adjust_responsive_ui()
        
        # 确保所有底部加载指示器都被清理
        QTimer.singleShot(100, self._cleanup_bottom_loading_indicators)

    def refresh_songs(self):
        """刷新歌曲列表（强制从API获取最新数据）"""
        # 确认用户操作
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(self.get_text('common.confirm', '确认'))
        msg_box.setText(self.get_text('playlist.confirm_refresh', '确定要刷新歌曲列表吗？这将从Spotify获取最新数据。'))
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)
        
        # 增加对话框的宽度和文本换行
        msg_box.setMinimumWidth(400)
        # 确保文本自动换行并设置足够大的最小高度
        msg_box.setMinimumHeight(150)
        
        # 更全面的样式，确保所有元素都正确显示
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #1E1E1E;
                color: white;
                min-width: 400px;
                min-height: 150px;
            }
            QLabel {
                color: white;
                font-size: 14px;
                padding: 10px;
                background-color: #1E1E1E;
                min-width: 380px;
                max-width: 380px;
                min-height: 60px;
                qproperty-wordWrap: true;
                qproperty-alignment: AlignLeft;
            }
            QPushButton {
                background-color: #333;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 15px;
                font-size: 13px;
                min-width: 80px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #404040;
            }
            QDialog, QWidget {
                background-color: #1E1E1E;
                color: white;
            }
            QDialogButtonBox {
                background-color: #1E1E1E;
                button-layout: 2;
                min-height: 40px;
                margin-top: 10px;
            }
        """)
        
        # 获取按钮并单独设置样式
        yes_button = msg_box.button(QMessageBox.Yes)
        no_button = msg_box.button(QMessageBox.No)
        
        if yes_button:
            yes_button.setStyleSheet("""
                QPushButton {
                    background-color: #1DB954;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 5px 15px;
                    font-size: 13px;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #1ED760;
                }
            """)
            
        if no_button:
            no_button.setStyleSheet("""
                QPushButton {
                    background-color: #333;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 5px 15px;
                    font-size: 13px;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #404040;
                }
            """)
            
        # 获取并调整标签样式，确保文本完全可见
        label = msg_box.findChild(QLabel)
        if label:
            label.setMinimumWidth(380)
            label.setWordWrap(True)
            
        # 调整对话框布局
        layout = msg_box.layout()
        if layout:
            layout.setSpacing(10)
            layout.setContentsMargins(20, 20, 20, 20)
            
        reply = msg_box.exec_()
        
        if reply == QMessageBox.Yes:
            # 强制刷新歌曲列表
            self.load_songs(force_refresh=True)
            
            # 显示刷新中状态
            self.status_label.setText(self.get_text('playlist.refreshing', "刷新中..."))
            
            # 更新歌曲计数
            QTimer.singleShot(1000, self.update_song_count)

    def _get_best_playlist_image(self, playlist):
        """获取最佳播放列表封面图片
        :param playlist: 播放列表数据
        :return: 最佳封面图片URL
        """
        if not playlist or not playlist.get('images'):
            return None
            
        # 优先使用第一张图片（通常是最大的封面）
        return playlist['images'][0]['url'] 

    def load_playlist_image(self):
        """加载播放列表封面图片"""
        if not self.playlist_image_url:
            # 没有封面图片，设置默认样式
            self.playlist_image.setText(self.get_text('playlist.no_image', "无封面"))
            self.playlist_image.setStyleSheet("""
                background-color: #333;
                color: white;
                font-size: 14px;
                border-radius: 4px;
                text-align: center;
            """)
            return
            
        # 首先尝试从缓存加载
        cached_image = self.cache_manager.get_cached_image(self.playlist_image_url, 'playlist')
        if cached_image:
            # 如果有缓存，直接设置
            pixmap = QPixmap.fromImage(cached_image)
            scaled_pixmap = pixmap.scaled(192, 192, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.playlist_image.setPixmap(scaled_pixmap)
        else:
            # 否则异步加载
            self.playlist_image.setText("")
            self.threads = getattr(self, 'threads', [])
            loader = ImageLoader(self.playlist_image_url, 'playlist_cover', self.cache_manager)
            loader.image_loaded.connect(self.on_playlist_image_loaded)
            self.threads.append(loader)
            loader.start()
            
    def on_playlist_image_loaded(self, image_id, image):
        """播放列表封面图片加载完成回调
        :param image_id: 图片标识符
        :param image: 加载的图片
        """
        if image_id != 'playlist_cover' or not hasattr(self, 'playlist_image'):
            return
            
        # 确保图片有效
        if image.isNull():
            self.playlist_image.setText(self.get_text('playlist.load_failed', "加载失败"))
            self.playlist_image.setStyleSheet("""
                background-color: #333;
                color: white;
                font-size: 14px;
                border-radius: 4px;
                text-align: center;
            """)
        else:
            # 缓存图片
            self.cache_manager.cache_image(self.playlist_image_url, image, 'playlist')
            
            # 缩放图片并设置
            scaled_image = image.scaled(192, 192, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.playlist_image.setPixmap(QPixmap.fromImage(scaled_image))
            
        # 停止加载动画
        if hasattr(self, 'playlist_image_loading'):
            self.playlist_image_loading.stop()
            self.playlist_image_loading.hide() 

    def update_ui(self):
        """更新UI状态"""
        # 更新歌曲计数
        self.update_song_count()
        
        # 检查是否需要加载更多歌曲
        self.check_for_load_more()
        
        # 延迟加载可见区域内的图片
        self.lazy_load_visible_images() 

    def on_scroll_end(self):
        """滚动结束时触发的方法"""
        # 记录当前滚动位置
        self.scroll_position = self.scroll_area.verticalScrollBar().value()
        
        # 延迟加载可见区域内的图片
        self.lazy_load_visible_images()
        
        # 检查是否需要加载更多歌曲
        self.check_for_load_more()

    def on_search_changed(self, text):
        """处理搜索框文本变化
        :param text: 搜索文本
        """
        self.search_text = text.strip().lower()
        if not self.search_text and hasattr(self, 'in_search_mode') and self.in_search_mode:
            # 如果文本清空且正处于搜索状态，退出搜索状态
            self.in_search_mode = False
            self.visible_songs = self.songs
            self.create_song_list()
            # 更新状态标签，显示已退出搜索
            self.status_label.setText(self.language_manager.get_text(
                'playlist.song_count', 
                "{0} 首歌曲"
            ).format(len(self.songs)))
        else:
            # 执行过滤
            self.filter_songs()
    
    def filter_songs(self):
        """根据搜索文本过滤歌曲"""
        if not self.search_text:
            # 如果没有搜索文本，显示所有歌曲
            self.visible_songs = self.songs
            if hasattr(self, 'in_search_mode'):
                self.in_search_mode = False
        else:
            # 标记为搜索模式
            self.in_search_mode = True
            
            # 根据搜索文本过滤，仅匹配歌曲名称
            self.visible_songs = []
            for song in self.songs:
                track = song.get('track', {})
                if not track:
                    continue
                
                # 获取歌曲名称
                track_name = track.get('name', '').lower()
                
                # 如果搜索文本出现在歌曲名中，保留该歌曲
                if self.search_text in track_name:
                    self.visible_songs.append(song)
            
            # 更新状态标签，显示搜索结果数量
            self.status_label.setText(
                self.language_manager.get_text(
                    'playlist.search_results', 
                    "显示 {0}/{1} 首歌曲"
                ).format(len(self.visible_songs), len(self.songs))
            )
            
        # 重新创建歌曲列表
        self.create_song_list()

    def get_text(self, key, default_text):
        """安全获取文本翻译
        :param key: 翻译键
        :param default_text: 默认文本
        :return: 翻译文本
        """
        if not hasattr(self, 'language_manager') or self.language_manager is None:
            return default_text
            
        if not hasattr(self.language_manager, 'get_text'):
            return default_text
            
        try:
            text = self.language_manager.get_text(key, default_text)
            if isinstance(text, str):
                return text
            return default_text
        except:
            return default_text

    def show_sort_menu(self):
        """显示排序菜单"""
        # 创建菜单
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #282828;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 5px;
            }
            QMenu::item {
                color: #b3b3b3;
                padding: 5px 30px 5px 20px;
                border-radius: 2px;
            }
            QMenu::item:selected {
                background-color: #333;
                color: white;
            }
            QMenu::separator {
                height: 1px;
                background: #333;
                margin: 5px 0px;
            }
        """)
        
        # 添加排序选项
        sort_options = {
            'order': self.get_text('playlist.sort_order', '原始顺序'),
            'name': self.get_text('playlist.sort_name', '歌曲名'),
            'artist': self.get_text('playlist.sort_artist', '艺术家'),
            'album': self.get_text('playlist.sort_album', '专辑'),
            'duration': self.get_text('playlist.sort_duration', '时长'),
            'added_at': self.get_text('playlist.sort_added', '添加时间')
        }
        
        # 获取当前排序方式
        current_sort = self.sort_key
        
        # 添加排序选项到菜单
        for key, text in sort_options.items():
            action = QAction(text, self)
            action.setCheckable(True)
            action.setChecked(key == current_sort)
            action.triggered.connect(lambda checked, k=key: self.change_sort_key(k))
            menu.addAction(action)
        
        # 添加分隔线
        menu.addSeparator()
        
        # 添加排序顺序选项
        ascending_action = QAction(self.get_text('playlist.sort_ascending', '升序'), self)
        ascending_action.setCheckable(True)
        ascending_action.setChecked(not self.sort_reverse)
        ascending_action.triggered.connect(lambda: self.change_sort_order(False))
        menu.addAction(ascending_action)
        
        descending_action = QAction(self.get_text('playlist.sort_descending', '降序'), self)
        descending_action.setCheckable(True)
        descending_action.setChecked(self.sort_reverse)
        descending_action.triggered.connect(lambda: self.change_sort_order(True))
        menu.addAction(descending_action)
        
        # 显示菜单
        menu.exec_(self.sort_button.mapToGlobal(self.sort_button.rect().bottomLeft()))
    
    def change_sort_key(self, key):
        """改变排序方式
        :param key: 排序键
        """
        if key != self.sort_key:
            self.sort_key = key
            self.settings.setValue("playlist_sort_key", key)
            self.reload_songs()
    
    def change_sort_order(self, reverse):
        """改变排序顺序
        :param reverse: 是否降序
        """
        if reverse != self.sort_reverse:
            self.sort_reverse = reverse
            self.settings.setValue("playlist_sort_reverse", "true" if reverse else "false")
            self.reload_songs()

    def on_scroll(self, value):
        """滚动事件处理
        :param value: 滚动条位置
        """
        # 记录当前滚动位置
        self.scroll_position = value
        
        # 重置滚动计时器
        self.scroll_timer.stop()
        self.scroll_timer.start()
        
        # 检查是否需要加载更多歌曲
        self.check_for_load_more()
        
        # 延迟加载可见区域内的图片
        self.lazy_load_visible_images()
        
    def select_all_songs(self):
        """选择所有歌曲"""
        if hasattr(self, 'select_all_checkbox'):
            self.select_all_checkbox.setChecked(True)
    
    def clear_song_selection(self):
        """清除所有歌曲选择"""
        if hasattr(self, 'select_all_checkbox'):
            self.select_all_checkbox.setChecked(False)
            for checkbox in self.song_checkboxes:
                if checkbox and checkbox.parent() is not None:
                    checkbox.setChecked(False)
    
    def create_header_labels(self):
        """创建表头标签"""
        # 复选框列（导出模式下显示但不再放在标题栏）
        checkbox_header = QLabel()
        checkbox_header.setFixedWidth(40)
        checkbox_header.setAlignment(Qt.AlignCenter)
        self.header_layout.addWidget(checkbox_header)
        
        # 序号列
        number_header = QLabel("#")
        number_header.setFixedWidth(30)
        number_header.setStyleSheet("color: #b3b3b3; font-size: 14px;")
        number_header.setAlignment(Qt.AlignCenter)
        self.header_layout.addWidget(number_header)
        
        # 如果设置显示专辑封面，添加封面列
        if self.settings.value("playlist_show_artwork", True, type=bool):
            artwork_header = QLabel()
            # 固定宽度，与歌曲行中的封面图片宽度一致
            artwork_header.setFixedWidth(50)
            self.header_layout.addWidget(artwork_header)
        
        # 标题列
        title_header = QLabel(self.get_text("playlist.title", "标题"))
        title_header.setStyleSheet("color: #b3b3b3; font-size: 14px;")
        self.header_layout.addWidget(title_header, 1)  # 1表示伸展因子
        
        # 时长列
        duration_header = QLabel(self.get_text("playlist.duration_field", "时长"))
        duration_header.setFixedWidth(80)
        duration_header.setStyleSheet("color: #b3b3b3; font-size: 14px;")
        duration_header.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.header_layout.addWidget(duration_header)