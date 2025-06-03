"""
播放列表视图的UI组件和布局逻辑
"""

from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QCheckBox,
    QScrollArea,
    QFrame,
)
from PyQt5.QtCore import Qt, QTimer
from src.utils.loading_indicator import LoadingIndicator
from src.utils.logger import logger

def init_ui(self):
    """初始化用户界面"""
    # 创建主布局
    main_layout = QVBoxLayout(self)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(0)

    # 如果有语言管理器，连接语言变更信号
    if hasattr(self, 'locale_manager') and self.locale_manager:
        self.locale_manager.language_changed.connect(self.update_ui_texts)

    # 创建顶部容器
    top_container = QWidget()
    top_container.setStyleSheet("background-color: #121212;")
    top_layout = QVBoxLayout(top_container)
    top_layout.setContentsMargins(30, 30, 30, 20)
    top_layout.setSpacing(20)

    # 创建图片容器
    image_container = QWidget()
    image_layout = QHBoxLayout(image_container)
    image_layout.setContentsMargins(0, 0, 0, 0)
    image_layout.setSpacing(20)

    # 创建播放列表图片标签
    self.playlist_image = QLabel()
    self.playlist_image.setFixedSize(192, 192)
    self.playlist_image.setStyleSheet("background-color: #282828; border-radius: 4px;")
    self.playlist_image.setAlignment(Qt.AlignCenter)

    # 创建加载指示器覆盖层，直接放在播放列表图片上方
    self.loading_container = QWidget(self)
    self.loading_container.setFixedSize(192, 192)
    self.loading_container.setStyleSheet("background-color: rgba(18, 18, 18, 0.7); border-radius: 4px;")
    loading_layout = QVBoxLayout(self.loading_container)
    loading_layout.setContentsMargins(20, 20, 20, 20)
    
    # 加载提示文本
    self.loading_text = QLabel("加载中...")
    self.loading_text.setStyleSheet("color: white; background-color: transparent; font-size: 14px;")
    self.loading_text.setAlignment(Qt.AlignCenter)
    
    # 创建加载指示器
    self.loading_indicator = LoadingIndicator(self.loading_container)
    self.loading_indicator.setFixedSize(48, 48)
    
    # 添加到布局中
    loading_layout.addWidget(self.loading_indicator, 0, Qt.AlignCenter)
    loading_layout.addWidget(self.loading_text, 0, Qt.AlignCenter)
    
    # 初始隐藏加载容器
    self.loading_container.hide()
    self.loading_container.raise_()  # 确保显示在最前面

    # 将加载指示器添加到图片标签
    image_layout.addWidget(self.playlist_image)

    # 创建信息容器
    info_container = QWidget()
    info_layout = QVBoxLayout(info_container)
    info_layout.setContentsMargins(0, 0, 0, 0)
    info_layout.setSpacing(10)

    # 创建标题标签
    self.title_label = QLabel(self.playlist_name)
    self.title_label.setStyleSheet("color: white; font-size: 28px; font-weight: bold;")
    info_layout.addWidget(self.title_label)

    # 创建状态标签
    self.status_label = QLabel()
    self.status_label.setStyleSheet("color: #b3b3b3; font-size: 14px;")
    info_layout.addWidget(self.status_label)

    # 创建按钮容器
    button_container = QWidget()
    button_container.setObjectName("button_container")
    self.button_container = button_container  # 保存为类属性以便后续使用
    button_layout = QHBoxLayout(button_container)
    button_layout.setContentsMargins(0, 0, 0, 0)
    button_layout.setSpacing(10)
    button_layout.setAlignment(Qt.AlignLeft)

    # 创建导出按钮
    self.export_button = QPushButton(self.get_text("playlist.export_button", "导出"))
    self.export_button.setCursor(Qt.PointingHandCursor)
    self.export_button.setStyleSheet(
        """
        QPushButton {
            background-color: #1db954;
            color: white;
            border: none;
            border-radius: 16px;
            padding: 8px 16px;
            font-size: 14px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #1ed760;
        }
        QPushButton:pressed {
            background-color: #1aa34a;
        }
    """
    )
    self.export_button.clicked.connect(self.toggle_export_mode)
    button_layout.addWidget(self.export_button)

    # 创建取消导出按钮
    self.cancel_export_button = QPushButton(self.get_text("playlist.cancel", "取消"))
    self.cancel_export_button.setCursor(Qt.PointingHandCursor)
    self.cancel_export_button.setStyleSheet(
        """
        QPushButton {
            background-color: #333333;
            color: white;
            border: none;
            border-radius: 16px;
            padding: 8px 20px;
            font-size: 14px;
            font-weight: bold;
            min-width: 110px;
            max-width: 180px;
            text-align: center;
            white-space: nowrap;
        }
        QPushButton:hover {
            background-color: #444444;
        }
        QPushButton:pressed {
            background-color: #222222;
        }
    """
    )
    self.cancel_export_button.clicked.connect(self.toggle_export_mode)
    self.cancel_export_button.hide()
    button_layout.addWidget(self.cancel_export_button)

    # 创建全选按钮
    self.select_all_button = QPushButton(self.get_text("playlist.select_all", "全选"))
    self.select_all_button.setCursor(Qt.PointingHandCursor)
    self.select_all_button.setStyleSheet(
        """
        QPushButton {
            background-color: #333333;
            color: white;
            border: none;
            border-radius: 16px;
            padding: 8px 16px;
            font-size: 14px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #444444;
        }
        QPushButton:pressed {
            background-color: #222222;
        }
    """
    )
    self.select_all_button.clicked.connect(self.select_all_songs)
    self.select_all_button.hide()
    button_layout.addWidget(self.select_all_button)

    # 创建清空选择按钮
    self.clear_selection_button = QPushButton(self.get_text("playlist.clear_selection", "清空"))
    self.clear_selection_button.setCursor(Qt.PointingHandCursor)
    self.clear_selection_button.setStyleSheet(
        """
        QPushButton {
            background-color: #333333;
            color: white;
            border: none;
            border-radius: 16px;
            padding: 8px 16px;
            font-size: 14px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #444444;
        }
        QPushButton:pressed {
            background-color: #222222;
        }
    """
    )
    self.clear_selection_button.clicked.connect(self.clear_song_selection)
    self.clear_selection_button.hide()
    button_layout.addWidget(self.clear_selection_button)

    # 创建确认导出按钮
    self.confirm_export_button = QPushButton(self.get_text("common.ok", "确认"))
    self.confirm_export_button.setCursor(Qt.PointingHandCursor)
    self.confirm_export_button.setStyleSheet(
        """
        QPushButton {
            background-color: #1db954;
            color: white;
            border: none;
            border-radius: 16px;
            padding: 8px 20px;
            font-size: 14px;
            font-weight: bold;
            min-width: 120px;
            max-width: 200px;
            text-align: center;
            white-space: nowrap;
        }
        QPushButton:hover {
            background-color: #1ed760;
        }
        QPushButton:pressed {
            background-color: #1aa34a;
        }
    """
    )
    self.confirm_export_button.clicked.connect(self.export_selected)
    self.confirm_export_button.hide()
    button_layout.addWidget(self.confirm_export_button)

    # 创建全选复选框（仅保留对象引用，不添加到UI）
    self.select_all_checkbox = QCheckBox(self.get_text("playlist.select_all", "全选"))
    self.select_all_checkbox.hide()
    
    # 创建全选容器（仅保留对象引用，不添加到UI）
    self.select_all_container = QWidget()
    self.select_all_container.hide()

    # 创建刷新按钮
    self.refresh_button = QPushButton(self.get_text("playlist.refresh", "刷新"))
    self.refresh_button.setStyleSheet(
        """
        QPushButton {
            background-color: #333;
            color: white;
            border-radius: 4px;
            padding: 5px 15px;
            font-size: 14px;
        }
        QPushButton:hover {
            background-color: #444;
        }
    """
    )
    self.refresh_button.clicked.connect(self.refresh_songs)
    button_layout.addWidget(self.refresh_button)

    # 添加按钮容器到信息布局
    info_layout.addWidget(button_container)

    # 添加信息容器到图片布局
    image_layout.addWidget(info_container)

    # 添加图片容器到顶部布局
    top_layout.addWidget(image_container)

    # 创建搜索容器
    search_container = QWidget()
    search_layout = QHBoxLayout(search_container)
    search_layout.setContentsMargins(30, 10, 30, 10)  # 增加上下边距，并与顶部容器保持一致的左右边距
    search_layout.setSpacing(10)

    # 创建搜索图标
    search_icon = QLabel()
    search_icon.setFixedSize(20, 20)
    search_icon.setStyleSheet("background-color: transparent;")
    search_layout.addWidget(search_icon)

    # 创建搜索框
    self.search_box = QLineEdit()
    self.search_box.setPlaceholderText(
        self.get_text("playlist.search_placeholder", "搜索歌曲、艺术家或专辑...")
    )
    self.search_box.setStyleSheet(
        """
        QLineEdit {
            background-color: #333;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 8px 12px;
            font-size: 14px;
        }
        QLineEdit:focus {
            background-color: #444;
        }
    """
    )
    self.search_box.textChanged.connect(self.on_search_changed)
    search_layout.addWidget(self.search_box)

    # 添加搜索容器到顶部布局
    top_layout.addWidget(search_container)

    # 创建歌曲列表容器
    song_list_container = QWidget()
    song_list_layout = QVBoxLayout(song_list_container)
    song_list_layout.setContentsMargins(0, 0, 0, 0)
    song_list_layout.setSpacing(0)

    # 创建歌曲列表标题
    header_container = QWidget()
    header_container.setFixedHeight(40)
    header_container.setStyleSheet("background-color: #121212;")
    header_layout = QHBoxLayout(header_container)
    header_layout.setContentsMargins(10, 0, 10, 0)
    header_layout.setSpacing(10)

    # 创建标题标签
    index_header = QLabel("#")
    index_header.setStyleSheet("color: #b3b3b3; font-size: 14px; font-weight: bold;")
    index_header.setFixedWidth(30)
    index_header.setAlignment(Qt.AlignCenter)
    header_layout.addWidget(index_header)

    # 创建占位符，用于对齐复选框位置
    checkbox_placeholder = QWidget()
    checkbox_placeholder.setFixedWidth(30)
    header_layout.addWidget(checkbox_placeholder)

    # 创建占位符，用于对齐封面位置
    cover_placeholder = QWidget()
    cover_placeholder.setFixedWidth(50)
    header_layout.addWidget(cover_placeholder)

    # 创建标题标签
    self.title_header = QLabel(self.get_text("playlist.column.title", "标题"))
    self.title_header.setStyleSheet("color: #b3b3b3; font-size: 14px; font-weight: bold;")
    self.title_header.setAlignment(Qt.AlignVCenter)
    header_layout.addWidget(self.title_header)

    # 创建专辑标签
    self.album_header = QLabel(self.get_text("playlist.column.album", "专辑"))
    self.album_header.setStyleSheet("color: #b3b3b3; font-size: 14px; font-weight: bold;")
    self.album_header.setAlignment(Qt.AlignVCenter)
    header_layout.addWidget(self.album_header)

    # 创建艺术家标签
    self.artist_header = QLabel(self.get_text("playlist.artist_field", "艺术家"))
    self.artist_header.setStyleSheet("color: #b3b3b3; font-size: 14px; font-weight: bold;")
    self.artist_header.setAlignment(Qt.AlignVCenter)
    header_layout.addWidget(self.artist_header)

    # 添加标题容器到歌曲列表布局
    song_list_layout.addWidget(header_container)

    # 创建分隔线
    separator = QFrame()
    separator.setFrameShape(QFrame.HLine)
    separator.setFrameShadow(QFrame.Plain)
    separator.setStyleSheet("background-color: #333;")
    separator.setFixedHeight(1)
    song_list_layout.addWidget(separator)

    # 创建滚动区域
    self.scroll_area = QScrollArea()
    self.scroll_area.setWidgetResizable(True)
    self.scroll_area.setFrameShape(QFrame.NoFrame)
    self.scroll_area.setStyleSheet(
        """
        QScrollArea {
            background-color: #121212;
            border: none;
        }
        QScrollBar:vertical {
            background-color: #121212;
            width: 10px;
            margin: 0px;
        }
        QScrollBar::handle:vertical {
            background-color: #535353;
            min-height: 20px;
            border-radius: 5px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: none;
        }
    """
    )

    # 创建内容窗口
    self.songs_container = QWidget()
    self.songs_container.setStyleSheet("background-color: #121212;")
    songs_layout = QVBoxLayout(self.songs_container)
    songs_layout.setContentsMargins(0, 0, 0, 0)
    songs_layout.setSpacing(0)
    self.songs_layout = songs_layout  # 将布局保存为类属性

    # 设置内容窗口
    self.scroll_area.setWidget(self.songs_container)

    # 连接滚动信号
    self.scroll_area.verticalScrollBar().valueChanged.connect(self.on_scroll)

    # 添加滚动区域到歌曲列表布局
    song_list_layout.addWidget(self.scroll_area)

    # 添加歌曲列表容器到顶部布局
    top_layout.addWidget(song_list_container)

    # 添加顶部容器到主布局
    main_layout.addWidget(top_container)

    # 设置布局
    self.setLayout(main_layout)


