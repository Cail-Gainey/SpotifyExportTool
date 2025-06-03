"""
线程管理工具，用于统一管理和控制应用程序中的线程
"""
import threading
from typing import List, Dict, Any, Callable
from src.utils.logger import logger

class ThreadManager:
    """
    全局线程管理器，提供线程生命周期管理和安全退出机制
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """单例模式实现"""
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._init()
        return cls._instance

    def _init(self):
        """初始化方法"""
        self._active_threads: Dict[str, List[threading.Thread]] = {}
        self._thread_cleanup_lock = threading.Lock()

    def register_thread(self, thread: threading.Thread, category: str = 'default'):
        """
        注册线程到管理器
        
        Args:
            thread: 要注册的线程
            category: 线程分类，默认为'default'
        """
        with self._thread_cleanup_lock:
            if category not in self._active_threads:
                self._active_threads[category] = []
            
            # 设置为守护线程
            if hasattr(thread, 'daemon'):
                thread.daemon = True
            
            # 注册线程
            self._active_threads[category].append(thread)
            logger.debug(f"注册线程: {thread} 到分类 {category}")

    def unregister_thread(self, thread: threading.Thread, category: str = 'default'):
        """
        从管理器中注销线程
        
        Args:
            thread: 要注销的线程
            category: 线程分类，默认为'default'
        """
        with self._thread_cleanup_lock:
            if category in self._active_threads and thread in self._active_threads[category]:
                self._active_threads[category].remove(thread)
                logger.debug(f"注销线程: {thread} 从分类 {category}")

    def stop_threads(self, category: str = None):
        """
        停止指定分类或所有线程
        
        Args:
            category: 要停止的线程分类，为None时停止所有线程
        """
        with self._thread_cleanup_lock:
            categories = [category] if category else list(self._active_threads.keys())
            
            for cat in categories:
                if cat in self._active_threads:
                    threads = self._active_threads[cat].copy()
                    for thread in threads:
                        try:
                            # 检查线程是否有 is_alive 方法
                            is_alive_method = getattr(thread, 'is_alive', getattr(thread, 'isRunning', None))
                            
                            if is_alive_method and is_alive_method():
                                logger.debug(f"尝试停止线程: {thread} 在分类 {cat}")
                                
                                # 对于QThread，使用quit()方法
                                if hasattr(thread, 'quit'):
                                    thread.quit()
                                
                                # 对于普通线程，使用_stop属性（不推荐，仅作为最后手段）
                                elif hasattr(thread, '_stop'):
                                    thread._stop()
                                
                                # 等待线程结束
                                if hasattr(thread, 'wait'):
                                    thread.wait(1000)  # 等待1秒
                                elif hasattr(thread, 'join'):
                                    thread.join(timeout=1)
                        except Exception as e:
                            logger.error(f"停止线程时发生错误: {str(e)}")
                    
                    # 清空该分类的线程列表
                    self._active_threads[cat].clear()

    def get_active_threads(self, category: str = None) -> List[threading.Thread]:
        """
        获取活跃线程列表
        
        Args:
            category: 线程分类，为None时返回所有活跃线程
        
        Returns:
            活跃线程列表
        """
        with self._thread_cleanup_lock:
            if category:
                return self._active_threads.get(category, [])
            
            # 返回所有分类的线程
            all_threads = []
            for threads in self._active_threads.values():
                all_threads.extend(threads)
            
            return all_threads

    def safe_thread_run(self, 
                         target: Callable, 
                         category: str = 'default', 
                         *args: Any, 
                         **kwargs: Any) -> threading.Thread:
        """
        安全地创建并启动线程
        
        Args:
            target: 线程执行的目标函数
            category: 线程分类
            *args: 传递给目标函数的位置参数
            **kwargs: 传递给目标函数的关键字参数
        
        Returns:
            创建的线程对象
        """
        def wrapped_target(*args, **kwargs):
            try:
                return target(*args, **kwargs)
            except Exception as e:
                logger.error(f"线程执行错误: {str(e)}")
            finally:
                # 线程结束时自动注销
                current_thread = threading.current_thread()
                self.unregister_thread(current_thread, category)
        
        thread = threading.Thread(target=wrapped_target, args=args, kwargs=kwargs)
        thread.daemon = True  # 设置为守护线程
        
        # 注册线程
        self.register_thread(thread, category)
        
        # 启动线程
        thread.start()
        
        return thread

# 创建全局单例
thread_manager = ThreadManager() 