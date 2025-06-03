"""
登录窗口
"""
import os
import json
import threading
import webbrowser
import http.server
import socketserver
import urllib.parse
from datetime import datetime
import sys

from PyQt5.QtWidgets import (QMainWindow, QLabel, QPushButton, QVBoxLayout, 
                           QWidget, QDesktopWidget, QApplication)
from PyQt5.QtGui import QFont, QPixmap, QIcon
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSettings

from spotipy.oauth2 import SpotifyOAuth
from src.config import config as config
from src.utils.language_manager import LanguageManager
from src.utils.logger import logger
from src.utils.thread_manager import thread_manager  # 引入线程管理器

# 获取当前文件所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 获取项目根目录
if getattr(sys, 'frozen', False):
    # 如果是打包后的可执行文件
    ROOT_DIR = os.path.dirname(sys.executable)
else:
    # 如果是直接运行脚本
    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 缓存目录
CACHE_DIR = os.path.join(ROOT_DIR, 'data')
os.makedirs(CACHE_DIR, exist_ok=True)

sp_oauth = SpotifyOAuth(
    client_id=config.CLIENT_ID,
    client_secret=config.CLIENT_SECRET,
    redirect_uri=config.REDIRECT_URI,
    scope=config.SCOPE
)

access_token = None
authorized = False
server_active = False  # 跟踪服务器状态

# Token文件路径
TOKEN_PATH = os.path.join(CACHE_DIR, 'token.json')

# 全局变量用于保存窗口实例，防止被垃圾回收
__main_window = None
__login_window = None

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        global access_token, authorized
        if self.path.startswith('/login/oauth2/code/spotify'):
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            if 'code' in params:
                try:
                    token_info = sp_oauth.get_access_token(params['code'][0], as_dict=True)
                    access_token = token_info['access_token']
                    # 保存token
                    save_token(token_info)
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.end_headers()
                    # 自定义成功页面，增加样式和友好提示
                    response_text = '''
                    <!DOCTYPE html>
                    <html lang="zh-CN">
                    <head>
                        <meta charset="UTF-8">
                        <title>授权成功</title>
                        <style>
                            body {
                                font-family: 'Arial', sans-serif;
                                background-color: #040404;
                                color: #1DB954;
                                display: flex;
                                justify-content: center;
                                align-items: center;
                                height: 100vh;
                                margin: 0;
                                text-align: center;
                            }
                            .container {
                                background-color: #282828;
                                padding: 40px;
                                border-radius: 10px;
                                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                            }
                            h1 {
                                color: #1DB954;
                                margin-bottom: 20px;
                            }
                            p {
                                color: #b3b3b3;
                                line-height: 1.6;
                            }
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <h1>授权成功！</h1>
                            <p>您已成功授权 SpotifyExportTool。</p>
                            <p>现在可以返回应用程序继续操作。</p>
                            <p>您可以关闭此页面。</p>
                        </div>
                    </body>
                    </html>
                    '''
                    self.wfile.write(response_text.encode('utf-8'))
                    # 更新UI状态
                    authorized = True
                    return
                except Exception as e:
                    logger.error(f"获取token失败: {str(e)}")
        self.send_response(404)
        self.end_headers()
    
    # 重写log_message方法，阻止输出到控制台
    def log_message(self, format, *args):
        pass

# 创建支持地址重用的TCP服务器
class ReuseAddressTCPServer(socketserver.TCPServer):
    allow_reuse_address = True  # 允许重用地址

httpd = None  # 全局服务器实例

def start_local_server():
    """启动本地服务器处理授权回调"""
    global server_active, httpd
    
    if server_active:
        return
        
    try:
        httpd = ReuseAddressTCPServer(("", 8080), MyHandler)
        server_active = True
        httpd.handle_request()  # 只处理一个请求
    except Exception as e:
        logger.error(f"服务器启动失败: {str(e)}")
    finally:
        # 确保服务器关闭并释放资源
        server_active = False
        if httpd:
            httpd.server_close()
            httpd = None

