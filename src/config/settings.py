"""
应用程序设置管理
"""
import os
import json
import sys

# 获取程序运行目录
if getattr(sys, 'frozen', False):
    # 如果是打包后的可执行文件
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # 如果是直接运行脚本
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置文件路径
SETTINGS_PATH = os.path.join(BASE_DIR, 'config', 'user_settings.json')

# 默认设置
DEFAULT_SETTINGS = {
    'language': 'auto',  # 语言设置
    'window_width': 1000,
    'window_height': 780,
    'window_x': 100,
    'window_y': 100,
    'sidebar_collapsed': False,
    'log_level': 'info',  # 默认日志级别改为info
    'export_format': 'name-artists',  # 默认导出格式
    'export_file_format': 'txt'  # 默认文件格式，使用具体的后缀名
}

# 递归保护标志
_loading_settings = False
# 缓存的设置
_cached_settings = None

def load_settings():
    """
    加载用户设置
    :return: 设置字典
    """
    global _loading_settings, _cached_settings
    
    # 如果已经在加载设置中，返回缓存或默认设置
    if _loading_settings:
        return _cached_settings if _cached_settings is not None else DEFAULT_SETTINGS.copy()
    
    # 如果设置已缓存，直接返回
    if _cached_settings is not None:
        return _cached_settings
    
    # 设置递归保护标志
    _loading_settings = True
    
    try:
        if os.path.exists(SETTINGS_PATH):
            with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                
            # 合并默认设置，确保所有键都存在
            for key, value in DEFAULT_SETTINGS.items():
                if key not in settings:
                    settings[key] = value
            
            # 缓存设置
            _cached_settings = settings
            return settings
    except Exception as e:
        print(f"加载设置失败: {str(e)}")
    finally:
        # 重置递归保护标志
        _loading_settings = False
    
    # 如果发生错误，返回默认设置
    _cached_settings = DEFAULT_SETTINGS.copy()
    return _cached_settings

def save_settings(settings):
    """
    保存用户设置
    :param settings: 设置字典
    """
    global _cached_settings
    
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
        
        with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
            
        # 更新缓存
        _cached_settings = settings.copy()
    except Exception as e:
        print(f"保存设置失败: {str(e)}")

def get_setting(key, default=None):
    """
    获取特定设置项
    :param key: 设置项键名
    :param default: 默认值
    :return: 设置值
    """
    settings = load_settings()
    return settings.get(key, default)

def set_setting(key, value):
    """
    设置特定设置项
    :param key: 设置项键名
    :param value: 设置值
    """
    # 直接从缓存或加载设置
    settings = load_settings()
    
    # 更新设置
    settings[key] = value
    
    # 保存设置
    save_settings(settings) 