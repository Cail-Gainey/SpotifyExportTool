"""
顶栏视图
"""
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QLabel, 
                           QFrame, QToolButton, QVBoxLayout,
                           QMenu, QAction, QMessageBox, QDesktopWidget)
from PyQt5.QtGui import QFont, QPixmap, QImage, QIcon, QPainter, QPalette
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QSize, QPoint, QTimer, QEvent
import requests
from io import BytesIO
import os
import sys
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import webbrowser
from src.utils.language_manager import LanguageManager
from src.utils.cache_manager import CacheManager
from src.utils.logger import logger

class ImageLoader(QThread):
    """图像加载线程"""
    image_loaded = pyqtSignal(QImage)
    
    def __init__(self, url):
        super().__init__()
        self.url = url
    
    def run(self):
        try:
            logger.debug(f"开始加载用户头像: {self.url}")
            # 设置重试策略
            session = requests.Session()
            retries = Retry(total=3, backoff_factor=0.5)
            session.mount('https://', HTTPAdapter(max_retries=retries))
            
            response = session.get(self.url, timeout=10)
            response.raise_for_status()
            
            # 加载图片
            img_data = BytesIO(response.content)
            image = QImage()
            image.loadFromData(img_data.getvalue())
            
            # 发送信号，传递图片
            logger.debug("用户头像加载成功，准备显示")
            self.image_loaded.emit(image)
            
        except Exception as e:
            logger.error(f"加载用户头像失败: {str(e)}")
            print(f"加载用户头像失败: {str(e)}")

