"""
音乐平台API客户端
支持QQ音乐和网易云音乐
"""
import requests
import json
import os
from typing import List, Dict, Optional

class MusicAPIClient:
    """音乐平台API客户端"""
    
    def __init__(self):
        self.qq_music_key = os.environ.get('QQ_MUSIC_API_KEY', '')
        self.netease_music_key = os.environ.get('NETEASE_MUSIC_API_KEY', '')
    
    def search_songs(self, keyword: str, platform: str = 'netease', limit: int = 10) -> List[Dict]:
        """搜索歌曲"""
        if platform == 'netease':
            return self._search_netease(keyword, limit)
        elif platform == 'qq':
            return self._search_qq(keyword, limit)
        else:
            return []
    
    def get_song_info(self, song_id: str, platform: str = 'netease') -> Optional[Dict]:
        """获取歌曲信息"""
        if platform == 'netease':
            return self._get_netease_song_info(song_id)
        elif platform == 'qq':
            return self._get_qq_song_info(song_id)
        else:
            return None
    
    def get_song_lyrics(self, song_id: str, platform: str = 'netease') -> Optional[str]:
        """获取歌词"""
        if platform == 'netease':
            return self._get_netease_lyrics(song_id)
        elif platform == 'qq':
            return self._get_qq_lyrics(song_id)
        else:
            return None
    
    def recommend_by_lyrics(self, lyrics: str, platform: str = 'netease', limit: int = 5) -> List[Dict]:
        """根据歌词推荐相似歌曲"""
        # 提取关键词
        keywords = self._extract_keywords(lyrics)
        
        # 搜索相关歌曲
        all_results = []
        for keyword in keywords[:3]:  # 使用前3个关键词
            results = self.search_songs(keyword, platform, limit)
            all_results.extend(results)
        
        # 去重并排序
        seen_ids = set()
        unique_results = []
        for song in all_results:
            if song.get('id') not in seen_ids:
                seen_ids.add(song['id'])
                unique_results.append(song)
        
        return unique_results[:limit]
    
    def _search_netease(self, keyword: str, limit: int) -> List[Dict]:
        """搜索网易云音乐（使用公开API）"""
        try:
            # 使用公开的网易云音乐API（需要实际API密钥时替换）
            url = f"https://music.163.com/api/search/get"
            params = {
                's': keyword,
                'type': 1,  # 1=单曲
                'limit': limit,
                'offset': 0
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 200 and 'result' in data:
                    songs = []
                    for song in data['result'].get('songs', [])[:limit]:
                        songs.append({
                            'id': str(song['id']),
                            'title': song['name'],
                            'artist': ', '.join([ar['name'] for ar in song.get('artists', [])]),
                            'platform': 'netease',
                            'album': song.get('album', {}).get('name', '')
                        })
                    return songs
        except Exception as e:
            print(f"网易云音乐搜索失败: {e}")
        
        return []
    
    def _search_qq(self, keyword: str, limit: int) -> List[Dict]:
        """搜索QQ音乐"""
        try:
            # QQ音乐API（需要实际API密钥时替换）
            url = "https://c.y.qq.com/soso/fcgi-bin/client_search_cp"
            params = {
                'ct': 24,
                'qqmusic_ver': 1298,
                'new_json': 1,
                'remoteplace': 'txt.yqq.song',
                'searchid': 1,
                't': 0,
                'aggr': 1,
                'cr': 1,
                'catZhida': 1,
                'lossless': 0,
                'flag_qc': 0,
                'p': 1,
                'n': limit,
                'w': keyword,
                'g_tk': 5381,
                'loginUin': 0,
                'hostUin': 0,
                'format': 'json',
                'inCharset': 'utf8',
                'outCharset': 'utf-8',
                'notice': 0,
                'platform': 'yqq.json',
                'needNewCode': 0
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and 'song' in data['data']:
                    songs = []
                    for song in data['data']['song'].get('list', [])[:limit]:
                        songs.append({
                            'id': str(song['songid']),
                            'title': song['songname'],
                            'artist': song.get('singer', [{}])[0].get('name', ''),
                            'platform': 'qq',
                            'album': song.get('albumname', '')
                        })
                    return songs
        except Exception as e:
            print(f"QQ音乐搜索失败: {e}")
        
        return []
    
    def _get_netease_song_info(self, song_id: str) -> Optional[Dict]:
        """获取网易云音乐歌曲信息"""
        try:
            url = f"https://music.163.com/api/song/detail"
            params = {
                'ids': f'[{song_id}]'
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 200 and 'songs' in data:
                    song = data['songs'][0]
                    return {
                        'id': str(song['id']),
                        'title': song['name'],
                        'artist': ', '.join([ar['name'] for ar in song.get('artists', [])]),
                        'album': song.get('album', {}).get('name', ''),
                        'duration': song.get('duration', 0),
                        'platform': 'netease'
                    }
        except Exception as e:
            print(f"获取网易云音乐信息失败: {e}")
        return None
    
    def _get_qq_song_info(self, song_id: str) -> Optional[Dict]:
        """获取QQ音乐歌曲信息"""
        # 实现QQ音乐歌曲信息获取
        return None
    
    def _get_netease_lyrics(self, song_id: str) -> Optional[str]:
        """获取网易云音乐歌词，并过滤时间戳"""
        try:
            url = f"https://music.163.com/api/song/lyric"
            params = {
                'id': song_id,
                'lv': -1,
                'tv': -1
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'lrc' in data and 'lyric' in data['lrc']:
                    lyrics = data['lrc']['lyric']
                    # 过滤时间戳，只保留歌词
                    import re
                    # 移除 [00:00.000] 格式的时间戳
                    lyrics = re.sub(r'\[\d{2}:\d{2}\.\d{3}\]', '', lyrics)
                    # 移除其他可能的格式，如 [00:00.00]
                    lyrics = re.sub(r'\[\d{2}:\d{2}\.\d{2}\]', '', lyrics)
                    # 移除作词、作曲等元信息行
                    lyrics = re.sub(r'\[.*?作词.*?\]', '', lyrics)
                    lyrics = re.sub(r'\[.*?作曲.*?\]', '', lyrics)
                    lyrics = re.sub(r'\[.*?编曲.*?\]', '', lyrics)
                    lyrics = re.sub(r'\[.*?制作人.*?\]', '', lyrics)
                    lyrics = re.sub(r'\[.*?监制.*?\]', '', lyrics)
                    # 清理多余的空行
                    lines = [line.strip() for line in lyrics.split('\n') if line.strip()]
                    return '\n'.join(lines)
        except Exception as e:
            print(f"获取网易云音乐歌词失败: {e}")
        return None
    
    def _get_qq_lyrics(self, song_id: str) -> Optional[str]:
        """获取QQ音乐歌词"""
        # 实现QQ音乐歌词获取
        return None
    
    def _extract_keywords(self, lyrics: str) -> List[str]:
        """提取关键词"""
        import jieba
        import jieba.analyse
        
        # 使用TF-IDF提取关键词
        keywords = jieba.analyse.extract_tags(lyrics, topK=5, withWeight=False)
        return keywords if keywords else ['音乐', '歌曲']

