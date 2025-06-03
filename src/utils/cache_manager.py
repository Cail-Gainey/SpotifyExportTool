"""
缓存管理器
"""
import os
import json
import sys
from datetime import datetime, timedelta
from PyQt5.QtGui import QImage
import hashlib
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    """缓存管理器"""
    
    def __init__(self):
        # 获取程序运行目录
        base_dir = self.get_base_dir()
        
        # 缓存目录
        self.cache_dir = os.path.join(base_dir, 'cache')
        self.playlists_cache_file = os.path.join(self.cache_dir, 'playlists.json')
        self.tracks_cache_dir = os.path.join(self.cache_dir, 'tracks')
        self.images_cache_dir = os.path.join(self.cache_dir, 'images')
        self.avatar_cache_dir = os.path.join(self.images_cache_dir, 'avatars')
        self.playlist_cover_cache_dir = os.path.join(self.images_cache_dir, 'playlists')
        self.track_cover_cache_dir = os.path.join(self.images_cache_dir, 'tracks')
        
        # 确保缓存目录存在
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.tracks_cache_dir, exist_ok=True)
        os.makedirs(self.images_cache_dir, exist_ok=True)
        os.makedirs(self.avatar_cache_dir, exist_ok=True)
        os.makedirs(self.playlist_cover_cache_dir, exist_ok=True)
        os.makedirs(self.track_cover_cache_dir, exist_ok=True)
        
        # 更新缓存过期时间: 歌单24小时, 歌曲12小时, 图片7天
        self.playlists_cache_expiry = timedelta(hours=24)
        self.tracks_cache_expiry = timedelta(hours=12)
        self.images_cache_expiry = timedelta(days=7)
        
        # 缓存刷新频率（单位：秒）
        self.refresh_interval = 3600  # 1小时
        
        # 缓存状态
        self.cache_status = {
            'playlists': {'last_update': None, 'error': None},
            'tracks': {},
            'images': {
                'avatars': {},
                'playlists': {},
                'tracks': {}
            }
        }
    
    def get_base_dir(self):
        """
        获取应用程序的基础目录
        
        考虑PyInstaller打包后的环境，确保在开发和生产环境中都能正确找到资源
        """
        try:
            # 检查是否在PyInstaller环境中
            if getattr(sys, 'frozen', False):
                # 在PyInstaller中，使用可执行文件所在目录
                base_path = os.path.dirname(sys.executable)
            else:
                # 在开发环境中，使用项目根目录（不是src目录）
                # 从src/utils向上三级到达项目根目录
                base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            # 打印出基础目录，便于调试
            logger.info(f"缓存管理器基础目录: {base_path}")
            return base_path
        except Exception as e:
            logger.error(f"获取基础目录失败: {str(e)}")
            # 如果出错，回退到当前目录
            return os.path.abspath(".")
    
    def get_cached_playlists(self, user_id):
        """
        获取缓存的歌单列表
        :param user_id: 用户ID
        :return: 缓存的歌单列表，如果没有缓存或已过期则返回None
        """
        try:
            if not os.path.exists(self.playlists_cache_file):
                return None
            
            with open(self.playlists_cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # 检查是否是当前用户的缓存
            if cache_data.get('user_id') != user_id:
                return None
            
            # 检查缓存是否过期
            cache_time = datetime.fromisoformat(cache_data['timestamp'])
            if datetime.now() - cache_time > self.playlists_cache_expiry:
                return None
            
            # 更新缓存状态
            self.cache_status['playlists']['last_update'] = cache_time
            self.cache_status['playlists']['error'] = None
            
            return cache_data['playlists']
            
        except Exception as e:
            logger.error(f"读取歌单缓存失败: {str(e)}")
            self.cache_status['playlists']['error'] = str(e)
            return None
    
    def should_refresh_playlists(self, user_id):
        """
        检查是否应该刷新歌单缓存
        :param user_id: 用户ID
        :return: 如果应该刷新返回True，否则返回False
        """
        try:
            if not os.path.exists(self.playlists_cache_file):
                return True
            
            with open(self.playlists_cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # 检查是否是当前用户的缓存
            if cache_data.get('user_id') != user_id:
                return True
            
            # 检查缓存是否应该刷新
            cache_time = datetime.fromisoformat(cache_data['timestamp'])
            if datetime.now() - cache_time > timedelta(seconds=self.refresh_interval):
                return True
            
            return False
            
        except Exception:
            return True
    
    def cache_playlists(self, user_id, playlists):
        """
        缓存歌单列表
        :param user_id: 用户ID
        :param playlists: 歌单列表
        """
        try:
            cache_data = {
                'user_id': user_id,
                'timestamp': datetime.now().isoformat(),
                'playlists': playlists
            }
            
            with open(self.playlists_cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            # 更新缓存状态
            self.cache_status['playlists']['last_update'] = datetime.now()
            self.cache_status['playlists']['error'] = None
                
        except Exception as e:
            logger.error(f"保存歌单缓存失败: {str(e)}")
            self.cache_status['playlists']['error'] = str(e)
    
    def get_cached_image(self, url, image_type='playlist'):
        """
        获取缓存的图片
        :param url: 图片URL
        :param image_type: 图片类型，可选值：'avatar', 'playlist', 'track'
        :return: 缓存的QImage对象，如果没有缓存则返回None
        """
        try:
            # 根据图片类型选择缓存目录
            cache_dir = self._get_image_cache_dir(image_type)
            
            # 使用URL的哈希作为文件名
            filename = hashlib.md5(url.encode()).hexdigest() + '.png'
            cache_file = os.path.join(cache_dir, filename)
            
            if not os.path.exists(cache_file):
                return None
            
            # 检查文件修改时间是否过期
            mtime = datetime.fromtimestamp(os.path.getmtime(cache_file))
            if datetime.now() - mtime > self.images_cache_expiry:
                return None
            
            # 加载图片
            image = QImage()
            if image.load(cache_file):
                # 更新缓存状态
                if url not in self.cache_status['images'][image_type + 's']:
                    self.cache_status['images'][image_type + 's'][url] = {}
                self.cache_status['images'][image_type + 's'][url]['last_update'] = mtime
                self.cache_status['images'][image_type + 's'][url]['error'] = None
                return image
            return None
            
        except Exception as e:
            logger.error(f"读取图片缓存失败: {str(e)}")
            if url not in self.cache_status['images'][image_type + 's']:
                self.cache_status['images'][image_type + 's'][url] = {}
            self.cache_status['images'][image_type + 's'][url]['error'] = str(e)
            return None
    
    def cache_image(self, url, image, image_type='playlist'):
        """
        缓存图片
        :param url: 图片URL
        :param image: QImage对象
        :param image_type: 图片类型，可选值：'avatar', 'playlist', 'track'
        """
        try:
            # 根据图片类型选择缓存目录
            cache_dir = self._get_image_cache_dir(image_type)
            
            # 使用URL的哈希作为文件名
            filename = hashlib.md5(url.encode()).hexdigest() + '.png'
            cache_file = os.path.join(cache_dir, filename)
            
            # 保存图片
            image.save(cache_file, 'PNG')
            
            # 更新缓存状态
            if url not in self.cache_status['images'][image_type + 's']:
                self.cache_status['images'][image_type + 's'][url] = {}
            self.cache_status['images'][image_type + 's'][url]['last_update'] = datetime.now()
            self.cache_status['images'][image_type + 's'][url]['error'] = None
                
        except Exception as e:
            logger.error(f"保存图片缓存失败: {str(e)}")
            if url not in self.cache_status['images'][image_type + 's']:
                self.cache_status['images'][image_type + 's'][url] = {}
            self.cache_status['images'][image_type + 's'][url]['error'] = str(e)
    
    def _get_image_cache_dir(self, image_type):
        """
        根据图片类型获取对应的缓存目录
        :param image_type: 图片类型
        :return: 缓存目录路径
        """
        if image_type == 'avatar':
            return self.avatar_cache_dir
        elif image_type == 'playlist':
            return self.playlist_cover_cache_dir
        elif image_type == 'track':
            return self.track_cover_cache_dir
        else:
            return self.images_cache_dir
    
    def get_cached_tracks(self, playlist_id):
        """
        获取缓存的歌曲列表
        :param playlist_id: 歌单ID
        :return: 缓存的歌曲列表，如果没有缓存或已过期则返回None
        """
        try:
            cache_file = os.path.join(self.tracks_cache_dir, f'{playlist_id}.json')
            if not os.path.exists(cache_file):
                return None
            
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # 检查缓存是否过期
            cache_time = datetime.fromisoformat(cache_data['timestamp'])
            if datetime.now() - cache_time > self.tracks_cache_expiry:
                return None
            
            # 更新缓存状态
            if playlist_id not in self.cache_status['tracks']:
                self.cache_status['tracks'][playlist_id] = {}
            self.cache_status['tracks'][playlist_id]['last_update'] = cache_time
            self.cache_status['tracks'][playlist_id]['error'] = None
            
            return cache_data['tracks']
            
        except Exception as e:
            logger.error(f"读取歌曲缓存失败: {str(e)}")
            if playlist_id not in self.cache_status['tracks']:
                self.cache_status['tracks'][playlist_id] = {}
            self.cache_status['tracks'][playlist_id]['error'] = str(e)
            return None
    
    def should_refresh_tracks(self, playlist_id):
        """
        检查是否应该刷新歌曲缓存
        :param playlist_id: 歌单ID
        :return: 如果应该刷新返回True，否则返回False
        """
        try:
            cache_file = os.path.join(self.tracks_cache_dir, f'{playlist_id}.json')
            if not os.path.exists(cache_file):
                return True
            
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # 检查缓存是否应该刷新
            cache_time = datetime.fromisoformat(cache_data['timestamp'])
            if datetime.now() - cache_time > timedelta(seconds=self.refresh_interval):
                return True
            
            return False
            
        except Exception:
            return True
    
    def cache_tracks(self, playlist_id, tracks):
        """
        缓存歌曲列表
        :param playlist_id: 歌单ID
        :param tracks: 歌曲列表
        """
        try:
            cache_file = os.path.join(self.tracks_cache_dir, f'{playlist_id}.json')
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'tracks': tracks
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            # 更新缓存状态
            if playlist_id not in self.cache_status['tracks']:
                self.cache_status['tracks'][playlist_id] = {}
            self.cache_status['tracks'][playlist_id]['last_update'] = datetime.now()
            self.cache_status['tracks'][playlist_id]['error'] = None
                
        except Exception as e:
            logger.error(f"保存歌曲缓存失败: {str(e)}")
            if playlist_id not in self.cache_status['tracks']:
                self.cache_status['tracks'][playlist_id] = {}
            self.cache_status['tracks'][playlist_id]['error'] = str(e)
    
    def get_cache_timestamp(self, cache_type, id_or_url):
        """
        获取缓存的时间戳
        :param cache_type: 缓存类型，'playlists', 'tracks', or 'image'
        :param id_or_url: 歌单ID, 歌曲ID, 或图片URL
        :return: 时间戳（datetime对象），如果缓存不存在则返回None
        """
        try:
            if cache_type == 'playlists':
                if not os.path.exists(self.playlists_cache_file):
                    return None
                
                with open(self.playlists_cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                # 检查是否是当前用户的缓存
                if cache_data.get('user_id') != id_or_url:
                    return None
                
                return datetime.fromisoformat(cache_data['timestamp'])
                
            elif cache_type == 'tracks':
                cache_file = os.path.join(self.tracks_cache_dir, f'{id_or_url}.json')
                if not os.path.exists(cache_file):
                    return None
                
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                return datetime.fromisoformat(cache_data['timestamp'])
                
            elif cache_type == 'image':
                # 使用URL的哈希作为文件名
                filename = hashlib.md5(id_or_url.encode()).hexdigest() + '.png'
                cache_file = os.path.join(self.images_cache_dir, filename)
                
                if not os.path.exists(cache_file):
                    return None
                
                # 返回文件修改时间
                return datetime.fromtimestamp(os.path.getmtime(cache_file))
                
            return None
            
        except Exception as e:
            logger.error(f"获取缓存时间戳失败: {str(e)}")
            return None
    
    def clear_expired_cache(self):
        """清理过期的缓存文件"""
        try:
            # 清理过期的图片缓存
            now = datetime.now()
            for cache_dir in [self.avatar_cache_dir, self.playlist_cover_cache_dir, self.track_cover_cache_dir]:
                for filename in os.listdir(cache_dir):
                    file_path = os.path.join(cache_dir, filename)
                    if datetime.fromtimestamp(os.path.getmtime(file_path)) + self.images_cache_expiry < now:
                        os.remove(file_path)
            
            # 清理过期的歌单缓存
            if os.path.exists(self.playlists_cache_file):
                with open(self.playlists_cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                cache_time = datetime.fromisoformat(cache_data['timestamp'])
                if now - cache_time > self.playlists_cache_expiry:
                    os.remove(self.playlists_cache_file)
            
            # 清理过期的歌曲缓存
            for filename in os.listdir(self.tracks_cache_dir):
                file_path = os.path.join(self.tracks_cache_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    
                    cache_time = datetime.fromisoformat(cache_data['timestamp'])
                    if now - cache_time > self.tracks_cache_expiry:
                        os.remove(file_path)
                except:
                    # 如果文件格式错误，直接删除
                    os.remove(file_path)
                    
        except Exception as e:
            logger.error(f"清理缓存失败: {str(e)}")
    
    def clear_all_cache(self):
        """清理所有缓存"""
        try:
            # 删除所有图片缓存
            for cache_dir in [self.avatar_cache_dir, self.playlist_cover_cache_dir, self.track_cover_cache_dir]:
                for filename in os.listdir(cache_dir):
                    os.remove(os.path.join(cache_dir, filename))
            
            # 删除所有歌曲缓存
            for filename in os.listdir(self.tracks_cache_dir):
                os.remove(os.path.join(self.tracks_cache_dir, filename))
            
            # 删除歌单缓存
            if os.path.exists(self.playlists_cache_file):
                os.remove(self.playlists_cache_file)
            
            # 重置缓存状态
            self.cache_status = {
                'playlists': {'last_update': None, 'error': None},
                'tracks': {},
                'images': {
                    'avatars': {},
                    'playlists': {},
                    'tracks': {}
                }
            }
                
        except Exception as e:
            logger.error(f"清理所有缓存失败: {str(e)}")
    
    def get_cache_status(self):
        """
        获取缓存状态
        :return: 缓存状态字典
        """
        return self.cache_status 