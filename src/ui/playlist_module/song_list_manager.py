"""
播放列表歌曲列表管理功能模块
处理歌曲创建、过滤、排序和选择相关操作
"""

from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QCheckBox, QSizePolicy
from PyQt5.QtCore import Qt, QTimer, QPoint, QRect, QTime
from PyQt5.QtGui import QFontMetrics
from src.utils.logger import logger

def create_song_item(self, track, index):
    """创建单个歌曲项

    Args:
        track: 歌曲信息
        index: 歌曲索引

    Returns:
        QWidget: 歌曲项控件
    """
    # 创建歌曲项
    song_item = QWidget()
    song_item.setObjectName(f"song_item_{track['id']}")
    song_item.setFixedHeight(60)
    song_item.setStyleSheet(
        """
        QWidget {
            background-color: transparent;
            border-radius: 4px;
        }
        QWidget:hover {
            background-color: rgba(255, 255, 255, 0.1);
        }
    """
    )

    # 创建歌曲布局
    song_layout = QHBoxLayout(song_item)
    song_layout.setContentsMargins(10, 5, 10, 5)
    song_layout.setSpacing(10)

    # 创建歌曲索引标签
    index_label = QLabel(str(index))
    index_label.setStyleSheet("color: #b3b3b3; font-size: 14px;")
    index_label.setFixedWidth(30)
    index_label.setAlignment(Qt.AlignCenter)
    song_layout.addWidget(index_label)

    # 创建选择框（默认隐藏）
    checkbox = QCheckBox()
    checkbox.setObjectName(f"checkbox_{track['id']}")
    checkbox.setStyleSheet(
        """
        QCheckBox {
            background-color: transparent;
        }
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
        }
        QCheckBox::indicator:unchecked {
            border: 2px solid #b3b3b3;
            border-radius: 4px;
            background-color: transparent;
        }
        QCheckBox::indicator:checked {
            border: 2px solid #1DB954;
            border-radius: 4px;
            background-color: #1DB954;
            image: url(./assets/check.png);
        }
    """
    )
    checkbox.setFixedWidth(30)
    checkbox.hide()  # 默认隐藏
    song_layout.addWidget(checkbox)

    # 创建封面容器
    artwork_container = QWidget()
    artwork_container.setObjectName(f"artwork_{track['id']}")
    artwork_container.setFixedSize(50, 50)
    artwork_container.setStyleSheet("background-color: #282828; border-radius: 4px;")
    song_layout.addWidget(artwork_container)

    # 创建标题标签 - 添加省略功能和工具提示
    title_label = QLabel(track["name"])
    title_label.setStyleSheet("color: white; font-size: 14px;")
    title_label.setAlignment(Qt.AlignVCenter)
    title_label.setToolTip(track["name"])  # 添加工具提示，在鼠标悬停时显示完整文本
    title_label.setTextFormat(Qt.PlainText)  # 使用纯文本格式以提高性能
    title_label.setTextInteractionFlags(Qt.NoTextInteraction)  # 禁用文本交互以提高性能
    title_label.setWordWrap(False)  # 禁用自动换行
    # 设置省略模式
    title_label.setMaximumWidth(200)  # 进一步减小最大宽度
    title_label.setMinimumWidth(60)   # 减小最小宽度
    title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    # 初始时先使用完整文本，省略将在布局完成后通过update_song_labels_text处理
    title_label.setText(track["name"])
    song_layout.addWidget(title_label)

    # 创建专辑标签 - 添加省略功能和工具提示
    album_label = QLabel(track["album"])
    album_label.setStyleSheet("color: #b3b3b3; font-size: 14px;")
    album_label.setAlignment(Qt.AlignVCenter)
    album_label.setToolTip(track["album"])  # 添加工具提示
    album_label.setTextFormat(Qt.PlainText)
    album_label.setTextInteractionFlags(Qt.NoTextInteraction)
    album_label.setWordWrap(False)
    # 设置省略模式
    album_label.setMaximumWidth(180)  # 减小最大宽度
    album_label.setMinimumWidth(50)   # 减小最小宽度
    album_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    # 初始时先使用完整文本，省略将在布局完成后通过update_song_labels_text处理
    album_label.setText(track["album"])
    song_layout.addWidget(album_label)

    # 创建歌手标签 - 添加省略功能和工具提示
    artist_label = QLabel(track["artist"])
    artist_label.setStyleSheet("color: #b3b3b3; font-size: 14px;")
    artist_label.setAlignment(Qt.AlignVCenter)
    artist_label.setToolTip(track["artist"])  # 添加工具提示
    artist_label.setTextFormat(Qt.PlainText)
    artist_label.setTextInteractionFlags(Qt.NoTextInteraction)
    artist_label.setWordWrap(False)
    # 设置省略模式
    artist_label.setMaximumWidth(200)  # 减小最大宽度
    artist_label.setMinimumWidth(60)   # 减小最小宽度
    artist_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    # 初始时先使用完整文本，省略将在布局完成后通过update_song_labels_text处理
    artist_label.setText(track["artist"])
    song_layout.addWidget(artist_label)

    # 保存引用
    song_item.index_label = index_label
    song_item.checkbox = checkbox
    song_item.title_label = title_label
    song_item.album_label = album_label
    song_item.artist_label = artist_label
    song_item.track_id = track["id"]
    song_item.track_data = track

    return song_item


