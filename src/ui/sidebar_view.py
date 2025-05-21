"""
侧边栏视图
"""
import os
from threading import Thread
import sys

from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, 
    QHBoxLayout, QFrame, QScrollArea, QSizePolicy, 
    QStackedWidget, QProgressBar
)
from PyQt5.QtGui import QPixmap, QImage, QIcon
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QSize, QPropertyAnimation, QEasingCurve

from src.utils.language_manager import LanguageManager
from src.utils.logger import logger

class ImageLoader(QThread):
    """图片加载线程"""
    image_loaded = pyqtSignal(QImage, str)
    
    def __init__(self, url, cache_manager):
        super().__init__()
        self.url = url
        self.cache_manager = cache_manager
    
    def run(self):
        try:
            # 尝试从缓存加载
            image = self.cache_manager.get_cached_image(self.url)
            
            if not image:
                # 从网络加载
                import requests
                from io import BytesIO
                from requests.adapters import HTTPAdapter
                from urllib3.util.retry import Retry
                
                session = requests.Session()
                retries = Retry(total=3, backoff_factor=0.5)
                session.mount('https://', HTTPAdapter(max_retries=retries))
                
                response = session.get(self.url, timeout=10)
                response.raise_for_status()
                
                image_data = BytesIO(response.content)
                
                image = QImage()
                image.loadFromData(image_data.getvalue())
                
                # 缓存图片
                if not image.isNull():
                    self.cache_manager.cache_image(self.url, image)
            
            if image and not image.isNull():
                self.image_loaded.emit(image, self.url)
        
        except Exception as e:
            logger.error(f"加载图片失败: {str(e)}")

class PlaylistItem(QWidget):
    """播放列表项组件"""
    clicked = pyqtSignal(object)  # 发送点击信号和播放列表数据
    
    def __init__(self, playlist_data, parent=None):
        super().__init__(parent)
        self.playlist_data = playlist_data
        self.is_selected = False
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # 播放列表图标（默认图标）
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(QSize(40, 40))
        
        # 使用父级的get_resource_path方法获取图标路径
        parent_view = self.parent()
        while parent_view and not hasattr(parent_view, 'get_resource_path'):
            parent_view = parent_view.parent()
            
        if parent_view and hasattr(parent_view, 'get_resource_path'):
            icon_path = parent_view.get_resource_path("app_icon.png")
        else:
            # 回退方案：直接使用相对路径
            icon_path = os.path.join("src", "assets", "app_icon.png")
            
        default_icon = QPixmap(icon_path)
        
        if not default_icon.isNull():
            self.icon_label.setPixmap(default_icon.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            # 如果图标加载失败，显示文本占位符
            self.icon_label.setText("🎵")
            self.icon_label.setAlignment(Qt.AlignCenter)
            self.icon_label.setStyleSheet("background-color: #282828; border-radius: 4px;")
        layout.addWidget(self.icon_label)
        
        # 播放列表标题
        self.title_label = QLabel(self.playlist_data.get("name", "未知播放列表"))
        self.title_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-weight: 600;
                font-size: 14px;
            }
        """)
        layout.addWidget(self.title_label)
        
        # 固定高度
        self.setFixedHeight(50)
        self.setMouseTracking(True)  # 跟踪鼠标移动
        
        # 设置样式
        self.update_style()
        
        # 尝试加载图像（如果有）
        self._set_playlist_image()
    
    def _set_playlist_image(self):
        """设置播放列表封面图像"""
        images = self.playlist_data.get("images", [])
        if images and len(images) > 0:
            image_url = images[0].get("url", "")
            if image_url:
                try:
                    # 尝试异步加载封面图像
                    from PyQt5.QtCore import QThread, pyqtSignal
                    
                    class SimpleImageLoader(QThread):
                        image_loaded = pyqtSignal(QPixmap)
                        
                        def __init__(self, url):
                            super().__init__()
                            self.url = url
                        
                        def run(self):
                            try:
                                import requests
                                from io import BytesIO
                                from requests.adapters import HTTPAdapter
                                from urllib3.util.retry import Retry
                                
                                session = requests.Session()
                                retries = Retry(total=3, backoff_factor=0.5)
                                session.mount('https://', HTTPAdapter(max_retries=retries))
                                
                                response = session.get(self.url, timeout=10)
                                response.raise_for_status()
                                
                                image_data = BytesIO(response.content)
                                pixmap = QPixmap()
                                pixmap.loadFromData(image_data.getvalue())
                                
                                if not pixmap.isNull():
                                    self.image_loaded.emit(pixmap)
                            except Exception as e:
                                logger.error(f"加载播放列表封面失败: {str(e)}")
                    
                    # 创建并启动加载器
                    self.img_loader = SimpleImageLoader(image_url)
                    self.img_loader.image_loaded.connect(self._on_image_loaded)
                    self.img_loader.start()
                except Exception as e:
                    logger.error(f"初始化图片加载器失败: {str(e)}")
    
    def _on_image_loaded(self, pixmap):
        """图片加载完成回调"""
        if self.icon_label and not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.icon_label.setPixmap(scaled_pixmap)
            
    def set_selected(self, selected):
        """设置是否选中状态"""
        self.is_selected = selected
        self.update_style()
    
    def update_style(self):
        """更新样式"""
        if self.is_selected:
            self.setStyleSheet("""
                QWidget {
                    background-color: #282828;
                    border-radius: 4px;
                }
            """)
        else:
            self.setStyleSheet("")
    
    def enterEvent(self, event):
        """鼠标进入事件"""
        if not self.is_selected:
            self.setStyleSheet("""
                QWidget {
                    background-color: #1A1A1A;
                    border-radius: 4px;
                }
            """)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开事件"""
        if not self.is_selected:
            self.setStyleSheet("")
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        self.clicked.emit(self.playlist_data)
        super().mousePressEvent(event)

