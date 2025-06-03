"""
播放列表视图的线程加载类
"""

import requests
from io import BytesIO
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from PyQt5.QtGui import QImage
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from src.utils.logger import logger


class SongLoader(QThread):
    """歌曲加载线程，负责从Spotify API或缓存加载歌曲"""

    songs_loaded = pyqtSignal(list, bool)  # 第二个参数表示是否是从缓存加载的
    load_error = pyqtSignal(str)

    def __init__(self, sp, playlist_id, cache_manager, force_refresh=False):
        """
        初始化歌曲加载线程

        :param sp: Spotify API客户端
        :param playlist_id: 播放列表ID
        :param cache_manager: 缓存管理器
        :param force_refresh: 是否强制刷新（忽略缓存）
        """
        super().__init__()
        self.sp = sp
        self.playlist_id = playlist_id
        self.cache_manager = cache_manager
        self.force_refresh = force_refresh  # 是否强制刷新，不使用缓存
        self._is_running = True
        
    def stop(self):
        """安全停止线程"""
        self._is_running = False
        
    def quit(self):
        """重写quit方法"""
        self.stop()
        super().quit()
        
    def terminate(self):
        """重写terminate方法"""
        self.stop()
        super().terminate()

    def run(self):
        """执行歌曲加载任务"""
        try:
            logger.debug(
                f"开始加载播放列表: {self.playlist_id}，强制刷新: {self.force_refresh}"
            )
            
            # 检查是否已经停止
            if not self._is_running:
                logger.debug(f"歌曲加载被取消: {self.playlist_id}")
                return

            # 如果不是强制刷新，首先尝试从缓存加载
            if not self.force_refresh:
                cached_tracks = self.cache_manager.get_cached_tracks(self.playlist_id)
                if cached_tracks:
                    logger.info(
                        f"成功从缓存加载播放列表: {self.playlist_id}, 共{len(cached_tracks)}首歌曲"
                    )
                    # 发送加载完成信号，并标记为从缓存加载
                    self.songs_loaded.emit(cached_tracks, True)
                    return
                logger.info(f"缓存中未找到播放列表或缓存已过期: {self.playlist_id}")
            else:
                logger.info(f"强制从API刷新播放列表: {self.playlist_id}")
                
            # 检查是否已经停止
            if not self._is_running:
                logger.debug(f"歌曲加载被取消: {self.playlist_id}")
                return

            # 如果没有缓存或强制刷新，从API加载
            tracks = []
            logger.info(f"开始从API加载播放列表: {self.playlist_id}")
            results = self.sp.playlist_tracks(self.playlist_id)

            # 添加原始索引
            for i, item in enumerate(results["items"]):
                item["original_index"] = i + 1
                tracks.append(item)
                
            # 检查是否已经停止
            if not self._is_running:
                logger.debug(f"歌曲加载被取消: {self.playlist_id}")
                return

            while results["next"]:
                logger.info(f"加载更多播放列表歌曲，当前已加载: {len(tracks)}首")
                results = self.sp.next(results)
                for i, item in enumerate(results["items"], len(tracks) + 1):
                    item["original_index"] = i
                    tracks.append(item)
                    
                # 检查是否已经停止
                if not self._is_running:
                    logger.debug(f"歌曲加载被取消: {self.playlist_id}")
                    return

            # 缓存歌曲列表
            logger.info(
                f"播放列表加载完成，准备缓存: {self.playlist_id}, 共{len(tracks)}首歌曲"
            )
            self.cache_manager.cache_tracks(self.playlist_id, tracks)

            # 发送加载完成信号，并标记为从API加载
            logger.info(f"从API加载播放列表完成: {self.playlist_id}")
            self.songs_loaded.emit(tracks, False)

        except Exception as e:
            logger.error(f"加载歌曲失败: {str(e)}")
            import traceback

            logger.error(traceback.format_exc())
            self.load_error.emit(str(e))

    def _process_track_data(self, track_item, total_tracks):
        """
        处理Spotify API返回的track数据，提取出需要的信息
        
        Args:
            track_item: Spotify API返回的track数据项
            total_tracks: 总歌曲数，用于处理最后一首歌曲的索引
            
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
            
            # 获取当前项的索引
            current_index = track_item.get('original_index', 0)
            
            # 如果索引为0，并且提供了总歌曲数，使用总歌曲数作为最后一首歌曲的索引
            if current_index == 0 and total_tracks > 0:
                current_index = total_tracks
            
            # 构造我们需要的数据结构
            processed_track = {
                'id': track_id,
                'name': track_name,
                'album': album_name,
                'artist': artist_name,
                'image_url': image_url,
                'original_index': current_index,  # 使用计算后的索引
                'raw_data': track  # 保留原始数据，以防后续需要
            }
            
            return processed_track
        except Exception as e:
            logger.error(f"处理歌曲数据失败: {str(e)}")
            # 返回一个默认的数据结构
            return {
                'id': f"error_{hash(str(track_item))}",
                'name': '处理错误',
                'album': '未知专辑',
                'artist': '未知艺术家',
                'image_url': '',
                'original_index': 0
            }

    def load_tracks(self, playlist_id, force_refresh=False):
        """
        加载播放列表中的所有歌曲
        
        Args:
            playlist_id: 播放列表ID
            force_refresh: 是否强制刷新缓存
        
        Returns:
            list: 处理后的歌曲列表
        """
        try:
            logger.debug(f"开始加载播放列表: {playlist_id}，强制刷新: {force_refresh}")
            
            # 尝试从缓存加载
            if not force_refresh:
                cached_tracks = self.cache_manager.get_playlist_tracks(playlist_id)
                if cached_tracks:
                    logger.info(f"成功从缓存加载播放列表: {playlist_id}, 共{len(cached_tracks)}首歌曲")
                    return cached_tracks
            
            # 从Spotify API获取歌曲
            tracks = []
            results = self.sp.playlist_tracks(playlist_id, limit=100)
            total_tracks = results['total']
            
            # 处理第一批歌曲
            for i, item in enumerate(results['items'], 1):
                processed_track = self._process_track_data(item, total_tracks)
                processed_track['original_index'] = i
                tracks.append(processed_track)
            
            # 处理分页
            while results['next']:
                results = self.sp.next(results)
                for i, item in enumerate(results['items'], len(tracks) + 1):
                    processed_track = self._process_track_data(item, total_tracks)
                    processed_track['original_index'] = i
                    tracks.append(processed_track)
            
            # 缓存歌曲列表
            self.cache_manager.cache_playlist_tracks(playlist_id, tracks)
            
            logger.info(f"成功加载播放列表: {playlist_id}, 共{len(tracks)}首歌曲")
            return tracks
        
        except Exception as e:
            logger.error(f"加载播放列表 {playlist_id} 失败: {str(e)}")
            self.load_error.emit(str(e))
            return []


class ImageLoader(QThread):
    """图像加载线程，负责从网络或缓存加载图片"""

    image_loaded = pyqtSignal(QImage, str)  # 发送图片和track ID

    def __init__(self, url, track_id, cache_manager):
        """
        初始化图像加载线程

        :param url: 图像URL
        :param track_id: 歌曲ID或标识符
        :param cache_manager: 缓存管理器
        """
        super().__init__()
        self.url = url
        self.track_id = track_id
        self.cache_manager = cache_manager
        self.session = None
        self._is_running = True
        
    def stop(self):
        """安全停止线程"""
        self._is_running = False
        
    def quit(self):
        """重写quit方法"""
        self.stop()
        super().quit()
        
    def terminate(self):
        """重写terminate方法"""
        self.stop()
        super().terminate()

    def run(self):
        """执行图像加载任务"""
        try:
            # 输出详细日志，帮助调试
            # logger.debug(
            #     f"正在加载图片: {self.url} 类型: {'playlist' if self.track_id == 'playlist_cover' else 'track'}"
            # )
            
            # 检查是否已经停止
            if not self._is_running:
                logger.debug(f"图片加载被取消: {self.url}")
                return

            # 确定图片类型
            image_type = "playlist" if self.track_id == "playlist_cover" else "track"

            # 首先尝试从缓存加载
            cached_image = self.cache_manager.get_cached_image(self.url, image_type)
            if cached_image and not cached_image.isNull():
                # logger.debug(f"图片已从缓存加载: {self.url}")
                self.image_loaded.emit(cached_image, self.track_id)
                return
                
            # 检查是否已经停止
            if not self._is_running:
                logger.debug(f"图片加载被取消: {self.url}")
                return

            # 如果没有缓存，从网络加载
            # logger.debug(f"从网络加载图片: {self.url}")

            # 检查URL是否有效
            if not self.url or not self.url.startswith("http"):
                logger.error(f"无效的图片URL: {self.url}")
                self._emit_empty_image()
                return

            # 创建会话并设置重试机制
            if not self.session:
                self.session = requests.Session()
                retries = Retry(total=3, backoff_factor=0.5)
                self.session.mount("https://", HTTPAdapter(max_retries=retries))
                
            # 检查是否已经停止
            if not self._is_running:
                logger.debug(f"图片加载被取消: {self.url}")
                return

            # 设置超时时间
            response = self.session.get(self.url, timeout=10)
            response.raise_for_status()

            # 加载图片
            img_data = BytesIO(response.content)
            image = QImage()
            load_success = image.loadFromData(img_data.getvalue())

            # 检查图片是否有效
            if not load_success or image.isNull():
                logger.debug(f"加载的图片无效: {self.url}")
                self._emit_empty_image()
                return
                
            # 检查是否已经停止
            if not self._is_running:
                logger.debug(f"图片加载被取消: {self.url}")
                return

            # logger.debug(
            #     f"图片加载成功: {self.url}, 大小: {image.width()}x{image.height()}"
            # )

            # 缓存图片
            try:
                self.cache_manager.cache_image(self.url, image, image_type)
                # logger.debug(f"图片已缓存: {self.url}")
            except Exception as cache_err:
                logger.error(f"缓存图片失败: {str(cache_err)}")
                # 缓存失败不影响继续使用图片

            # 发送信号
            self.image_loaded.emit(image, self.track_id)

        except requests.exceptions.RequestException as req_err:
            logger.error(f"网络请求错误: {self.url} - {str(req_err)}")
            self._emit_empty_image()
        except Exception as e:
            import traceback

            logger.error(f"加载图片失败: {self.url} - {str(e)}")
            logger.error(traceback.format_exc())  # 打印更详细的错误信息
            self._emit_empty_image()
        finally:
            # 关闭会话
            if self.session:
                try:
                    self.session.close()
                except:
                    pass
            self.session = None

    def _emit_empty_image(self):
        """创建并发送空图片"""
        empty_image = QImage(100, 100, QImage.Format_ARGB32)
        empty_image.fill(Qt.transparent)
        self.image_loaded.emit(empty_image, self.track_id)
