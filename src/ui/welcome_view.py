"""
欢迎页面视图
"""
from PyQt5.QtWidgets import (QWidget, QLabel, QVBoxLayout, QScrollArea, QSizePolicy)
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt
from datetime import datetime
from src.utils.language_manager import LanguageManager
from src.utils.logger import logger
import os

class WelcomeView(QWidget):
    def __init__(self, sp):
        try:
            logger.debug("WelcomeView初始化开始")
            super().__init__()
            self.sp = sp
            
            # 初始化语言管理器
            self.language_manager = LanguageManager()
            
            # 初始化UI元素
            self.welcome_label = None
            self.message_labels = []
            self.logo_label = None
            self.error_label = None
            
            # 初始化UI
            logger.debug("初始化WelcomeView UI")
            self.init_ui()
            
            # 连接语言变更信号
            self.language_manager.language_changed.connect(self.update_ui_texts)
            
            # 加载用户信息并更新UI
            logger.debug("加载用户信息")
            self.load_user_info()
            logger.info("WelcomeView初始化完成")
        except Exception as e:
            logger.error(f"WelcomeView初始化失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def init_ui(self):
        """初始化UI"""
        # 设置背景颜色
        self.setStyleSheet("""
            QWidget {
                background-color: #040404;
            }
            QLabel {
                background-color: transparent;
            }
            QScrollArea {
                background-color: #040404;
                border: none;
            }
            QScrollBar:vertical {
                background: #282828;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #535353;
                min-height: 30px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #b3b3b3;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建滚动区域，确保在小窗口下可以滚动
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("background-color: #040404;")
        
        # 创建内容容器
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: #040404;")
        content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 中央容器布局 - 使用垂直布局并添加上下边距以实现更好的垂直居中
        self.layout = QVBoxLayout(content_widget)
        self.layout.setContentsMargins(40, 60, 40, 30)  # 左右边距略大，上下边距差异用于视觉平衡
        self.layout.setSpacing(12)  # 减小间距
        self.layout.setAlignment(Qt.AlignHCenter)  # 水平居中
        
        # 欢迎信息
        self.welcome_label = QLabel()
        self.welcome_label.setFont(QFont("PingFang SC", 28, QFont.Bold))
        self.welcome_label.setStyleSheet("color: white;")
        self.welcome_label.setWordWrap(True)  # 允许文本换行
        self.welcome_label.setAlignment(Qt.AlignCenter)  # 文本居中
        self.layout.addWidget(self.welcome_label)
        
        # 间距
        self.layout.addSpacing(15)
        
        # 创建一个内容区域容器，增加文本与左边缘的距离
        message_container = QWidget()
        message_container.setStyleSheet("background-color: transparent;")
        message_layout = QVBoxLayout(message_container)
        message_layout.setContentsMargins(30, 0, 30, 0)  # 左右有30的边距
        message_layout.setSpacing(12)
        
        # 创建消息标签数组
        for i in range(4):
            msg_label = QLabel()
            msg_label.setFont(QFont("PingFang SC", 14))
            msg_label.setStyleSheet("color: #b3b3b3;")
            msg_label.setWordWrap(True)  # 允许文本换行
            msg_label.setAlignment(Qt.AlignLeft)  # 左对齐
            message_layout.addWidget(msg_label)
            self.message_labels.append(msg_label)
        
        # 添加消息容器到主布局
        self.layout.addWidget(message_container)
        
        # 间距
        self.layout.addSpacing(30)
        
        # 添加Logo图片，调整为更小的尺寸
        logo_label = QLabel()
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'app_icon.png')
        if os.path.exists(logo_path):
            logo_pixmap = QPixmap(logo_path)
            logo_pixmap = logo_pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)  # 减小图片尺寸
            logo_label.setPixmap(logo_pixmap)
            logo_label.setAlignment(Qt.AlignCenter)
            logo_label.setStyleSheet("background-color: transparent;")
            self.layout.addWidget(logo_label)
        
        # Spotify Logo文字
        self.logo_label = QLabel()
        self.logo_label.setFont(QFont("PingFang SC", 32, QFont.Bold))  # 减小字体大小
        self.logo_label.setStyleSheet("color: #1DB954;")
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.logo_label)
        
        # 添加底部空间
        self.layout.addStretch()
        
        # 设置滚动区域的内容
        scroll_area.setWidget(content_widget)
        
        # 添加滚动区域到主布局
        main_layout.addWidget(scroll_area)
    
    def paintEvent(self, event):
        """重写绘制事件，确保背景色总是正确的"""
        super().paintEvent(event)
        # 这个方法的存在确保在某些布局变更时，背景色会被重新绘制
    
    def load_user_info(self):
        """加载用户信息并更新UI"""
        try:
            logger.info("开始加载用户信息")
            # 获取用户信息
            user_info = self.sp.current_user()
            self.user_name = user_info['display_name']
            logger.info(f"加载到用户名: {self.user_name}")
            
            # 更新UI文本
            self.update_ui_texts()
            logger.info("用户信息加载完成")
            
        except Exception as e:
            logger.error(f"加载用户信息失败: {str(e)}")
            import traceback
            traceback.print_exc()
            self.error_label = QLabel()
            self.error_label.setStyleSheet("color: #b3b3b3;")
            self.layout.addWidget(self.error_label)
            self.update_ui_texts()
    
    def update_ui_texts(self):
        """更新UI文本"""
        try:
            if self.error_label:
                self.error_label.setText(self.language_manager.get_text('home.loading_failed', '加载失败，请检查网络连接'))
                return
            
            # 获取当前时间
            hour = datetime.now().hour
            if 5 <= hour < 12:
                greeting_key = 'home.good_morning'
            elif 12 <= hour < 18:
                greeting_key = 'home.good_afternoon'
            else:
                greeting_key = 'home.good_evening'
                
            greeting = self.language_manager.get_text(greeting_key)
            
            # 更新欢迎文本
            if hasattr(self, 'user_name'):
                self.welcome_label.setText(f"{greeting}，{self.user_name}")
            else:
                self.welcome_label.setText(greeting)
            
            # 更新使用说明
            message_keys = [
                'home.welcome_msg',
                'home.instruction_1',
                'home.instruction_2',
                'home.instruction_3'
            ]
            
            for i, key in enumerate(message_keys):
                if i < len(self.message_labels):
                    self.message_labels[i].setText(self.language_manager.get_text(key))
            
            # 更新Logo文本
            self.logo_label.setText(self.language_manager.get_text('topbar.app_name', 'SpotifyExport'))
            
        except Exception as e:
            logger.error(f"更新欢迎页面文本失败: {str(e)}") 