def create_song_list(self, songs=None, filter_text=None, replace=False):
    """创建歌曲列表

    Args:
        songs: 歌曲列表，如果为None则使用当前的歌曲
        filter_text: 过滤文本
        replace: 是否替换现有歌曲列表
    """
    # 如果正在创建列表，跳过
    if self.is_creating_list:
        logger.debug("跳过创建歌曲列表，因为当前已经在创建")
        return

    self.is_creating_list = True
    try:
        # 获取歌曲列表
        songs_to_display = songs if songs is not None else self.current_songs

        # 如果没有歌曲，清空列表并返回
        if not songs_to_display:
            if replace:
                self._clear_song_list()
                self.status_label.setText(
                    self.get_text("playlist.empty", "播放列表为空")
                )
            self.is_creating_list = False
            return

        # 如果需要过滤
        if filter_text:
            filter_text = filter_text.lower()
            filtered_songs = []

            # 优化的过滤逻辑
            for song in songs_to_display:
                if (
                    filter_text in song["name"].lower()
                    or filter_text in song["artist"].lower()
                    or filter_text in song["album"].lower()
                ):
                    filtered_songs.append(song)

            songs_to_display = filtered_songs

        # 如果过滤后没有歌曲
        if not songs_to_display:
            if replace:
                self._clear_song_list()
                self.status_label.setText(
                    self.get_text("playlist.no_results", "没有符合条件的歌曲")
                )
            self.is_creating_list = False
            return

        # 如果需要替换现有列表
        if replace:
            self._clear_song_list()

        # 批量创建歌曲项 - 使用懒加载方式
        self._add_songs_batch(songs_to_display)

        # 更新状态标签
        if replace:
            try:
                logger.debug(f"准备显示歌曲数量文本，songs_count={len(songs_to_display)}")
                # 直接使用f-string替代format方法
                count = len(songs_to_display)
                count_text = f"{count} 首歌曲"
                logger.debug(f"格式化后的文本: '{count_text}'")
                self.status_label.setText(count_text)
            except Exception as e:
                logger.error(f"设置歌曲数量文本时出错: {str(e)}")
                # 使用简单的备用文本
                self.status_label.setText(f"{len(songs_to_display)} 首歌曲")

    finally:
        self.is_creating_list = False


def _add_songs_batch(self, songs, batch_size=30):
    """批量添加歌曲以提高性能

    Args:
        songs: 歌曲列表
        batch_size: 每批添加的歌曲数量
    """
    # 保存所有要添加的歌曲
    self.pending_songs = songs.copy()
    self.batch_size = batch_size
    self.current_batch_index = 0

    # 开始批量添加
    self._add_next_songs_batch()


