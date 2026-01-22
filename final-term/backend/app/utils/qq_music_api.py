"""
QQ 音乐 API 客户端
基于官方API实现
"""
import requests
import json
from typing import List, Dict, Optional
import time


class QQMusicAPI:
    """QQ音乐API客户端"""
    
    def __init__(self):
        self.base_url = "https://u.y.qq.com/cgi-bin/musicu.fcg"
        self.lyric_url = "https://i.y.qq.com/lyric/fcgi-bin/fcg_query_lyric_new.fcg"
    
    def search_songs(self, keyword: str, limit: int = 50, page: int = 1) -> List[Dict]:
        """搜索歌曲"""
        try:
            body = {
                "comm": {"ct": "19", "cv": "1859", "uin": "0"},
                "req": {
                    "method": "DoSearchForQQMusicDesktop",
                    "module": "music.search.SearchCgiService",
                    "param": {
                        "grp": 1,
                        "num_per_page": limit,
                        "page_num": page,
                        "query": keyword,
                        "search_type": 0  # 0=歌曲
                    }
                }
            }
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
                "Content-Type": "application/json;charset=utf-8",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
            }
            
            response = requests.post(
                self.base_url,
                json=body,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"QQ音乐API响应: {json.dumps(data, ensure_ascii=False)[:500]}")  # 调试信息
                
                # 检查响应结构
                if 'req' in data and 'data' in data['req']:
                    body = data['req']['data'].get('body', {})
                    song_list = body.get('song', {}).get('list', [])
                    
                    if not song_list:
                        print(f"QQ音乐搜索无结果，关键词: {keyword}")
                        print(f"响应结构: {json.dumps(data, ensure_ascii=False)[:1000]}")
                    
                    songs = []
                    for idx, song in enumerate(song_list[:limit]):
                        # 调试：打印第一首歌曲的完整结构
                        if idx == 0:
                            print(f"QQ音乐API返回的歌曲数据结构（第一首）: {json.dumps(song, ensure_ascii=False)[:1000]}")
                        
                        # 尝试多种可能的字段名
                        songmid = song.get('songmid') or song.get('mid') or song.get('songMid') or ''
                        songname = song.get('songname') or song.get('songName') or song.get('name') or ''
                        albumname = song.get('albumname') or song.get('albumName') or song.get('album', {}).get('name', '') if isinstance(song.get('album'), dict) else ''
                        albummid = song.get('albummid') or song.get('albumMid') or (song.get('album', {}).get('mid', '') if isinstance(song.get('album'), dict) else '')
                        
                        # 处理歌手信息
                        singers = song.get('singer', [])
                        if not singers and 'singerName' in song:
                            # 如果singer是字符串
                            artist = song.get('singerName', '')
                        else:
                            artist = ', '.join([s.get('name', '') or s.get('singerName', '') for s in singers if isinstance(s, dict)])
                        
                        songs.append({
                            'id': songmid,
                            'songmid': songmid,
                            'title': songname,
                            'artist': artist,
                            'album': albumname,
                            'albummid': albummid,
                            'duration': song.get('interval', 0) or song.get('duration', 0),
                            'platform': 'qq',
                            '_raw': song  # 保存原始数据用于调试
                        })
                        
                        if idx == 0:
                            print(f"提取的第一首歌曲: songmid={songmid}, title={songname}, artist={artist}")
                    
                    print(f"QQ音乐搜索成功，找到 {len(songs)} 首歌曲")
                    return songs
                else:
                    print(f"QQ音乐API响应格式异常: {json.dumps(data, ensure_ascii=False)[:500]}")
        except Exception as e:
            print(f"QQ音乐搜索失败: {e}")
            import traceback
            traceback.print_exc()
        
        return []
    
    def get_song_lyrics(self, songmid: str) -> Optional[str]:
        """获取歌曲歌词（尝试多种方法）"""
        if not songmid:
            print(f"获取QQ音乐歌词失败: songmid为空")
            return None
        
        # 方法1：使用标准歌词API
        try:
            url = f"{self.lyric_url}?songmid={songmid}&g_tk=5381&format=json&inCharset=utf8&outCharset=utf-8&nobase64=1"
            
            headers = {
                "Referer": "https://y.qq.com/",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                retcode = data.get('retcode', data.get('code', -1))
                
                if retcode == 0 and 'lyric' in data:
                    lyrics = data.get('lyric', '')
                    trans = data.get('trans', '')
                    
                    if lyrics and lyrics.strip():
                        # 解析歌词，移除时间戳
                        import re
                        lyrics = re.sub(r'\[\d{2}:\d{2}\.\d{2}\]', '', lyrics)
                        lyrics = re.sub(r'\[\d{2}:\d{2}\.\d{3}\]', '', lyrics)
                        lyrics = re.sub(r'\[ti:.*?\]', '', lyrics)
                        lyrics = re.sub(r'\[ar:.*?\]', '', lyrics)
                        lyrics = re.sub(r'\[al:.*?\]', '', lyrics)
                        lyrics = re.sub(r'\[by:.*?\]', '', lyrics)
                        lyrics = re.sub(r'\[offset:.*?\]', '', lyrics)
                        
                        lines = [line.strip() for line in lyrics.split('\n') if line.strip()]
                        result = '\n'.join(lines)
                        print(f"成功获取QQ音乐歌词 (songmid={songmid}): {len(result)} 字符")
                        return result
                
                # 如果返回-1310错误，尝试使用新的API端点
                if retcode == -1310:
                    print(f"QQ音乐歌词API返回-1310错误，尝试备用方法 (songmid={songmid})")
                    return self._get_lyrics_alternative(songmid)
        except Exception as e:
            print(f"获取QQ音乐歌词失败 (songmid={songmid}): {e}")
        
        # 方法2：尝试备用API
        return self._get_lyrics_alternative(songmid)
    
    def _get_lyrics_alternative(self, songmid: str) -> Optional[str]:
        """备用方法获取歌词"""
        try:
            # 使用musicu.fcg API获取歌词
            body = {
                "comm": {"ct": 24, "cv": 0},
                "lyric": {
                    "method": "GetLyric",
                    "module": "music.musichallSong.PlayLyricInfo",
                    "param": {"songmid": songmid}
                }
            }
            
            headers = {
                "Referer": "https://y.qq.com/",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                self.base_url,
                json=body,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'lyric' in data and 'data' in data['lyric']:
                    lyric_data = data['lyric']['data']
                    if 'lyric' in lyric_data:
                        lyrics = lyric_data['lyric']
                        if lyrics:
                            import re
                            lyrics = re.sub(r'\[\d{2}:\d{2}\.\d{2}\]', '', lyrics)
                            lyrics = re.sub(r'\[\d{2}:\d{2}\.\d{3}\]', '', lyrics)
                            lines = [line.strip() for line in lyrics.split('\n') if line.strip()]
                            result = '\n'.join(lines)
                            print(f"使用备用方法成功获取QQ音乐歌词 (songmid={songmid}): {len(result)} 字符")
                            return result
        except Exception as e:
            print(f"备用方法获取歌词失败 (songmid={songmid}): {e}")
        
        return None
    
    def get_music_url(self, songmid: str, quality: str = "320") -> Optional[str]:
        """获取音乐播放URL"""
        try:
            prefix_map = {
                "m4a": "C400",
                "128": "M500",
                "320": "M800"
            }
            suffix_map = {
                "m4a": "m4a",
                "128": "mp3",
                "320": "mp3"
            }
            
            prefix = prefix_map.get(quality.lower(), "M800")
            suffix = suffix_map.get(quality.lower(), "mp3")
            
            body = {
                "req_1": {
                    "module": "vkey.GetVkeyServer",
                    "method": "CgiGetVkey",
                    "param": {
                        "filename": [f"{prefix}{songmid}.{suffix}"],
                        "guid": "10000",
                        "songmid": [songmid],
                        "songtype": [0],
                        "uin": "0",
                        "loginflag": 1,
                        "platform": "20"
                    }
                },
                "loginUin": "0",
                "comm": {
                    "uin": "0",
                    "format": "json",
                    "ct": 24,
                    "cv": 0
                }
            }
            
            headers = {
                "accept": "application/json, text/plain, */*",
                "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
                "content-type": "application/json;charset=UTF-8",
                "referer": "https://y.qq.com/",
                "origin": "https://y.qq.com",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            
            response = requests.post(
                self.base_url,
                json=body,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"QQ音乐URL API响应: {json.dumps(data, ensure_ascii=False)[:1000]}")
                
                # 检查多种可能的响应结构
                sip = None
                midurlinfo = None
                
                # 方法1: 标准结构 req_1.data
                if 'req_1' in data and 'data' in data['req_1']:
                    sip = data['req_1']['data'].get('sip', [])
                    midurlinfo = data['req_1']['data'].get('midurlinfo', [])
                
                # 方法2: 直接data结构
                elif 'data' in data:
                    sip = data['data'].get('sip', [])
                    midurlinfo = data['data'].get('midurlinfo', [])
                
                # 检查是否有错误
                if 'code' in data and data.get('code') != 0:
                    error_msg = data.get('message', '未知错误')
                    print(f"QQ音乐API返回错误: code={data.get('code')}, message={error_msg}")
                    return None
                
                if sip and midurlinfo and len(sip) > 0 and len(midurlinfo) > 0:
                    # 处理purl，可能是字符串或字典
                    purl = midurlinfo[0].get('purl', '') if isinstance(midurlinfo[0], dict) else midurlinfo[0]
                    url = sip[0] + purl
                    if url and url.startswith('http'):
                        print(f"成功获取QQ音乐播放URL (songmid={songmid}): {url[:100]}...")
                        return url
                    else:
                        print(f"QQ音乐URL格式异常 (songmid={songmid}): {url[:100] if url else 'None'}")
                else:
                    print(f"QQ音乐URL API返回数据不完整: sip={sip}, midurlinfo={midurlinfo}")
                    print(f"完整响应: {json.dumps(data, ensure_ascii=False)[:2000]}")
            else:
                print(f"QQ音乐URL API HTTP错误: status_code={response.status_code}")
                print(f"响应内容: {response.text[:500]}")
        except Exception as e:
            print(f"获取QQ音乐URL失败 (songmid={songmid}): {e}")
            import traceback
            traceback.print_exc()
        
        return None

