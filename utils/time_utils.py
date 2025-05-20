from datetime import datetime, timedelta
from utils.language_manager import LanguageManager

class TimeUtils:
    @staticmethod
    def format_relative_time(timestamp, language_manager=None):
        """
        将时间戳格式化为相对时间（如：刚刚，5分钟前，2小时前等）
        
        :param timestamp: datetime对象或ISO 8601格式的时间字符串
        :param language_manager: LanguageManager实例，用于获取本地化文本
        :return: 格式化后的相对时间字符串
        """
        if language_manager is None:
            language_manager = LanguageManager()
            
        # 如果是字符串，尝试解析为datetime对象
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                return timestamp
        
        # 确保timestamp是datetime对象
        if not isinstance(timestamp, datetime):
            return str(timestamp)
        
        # 如果timestamp是UTC时间，转换为本地时间
        if timestamp.tzinfo is not None:
            timestamp = timestamp.astimezone(None).replace(tzinfo=None)
        
        now = datetime.now()
        diff = now - timestamp
        
        # 刚刚
        if diff < timedelta(seconds=10):
            return language_manager.get_text("date.now")
        
        # 几秒前
        if diff < timedelta(minutes=1):
            seconds = int(diff.total_seconds())
            return language_manager.get_text("date.seconds_ago").format(time=seconds)
        
        # 几分钟前
        if diff < timedelta(hours=1):
            minutes = int(diff.total_seconds() / 60)
            return language_manager.get_text("date.minutes_ago").format(time=minutes)
        
        # 几小时前
        if diff < timedelta(days=1):
            hours = int(diff.total_seconds() / 3600)
            return language_manager.get_text("date.hours_ago").format(time=hours)
        
        # 昨天
        if diff < timedelta(days=2):
            return language_manager.get_text("date.yesterday")
        
        # 几天前（最多显示7天）
        if diff < timedelta(days=7):
            days = int(diff.total_seconds() / 86400)
            return language_manager.get_text("date.days_ago").format(time=days)
        
        # 超过7天则显示具体日期
        return timestamp.strftime("%Y-%m-%d")
    
    @staticmethod
    def format_cache_time(timestamp, language_manager=None):
        """
        格式化缓存时间，用于显示数据最后更新时间
        
        :param timestamp: datetime对象
        :param language_manager: LanguageManager实例，用于获取本地化文本
        :return: 格式化后的缓存时间信息
        """
        if language_manager is None:
            language_manager = LanguageManager()
            
        if timestamp is None:
            return language_manager.get_text("app.cache_expired")
            
        relative_time = TimeUtils.format_relative_time(timestamp, language_manager)
        return language_manager.get_text("app.cache_info").format(time=relative_time)
    
    @staticmethod
    def format_iso8601(iso_time, format_str="%Y-%m-%d"):
        """
        将ISO 8601格式的时间字符串转换为指定格式
        
        :param iso_time: ISO 8601格式的时间字符串
        :param format_str: 输出格式字符串
        :return: 格式化后的时间字符串
        """
        if not iso_time:
            return ""
            
        try:
            # 解析ISO 8601格式的时间字符串
            dt = datetime.fromisoformat(iso_time.replace('Z', '+00:00'))
            # 转换为本地时区
            if dt.tzinfo is not None:
                dt = dt.astimezone(None)
            # 格式化
            return dt.strftime(format_str)
        except:
            return iso_time 