def login_spotify():
    """启动Spotify授权流程"""
    global authorized, server_active
    
    # 重置授权状态
    authorized = False
    
    # 创建并启动服务器线程
    if not server_active:
        server_thread = threading.Thread(target=start_local_server, daemon=True)
        server_thread.start()
    
    # 生成授权URL并打开浏览器
    auth_url = sp_oauth.get_authorize_url()
    webbrowser.open(auth_url)

def save_token(token_info):
    """
    保存token信息
    :param token_info: token信息字典
    """
    try:
        # 确保缓存目录存在
        os.makedirs(CACHE_DIR, exist_ok=True)
        
        # 保存token
        with open(TOKEN_PATH, 'w') as f:
            json.dump(token_info, f)
            
    except Exception as e:
        logger.error(f"保存token失败: {str(e)}")

def load_token():
    """
    加载token信息
    :return: token信息字典，如果不存在或已过期返回None
    """
    try:
        if not os.path.exists(TOKEN_PATH):
            # 尝试从旧的.cache文件加载
            old_cache = 'data/token.json'
            if os.path.exists(old_cache):
                with open(old_cache, 'r') as f:
                    token_info = json.load(f)
                # 保存到新位置
                save_token(token_info)
                # 删除旧文件
                os.remove(old_cache)
                return token_info
            return None
        
        with open(TOKEN_PATH, 'r') as f:
            token_info = json.load(f)
        
        # 检查token是否过期
        expires_at = token_info.get('expires_at', 0)
        if datetime.now().timestamp() > expires_at:
            return None
        
        return token_info
        
    except Exception as e:
        logger.error(f"加载token失败: {str(e)}")
        return None

