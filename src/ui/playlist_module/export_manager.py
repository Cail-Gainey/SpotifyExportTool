"""
播放列表导出功能模块
处理歌曲导出相关的功能
"""

from PyQt5.QtWidgets import (
    QMessageBox,
    QFileDialog,
    QPushButton,
    QVBoxLayout,
    QLabel,
    QDialog,
    QProgressBar,
)
from PyQt5.QtCore import QSettings
import os
import logging
from datetime import datetime

# 导入文件导出器
from src.exporters import get_file_exporter

# 设置日志
logger = logging.getLogger(__name__)


def create_styled_message_box(parent, icon, title, text):
    """
    创建自定义样式的消息框，确保在深色主题下文字清晰可见
    
    Args:
        parent: 父窗口
        icon: 消息框图标类型 (QMessageBox.Information, QMessageBox.Warning, QMessageBox.Critical)
        title: 标题
        text: 消息内容
        
    Returns:
        QMessageBox: 样式化的消息框对象
    """
    msg_box = QMessageBox(parent)
    msg_box.setIcon(icon)
    msg_box.setWindowTitle(title)
    msg_box.setText(text)
    
    # 设置深色主题样式
    msg_box.setStyleSheet("""
        QMessageBox {
            background-color: #121212;
            color: white;
            border: 1px solid #333333;
        }
        QLabel {
            color: white;
            font-size: 14px;
            background-color: transparent;
        }
        QPushButton {
            background-color: #333333;
            color: white;
            border-radius: 4px;
            padding: 8px 15px;
            font-size: 14px;
            min-width: 80px;
            border: none;
        }
        QPushButton:hover {
            background-color: #444444;
        }
        QPushButton:focus {
            background-color: #1DB954;
            outline: none;
        }
        QMessageBox QLabel#qt_msgbox_label { 
            color: white;
            font-size: 14px;
            min-width: 300px;
            background-color: transparent;
        }
        QMessageBox QLabel#qt_msgboxex_icon_label {
            padding: 5px;
            background-color: transparent;
        }
    """)
    
    return msg_box


def toggle_export_mode(self):
    """切换导出模式"""
    # 切换导出模式状态
    self.export_mode = not self.export_mode

    # 更新UI
    if self.export_mode:
        # 进入导出模式
        self.status_label.setText(
            self.get_text("playlist.select_export", "请选择要导出的歌曲")
        )

        # 显示导出相关按钮
        self.cancel_export_button.show()
        self.select_all_button.show()
        self.clear_selection_button.show()
        

        # 隐藏导出按钮
        self.export_button.hide()

        # 显示确认导出按钮
        if not hasattr(self, "confirm_export_button"):
            self.confirm_export_button = QPushButton(
                self.get_text("common.ok", "确认")
            )
            self.confirm_export_button.setStyleSheet(
                """
                QPushButton {
                    background-color: #1DB954;
                    color: white;
                    border-radius: 16px;
                    padding: 8px 20px;
                    font-weight: bold;
                    font-size: 14px;
                    min-width: 120px;
                    max-width: 200px;
                    text-align: center;
                    white-space: nowrap;
                }
                QPushButton:hover {
                    background-color: #1ED760;
                }
                QPushButton:pressed {
                    background-color: #1aa34a;
                }
            """
            )
            self.confirm_export_button.clicked.connect(self.export_selected)

            # 尝试找到导出按钮所在的容器并添加确认按钮
            if hasattr(self, "button_container") and self.button_container:
                self.button_container.layout().addWidget(self.confirm_export_button)
            elif hasattr(self, "export_button") and self.export_button:
                # 找到导出按钮的父容器
                parent = self.export_button.parent()
                if parent and hasattr(parent, "layout"):
                    parent.layout().addWidget(self.confirm_export_button)
                else:
                    # 如果找不到合适的容器，添加到主布局
                    logger.warning("无法找到合适的按钮容器，添加到主布局")
                    self.layout().addWidget(self.confirm_export_button)
            else:
                # 如果没有找到任何容器，直接添加到当前控件
                logger.warning("无法找到导出按钮或其容器，直接添加到当前控件")
                self.layout().addWidget(self.confirm_export_button)
        else:
            self.confirm_export_button.show()

        # 显示所有歌曲的复选框
        for song_id, song_item in self.song_items.items():
            if hasattr(song_item, "checkbox"):
                song_item.checkbox.show()
    else:
        # 退出导出模式
        count_text = self.get_text("playlist.song_count", "{0} 首歌曲").format(
            len(self.song_items)
        )
        self.status_label.setText(count_text)

        # 隐藏导出相关按钮
        self.cancel_export_button.hide()
        self.select_all_button.hide()
        self.clear_selection_button.hide()
        # 移除全选复选框的隐藏
        # self.select_all_checkbox.hide()
        # self.select_all_container.hide()

        if hasattr(self, "confirm_export_button"):
            self.confirm_export_button.hide()

        # 显示导出按钮
        self.export_button.show()

        # 隐藏所有歌曲的复选框
        for song_id, song_item in self.song_items.items():
            if hasattr(song_item, "checkbox"):
                song_item.checkbox.hide()

        # 清除所有选择
        self.clear_song_selection()


