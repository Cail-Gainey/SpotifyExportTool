"""
语言管理器
"""
import os
import json
import sys
import locale
from PyQt5.QtCore import QObject, pyqtSignal
from src.config import settings
import logging

logger = logging.getLogger(__name__)

class LanguageManager(QObject):
    """语言管理器类"""
    
    # 语言变更信号
    language_changed = pyqtSignal(str)
    
    # 单例实例
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LanguageManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        super().__init__()
        self._initialized = True
        
        # 获取程序运行目录
        if getattr(sys, 'frozen', False):
            # 如果是打包后的可执行文件
            self.base_dir = os.path.dirname(sys.executable)
        else:
            # 如果是直接运行脚本
            self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # 语言文件目录
        self.locale_dir = os.path.join(self.base_dir, 'locale')
        
        # 支持的语言列表
        self.supported_languages = ['zh_CN', 'en_US']
        
        # 默认语言
        self.default_language = 'zh_CN'
        
        # 当前语言
        self.current_language = None
        
        # 翻译数据
        self.translations = {}
        
        # 加载翻译
        self._load_translations()
        
        # 设置初始语言
        self._load_language_from_settings()
    
    def _load_translations(self):
        """加载所有支持的语言翻译"""
        for lang in self.supported_languages:
            # 尝试多个可能的路径
            file_paths = [
                os.path.join(self.locale_dir, f'{lang}.json'),  # 标准路径
                os.path.join(self.base_dir, 'locale', f'{lang}.json'),  # 根目录下的locale
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'locale', f'{lang}.json')  # 相对于当前文件的路径
            ]
            
            loaded = False
            for file_path in file_paths:
                try:
                    if os.path.exists(file_path):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            self.translations[lang] = json.load(f)
                            logger.debug(f"成功加载语言文件: {file_path}")
                            loaded = True
                            break
                except Exception as e:
                    logger.error(f"尝试加载语言文件失败 {lang} 从 {file_path}: {str(e)}")
            
            if not loaded:
                logger.error(f"无法加载语言文件 {lang}，尝试了以下路径: {file_paths}")
                # 如果加载失败，使用空字典
                self.translations[lang] = {}
    
    def _load_language_from_settings(self):
        """从设置中加载语言偏好"""
        # 获取设置中的语言选项
        language_setting = settings.get_setting('language', 'auto')
        
        if language_setting == 'auto':
            # 内部使用系统语言，但保持设置值为'auto'
            system_lang = self._get_system_detected_language()
            self.current_language = system_lang
            # 不发送信号，因为这是初始化
        else:
            if language_setting in self.supported_languages:
                self.current_language = language_setting
            else:
                self.current_language = self.default_language
    
    def _get_system_detected_language(self):
        """获取系统检测到的语言"""
        try:
            system_locale = locale.getdefaultlocale()[0]
            
            # 如果系统语言是中文
            if system_locale and (system_locale.startswith('zh_') or system_locale.startswith('zh-')):
                return 'zh_CN'
                
            # 如果系统语言是英文
            if system_locale and (system_locale.startswith('en_') or system_locale.startswith('en-')):
                return 'en_US'
                
            # 对于其他不支持的语言，返回默认语言
            return self.default_language
        except Exception as e:
            logger.error(f"检测系统语言失败: {str(e)}")
            return self.default_language
    
    def set_language(self, language_code):
        """
        设置当前语言
        :param language_code: 语言代码 (zh_CN, en_US) 或 'auto'
        """
        # 防止递归调用
        if hasattr(self, '_is_setting_language') and self._is_setting_language:
            logger.warning("检测到递归调用set_language，已跳过")
            return
            
        # 设置递归保护标志
        self._is_setting_language = True
        
        try:
            # 处理自动选项
            if language_code == 'auto':
                # 保存设置为'auto'
                try:
                    settings.set_setting('language', 'auto')
                except Exception as e:
                    logger.error(f"保存语言设置失败: {str(e)}")
                    
                # 使用系统检测的语言
                system_lang = self._get_system_detected_language()
                # 仅在内部使用实际语言
                if self.current_language != system_lang:
                    self.current_language = system_lang
                    self.language_changed.emit(system_lang)
                return
            
            # 处理明确指定的语言
            if language_code not in self.supported_languages:
                language_code = self.default_language
                
            if self.current_language != language_code:
                self.current_language = language_code
                # 保存到设置
                try:
                    settings.set_setting('language', language_code)
                except Exception as e:
                    logger.error(f"保存语言设置失败: {str(e)}")
                    
                # 发送语言变更信号
                self.language_changed.emit(language_code)
        finally:
            # 重置递归保护标志
            self._is_setting_language = False
    
    def get_text(self, key, default=''):
        """
        获取指定键的翻译文本
        :param key: 点分隔的键，如'login.btn_login'
        :param default: 如果未找到翻译，返回该默认值
        :return: 翻译文本
        """
        if not self.current_language:
            logger.debug(f"当前语言未设置，返回默认值: {default}")
            return default
            
        # 获取当前语言的翻译
        translations = self.translations.get(self.current_language, {})
        
        # 分割键路径
        keys = key.split('.')
        
        # 获取嵌套结构中的值
        value = translations
        for i, k in enumerate(keys):
            if isinstance(value, dict) and k in value:
                value = value[k]
                # 如果是最后一个键且值是字典，则返回默认值
                if i == len(keys) - 1 and isinstance(value, dict):
                    logger.warning(f"翻译键 '{key}' 返回了字典而不是字符串: {value}")
                    return default
            else:
                logger.debug(f"在翻译中找不到键 '{k}' (完整键: '{key}')，返回默认值: {default}")
                return default
        
        # 确保返回的是字符串
        if isinstance(value, dict):
            logger.warning(f"翻译键 '{key}' 返回了字典而不是字符串: {value}")
            return default
        elif value is None:
            logger.debug(f"翻译键 '{key}' 的值为None，返回默认值: {default}")
            return default
        
        # 转换为字符串并返回
        result = str(value) if value else default
        logger.debug(f"翻译键 '{key}' 返回值: {result}")
        return result
    
    def get_current_language(self):
        """获取当前语言代码"""
        return self.current_language
    
    def get_supported_languages(self):
        """获取支持的语言列表"""
        return self.supported_languages 