def _process_track_data(self, track_item):
    """
    处理Spotify API返回的track数据，提取出我们需要的信息
    
    Args:
        track_item: Spotify API返回的track数据项
        
    Returns:
        dict: 处理后的track数据，包含id, name, album, artist等字段
    """
    try:
        # 从track_item中提取track信息
        track = track_item.get('track', {})
        if not track:
            # 如果没有track字段，尝试直接使用track_item
            track = track_item
            
        # 提取基本信息
        track_id = track.get('id', f"unknown_{hash(str(track))}")
        track_name = track.get('name', '未知歌曲')
        
        # 提取专辑信息
        album = track.get('album', {})
        album_name = album.get('name', '未知专辑')
        
        # 提取艺术家信息
        artists = track.get('artists', [])
        artist_names = []
        for artist in artists:
            artist_names.append(artist.get('name', '未知艺术家'))
        artist_name = ', '.join(artist_names) if artist_names else '未知艺术家'
        
        # 提取图片信息
        album_images = album.get('images', [])
        image_url = album_images[0].get('url') if album_images else ''
        
        # 构造我们需要的数据结构
        processed_track = {
            'id': track_id,
            'name': track_name,
            'album': album_name,
            'artist': artist_name,
            'image_url': image_url,
            'raw_data': track  # 保留原始数据，以防后续需要
        }
        
        # 如果有original_index，保留它
        if 'original_index' in track_item:
            processed_track['original_index'] = track_item['original_index']
            
        return processed_track
    except Exception as e:
        logger.error(f"处理歌曲数据失败: {str(e)}")
        # 返回一个默认的数据结构
        return {
            'id': f"error_{hash(str(track_item))}",
            'name': '处理错误',
            'album': '未知专辑',
            'artist': '未知艺术家',
            'image_url': ''
        }


def _add_next_songs_batch(self):
    """添加下一批歌曲"""
    if not self.pending_songs or self.current_batch_index >= len(self.pending_songs):
        # 所有批次添加完成
        return

    # 计算当前批次范围
    start_index = self.current_batch_index
    end_index = min(start_index + self.batch_size, len(self.pending_songs))
    current_batch = self.pending_songs[start_index:end_index]

    # 获取当前歌曲列表中的歌曲数量
    current_count = self.songs_layout.count() - 1  # 减去stretch

    # 批量添加歌曲项
    for i, track_item in enumerate(current_batch):
        # 处理track数据
        track = self._process_track_data(track_item)
        
        # 确保track有id字段
        if 'id' not in track:
            logger.debug(f"跳过没有ID的歌曲 (索引: {i})")
            continue
            
        song_index = current_count + i + 1  # +1 是因为歌曲索引从1开始
        song_item = self.create_song_item(track, song_index)

        # 如果是在导出模式下，显示复选框
        if self.export_mode:
            song_item.checkbox.show()

        # 将歌曲项添加到布局
        self.songs_layout.insertWidget(self.songs_layout.count() - 1, song_item)

        # 记录歌曲项
        self.song_items[track["id"]] = song_item

    # 更新当前批次索引
    self.current_batch_index = end_index

    # 如果还有更多批次要添加，延迟添加下一批
    if self.current_batch_index < len(self.pending_songs):
        QTimer.singleShot(20, self._add_next_songs_batch)
    else:
        # 所有批次添加完成后
        # 首先更新文本省略显示
        QTimer.singleShot(50, self.update_song_labels_text)
        # 然后请求加载图片
        QTimer.singleShot(100, self.load_visible_song_images)


def _clear_song_list(self):
    """清空歌曲列表"""
    # 删除所有歌曲项，保留最后的stretch
    while self.songs_layout.count() > 1:
        item = self.songs_layout.takeAt(0)
        if item.widget():
            item.widget().deleteLater()

    # 清空歌曲项字典
    self.song_items.clear()


def filter_songs(self, filter_text):
    """根据文本过滤歌曲

    Args:
        filter_text: 过滤文本
    """
    # 防止过于频繁的过滤
    if hasattr(self, "_last_filter_time"):
        current_time = QTime.currentTime().msecsSinceStartOfDay()
        if current_time - self._last_filter_time < 100:  # 100毫秒防抖
            return

    # 记录本次过滤时间
    self._last_filter_time = QTime.currentTime().msecsSinceStartOfDay()

    # 使用当前的排序方式重新创建歌曲列表
    self.create_song_list(self.current_songs, filter_text, replace=True)


def sort_songs(self, sort_key="index", reverse=False):
    """按指定键排序歌曲

    Args:
        sort_key: 排序键（'index', 'name', 'artist', 'album'）
        reverse: 是否逆序
    """
    if not self.current_songs:
        return

    # 映射排序键到歌曲属性
    key_mapping = {
        "index": lambda x: x.get("index", 0),
        "name": lambda x: x.get("name", "").lower(),
        "artist": lambda x: x.get("artist", "").lower(),
        "album": lambda x: x.get("album", "").lower(),
    }

    # 检查是否有效的排序键
    if sort_key not in key_mapping:
        logger.warning(f"无效的排序键: {sort_key}")
        return

    # 排序歌曲
    sorted_songs = sorted(
        self.current_songs, key=key_mapping[sort_key], reverse=reverse
    )

    # 保存当前排序方式
    self.current_sort_key = sort_key
    self.current_sort_reverse = reverse

    # 重新创建歌曲列表（保留过滤）
    filter_text = self.search_box.text() if hasattr(self, "search_box") else None
    self.create_song_list(sorted_songs, filter_text, replace=True)