def adjust_responsive_ui(self):
    """根据当前宽度调整UI组件大小，优化响应式布局"""
    current_width = self.width()

    # 如果当前正在重绘，延迟调整
    if self.is_redrawing:
        QTimer.singleShot(100, self.adjust_responsive_ui)
        return

    # 设置正在调整标志
    self.is_redrawing = True

    try:
        # 根据窗口宽度动态调整组件大小
        if current_width < 800:
            # 窄屏适配
            self.width_factor = 0.8
            # 调整标题字体大小
            if hasattr(self, "title_label") and self.title_label:
                self.title_label.setStyleSheet(
                    "color: white; font-size: 22px; font-weight: bold;"
                )

            # 调整按钮字体和大小
            button_style = """
                QPushButton {
                    background-color: #333;
                    color: white;
                    border-radius: 4px;
                    padding: 4px 10px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #444;
                }
            """
            export_button_style = """
            QPushButton {
                background-color: #1DB954;
                    color: white;
                    border-radius: 4px;
                    padding: 4px 10px;
                    font-weight: bold;
                    font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1ED760;
                }
            """

            # 调整搜索框宽度
            if hasattr(self, "search_box"):
                self.search_box.setStyleSheet(
                    """
                    QLineEdit {
                        background-color: #333;
                        color: white;
                        border-radius: 4px;
                        padding: 4px;
                        min-width: 150px;
                        max-width: 200px;
                        font-size: 12px;
            }
        """
                )

            # 调整播放列表封面(顶部大封面)图片大小
            if hasattr(self, "playlist_image") and self.playlist_image:
                self.playlist_image.setFixedSize(150, 150)

        elif current_width < 1000:
            # 中等宽度适配
            self.width_factor = 0.9
            # 调整播放列表封面(顶部大封面)图片大小
            if hasattr(self, "playlist_image") and self.playlist_image:
                self.playlist_image.setFixedSize(180, 180)

            # 调整标题字体大小
            if hasattr(self, "title_label") and self.title_label:
                self.title_label.setStyleSheet(
                    "color: white; font-size: 24px; font-weight: bold;"
                )

            # 调整按钮字体和大小
            button_style = """
            QPushButton {
                    background-color: #333;
                color: white;
                border-radius: 4px;
                    padding: 5px 12px;
                    font-size: 13px;
            }
            QPushButton:hover {
                    background-color: #444;
                }
            """
            export_button_style = """
            QPushButton {
                    background-color: #1DB954;
                color: white;
                border-radius: 4px;
                    padding: 5px 12px;
                    font-weight: bold;
                    font-size: 13px;
            }
            QPushButton:hover {
                    background-color: #1ED760;
                }
            """

            # 调整搜索框宽度
            if hasattr(self, "search_box"):
                self.search_box.setStyleSheet(
                    """
                    QLineEdit {
                        background-color: #333;
                        color: white;
                        border-radius: 4px;
                        padding: 5px;
                        min-width: 180px;
                        max-width: 250px;
                        font-size: 13px;
            }
        """
                )

        else:
            # 宽屏适配
            self.width_factor = 1.0
            # 恢复默认播放列表封面(顶部大封面)图片大小
            if hasattr(self, "playlist_image") and self.playlist_image:
                self.playlist_image.setFixedSize(192, 192)

            # 恢复标题字体大小
            if hasattr(self, "title_label") and self.title_label:
                self.title_label.setStyleSheet(
                    "color: white; font-size: 28px; font-weight: bold;"
                )

            # 标准按钮样式
            button_style = """
            QPushButton {
                    background-color: #333;
                color: white;
                border-radius: 4px;
                    padding: 5px 15px;
                    font-size: 14px;
            }
            QPushButton:hover {
                    background-color: #444;
                }
            """
            export_button_style = """
            QPushButton {
                background-color: #1DB954;
                color: white;
                border-radius: 4px;
                    padding: 5px 15px;
                    font-weight: bold;
                    font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1ED760;
                }
            """

            # 恢复搜索框默认样式
            if hasattr(self, "search_box"):
                self.search_box.setStyleSheet(
                    """
                    QLineEdit {
                        background-color: #333;
                        color: white;
                        border-radius: 4px;
                        padding: 5px;
                        min-width: 200px;
                        max-width: 300px;
                        font-size: 14px;
            }
        """
                )

        # 批量应用按钮样式，避免重复代码
        self._apply_button_styles(button_style, export_button_style)

        # 更新歌曲列表中的项目宽度 - 只调整标题和专辑列
        self.update_song_item_widths()

    finally:
        # 重置正在调整标志
        self.is_redrawing = False


