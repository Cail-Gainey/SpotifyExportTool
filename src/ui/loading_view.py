"""
加载页面视图
"""
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QProgressBar
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QTimer
from src.utils.language_manager import LanguageManager
from src.utils.logger import logger
from src.utils.loading_indicator import LoadingIndicator

class LoadingView(QWidget):
    """加载页面视图类"""
    
    def __init__(self, message_key='common.loading', message=None, parent=None):
        """
        初始化加载页面
        :param message_key: 消息的语言键
        :param message: 默认消息
        :param parent: 父窗口
        """
        super().__init__(parent)
        
        # 初始化语言管理器
        self.language_manager = LanguageManager()
        self.language_manager.language_changed.connect(self.update_ui_texts)
        
        # 保存消息键和默认消息
        self.message_key = message_key
        self.default_message = message or "加载中..."
        
        # 安全计时器，防止加载页面无限显示
        self.safety_timer = QTimer(self)
        self.safety_timer.setSingleShot(True)
        self.safety_timer.timeout.connect(self.on_safety_timeout)
        self.safety_timer.start(10000)  # 10秒安全超时
        
        # 初始化UI
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        logger.debug("初始化LoadingView界面")
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setAlignment(Qt.AlignCenter)
        
        # 添加加载指示器
        self.loading_indicator = LoadingIndicator(self)
        self.loading_indicator.setFixedSize(60, 60)
        layout.addWidget(self.loading_indicator, 0, Qt.AlignCenter)
        
        # 启动加载动画
        self.loading_indicator.start()
        
        # 加载消息
        self.message_label = QLabel(self.language_manager.get_text(self.message_key, self.default_message))
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setFont(QFont("Arial", 14))
        self.message_label.setStyleSheet("""
            color: #FFFFFF;
            margin-top: 20px;
        """)
        layout.addWidget(self.message_label)
        
        # 加载进度条
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 0)  # 不确定进度
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setFixedWidth(200)  # 固定宽度
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #282828;
                border-radius: 2px;
                border: none;
            }
            QProgressBar::chunk {
                background-color: #1DB954;
                border-radius: 2px;
            }
        """)
        layout.addWidget(self.progress_bar, 0, Qt.AlignCenter)
        
        # 设置背景色和样式
        self.setStyleSheet("""
            background-color: #121212;
        """)
        
        # 更新界面文本
        self.update_ui_texts()
    
    def update_ui_texts(self):
        """更新界面文本"""
        self.message_label.setText(self.language_manager.get_text(self.message_key, self.default_message))
    
    def on_safety_timeout(self):
        """安全计时器触发，防止加载页面无限显示"""
        logger.warning("加载视图安全计时器触发，已超过10秒")
        # 这里不做任何操作，仅记录日志
        # 具体处理逻辑由调用方实现
    
    def set_message(self, message_key):
        """
        设置加载消息
        :param message_key: 消息的语言键
        """
        self.message_key = message_key
        self.update_ui_texts()
        
    def closeEvent(self, event):
        """处理关闭事件"""
        # 停止加载动画
        if hasattr(self, 'loading_indicator'):
            self.loading_indicator.stop()
        event.accept() 