def select_all_songs(self):
    """选择所有歌曲"""
    for song_id, song_item in self.song_items.items():
        if hasattr(song_item, "checkbox"):
            song_item.checkbox.setChecked(True)
    
    # 更新UI显示选中数量
    self.update_song_selection()


def clear_song_selection(self):
    """清除所有歌曲选择"""
    for song_id, song_item in self.song_items.items():
        if hasattr(song_item, "checkbox"):
            song_item.checkbox.setChecked(False)
    
    # 更新UI显示选中数量
    self.update_song_selection()


def get_selected_song_ids(self):
    """获取所有选中的歌曲ID

    Returns:
        list: 选中的歌曲ID列表
    """
    selected_ids = []

    for song_id, song_item in self.song_items.items():
        if hasattr(song_item, "checkbox") and song_item.checkbox.isChecked():
            selected_ids.append(song_id)

    return selected_ids


def update_song_selection(self):
    """更新歌曲选择状态并更新UI"""
    selected_count = 0
    total_count = len(self.song_items)

    # 计算选中的歌曲数量
    for song_id, song_item in self.song_items.items():
        if hasattr(song_item, "checkbox") and song_item.checkbox.isChecked():
            selected_count += 1

    # 更新状态标签
    if selected_count > 0:
        try:
            # 直接使用f-string
            selection_text = f"已选择 {selected_count} 首歌曲"
            self.status_label.setText(selection_text)
        except Exception as e:
            logger.error(f"设置选中歌曲数量文本时出错: {str(e)}")
            self.status_label.setText(f"已选择 {selected_count} 首歌曲")
    else:
        try:
            # 直接使用f-string
            count_text = f"{total_count} 首歌曲"
            self.status_label.setText(count_text)
        except Exception as e:
            logger.error(f"设置歌曲总数文本时出错: {str(e)}")
            self.status_label.setText(f"{total_count} 首歌曲")


def on_select_all_changed(self, state):
    """全选复选框状态变更回调 - 保留此方法以兼容可能的调用

    Args:
        state: 复选框状态
    """
    is_checked = state == Qt.Checked

    # 更新所有歌曲的选择状态
    for song_id, song_item in self.song_items.items():
        if hasattr(song_item, "checkbox"):
            song_item.checkbox.setChecked(is_checked)

    # 更新选择状态
    self.update_song_selection()


def load_visible_song_images(self):
    """加载可见的歌曲图片"""
    # 如果正在创建列表，跳过
    if self.is_creating_list:
        return

    # 获取滚动区域的可见范围
    visible_rect = self.scroll_area.viewport().rect()
    visible_pos = self.scroll_area.mapToGlobal(visible_rect.topLeft())
    
    # 调整为相对于内容窗口的坐标
    content_widget = self.scroll_area.widget()
    content_pos = content_widget.mapToGlobal(QPoint(0, 0))
    
    # 创建可见区域的副本并调整位置
    adjusted_rect = QRect(visible_rect)
    adjusted_rect.moveTopLeft(QPoint(0, visible_pos.y() - content_pos.y()))

    # 预加载范围（上下多加载几个）
    preload_range = 300
    adjusted_rect.adjust(0, -preload_range, 0, preload_range)

    # 遍历所有歌曲项，检查是否在可见范围内
    for song_id, song_item in self.song_items.items():
        # 获取歌曲项在内容窗口中的位置
        song_rect = song_item.geometry()
        
        # 判断是否在可见范围内
        if adjusted_rect.intersects(song_rect):
            # 检查是否已加载图片
            artwork_container = song_item.findChild(QWidget, f"artwork_{song_id}")
            if artwork_container and not hasattr(artwork_container, "image_loaded"):
                # 检查歌曲数据中是否有图片URL
                if hasattr(song_item, "track_data") and song_item.track_data.get("image_url"):
                    # 加载图片
                    self.request_song_image(song_item.track_data["image_url"], song_id)
                    # 标记为已加载
                    artwork_container.image_loaded = True