class SidebarView(QWidget):
    """侧边栏视图"""
    playlist_selected = pyqtSignal(object)  # 发送选中的播放列表数据
    collapsed_changed = pyqtSignal(bool)    # 侧边栏折叠状态变化信号
    
    # 添加内部信号用于线程通信
    _playlists_loaded = pyqtSignal(list)  # 播放列表加载完成信号
    _loading_error = pyqtSignal()         # 加载错误信号
    
    def __init__(self, spotify_client):
        super().__init__()
        
        # 基础设置
        self.sp = spotify_client
        self.playlists_loaded = False
        self.language_manager = LanguageManager()
        self.is_collapsed = False
        self.playlist_items = []  # 保存所有播放列表项
        self.selected_item = None  # 当前选中的项
        
        # 设置固定宽度
        self.expanded_width = 200  # 减小展开宽度，原为220
        self.collapsed_width = 50  # 折叠宽度 - 与图片宽度相同
        self.setFixedWidth(self.expanded_width)
        
        # 缓存折叠状态下的图标按钮
        self.cached_icon_buttons = []
        
        # 初始化UI
        self.init_ui()
        
        # 连接内部信号
        self._playlists_loaded.connect(self._handle_playlists_loaded)
        self._loading_error.connect(self._show_error_state)
        
        # 监听语言变更
        self.language_manager.language_changed.connect(self.update_ui_texts)
        
        # 更新UI文本
        self.update_ui_texts()
        
    def get_resource_path(self, relative_path):
        """
        获取资源文件的绝对路径，适用于开发环境和打包环境
        
        :param relative_path: 相对路径或文件名
        :return: 资源文件的绝对路径
        """
        try:
            # 如果在打包环境中，基础路径会有所不同
            if getattr(sys, 'frozen', False):
                # 在打包环境中，使用应用程序所在目录
                base_path = os.path.dirname(sys.executable)

                # 然后尝试在assets目录查找
                assets_path = os.path.join(base_path, "assets", relative_path)
                if os.path.exists(assets_path):
                    return assets_path
                    
            else:
                # 在开发环境中，使用项目根目录
                base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                
                # 尝试在src/assets目录查找
                src_assets_path = os.path.join(base_path, "assets", relative_path)
                if os.path.exists(src_assets_path):
                    return src_assets_path
                    
                # 如果找不到，返回默认路径
                return src_assets_path
        except Exception as e:
            logger.error(f"获取资源路径失败: {str(e)}")
            # 如果出错，返回相对路径
            return relative_path
        
    def init_ui(self):
        """初始化UI"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # 设置样式
        self.setStyleSheet("""
            QWidget {
                background-color: #000000;
            }
            QLabel {
                color: #B3B3B3;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #121212;
                width: 8px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #535353;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)
        
        # 移除顶部标题区域
        # 直接添加分隔线作为顶部边界
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #282828;")
        separator.setFixedHeight(1)
        self.main_layout.addWidget(separator)
        
        # 为折叠状态创建一个垂直容器 - 使用QScrollArea支持滚动
        self.collapsed_scroll = QScrollArea()
        self.collapsed_scroll.setWidgetResizable(True)
        self.collapsed_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.collapsed_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        self.collapsed_container = QWidget()
        self.collapsed_layout = QVBoxLayout(self.collapsed_container)
        self.collapsed_layout.setContentsMargins(0, 10, 0, 10)
        self.collapsed_layout.setSpacing(8)
        self.collapsed_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        
        # 为折叠状态创建一个专用的按钮
        self.collapsed_button = QPushButton()
        icon_path = self.get_resource_path("collapse.svg")
        if os.path.exists(icon_path):
            self.collapsed_button.setIcon(QIcon(icon_path))
        else:
            self.collapsed_button.setIcon(QIcon())
            logger.warning(f"警告: 找不到图标文件 {icon_path}")
        self.collapsed_button.setFixedSize(QSize(30, 30))
        self.collapsed_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #FFFFFF;
            }
            QPushButton:hover {
                background-color: #282828;
                border-radius: 15px;
            }
        """)
        self.collapsed_button.clicked.connect(self.toggle_sidebar)
        
        # 将折叠按钮添加到折叠容器
        self.collapsed_layout.addWidget(self.collapsed_button, 0, Qt.AlignHCenter)
        
        # 添加一个小间隔
        spacer = QFrame()
        spacer.setFrameShape(QFrame.HLine)
        spacer.setStyleSheet("background-color: #282828;")
        spacer.setFixedHeight(1)
        spacer.setFixedWidth(30)  # 与按钮宽度接近
        self.collapsed_layout.addWidget(spacer, 0, Qt.AlignHCenter)
        
        # 设置滚动区域的内容
        self.collapsed_scroll.setWidget(self.collapsed_container)
        
        # 将折叠滚动区域添加到主布局，但初始时隐藏
        self.main_layout.addWidget(self.collapsed_scroll)
        self.collapsed_scroll.hide()
        
        # 添加"我的播放列表"标题
        self.playlist_header = QWidget()
        self.playlist_header_layout = QHBoxLayout(self.playlist_header)
        self.playlist_header_layout.setContentsMargins(12, 10, 12, 10)  # 减小左右边距
        
        self.playlist_title = QLabel("我的播放列表")
        self.playlist_title.setStyleSheet("""
            QLabel {
                color: #B3B3B3;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        self.playlist_header_layout.addWidget(self.playlist_title)
        
        # 添加刷新按钮
        self.refresh_button = QPushButton()
        # 如果没有refresh_icon.png，使用文本代替
        self.refresh_button.setText("↻")
        self.refresh_button.setFixedSize(QSize(20, 20))
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #FFFFFF;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #282828;
                border-radius: 10px;
            }
        """)
        self.refresh_button.clicked.connect(self.reload_playlists)
        self.playlist_header_layout.addWidget(self.refresh_button)
        
        # 侧边栏折叠/展开按钮 - 现在放在刷新按钮右边
        self.toggle_button = QPushButton()
        if os.path.exists(icon_path):
            self.toggle_button.setIcon(QIcon(icon_path))
        else:
            # 创建一个空图标而不是使用文本
            self.toggle_button.setIcon(QIcon())
            self.toggle_button.setIconSize(QSize(16, 16))
        self.toggle_button.setFixedSize(QSize(20, 20))
        self.toggle_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #FFFFFF;
            }
            QPushButton:hover {
                background-color: #282828;
                border-radius: 10px;
            }
        """)
        self.toggle_button.clicked.connect(self.toggle_sidebar)
        
        # 将折叠按钮添加到播放列表标题栏
        self.playlist_header_layout.addWidget(self.toggle_button)
        
        self.main_layout.addWidget(self.playlist_header)
        
        # 添加播放列表容器（使用QScrollArea实现滚动）
        self.playlist_container = QScrollArea()
        self.playlist_container.setWidgetResizable(True)
        self.playlist_container.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # 创建内容控件
        self.playlist_content = QWidget()
        self.playlist_content_layout = QVBoxLayout(self.playlist_content)
        self.playlist_content_layout.setContentsMargins(5, 0, 5, 0)
        self.playlist_content_layout.setSpacing(2)
        self.playlist_content_layout.setAlignment(Qt.AlignTop)
        
        # 添加加载指示器容器
        self.loading_widget = QWidget()
        self.loading_layout = QVBoxLayout(self.loading_widget)
        self.loading_layout.setContentsMargins(10, 20, 10, 20)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # 不确定进度
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #535353;
                border-radius: 2px;
                border: none;
            }
            QProgressBar::chunk {
                background-color: #1DB954;
                border-radius: 2px;
            }
        """)
        self.loading_layout.addWidget(self.progress_bar)
        
        # 加载文字
        self.loading_label = QLabel("正在加载播放列表...")
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setStyleSheet("""
            QLabel {
                color: #B3B3B3;
                font-size: 13px;
            }
        """)
        self.loading_layout.addWidget(self.loading_label)
        
        # 创建空提示控件
        self.empty_widget = QWidget()
        self.empty_layout = QVBoxLayout(self.empty_widget)
        self.empty_layout.setContentsMargins(10, 20, 10, 20)
        
        # 空提示图标
        self.empty_icon = QLabel()
        empty_icon_text = "📂"
        self.empty_icon.setText(empty_icon_text)
        self.empty_icon.setStyleSheet("font-size: 32px; color: #B3B3B3;")
        self.empty_icon.setAlignment(Qt.AlignCenter)
        self.empty_layout.addWidget(self.empty_icon)
        
        # 空提示文字
        self.empty_label = QLabel("没有找到播放列表")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet("""
            QLabel {
                color: #B3B3B3;
                font-size: 13px;
                margin-top: 10px;
            }
        """)
        self.empty_layout.addWidget(self.empty_label)
        
        # 播放列表容器的堆栈控件
        self.playlist_stack = QStackedWidget()
        self.playlist_stack.addWidget(self.loading_widget)  # 0: 加载中
        self.playlist_stack.addWidget(self.playlist_content)  # 1: 播放列表内容
        self.playlist_stack.addWidget(self.empty_widget)  # 2: 空提示
        
        # 默认显示加载中状态
        self.playlist_stack.setCurrentIndex(0)
        
        # 将堆栈控件设置为ScrollArea的内容
        self.playlist_container.setWidget(self.playlist_stack)
        self.main_layout.addWidget(self.playlist_container)
    
    def update_ui_texts(self):
        """更新UI文本"""
        # 更新播放列表标题
        self.playlist_title.setText(self.language_manager.get_text('sidebar.your_playlists', '我的播放列表'))
        
        # 更新加载文字
        self.loading_label.setText(self.language_manager.get_text('sidebar.loading', '正在加载播放列表...'))
        
        # 更新空提示
        self.empty_label.setText(self.language_manager.get_text('sidebar.no_playlists', '没有找到播放列表'))
    
    def load_playlists(self):
        """加载用户播放列表"""
        # 如果已经加载过，直接返回
        if self.playlists_loaded:
            return
        
        # 显示加载状态
        self.playlist_stack.setCurrentIndex(0)
        
        # 创建异步线程加载
        thread = Thread(target=self._load_playlists_thread)
        thread.daemon = True
        thread.start()
    
    def _load_playlists_thread(self):
        """异步线程加载播放列表"""
        try:
            # 获取所有用户播放列表
            logger.info("开始加载用户播放列表")
            results = self.sp.current_user_playlists()
            playlists = results['items']
            
            while results['next']:
                results = self.sp.next(results)
                playlists.extend(results['items'])
            
            # 发送信号更新UI
            self._playlists_loaded.emit(playlists)
            logger.info(f"成功加载{len(playlists)}个播放列表")
        except Exception as e:
            logger.error(f"加载播放列表失败: {str(e)}")
            # 发送错误信号
            self._loading_error.emit()
    
    def _show_error_state(self):
        """显示错误状态"""
        self.empty_label.setText(self.language_manager.get_text('sidebar.loading_failed', '加载播放列表失败'))
        self.playlist_stack.setCurrentIndex(2)
    
    def _handle_playlists_loaded(self, playlists):
        """处理播放列表加载完成
        :param playlists: 播放列表数据列表
        """
        # 清空现有内容
        self._clear_playlists()
        
        # 添加播放列表
        if playlists and len(playlists) > 0:
            for playlist in playlists:
                self._add_playlist_item(playlist)
            
            # 显示播放列表内容
            self.playlist_stack.setCurrentIndex(1)
            
            # 如果是折叠状态，调整播放列表项显示
            if self.is_collapsed:
                self._update_playlist_items_collapsed(True)
        else:
            # 显示空状态
            self.playlist_stack.setCurrentIndex(2)
        
        # 标记为已加载
        self.playlists_loaded = True
    
    def _clear_playlists(self):
        """清空播放列表"""
        # 清除内容布局中的所有控件
        while self.playlist_content_layout.count():
            item = self.playlist_content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 清空播放列表项列表
        self.playlist_items = []
        self.selected_item = None
    
    def _add_playlist_item(self, playlist_data):
        """添加播放列表项"""
        item = PlaylistItem(playlist_data)
        item.clicked.connect(self._on_playlist_item_clicked)
        self.playlist_content_layout.addWidget(item)
        self.playlist_items.append(item)
    
    def _on_playlist_item_clicked(self, playlist_data):
        """处理播放列表项点击事件"""
        # 检查是否点击了已选中的项
        is_same_item = False
        if self.selected_item and self.selected_item.playlist_data["id"] == playlist_data["id"]:
            is_same_item = True
            logger.info(f"重复点击同一个播放列表项: {playlist_data['name']}")
        
        # 清除上一个选中项
        if self.selected_item:
            self.selected_item.set_selected(False)
        
        # 找到当前点击的项
        for item in self.playlist_items:
            if item.playlist_data == playlist_data:
                self.selected_item = item
                item.set_selected(True)
                break
        
        # 发出播放列表选中信号（标记是否是同一个播放列表的重复点击）
        self.playlist_selected.emit(playlist_data)
    
    def reload_playlists(self):
        """重新加载播放列表"""
        # 显示加载状态
        self.playlist_stack.setCurrentIndex(0)
        
        # 重置加载状态，以便重新加载
        self.playlists_loaded = False
        
        # 创建异步线程加载
        thread = Thread(target=self._load_playlists_thread)
        thread.daemon = True
        thread.start()
    
    def toggle_sidebar(self):
        """切换侧边栏折叠/展开状态"""
        # 如果动画正在进行，停止它
        if hasattr(self, 'animation') and self.animation.state() == QPropertyAnimation.Running:
            self.animation.stop()
            self.animation.finished.disconnect()  # 断开之前的连接，避免多次触发
        
        # 阻止UI更新，减少闪烁
        self.setUpdatesEnabled(False)
            
        # 切换状态
        self.is_collapsed = not self.is_collapsed
        
        # 立即调整宽度，减少动画过程中的布局计算
        target_width = self.collapsed_width if self.is_collapsed else self.expanded_width
        
        # 预准备UI状态，但不立即显示/隐藏控件
        if self.is_collapsed:
            # 折叠状态 - 准备UI
            # 使用展开图标
            icon_path = self.get_resource_path("expand.svg")
            if os.path.exists(icon_path):
                self.collapsed_button.setIcon(QIcon(icon_path))
            else:
                logger.warning(f"警告: 找不到图标文件 {icon_path}")
                
            # 创建并准备折叠状态下的图标按钮（如果尚未创建）
            if not self.cached_icon_buttons:
                self._prepare_collapsed_icons()
                
            # 暂时不显示折叠容器，等动画开始后再显示
        else:
            # 展开状态
            # 使用折叠图标
            icon_path = self.get_resource_path("collapse.svg")
            if os.path.exists(icon_path):
                self.toggle_button.setIcon(QIcon(icon_path))
        
        # 仅创建一次动画，使用简单属性动画
        self.animation = QPropertyAnimation(self, b"minimumWidth")
        self.animation.setDuration(150)  # 增加时间略微提高平滑度
        self.animation.setEasingCurve(QEasingCurve.OutCubic)  # 更平滑的曲线
        self.animation.setStartValue(self.width())
        self.animation.setEndValue(target_width)
        
        # 监听动画的valueChanged信号，在动画进行一半时切换界面
        self.animation.valueChanged.connect(self._on_animation_value_changed)
        
        # 动画完成后进行最终清理
        self.animation.finished.connect(self._finish_toggle_sidebar)
        
        # 发送折叠状态变化信号
        self.collapsed_changed.emit(self.is_collapsed)
        
        # 允许UI更新并开始动画
        self.setUpdatesEnabled(True)
        self.animation.start()
        
    def _on_animation_value_changed(self, value):
        """动画进行中的回调，用于在合适的时机切换界面，减少闪烁"""
        # 计算当前动画进度
        target_width = self.collapsed_width if self.is_collapsed else self.expanded_width
        start_width = self.expanded_width if self.is_collapsed else self.collapsed_width
        progress = abs(value - start_width) / abs(target_width - start_width)
        
        # 在动画进行到30%时切换界面元素，这样用户看到的是平滑过渡
        if progress > 0.3 and not hasattr(self, '_ui_switched'):
            self._ui_switched = True
            
            # 暂停UI更新
            self.setUpdatesEnabled(False)
            
            if self.is_collapsed:
                # 隐藏常规控件，显示折叠控件
                self.playlist_header.hide()
                self.playlist_container.hide()
                
                # 显示折叠容器
                self.collapsed_scroll.show()
            else:
                # 隐藏折叠控件
                self.collapsed_scroll.hide()
                
                # 准备但暂不显示常规控件，等动画快结束时再显示
                if progress > 0.7:
                    self.playlist_header.show()
                    self.playlist_container.show()
            
            # 恢复UI更新
            self.setUpdatesEnabled(True)
        
        # 在动画接近结束时确保正确显示控件
        if progress > 0.7 and not hasattr(self, '_ui_finalized'):
            self._ui_finalized = True
            
            if not self.is_collapsed:
                # 确保展开状态下的控件可见
                self.playlist_header.show()
                self.playlist_container.show()
        
    def _finish_toggle_sidebar(self):
        """完成侧边栏折叠/展开的后续操作"""
        # 清除状态标记
        if hasattr(self, '_ui_switched'):
            delattr(self, '_ui_switched')
        if hasattr(self, '_ui_finalized'):
            delattr(self, '_ui_finalized')
            
        # 断开动画信号连接
        if hasattr(self, 'animation'):
            self.animation.valueChanged.disconnect()
        
        # 阻止UI更新以减少闪烁
        self.setUpdatesEnabled(False)
        
        try:
            if self.is_collapsed:
                # 折叠状态 - 确保正常显示控件隐藏，折叠控件显示
                self.playlist_header.hide()
                self.playlist_container.hide()
                
                self.collapsed_scroll.show()
                self.collapsed_container.show()
                
                # 应用折叠状态样式
                self._update_playlist_items_collapsed(True)
            else:
                # 展开状态 - 确保折叠控件隐藏，正常控件显示
                self.collapsed_scroll.hide()
                
                self.playlist_header.show()
                self.playlist_container.show()
                
                # 显示常规控件
                self._show_expanded_controls()
                
                # 应用展开状态样式
                self._update_playlist_items_collapsed(False)
        finally:
            # 恢复UI更新
            self.setUpdatesEnabled(True)
            
            # 强制刷新
            self.update()
        
    def _show_expanded_controls(self):
        """在展开状态下显示控件"""
        # 确保折叠控件隐藏
        self.collapsed_scroll.hide()
        
        # 确保按钮可见，无需再移动
        self.toggle_button.show()
    
    def _update_playlist_items_collapsed(self, collapsed):
        """更新播放列表项目的显示状态
        :param collapsed: 是否折叠
        """
        # 如果只是更新已有状态，不做任何操作
        if collapsed == self.is_collapsed and (collapsed and self.cached_icon_buttons):
            return
            
        # 暂停UI更新以减少重绘
        if hasattr(self, 'playlist_content'):
            self.playlist_content.setUpdatesEnabled(False)
        if hasattr(self, 'playlist_container'):
            self.playlist_container.setUpdatesEnabled(False)
        
        try:
            if collapsed:
                # 如果没有缓存的图标按钮，则创建
                if not self.cached_icon_buttons:
                    self._prepare_collapsed_icons()
                
                if hasattr(self, 'playlist_content_layout'):
                    # 设置内容区域的对齐方式为居中
                    self.playlist_content_layout.setAlignment(Qt.AlignHCenter)
                
                # 隐藏正常播放列表项
                for item in self.playlist_items:
                    if item:
                        item.hide()
            else:
                if hasattr(self, 'playlist_content_layout'):
                    # 展开状态 - 恢复正常显示，调整内容边距以适应较窄的侧边栏
                    self.playlist_content_layout.setContentsMargins(4, 0, 4, 0)  # 减小边距
                    self.playlist_content_layout.setAlignment(Qt.AlignTop)
                
                # 显示所有播放列表项
                for item in self.playlist_items:
                    if not item:
                        continue
                        
                    item.show()
                    
                    # 确保标题可见
                    if hasattr(item, 'title_label'):
                        item.title_label.show()
                    
                    # 恢复图标大小
                    if hasattr(item, 'icon_label'):
                        item.icon_label.setFixedSize(QSize(40, 40))
                    
                    # 恢复布局设置，减小内容边距
                    if hasattr(item, 'layout'):
                        item.layout().setContentsMargins(8, 5, 8, 5)  # 减小边距
                        item.layout().setAlignment(Qt.AlignLeft)
                    
                    # 恢复大小策略，调整为新的宽度
                    item.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                    item.setMinimumWidth(self.expanded_width - 16)  # 调整为新宽度
        except Exception as e:
            logger.error(f"更新播放列表项目显示状态失败: {str(e)}")
        finally:
            # 恢复UI更新
            if hasattr(self, 'playlist_content'):
                self.playlist_content.setUpdatesEnabled(True)
            if hasattr(self, 'playlist_container'):
                self.playlist_container.setUpdatesEnabled(True)
    
    def _prepare_collapsed_icons(self):
        """提前准备好折叠状态下的图标按钮，避免在切换时创建"""
        # 清空缓存
        self.cached_icon_buttons = []
        
        # 清空折叠容器中除了折叠按钮和分隔线外的所有内容
        while self.collapsed_layout.count() > 2:
            item = self.collapsed_layout.takeAt(2)
            if item.widget():
                item.widget().deleteLater()
        
        # 为每个播放列表创建图标按钮并添加到容器
        for item in self.playlist_items:
            if hasattr(item, 'icon_label'):
                # 获取图标
                icon = None
                if hasattr(item.icon_label, 'pixmap') and item.icon_label.pixmap():
                    icon = item.icon_label.pixmap()
                else:
                    try:
                        app_icon_path = self.get_resource_path(os.path.join("assets", "app_icon.png"))
                        if os.path.exists(app_icon_path):
                            icon = QPixmap(app_icon_path)
                        else:
                            print(f"警告: 找不到应用图标文件 {app_icon_path}")
                    except Exception as e:
                        print(f"加载应用图标失败: {str(e)}")
                        
                if icon and not icon.isNull():
                    # 创建按钮
                    icon_button = QPushButton()
                    icon_button.setIcon(QIcon(icon))
                    icon_button.setIconSize(QSize(36, 36))
                    icon_button.setFixedSize(QSize(40, 40))
                    icon_button.setStyleSheet("""
                        QPushButton {
                            background-color: transparent;
                            border: none;
                        }
                        QPushButton:hover {
                            background-color: #282828;
                            border-radius: 20px;
                        }
                    """)
                    # 存储播放列表数据以便点击时使用
                    icon_button.playlist_data = item.playlist_data
                    icon_button.clicked.connect(lambda checked, data=item.playlist_data: self._on_playlist_item_clicked(data))
                    
                    # 添加到折叠容器
                    self.collapsed_layout.addWidget(icon_button, 0, Qt.AlignHCenter)
                    
                    # 缓存按钮以便后续使用
                    self.cached_icon_buttons.append(icon_button)