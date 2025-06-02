"""启动动画窗口"""
from PyQt5.QtWidgets import QSplashScreen, QProgressBar, QLabel, QVBoxLayout, QWidget, QDesktopWidget
from PyQt5.QtGui import QFont, QPainter, QColor, QPixmap
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QDateTime
import os
from src.utils.logger import logger

class SplashWindow(QSplashScreen):
    # 添加完成信号
    finished = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setFixedSize(400, 300)
        
        # 设置窗口背景色
        self.setStyleSheet("background-color: #040404;")
        
        # 创建内容容器
        content = QWidget(self)
        content.setGeometry(0, 0, 400, 300)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 20, 0, 0)
        layout.setSpacing(10)
        
        # 添加Logo图标
        logo_label = QLabel()
        logo_pixmap = QPixmap(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../assets', 'app_icon.png'))
        logo_pixmap = logo_pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo_label.setPixmap(logo_pixmap)
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)
        
        # 添加文字
        text_label = QLabel("SpotifyExportTool")
        text_label.setFont(QFont("PingFang SC", 24, QFont.Bold))
        text_label.setStyleSheet("color: #1DB954;")
        text_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(text_label)
        
        # 添加进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedSize(300, 3)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #282828;
                border: none;
                border-radius: 1px;
            }
            QProgressBar::chunk {
                background-color: #1DB954;
                border-radius: 1px;
            }
        """)
        layout.addWidget(self.progress_bar, 0, Qt.AlignCenter)
        
        # 设置进度条初始值
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        
        # 创建定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        
        # 设置进度控制参数
        self.min_display_time = 1200  # 最小显示时间(毫秒)，减少为1.2秒
        self.start_time = 0
        
        # 添加安全定时器，防止动画卡住
        self.safety_timer = QTimer()
        self.safety_timer.setSingleShot(True)
        self.safety_timer.timeout.connect(self.force_finish)
        
    def start(self):
        """启动动画"""
        self.start_time = QDateTime.currentMSecsSinceEpoch()
        
        # 获取屏幕几何信息
        screen = QDesktopWidget().screenGeometry()
        
        # 计算窗口居中位置
        window_width = self.width()
        window_height = self.height()
        x = (screen.width() - window_width) // 2
        y = (screen.height() - window_height) // 2
        
        # 移动窗口到屏幕中央
        self.move(x, y)
        
        self.show()
        self.timer.start(30)  # 更新频率
        
        # 启动安全定时器，3秒后强制完成
        self.safety_timer.start(3000)
    
    def force_finish(self):
        """强制完成启动动画，防止卡住"""
        if self.timer.isActive():
            logger.warning("启动动画安全定时器触发")
            self.timer.stop()
            self.progress_bar.setValue(100)
            self.finished.emit()
    
    def update_progress(self):
        """更新进度条"""
        current_time = QDateTime.currentMSecsSinceEpoch()
        elapsed_time = current_time - self.start_time
        
        current = self.progress_bar.value()
        
        # 简化进度控制逻辑
        if current < 100:
            # 设置固定步长
            step = 2
            
            # 确保在指定时间内能够完成
            if elapsed_time >= self.min_display_time and current < 90:
                step = 5  # 如果时间已经到了但进度条还没接近完成，加快速度
                
            # 更新进度条值
            new_value = min(100, current + step)
            self.progress_bar.setValue(new_value)
            
            # 如果达到100%，发出完成信号
            if new_value == 100:
                # 延迟很短的时间再发送完成信号，确保UI能够更新
                QTimer.singleShot(100, self.complete_animation)
        
    def complete_animation(self):
        """完成动画"""
        self.timer.stop()
        self.safety_timer.stop()  # 停止安全定时器
        self.finished.emit()  # 发出完成信号
    
    def paintEvent(self, event):
        """重写绘制事件，保持背景纯黑"""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#040404"))