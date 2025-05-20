"""
设置页面视图
"""
from PyQt5.QtWidgets import (QWidget, QLabel, QPushButton, QVBoxLayout, 
                           QHBoxLayout, QFrame, QMessageBox, QComboBox, QRadioButton, QButtonGroup)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from utils.cache_manager import CacheManager
from utils.language_manager import LanguageManager
from utils.logger import logger
import os
from PyQt5.QtCore import QSettings, QEvent
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

class SettingsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cache_manager = CacheManager()
        self.language_manager = LanguageManager()
        
        # 存储UI元素的引用
        self.title_label = None
        self.lang_title = None
        self.lang_desc = None
        self.language_combo = None
        self.cache_title = None
        self.cache_desc = None
        self.cache_size_label = None
        self.clear_cache_btn = None
        self.export_title = None
        self.export_desc = None
        self.export_format_combo = None
        self.txt_radio = None
        self.csv_radio = None
        self.file_format_group = None
        self.file_format_label = None
        self.format_label = None
        
        # 日志设置相关元素
        self.log_title = None
        self.log_desc = None
        self.log_level_label = None
        self.log_level_combo = None
        self.view_log_btn = None
        
        # 连接语言变更信号
        self.language_manager.language_changed.connect(self.update_ui_texts)
        
        # 初始化UI
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        # 设置背景颜色
        self.setStyleSheet("background-color: #040404;")
        
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(30)
        
        # 设置标题
        self.title_label = QLabel(self.language_manager.get_text("settings.title"))
        self.title_label.setFont(QFont("PingFang SC", 24, QFont.Bold))
        self.title_label.setStyleSheet("color: white;")
        main_layout.addWidget(self.title_label)
        
        # ====== 语言设置部分 ======
        language_container = QWidget()
        language_layout = QHBoxLayout(language_container)
        language_layout.setContentsMargins(0, 10, 0, 10)
        language_layout.setSpacing(0)
        
        # 左侧文本区域
        lang_text_area = QWidget()
        lang_text_layout = QVBoxLayout(lang_text_area)
        lang_text_layout.setContentsMargins(0, 0, 0, 0)
        lang_text_layout.setSpacing(5)
        lang_text_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        # 语言设置标题
        self.lang_title = QLabel(self.language_manager.get_text("settings.language.title"))
        self.lang_title.setFont(QFont("PingFang SC", 16, QFont.Bold))
        self.lang_title.setStyleSheet("color: white;")
        lang_text_layout.addWidget(self.lang_title)
        
        # 语言设置描述
        self.lang_desc = QLabel(self.language_manager.get_text("settings.language.label"))
        self.lang_desc.setStyleSheet("color: #b3b3b3; font-size: 13px;")
        self.lang_desc.setWordWrap(True)
        lang_text_layout.addWidget(self.lang_desc)
        
        language_layout.addWidget(lang_text_area, 1)  # 左侧占更多空间
        
        # 右侧控制区域
        lang_control_area = QWidget()
        lang_control_layout = QHBoxLayout(lang_control_area)
        lang_control_layout.setContentsMargins(20, 0, 0, 0)
        lang_control_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        # 语言下拉选择框
        self.language_combo = QComboBox()
        self.language_combo.addItem(self.language_manager.get_text("settings.language.zh_CN"), "zh_CN")
        self.language_combo.addItem(self.language_manager.get_text("settings.language.en_US"), "en_US")
        self.language_combo.setMinimumWidth(250)
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
            QComboBox:hover {
                background-color: #333333;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
                subcontrol-origin: padding;
                subcontrol-position: right center;
            }
            QComboBox::down-arrow {
                image: none;
                width: 0;
            }
            QComboBox QAbstractItemView {
                background-color: #282828;
                color: white;
                selection-background-color: #1DB954;
                selection-color: white;
                border: none;
                padding: 0px;
                margin: 0px;
                outline: none;
                border-radius: 4px;
                margin-top: -1px;  /* 去除顶部间隙 */
                /* 强制样式覆盖Qt默认行为 */
                border-top: 0px solid transparent;
                border-bottom: 0px solid transparent;
            }
            /* 使用QListView的样式更精确地控制下拉列表 */
            QComboBox QListView {
                background-color: #282828;
                outline: none;
                padding: 0px;
                margin: 0px;
            }
            QComboBox QListView::item {
                min-height: 30px;
                height: 30px;
                padding: 5px 15px;
                margin: 0px;
                border: none;
                color: white;
            }
            QComboBox QListView::item:selected {
                background-color: #1DB954;
                color: white;
            }
            QComboBox QListView::item:hover {
                background-color: #333333;
            }
            QComboBox QListView QScrollBar:vertical {
                width: 8px;
                background: #282828;
                border: none;
                margin: 0px;
            }
            QComboBox QListView QScrollBar::handle:vertical {
                background: #535353;
                min-height: 20px;
                border-radius: 4px;
            }
            QComboBox QListView QScrollBar::add-line:vertical, 
            QComboBox QListView QScrollBar::sub-line:vertical {
                height: 0px;
                border: none;
                background: none;
            }
            QComboBox QListView QScrollBar::add-page:vertical,
            QComboBox QListView QScrollBar::sub-page:vertical {
                background: none;
                height: 0px;
                width: 0px;
            }
        """)
        
        # 连接信号
        self.language_combo.currentIndexChanged.connect(self.on_language_changed)
        
        # 设置当前语言
        current_lang = self.language_manager.current_language
        index = self.language_combo.findData(current_lang)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)
        
        lang_control_layout.addWidget(self.language_combo)
        language_layout.addWidget(lang_control_area)
        
        # 添加到主布局
        main_layout.addWidget(language_container)
        
        # ====== 导出格式设置部分 ======
        self.settings = QSettings("Spotify", "SpotifyExport")
        
        export_container = QWidget()
        export_layout = QHBoxLayout(export_container)
        export_layout.setContentsMargins(0, 10, 0, 10)
        export_layout.setSpacing(0)
        
        # 左侧文本区域
        export_text_area = QWidget()
        export_text_layout = QVBoxLayout(export_text_area)
        export_text_layout.setContentsMargins(0, 0, 0, 0)
        export_text_layout.setSpacing(5)
        export_text_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        # 导出格式设置标题
        self.export_title = QLabel(self.language_manager.get_text("settings.export.title", "导出设置"))
        self.export_title.setFont(QFont("PingFang SC", 16, QFont.Bold))
        self.export_title.setStyleSheet("color: white;")
        export_text_layout.addWidget(self.export_title)
        
        # 导出格式设置描述
        self.export_desc = QLabel(self.language_manager.get_text("settings.export.desc", "设置歌曲导出的默认格式和文件类型"))
        self.export_desc.setStyleSheet("color: #b3b3b3; font-size: 13px;")
        self.export_desc.setWordWrap(True)
        export_text_layout.addWidget(self.export_desc)
        
        export_layout.addWidget(export_text_area, 1)  # 左侧占更多空间
        
        # 右侧控制区域
        export_control_area = QWidget()
        export_control_layout = QVBoxLayout(export_control_area)
        export_control_layout.setContentsMargins(20, 0, 0, 0)
        export_control_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        # 格式选择标签
        format_label = QLabel(self.language_manager.get_text("settings.export.format_label", "导出格式:"))
        format_label.setStyleSheet("color: white; font-size: 14px;")
        format_label.setObjectName("format_label")  # 设置objectName
        self.format_label = format_label  # 保存为类成员变量
        
        # 格式选择下拉框
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
            QComboBox:hover {
                background-color: #333333;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
                subcontrol-origin: padding;
                subcontrol-position: right center;
            }
            QComboBox::down-arrow {
                image: none;
                width: 0;
            }
            QComboBox QAbstractItemView {
                background-color: #282828;
                color: white;
                selection-background-color: #1DB954;
                selection-color: white;
                border: none;
                padding: 0px;
                margin: 0px;
                outline: none;
                border-radius: 4px;
                margin-top: -1px;  /* 去除顶部间隙 */
                /* 强制样式覆盖Qt默认行为 */
                border-top: 0px solid transparent;
                border-bottom: 0px solid transparent;
            }
            /* 使用QListView的样式更精确地控制下拉列表 */
            QComboBox QListView {
                background-color: #282828;
                outline: none;
                padding: 0px;
                margin: 0px;
            }
            QComboBox QListView::item {
                min-height: 30px;
                height: 30px;
                padding: 5px 15px;
                margin: 0px;
                border: none;
                color: white;
            }
            QComboBox QListView::item:selected {
                background-color: #1DB954;
                color: white;
            }
            QComboBox QListView::item:hover {
                background-color: #333333;
            }
            QComboBox QListView QScrollBar:vertical {
                width: 8px;
                background: #282828;
                border: none;
                margin: 0px;
            }
            QComboBox QListView QScrollBar::handle:vertical {
                background: #535353;
                min-height: 20px;
                border-radius: 4px;
            }
            QComboBox QListView QScrollBar::add-line:vertical, 
            QComboBox QListView QScrollBar::sub-line:vertical {
                height: 0px;
                border: none;
                background: none;
            }
            QComboBox QListView QScrollBar::add-page:vertical,
            QComboBox QListView QScrollBar::sub-page:vertical {
                background: none;
                height: 0px;
                width: 0px;
            }
        """)
        
        # 获取当前格式设置，如果是自定义格式，改为默认格式
        current_format = self.settings.value("export_format", "name-artists")
        if current_format == "custom":
            current_format = "name-artists"
            self.settings.setValue("export_format", current_format)
            
        index = self.export_format_combo.findData(current_format)
        if index >= 0:
            self.export_format_combo.setCurrentIndex(index)
        
        # 连接信号
        self.export_format_combo.currentIndexChanged.connect(self.on_export_format_changed)
        
        # 添加文件格式选择
        file_format_label = QLabel(self.language_manager.get_text("settings.export.file_format_label", "文件格式:"))
        file_format_label.setStyleSheet("color: white; font-size: 14px; margin-top: 15px;")
        file_format_label.setObjectName("file_format_label")  # 设置objectName以便后续查找
        self.file_format_label = file_format_label  # 保存为类成员变量
        
        # 创建两个单选按钮
        file_format_container = QWidget()
        file_format_layout = QHBoxLayout(file_format_container)
        file_format_layout.setContentsMargins(0, 0, 0, 0)
        file_format_layout.setSpacing(20)
        
        self.txt_radio = QRadioButton(self.language_manager.get_text("settings.export.txt_format", "文本文件 (.txt)"))
        self.txt_radio.setStyleSheet("color: white; font-size: 14px;")
        
        self.csv_radio = QRadioButton(self.language_manager.get_text("settings.export.csv_format", "CSV文件 (.csv)"))
        self.csv_radio.setStyleSheet("color: white; font-size: 14px;")
        
        # 创建按钮组
        self.file_format_group = QButtonGroup(self)
        self.file_format_group.addButton(self.txt_radio, 1)
        self.file_format_group.addButton(self.csv_radio, 2)
        
        # 默认选择TXT
        use_txt = self.settings.value("export_use_txt", "true") == "true"
        if use_txt:
            self.txt_radio.setChecked(True)
        else:
            self.csv_radio.setChecked(True)
        
        # 连接信号
        self.file_format_group.buttonClicked.connect(self.on_file_format_changed)
        
        file_format_layout.addWidget(self.txt_radio)
        file_format_layout.addWidget(self.csv_radio)
        file_format_layout.addStretch()
        
        # 添加组件到布局
        format_container = QWidget()
        format_layout = QHBoxLayout(format_container)
        format_layout.setContentsMargins(0, 0, 0, 0)
        format_layout.addWidget(format_label)
        format_layout.addWidget(self.export_format_combo)
        
        export_control_layout.addWidget(format_container)
        export_control_layout.addWidget(file_format_label)
        export_control_layout.addWidget(file_format_container)
        
        export_layout.addWidget(export_control_area)
        
        # 添加到主布局
        main_layout.addWidget(export_container)
        
        # ====== 缓存设置部分 ======
        cache_container = QWidget()
        cache_layout = QHBoxLayout(cache_container)
        cache_layout.setContentsMargins(0, 10, 0, 10)
        cache_layout.setSpacing(0)
        
        # 左侧文本区域
        cache_text_area = QWidget()
        cache_text_layout = QVBoxLayout(cache_text_area)
        cache_text_layout.setContentsMargins(0, 0, 0, 0)
        cache_text_layout.setSpacing(5)
        cache_text_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        # 缓存标题
        self.cache_title = QLabel(self.language_manager.get_text("settings.cache.title"))
        self.cache_title.setFont(QFont("PingFang SC", 16, QFont.Bold))
        self.cache_title.setStyleSheet("color: white;")
        cache_text_layout.addWidget(self.cache_title)
        
        # 缓存描述
        self.cache_desc = QLabel(self.language_manager.get_text("settings.cache.desc"))
        self.cache_desc.setStyleSheet("color: #b3b3b3; font-size: 13px;")
        self.cache_desc.setWordWrap(True)
        cache_text_layout.addWidget(self.cache_desc)
        
        # 缓存信息
        total_size = self.get_cache_size()
        size_str = self.format_size(total_size)
        self.cache_size_label = QLabel(self.language_manager.get_text("settings.cache.size").format(size_str))
        self.cache_size_label.setStyleSheet("color: #b3b3b3; font-size: 13px; margin-top: 10px;")
        cache_text_layout.addWidget(self.cache_size_label)
        
        cache_layout.addWidget(cache_text_area, 1)  # 左侧占更多空间
        
        # 右侧控制区域
        cache_control_area = QWidget()
        cache_control_layout = QHBoxLayout(cache_control_area)
        cache_control_layout.setContentsMargins(20, 0, 0, 0)
        cache_control_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
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
        self.clear_cache_btn.clicked.connect(self.clear_cache)
        
        cache_control_layout.addWidget(self.clear_cache_btn)
        cache_layout.addWidget(cache_control_area)
        
        # 添加到主布局
        main_layout.addWidget(cache_container)
        
        # ===== 日志设置部分 =====
        log_container = QWidget()
        log_layout = QHBoxLayout(log_container)
        log_layout.setContentsMargins(0, 10, 0, 10)
        log_layout.setSpacing(0)
        
        # 左侧文本区域
        log_text_area = QWidget()
        log_text_layout = QVBoxLayout(log_text_area)
        log_text_layout.setContentsMargins(0, 0, 0, 0)
        log_text_layout.setSpacing(5)
        log_text_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        # 日志设置标题
        self.log_title = QLabel(self.language_manager.get_text("settings.log.title", "日志设置"))
        self.log_title.setFont(QFont("PingFang SC", 16, QFont.Bold))
        self.log_title.setStyleSheet("color: white;")
        log_text_layout.addWidget(self.log_title)
        
        # 日志设置描述
        self.log_desc = QLabel(self.language_manager.get_text("settings.log.desc", "设置日志记录的详细程度和查看日志文件"))
        self.log_desc.setStyleSheet("color: #b3b3b3; font-size: 13px;")
        self.log_desc.setWordWrap(True)
        log_text_layout.addWidget(self.log_desc)
        
        log_layout.addWidget(log_text_area, 1)  # 左侧占更多空间
        
        # 右侧控制区域
        log_control_area = QWidget()
        log_control_layout = QVBoxLayout(log_control_area)
        log_control_layout.setContentsMargins(20, 0, 0, 0)
        log_control_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        # 日志级别设置
        log_level_container = QWidget()
        log_level_layout = QHBoxLayout(log_level_container)
        log_level_layout.setContentsMargins(0, 0, 0, 0)
        
        # 日志级别标签
        self.log_level_label = QLabel(self.language_manager.get_text("settings.log.level", "日志级别:"))
        self.log_level_label.setStyleSheet("color: white; font-size: 14px;")
        log_level_layout.addWidget(self.log_level_label)
        
        # 日志级别下拉框
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItem(self.language_manager.get_text("settings.log.level.debug", "调试"), "debug")
        self.log_level_combo.addItem(self.language_manager.get_text("settings.log.level.info", "信息"), "info")
        self.log_level_combo.addItem(self.language_manager.get_text("settings.log.level.warning", "警告"), "warning")
        self.log_level_combo.addItem(self.language_manager.get_text("settings.log.level.error", "错误"), "error")
        self.log_level_combo.setMinimumWidth(150)
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
            QComboBox:hover {
                background-color: #333333;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
                subcontrol-origin: padding;
                subcontrol-position: right center;
            }
            QComboBox::down-arrow {
                image: none;
                width: 0;
            }
            QComboBox QAbstractItemView {
                background-color: #282828;
                color: white;
                selection-background-color: #1DB954;
                selection-color: white;
                border: none;
                padding: 0px;
                margin: 0px;
                outline: none;
                border-radius: 4px;
                margin-top: -1px;  /* 去除顶部间隙 */
                /* 强制样式覆盖Qt默认行为 */
                border-top: 0px solid transparent;
                border-bottom: 0px solid transparent;
            }
            /* 使用QListView的样式更精确地控制下拉列表 */
            QComboBox QListView {
                background-color: #282828;
                outline: none;
                padding: 0px;
                margin: 0px;
            }
            QComboBox QListView::item {
                min-height: 30px;
                height: 30px;
                padding: 5px 15px;
                margin: 0px;
                border: none;
                color: white;
            }
            QComboBox QListView::item:selected {
                background-color: #1DB954;
                color: white;
            }
            QComboBox QListView::item:hover {
                background-color: #333333;
            }
            QComboBox QListView QScrollBar:vertical {
                width: 8px;
                background: #282828;
                border: none;
                margin: 0px;
            }
            QComboBox QListView QScrollBar::handle:vertical {
                background: #535353;
                min-height: 20px;
                border-radius: 4px;
            }
            QComboBox QListView QScrollBar::add-line:vertical, 
            QComboBox QListView QScrollBar::sub-line:vertical {
                height: 0px;
                border: none;
                background: none;
            }
            QComboBox QListView QScrollBar::add-page:vertical,
            QComboBox QListView QScrollBar::sub-page:vertical {
                background: none;
                height: 0px;
                width: 0px;
            }
        """)
        
        # 连接信号
        self.log_level_combo.currentIndexChanged.connect(self.on_log_level_changed)
        
        # 设置当前日志级别
        settings = QSettings()
        current_log_level = settings.value("log/level", "info")
        index = self.log_level_combo.findData(current_log_level)
        if index >= 0:
            self.log_level_combo.setCurrentIndex(index)
            
        log_level_layout.addWidget(self.log_level_combo)
        
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
        self.view_log_btn.clicked.connect(self.view_log)
        
        # 添加各组件到布局
        log_control_layout.addWidget(log_level_container)
        log_control_layout.addWidget(self.view_log_btn, 0, Qt.AlignRight)
        
        log_layout.addWidget(log_control_area)
        
        # 添加到主布局
        main_layout.addWidget(log_container)
        
        # 添加底部空间
        main_layout.addStretch()
        
        # 应用特殊设置确保下拉框没有空白
        self._apply_combo_box_fixes()
    
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
            for combo_box in [self.language_combo, self.export_format_combo]:
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
        if event.type() == QEvent.Show and (obj == self.language_combo or obj == self.export_format_combo):
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
        """更新UI文本，但不重新创建UI"""
        try:
            # 更新标题文本
            self.title_label.setText(self.language_manager.get_text("settings.title"))
            
            # 更新语言部分文本
            self.lang_title.setText(self.language_manager.get_text("settings.language.title"))
            self.lang_desc.setText(self.language_manager.get_text("settings.language.label"))
            
            # 更新下拉框选项文本
            self.language_combo.blockSignals(True)
            self.language_combo.setItemText(0, self.language_manager.get_text("settings.language.zh_CN"))
            self.language_combo.setItemText(1, self.language_manager.get_text("settings.language.en_US"))
            
            # 更新下拉框选中项，阻止信号触发
            current_lang = self.language_manager.current_language
            index = self.language_combo.findData(current_lang)
            if index >= 0:
                self.language_combo.setCurrentIndex(index)
            self.language_combo.blockSignals(False)
            
            # 更新导出格式部分文本
            self.export_title.setText(self.language_manager.get_text("settings.export.title", "导出设置"))
            self.export_desc.setText(self.language_manager.get_text("settings.export.desc", "设置歌曲导出的默认格式和文件类型"))
            
            # 更新格式标签文本
            if hasattr(self, 'format_label') and self.format_label:
                self.format_label.setText(self.language_manager.get_text("settings.export.format_label", "导出格式:"))
            
            # 更新导出格式下拉框的选项文本
            self.export_format_combo.blockSignals(True)
            self.export_format_combo.setItemText(0, self.language_manager.get_text('playlist.format_name_artist', '歌名-歌手'))
            self.export_format_combo.setItemText(1, self.language_manager.get_text('playlist.format_artist_name', '歌手-歌名'))
            self.export_format_combo.setItemText(2, self.language_manager.get_text('playlist.format_name_artist_album', '歌名-歌手-专辑'))
            
            # 刷新导出格式设置
            current_format = self.settings.value("export_format", "name-artists")
            # 如果之前是自定义格式，改为默认格式
            if current_format == "custom":
                current_format = "name-artists"
                self.settings.setValue("export_format", current_format)
                
            index = self.export_format_combo.findData(current_format)
            if index >= 0:
                self.export_format_combo.setCurrentIndex(index)
            self.export_format_combo.blockSignals(False)
            
            # 更新文件格式标签文本
            if hasattr(self, 'file_format_label') and self.file_format_label:
                self.file_format_label.setText(self.language_manager.get_text("settings.export.file_format_label", "文件格式:"))
            
            # 更新文件格式选择按钮文本
            self.txt_radio.setText(self.language_manager.get_text("settings.export.txt_format", "文本文件 (.txt)"))
            self.csv_radio.setText(self.language_manager.get_text("settings.export.csv_format", "CSV文件 (.csv)"))
            
            # 更新缓存部分文本
            self.cache_title.setText(self.language_manager.get_text("settings.cache.title"))
            self.cache_desc.setText(self.language_manager.get_text("settings.cache.desc"))
            
            # 刷新缓存大小
            total_size = self.get_cache_size()
            size_str = self.format_size(total_size)
            self.cache_size_label.setText(self.language_manager.get_text("settings.cache.size").format(size_str))
            
            # 更新按钮文本
            self.clear_cache_btn.setText(self.language_manager.get_text("settings.cache.clear_btn"))
            
            # 更新日志部分文本
            if hasattr(self, 'log_title') and self.log_title:
                self.log_title.setText(self.language_manager.get_text("settings.log.title", "日志设置"))
                
            if hasattr(self, 'log_desc') and self.log_desc:
                self.log_desc.setText(self.language_manager.get_text("settings.log.desc", "设置日志记录的详细程度和查看日志文件"))
                
            if hasattr(self, 'log_level_label') and self.log_level_label:
                self.log_level_label.setText(self.language_manager.get_text("settings.log.level", "日志级别:"))
                
            if hasattr(self, 'log_level_combo') and self.log_level_combo:
                self.log_level_combo.blockSignals(True)
                self.log_level_combo.setItemText(0, self.language_manager.get_text("settings.log.level.debug", "调试"))
                self.log_level_combo.setItemText(1, self.language_manager.get_text("settings.log.level.info", "信息"))
                self.log_level_combo.setItemText(2, self.language_manager.get_text("settings.log.level.warning", "警告"))
                self.log_level_combo.setItemText(3, self.language_manager.get_text("settings.log.level.error", "错误"))
                
                # 恢复当前选项
                current_level = QSettings().value("log/level", "info")
                index = self.log_level_combo.findData(current_level)
                if index >= 0:
                    self.log_level_combo.setCurrentIndex(index)
                self.log_level_combo.blockSignals(False)
                
            if hasattr(self, 'view_log_btn') and self.view_log_btn:
                self.view_log_btn.setText(self.language_manager.get_text("settings.log.view_btn", "查看日志"))
            
        except Exception as e:
            print(f"更新UI文本失败: {str(e)}")
            import traceback
            traceback.print_exc()
            logger.error(f"更新设置页面UI文本失败: {str(e)}")
            logger.error(traceback.format_exc())
    
    def on_language_changed(self, index):
        """语言选择改变时的处理函数"""
        language_code = self.language_combo.itemData(index)
        if language_code:
            self.change_language(language_code)
    
    def change_language(self, language):
        """切换语言"""
        if language != self.language_manager.current_language:
            self.language_manager.set_language(language)
            # 通过信号会触发update_ui_texts方法
    
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
            reply = QMessageBox.question(
                self, 
                self.language_manager.get_text("settings.cache.confirm"), 
                self.language_manager.get_text("settings.cache.confirm_msg"),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.cache_manager.clear_all_cache()
                QMessageBox.information(
                    self, 
                    self.language_manager.get_text("common.success"),
                    self.language_manager.get_text("settings.cache.success")
                )
                # 刷新缓存大小显示
                total_size = self.get_cache_size()
                size_str = self.format_size(total_size)
                self.cache_size_label.setText(self.language_manager.get_text("settings.cache.size").format(size_str))
        except Exception as e:
            QMessageBox.critical(
                self, 
                self.language_manager.get_text("common.error"),
                self.language_manager.get_text("settings.cache.error").format(str(e))
            )
    
    def on_export_format_changed(self, index):
        """处理导出格式变更"""
        format_key = self.export_format_combo.itemData(index)
        if format_key:
            # 保存设置
            self.settings.setValue("export_format", format_key)
    
    def on_file_format_changed(self, button):
        """处理文件格式变更"""
        use_txt = (button == self.txt_radio)
        self.settings.setValue("export_use_txt", "true" if use_txt else "false")
    
    def on_log_level_changed(self, index):
        """处理日志级别变更"""
        log_level = self.log_level_combo.itemData(index)
        if log_level:
            try:
                logger.info(f"设置日志级别为: {log_level}")
                # 保存设置
                settings = QSettings()
                settings.setValue("log/level", log_level)
                
                # 更新日志级别
                if logger.set_level(log_level):
                    logger.info(f"日志级别已更新为: {log_level}")
                else:
                    logger.warning(f"更新日志级别失败: {log_level}")
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