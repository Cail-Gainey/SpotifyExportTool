"""
错误页面视图
"""
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QHBoxLayout
from PyQt5.QtGui import QFont, QIcon, QPixmap
from PyQt5.QtCore import Qt, pyqtSignal
import os
from utils.language_manager import LanguageManager
from utils.logger import logger

class ErrorView(QWidget):
    """错误页面视图类"""
    
    # 信号定义
    retry_clicked = pyqtSignal()
    back_clicked = pyqtSignal()
    
    def __init__(self, error_type="general", error_message=None, parent=None):
        """
        初始化错误页面
        :param error_type: 错误类型，支持 "general", "loading", "network", "permission", "not_found"
        :param error_message: 自定义错误消息
        :param parent: 父控件
        """
        super().__init__(parent)
        
        # 初始化语言管理器
        self.language_manager = LanguageManager()
        
        # 保存错误类型和消息
        self.error_type = error_type
        self.error_message = error_message
        
        # 初始化UI
        self.init_ui()
        
        # 监听语言变更
        self.language_manager.language_changed.connect(self.update_ui_texts)
    
    def init_ui(self):
        """初始化UI"""
        logger.debug(f"初始化ErrorView界面，错误类型：{self.error_type}")
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        
        # 错误图标
        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignCenter)
        icon_path = os.path.join("assets", f"error_{self.error_type}.png")
        if not os.path.exists(icon_path):
            icon_path = os.path.join("assets", "error_general.png")
        
        icon_pixmap = QPixmap(icon_path)
        if not icon_pixmap.isNull():
            icon_pixmap = icon_pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(icon_pixmap)
        else:
            # 如果图标不存在，使用文本代替
            icon_label.setText("⚠️")
            icon_label.setStyleSheet("font-size: 64px;")
        
        layout.addWidget(icon_label)
        
        # 错误标题
        self.title_label = QLabel()
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(QFont("Arial", 18, QFont.Bold))
        self.title_label.setStyleSheet("color: #FFFFFF;")
        layout.addWidget(self.title_label)
        
        # 错误描述
        self.description_label = QLabel()
        self.description_label.setAlignment(Qt.AlignCenter)
        self.description_label.setFont(QFont("Arial", 14))
        self.description_label.setStyleSheet("color: #B3B3B3;")
        self.description_label.setWordWrap(True)
        layout.addWidget(self.description_label)
        
        # 自定义错误消息
        if self.error_message:
            self.message_label = QLabel(self.error_message)
            self.message_label.setAlignment(Qt.AlignCenter)
            self.message_label.setFont(QFont("Arial", 12))
            self.message_label.setStyleSheet("color: #E91429; margin-top: 10px;")
            self.message_label.setWordWrap(True)
            layout.addWidget(self.message_label)
        
        # 按钮容器
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 20, 0, 0)
        button_layout.setSpacing(15)
        
        # 重试按钮
        self.retry_button = QPushButton()
        self.retry_button.setFixedSize(120, 40)
        self.retry_button.setCursor(Qt.PointingHandCursor)
        self.retry_button.setStyleSheet("""
            QPushButton {
                background-color: #1DB954;
                color: white;
                border-radius: 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1ED760;
            }
            QPushButton:pressed {
                background-color: #1AA34A;
            }
        """)
        self.retry_button.clicked.connect(self.retry_clicked)
        button_layout.addWidget(self.retry_button)
        
        # 返回按钮
        self.back_button = QPushButton()
        self.back_button.setFixedSize(120, 40)
        self.back_button.setCursor(Qt.PointingHandCursor)
        self.back_button.setStyleSheet("""
            QPushButton {
                background-color: #333333;
                color: white;
                border-radius: 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #3E3E3E;
            }
            QPushButton:pressed {
                background-color: #282828;
            }
        """)
        self.back_button.clicked.connect(self.back_clicked)
        button_layout.addWidget(self.back_button)
        
        layout.addWidget(button_container)
        
        # 设置背景色
        self.setStyleSheet("background-color: #121212;")
        
        # 更新界面文本
        self.update_ui_texts()
    
    def update_ui_texts(self):
        """更新UI文本"""
        # 根据错误类型设置标题和描述
        if self.error_type == "loading":
            self.title_label.setText(self.language_manager.get_text("error.loading_title", "加载失败"))
            self.description_label.setText(self.language_manager.get_text("error.loading_description", "无法加载内容，请检查网络连接后重试。"))
        elif self.error_type == "network":
            self.title_label.setText(self.language_manager.get_text("error.network_title", "网络错误"))
            self.description_label.setText(self.language_manager.get_text("error.network_description", "无法连接到服务器，请检查网络连接后重试。"))
        elif self.error_type == "permission":
            self.title_label.setText(self.language_manager.get_text("error.permission_title", "权限错误"))
            self.description_label.setText(self.language_manager.get_text("error.permission_description", "您没有访问此内容的权限。"))
        elif self.error_type == "not_found":
            self.title_label.setText(self.language_manager.get_text("error.not_found_title", "内容不存在"))
            self.description_label.setText(self.language_manager.get_text("error.not_found_description", "您请求的内容不存在或已被删除。"))
        else:
            self.title_label.setText(self.language_manager.get_text("error.general_title", "出现错误"))
            self.description_label.setText(self.language_manager.get_text("error.general_description", "应用程序遇到一个错误，请稍后重试。"))
        
        # 设置按钮文本
        self.retry_button.setText(self.language_manager.get_text("common.retry", "重试"))
        self.back_button.setText(self.language_manager.get_text("common.back", "返回")) 