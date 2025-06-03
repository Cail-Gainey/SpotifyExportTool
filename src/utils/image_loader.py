"""
图片异步加载工具
"""
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication
from src.utils.logger import logger
from src.utils.thread_manager import thread_manager  # 引入线程管理器

import requests
from io import BytesIO
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class ImageLoader(QThread):
    """图片加载线程"""
    # 修改信号定义，接受QImage或QPixmap
    image_loaded = pyqtSignal(object, str)
    load_failed = pyqtSignal(str)
    
    def __init__(self, image_url: str, track_id: str = None, cache_manager=None):
        """
        初始化图像加载器线程
        
        Args:
            image_url: 图像的URL
            track_id: 关联的曲目ID，用于缓存和日志记录
            cache_manager: 缓存管理器
        """
        super().__init__()
        self.image_url = image_url
        self.track_id = track_id or 'unknown'
        self.cache_manager = cache_manager
        
        # 防止线程过早终止
        self.setTerminationEnabled(False)
        
        # 确保线程在主线程中运行
        self.moveToThread(QApplication.instance().thread())
    
    def run(self):
        """
        图像加载的主方法
        """
        try:
            # 日志记录开始加载
            logger.debug(f"开始加载图像: URL={self.image_url}, TrackID={self.track_id}")
            
            # 检查URL有效性
            if not self.image_url or not self.image_url.startswith(('http://', 'https://')):
                logger.error(f"无效的图像URL: {self.image_url}")
                self.load_failed.emit(self.image_url)
                return

            # 设置重试策略
            retry_strategy = Retry(
                total=3,  # 总重试次数
                backoff_factor=0.5,  # 重试间隔指数退避
                status_forcelist=[429, 500, 502, 503, 504]  # 需要重试的状态码
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session = requests.Session()
            session.mount('http://', adapter)
            session.mount('https://', adapter)

            # 尝试从缓存加载
            if self.cache_manager:
                # 根据URL确定图像类型
                image_type = 'avatar' if 'user_avatar' in str(self.track_id) else 'track'
                cached_image = self.cache_manager.get_cached_image(self.image_url, image_type)
                
                if cached_image:
                    logger.debug(f"从缓存加载图像成功: {self.image_url}")
                    # 转换为QPixmap并发送
                    pixmap = QPixmap.fromImage(cached_image)
                    self.image_loaded.emit(pixmap, self.track_id)
                    return

            # 下载图像，增加超时和重试
            response = session.get(
                self.image_url, 
                timeout=(5, 10),  # 连接超时5秒，读取超时10秒
                stream=True  # 流式下载，减少内存占用
            )
            response.raise_for_status()
            
            # 读取图像数据
            image_data = response.content
            
            # 创建 QPixmap
            pixmap = QPixmap()
            pixmap.loadFromData(image_data)
            
            # 检查图像是否有效
            if pixmap.isNull():
                logger.warning(f"无效的图像数据: {self.image_url}")
                self.load_failed.emit(self.image_url)
                return
            
            # 缓存图像
            if self.cache_manager:
                # 根据URL确定图像类型
                image_type = 'avatar' if 'user_avatar' in str(self.track_id) else 'track'
                self.cache_manager.cache_image(self.image_url, image_data, image_type)
            
            # 发送成功信号
            self.image_loaded.emit(pixmap, self.track_id)
            
            logger.debug(f"图像加载成功: URL={self.image_url}, TrackID={self.track_id}")
        
        except requests.RequestException as e:
            logger.error(f"图像下载失败: URL={self.image_url}, 错误={str(e)}")
            self.load_failed.emit(self.image_url)
        
        except Exception as e:
            logger.error(f"图像加载发生未知错误: URL={self.image_url}, 错误={str(e)}")
            self.load_failed.emit(self.image_url)
        
        finally:
            # 确保线程退出
            self.quit()
    
    def cancel(self):
        """取消图像加载"""
        self.requestInterruption()
    
    def __del__(self):
        """确保线程安全退出"""
        try:
            self.cancel()
            self.wait(1000)  # 等待线程结束
        except Exception as e:
            logger.error(f"ImageLoader 销毁时发生错误: {str(e)}")

def load_image_async(url, track_id, cache_manager=None, on_loaded=None):
    """
    异步加载图片的便捷函数
    
    Args:
        url: 图片URL
        track_id: 唯一标识符
        cache_manager: 缓存管理器
        on_loaded: 图片加载完成的回调函数
    
    Returns:
        ImageLoader线程实例
    """
    # 创建图片加载线程
    image_loader = ImageLoader(url, track_id, cache_manager)
    
    # 如果提供了回调函数，连接信号
    if on_loaded:
        image_loader.image_loaded.connect(on_loaded)
    
    # 使用线程管理器注册线程
    thread_manager.register_thread(image_loader, 'image_loader')
    
    # 启动线程
    image_loader.start()
    
    return image_loader 