def update_song_item_widths(self):
    """根据当前窗口宽度更新歌曲项的宽度比例"""
    # 获取当前可见区域宽度
    viewport_width = self.scroll_area.viewport().width() if hasattr(self, "scroll_area") else self.width()
    
    # 计算有效宽度（减去边距和滚动条宽度）
    effective_width = max(viewport_width - 60, 500)  # 进一步降低最小有效宽度到500
    
    # 根据窗口宽度设置不同的列宽比例
    if viewport_width < 800:
        # 窄屏模式
        index_width = 30
        checkbox_width = 30
        artwork_width = 40
        # 剩余宽度
        remaining_width = effective_width - index_width - checkbox_width - artwork_width - 60
        # 分配比例 - 窄屏模式下进一步优化比例
        title_ratio = 0.38
        album_ratio = 0.24
        artist_ratio = 0.38
    elif viewport_width < 1000:
        # 中等宽度
        index_width = 30
        checkbox_width = 30
        artwork_width = 50
        # 剩余宽度
        remaining_width = effective_width - index_width - checkbox_width - artwork_width - 70
        # 分配比例
        title_ratio = 0.34
        album_ratio = 0.28
        artist_ratio = 0.38
    else:
        # 宽屏模式
        index_width = 30
        checkbox_width = 30
        artwork_width = 50
        # 剩余宽度
        remaining_width = effective_width - index_width - checkbox_width - artwork_width - 80
        # 分配比例
        title_ratio = 0.33
        album_ratio = 0.33
        artist_ratio = 0.34
    
    # 计算具体宽度 - 降低最小宽度以适应更小的窗口
    title_width = max(int(remaining_width * title_ratio), 60)
    album_width = max(int(remaining_width * album_ratio), 50)
    artist_width = max(int(remaining_width * artist_ratio), 60)
    
    # 确保宽度不会超过实际可用空间
    total_allocated = title_width + album_width + artist_width
    if total_allocated > remaining_width:
        # 按比例缩小各列宽度
        reduction_factor = remaining_width / total_allocated
        title_width = int(title_width * reduction_factor)
        album_width = int(album_width * reduction_factor)
        artist_width = int(artist_width * reduction_factor)
        # 再次确保最小宽度，但使用更小的值
        title_width = max(title_width, 60)
        album_width = max(album_width, 50)
        artist_width = max(artist_width, 60)
    
    # 记录日志
    logger.debug(f"调整歌曲列表宽度: 视口宽度={viewport_width}, 有效宽度={effective_width}, " +
                f"标题={title_width}, 专辑={album_width}, 艺术家={artist_width}")

    # 遍历所有歌曲项，调整其内部控件的宽度
    for i in range(self.songs_layout.count() - 1):  # 减1是因为有一个stretch在最后
        item = self.songs_layout.itemAt(i)
        if item and item.widget():
            song_item = item.widget()

            # 更新歌曲项的布局比例
            if hasattr(song_item, "layout") and song_item.layout():
                layout = song_item.layout()
                
                # 查找各列组件并调整宽度
                for j in range(layout.count()):
                    layout_item = layout.itemAt(j)
                    if layout_item and layout_item.widget():
                        widget = layout_item.widget()
                        
                        if j == 0:  # 索引列
                            widget.setFixedWidth(index_width)
                        elif j == 1:  # 复选框列
                            widget.setFixedWidth(checkbox_width)
                        elif j == 2:  # 图片容器
                            widget.setFixedSize(artwork_width, artwork_width)
                        elif j == 3:  # 标题列
                            widget.setMinimumWidth(title_width)
                            widget.setMaximumWidth(title_width + 20)
                            # 确保文本省略
                            if isinstance(widget, QLabel):
                                widget.setWordWrap(False)
                                widget.setTextFormat(Qt.PlainText)
                                widget.setTextInteractionFlags(Qt.NoTextInteraction)
                        elif j == 4:  # 专辑列
                            widget.setMinimumWidth(album_width)
                            widget.setMaximumWidth(album_width + 20)
                            # 确保文本省略
                            if isinstance(widget, QLabel):
                                widget.setWordWrap(False)
                                widget.setTextFormat(Qt.PlainText)
                                widget.setTextInteractionFlags(Qt.NoTextInteraction)
                        elif j == 5:  # 艺术家列
                            widget.setMinimumWidth(artist_width)
                            widget.setMaximumWidth(artist_width + 20)
                            # 确保文本省略
                            if isinstance(widget, QLabel):
                                widget.setWordWrap(False)
                                widget.setTextFormat(Qt.PlainText)
                                widget.setTextInteractionFlags(Qt.NoTextInteraction)


