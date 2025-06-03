"""
主页面 - 只负责基本布局
"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QStackedWidget)
from PyQt5.QtCore import Qt, QTimer
import os
import sys

# 定义 BASE_DIR
if getattr(sys, 'frozen', False):
    # 如果是打包后的可执行文件
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # 如果是直接运行脚本
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtGui import QIcon, QResizeEvent
import spotipy

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
    
    def __init__(self, access_token):
        try:
            logger.debug("HomePage初始化开始")
            super().__init__()
            
            # 初始化Spotify客户端
            logger.debug("初始化Spotify客户端")
            self.sp = spotipy.Spotify(auth=access_token)
            
            # 初始化语言和缓存管理器
            logger.debug("初始化语言和缓存管理器")
            self.language_manager = LanguageManager()
            self.cache_manager = CacheManager()
            
            # 添加 last_window_width 属性
            self.last_window_width = 0
            
            # 初始化 playlist_view 属性
            self.playlist_view = None
            
            # 初始化HomePage界面
            logger.debug("初始化HomePage界面")
            self.init_ui()
            
            # 尝试加载用户信息和播放列表
            logger.debug("尝试加载用户信息和播放列表")
            self.load_user_data()
            
            # 清理过期缓存
            logger.debug("清理过期缓存")
            if hasattr(self.cache_manager, 'clean_expired_cache'):
                self.cache_manager.clean_expired_cache()
            
            logger.debug("HomePage初始化完成")
        except Exception as e:
            logger.error(f"HomePage初始化失败: {str(e)}")
            import traceback
            traceback.print_exc()
            self.show_loading_error(str(e))
            
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
        """初始化用户界面"""
        try:
            logger.debug("开始初始化HomePage布局")
            
            # 设置窗口标题
            self.setWindowTitle(self.language_manager.get_text("app.title", "Spotify Export Tool"))
            
            # 设置应用图标
            icon_path = os.path.join(BASE_DIR, "assets", "app_icon.png")
            if os.path.exists(icon_path):
                logger.debug(f"设置应用图标: {icon_path}")
                self.setWindowIcon(QIcon(icon_path))
            
            # 创建中央部件
            logger.debug("创建中央部件")
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            # 创建主布局
            main_layout = QVBoxLayout(central_widget)
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.setSpacing(0)
            
            # 创建顶部栏
            logger.debug("创建顶部栏")
            self.topbar = TopbarView(self.sp)
            main_layout.addWidget(self.topbar)
            
            # 创建主内容区域
            logger.debug("创建主内容区域")
            content_layout = QHBoxLayout()
            content_layout.setContentsMargins(0, 0, 0, 0)
            content_layout.setSpacing(0)
            
            # 创建侧边栏
            logger.debug("创建侧边栏")
            self.sidebar = SidebarView(self.sp)
            content_layout.addWidget(self.sidebar)
            
            # 创建主视图区域
            self.stacked_widget = QStackedWidget()
            content_layout.addWidget(self.stacked_widget)
            
            # 添加内容布局到主布局
            main_layout.addLayout(content_layout)
            
            # 创建欢迎页面
            logger.debug("创建欢迎页面")
            self.welcome_view = WelcomeView(self.sp)
            self.stacked_widget.addWidget(self.welcome_view)
            
            # 连接各组件信号
            logger.debug("连接各组件信号")
            self.topbar.home_clicked.connect(self.show_welcome_view)
            self.topbar.settings_clicked.connect(self.show_settings_view)
            self.sidebar.playlist_selected.connect(self.show_playlist_view)
            
            # 显示欢迎页
            logger.debug("显示欢迎页")
            self.stacked_widget.setCurrentWidget(self.welcome_view)
            
            # 自动加载播放列表
            logger.debug("自动加载播放列表")
            self.sidebar.load_playlists()
            
            logger.debug("HomePage布局初始化完成")
        except Exception as e:
            logger.error(f"HomePage布局初始化失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
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
        """安全地登出并返回登录界面"""
        try:
            # 使用上下文管理器确保资源正确释放
            from contextlib import suppress
            
            # 删除token文件，忽略可能的文件不存在错误
            with suppress(FileNotFoundError):
                token_path = os.path.join(self.base_dir, 'data', 'token.json')
                os.remove(token_path)
            
            # 导入登录模块（在需要时导入，避免循环导入）
            from src.ui.login import LoginWindow
            
            # 创建登录窗口并居中
            login_window = LoginWindow()
            self._center_window(login_window)
            
            # 显示登录窗口并关闭主窗口
            login_window.show()
            self.close()
        
        except Exception as e:
            logger.error(f"注销失败: {e}")
            self._show_logout_error(e)
    
    def _center_window(self, window):
        """将窗口居中显示
        :param window: 待居中的窗口
        """
        from PyQt5.QtWidgets import QDesktopWidget
        screen = QDesktopWidget().screenGeometry()
        window_size = window.geometry()
        x = (screen.width() - window_size.width()) // 2
        y = (screen.height() - window_size.height()) // 2
        window.move(x, y)
    
    def _show_logout_error(self, error):
        """显示注销错误
        :param error: 错误对象
        """
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.warning(
            self, 
            self.language_manager.get_text('common.error', '错误'),
            f"{self.language_manager.get_text('logout.failed', '注销失败')}: {str(error)}"
        )
    
    def show_playlist(self, playlist):
        """显示播放列表页面，增加健壮性
        :param playlist: 播放列表数据
        """
        try:
            # 验证输入数据
            if not playlist or not isinstance(playlist, dict):
                logger.warning("无效的播放列表数据")
                return
            
            # 检查是否已经在显示该播放列表
            current_playlist_id = None
            if (hasattr(self, 'playlist_view') and 
                self.playlist_view and 
                hasattr(self.playlist_view, 'playlist_id')):
                current_playlist_id = self.playlist_view.playlist_id
            
            # 如果当前已经显示的播放列表ID与要显示的播放列表ID相同，直接返回
            if current_playlist_id == playlist.get("id"):
                logger.debug(f"已经显示播放列表: {playlist.get('name', '未知')}")
                return
            
            # 清除之前的内容
            self.clear_content()
            
            # 创建播放列表视图
            self.playlist_view = PlaylistView(
                parent=self,
                spotify_client=self.sp, 
                playlist_id=playlist.get("id"),
                playlist_name=playlist.get("name", "未命名播放列表"),
                cache_manager=self.cache_manager,
                locale_manager=self.language_manager
            )
            
            # 添加并显示播放列表视图
            self.stacked_widget.addWidget(self.playlist_view)
            self.stacked_widget.setCurrentWidget(self.playlist_view)
            
            # 强制更新布局
            self.playlist_view.update()
            self.update()
        
        except Exception as e:
            logger.error(f"显示播放列表时发生错误: {e}")
            import traceback
            traceback.print_exc()
            # 可以添加错误处理逻辑，例如显示错误提示
    
    def load_user_data(self):
        """尝试加载用户信息和播放列表"""
        try:
            # 显示加载视图
            loading_view = LoadingView(parent=self.stacked_widget)
            self.stacked_widget.addWidget(loading_view)
            self.stacked_widget.setCurrentWidget(loading_view)
            
            # 尝试获取用户信息
            user_info = self.sp.current_user()
            
            # 缓存用户信息
            self.sp.user_info = user_info
            
            # 尝试加载播放列表
            self.sidebar.load_playlists()
            
            # 显示欢迎页
            self.stacked_widget.removeWidget(loading_view)
            loading_view.deleteLater()
            self.stacked_widget.setCurrentWidget(self.welcome_view)
        
        except Exception as e:
            logger.error(f"加载用户数据失败: {str(e)}")
            self.show_loading_error(str(e))
    
    def show_loading_error(self, error_msg):
        """显示加载错误页面"""
        try:
            # 移除可能存在的加载视图
            for i in range(self.stacked_widget.count()):
                widget = self.stacked_widget.widget(i)
                if isinstance(widget, LoadingView):
                    self.stacked_widget.removeWidget(widget)
                    widget.deleteLater()
            
            # 创建错误视图
            error_view = ErrorView(
                error_type="loading", 
                error_message=error_msg, 
                parent=self.stacked_widget
            )
            
            # 添加并显示错误视图
            self.stacked_widget.addWidget(error_view)
            self.stacked_widget.setCurrentWidget(error_view)
        
        except Exception as e:
            logger.error(f"显示加载错误页面失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def show_settings(self):
        """显示设置页面"""
        self.clear_content()
        
        # 创建加载视图并添加到主内容区域
        loading_view = LoadingView(message_key='common.loading_settings', parent=self.stacked_widget)
        self.stacked_widget.addWidget(loading_view)
        self.stacked_widget.setCurrentWidget(loading_view)
        
        # 刷新UI
        QTimer.singleShot(100, lambda: self._load_settings_content(loading_view))
    
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
            settings_view = SettingsView(self.stacked_widget)
            self.stacked_widget.addWidget(settings_view)
            self.stacked_widget.setCurrentWidget(settings_view)
            
        except Exception as e:
            logger.error(f"显示设置页面失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            # 移除加载视图
            if loading_view:
                self.stacked_widget.removeWidget(loading_view)
                loading_view.deleteLater()
                
            error_view = ErrorView(error_type="loading", parent=self.stacked_widget)
            self.stacked_widget.addWidget(error_view)
            self.stacked_widget.setCurrentWidget(error_view)
    
    def resizeEvent(self, event: QResizeEvent):
        """窗口大小改变事件处理"""
        try:
            # 获取当前窗口宽度
            current_width = self.width()
            
            # 计算宽度变化百分比
            width_change_percent = abs(current_width - self.last_window_width) / self.last_window_width if self.last_window_width > 0 else 0
            
            # 如果宽度变化超过5%，触发响应式布局调整
            if width_change_percent > 0.05:
                self.adjust_responsive_layout()
            
            # 更新最后的窗口宽度
            self.last_window_width = current_width
            
            # 调用父类的 resizeEvent 方法
            super().resizeEvent(event)
        except Exception as e:
            logger.error(f"窗口大小调整事件处理失败: {str(e)}")
            import traceback
            traceback.print_exc()

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

    def show_welcome_view(self):
        """显示欢迎页面，兼容信号连接"""
        self.show_welcome()

    def show_settings_view(self):
        """显示设置页面，兼容信号连接"""
        self.show_settings()

    def show_playlist_view(self, playlist):
        """显示播放列表页面，兼容信号连接
        :param playlist: 播放列表数据
        """
        self.show_playlist(playlist)