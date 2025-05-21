"""
主页面 - 只负责基本布局
"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QStackedWidget)
from PyQt5.QtCore import Qt, QTimer
import os
from PyQt5.QtGui import QIcon, QResizeEvent
import spotipy
import sys

from src.ui.welcome_view import WelcomeView
from src.ui.playlist_view import PlaylistView
from src.ui.sidebar_view import SidebarView
from src.ui.topbar_view import TopbarView
from src.ui.settings_view import SettingsView
from src.ui.error_view import ErrorView
from src.ui.loading_view import LoadingView
from src.utils.language_manager import LanguageManager
from src.utils.cache_manager import CacheManager
from src.utils.logger import logger

class HomePage(QMainWindow):
    """主页"""
    
    def __init__(self, token):
        try:
            logger.info("HomePage初始化开始")
            super().__init__()
            
            # 初始化Spotify客户端
            self.token = token
            logger.info("初始化Spotify客户端")
            self.sp = spotipy.Spotify(auth=token)
            
            # 状态属性
            self.api_connected = True
            self.last_window_width = 0
            self.last_window_height = 0
            
            # 初始化管理器
            logger.info("初始化语言和缓存管理器")
            self.language_manager = LanguageManager()
            self.cache_manager = CacheManager()
            
            # 监听语言变更
            self.language_manager.language_changed.connect(self.update_ui_texts)
            
            # 初始化界面
            logger.info("初始化HomePage界面")
            self.init_ui()
            
            # 清理过期缓存
            logger.info("清理过期缓存")
            self.cache_manager.clear_expired_cache()
            logger.info("HomePage初始化完成")
        except Exception as e:
            logger.error(f"HomePage初始化失败: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    def update_window_title(self):
        """更新窗口标题"""
        self.setWindowTitle("SpotifyExportTool")
    
    def update_ui_texts(self):
        """更新UI文本"""
        self.update_window_title()
        
        # 刷新子控件文本
        if hasattr(self, 'topbar_view'):
            self.topbar_view.update_ui_texts()
            
        if hasattr(self, 'sidebar_view'):
            self.sidebar_view.update_ui_texts()
            
        if hasattr(self, 'welcome_view'):
            self.welcome_view.update_ui_texts()
            
        if hasattr(self, 'playlist_view') and self.playlist_view:
            self.playlist_view.update_ui_texts()
    
    def init_ui(self):
        """初始化界面"""
        try:
            logger.info("开始初始化HomePage布局")
            # 设置窗口属性
            self.setWindowTitle("SpotifyExportTool")
            # 获取正确的图标路径
            icon_path = self.get_resource_path("app_icon.png")
            
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
                logger.info(f"设置应用图标: {icon_path}")
            else:
                logger.warning(f"应用图标不存在: {icon_path}")
                
            self.setMinimumSize(800, 600)  # 设置最小尺寸

            # 创建中央部件
            logger.info("创建中央部件")
            central_widget = QWidget()
            self.setCentralWidget(central_widget)

            # 创建主布局（改为垂直布局）
            main_layout = QVBoxLayout(central_widget)
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.setSpacing(0)

            # 添加顶部栏 - 现在放在最上方，横向占满
            logger.info("创建顶部栏")
            self.topbar_view = TopbarView(self.sp)
            main_layout.addWidget(self.topbar_view)

            # 创建内容区域的布局（水平布局，包含侧边栏和主内容区）
            self.content_container = QWidget()
            self.content_layout = QHBoxLayout(self.content_container)
            self.content_layout.setContentsMargins(0, 0, 0, 0)
            self.content_layout.setSpacing(0)
            
            # 添加侧边栏 - 左侧，竖向占满
            logger.info("创建侧边栏")
            self.sidebar_view = SidebarView(self.sp)
            self.content_layout.addWidget(self.sidebar_view)

            # 添加主内容区域
            logger.info("创建主内容区域")
            main_content = QWidget()
            main_content.setStyleSheet("background-color: #040404;")
            main_content_layout = QVBoxLayout(main_content)
            main_content_layout.setContentsMargins(0, 0, 0, 0)
            main_content_layout.setSpacing(0)

            # 内容主体区域（使用QStackedWidget实现页面切换）
            self.stacked_widget = QStackedWidget()
            self.stacked_widget.setStyleSheet("background-color: #040404;")
            main_content_layout.addWidget(self.stacked_widget)

            # 创建欢迎页面
            logger.info("创建欢迎页面")
            self.welcome_view = WelcomeView(self.sp)
            self.stacked_widget.addWidget(self.welcome_view)

            # 创建播放列表视图页（初始时为空，将在选择歌单时创建）
            self.playlist_view = None

            # 将主内容区添加到水平布局中
            self.content_layout.addWidget(main_content)
            
            # 设置比例（侧边栏宽度固定，主内容区域伸缩）
            self.content_layout.setStretch(0, 0)  # 侧边栏不伸缩
            self.content_layout.setStretch(1, 1)  # 主内容区域伸缩
            
            # 将内容容器添加到主布局
            main_layout.addWidget(self.content_container)
            main_layout.setStretch(1, 1)  # 内容容器可伸缩

            # 连接信号
            logger.info("连接各组件信号")
            self.sidebar_view.playlist_selected.connect(self.show_playlist)
            self.sidebar_view.collapsed_changed.connect(self.adjust_layout)
            self.topbar_view.home_clicked.connect(self.show_home)
            self.topbar_view.settings_clicked.connect(self.show_settings)

            # 显示欢迎页
            logger.info("显示欢迎页")
            self.show_home()

            # 加载用户数据
            QTimer.singleShot(500, self.load_user_data)
            
            # 更新界面文本
            self.update_ui_texts()
            
            # 存储初始窗口大小
            self.last_window_width = self.width()
            self.last_window_height = self.height()
            logger.info("HomePage布局初始化完成")
        except Exception as e:
            logger.error(f"HomePage界面初始化失败: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
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
    
    def show_home(self):
        """显示欢迎页面"""
        # 清除之前的内容
        self.clear_content()
        
        # 显示欢迎页面
        if hasattr(self, 'welcome_view'):
            self.stacked_widget.setCurrentWidget(self.welcome_view)
        else:
            self.welcome_view = WelcomeView(self.sp)
            self.stacked_widget.addWidget(self.welcome_view)
            self.stacked_widget.setCurrentWidget(self.welcome_view)
    
    def show_welcome(self):
        """兼容旧接口的方法"""
        self.show_home()
    
    def logout(self):
        """登出并返回登录界面"""
        try:
            # 删除token文件
            token_path = os.path.join(self.base_dir, 'data', 'token.json')
            if os.path.exists(token_path):
                os.remove(token_path)
            
            # 导入登录模块（在需要时导入，避免循环导入）
            from src.ui.login import LoginWindow
            
            # 创建登录窗口
            self.login_window = LoginWindow()
            
            # 调整登录窗口位置到屏幕中央
            from PyQt5.QtWidgets import QDesktopWidget
            screen = QDesktopWidget().screenGeometry()
            window_size = self.login_window.geometry()
            x = (screen.width() - window_size.width()) // 2
            y = (screen.height() - window_size.height()) // 2
            self.login_window.move(x, y)
            
            # 显示登录窗口
            self.login_window.show()
            
            # 关闭主窗口
            self.close()
            
        except Exception as e:
            logger.error(f"注销失败: {str(e)}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, self.language_manager.get_text('common.error', '错误'),
                               f"{self.language_manager.get_text('logout.failed', '注销失败')}: {str(e)}")
    
    def show_playlist(self, playlist):
        """显示播放列表页面
        :param playlist: 播放列表数据
        """
        # 检查是否已经在显示该播放列表
        if hasattr(self, 'playlist_view') and self.playlist_view and \
           hasattr(self.playlist_view, 'playlist_id') and \
           self.playlist_view.playlist_id == playlist["id"]:
            # 已经在显示该播放列表，触发刷新
            logger.info(f"重新加载当前显示的播放列表: {playlist['name']}")
            self.playlist_view.load_songs(force_refresh=True)
            return
        
        # 清除之前的内容
        self.clear_content()
        
        # 创建播放列表视图，传递语言管理器和缓存管理器
        self.playlist_view = PlaylistView(
            self.sp, 
            playlist,
            parent=self,
            language_manager=self.language_manager,
            cache_manager=self.cache_manager
        )
        self.stacked_widget.addWidget(self.playlist_view)
        self.stacked_widget.setCurrentWidget(self.playlist_view)
    
    def load_user_data(self):
        """加载用户数据"""
        # 加载侧边栏数据
        self.sidebar_view.load_playlists()
    
    def show_settings(self):
        """显示设置页面"""
        self.clear_content()
        
        # 先显示加载页面
        loading_view = LoadingView(message_key='common.loading_settings')
        self.stacked_widget.addWidget(loading_view)
        self.stacked_widget.setCurrentWidget(loading_view)
        
        # 刷新UI
        QTimer.singleShot(10, lambda: self._load_settings_content(loading_view))
    
    def _load_settings_content(self, loading_view=None):
        """
        加载设置页面内容
        :param loading_view: 加载视图，如果不为None则会被移除
        """
        try:
            # 移除加载视图
            if loading_view:
                self.stacked_widget.removeWidget(loading_view)
                loading_view.deleteLater()
                
            # 创建设置页面视图
            settings_view = SettingsView()
            self.stacked_widget.addWidget(settings_view)
            self.stacked_widget.setCurrentWidget(settings_view)
            
        except Exception as e:
            logger.error(f"显示设置页面失败: {str(e)}")
            
            # 移除加载视图
            if loading_view:
                self.stacked_widget.removeWidget(loading_view)
                loading_view.deleteLater()
                
            error_view = ErrorView(error_type="loading")
            self.stacked_widget.addWidget(error_view)
            self.stacked_widget.setCurrentWidget(error_view)
    
    def resizeEvent(self, event: QResizeEvent):
        """窗口大小变化事件"""
        super().resizeEvent(event)
        
        # 检测窗口大小是否有明显变化
        current_width = self.width()
        current_height = self.height()
        
        # 如果窗口宽度变化超过5%，重新调整侧边栏和内容区域的比例
        width_change_percent = abs(current_width - self.last_window_width) / self.last_window_width if self.last_window_width > 0 else 0
        if width_change_percent > 0.05:
            self.adjust_responsive_layout()
            
        # 如果窗口大小变化，强制子控件重新布局
        if abs(current_width - self.last_window_width) > 5 or abs(current_height - self.last_window_height) > 5:
            # 更新当前显示的视图
            current_widget = self.stacked_widget.currentWidget()
            if current_widget:
                current_widget.updateGeometry()
                
        # 更新存储的窗口大小
        self.last_window_width = current_width
        self.last_window_height = current_height

    def adjust_responsive_layout(self):
        """响应窗口大小变化，调整布局"""
        window_width = self.width()
        
        # 根据窗口宽度自动折叠/展开侧边栏
        if hasattr(self.sidebar_view, 'is_collapsed') and hasattr(self.sidebar_view, 'toggle_sidebar'):
            sidebar_collapsed = self.sidebar_view.is_collapsed
            
            if window_width < 900 and not sidebar_collapsed:
                # 折叠侧边栏
                QTimer.singleShot(100, self.sidebar_view.toggle_sidebar)
            elif window_width > 1100 and sidebar_collapsed:
                # 展开侧边栏
                QTimer.singleShot(100, self.sidebar_view.toggle_sidebar)

    def on_sidebar_collapsed(self, collapsed):
        """处理侧边栏折叠状态变化"""
        # 由于不再使用splitter，此方法可以保留但不再需要原来的逻辑
        pass

    def clear_content(self):
        """清空内容区域"""
        # 移除播放列表视图（如果存在）
        if self.playlist_view is not None:
            if self.stacked_widget.indexOf(self.playlist_view) != -1:
                self.stacked_widget.removeWidget(self.playlist_view)
            self.playlist_view.deleteLater()
            self.playlist_view = None
    
    def adjust_layout(self, collapsed):
        """根据侧边栏折叠状态调整布局
        :param collapsed: 侧边栏是否折叠
        """
        # 暂停UI更新以减少重绘次数
        self.setUpdatesEnabled(False)
        
        # 延迟绘制标志，防止过度重绘
        self.is_adjusting_layout = True
        
        # 更新主内容区域的风格表
        if hasattr(self, 'stacked_widget'):
            self.stacked_widget.setStyleSheet("background-color: #040404;")
            
            # 获取当前显示的控件
            current_widget = self.stacked_widget.currentWidget()
            if current_widget:
                # 使用setUpdatesEnabled暂停和恢复更新，比反复应用样式更高效
                current_widget.setUpdatesEnabled(False)
                current_widget.update()
                QTimer.singleShot(50, lambda: current_widget.setUpdatesEnabled(True))
        
        # 选择性处理必要的子控件
        self.process_critical_widgets()
        
        # 延迟恢复UI更新
        QTimer.singleShot(100, self.finish_layout_adjustment)
    
    def process_critical_widgets(self):
        """只处理需要刷新的关键控件"""
        # 查找所有直接子控件中包含背景色的关键控件
        for child in self.findChildren(QWidget, options=Qt.FindDirectChildrenOnly):
            if child.styleSheet() and "background-color" in child.styleSheet():
                # 暂停更新
                child.setUpdatesEnabled(False)
                # 标记为需要更新
                child.setProperty("needs_update", True)
    
    def finish_layout_adjustment(self):
        """完成布局调整后的操作"""
        # 恢复标记的控件更新
        for child in self.findChildren(QWidget):
            if child.property("needs_update"):
                child.setProperty("needs_update", False)
                child.setUpdatesEnabled(True)
                child.update()
        
        # 恢复整体更新
        self.is_adjusting_layout = False
        self.setUpdatesEnabled(True)
        
        # 强制更新当前主内容视图
        if hasattr(self, 'stacked_widget') and self.stacked_widget.currentWidget():
            current_widget = self.stacked_widget.currentWidget()
            if hasattr(current_widget, 'update'):
                current_widget.update()