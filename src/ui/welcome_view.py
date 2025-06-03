"""
欢迎页面视图
"""
from PyQt5.QtWidgets import (QWidget, QLabel, QVBoxLayout, QScrollArea, QSizePolicy)
from PyQt5.QtGui import QFont, QPixmap, QPainter, QBrush, QImage
from PyQt5.QtCore import Qt
from datetime import datetime
from src.utils.language_manager import LanguageManager
from src.utils.logger import logger
import os
from src.utils.image_loader import ImageLoader
from src.utils.cache_manager import CacheManager

class WelcomeView(QWidget):
    def __init__(self, sp):
        try:
            logger.debug("WelcomeView初始化开始")
            super().__init__()
            self.sp = sp
            
            # 初始化语言管理器和缓存管理器
            self.language_manager = LanguageManager()
            self.cache_manager = CacheManager()
            
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
            self.load_user_info()
            logger.debug("WelcomeView初始化完成")
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
        """加载用户信息"""
        try:
            logger.debug("开始加载用户信息")
            
            # 尝试从多个来源获取用户信息
            user_info = None
            
            # 首先尝试从Spotify客户端的user_info属性获取
            if hasattr(self.sp, 'user_info'):
                user_info = self.sp.user_info
                logger.debug("从sp.user_info获取用户信息")
            
            # 如果user_info为None，尝试直接调用current_user()
            if user_info is None:
                try:
                    user_info = self.sp.current_user()
                    logger.debug("通过current_user()获取用户信息")
                except Exception as current_user_error:
                    logger.error(f"获取用户信息失败: {current_user_error}")
            
            # 检查用户信息是否有效
            if user_info and isinstance(user_info, dict):
                # 存储用户名
                self.user_name = user_info.get('display_name', '未知用户')
                logger.info(f"加载到用户名: {self.user_name}")
                
                # 更新欢迎文本
                self._update_welcome_text()
                
                # 加载用户头像
                if user_info.get('images'):
                    image_url = user_info['images'][0]['url']
                    logger.debug(f"开始加载用户头像: {image_url}")
                    
                    # 使用异步加载头像
                    loader = ImageLoader(image_url, track_id='user_avatar', cache_manager=self.cache_manager)
                    loader.image_loaded.connect(self.on_avatar_loaded)
                    loader.load_failed.connect(self._on_avatar_load_failed)
                    loader.start()
                else:
                    logger.warning("用户信息中没有头像")
            else:
                # 如果无法获取用户信息，显示默认文本
                logger.error("无法获取有效的用户信息")
                self.welcome_label.setText(self.language_manager.get_text('welcome.unknown_user', '未知用户'))
                
                # 尝试加载默认头像
                self._load_default_avatar()
        
        except Exception as e:
            logger.error(f"加载用户信息时发生异常: {str(e)}")
            self.welcome_label.setText(self.language_manager.get_text('welcome.unknown_user', '未知用户'))
            self._load_default_avatar()
    
    def _load_default_avatar(self):
        """加载默认头像"""
        default_avatar_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            'assets', 
            'default_avatar.png'
        )
        
        if os.path.exists(default_avatar_path):
            logger.debug(f"加载默认头像: {default_avatar_path}")
            avatar_pixmap = QPixmap(default_avatar_path)
            avatar_pixmap = avatar_pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.on_avatar_loaded(avatar_pixmap.toImage())
        else:
            logger.error(f"默认头像文件不存在: {default_avatar_path}")
    
    def _update_welcome_text(self):
        """更新欢迎文本，添加更多个性化信息"""
        try:
            # 获取当前时间
            hour = datetime.now().hour
            
            # 根据时间选择问候语
            if 5 <= hour < 12:
                greeting_key = 'home.good_morning'
            elif 12 <= hour < 18:
                greeting_key = 'home.good_afternoon'
            else:
                greeting_key = 'home.good_evening'
            
            # 获取问候语
            greeting = self.language_manager.get_text(greeting_key)
            
            # 组合欢迎文本
            welcome_text = f"{greeting}，{self.user_name}"
            
            # 设置欢迎标签文本
            self.welcome_label.setText(welcome_text)
            
            # 更新其他消息标签
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
            if hasattr(self, 'logo_label'):
                self.logo_label.setText(self.language_manager.get_text('topbar.app_name', 'SpotifyExport'))
        
        except Exception as e:
            logger.error(f"更新欢迎页面文本失败: {str(e)}")
            # 如果出错，至少显示用户名
            if hasattr(self, 'user_name'):
                self.welcome_label.setText(self.user_name)
    
    def _on_avatar_load_failed(self, url):
        """处理头像加载失败的情况"""
        logger.warning(f"用户头像加载失败: {url}")
        
        # 尝试加载默认头像
        self._load_default_avatar()
    
    def update_ui_texts(self):
        """更新UI文本"""
        try:
            # 如果已经有用户名，重新更新欢迎文本
            if hasattr(self, 'user_name'):
                self._update_welcome_text()
            
            # 更新Logo文本
            if hasattr(self, 'logo_label'):
                self.logo_label.setText(self.language_manager.get_text('topbar.app_name', 'SpotifyExport'))
        
        except Exception as e:
            logger.error(f"更新欢迎页面文本失败: {str(e)}")
    
    def on_avatar_loaded(self, image):
        """头像加载完成回调"""
        try:
            if image is None or (hasattr(image, 'isNull') and image.isNull()):
                logger.warning("用户头像加载失败")
                return
            
            # 处理不同类型的图像输入
            if isinstance(image, QImage):
                pixmap = QPixmap.fromImage(image)
            elif isinstance(image, QPixmap):
                pixmap = image
            else:
                logger.warning(f"未知的图像类型: {type(image)}")
                return
            
            # 缩放头像到合适尺寸
            scaled_pixmap = pixmap.scaled(
                120, 120, 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            
            logger.debug("用户头像加载成功")
            
            # 更新欢迎页面的头像显示
            if hasattr(self, 'logo_label'):
                # 如果有logo标签，可以在这里进行进一步处理
                pass
        except Exception as e:
            logger.error(f"处理用户头像时发生错误: {str(e)}")
            import traceback
            logger.error(traceback.format_exc()) 