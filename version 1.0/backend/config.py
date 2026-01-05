"""
配置文件
管理API密钥和系统配置
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """应用配置"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///data/database.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # DeepSeek API配置
    DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
    DEEPSEEK_API_URL = os.environ.get('DEEPSEEK_API_URL', 'https://api.deepseek.com/v1/chat/completions')
    
    # QQ音乐API配置（需要申请）
    QQ_MUSIC_API_KEY = os.environ.get('QQ_MUSIC_API_KEY', '')
    QQ_MUSIC_API_URL = os.environ.get('QQ_MUSIC_API_URL', 'https://c.y.qq.com')
    
    # 网易云音乐API配置（需要申请）
    NETEASE_MUSIC_API_KEY = os.environ.get('NETEASE_MUSIC_API_KEY', '')
    NETEASE_MUSIC_API_URL = os.environ.get('NETEASE_MUSIC_API_URL', 'https://music.163.com')
    
    # 情感分析配置
    SENTIMENT_MODEL = 'advanced'  # 'simple' 或 'advanced'
    
    # 生成配置
    DEFAULT_LYRIC_LENGTH = 16  # 默认歌词行数
    MAX_LYRIC_LENGTH = 100  # 最大歌词行数