def export_selected(self):
    """导出选中的歌曲"""
    # 如果不在导出模式，进入导出模式
    if not self.export_mode:
        self.toggle_export_mode()
        return

    # 获取选中的歌曲ID
    selected_ids = self.get_selected_song_ids()

    # 如果没有选中歌曲，提示用户
    if not selected_ids:
        msg_box = create_styled_message_box(
            self, 
            QMessageBox.Warning, 
            self.get_text("export.no_songs_selected", "未选择歌曲"),
            self.get_text("export.select_songs_prompt", "请选择要导出的歌曲")
        )
        msg_box.exec_()
        return

    # 获取选中的歌曲数据
    selected_songs = [self.song_items[song_id].song_data for song_id in selected_ids]

    # 显示文件保存对话框
    file_path = self._show_save_file_dialog(self.file_exporter.file_format)
    if not file_path:
        return

    # 创建导出进度对话框
    export_dialog = QDialog(self)
    export_dialog.setWindowTitle(self.get_text("export.progress_title", "导出进度"))
    layout = QVBoxLayout()
    
    status_label = QLabel(self.get_text("export.preparing", "正在准备导出..."))
    progress_bar = QProgressBar()
    progress_bar.setRange(0, 100)
    progress_bar.setValue(0)
    
    layout.addWidget(status_label)
    layout.addWidget(progress_bar)
    
    export_dialog.setLayout(layout)
    export_dialog.setModal(True)
    export_dialog.show()

    # 连接导出器的信号
    def update_progress(progress):
        progress_bar.setValue(progress)
    
    def update_status(status):
        status_label.setText(status)
    
    def on_export_finished(success, error_msg):
        export_dialog.close()
        if success:
            msg_box = create_styled_message_box(
                self, 
                QMessageBox.Information, 
                self.get_text("export.success_title", "导出成功"),
                self.get_text("export.success_message", "歌曲已成功导出到文件：{0}").format(file_path)
            )
        else:
            msg_box = create_styled_message_box(
                self, 
                QMessageBox.Critical, 
                self.get_text("export.error_title", "导出失败"),
                self.get_text("export.error_message", "导出歌曲时发生错误：{0}").format(error_msg)
            )
        
        msg_box.exec_()

    # 连接信号
    self.file_exporter.progress_signal.connect(update_progress)
    self.file_exporter.status_signal.connect(update_status)
    self.file_exporter.finished_signal.connect(on_export_finished)

    # 开始导出
    self.file_exporter.export(
        songs=selected_songs, 
        file_path=file_path, 
        format_type=self.file_exporter.file_format
    )


def _show_save_file_dialog(self, export_format):
    """显示文件保存对话框

    Args:
        export_format: 导出格式

    Returns:
        str: 保存文件路径，如果用户取消则返回空字符串
    """
    try:
        # 格式映射
        format_map = {
            "json": "JSON文件 (*.json)",
            "csv": "CSV文件 (*.csv)",
            "txt": "文本文件 (*.txt)",
        }
        
        # 验证导出格式是否有效
        valid_formats = ["txt", "csv", "json"]
        if export_format not in valid_formats:
            logger.warning(f"无效的导出格式: {export_format}，使用默认值: txt")
            export_format = "txt"
        
        logger.debug(f"文件保存对话框使用格式: {export_format}")

        # 创建默认文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"{self.playlist_name}_{timestamp}.{export_format}"

        # 清理文件名中的非法字符
        default_name = (
            default_name.replace("/", "_")
            .replace("\\", "_")
            .replace(":", "_")
            .replace("*", "_")
            .replace("?", "_")
            .replace('"', "_")
            .replace("<", "_")
            .replace(">", "_")
            .replace("|", "_")
        )
        
        logger.debug(f"默认文件名: {default_name}")

        # 显示保存对话框
        options = QFileDialog.Options()
        # 使用系统默认对话框，移除DontUseNativeDialog选项
        
        file_path = ""
        selected_filter = ""
        
        try:
            file_path, selected_filter = QFileDialog.getSaveFileName(
                self,
                self.get_text("playlist.save_file_title", "保存文件"),
                default_name,
                format_map.get(export_format, "All Files (*)"),
                options=options,
            )
        except KeyboardInterrupt:
            logger.warning("文件保存对话框被用户中断")
            return ""
        except Exception as e:
            logger.error(f"显示文件保存对话框时发生错误: {str(e)}")
            return ""
        
        logger.debug(f"用户选择的文件路径: {file_path}, 选择的过滤器: {selected_filter}")

        # 如果用户取消了选择，返回空字符串
        if not file_path:
            logger.info("用户取消了文件保存")
            return ""

        # 确保文件扩展名正确
        # 检查扩展名是否匹配选择的导出格式
        if not file_path.lower().endswith(f".{export_format}"):
            logger.warning(f"文件路径没有正确的扩展名: {file_path}")
            
            # 移除现有的扩展名（如果有）
            base_name, existing_ext = os.path.splitext(file_path)
            
            # 添加正确的扩展名
            file_path = f"{base_name}.{export_format}"
            logger.info(f"已修正文件路径: {file_path}")

        return file_path
    except Exception as e:
        logger.error(f"_show_save_file_dialog函数发生未处理的异常: {str(e)}", exc_info=True)
        return ""


def on_export_finished(self, success, error_msg):
    """
    导出完成后的回调函数
    
    Args:
        success: 是否成功导出
        error_msg: 错误信息（如果有）
    """
    # 隐藏进度对话框
    if hasattr(self, 'progress_dialog'):
        self.progress_dialog.close()
        del self.progress_dialog

    # 根据导出结果显示消息
    if success:
        # 成功导出
        msg_box = create_styled_message_box(
            self, 
            QMessageBox.Information, 
            self.get_text("export.success_title", "导出成功"),
            self.get_text("export.success_message", "歌曲已成功导出")
        )
    else:
        # 导出失败
        msg_box = create_styled_message_box(
            self, 
            QMessageBox.Warning, 
            self.get_text("export.failed_title", "导出失败"),
            error_msg or self.get_text("export.unknown_error", "未知错误")
        )
    
    # 显示消息框
    msg_box.exec_()

# 为了向后兼容，添加带下划线前缀的别名
_on_export_finished = on_export_finished
