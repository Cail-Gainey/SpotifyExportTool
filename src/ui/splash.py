"""启动动画窗口"""
from PyQt5.QtWidgets import QSplashScreen, QProgressBar, QLabel, QVBoxLayout, QWidget, QDesktopWidget
from PyQt5.QtGui import QFont, QPainter, QColor, QPixmap
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QDateTime, QThread
import os
from src.utils.logger import logger
from src.utils.thread_manager import thread_manager  # 引入线程管理器

class UserInfoLoader(QThread):
    """用户信息加载线程"""
    user_info_loaded = pyqtSignal(dict)
    load_error = pyqtSignal(str)
    loading_status = pyqtSignal(str)  # 新增状态报告信号

    def __init__(self, spotify_client):
        super().__init__()
        self.sp = spotify_client

    def run(self):
        """加载用户信息"""
        try:
            # 发送加载状态
            self.loading_status.emit("正在获取用户信息...")
            
            # 获取用户信息
            user_info = self.sp.current_user()
            
            # 发送加载状态
            self.loading_status.emit("正在处理用户信息...")
            
            # 构造用户信息字典
            processed_user_info = {
                'id': user_info.get('id', ''),
                'display_name': user_info.get('display_name', ''),
                'email': user_info.get('email', ''),
                'images': user_info.get('images', []),
                'followers': user_info.get('followers', {}).get('total', 0),
                'country': user_info.get('country', '')
            }
            
            # 发送用户信息
            self.user_info_loaded.emit(processed_user_info)
        
        except Exception as e:
            error_msg = f"加载用户信息失败: {str(e)}"
            logger.error(error_msg)
            self.load_error.emit(error_msg)
            self.loading_status.emit(error_msg)

class PlaylistLoader(QThread):
    """播放列表加载线程"""
    playlists_loaded = pyqtSignal(list)
    load_error = pyqtSignal(str)
    loading_status = pyqtSignal(str)  # 新增状态报告信号

    def __init__(self, spotify_client):
        super().__init__()
        self.sp = spotify_client

    def run(self):
        """加载播放列表"""
        try:
            # 发送加载状态
            self.loading_status.emit("正在获取播放列表...")
            
            # 获取用户播放列表
            results = self.sp.current_user_playlists(limit=50)  # 限制每次获取50个
            playlists = results['items']
            
            # 发送加载状态
            self.loading_status.emit(f"已加载 {len(playlists)} 个播放列表，正在检查更多...")
            
            # 处理分页
            while results['next'] and len(playlists) < 200:  # 限制总数为200个
                try:
                    results = self.sp.next(results)
                    playlists.extend(results['items'])
                    
                    # 更新加载状态
                    self.loading_status.emit(f"已加载 {len(playlists)} 个播放列表...")
                except Exception as page_error:
                    logger.warning(f"获取下一页播放列表时出错: {page_error}")
                    break
            
            # 过滤并清理播放列表数据
            valid_playlists = [
                playlist for playlist in playlists 
                if playlist and isinstance(playlist, dict) and playlist.get('id')
            ]
            
            # 发送加载状态
            self.loading_status.emit(f"成功加载 {len(valid_playlists)} 个有效播放列表")
            
            # 发送播放列表
            self.playlists_loaded.emit(valid_playlists)
        
        except Exception as e:
            error_msg = f"加载播放列表失败: {str(e)}"
            logger.error(error_msg)
            self.load_error.emit(error_msg)
            self.loading_status.emit(error_msg)

class SplashWindow(QSplashScreen):
    # 修改信号定义，增加加载状态信号
    finished = pyqtSignal()
    loading_status = pyqtSignal(str)
    loading_failed = pyqtSignal(str)
    
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
        
        # 添加加载状态标签
        self.status_label = QLabel("正在准备...")
        self.status_label.setStyleSheet("color: #B3B3B3; font-size: 12px;")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # 添加加载参数
        self.sp = None
        self.user_info = None
        self.playlists = None
    
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

    def update_status(self, status):
        """更新加载状态"""
        self.status_label.setText(status)

    def show_error(self, error_msg):
        """显示错误信息"""
        self.status_label.setStyleSheet("color: #FF0000; font-size: 12px;")
        self.status_label.setText(f"加载失败: {error_msg}")
        
        # 确保进度条达到100%
        self.progress_bar.setValue(100)
        
        # 延迟发送完成信号
        QTimer.singleShot(2000, self.complete_animation)

    def start_loading(self, sp):
        """开始加载用户数据和播放列表"""
        self.sp = sp
        
        # 更新状态并记录日志
        logger.info("启动动画开始加载用户数据")
        self.update_status("正在加载用户信息...")
        
        # 创建线程加载用户信息和播放列表
        self.user_loader = UserInfoLoader(self.sp)
        self.user_loader.user_info_loaded.connect(self._on_user_info_loaded)
        self.user_loader.load_error.connect(self._on_load_error)
        self.user_loader.loading_status.connect(self.update_status)  # 连接状态更新信号
        
        # 使用线程管理器注册线程
        thread_manager.register_thread(self.user_loader, 'splash_loader')
        self.user_loader.start()
    
    def _on_user_info_loaded(self, user_info):
        """用户信息加载完成回调"""
        logger.info(f"成功加载用户信息：{user_info.get('display_name', 'Unknown')}")
        
        # 加载播放列表
        logger.info("开始加载播放列表")
        self.update_status("正在加载播放列表...")
        
        self.playlist_loader = PlaylistLoader(self.sp)
        self.playlist_loader.playlists_loaded.connect(self._on_playlists_loaded)
        self.playlist_loader.load_error.connect(self._on_load_error)
        self.playlist_loader.loading_status.connect(self.update_status)  # 连接状态更新信号
        
        # 使用线程管理器注册线程
        thread_manager.register_thread(self.playlist_loader, 'splash_loader')
        self.playlist_loader.start()

    def _on_playlists_loaded(self, playlists):
        """播放列表加载完成回调"""
        logger.info(f"成功加载{len(playlists)}个播放列表")
        
        # 将播放列表存储到Spotify客户端
        self.sp.playlists = playlists
        
        # 发送加载完成信号
        self.close()

    def _on_load_error(self, error):
        """加载错误处理"""
        logger.error(f"启动加载失败: {error}")
        
        # 显示错误信息
        self.show_error(error)
        
        # 关闭启动动画
        self.close()

    def closeEvent(self, event):
        """处理窗口关闭事件"""
        # 停止相关线程
        thread_manager.stop_threads('splash_loader')
        
        # 接受关闭事件
        event.accept()