class LoginWindow(QMainWindow):
    # 定义授权状态变化信号
    auth_status_changed = pyqtSignal(bool)
    
    def __init__(self):
        try:
            global __login_window
            __login_window = self  # 将自身保存到全局变量中

            logger.debug("LoginWindow初始化开始")
            super().__init__()
            
            # 初始化语言管理器
            self.status_label = None
            self.language_manager = LanguageManager()
            self.language_manager.language_changed.connect(self.update_ui_texts)
            
            logger.debug("设置登录窗口UI")
            self.setup_ui()
            logger.debug("更新UI文本")
            self.update_ui_texts()
            
            # 应用全局样式修复，防止白色背景
            self._apply_dark_theme_fixes()
            
            # 设置计时器检查授权状态
            self.auth_timer = QTimer(self)
            self.auth_timer.timeout.connect(self.check_auth_status)
            
            # 连接授权状态变化信号
            self.auth_status_changed.connect(self.on_auth_status_changed)
            
            # 登录状态标志
            self.login_in_progress = False
            
            # 记录主窗口引用
            self.main_window = None
            
            # 窗口居中显示
            self.center_window()
            logger.debug("LoginWindow初始化完成")
        except Exception as e:
            logger.error(f"LoginWindow初始化失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _apply_dark_theme_fixes(self):
        """应用深色主题修复，确保没有白色背景"""
        try:
            # 获取应用程序实例
            app = QApplication.instance()
            if not app:
                return
                
            # 添加更多全局样式，覆盖QComboBox和QMenu的默认白色背景
            additional_style = """
                QComboBox QAbstractItemView, QComboBoxPrivateContainer {
                    background-color: #282828;
                    color: white;
                    border: none;
                    outline: none;
                    padding: 0px;
                    margin: 0px;
                }
                QListView, QTreeView, QTableView {
                    background-color: #282828;
                    color: white;
                    border: none;
                }
                QWidget#qt_scrollarea_viewport {
                    background-color: #282828;
                }
            """
            
            # 检查是否已经有样式表，并追加新样式
            current_style = app.styleSheet()
            if "QComboBox QAbstractItemView" not in current_style:
                app.setStyleSheet(current_style + additional_style)
                
        except Exception as e:
            logger.error(f"应用深色主题修复失败: {str(e)}")
            import traceback
            traceback.print_exc()
            
    def center_window(self):
        """窗口居中显示"""
        try:
            screen = QDesktopWidget().screenGeometry()
            window_size = self.geometry()
            x = (screen.width() - window_size.width()) // 2
            y = (screen.height() - window_size.height()) // 2
            self.move(x, y)
        except Exception as e:
            logger.error(f"窗口居中显示失败: {str(e)}")
    
    def setup_ui(self):
        """设置UI"""
        # 设置窗口属性
        self.setWindowTitle("SpotifyExportTool - 登录")
        self.setFixedSize(400, 500)  # 固定窗口大小
        self.setStyleSheet("background-color: #040404; color: white;")
        
        # 设置窗口图标
        icon_path = os.path.join(ROOT_DIR, "assets", "app_icon.png")
        
            
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            logger.warning(f"窗口图标不存在: {icon_path}")
        
        # 居中显示窗口
        self.center_window()
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建垂直布局
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # 添加Logo
        logo_path = os.path.join(ROOT_DIR, 'assets', 'app_icon.png')
       
        if os.path.exists(logo_path):
            logo_label = QLabel()
            logo_pixmap = QPixmap(logo_path)
            logo_pixmap = logo_pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(logo_pixmap)
            logo_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(logo_label)
        else:
            logger.warning(f"Logo图标不存在: {logo_path}")
        
        # Spotify Logo文字
        self.logo_label = QLabel("SpotifyExportTool")
        self.logo_label.setFont(QFont("PingFang SC", 24, QFont.Bold))
        self.logo_label.setStyleSheet("color: #1DB954;")
        self.logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.logo_label)
        
        # 添加空间
        layout.addSpacing(20)
        
        # 登录按钮
        self.login_button = QPushButton()
        self.login_button.setFont(QFont("PingFang SC", 14))
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #1DB954;
                color: white;
                border: none;
                border-radius: 20px;
                padding: 12px;
            }
            QPushButton:hover {
                background-color: #1ED760;
            }
        """)
        self.login_button.setMinimumHeight(50)
        self.login_button.clicked.connect(self.on_login_clicked)
        layout.addWidget(self.login_button)
        
        # 创建重试按钮（初始隐藏）
        self.retry_button = QPushButton()
        self.retry_button.setFont(QFont("PingFang SC", 12))
        self.retry_button.setStyleSheet("""
            QPushButton {
                background-color: #282828;
                color: white;
                border: none;
                border-radius: 15px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #333333;
            }
        """)
        self.retry_button.setMinimumHeight(40)
        self.retry_button.clicked.connect(self.on_retry_clicked)
        self.retry_button.setVisible(False)  # 初始不可见
        layout.addWidget(self.retry_button)
        
        # 状态文本
        self.status_label = QLabel()
        self.status_label.setFont(QFont("PingFang SC", 12))
        self.status_label.setStyleSheet("color: #b3b3b3;")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # 添加伸展空间
        layout.addStretch()
        
        # 版权信息
        self.copyright_label = QLabel()
        self.copyright_label.setFont(QFont("PingFang SC", 10))
        self.copyright_label.setStyleSheet("color: #535353;")
        self.copyright_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.copyright_label)
        logger.debug("UI界面设置完成")
    
    def update_ui_texts(self):
        """更新UI文本"""
        # 设置窗口标题
        self.setWindowTitle(self.language_manager.get_text('login.title', 'Spotify登录'))
        
        # 更新标签文本
        self.logo_label.setText(self.language_manager.get_text('topbar.app_name', 'SpotifyExport'))
        self.login_button.setText(self.language_manager.get_text('login.btn_login', '使用Spotify账号登录'))
        self.retry_button.setText(self.language_manager.get_text('login.btn_retry', '重试'))
        self.status_label.setText(self.language_manager.get_text('login.welcome', '欢迎使用Spotify导出工具'))
        self.copyright_label.setText(self.language_manager.get_text('login.copyright', '© Cail Gainey'))
    
    def on_login_clicked(self):
        """处理登录按钮点击事件"""
        # 防止重复点击
        if self.login_in_progress:
            return
            
        self.login_in_progress = True
        self.login_button.setEnabled(False)
        self.retry_button.setVisible(True)  # 显示重试按钮
        
        self.status_label.setText(self.language_manager.get_text('login.status_waiting', '正在等待授权...'))
        login_spotify()
        self.auth_timer.start(1000)  # 每秒检查授权状态
    
    def on_retry_clicked(self):
        """处理重试按钮点击事件"""
        # 重置状态
        global authorized, server_active, httpd
        authorized = False
        
        # 检查并强制关闭之前的服务器实例
        if server_active and httpd:
            try:
                httpd.server_close()
            except:
                pass
            httpd = None
            server_active = False
        
        # 重新启动登录流程
        self.status_label.setText(self.language_manager.get_text('login.status_retrying', '正在尝试重新授权...'))
        login_spotify()
        self.auth_timer.start(1000)  # 重新启动计时器
    
    def check_auth_status(self):
        """检查授权状态"""
        global authorized, server_active
        if authorized:
            self.auth_status_changed.emit(True)
            self.auth_timer.stop()
            self.retry_button.setVisible(False)  # 授权成功时隐藏重试按钮
        elif not server_active and self.login_in_progress:
            # 服务器已结束但未授权成功
            self.status_label.setText(self.language_manager.get_text('login.status_incomplete', '授权未完成，请点击重试按钮或重新登录'))
            self.login_button.setEnabled(True)
            # 不重置 login_in_progress，保持重试按钮可见
    
    def on_auth_status_changed(self, status):
        """处理授权状态变化"""
        if status:
            self.status_label.setText(self.language_manager.get_text('login.status_success', '授权成功，正在加载...'))
            QTimer.singleShot(1000, self.open_main_window)
    
    def open_main_window(self):
        """打开主窗口"""
        try:
            logger.debug("准备打开主窗口")
            global __main_window
            from src.ui.home import HomePage
            token_info = load_token()
            if token_info:
                logger.debug("Token有效，创建主窗口")
                self.main_window = HomePage(token_info['access_token'])
                __main_window = self.main_window  # 将主窗口保存到全局变量中，防止被垃圾回收
                
                # 从QSettings中恢复窗口几何属性
                logger.debug("从设置中读取窗口几何信息")
                settings = QSettings()
                if settings.contains("window/geometry"):
                    logger.debug("恢复窗口几何信息")
                    self.main_window.restoreGeometry(settings.value("window/geometry"))
                else:
                    logger.debug("使用默认窗口大小和位置")
                    # 默认窗口大小
                    self.main_window.resize(1200, 780)
                    # 居中显示
                    screen = QDesktopWidget().screenGeometry()
                    window_x = (screen.width() - self.main_window.width()) // 2
                    window_y = (screen.height() - self.main_window.height()) // 2
                    self.main_window.move(window_x, window_y)
                
                # 显示主窗口
                logger.debug("显示主窗口")
                self.main_window.show()
                
                # 确保退出时保存窗口几何属性
                logger.debug("连接窗口几何属性保存")
                try:
                    app = QApplication.instance()
                    if app:
                        app.aboutToQuit.connect(
                            lambda: settings.setValue("window/geometry", self.main_window.saveGeometry())
                        )
                except Exception as e:
                    logger.error(f"连接窗口几何属性保存信号失败: {str(e)}")
                
                # 使用定时器延迟关闭登录窗口，确保主窗口已完全显示
                logger.debug("延迟关闭登录窗口")
                QTimer.singleShot(1000, lambda: self.__close_login_window())
            else:
                logger.warning("Token无效，无法打开主窗口")
                # 重新启用登录按钮
                self.login_button.setEnabled(True)
                self.login_in_progress = False
                self.status_label.setText(self.language_manager.get_text('login.status_invalid_token', 'Token无效，请重新登录'))
        except Exception as e:
            logger.error(f"打开主窗口失败: {str(e)}")
            import traceback
            traceback.print_exc()
            # 恢复登录界面状态
            self.login_button.setEnabled(True)
            self.login_in_progress = False
            self.status_label.setText(self.language_manager.get_text('login.status_error', '打开主窗口失败，请重试'))
    
    def __close_login_window(self):
        """安全关闭登录窗口"""
        try:
            logger.debug("安全关闭登录窗口")
            # 检查主窗口是否已显示
            if self.main_window and self.main_window.isVisible():
                logger.debug("主窗口已显示，关闭登录窗口")
                self.close()
            else:
                logger.debug("主窗口未显示，延迟关闭登录窗口")
                QTimer.singleShot(500, lambda: self.__close_login_window())
        except Exception as e:
            logger.error(f"关闭登录窗口失败: {str(e)}")
            import traceback
            traceback.print_exc()

def start_authorization(self):
    """启动授权过程"""
    # 创建本地服务器
    def start_local_server():
        """启动本地授权服务器"""
        try:
            # 创建并启动本地服务器
            from http.server import HTTPServer, BaseHTTPRequestHandler
            import urllib.parse
            
            class AuthHandler(BaseHTTPRequestHandler):
                def do_GET(self):
                    """处理GET请求"""
                    # 解析查询参数
                    query = urllib.parse.urlparse(self.path).query
                    params = dict(urllib.parse.parse_qsl(query))
                    
                    # 检查是否包含授权码
                    if 'code' in params:
                        # 发送成功响应
                        self.send_response(200)
                        self.send_header('Content-type', 'text/html; charset=utf-8')
                        self.end_headers()
                        
                        # 返回成功页面
                        success_html = f"""
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <meta charset="utf-8">
                            <title>授权成功</title>
                            <style>
                                body {{ 
                                    font-family: Arial, sans-serif; 
                                    background-color: #040404; 
                                    color: #1DB954; 
                                    display: flex; 
                                    justify-content: center; 
                                    align-items: center; 
                                    height: 100vh; 
                                    margin: 0; 
                                    text-align: center;
                                }}
                                .container {{ 
                                    background-color: #121212; 
                                    padding: 30px; 
                                    border-radius: 10px; 
                                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                                }}
                            </style>
                        </head>
                        <body>
                            <div class="container">
                                <h1>登录成功！</h1>
                                <p>正在跳转...</p>
                            </div>
                            <script>
                                setTimeout(function() {{ 
                                    window.close(); 
                                }}, 2000);
                            </script>
                        </body>
                        </html>
                        """
                        
                        self.wfile.write(success_html.encode('utf-8'))
                        
                        # 将授权码传递给主线程
                        self.server.auth_code = params['code']
                    else:
                        # 发送错误响应
                        self.send_response(400)
                        self.end_headers()
                        self.wfile.write(b'Authorization failed')
            
            # 创建服务器
            server_address = ('localhost', 8888)
            httpd = HTTPServer(server_address, AuthHandler)
            httpd.auth_code = None
            
            logger.info("本地授权服务器已启动")
            
            # 等待授权码
            httpd.handle_request()
            
            # 检查是否获取到授权码
            if httpd.auth_code:
                # 发送授权码到主线程
                self.auth_code_received.emit(httpd.auth_code)
            else:
                # 发送错误信号
                self.auth_error.emit("未获取到授权码")
        
        except Exception as e:
            logger.error(f"本地服务器启动失败: {str(e)}")
            self.auth_error.emit(str(e))
    
    # 使用线程管理器安全地运行线程
    thread_manager.safe_thread_run(start_local_server, category='auth_server')