def _apply_button_styles(self, button_style, export_button_style):
    """批量应用按钮样式
    :param button_style: 普通按钮样式
    :param export_button_style: 导出按钮样式
    """
    # 应用普通按钮样式
    for button_name in [
        "refresh_button",
        "sort_button",
        "cancel_export_button",
        "select_all_button",
        "clear_selection_button",
    ]:
        if hasattr(self, button_name):
            button = getattr(self, button_name)
            if button:
                button.setStyleSheet(button_style)

    # 应用导出按钮样式
    for button_name in ["export_button", "confirm_export_button"]:
        if hasattr(self, button_name):
            button = getattr(self, button_name)
            if button:
                button.setStyleSheet(export_button_style)

def update_ui_texts(self):
    """更新UI文本，用于语言切换"""
    logger.debug("更新播放列表UI文本")
    
    # 更新标题和状态标签
    if hasattr(self, "status_label") and self.song_items:
        count_text = self.get_text("playlist.song_count", "{0} 首歌曲").format(len(self.song_items))
        self.status_label.setText(count_text)
    
    # 更新按钮文本
    if hasattr(self, "export_button"):
        self.export_button.setText(self.get_text("playlist.export_button", "导出"))
        
    if hasattr(self, "cancel_export_button"):
        self.cancel_export_button.setText(self.get_text("playlist.cancel", "取消"))
        
    if hasattr(self, "select_all_button"):
        self.select_all_button.setText(self.get_text("playlist.select_all", "全选"))
        
    if hasattr(self, "clear_selection_button"):
        self.clear_selection_button.setText(self.get_text("playlist.clear_selection", "清空"))
        
    if hasattr(self, "confirm_export_button"):
        self.confirm_export_button.setText(self.get_text("common.ok", "确认"))
        
    if hasattr(self, "refresh_button"):
        self.refresh_button.setText(self.get_text("playlist.refresh", "刷新"))
    
    # 更新搜索框占位符
    if hasattr(self, "search_box"):
        self.search_box.setPlaceholderText(self.get_text("playlist.search_placeholder", "搜索歌曲、艺术家或专辑..."))
    
    # 更新标题栏标签
    if hasattr(self, "title_header"):
        self.title_header.setText(self.get_text("playlist.column.title", "标题"))
        
    if hasattr(self, "album_header"):
        self.album_header.setText(self.get_text("playlist.column.album", "专辑"))
        
    if hasattr(self, "artist_header"):
        self.artist_header.setText(self.get_text("playlist.artist_field", "艺术家"))
    
    # 更新选择框文本
    if hasattr(self, "select_all_checkbox"):
        self.select_all_checkbox.setText(self.get_text("playlist.select_all", "全选"))