def on_search_changed(self, text):
    """搜索框文本变更回调

    Args:
        text: 搜索文本
    """
    # 延迟处理搜索，避免频繁更新
    if hasattr(self, "_search_timer"):
        self._search_timer.stop()
    else:
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(
            lambda: self.filter_songs(self.search_box.text())
        )

    self._search_timer.start(300)  # 300毫秒延迟


def update_song_image(self, track_id, pixmap):
    """更新歌曲图片

    Args:
        track_id: 歌曲ID
        pixmap: 图片
    """
    # 查找对应的歌曲项
    if track_id in self.song_items:
        song_item = self.song_items[track_id]

        # 查找封面容器
        artwork_container = song_item.findChild(QWidget, f"artwork_{track_id}")
        if artwork_container:
            # 创建图片标签（如果不存在）
            artwork_label = artwork_container.findChild(QLabel)
            if not artwork_label:
                artwork_label = QLabel(artwork_container)
                artwork_label.setGeometry(0, 0, 50, 50)
                artwork_label.setScaledContents(True)

            # 设置图片
            artwork_label.setPixmap(pixmap)
            artwork_label.show()

            # 标记为已加载完成
            artwork_container.setProperty("loaded_complete", True)


def update_song_labels_text(self):
    """更新所有歌曲标签的文本，处理省略号显示"""
    # 获取当前设置的宽度值
    viewport_width = self.scroll_area.viewport().width() if hasattr(self, "scroll_area") else self.width()
    effective_width = max(viewport_width - 60, 500)  # 进一步降低最小有效宽度到500
    
    # 根据窗口宽度获取不同的列宽比例
    if viewport_width < 800:
        # 窄屏模式
        index_width = 30
        checkbox_width = 30
        artwork_width = 40
        padding = 60  # 增加内边距考虑以防止溢出
        remaining_width = effective_width - index_width - checkbox_width - artwork_width - padding
        # 窄屏模式下进一步优化比例
        title_ratio = 0.38
        album_ratio = 0.24
        artist_ratio = 0.38
    elif viewport_width < 1000:
        # 中等宽度
        index_width = 30
        checkbox_width = 30
        artwork_width = 50
        padding = 70  # 增加内边距考虑
        remaining_width = effective_width - index_width - checkbox_width - artwork_width - padding
        title_ratio = 0.34
        album_ratio = 0.28
        artist_ratio = 0.38
    else:
        # 宽屏模式
        index_width = 30
        checkbox_width = 30
        artwork_width = 50
        padding = 80  # 增加内边距考虑
        remaining_width = effective_width - index_width - checkbox_width - artwork_width - padding
        title_ratio = 0.33
        album_ratio = 0.33
        artist_ratio = 0.34
    
    # 计算实际列宽 - 降低最小宽度以适应更小的窗口
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
    
    # 使用正确的方式记录日志，避免显示为logger工具类
    logger.debug(f"更新歌曲文本省略: 视口宽度={viewport_width}, 有效宽度={effective_width}, " +
                f"标题宽度={title_width}, 专辑宽度={album_width}, 艺术家宽度={artist_width}")
    
    # 遍历所有歌曲项
    for song_id, song_item in self.song_items.items():
        if hasattr(song_item, "title_label") and hasattr(song_item, "album_label") and hasattr(song_item, "artist_label"):
            # 获取标签和原始文本
            title_label = song_item.title_label
            album_label = song_item.album_label
            artist_label = song_item.artist_label
            
            original_title = song_item.track_data.get("name", "")
            original_album = song_item.track_data.get("album", "")
            original_artist = song_item.track_data.get("artist", "")
            
            # 获取字体度量对象
            metrics = QFontMetrics(title_label.font())
            
            # 应用文本省略 - 使用固定计算出的宽度，减去一个小的安全边距
            if original_title and len(original_title) > 0:
                elided_title = metrics.elidedText(original_title, Qt.ElideRight, title_width - 5)
                title_label.setText(elided_title)
            
            if original_album and len(original_album) > 0:
                elided_album = metrics.elidedText(original_album, Qt.ElideRight, album_width - 5)
                album_label.setText(elided_album)
            
            if original_artist and len(original_artist) > 0:
                elided_artist = metrics.elidedText(original_artist, Qt.ElideRight, artist_width - 5)
                artist_label.setText(elided_artist)