class TopbarView(QWidget):
    """顶栏视图"""
    home_clicked = pyqtSignal()  # 主页按钮点击信号
    settings_clicked = pyqtSignal()  # 设置按钮点击信号
    
    def __init__(self, sp):
        super().__init__()
        logger.info("初始化TopbarView")
        self.sp = sp
        self.threads = []
        self.login_window = None
        self.is_logging_out = False  # 添加标志防止重复点击
        self.api_connected = True    # 添加API连接状态标志
        
        # 初始化管理器
        self.language_manager = LanguageManager()
        self.cache_manager = CacheManager()
        
        # 监听语言变更
        self.language_manager.language_changed.connect(self.update_ui_texts)
        
        # 设置固定高度
        self.setFixedHeight(64)
        
        # 初始化UI
        self.init_ui()
    
    def update_ui_texts(self):
        """更新UI文本"""
        logger.debug("更新TopbarView UI文本")
        # 更新Spotify标签
        if hasattr(self, 'spotify_label'):
            self.spotify_label.setText(self.language_manager.get_text('topbar.app_name', 'SpotifyExport'))
            
        # 更新主页按钮提示
        if hasattr(self, 'home_btn'):
            self.home_btn.setToolTip(self.language_manager.get_text('topbar.home', '主页'))
        
        # 更新菜单项
        if hasattr(self, 'username_action'):
            if not self.api_connected:
                self.username_action.setText(self.language_manager.get_text('topbar.unknown_user', '未知用户'))
            elif self.username_action.text() == "加载中...":
                self.username_action.setText(self.language_manager.get_text('topbar.loading', '加载中...'))
        
        if hasattr(self, 'account_action'):
            self.account_action.setText(self.language_manager.get_text('topbar.menu.account', '账户'))
        
        if hasattr(self, 'settings_action'):
            self.settings_action.setText(self.language_manager.get_text('topbar.menu.settings', '设置'))
        
        if hasattr(self, 'logout_action'):
            self.logout_action.setText(self.language_manager.get_text('topbar.menu.logout', '退出'))

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
        logger.info("初始化TopbarView UI")
        # 设置背景颜色和底部边框
        self.setStyleSheet("""
            QWidget {
                background-color: #040404;
            }
            QWidget#topbar {
                background-color: #040404;
                border-bottom: 1px solid #282828;
            }
            QLabel {
                background-color: transparent;
                color: white;
            }
            QToolButton {
                background-color: transparent;
                border: none;
                padding: 5px;
                color: #b3b3b3;
            }
            QToolButton:hover {
                color: white;
                background-color: rgba(255, 255, 255, 0.1);
            }
            QMenu {
                background-color: #040404;
                border: none;
                padding: 5px;
                border-radius: 4px;
            }
            QMenu::item {
                background-color: transparent;
                padding: 8px 32px 8px 32px;
                margin: 0px;
                border-radius: 2px;
                color: #b3b3b3;
            }
            QMenu::item:selected {
                background-color: #282828;
                color: white;
            }
        """)
        self.setObjectName("topbar")
        
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建内容容器（确保整个顶栏都有背景色）
        content_container = QWidget()
        content_container.setStyleSheet("background-color: #040404;")
        
        # 创建顶部内容布局
        content_layout = QHBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(15)
        
        # 导航按钮区域
        nav_frame = QWidget()
        nav_frame.setStyleSheet("background-color: #040404;")
        nav_layout = QHBoxLayout(nav_frame)
        nav_layout.setContentsMargins(15, 0, 0, 0)
        nav_layout.setSpacing(10)
        
        # 应用Logo图标
        app_logo = QLabel()
        logo_path = self.get_resource_path('app_icon.png')
        if os.path.exists(logo_path):
            logo_pixmap = QPixmap(logo_path)
            # 将Logo缩放到合适的尺寸
            logo_pixmap = logo_pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            app_logo.setPixmap(logo_pixmap)
            app_logo.setFixedSize(32, 32)
            app_logo.setAlignment(Qt.AlignCenter)
            app_logo.setStyleSheet("background-color: transparent;")
            nav_layout.addWidget(app_logo)
        
        # 首页按钮
        self.home_btn = QToolButton()
        home_icon_path = self.get_resource_path('home.svg')
        if os.path.exists(home_icon_path):
            self.home_btn.setIcon(QIcon(home_icon_path))
        else:
            logger.warning(f"找不到首页图标: {home_icon_path}")
            self.home_btn.setText("🏠")
        self.home_btn.setIconSize(QSize(24, 24))
        self.home_btn.setFixedSize(40, 40)
        self.home_btn.setToolTip(self.language_manager.get_text('topbar.home', '主页'))
        self.home_btn.clicked.connect(self.on_home_clicked)
        nav_layout.addWidget(self.home_btn)
        
        # 添加Spotify标志
        self.spotify_label = QLabel(self.language_manager.get_text('topbar.app_name', 'SpotifyExport'))
        self.spotify_label.setFont(QFont("PingFang SC", 16, QFont.Bold))
        self.spotify_label.setStyleSheet("color: white; background-color: transparent;")
        nav_layout.addWidget(self.spotify_label)
        
        content_layout.addWidget(nav_frame)
        
        # 中间填充区域（使用带背景色的部件替代简单的伸展空间）
        middle_spacer = QWidget()
        middle_spacer.setStyleSheet("background-color: #040404;")
        content_layout.addWidget(middle_spacer, 1)  # 占据所有可用空间
        
        # 用户头像按钮（带下拉菜单）
        self.avatar_btn = QToolButton()
        self.avatar_btn.setFixedSize(32, 32)
        self.avatar_btn.setStyleSheet("""
            QToolButton {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 16px;
                color: white;
            }
            QToolButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
            QToolButton::menu-indicator {
                image: none;
            }
        """)
        self.avatar_btn.setText("")
        
        # 创建下拉菜单
        self.menu = QMenu(self)
        self.menu.setStyleSheet("""
            QMenu {
                background-color: #040404;
                border: none;
                border-radius: 4px;
                padding: 0px;
                margin: 0px;
            }
            QMenu::item {
                background-color: transparent;
                padding: 8px 32px;
                color: #b3b3b3;
                min-width: 150px;
                margin: 0px;
                border: none;
            }
            QMenu::item:selected {
                background-color: #282828;
                color: white;
            }
            QMenu::separator {
                height: 1px;
                background-color: #282828;
                margin: 0px;
                padding: 0px;
            }
            QMenu QWidget {
                background-color: #040404;
                color: #b3b3b3;
            }
            QMenu QWidget::item {
                background-color: transparent;
            }
            QMenu QWidget::item:selected {
                background-color: #282828;
            }
            /* 由于Qt的绘制机制，需要明确设置背景色为完全不透明 */
            QMenu::background {
                background-color: #040404;
            }
            /* 覆盖QMenu内部视图类的样式 */
            QMenu QAbstractItemView {
                background-color: #040404;
                border: none;
                outline: none;
                padding: 0px;
                margin: 0px;
            }
            QMenu QPushButton, QMenu QToolButton {
                background-color: #040404;
                color: #b3b3b3;
            }
        """)
        
        # 添加用户名（作为不可点击的菜单项）
        self.username_action = QAction(self.language_manager.get_text('topbar.loading', '加载中...'), self)
        self.username_action.setEnabled(False)
        self.menu.addAction(self.username_action)
        
        # 添加分隔线
        self.menu.addSeparator()
        
        # 添加账户选项
        self.account_action = QAction(self.language_manager.get_text('topbar.menu.account', '账户'), self)
        self.account_action.triggered.connect(self.open_account_page)
        self.menu.addAction(self.account_action)
        
        # 添加设置选项
        self.settings_action = QAction(self.language_manager.get_text('topbar.menu.settings', '设置'), self)
        self.settings_action.triggered.connect(self.on_settings_clicked)
        self.menu.addAction(self.settings_action)
        
        # 添加分隔线
        self.menu.addSeparator()
        
        # 添加退出选项
        self.logout_action = QAction(self.language_manager.get_text('topbar.menu.logout', '退出'), self)
        self.logout_action.triggered.connect(self.logout)
        self.menu.addAction(self.logout_action)
        
        # 设置下拉菜单，使用自定义的showMenu方法，防止菜单溢出窗口
        self.avatar_btn.clicked.connect(self.showAvatarMenu)
        
        # 添加头像按钮到布局，右侧有15px的边距
        right_container = QWidget()
        right_container.setStyleSheet("background-color: #040404;")
        right_layout = QHBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 15, 0)
        right_layout.addWidget(self.avatar_btn)
        
        content_layout.addWidget(right_container)
        
        # 将内容容器添加到主布局
        main_layout.addWidget(content_container)
        
        # 尝试加载用户信息，但如果失败不会阻止界面显示
        QTimer.singleShot(0, self.load_user_info)
    
    def showAvatarMenu(self):
        """显示头像下拉菜单，确保位置在窗口内"""
        logger.debug("显示用户菜单")
        # 强制设置菜单样式，确保没有白色区域
        self.menu.setWindowFlags(self.menu.windowFlags() | Qt.NoDropShadowWindowHint | Qt.FramelessWindowHint)
        self.menu.setAttribute(Qt.WA_TranslucentBackground, True)
        self.menu.setAutoFillBackground(False)
        
        # 设置自定义样式表以处理圆角问题
        self.menu.setStyleSheet(self.menu.styleSheet() + """
            QMenu {
                background-color: #040404;
                border: none; 
                border-radius: 8px;
                padding: 0px;
                margin: 0px;
            }
            /* 彻底禁用菜单的外部边框 */
            QMenu::frame {
                border: none;
                background-color: #040404;
                padding: 0px;
                margin: 0px;
            }
        """)
        
        # 为菜单设置事件过滤器
        self.menu.installEventFilter(self)
        
        # 获取按钮在屏幕上的位置
        button_pos = self.avatar_btn.mapToGlobal(QPoint(0, 0))
        
        # 获取主窗口位置和大小
        main_window = self.window()
        window_geometry = main_window.geometry()
        
        # 获取菜单尺寸
        menu_width = self.menu.sizeHint().width()
        menu_height = self.menu.sizeHint().height()
        
        # 计算菜单位置 - 默认右对齐
        x_pos = button_pos.x() + self.avatar_btn.width() - menu_width
        
        # 确保不超出窗口右边界
        if x_pos + menu_width > window_geometry.right():
            x_pos = window_geometry.right() - menu_width
            
        # 确保不超出窗口左边界
        if x_pos < window_geometry.left():
            x_pos = window_geometry.left()
        
        # 计算y坐标，默认显示在按钮下方
        y_pos = button_pos.y() + self.avatar_btn.height()
        
        # 如果超出窗口底部，则显示在按钮上方
        if y_pos + menu_height > window_geometry.bottom():
            y_pos = button_pos.y() - menu_height
        
        # 显示菜单
        logger.debug(f"显示菜单，位置: ({x_pos}, {y_pos})")
        self.menu.popup(QPoint(x_pos, y_pos))
    
    def eventFilter(self, obj, event):
        """事件过滤器，处理菜单事件"""
        if obj == self.menu and event.type() == QEvent.Show:
            logger.debug("菜单显示事件触发，应用深色样式")
            # 全面处理菜单及其子控件，消除白色背景
            obj.setAutoFillBackground(False)
            
            # 递归处理所有子控件
            self._apply_dark_style_to_widget(obj)
            
            # 设置整个菜单的外观
            obj.setStyleSheet(obj.styleSheet() + """
                QMenu {
                    background-color: #040404;
                    border: none;
                }
            """)
            
            # 使用定时器延迟处理，确保所有子控件都创建完毕
            QTimer.singleShot(10, lambda: self._apply_dark_style_to_widget(obj))
                
        return False  # 继续处理事件
    
    def _apply_dark_style_to_widget(self, widget):
        """递归应用暗色样式到控件及其子控件"""
        logger.debug(f"为控件应用深色样式: {widget.__class__.__name__}")
        # 对当前控件应用样式
        widget.setAutoFillBackground(False)
        
        # 如果有背景角色，明确设置为黑色
        if hasattr(widget, 'setBackgroundRole'):
            widget.setBackgroundRole(QPalette.Window)
        
        # 如果是菜单，显式处理
        if isinstance(widget, QMenu):
            widget.setStyleSheet("""
                background-color: #040404;
                border: none;
                border-radius: 8px;
            """)
            widget.setAttribute(Qt.WA_TranslucentBackground, True)
        
        # 递归处理所有子控件
        for child in widget.findChildren(QWidget):
            # 禁用自动填充背景
            child.setAutoFillBackground(False)
            
            # 设置透明属性
            child.setAttribute(Qt.WA_TranslucentBackground, True)
            
            # 为所有子控件设置背景色
            child.setStyleSheet("background-color: #040404; border: none;")
            
            # 如果是可视控件，应用额外样式
            if child.isVisible():
                # 针对特定类型控件的处理
                if isinstance(child, QFrame):
                    child.setFrameShape(QFrame.NoFrame)
                    child.setStyleSheet("background-color: #040404; border: none;")
    
    def load_user_info(self):
        """加载用户信息"""
        try:
            logger.info("开始加载用户信息")
            user_info = self.sp.current_user()
            self.username_action.setText(user_info['display_name'])
            self.api_connected = True
            logger.info(f"加载到用户名: {user_info['display_name']}")
            
            # 加载用户头像
            if user_info['images']:
                image_url = user_info['images'][0]['url']
                logger.debug(f"开始加载用户头像: {image_url}")
                loader = ImageLoader(image_url)
                loader.image_loaded.connect(lambda image: self.on_avatar_loaded(image, image_url))
                self.threads.append(loader)
                loader.start()
                
        except Exception as e:
            logger.error(f"加载用户信息失败: {str(e)}")
            self.username_action.setText(self.language_manager.get_text('topbar.unknown_user', '未知用户'))
            self.api_connected = False
            # 加载默认头像
            self.avatar_btn.setText("?")
            self.avatar_btn.setStyleSheet("""
                QToolButton {
                    background-color: rgba(255, 255, 255, 0.1);
                    border-radius: 16px;
                    color: white;
                    font-weight: bold;
                    font-size: 16px;
                }
                QToolButton:hover {
                    background-color: rgba(255, 255, 255, 0.2);
                }
                QToolButton::menu-indicator {
                    image: none;
                }
            """)
    
    def on_avatar_loaded(self, image, url):
        """头像加载完成回调"""
        if not image.isNull():
            logger.debug("用户头像加载成功，开始处理圆形裁剪")
            # 创建圆形头像
            target_size = 32
            rounded = QImage(target_size, target_size, QImage.Format_ARGB32)
            rounded.fill(Qt.transparent)
            
            painter = QPainter(rounded)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(Qt.white)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(0, 0, target_size, target_size)
            painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
            
            scaled = image.scaled(target_size, target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            painter.drawImage(0, 0, scaled)
            painter.end()
            
            # 缓存头像
            self.cache_manager.cache_image(url, rounded, 'avatar')
            
            self.avatar_btn.setIcon(QIcon(QPixmap.fromImage(rounded)))
            self.avatar_btn.setIconSize(QSize(32, 32))
            logger.debug("用户头像显示完成")
    
    def on_home_clicked(self):
        """处理主页点击事件"""
        logger.debug("用户点击主页按钮")
        self.home_clicked.emit()
    
    def on_settings_clicked(self):
        """处理设置点击事件"""
        logger.debug("用户点击设置按钮")
        self.settings_clicked.emit()
    
    def open_account_page(self):
        """打开Spotify账户页面"""
        logger.info("用户请求打开Spotify账户页面")
        webbrowser.open('https://www.spotify.com/account/overview/')
    
    def logout(self):
        """注销登录"""
        # 检查是否已在注销过程中，防止重复点击
        if self.is_logging_out:
            logger.debug("注销操作已在进行中，忽略重复请求")
            return
            
        self.is_logging_out = True
        logger.info("用户请求注销登录")
        
        try:
            # 删除token文件
            if getattr(sys, 'frozen', False):
                # 如果是打包后的可执行文件
                base_dir = os.path.dirname(sys.executable)
            else:
                # 如果是直接运行脚本
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                
            token_path = os.path.join(base_dir, 'data', 'token.json')
            logger.debug(f"准备删除token文件: {token_path}")
            if os.path.exists(token_path):
                os.remove(token_path)
                logger.info("Token文件已删除")
            else:
                logger.warning(f"Token文件不存在: {token_path}")
            
            # 保存对主窗口的引用
            main_window = self.window()
            
            # 导入在这里，以避免循环导入
            from src.ui.login import LoginWindow
            
            # 创建登录窗口
            logger.info("创建登录窗口")
            self.login_window = LoginWindow()
            
            # 调整登录窗口位置到屏幕中央
            screen = QDesktopWidget().screenGeometry()
            window_size = self.login_window.geometry()
            x = (screen.width() - window_size.width()) // 2
            y = (screen.height() - window_size.height()) // 2
            self.login_window.move(x, y)
            
            # 显示登录窗口
            logger.info("显示登录窗口")
            self.login_window.show()
            
            # 使用timer延迟关闭主窗口，确保登录窗口已完全显示
            logger.info("准备关闭主窗口")
            QTimer.singleShot(100, main_window.close)
            
        except Exception as e:
            logger.error(f"注销失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            self.is_logging_out = False
            QMessageBox.warning(
                self, 
                self.language_manager.get_text('common.error', '错误'), 
                f"{self.language_manager.get_text('logout.failed', '注销失败')}: {str(e)}"
            )