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
            self.get_text("playlist.export.title", "导出歌曲"),
            self.get_text("playlist.export.warning", "请至少选择一首歌曲进行导出")
        )
        msg_box.exec_()
        return

    logger.info(f"用户选择了 {len(selected_ids)} 首歌曲进行导出")
    
    # 从用户设置中读取导出格式
    try:
        # 优先从user_settings.json读取新的设置
        from src.config import settings
        file_format = settings.get_setting("export_file_format")
        logger.debug(f"从user_settings.json读取的文件格式: {file_format}")
        
        if file_format is None:
            # 尝试读取旧的设置
            use_txt_json = settings.get_setting("export_use_txt")
            if use_txt_json is not None:
                file_format = "txt" if use_txt_json else "csv"
                logger.debug(f"从user_settings.json的export_use_txt设置推导文件格式: {file_format}")
            else:
                # 如果user_settings.json中不存在，则从QSettings读取
                settings_qt = QSettings("Spotify", "SpotifyExport")
                # 优先使用export_file_format，如果不存在则使用export_use_txt的推导值
                file_format_qt = settings_qt.value("export_file_format")
                if file_format_qt:
                    file_format = file_format_qt
                    logger.debug(f"从QSettings的export_file_format读取文件格式: {file_format}")
                else:
                    use_txt = settings_qt.value("export_use_txt", "true") == "true"
                    file_format = "txt" if use_txt else "csv"
                    logger.debug(f"从QSettings的export_use_txt设置推导文件格式: {file_format}")
                
                # 同步到user_settings.json
                try:
                    settings.set_setting("export_file_format", file_format)
                    logger.debug(f"将文件格式同步到user_settings.json: {file_format}")
                except Exception as e:
                    logger.error(f"同步文件格式到user_settings.json失败: {str(e)}")
    except ImportError:
        # 如果无法导入settings模块，则只从QSettings读取
        logger.warning("无法导入settings模块，只从QSettings读取设置")
        settings_qt = QSettings("Spotify", "SpotifyExport")
        # 优先使用export_file_format，如果不存在则使用export_use_txt的推导值
        file_format_qt = settings_qt.value("export_file_format")
        if file_format_qt:
            file_format = file_format_qt
            logger.debug(f"从QSettings的export_file_format读取文件格式: {file_format}")
        else:
            use_txt = settings_qt.value("export_use_txt", "true") == "true"
            file_format = "txt" if use_txt else "csv"
            logger.debug(f"从QSettings的export_use_txt设置推导文件格式: {file_format}")

    # 验证文件格式是否有效，如果无效则使用默认值
    valid_formats = ["txt", "csv", "json"]
    if file_format not in valid_formats:
        logger.warning(f"无效的文件格式: {file_format}，使用默认值: txt")
        file_format = "txt"

    # 使用文件格式
    export_format = file_format
    logger.info(f"最终使用的导出文件格式: {export_format}")

    # 弹出文件保存对话框
    try:
        file_path = self._show_save_file_dialog(export_format)
        
        # 检查文件路径是否有效
        if not file_path:
            logger.info("用户取消了文件保存或保存对话框出现错误")
            return
            
        # 验证文件路径
        if not os.path.dirname(os.path.abspath(file_path)):
            logger.error(f"无效的文件路径: {file_path}")
            msg_box = create_styled_message_box(
                self,
                QMessageBox.Critical,
                self.get_text("common.error", "错误"),
                self.get_text("playlist.invalid_path", "无效的文件保存路径")
            )
            msg_box.exec_()
            return
    except Exception as e:
        logger.error(f"显示文件保存对话框时发生错误: {str(e)}", exc_info=True)
        msg_box = create_styled_message_box(
            self,
            QMessageBox.Critical,
            self.get_text("common.error", "错误"),
            self.get_text("playlist.save_dialog_error", "显示文件保存对话框时发生错误: {0}").format(str(e))
        )
        msg_box.exec_()
        return

    logger.info(f"用户选择的保存路径: {file_path}")

    # 获取选中的歌曲数据 - 修改为直接从song_items构建
    logger.info("开始收集选中歌曲数据")
    selected_songs = []

    # 直接从song_items构建导出数据，跳过current_songs匹配
    for song_id in selected_ids:
        if song_id in self.song_items:
            song_item = self.song_items[song_id]
            
            # 提取歌曲数据
            export_song = {}
            
            # 设置ID
            export_song['id'] = song_id
            
            # 提取歌曲名称
            if hasattr(song_item, "title_label") and song_item.title_label.text():
                export_song['name'] = song_item.title_label.text()
            else:
                export_song['name'] = "未知歌曲"
                
            # 提取艺术家
            if hasattr(song_item, "artist_label") and song_item.artist_label.text():
                export_song['artist'] = song_item.artist_label.text()
            else:
                export_song['artist'] = "未知艺术家"
                
            # 提取专辑
            if hasattr(song_item, "album_label") and song_item.album_label.text():
                export_song['album'] = song_item.album_label.text()
            else:
                export_song['album'] = "未知专辑"
                
            # 其他字段
            export_song['duration_ms'] = 0
            export_song['url'] = ""
            
            # 如果有track_data，优先使用
            if hasattr(song_item, "track_data"):
                track_data = song_item.track_data
                
                # 更新字段
                if track_data.get("name"):
                    export_song['name'] = track_data.get("name")
                    
                if track_data.get("artist"):
                    export_song['artist'] = track_data.get("artist")
                    
                if track_data.get("album"):
                    export_song['album'] = track_data.get("album")
                    
                if track_data.get("duration_ms"):
                    export_song['duration_ms'] = track_data.get("duration_ms")
                    
                if track_data.get("url"):
                    export_song['url'] = track_data.get("url")
            
            # 添加到导出列表
            selected_songs.append(export_song)
            logger.debug(f"添加歌曲到导出列表: {export_song['name']} - {export_song['artist']}")
        else:
            logger.warning(f"找不到选中的歌曲项: {song_id}")

    logger.info(f"已收集 {len(selected_songs)} 首歌曲进行导出")

    # 如果没有有效的歌曲数据，提示用户
    if not selected_songs:
        msg_box = create_styled_message_box(
            self,
            QMessageBox.Warning,
            self.get_text("playlist.export_title", "导出歌曲"),
            self.get_text("playlist.no_valid_tracks", "没有有效的歌曲数据")
        )
        msg_box.exec_()
        return

    # 使用文件导出器执行导出
    try:
        # 创建进度对话框
        progress_dialog = QDialog(self)
        progress_dialog.setWindowTitle(self.get_text("playlist.export.title", "导出歌曲"))
        progress_dialog.setMinimumWidth(400)
        progress_dialog.setStyleSheet("""
            QDialog {
                background-color: #121212;
                color: white;
                border: 1px solid #333333;
            }
            QLabel {
                color: white;
                font-size: 14px;
                background-color: transparent;
            }
            QProgressBar {
                border: 1px solid #555555;
                border-radius: 4px;
                text-align: center;
                background-color: #333333;
                color: white;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #1DB954;
                border-radius: 3px;
            }
        """)
        
        # 创建布局
        layout = QVBoxLayout(progress_dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 添加状态标签
        status_label = QLabel(self.get_text("playlist.export_processing", "正在处理导出..."))
        layout.addWidget(status_label)
        
        # 显示对话框（非模态，让导出在后台进行）
        progress_dialog.show()
        
        # 执行导出
        logger.info(f"开始导出 {len(selected_songs)} 首歌曲到 {file_path}，格式: {export_format}")
        exporter = get_file_exporter()
        
        # 连接信号
        exporter.progress_signal.connect(lambda p: status_label.setText(
            self.get_text("playlist.export_progress", "正在导出: {percent}%").format(percent=p)
        ))
        exporter.finished_signal.connect(lambda success, error: self._on_export_finished(
            progress_dialog, success, error, file_path
        ))
        
        # 执行导出
        result = exporter.export(selected_songs, file_path=file_path, format_type=export_format)
        
        if not result:
            # 导出失败
            error_message = exporter.get_last_error() or "未知错误"
            logger.error(f"导出失败: {error_message}")
            progress_dialog.close()
            msg_box = create_styled_message_box(
                self,
                QMessageBox.Critical,
                self.get_text("common.error", "错误"),
                self.get_text(
                    "playlist.export_error", "导出歌曲时发生错误：{0}"
                ).format(error_message)
            )
            msg_box.exec_()
            return
    except Exception as e:
        logger.error(f"导出歌曲时发生错误: {e}", exc_info=True)
        msg_box = create_styled_message_box(
            self,
            QMessageBox.Critical,
            self.get_text("common.error", "错误"),
            self.get_text(
                "playlist.export_error", "导出歌曲时发生错误：{0}"
            ).format(str(e))
        )
        msg_box.exec_()
        return

    # 导出完成后退出导出模式
    self.toggle_export_mode()


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


def _on_export_finished(self, dialog, success, error, file_path):
    """导出完成回调

    Args:
        dialog: 对话框
        success: 是否成功
        error: 错误信息
        file_path: 文件路径
    """
    # 关闭对话框
    dialog.accept()

    # 处理结果
    if success:
        # 获取选中的歌曲ID的数量
        selected_count = len(self.get_selected_song_ids())
        
        # 导出成功
        msg_box = create_styled_message_box(
            self,
            QMessageBox.Information,
            self.get_text("common.success", "成功"),
            self.get_text(
                "playlist.export_success", "已成功导出 {0} 首歌曲到 {1}"
            ).format(selected_count, file_path)
        )
        msg_box.exec_()
    else:
        # 导出失败
        msg_box = create_styled_message_box(
            self,
            QMessageBox.Critical,
            self.get_text("common.error", "错误"),
            self.get_text(
                "playlist.export_error", "导出歌曲时发生错误：{0}"
            ).format(error)
        )
        msg_box.exec_()
