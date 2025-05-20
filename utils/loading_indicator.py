"""
加载指示器控件
"""
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen

class LoadingIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 设置透明背景
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 旋转角度
        self.angle = 0
        
        # 默认尺寸
        self.setFixedSize(40, 40)
        
        # 动画计时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate)
        self.timer.setInterval(50)  # 50毫秒间隔
        
        # 默认颜色
        self.color = QColor("#1DB954")  # Spotify绿色
        
    def rotate(self):
        """旋转指示器"""
        self.angle = (self.angle + 10) % 360
        self.update()
        
    def start(self):
        """开始动画"""
        self.timer.start()
        
    def stop(self):
        """停止动画"""
        self.timer.stop()
        
    def isRunning(self):
        """是否正在运行"""
        return self.timer.isActive()
        
    def setColor(self, color):
        """设置颜色
        :param color: QColor对象或颜色字符串
        """
        if isinstance(color, str):
            self.color = QColor(color)
        else:
            self.color = color
        self.update()
        
    def paintEvent(self, event):
        """绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 计算中心点和半径
        center_x = self.width() / 2
        center_y = self.height() / 2
        radius = min(center_x, center_y) * 0.8
        
        # 保存当前状态
        painter.save()
        
        # 移动到中心点
        painter.translate(center_x, center_y)
        
        # 绘制12个点
        for i in range(12):
            # 计算当前角度
            current_angle = (self.angle + i * 30) % 360
            
            # 计算透明度（角度越大越透明）
            alpha = 255 - int(i * 255 / 14)
            
            # 设置画笔颜色
            color = QColor(self.color)
            color.setAlpha(alpha)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(color))
            
            # 绘制一个圆点
            dot_radius = radius * 0.15
            
            # 计算点的位置
            x = radius * 0.7 * qCos(current_angle * 3.14159 / 180)
            y = radius * 0.7 * qSin(current_angle * 3.14159 / 180)
            
            # 绘制点
            painter.drawEllipse(int(x - dot_radius/2), int(y - dot_radius/2), 
                               int(dot_radius), int(dot_radius))
        
        # 恢复状态
        painter.restore()

def qCos(angle):
    """简单的余弦函数"""
    import math
    return math.cos(angle)

def qSin(angle):
    """简单的正弦函数"""
    import math
    return math.sin(angle) 