"""
文件导出器
支持导出到TXT、CSV和JSON格式
"""
import os
import json
import csv
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from PyQt5.QtCore import QSettings, QObject, pyqtSignal

from src.utils.logger import logger
from src.config import settings
from src.utils.thread_manager import thread_manager


class FileExporter(QObject):
    """
    文件导出器
    支持导出到TXT、CSV和JSON格式
    """
    
    # 信号定义
    progress_signal = pyqtSignal(int)  # 导出进度信号
    status_signal = pyqtSignal(str)    # 导出状态信号
    finished_signal = pyqtSignal(bool, str)  # 导出完成信号，参数为(是否成功, 错误信息)
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化文件导出器
        
        Args:
            config: 导出器配置
        """
        super().__init__()
        self.config = config or {}
        self.last_error = None
        self.settings_qt = QSettings("Spotify", "SpotifyExport")
        
        # 从配置中读取导出格式设置
        self._init_export_settings()
        
    def _init_export_settings(self):
        """初始化导出设置，从user_settings.json或QSettings中读取"""
        try:
            # 优先从user_settings.json读取
            self.export_format = settings.get_setting("export_format")
            self.file_format = settings.get_setting("export_file_format")
            
            # 记录从user_settings.json读取的原始值
            logger.debug(f"从user_settings.json读取的导出格式: {self.export_format}")
            logger.debug(f"从user_settings.json读取的文件格式: {self.file_format}")
            
            # 如果user_settings.json中不存在，则从QSettings读取
            if self.export_format is None:
                raw_export_format = self.settings_qt.value("export_format")
                logger.debug(f"从QSettings读取的原始导出格式: {raw_export_format}")
                self.export_format = raw_export_format if raw_export_format is not None else "name-artists"
                # 同步到user_settings.json
                try:
                    settings.set_setting("export_format", self.export_format)
                    logger.debug(f"将导出格式同步到user_settings.json: {self.export_format}")
                except Exception as e:
                    logger.error(f"同步导出格式到user_settings.json失败: {str(e)}")
                
            if self.file_format is None:
                # 尝试读取旧的设置
                use_txt_json = settings.get_setting("export_use_txt")
                if use_txt_json is not None:
                    self.file_format = "txt" if use_txt_json else "csv"
                    logger.debug(f"从user_settings.json的export_use_txt设置推导文件格式: {self.file_format}")
                else:
                    # 从QSettings读取
                    use_txt = self.settings_qt.value("export_use_txt", "true") == "true"
                    file_format_qt = self.settings_qt.value("export_file_format")
                    
                    # 优先使用export_file_format，如果不存在则使用export_use_txt的推导值
                    if file_format_qt:
                        self.file_format = file_format_qt
                        logger.debug(f"从QSettings的export_file_format读取文件格式: {self.file_format}")
                    else:
                        self.file_format = "txt" if use_txt else "csv"
                        logger.debug(f"从QSettings的export_use_txt设置推导文件格式: {self.file_format}")
                
                # 同步到user_settings.json
                try:
                    settings.set_setting("export_file_format", self.file_format)
                    logger.debug(f"将文件格式同步到user_settings.json: {self.file_format}")
                except Exception as e:
                    logger.error(f"同步文件格式到user_settings.json失败: {str(e)}")
                    
            # 验证文件格式是否有效，如果无效则使用默认值
            valid_formats = ["txt", "csv", "json"]
            if self.file_format not in valid_formats:
                logger.warning(f"无效的文件格式: {self.file_format}，使用默认值: txt")
                self.file_format = "txt"
                
            # 保留use_txt属性以保持兼容性
            self.use_txt = self.file_format == "txt"
            
            logger.info(f"初始化导出器，最终导出格式: {self.export_format}, 文件格式: {self.file_format}")
            
        except Exception as e:
            # 如果发生任何错误，使用默认值
            logger.error(f"初始化导出设置失败: {str(e)}")
            self.export_format = "name-artists"
            self.file_format = "txt"
            self.use_txt = True
        
    @property
    def name(self) -> str:
        return "file"
        
    @property
    def display_name(self) -> str:
        return "文件导出器"
        
    @property
    def description(self) -> str:
        return "将歌曲导出到文本文件，支持TXT、CSV和JSON格式"
        
    @property
    def icon_path(self) -> Optional[str]:
        """
        导出器图标路径
        
        Returns:
            Optional[str]: 导出器图标路径，如果没有则返回None
        """
        return None
        
    def get_export_options(self) -> Dict[str, Any]:
        """
        获取导出选项
        
        Returns:
            Dict[str, Any]: 导出选项
        """
        return {
            "format": {
                "type": "select",
                "label": "文件格式",
                "options": [
                    {"value": "txt", "label": "文本文件 (.txt)"},
                    {"value": "csv", "label": "CSV文件 (.csv)"},
                    {"value": "json", "label": "JSON文件 (.json)"}
                ],
                "default": self.file_format
            }
        }
        
    def threaded_export(func):
        """
        装饰器，用于在线程中安全地运行导出方法
        
        Args:
            func: 要在线程中运行的方法
        
        Returns:
            包装后的方法
        """
        def wrapper(self, *args, **kwargs):
            def export_task():
                try:
                    result = func(self, *args, **kwargs)
                    self.finished_signal.emit(result, self.last_error or "")
                except Exception as e:
                    self.last_error = str(e)
                    logger.error(f"导出任务出错: {e}")
                    self.finished_signal.emit(False, self.last_error)
            
            # 使用线程管理器安全地运行导出任务
            thread_manager.safe_thread_run(export_task, category='file_export')
            return True
        return wrapper

    @threaded_export
    def export(self, songs: List[Dict[str, Any]], **kwargs) -> bool:
        """
        执行导出操作
        
        Args:
            songs: 要导出的歌曲列表
            **kwargs: 额外参数，包括：
                - file_path: 文件保存路径
                - format_type: 文件格式（txt, csv, json），如果为None则使用配置中的格式
                
        Returns:
            bool: 是否成功
        """
        try:
            # 获取参数
            file_path = kwargs.get("file_path")
            format_type = kwargs.get("format_type") or kwargs.get("format")
            
            # 如果未指定格式类型，则使用配置中的格式
            if format_type is None:
                format_type = self.file_format
            
            # 验证参数
            if not file_path:
                raise ValueError("未指定文件保存路径")
                
            # 验证歌曲数据
            valid_songs = self.validate_songs(songs)
            if not valid_songs:
                self.last_error = "没有有效的歌曲数据"
                logger.warning("导出失败：没有有效的歌曲数据")
                return False
            
            # 记录导出信息，用于调试
            logger.info(f"使用格式类型 {format_type} 导出到文件: {file_path}")
            logger.info(f"导出格式设置: {self.export_format}")
            logger.info(f"开始导出 {len(valid_songs)} 首歌曲")
            
            # 检查文件扩展名与格式类型
            file_ext = os.path.splitext(file_path)[1].lower().lstrip('.')
            if file_ext != format_type:
                logger.warning(f"文件扩展名 ({file_ext}) 与指定的导出格式 ({format_type}) 不匹配，将使用指定的格式 {format_type} 导出")
            
            # 根据格式类型调用不同的导出方法
            total_songs = len(valid_songs)
            
            if format_type.lower() == 'json':
                self._export_json(valid_songs, file_path, total_songs)
            elif format_type.lower() == 'csv':
                self._export_csv(valid_songs, file_path, total_songs)
            elif format_type.lower() == 'txt':
                self._export_txt(valid_songs, file_path, total_songs)
            else:
                raise ValueError(f"不支持的导出格式: {format_type}")
            
            return True
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"导出失败: {e}")
            return False
            
    def validate_songs(self, songs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        验证并清理歌曲数据
        
        Args:
            songs: 原始歌曲数据
            
        Returns:
            List[Dict[str, Any]]: 清理后的歌曲数据
        """
        valid_songs = []
        skipped_songs = 0
        
        logger.info(f"验证 {len(songs)} 首歌曲数据")
        if songs and len(songs) > 0:
            logger.debug(f"第一首歌曲数据结构: {songs[0].keys()}")
        
        for song in songs:
            # 创建标准化的歌曲对象
            standardized_song = {
                'id': '',
                'name': '未知歌曲',
                'artist': '未知艺术家',
                'album': '未知专辑',
                'duration_ms': 0,  # 确保使用duration_ms作为标准字段名
                'url': ''
            }
            
            # 支持多种命名约定
            # ID字段
            if 'id' in song:
                standardized_song['id'] = song['id']
                
            # 歌曲名称字段
            for name_field in ['name', 'title', 'track_name', 'song_name']:
                if name_field in song and song[name_field]:
                    standardized_song['name'] = song[name_field]
                    break
                    
            # 艺术家字段
            for artist_field in ['artist', 'artists', 'artist_name']:
                if artist_field in song:
                    artist_value = song[artist_field]
                    # 处理艺术家可能是字符串或列表的情况
                    if isinstance(artist_value, list):
                        try:
                            # 列表可能是艺术家名称列表或对象列表
                            if artist_value and isinstance(artist_value[0], str):
                                standardized_song['artist'] = ', '.join(artist_value)
                            elif artist_value and isinstance(artist_value[0], dict) and 'name' in artist_value[0]:
                                artists = [a['name'] for a in artist_value if 'name' in a]
                                standardized_song['artist'] = ', '.join(artists)
                        except (IndexError, TypeError) as e:
                            logger.warning(f"处理艺术家列表失败: {e}")
                    else:
                        standardized_song['artist'] = str(artist_value)
                    break
                    
            # 专辑字段
            for album_field in ['album', 'album_name']:
                if album_field in song:
                    album_value = song[album_field]
                    if isinstance(album_value, dict) and 'name' in album_value:
                        standardized_song['album'] = album_value['name']
                    else:
                        standardized_song['album'] = str(album_value)
                    break
                    
            # 时长字段 - 确保使用duration_ms作为标准字段名
            for duration_field in ['duration_ms', 'duration', 'length']:
                if duration_field in song and song[duration_field]:
                    try:
                        # 可能是字符串或数字
                        duration_value = int(song[duration_field])
                        
                        # 如果是秒，转换为毫秒
                        if duration_field != 'duration_ms' and duration_value < 10000:  # 假设小于10000的是秒
                            duration_value *= 1000
                            
                        standardized_song['duration_ms'] = duration_value
                    except (ValueError, TypeError):
                        # 如果转换失败，保留默认值
                        pass
                    break
                    
            # URL字段
            for url_field in ['url', 'external_url', 'external_urls', 'href']:
                if url_field in song:
                    url_value = song[url_field]
                    if isinstance(url_value, dict) and 'spotify' in url_value:
                        standardized_song['url'] = url_value['spotify']
                    elif isinstance(url_value, str):
                        standardized_song['url'] = url_value
                    break
                    
            # 总是添加歌曲，即使缺少某些字段
            valid_songs.append(standardized_song)
            
        logger.info(f"验证完成: 有效歌曲 {len(valid_songs)} 首, 跳过 {skipped_songs} 首")
        return valid_songs
        
    def get_last_error(self) -> str:
        """
        获取最后一次错误信息
        
        Returns:
            str: 错误信息
        """
        return self.last_error or ""

    def _export_json(self, songs: List[Dict[str, Any]], file_path: str, total_songs: int) -> None:
        """
        导出为JSON格式
        
        Args:
            songs: 歌曲列表
            file_path: 文件保存路径
            total_songs: 歌曲总数
        """
        try:
            # 使用构造函数中已经读取的导出格式
            export_format = self.export_format
            logger.info(f"JSON导出使用格式: {export_format}")
                
            # 准备导出数据
            export_data = {
                "playlist_name": os.path.basename(file_path).split(".")[0],
                "export_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "format_info": {
                    "export_format": export_format
                },
                "songs": []
            }
            
            # 处理每首歌曲
            for i, song in enumerate(songs):
                # 根据导出格式构建歌曲数据
                if export_format == "name-artists":
                    # 歌名-歌手格式：只包含序号、歌曲名称和艺术家
                    song_data = {
                        "序号": i + 1,  # 使用索引+1作为序号，而不是ID
                        "name": song.get("name", ""),
                        "artist": song.get("artist", "")
                    }
                elif export_format == "artists-name":
                    # 歌手-歌名格式：只包含序号、艺术家和歌曲名称
                    song_data = {
                        "序号": i + 1,  # 使用索引+1作为序号，而不是ID
                        "artist": song.get("artist", ""),
                        "name": song.get("name", "")
                    }
                elif export_format == "name-artists-album":
                    # 歌名-歌手-专辑格式：只包含序号、歌曲名称、艺术家和专辑
                    song_data = {
                        "序号": i + 1,  # 使用索引+1作为序号，而不是ID
                        "name": song.get("name", ""),
                        "artist": song.get("artist", ""),
                        "album": song.get("album", "")
                    }
                else:
                    # 默认格式：使用最基本的序号和歌曲名称
                    song_data = {
                        "序号": i + 1,  # 使用索引+1作为序号，而不是ID
                        "name": song.get("name", "")
                    }
                    logger.warning(f"未知的导出格式: {export_format}，使用默认字段")
                
                # 添加到导出数据
                export_data["songs"].append(song_data)
                
                # 更新进度
                progress = int((i + 1) / total_songs * 100)
                self.progress_signal.emit(progress)
                self.status_signal.emit(f"正在导出: {progress}%")
            
            # 写入文件
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"成功导出JSON文件: {file_path}, 使用格式: {export_format}")
        except Exception as e:
            logger.error(f"导出JSON失败: {str(e)}", exc_info=True)
            raise
            
    def _export_csv(self, songs: List[Dict[str, Any]], file_path: str, total_songs: int) -> None:
        """
        导出为CSV格式
        
        Args:
            songs: 歌曲列表
            file_path: 文件保存路径
            total_songs: 歌曲总数
        """
        try:
            # 使用构造函数中已经读取的导出格式
            export_format = self.export_format
            logger.info(f"CSV导出使用格式: {export_format}")
                
            # 根据导出格式定义表头和数据行
            if export_format == "name-artists":
                # 歌名-歌手格式：只包含序号、歌曲名称和艺术家
                headers = ["序号", "歌曲名称", "艺术家"]
                
                # 写入文件
                with open(file_path, "w", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                    
                    # 处理每首歌曲
                    for i, song in enumerate(songs):
                        writer.writerow([
                            i + 1,  # 使用索引+1作为序号，而不是ID
                            song.get("name", ""),
                            song.get("artist", "")
                        ])
                        
                        # 更新进度
                        progress = int((i + 1) / total_songs * 100)
                        self.progress_signal.emit(progress)
                        self.status_signal.emit(f"正在导出: {progress}%")
                        
            elif export_format == "artists-name":
                # 歌手-歌名格式：只包含序号、艺术家和歌曲名称
                headers = ["序号", "艺术家", "歌曲名称"]
                
                # 写入文件
                with open(file_path, "w", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                    
                    # 处理每首歌曲
                    for i, song in enumerate(songs):
                        writer.writerow([
                            i + 1,  # 使用索引+1作为序号，而不是ID
                            song.get("artist", ""),
                            song.get("name", "")
                        ])
                        
                        # 更新进度
                        progress = int((i + 1) / total_songs * 100)
                        self.progress_signal.emit(progress)
                        self.status_signal.emit(f"正在导出: {progress}%")
                        
            elif export_format == "name-artists-album":
                # 歌名-歌手-专辑格式：只包含序号、歌曲名称、艺术家和专辑
                headers = ["序号", "歌曲名称", "艺术家", "专辑"]
                
                # 写入文件
                with open(file_path, "w", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                    
                    # 处理每首歌曲
                    for i, song in enumerate(songs):
                        writer.writerow([
                            i + 1,  # 使用索引+1作为序号，而不是ID
                            song.get("name", ""),
                            song.get("artist", ""),
                            song.get("album", "")
                        ])
                        
                        # 更新进度
                        progress = int((i + 1) / total_songs * 100)
                        self.progress_signal.emit(progress)
                        self.status_signal.emit(f"正在导出: {progress}%")
                        
            else:
                # 默认格式：使用最基本的序号和歌曲名称
                headers = ["序号", "歌曲名称"]
                logger.warning(f"未知的导出格式: {export_format}，使用默认表头")
                
                # 写入文件
                with open(file_path, "w", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                    
                    # 处理每首歌曲
                    for i, song in enumerate(songs):
                        writer.writerow([
                            i + 1,  # 使用索引+1作为序号，而不是ID
                            song.get("name", "")
                        ])
                        
                        # 更新进度
                        progress = int((i + 1) / total_songs * 100)
                        self.progress_signal.emit(progress)
                        self.status_signal.emit(f"正在导出: {progress}%")
                    
            logger.info(f"成功导出CSV文件: {file_path}, 使用格式: {export_format}")
        except Exception as e:
            logger.error(f"导出CSV失败: {str(e)}", exc_info=True)
            raise
            
    def _export_txt(self, songs: List[Dict[str, Any]], file_path: str, total_songs: int) -> None:
        """
        导出为TXT格式
        
        Args:
            songs: 歌曲列表
            file_path: 文件保存路径
            total_songs: 歌曲总数
        """
        try:
            # 使用构造函数中已经读取的导出格式
            export_format = self.export_format
            logger.info(f"TXT导出使用格式: {export_format}")
            logger.info(f"正在导出到文件: {file_path}")
            
            # 确保目录存在
            try:
                dir_path = os.path.dirname(os.path.abspath(file_path))
                if not os.path.exists(dir_path):
                    logger.info(f"创建目录: {dir_path}")
                    os.makedirs(dir_path, exist_ok=True)
            except Exception as e:
                logger.error(f"创建目录失败: {str(e)}")
                raise ValueError(f"无法创建目录 {dir_path}: {str(e)}")
            
            # 写入文件
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    # 写入标题
                    playlist_name = os.path.basename(file_path).split('.')[0]
                    f.write(f"# {playlist_name}\n")
                    f.write(f"# 导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    
                    # 处理每首歌曲
                    for i, song in enumerate(songs):
                        # 获取歌曲信息，使用空字符串作为默认值
                        song_name = song.get('name', '')
                        artist = song.get('artist', '')
                        album = song.get('album', '')
                        
                        logger.debug(f"处理歌曲 {i+1}/{total_songs}: {song_name} - {artist}")
                        
                        # 根据导出格式生成输出行
                        if export_format == "name-artists":
                            # 歌名-歌手格式：只输出歌曲名称和艺术家
                            output_line = f"{i+1}. {song_name} - {artist}\n"
                        elif export_format == "artists-name":
                            # 歌手-歌名格式：只输出艺术家和歌曲名称
                            output_line = f"{i+1}. {artist} - {song_name}\n"
                        elif export_format == "name-artists-album":
                            # 歌名-歌手-专辑格式：只输出歌曲名称、艺术家和专辑
                            output_line = f"{i+1}. {song_name} - {artist} - {album}\n"
                        else:
                            # 默认格式：只输出歌曲名称
                            output_line = f"{i+1}. {song_name}\n"
                            logger.warning(f"未知的导出格式: {export_format}，使用默认格式")
                        
                        # 写入行，确保编码正确
                        try:
                            f.write(output_line)
                        except UnicodeEncodeError as e:
                            logger.warning(f"写入歌曲时出现编码错误，尝试处理特殊字符: {str(e)}")
                            # 尝试处理特殊字符
                            clean_line = output_line.encode('utf-8', 'ignore').decode('utf-8')
                            f.write(clean_line)
                        
                        # 更新进度
                        progress = int((i + 1) / total_songs * 100)
                        self.progress_signal.emit(progress)
                        self.status_signal.emit(f"正在导出: {progress}%")
            except PermissionError:
                logger.error(f"无法写入文件 {file_path}，权限被拒绝")
                raise ValueError(f"无法写入文件，请检查您是否有权限写入该位置或文件是否被其他程序占用")
            except IOError as e:
                logger.error(f"写入文件失败: {str(e)}")
                raise ValueError(f"写入文件失败: {str(e)}")
                
            logger.info(f"成功导出TXT文件: {file_path}, 使用格式: {export_format}, 共 {total_songs} 首歌曲")
        except Exception as e:
            logger.error(f"导出TXT失败: {str(e)}", exc_info=True)
            raise 