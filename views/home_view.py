"""
主页视图
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSplitter, QStackedWidget
from PyQt5.QtCore import Qt
from .menu_view import MenuView
from .topbar_view import TopbarView

class HomeView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        # 设置背景颜色
        self.setStyleSheet("""
            QWidget {
                background-color: #040404;
            }
            QSplitter::handle {
                background-color: #040404;
                width: 1px;
            }
        """)
        
        # 创建水平分割器
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(1)
        self.splitter.setChildrenCollapsible(False)
        
        # 创建左侧菜单
        self.menu_view = MenuView()
        self.menu_view.setMinimumWidth(200)
        self.menu_view.setMaximumWidth(200)
        
        # 创建右侧内容区域
        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # 添加顶栏
        self.topbar_view = TopbarView()
        content_layout.addWidget(self.topbar_view)
        
        # 添加主内容区域
        self.main_content = QStackedWidget()
        content_layout.addWidget(self.main_content)
        
        # 将左侧菜单和右侧内容添加到分割器
        self.splitter.addWidget(self.menu_view)
        self.splitter.addWidget(self.content_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.splitter)
        
        # 连接菜单展开/折叠信号
        self.menu_view.menu_toggled.connect(self.on_menu_toggled)

    def on_menu_toggled(self, expanded):
        """处理菜单展开/折叠"""
        width = 200 if expanded else 60
        self.menu_view.setFixedWidth(width)
        self.menu_view.setMaximumWidth(width) 