"""
设置页面视图
"""
from PyQt5.QtWidgets import (QWidget, QLabel, QPushButton, QVBoxLayout, 
                           QHBoxLayout, QFrame, QMessageBox, QComboBox, QRadioButton, QButtonGroup, QScrollArea, QSizePolicy)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from src.utils.cache_manager import CacheManager
from src.utils.language_manager import LanguageManager
from src.utils.logger import logger, set_log_level
import os
from PyQt5.QtCore import QSettings, QEvent
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from src.config import settings
from src.config import version as version_module

class SettingsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cache_manager = CacheManager()
        self.language_manager = LanguageManager()
        
        # 创建所有必要的控件
        self.language_combo = QComboBox()
        self.language_combo.addItem(self.language_manager.get_text("settings.language.zh_CN"), "zh_CN")
        self.language_combo.addItem(self.language_manager.get_text("settings.language.en_US"), "en_US")
        self.language_combo.setMinimumWidth(200)
        self.language_combo.setFixedHeight(40)
        self.language_combo.setStyleSheet("""
            QComboBox {
                background-color: #282828;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 15px;
                font-size: 14px;
            }
        """)
        
        # 导出格式下拉框
        self.export_format_combo = QComboBox()
        self.export_format_combo.addItem(self.language_manager.get_text('playlist.format_name_artist', '歌名-歌手'), "name-artists")
        self.export_format_combo.addItem(self.language_manager.get_text('playlist.format_artist_name', '歌手-歌名'), "artists-name")
        self.export_format_combo.addItem(self.language_manager.get_text('playlist.format_name_artist_album', '歌名-歌手-专辑'), "name-artists-album")
        self.export_format_combo.setMinimumWidth(200)
        self.export_format_combo.setFixedHeight(40)
        self.export_format_combo.setStyleSheet("""
            QComboBox {
                background-color: #282828;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 15px;
                font-size: 14px;
            }
        """)
        
        # 文件格式单选按钮
        self.txt_radio = QRadioButton(self.language_manager.get_text("settings.export.txt_format", "文本文件 (.txt)"))
        self.txt_radio.setStyleSheet("color: white; font-size: 14px;")
        
        self.csv_radio = QRadioButton(self.language_manager.get_text("settings.export.csv_format", "CSV文件 (.csv)"))
        self.csv_radio.setStyleSheet("color: white; font-size: 14px;")
        
        self.json_radio = QRadioButton(self.language_manager.get_text("settings.export.json_format", "JSON文件 (.json)"))
        self.json_radio.setStyleSheet("color: white; font-size: 14px;")
        
        # 创建按钮组
        self.file_format_group = QButtonGroup(self)
        self.file_format_group.addButton(self.txt_radio, 1)
        self.file_format_group.addButton(self.csv_radio, 2)
        self.file_format_group.addButton(self.json_radio, 3)
        
        # 日志级别下拉框
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItem(self.language_manager.get_text("settings.log.level.debug", "调试"), "debug")
        self.log_level_combo.addItem(self.language_manager.get_text("settings.log.level.info", "信息"), "info")
        self.log_level_combo.addItem(self.language_manager.get_text("settings.log.level.warning", "警告"), "warning")
        self.log_level_combo.addItem(self.language_manager.get_text("settings.log.level.error", "错误"), "error")
        self.log_level_combo.setMinimumWidth(200)
        self.log_level_combo.setFixedHeight(40)
        self.log_level_combo.setStyleSheet("""
            QComboBox {
                background-color: #282828;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 15px;
                font-size: 14px;
            }
        """)
        
        # 清除缓存按钮
        self.clear_cache_btn = QPushButton(self.language_manager.get_text("settings.cache.clear_btn"))
        self.clear_cache_btn.setFixedSize(120, 40)
        self.clear_cache_btn.setStyleSheet("""
            QPushButton {
                background-color: #E91429;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #FF1622;
            }
        """)
        
        # 查看日志按钮
        self.view_log_btn = QPushButton(self.language_manager.get_text("settings.log.view_btn", "查看日志"))
        self.view_log_btn.setFixedSize(120, 40)
        self.view_log_btn.setStyleSheet("""
            QPushButton {
                background-color: #282828;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #333333;
            }
        """)
        
        # 版本标签
        current_version = version_module.get_version()
        self.version_label = QLabel(f"v{current_version}")
        self.version_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        
        # 连接信号
        self.language_combo.currentIndexChanged.connect(self.on_language_changed)
        self.export_format_combo.currentIndexChanged.connect(self.on_export_format_changed)
        self.file_format_group.buttonClicked.connect(self.on_file_format_changed)
        self.log_level_combo.currentIndexChanged.connect(self.on_log_level_changed)
        self.clear_cache_btn.clicked.connect(self.clear_cache)
        self.view_log_btn.clicked.connect(self.view_log)
        
        # 连接语言变更信号
        self.language_manager.language_changed.connect(self.update_ui_texts)
        
        # 初始化QSettings
        self.settings = QSettings("Spotify", "SpotifyExport")
        
        # 初始化UI
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        # 设置背景颜色和边框
        self.setStyleSheet("""
            QWidget {
                background-color: #040404;
                border: none;
            }
        """)
        
        # 创建外层布局
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)  # 完全移除外部边距
        outer_layout.setSpacing(0)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)  # 确保无边框
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #040404;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #121212;
                width: 8px;
                margin: 0px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background-color: #535353;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
                border: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
                border: none;
            }
        """)
        
        # 创建内容容器
        content_widget = QWidget()
        content_widget.setStyleSheet("""
            QWidget {
                background-color: #040404;
                border: none;
            }
        """)
        
        # 创建内容布局
        main_layout = QVBoxLayout(content_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)  # 保持内部边距
        main_layout.setSpacing(8)  # 减小组件间距
        
        # 定义通用的布局创建函数
        def create_section_container(title_text, desc_text, control_widget=None):
            container = QWidget()
            container.setStyleSheet("background-color: #040404;")
            layout = QVBoxLayout(container)
            layout.setContentsMargins(0, 3, 0, 3)  # 更小的垂直边距
            layout.setSpacing(5)  # 减小内部间距
            
            # 标题
            title_label = QLabel(title_text)
            title_label.setFont(QFont("PingFang SC", 16, QFont.Bold))
            title_label.setStyleSheet("color: white; margin-bottom: 2px;")
            title_label.setWordWrap(True)
            title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            layout.addWidget(title_label)
            
            # 描述
            desc_label = QLabel(desc_text)
            desc_label.setStyleSheet("color: #b3b3b3; font-size: 12px; margin-bottom: 3px;")
            desc_label.setWordWrap(True)
            desc_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            layout.addWidget(desc_label)
            
            # 控制区域
            if control_widget:
                control_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                layout.addWidget(control_widget)
            
            return container, title_label, desc_label
        
        # 设置标题
        self.title_label = QLabel(self.language_manager.get_text("settings.title"))
        self.title_label.setFont(QFont("PingFang SC", 20, QFont.Bold))
        self.title_label.setStyleSheet("color: white; margin-bottom: 10px;")
        self.title_label.setWordWrap(True)
        self.title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        main_layout.addWidget(self.title_label)
        
        # 语言设置部分
        language_container, self.lang_title, self.lang_desc = create_section_container(
            self.language_manager.get_text("settings.language.title"),
            self.language_manager.get_text("settings.language.label"),
            self.language_combo
        )
        main_layout.addWidget(language_container)
        
        # 导出设置部分
        export_control_widget = QWidget()
        export_control_layout = QVBoxLayout(export_control_widget)
        export_control_layout.setContentsMargins(0, 0, 0, 0)
        export_control_layout.setSpacing(5)
        
        # 导出格式容器
        format_container = QWidget()
        format_layout = QHBoxLayout(format_container)
        format_layout.setContentsMargins(0, 0, 0, 0)
        format_layout.setSpacing(5)
        format_label = QLabel(self.language_manager.get_text("settings.export.format_label"))
        format_label.setStyleSheet("color: white;")
        format_layout.addWidget(format_label)
        format_layout.addWidget(self.export_format_combo)
        export_control_layout.addWidget(format_container)
        
        # 文件格式容器
        file_format_container = QWidget()
        file_format_layout = QHBoxLayout(file_format_container)
        file_format_layout.setContentsMargins(0, 0, 0, 0)
        file_format_layout.setSpacing(10)
        file_format_layout.addWidget(self.txt_radio)
        file_format_layout.addWidget(self.csv_radio)
        file_format_layout.addWidget(self.json_radio)
        file_format_layout.addStretch()
        export_control_layout.addWidget(file_format_container)
        
        export_container, self.export_title, self.export_desc = create_section_container(
            self.language_manager.get_text("settings.export.title"),
            self.language_manager.get_text("settings.export.desc"),
            export_control_widget
        )
        main_layout.addWidget(export_container)
        
        # 缓存设置部分
        cache_container, self.cache_title, self.cache_desc = create_section_container(
            self.language_manager.get_text("settings.cache.title"),
            self.language_manager.get_text("settings.cache.desc"),
            self.clear_cache_btn
        )
        main_layout.addWidget(cache_container)
        
        # 日志设置部分
        log_control_widget = QWidget()
        log_control_layout = QHBoxLayout(log_control_widget)
        log_control_layout.setContentsMargins(0, 0, 0, 0)
        log_control_layout.setSpacing(5)
        log_level_label = QLabel(self.language_manager.get_text("settings.log.level_label"))
        log_level_label.setStyleSheet("color: white;")
        log_control_layout.addWidget(log_level_label)
        log_control_layout.addWidget(self.log_level_combo)
        log_control_layout.addWidget(self.view_log_btn)
        log_control_layout.addStretch()
        
        log_container, self.log_title, self.log_desc = create_section_container(
            self.language_manager.get_text("settings.log.title"),
            self.language_manager.get_text("settings.log.desc"),
            log_control_widget
        )
        main_layout.addWidget(log_container)
        
        # 版本信息部分
        version_container, self.version_title, self.version_desc = create_section_container(
            self.language_manager.get_text("settings.version.title"),
            self.language_manager.get_text("settings.version.desc"),
            self.version_label
        )
        main_layout.addWidget(version_container)
        
        # 设置滚动区域的内容部件
        scroll_area.setWidget(content_widget)
        outer_layout.addWidget(scroll_area)
        
        # 调整控件的最小宽度和大小策略
        self.language_combo.setMinimumWidth(180)
        self.language_combo.setMaximumWidth(250)
        self.language_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        self.export_format_combo.setMinimumWidth(180)
        self.export_format_combo.setMaximumWidth(250)
        self.export_format_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        self.log_level_combo.setMinimumWidth(180)
        self.log_level_combo.setMaximumWidth(250)
        self.log_level_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # 单选按钮的大小策略
        for radio_btn in [self.txt_radio, self.csv_radio, self.json_radio]:
            radio_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # 应用下拉框的修复
        self._apply_combo_box_fixes()
        
        # 设置当前语言
        current_lang = settings.get_setting("language", "zh_CN")  # 优先从user_settings.json读取
        if not current_lang:
            current_lang = self.settings.value("language", "zh_CN")  # 从QSettings读取
        
        # 设置语言下拉框的当前选项
        index = self.language_combo.findData(current_lang)
        if index >= 0:
            self.language_combo.blockSignals(True)
            self.language_combo.setCurrentIndex(index)
            self.language_combo.blockSignals(False)
        
        # 设置实际语言
        self.language_manager.set_language(current_lang)
        
        # 更新UI文本
        self.update_ui_texts()
        
        # 获取缓存大小
        self.get_cache_size()
    
    def _apply_combo_box_fixes(self):
        """应用ComboBox特殊修复，解决下拉框空白问题"""
        try:
            # 设置全局样式以覆盖所有可能的白色背景区域
            additional_style = """
                QComboBoxPrivateContainer, QComboBox QAbstractItemView {
                    background-color: #282828;
                    color: white;
                    border: none;
                    outline: none;
                    padding: 0px;
                    margin: 0px;
                    border-radius: 0px;
                    selection-background-color: #1DB954;
                    selection-color: white;
                }
                QListView, QListView::item, QTreeView, QTreeView::item, QTableView {
                    background-color: #282828;
                    color: white;
                    border: none;
                    outline: none;
                }
                QListView::item:hover, QTreeView::item:hover {
                    background-color: #333333;
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
                /* 针对标准部件容器的显式样式 */
                QWidget#qt_scrollarea_viewport, QWidget#qt_scrollarea_hcontainer, 
                QWidget#qt_scrollarea_vcontainer {
                    background-color: #282828;
                    border: none;
                }
                /* 处理QMenu下的视图 */
                QMenu, QMenu::item, QMenu QWidget {
                    background-color: #040404;
                    color: #b3b3b3;
                }
                QMenu::item:selected {
                    background-color: #282828;
                    color: white;
                }
            """
            QApplication.instance().setStyleSheet(QApplication.instance().styleSheet() + additional_style)
            
            # 为所有ComboBox应用设置
            for combo_box in [self.language_combo, self.export_format_combo, self.log_level_combo]:
                if combo_box:
                    # 安装事件过滤器捕获弹出事件
                    combo_box.installEventFilter(self)
                    # 设置视图属性
                    popup = combo_box.view()
                    if popup:
                        popup.viewport().setAutoFillBackground(False)
                        popup.viewport().setStyleSheet("background-color: #282828; border: none;")
                        # 设置视图边框和边距
                        popup.setFrameShape(QFrame.NoFrame)
                        popup.setContentsMargins(0, 0, 0, 0)
                        
                        # 递归设置所有子控件
                        for child in popup.findChildren(QWidget):
                            child.setAutoFillBackground(False)
                            if "viewport" in child.objectName().lower():
                                child.setStyleSheet("background-color: #282828; border: none;")
        except Exception as e:
            print(f"应用ComboBox修复失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def eventFilter(self, obj, event):
        """事件过滤器，用于处理ComboBox弹出事件"""
        # 阻止鼠标滚轮事件改变下拉框选项
        if event.type() == QEvent.Wheel and isinstance(obj, QComboBox):
            # 拦截滚轮事件，防止滚动改变选项
            return True
            
        if event.type() == QEvent.Show and isinstance(obj, QComboBox):
            # 当下拉框显示时调整其视图
            popup = obj.view()
            if popup:
                # 确保视图没有空白
                popup.setContentsMargins(0, 0, 0, 0)
                popup.setFrameShape(QFrame.NoFrame)
                popup.viewport().setAutoFillBackground(False)
                popup.viewport().setStyleSheet("background-color: #282828; border: none;")
                
                # 设置窗口标志，防止阴影和透明
                container = obj.findChild(QWidget, "QComboBoxPrivateContainer")
                if container:
                    container.setWindowFlags(container.windowFlags() | Qt.NoDropShadowWindowHint)
                    container.setAttribute(Qt.WA_TranslucentBackground, True)
                    container.setStyleSheet("background-color: #282828; border: none;")
                
                # 延迟执行一些额外的样式设置，确保dropdown真正显示后应用
                QTimer.singleShot(10, lambda: self._apply_additional_dropdown_fixes(popup))
                # 设置另一个延迟，确保所有子控件都创建完毕
                QTimer.singleShot(50, lambda: self._apply_additional_dropdown_fixes(popup))
        return super().eventFilter(obj, event)
        
    def _apply_additional_dropdown_fixes(self, widget):
        """应用额外的下拉框修复"""
        try:
            # 对视图的所有子部件设置样式
            for child in widget.findChildren(QWidget):
                # 禁用自动填充背景，这是导致白色区域的主要原因之一
                child.setAutoFillBackground(False)
                
                if "viewport" in child.objectName().lower():
                    child.setStyleSheet("background-color: #282828; border: none;")
                
                # 处理可能的滚动区域viewport
                if child.objectName() == "qt_scrollarea_viewport":
                    child.setAutoFillBackground(False)
                    child.setStyleSheet("background-color: #282828; border: none;")
                    
                # 递归处理这个控件的子控件
                for grandchild in child.findChildren(QWidget):
                    grandchild.setAutoFillBackground(False)
                    if "viewport" in grandchild.objectName().lower():
                        grandchild.setStyleSheet("background-color: #282828; border: none;")
                
            # 设置容器小部件的样式
            parent = widget.parentWidget()
            if parent:
                parent.setAutoFillBackground(False)
                parent.setStyleSheet("background-color: #282828; border: none;")
                
                # 查找并处理QComboBoxPrivateContainer
                container = parent.findChild(QWidget, "QComboBoxPrivateContainer")
                if container:
                    container.setAutoFillBackground(False)
                    container.setStyleSheet("background-color: #282828; border: none;")
                    
                    # 处理容器的所有子控件
                    for child in container.findChildren(QWidget):
                        child.setAutoFillBackground(False)
                        child.setStyleSheet("background-color: #282828; border: none;")
        except Exception as e:
            print(f"应用额外下拉框修复失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def update_ui_texts(self):
        """更新UI文本"""
        # 更新设置标题
        if hasattr(self, 'title_label') and self.title_label:
            self.title_label.setText(self.language_manager.get_text("settings.title", "设置"))
        
        # 更新语言设置部分
        if hasattr(self, 'lang_title') and self.lang_title:
            self.lang_title.setText(self.language_manager.get_text("settings.language.title", "语言设置"))
            
        if hasattr(self, 'lang_desc') and self.lang_desc:
            self.lang_desc.setText(self.language_manager.get_text("settings.language.label", "选择应用界面语言"))
            
        if hasattr(self, 'language_combo') and self.language_combo:
            current_index = self.language_combo.currentIndex()
            self.language_combo.clear()
            self.language_combo.addItem(self.language_manager.get_text("settings.language.zh_CN", "中文"), "zh_CN")
            self.language_combo.addItem(self.language_manager.get_text("settings.language.en_US", "English"), "en_US")
            self.language_combo.setCurrentIndex(current_index)
        
        # 更新导出格式部分
        if hasattr(self, 'export_title') and self.export_title:
            self.export_title.setText(self.language_manager.get_text("settings.export.title", "导出设置"))
            
        if hasattr(self, 'export_desc') and self.export_desc:
            self.export_desc.setText(self.language_manager.get_text("settings.export.desc", "设置歌曲导出的默认格式和文件类型"))
            
        if hasattr(self, 'format_label') and self.format_label:
            self.format_label.setText(self.language_manager.get_text("settings.export.format_label", "导出格式:"))
            
        if hasattr(self, 'export_format_combo') and self.export_format_combo:
            current_format = self.settings.value("export_format", "name-artists")
            self.export_format_combo.blockSignals(True)
            self.export_format_combo.setItemText(0, self.language_manager.get_text('playlist.format_name_artist', '歌名-歌手'))
            self.export_format_combo.setItemText(1, self.language_manager.get_text('playlist.format_artist_name', '歌手-歌名'))
            self.export_format_combo.setItemText(2, self.language_manager.get_text('playlist.format_name_artist_album', '歌名-歌手-专辑'))
            
            index = self.export_format_combo.findData(current_format)
            if index >= 0:
                self.export_format_combo.setCurrentIndex(index)
            self.export_format_combo.blockSignals(False)
        
        if hasattr(self, 'file_format_label') and self.file_format_label:
            self.file_format_label.setText(self.language_manager.get_text("settings.export.file_format_label", "文件格式:"))
        
        if hasattr(self, 'txt_radio') and self.txt_radio:
            self.txt_radio.setText(self.language_manager.get_text("settings.export.txt_format", "文本文件 (.txt)"))
        
        if hasattr(self, 'csv_radio') and self.csv_radio:
            self.csv_radio.setText(self.language_manager.get_text("settings.export.csv_format", "CSV文件 (.csv)"))
        
        if hasattr(self, 'json_radio') and self.json_radio:
            self.json_radio.setText(self.language_manager.get_text("settings.export.json_format", "JSON文件 (.json)"))
        
        # 更新缓存部分
        if hasattr(self, 'cache_title') and self.cache_title:
            self.cache_title.setText(self.language_manager.get_text("settings.cache.title"))
        
        if hasattr(self, 'cache_desc') and self.cache_desc:
            self.cache_desc.setText(self.language_manager.get_text("settings.cache.desc"))
        
        if hasattr(self, 'cache_size_label') and self.cache_size_label:
            total_size = self.get_cache_size()
            size_str = self.format_size(total_size)
            self.cache_size_label.setText(self.language_manager.get_text("settings.cache.size").format(size_str))
        
        if hasattr(self, 'clear_cache_btn') and self.clear_cache_btn:
            self.clear_cache_btn.setText(self.language_manager.get_text("settings.cache.clear_btn"))
        
        # 更新日志部分
        if hasattr(self, 'log_title') and self.log_title:
            self.log_title.setText(self.language_manager.get_text("settings.log.title", "日志设置"))
        
        if hasattr(self, 'log_desc') and self.log_desc:
            self.log_desc.setText(self.language_manager.get_text("settings.log.desc", "设置日志记录的详细程度和查看日志文件"))
        
        if hasattr(self, 'log_level_label') and self.log_level_label:
            self.log_level_label.setText(self.language_manager.get_text("settings.log.level_label", "日志级别:"))
        
        if hasattr(self, 'log_level_combo') and self.log_level_combo:
            current_level = settings.get_setting("log_level", "info")
            self.log_level_combo.blockSignals(True)
            self.log_level_combo.setItemText(0, self.language_manager.get_text("settings.log.level.debug", "调试"))
            self.log_level_combo.setItemText(1, self.language_manager.get_text("settings.log.level.info", "信息"))
            self.log_level_combo.setItemText(2, self.language_manager.get_text("settings.log.level.warning", "警告"))
            self.log_level_combo.setItemText(3, self.language_manager.get_text("settings.log.level.error", "错误"))
            
            index = self.log_level_combo.findData(current_level)
            if index >= 0:
                self.log_level_combo.setCurrentIndex(index)
            self.log_level_combo.blockSignals(False)
        
        if hasattr(self, 'view_log_btn') and self.view_log_btn:
            self.view_log_btn.setText(self.language_manager.get_text("settings.log.view_btn", "查看日志"))
        
        # 更新版本信息部分
        if hasattr(self, 'version_title') and self.version_title:
            self.version_title.setText(self.language_manager.get_text("settings.version.title", "版本信息"))
        
        if hasattr(self, 'version_desc') and self.version_desc:
            self.version_desc.setText(self.language_manager.get_text("settings.version.desc", "查看应用程序版本信息"))
        
        if hasattr(self, 'version_label') and self.version_label:
            current_version = version_module.get_version()
            self.version_label.setText(f"v{current_version}")
    
    def on_language_changed(self, index):
        """语言选择改变时的处理函数"""
        # 阻止信号触发，避免重复调用
        self.language_combo.blockSignals(True)
        
        try:
            language_code = self.language_combo.itemData(index)
            if language_code:
                self.change_language(language_code)
        finally:
            # 恢复信号
            self.language_combo.blockSignals(False)
    
    def change_language(self, language):
        """切换语言"""
        # 检查语言是否真的发生了变化
        if language != self.language_manager.current_language:
            # 保存到user_settings.json
            try:
                settings.set_setting("language", language)
            except Exception as e:
                logger.error(f"保存语言设置到user_settings.json失败: {str(e)}")
            
            # 保存到QSettings
            self.settings.setValue("language", language)
            self.settings.sync()
            
            # 切换语言
            self.language_manager.set_language(language)
            
            # 更新UI文本
            self.update_ui_texts()
    
    def get_cache_size(self):
        """获取缓存大小"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(self.cache_manager.cache_dir):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    total_size += os.path.getsize(fp)
        except Exception as e:
            print(f"计算缓存大小失败: {str(e)}")
        return total_size
    
    def format_size(self, size):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def clear_cache(self):
        """清除缓存"""
        try:
            # 创建自定义样式的消息框
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle(self.language_manager.get_text("settings.cache.confirm"))
            msg_box.setText(self.language_manager.get_text("settings.cache.confirm_msg"))
            msg_box.setIcon(QMessageBox.Question)
            
            # 设置自定义样式表
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: #040404;
                    color: white;
                    border: 1px solid #282828;
                }
                QMessageBox QLabel {
                    color: #b3b3b3;
                    font-size: 14px;
                }
                QMessageBox QPushButton {
                    background-color: #1DB954;
                    color: white;
                    min-width: 80px;
                    padding: 5px;
                    border-radius: 4px;
                    border: none;
                }
                QMessageBox QPushButton:hover {
                    background-color: #1ED760;
                }
                QMessageBox QPushButton:pressed {
                    background-color: #169B42;
                }
                QMessageBox QFrame {
                    background-color: #040404;
                    border: none;
                }
            """)
            
            # 添加按钮
            yes_btn = msg_box.addButton(self.language_manager.get_text("common.yes"), QMessageBox.YesRole)
            no_btn = msg_box.addButton(self.language_manager.get_text("common.no"), QMessageBox.NoRole)
            
            # 显示消息框并等待用户响应
            msg_box.exec_()
            
            if msg_box.clickedButton() == yes_btn:
                self.cache_manager.clear_all_cache()
                
                # 成功消息框
                success_box = QMessageBox(self)
                success_box.setWindowTitle(self.language_manager.get_text("common.success"))
                success_box.setText(self.language_manager.get_text("settings.cache.success"))
                success_box.setIcon(QMessageBox.Information)
                success_box.setStyleSheet("""
                    QMessageBox {
                        background-color: #040404;
                        color: white;
                        border: 1px solid #282828;
                    }
                    QMessageBox QLabel {
                        color: #b3b3b3;
                        font-size: 14px;
                    }
                    QMessageBox QPushButton {
                        background-color: #1DB954;
                        color: white;
                        min-width: 80px;
                        padding: 5px;
                        border-radius: 4px;
                        border: none;
                    }
                    QMessageBox QFrame {
                        background-color: #040404;
                        border: none;
                    }
                """)
                success_box.exec_()
                
                # 刷新缓存大小显示
                total_size = self.get_cache_size()
                size_str = self.format_size(total_size)
                self.cache_size_label.setText(self.language_manager.get_text("settings.cache.size").format(size_str))
        except Exception as e:
            # 错误消息框
            error_box = QMessageBox(self)
            error_box.setWindowTitle(self.language_manager.get_text("common.error"))
            error_box.setText(self.language_manager.get_text("settings.cache.error").format(str(e)))
            error_box.setIcon(QMessageBox.Critical)
            error_box.setStyleSheet("""
                QMessageBox {
                    background-color: #040404;
                    color: white;
                    border: 1px solid #282828;
                }
                QMessageBox QLabel {
                    color: #b3b3b3;
                    font-size: 14px;
                }
                QMessageBox QPushButton {
                    background-color: #E91429;
                    color: white;
                    min-width: 80px;
                    padding: 5px;
                    border-radius: 4px;
                    border: none;
                }
                QMessageBox QFrame {
                    background-color: #040404;
                    border: none;
                }
            """)
            error_box.exec_()
    
    def on_export_format_changed(self, index):
        """处理导出格式变更"""
        format_key = self.export_format_combo.itemData(index)
        if format_key:
            # 保存设置到QSettings
            self.settings.setValue("export_format", format_key)
            self.settings.sync() # 确保设置立即写入
            logger.debug(f"导出格式设置已同步到QSettings: export_format = {format_key}")
            
            # 同时保存到user_settings.json
            try:
                settings.set_setting("export_format", format_key)
                logger.debug(f"导出格式设置已同步到user_settings.json: export_format = {format_key}")
            except Exception as e:
                logger.error(f"保存导出格式到user_settings.json失败: {str(e)}")
    
    def on_file_format_changed(self, button):
        """处理文件格式变更"""
        # 确定选择的文件格式
        if button == self.txt_radio:
            file_format = "txt"
        elif button == self.csv_radio:
            file_format = "csv"
        elif button == self.json_radio:
            file_format = "json"
        else:
            file_format = "txt"  # 默认值
        
        # 保存设置到QSettings（保留旧的布尔值方式以保持兼容性，仅对txt和csv有效）
        if file_format == "txt":
            self.settings.setValue("export_use_txt", "true")
        elif file_format == "csv":
            self.settings.setValue("export_use_txt", "false")
            
        # 同时保存新的文件格式设置
        self.settings.setValue("export_file_format", file_format)
        self.settings.sync() # 确保设置立即写入
        logger.debug(f"文件格式设置已同步到QSettings: export_file_format = {file_format}")
        
        # 同时保存到user_settings.json
        try:
            # 保存新的设置
            settings.set_setting("export_file_format", file_format)
            logger.debug(f"文件格式设置已同步到user_settings.json: export_file_format = {file_format}")
        except Exception as e:
            logger.error(f"保存文件格式到user_settings.json失败: {str(e)}")
    
    def on_log_level_changed(self, index):
        """处理日志级别变更"""
        log_level = self.log_level_combo.itemData(index)
        if log_level:
            try:
                logger.info(f"设置日志级别为: {log_level}")
                # 保存设置到user_settings.json
                settings.set_setting("log_level", log_level)
                # 同时也保存到QSettings以保持兼容性
                qt_settings = QSettings()
                qt_settings.setValue("log/level", log_level)
                # 动态切换日志级别
                set_log_level(log_level)
                logger.info(f"日志级别已更新为: {log_level}")
            except Exception as e:
                logger.error(f"设置日志级别失败: {str(e)}")
                QMessageBox.warning(
                    self,
                    self.language_manager.get_text("common.error", "错误"),
                    self.language_manager.get_text("settings.log.level_error", "设置日志级别失败: {0}").format(str(e))
                )
    
    def view_log(self):
        """打开日志文件"""
        try:
            logger.info("用户请求查看日志文件")
            import platform
            import subprocess
            
            log_path = logger.get_log_path()
            
            if not os.path.exists(log_path):
                QMessageBox.information(
                    self,
                    self.language_manager.get_text("common.info", "提示"),
                    self.language_manager.get_text("settings.log.not_found", "日志文件不存在")
                )
                return
                
            logger.info(f"打开日志文件: {log_path}")
            
            # 根据操作系统使用不同的方式打开文件
            system = platform.system()
            if system == "Darwin":  # macOS
                subprocess.call(["open", log_path])
            elif system == "Windows":
                os.startfile(log_path)
            else:  # Linux
                subprocess.call(["xdg-open", log_path])
                
        except Exception as e:
            logger.error(f"打开日志文件失败: {str(e)}")
            QMessageBox.warning(
                self,
                self.language_manager.get_text("common.error", "错误"),
                self.language_manager.get_text("settings.log.open_error", "打开日志文件失败: {0}").format(str(e))
            )