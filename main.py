"""
程序主入口文件
"""
import sys
import os
import json
import traceback
from PyQt5.QtWidgets import QApplication, QDesktopWidget, QMessageBox
from PyQt5.QtCore import QSettings
from src.ui.login import load_token, LoginWindow
from src.ui.home import HomePage
from src.ui.splash import SplashWindow  # 添加启动动画导入
from src.utils.logger import logger
from src.config import settings as settings_module

# 设置 QSettings
APP_NAME = "SpotifyExportTool"
ORGANIZATION_NAME = "SpotifyExport"

# 获取程序运行目录
if getattr(sys, 'frozen', False):
    # 如果是打包后的可执行文件
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # 如果是直接运行脚本
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 确保配置目录存在
CONFIG_DIR = os.path.join(BASE_DIR, 'config')
os.makedirs(CONFIG_DIR, exist_ok=True)

SETTINGS_PATH = os.path.join(CONFIG_DIR, 'settings.json')

# 确保日志目录存在
LOG_DIR = os.path.join(BASE_DIR, 'log')
os.makedirs(LOG_DIR, exist_ok=True)

def display_error_message(error_message):
    """显示错误对话框"""
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Critical)
    msg_box.setWindowTitle("运行错误")
    msg_box.setText("程序遇到错误并需要关闭")
    msg_box.setDetailedText(error_message)
    msg_box.setStandardButtons(QMessageBox.Ok)
    msg_box.exec_()

def check_auth_status():
    """
    检查token有效性
    :return: 如果token有效返回token信息，否则返回None
    """
    try:
        token_info = load_token()
        return token_info
    except Exception as e:
        logger.error(f"检查认证状态失败: {str(e)}")
        return None

def load_settings():
    """
    加载应用设置
    :return: 设置字典
    """
    default_settings = {
        'window_width': 1200,
        'window_height': 780,
        'window_x': 100,
        'window_y': 100,
        'sidebar_collapsed': False
    }
    
    try:
        if os.path.exists(SETTINGS_PATH):
            with open(SETTINGS_PATH, 'r') as f:
                settings = json.load(f)
                
            # 合并默认设置，确保所有键都存在
            for key, value in default_settings.items():
                if key not in settings:
                    settings[key] = value
            
            return settings
    except Exception as e:
        logger.error(f"加载设置失败: {str(e)}")
    
    return default_settings

def save_settings(settings):
    """
    保存应用设置
    :param settings: 设置字典
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
        
        with open(SETTINGS_PATH, 'w') as f:
            json.dump(settings, f, indent=2)
    except Exception as e:
        logger.error(f"保存设置失败: {str(e)}")

def main():
    """主函数"""
    try:
        # 在程序开始时记录日志路径
        logger.info(f"程序启动，日志路径: {logger.get_log_path()}")
        logger.info(f"错误日志路径: {logger.get_error_log_path()}")
        logger.info(f"基础目录: {BASE_DIR}")
        logger.info(f"Python版本: {sys.version}")
        logger.info(f"运行模式: {'打包' if getattr(sys, 'frozen', False) else '脚本'}")
        
        global login_window, main_window, splash_window
        app = QApplication(sys.argv)
        
        # 预先检查认证状态
        token = check_auth_status()
        screen = QDesktopWidget().screenGeometry() # 获取屏幕信息以备后用

        # 设置应用名称和组织名称
        app.setApplicationName(APP_NAME)
        app.setOrganizationName(ORGANIZATION_NAME)
        app.setApplicationDisplayName(APP_NAME)  # 设置显示名称
        
        # 设置日志级别
        log_level = settings_module.get_setting("log_level", "info")
        logger.info(f"应用程序启动，设置日志级别为: {log_level}")
        logger.set_level(log_level)  # 确保设置日志级别为 info
        
        # 设置全局样式表
        global_style = """
            QComboBox QAbstractItemView, QComboBoxPrivateContainer {
                background-color: #282828;
                color: white;
                border: none;
                outline: none;
                border-radius: 0px;
                selection-background-color: #1DB954;
                selection-color: white;
                padding: 0px;
                margin: 0px;
            }
            QListView, QTreeView, QTableView {
                background-color: #282828;
                color: white;
                border: none;
                outline: none;
            }
            QListView::item:selected, QTreeView::item:selected {
                background-color: #1DB954;
                color: white;
            }
            QScrollBar:vertical {
                background-color: #282828;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #535353;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
                height: 0px;
                width: 0px;
            }
            QMenu, QMenu::item {
                background-color: #040404;
                color: #b3b3b3;
                margin: 0px;
                padding: 8px 32px;
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
        """
        app.setStyleSheet(global_style)
        
        # 设置应用图标
        from PyQt5.QtGui import QIcon
        icon_path = os.path.join(BASE_DIR, "assets", "app_icon.png")
        if os.path.exists(icon_path):
            app_icon = QIcon(icon_path)
            app.setWindowIcon(app_icon)
        else:
            logger.warning(f"找不到应用图标: {icon_path}")
        
        # 如果token无效，直接显示登录窗口
        if not token:
            logger.info("Token无效或过期，直接显示登录窗口")
            login_window = LoginWindow()
            login_window.show()
        else:
            # 创建启动动画
            splash_window = SplashWindow()
            splash_window.start()

            def on_splash_finished():
                """启动动画完成后的处理函数"""
                splash_window.close()
                
                logger.info("Token有效，创建主窗口")
                # 创建主窗口
                main_window = HomePage(token['access_token'])
                
                # 从设置中读取窗口大小和位置
                logger.info("从设置中读取窗口几何信息")
                settings = QSettings()
                if settings.contains("window/geometry"):
                    logger.info("恢复窗口几何信息")
                    main_window.restoreGeometry(settings.value("window/geometry"))
                else:
                    logger.info("使用默认窗口大小和位置")
                    # 默认窗口大小
                    main_window.resize(1000, 800)
                    # 居中显示
                    window_x = (screen.width() - main_window.width()) // 2
                    window_y = (screen.height() - main_window.height()) // 2
                    main_window.move(window_x, window_y)
                
                # 显示主窗口
                logger.info("显示主窗口")
                main_window.show()
                
                # 程序退出时保存窗口大小和位置
                logger.info("连接窗口退出信号")
                app.aboutToQuit.connect(lambda: settings.setValue("window/geometry", main_window.saveGeometry()))
                logger.info("主窗口设置完成")
            
            # 连接启动动画完成信号
            splash_window.finished.connect(on_splash_finished)
        
        return app.exec_()
    except Exception as e:
        error_message = f"程序启动失败: {str(e)}\n\n详细错误信息:\n{traceback.format_exc()}"
        logger.error(error_message)
        
        # 保存错误信息到文件，确保即使日志系统失败也能捕获错误
        try:
            with open(os.path.join(BASE_DIR, 'crash_report.txt'), 'w', encoding='utf-8') as f:
                f.write(error_message)
        except:
            pass
            
        # 尝试显示错误对话框，如果QApplication已经初始化
        if 'app' in locals():
            try:
                display_error_message(error_message)
            except:
                pass
                
        return 1

# 全局变量用于保存窗口实例
login_window = None
main_window = None

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        error_message = f"未捕获的异常: {str(e)}\n\n详细错误信息:\n{traceback.format_exc()}"
        
        # 保存错误信息到文件
        try:
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'crash_report.txt'), 'w', encoding='utf-8') as f:
                f.write(error_message)
        except:
            pass
            
        print(error_message, file=sys.stderr)
        sys.exit(1)