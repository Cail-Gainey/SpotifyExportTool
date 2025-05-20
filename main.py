"""
程序主入口文件
"""
import sys
import os
import json
from PyQt5.QtWidgets import QApplication, QDesktopWidget
from PyQt5.QtCore import QSettings
from login import load_token, LoginWindow
from home import HomePage
from utils.logger import logger

# 设置 QSettings
APP_NAME = "SpotifyExportTool"
ORGANIZATION_NAME = "SpotifyExport"

# 获取程序运行目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_PATH = os.path.join(BASE_DIR, 'config', 'settings.json')

def check_auth_status():
    """
    检查token有效性
    :return: 如果token有效返回token信息，否则返回None
    """
    token_info = load_token()
    return token_info

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
        global login_window, main_window  # 将窗口实例声明为全局变量，防止被垃圾回收
        app = QApplication(sys.argv)
        
        # 设置应用名称和组织名称
        app.setApplicationName(APP_NAME)
        app.setOrganizationName(ORGANIZATION_NAME)
        app.setApplicationDisplayName(APP_NAME)  # 设置显示名称
        
        # 设置日志级别
        settings = QSettings()
        log_level = settings.value("log/level", "info")
        logger.info(f"应用程序启动，设置日志级别为: {log_level}")
        logger.set_level(log_level)
        
        # 设置全局样式表，确保所有下拉框和弹出窗口都有深色背景
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
            logger.info(f"已设置应用图标: {icon_path}")
        else:
            logger.warning(f"找不到应用图标: {icon_path}")
        
        # 预先检查认证状态
        token = check_auth_status()
        screen = QDesktopWidget().screenGeometry() # 获取屏幕信息以备后用

        if not token:
            logger.info("Token无效或过期，直接显示登录窗口")
            login_window = LoginWindow()
            login_window.show()
        else:
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
        
        return app.exec_()
    except Exception as e:
        logger.error(f"程序启动失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

# 全局变量用于保存窗口实例
login_window = None
main_window = None

if __name__ == "__main__":
    sys.exit(main())