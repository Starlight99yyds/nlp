"""
推荐服务
个性化推荐、知识图谱
集成音乐平台API
"""
import json
from typing import Dict, List, Optional
from typing import List as ListType
import sys
import os

# 添加backend目录到路径
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from nlp_engine.recommendation import MusicRecommender
from app.models import RecommendationHistory
from app import db
from app.utils.music_api_client import MusicAPIClient


class RecommendationService:
    """推荐服务类"""
    
    def __init__(self):
        self.recommender = MusicRecommender()
        self.music_api = MusicAPIClient()
        # 添加缓存机制，减少重复计算
        self._similarity_cache = {}  # 缓存相似度计算结果
        self._theme_extractor_cache = None  # 缓存主题提取器实例
        self._initialize_sample_songs()
    
    def _initialize_sample_songs(self):
        """初始化示例歌曲库"""
        sample_songs = [
            {
                'id': 1,
                'title': '爱情故事',
                'artist': '示例歌手A',
                'lyrics': '我爱你\n就像爱春天\n你是我心中的\n最美的风景',
                'theme': '爱情',
                'style': '流行'
            },
            {
                'id': 2,
                'title': '追梦人',
                'artist': '示例歌手B',
                'lyrics': '追逐梦想\n永不放弃\n坚持到底\n成功在望',
                'theme': '励志',
                'style': '摇滚'
            },
            {
                'id': 3,
                'title': '回忆',
                'artist': '示例歌手C',
                'lyrics': '回忆过去\n那些美好时光\n青春岁月\n永远难忘',
                'theme': '怀旧',
                'style': '抒情'
            }
        ]
        
        for song in sample_songs:
            self.recommender.add_song_to_database(song)
    
    def recommend(self, query_lyrics: str, top_k: int = 5,
                 user_id: int = None, user_preferences: Optional[Dict] = None) -> Dict:
        """推荐歌曲（改进算法：基于主题、关键词和歌词相似度，集成DeepSeek优化）"""
        # 使用DeepSeek优化关键词和主题提取
        from app.utils.deepseek_client import DeepSeekClient
        deepseek_client = DeepSeekClient()
        
        # 尝试使用DeepSeek提取关键词和主题
        if deepseek_client.api_key and deepseek_client.client:
            try:
                prompt = f"""请分析以下歌词，提取关键词和主题，以JSON格式返回：
{{
    "keywords": ["关键词1", "关键词2", "关键词3", "关键词4", "关键词5"],
    "themes": ["主题1", "主题2", "主题3"]
}}

歌词：
{query_lyrics}

请直接返回JSON，不要添加其他文字。"""
                
                response = deepseek_client.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {'role': 'system', 'content': '你是一位专业的歌词分析专家。'},
                        {'role': 'user', 'content': prompt}
                    ],
                    temperature=0.3,
                    max_tokens=500,
                    stream=False
                )
                
                import json
                import re
                result_text = response.choices[0].message.content
                # 尝试提取JSON
                json_match = re.search(r'\{[^}]+\}', result_text, re.DOTALL)
                if json_match:
                    deepseek_result = json.loads(json_match.group())
                    keywords = deepseek_result.get('keywords', [])
                    themes = deepseek_result.get('themes', [])
                    if keywords and themes:
                        print(f"DeepSeek提取成功: 关键词={keywords}, 主题={themes}")
                    else:
                        keywords = self._extract_keywords_from_lyrics(query_lyrics)
                        themes = self._extract_themes_from_lyrics(query_lyrics)
                else:
                    keywords = self._extract_keywords_from_lyrics(query_lyrics)
                    themes = self._extract_themes_from_lyrics(query_lyrics)
            except Exception as e:
                print(f"DeepSeek关键词提取失败，使用本地方法: {e}")
                keywords = self._extract_keywords_from_lyrics(query_lyrics)
                themes = self._extract_themes_from_lyrics(query_lyrics)
        else:
            # 使用本地方法
            keywords = self._extract_keywords_from_lyrics(query_lyrics)
            themes = self._extract_themes_from_lyrics(query_lyrics)
        
        print(f"推荐请求: 关键词={keywords}, 主题={themes}, top_k={top_k}")
        
        # 优化策略：减少搜索次数，优先识别原唱
        all_songs = []
        seen_song_ids = set()
        exact_match_songs = []  # 完全匹配的歌曲（优先处理）
        
        try:
            # 第一步：使用最关键的歌词片段搜索（只使用前2-3行，优先找到原唱）
            print("第一步：使用关键歌词片段搜索，优先寻找原唱...")
            lyrics_lines = [line.strip() for line in query_lyrics.split('\n') if line.strip()]
            
            # 只使用前2-3行最关键的歌词（减少搜索次数）
            for line in lyrics_lines[:3]:  # 从5行减少到3行
                if len(line) > 5:  # 只使用长度大于5的行（更精确）
                    print(f"使用歌词行搜索: {line[:30]}...")
                    # 优先使用QQ音乐（通常原唱排名更靠前）
                    songs = self.music_api.search_songs(line, platform='qq', limit=15)
                    # 识别和标记原唱
                    for idx, song in enumerate(songs):
                        song_key = f"{song.get('title', '')}_{song.get('artist', '')}"
                        if song_key not in seen_song_ids:
                            seen_song_ids.add(song_key)
                            # 识别原唱：搜索结果前3个通常更可能是原唱，且不包含翻唱标记
                            is_original = self._is_original_song(song, idx)
                            song['_search_priority'] = 'lyrics_line'
                            song['_is_original'] = is_original
                            song['_search_rank'] = idx  # 保存搜索排名（排名越靠前越可能是原唱）
                            if is_original:
                                exact_match_songs.insert(0, song)  # 原唱放在前面
                            else:
                                exact_match_songs.append(song)
            
            # 第二步：使用关键词搜索（只使用前3个关键词，减少搜索次数）
            print("第二步：使用关键词搜索，补充搜索结果...")
            for keyword in keywords[:3]:  # 从5个减少到3个
                songs = self.music_api.search_songs(keyword, platform='qq', limit=min(20, top_k * 3))
                for idx, song in enumerate(songs):
                    song_key = f"{song.get('title', '')}_{song.get('artist', '')}"
                    if song_key not in seen_song_ids:
                        seen_song_ids.add(song_key)
                        is_original = self._is_original_song(song, idx)
                        song['_search_priority'] = 'keyword'
                        song['_is_original'] = is_original
                        song['_search_rank'] = idx
                        if is_original and idx < 3:  # 只保留前3个原唱候选
                            all_songs.insert(0, song)
                        else:
                            all_songs.append(song)
            
            # 合并搜索结果：原唱优先
            all_songs = exact_match_songs + all_songs
            print(f"搜索完成: 完全匹配候选={len(exact_match_songs)}, 其他候选={len(all_songs) - len(exact_match_songs)}, 总计={len(all_songs)}")
        except Exception as e:
            print(f"音乐平台API调用失败: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"推荐服务：搜索到 {len(all_songs)} 首歌曲")
        
        # 如果API有结果，先获取所有歌曲的歌词，然后按歌词相似度排序
        if all_songs:
            # 优化：限制处理数量，优先处理原唱和高匹配度的歌曲
            print(f"搜索到 {len(all_songs)} 首歌曲，优化处理策略...")
            
            # 先按原唱标识和标题相似度快速筛选，只处理前50首
            preliminary_scores = []
            for song in all_songs[:80]:  # 从200首减少到80首
                title = song.get('title', '')
                artist = song.get('artist', '')
                title_artist = f"{title} {artist}"
                title_sim = self._calculate_keyword_similarity(keywords, title_artist)
                # 原唱加分：原唱歌曲相似度提升20%
                is_original = song.get('_is_original', False)
                search_rank = song.get('_search_rank', 999)
                original_bonus = 0.2 if is_original else 0.0
                rank_bonus = max(0, (10 - search_rank) * 0.01)  # 排名越靠前加分越多
                final_score = title_sim + original_bonus + rank_bonus
                preliminary_scores.append((final_score, song))
            
            # 按综合得分排序（原唱优先）
            preliminary_scores.sort(key=lambda x: x[0], reverse=True)
            sorted_songs = [song for _, song in preliminary_scores[:30]]  # 从100首减少到30首
            
            print(f"优化后处理 {len(sorted_songs)} 首歌曲，优先处理原唱...")
            
            recommendations = []
            lyrics_failed_count = 0
            
            # 分离原唱和非原唱，优先处理原唱
            original_songs = [s for s in sorted_songs if s.get('_is_original', False)]
            other_songs = [s for s in sorted_songs if not s.get('_is_original', False)]
            prioritized_songs = original_songs + other_songs  # 原唱在前
            
            # 使用并发处理提高速度（减少并发数避免过载）
            import concurrent.futures
            from threading import Lock
            lock = Lock()
            
            def process_song(song):
                """处理单首歌曲"""
                platform = song.get('platform', 'qq')
                song_id = song.get('songmid') or song.get('id', '')
                lyrics = self.music_api.get_song_lyrics(song_id, platform)
                
                if lyrics and len(lyrics) > 50:
                    song['lyrics'] = lyrics
                    
                    # 检查是否为完全匹配（歌词一模一样）
                    query_normalized = query_lyrics.replace(' ', '').replace('\n', '').replace('，', '').replace('。', '').replace('、', '').replace('\r', '')
                    lyrics_normalized = lyrics.replace(' ', '').replace('\n', '').replace('，', '').replace('。', '').replace('、', '').replace('\r', '')
                    
                    # 计算完全匹配度
                    is_exact_match = False
                    exact_match_score = 0.0
                    
                    # 如果查询歌词完全包含在歌曲歌词中，或歌曲歌词完全包含在查询歌词中
                    if query_normalized in lyrics_normalized or lyrics_normalized in query_normalized:
                        # 计算匹配比例
                        if len(query_normalized) > 0:
                            match_ratio = min(len(query_normalized), len(lyrics_normalized)) / max(len(query_normalized), len(lyrics_normalized))
                            if match_ratio > 0.8:  # 80%以上匹配认为是完全匹配
                                is_exact_match = True
                                exact_match_score = match_ratio
                    
                    # 计算综合相似度（优先歌词内容相似度）
                    keyword_sim = self._calculate_keyword_similarity(keywords, lyrics)
                    theme_sim = self._calculate_theme_similarity(themes, lyrics)
                    content_sim = self._calculate_similarity(query_lyrics, lyrics)
                    
                    # 原唱加分：如果是原唱，相似度提升10%
                    is_original = song.get('_is_original', False)
                    original_bonus = 0.1 if is_original else 0.0
                    
                    # 如果是完全匹配，大幅提高相似度
                    if is_exact_match:
                        overall_similarity = 0.95 + (exact_match_score * 0.05) + original_bonus  # 完全匹配的相似度在0.95-1.0之间
                    else:
                        # 优先歌词内容相似度（权重提高到0.6），原唱额外加分
                        overall_similarity = (keyword_sim * 0.2 + theme_sim * 0.2 + content_sim * 0.6) + original_bonus
                    
                    explanation = self._generate_explanation(query_lyrics, lyrics, keywords, themes)
                    if is_exact_match:
                        explanation = f"完全匹配原唱：{song.get('title', '')} - {song.get('artist', '')} (匹配度: {exact_match_score:.2%})"
                    elif is_original:
                        explanation = f"原唱版本：{explanation}"
                    
                    return {
                        'song': song,
                        'similarity': min(overall_similarity, 1.0),  # 确保不超过1.0
                        'explanation': explanation,
                        'platform': platform,
                        'details': {
                            'keyword_similarity': keyword_sim,
                            'theme_similarity': theme_sim,
                            'content_similarity': content_sim,
                            'is_exact_match': is_exact_match,
                            'exact_match_score': exact_match_score if is_exact_match else 0.0,
                            'is_original': is_original
                        }
                    }
                return None
            
            # 并发处理（优化线程池大小，根据CPU核心数动态调整）
            import multiprocessing
            max_workers = min(10, max(3, multiprocessing.cpu_count()))  # 3-10个线程
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(process_song, song) for song in prioritized_songs]
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    if result:
                        recommendations.append(result)
                    else:
                        lyrics_failed_count += 1
            
            # 旧代码保留作为备用（如果并发处理失败）
            if not recommendations:
                print("并发处理失败，使用串行处理...")
                for idx, song in enumerate(sorted_songs[:50]):  # 备用方案只处理前50首
                    if idx % 20 == 0:
                        print(f"处理进度: {idx}/{len(sorted_songs)}")
                    
                    # 获取歌词（优先使用QQ音乐）
                    platform = song.get('platform', 'qq')
                    song_id = song.get('songmid') or song.get('id', '')
                    
                    lyrics = self.music_api.get_song_lyrics(song_id, platform)
                    
                    if lyrics and len(lyrics) > 50:  # 只处理有实际歌词的歌曲（长度>50字符）
                        song['lyrics'] = lyrics
                        
                        # 检查是否为完全匹配（歌词一模一样）
                        query_normalized = query_lyrics.replace(' ', '').replace('\n', '').replace('，', '').replace('。', '').replace('、', '').replace('\r', '')
                        lyrics_normalized = lyrics.replace(' ', '').replace('\n', '').replace('，', '').replace('。', '').replace('、', '').replace('\r', '')
                        
                        # 计算完全匹配度
                        is_exact_match = False
                        exact_match_score = 0.0
                        
                        # 如果查询歌词完全包含在歌曲歌词中，或歌曲歌词完全包含在查询歌词中
                        if query_normalized in lyrics_normalized or lyrics_normalized in query_normalized:
                            # 计算匹配比例
                            if len(query_normalized) > 0:
                                match_ratio = min(len(query_normalized), len(lyrics_normalized)) / max(len(query_normalized), len(lyrics_normalized))
                                if match_ratio > 0.8:  # 80%以上匹配认为是完全匹配
                                    is_exact_match = True
                                    exact_match_score = match_ratio
                                    print(f"发现完全匹配: {song.get('title', '')} - {song.get('artist', '')} (匹配度: {match_ratio:.2%})")
                        
                        # 计算综合相似度（优先歌词内容相似度）
                        keyword_sim = self._calculate_keyword_similarity(keywords, lyrics)
                        theme_sim = self._calculate_theme_similarity(themes, lyrics)
                        content_sim = self._calculate_similarity(query_lyrics, lyrics)
                        
                        # 如果是完全匹配，大幅提高相似度
                        if is_exact_match:
                            overall_similarity = 0.95 + (exact_match_score * 0.05)  # 完全匹配的相似度在0.95-1.0之间
                            print(f"完全匹配歌曲 {song.get('title', '')} 相似度提升至: {overall_similarity:.3f}")
                        else:
                            # 优先歌词内容相似度（权重提高到0.6）
                            overall_similarity = (keyword_sim * 0.2 + theme_sim * 0.2 + content_sim * 0.6)
                        
                        if idx < 10:  # 只打印前10首的详细信息
                            print(f"歌曲 {song.get('title', '')} 相似度: 关键词={keyword_sim:.2f}, 主题={theme_sim:.2f}, 内容={content_sim:.2f}, 综合={overall_similarity:.2f}")
                        
                        explanation = self._generate_explanation(query_lyrics, lyrics, keywords, themes)
                        if is_exact_match:
                            explanation = f"完全匹配原唱：{song.get('title', '')} - {song.get('artist', '')} (匹配度: {exact_match_score:.2%})"
                        
                        rec_item = {
                            'song': song,
                            'similarity': overall_similarity,
                            'explanation': explanation,
                            'platform': platform,
                            'details': {
                                'keyword_similarity': keyword_sim,
                                'theme_similarity': theme_sim,
                                'content_similarity': content_sim,
                                'is_exact_match': is_exact_match,
                                'exact_match_score': exact_match_score if is_exact_match else 0.0
                            }
                        }
                        
                        recommendations.append(rec_item)
                    else:
                        lyrics_failed_count += 1
                        # 即使没有歌词，也基于标题和艺术家进行推荐（降低权重）
                        if song.get('title') and song.get('artist'):
                            title_artist_text = f"{song.get('title', '')} {song.get('artist', '')}"
                            keyword_sim = self._calculate_keyword_similarity(keywords, title_artist_text)
                            theme_sim = self._calculate_theme_similarity(themes, title_artist_text)
                            content_sim = self._calculate_similarity(query_lyrics, title_artist_text)
                            
                            overall_similarity = (keyword_sim * 0.4 + theme_sim * 0.4 + content_sim * 0.2) * 0.5  # 进一步降低权重
                            
                            if overall_similarity > 0.1:  # 提高阈值，只保留真正相关的
                                recommendations.append({
                                    'song': song,
                                    'similarity': overall_similarity,
                                    'explanation': self._generate_explanation(query_lyrics, title_artist_text, keywords, themes) + "（无歌词，基于标题和艺术家）",
                                    'platform': platform,
                                    'details': {
                                        'keyword_similarity': keyword_sim,
                                        'theme_similarity': theme_sim,
                                        'content_similarity': content_sim,
                                        'note': '无歌词数据'
                                    }
                                })
            
            print(f"歌词获取统计: 成功={len([r for r in recommendations if r.get('song', {}).get('lyrics')])}, 失败={lyrics_failed_count}, 总计推荐={len(recommendations)}")
            
            # 如果歌名和歌词完全匹配，优先选择原唱（相似度最高的）
            # 检查是否有完全匹配的歌曲，并搜索原唱
            exact_matches = []
            other_matches = []
            
            # 提取可能的歌名（从查询歌词中提取）
            import jieba
            import jieba.analyse
            possible_titles = []
            # 尝试从歌词中提取可能的歌名（前几个关键词）
            keywords = jieba.analyse.extract_tags(query_lyrics, topK=3, withWeight=False)
            if keywords:
                possible_titles = keywords[:2]  # 使用前2个关键词作为可能的歌名
            
            # 如果发现完全匹配的歌曲，尝试搜索原唱
            for rec in recommendations:
                song = rec.get('song', {})
                song_title = song.get('title', '').strip()
                song_lyrics = song.get('lyrics', '').strip()
                song_artist = song.get('artist', '').strip()
                
                # 检查歌名是否在查询歌词中，或者查询歌词是否在歌曲歌词中
                query_normalized = query_lyrics.replace(' ', '').replace('\n', '').replace('，', '').replace('。', '').replace('、', '')
                song_lyrics_normalized = song_lyrics.replace(' ', '').replace('\n', '').replace('，', '').replace('。', '').replace('、', '')
                
                # 如果歌名完全匹配或歌词高度相似（相似度>0.9），认为是原唱或翻唱
                is_exact_match = (song_title in query_lyrics or 
                                 query_lyrics in song_lyrics or 
                                 query_normalized in song_lyrics_normalized or
                                 rec.get('similarity', 0) > 0.9)
                
                if is_exact_match:
                    exact_matches.append(rec)
                else:
                    other_matches.append(rec)
            
            # 如果有完全匹配的，尝试搜索原唱
            if exact_matches:
                print(f"发现 {len(exact_matches)} 首完全匹配的歌曲，尝试搜索原唱...")
                
                # 从匹配的歌曲中提取歌名和艺术家信息
                best_match = max(exact_matches, key=lambda x: x['similarity'])
                best_song = best_match.get('song', {})
                search_title = best_song.get('title', '')
                search_artist = best_song.get('artist', '')
                
                # 使用歌名+艺术家搜索原唱
                if search_title:
                    print(f"搜索原唱: {search_title} - {search_artist}")
                    try:
                        # 方法1：使用歌名+艺术家搜索
                        search_queries = [
                            f"{search_title} {search_artist}".strip(),
                            search_title,  # 只用歌名搜索
                            f"{search_title} 周深",  # 如果知道是周深的歌，直接搜索
                            f"{search_title} 原唱"
                        ]
                        
                        original_found = False
                        for search_query in search_queries:
                            if original_found:
                                break
                                
                            original_songs = self.music_api.search_songs(
                                search_query,
                                platform='qq',
                                limit=30
                            )
                            
                            # 在搜索结果中查找原唱（优先匹配艺术家）
                            for orig_song in original_songs:
                                orig_title = orig_song.get('title', '').strip()
                                orig_artist = orig_song.get('artist', '').strip()
                                
                                # 检查是否已经存在（避免重复）
                                existing = any(
                                    r.get('song', {}).get('title', '').strip() == orig_title and
                                    r.get('song', {}).get('artist', '').strip() == orig_artist
                                    for r in exact_matches + other_matches
                                )
                                if existing:
                                    continue
                                
                                # 如果标题完全匹配，且艺术家匹配或包含在搜索结果中
                                title_match = orig_title == search_title or search_title in orig_title
                                artist_match = (search_artist and search_artist in orig_artist) or (not search_artist)
                                
                                # 如果标题匹配，认为是候选原唱
                                if title_match:
                                    # 获取原唱的歌词和详细信息
                                    orig_songmid = orig_song.get('songmid') or orig_song.get('id', '')
                                    if orig_songmid:
                                        orig_lyrics = self.music_api.get_song_lyrics(orig_songmid, 'qq')
                                        if orig_lyrics:
                                            orig_song['lyrics'] = orig_lyrics
                                            # 计算相似度
                                            keyword_sim = self._calculate_keyword_similarity(keywords, orig_lyrics)
                                            theme_sim = self._calculate_theme_similarity(themes, orig_lyrics)
                                            content_sim = self._calculate_similarity(query_lyrics, orig_lyrics)
                                            overall_sim = (keyword_sim * 0.2 + theme_sim * 0.2 + content_sim * 0.6)
                                            
                                            # 如果是原唱（艺术家匹配或排名靠前），给予更高相似度
                                            is_original = artist_match or orig_song.get('_is_original', False)
                                            if is_original:
                                                overall_sim = min(overall_sim + 0.1, 1.0)  # 原唱加分
                                            
                                            # 创建原唱推荐
                                            original_rec = {
                                                'song': orig_song,
                                                'similarity': overall_sim,
                                                'explanation': f"原唱版本：{orig_title} - {orig_artist}" if is_original else f"{orig_title} - {orig_artist}",
                                                'platform': 'qq',
                                                'details': {
                                                    'keyword_similarity': keyword_sim,
                                                    'theme_similarity': theme_sim,
                                                    'content_similarity': content_sim,
                                                    'is_original': is_original
                                                }
                                            }
                                            
                                            # 如果是原唱，放在第一位；否则放在匹配列表前面
                                            if is_original:
                                                exact_matches.insert(0, original_rec)
                                                print(f"找到原唱: {orig_title} - {orig_artist}")
                                                original_found = True
                                                break
                                            else:
                                                # 非原唱但标题匹配的，也添加到列表中
                                                exact_matches.append(original_rec)
                    except Exception as e:
                        print(f"搜索原唱失败: {e}")
                        import traceback
                        traceback.print_exc()
                
                # 按相似度排序，原唱优先
                exact_matches.sort(key=lambda x: (x.get('details', {}).get('is_original', False), x['similarity']), reverse=True)
                # 原唱放在第一位，其他匹配的也保留（最多保留3个匹配的）
                recommendations = exact_matches[:3] + other_matches  # 原唱和最多2个其他匹配版本放在前面
            
            # 按相似度排序（原唱优先，然后按相似度）
            recommendations.sort(key=lambda x: (
                x.get('details', {}).get('is_original', False),  # 原唱优先
                x.get('details', {}).get('is_exact_match', False),  # 完全匹配次优先
                x['similarity']  # 最后按相似度
            ), reverse=True)
            
            # 优先返回有歌词的推荐
            with_lyrics = [r for r in recommendations if r.get('song', {}).get('lyrics')]
            without_lyrics = [r for r in recommendations if not r.get('song', {}).get('lyrics')]
            
            print(f"推荐统计: 有歌词={len(with_lyrics)}, 无歌词={len(without_lyrics)}")
            if with_lyrics:
                top_songs = [(r['song'].get('title', ''), round(r.get('similarity', 0), 3)) for r in with_lyrics[:10]]
                print(f"有歌词推荐前10首（相似度）: {top_songs}")
            
            # 优先返回有歌词且相似度高的推荐，返回更多结果
            # 至少返回top_k * 3首歌曲，让用户有更多选择
            final_recommendations = with_lyrics[:top_k * 3]  # 优先返回有歌词的，返回更多
            if len(final_recommendations) < top_k * 2:
                remaining = (top_k * 2) - len(final_recommendations)
                final_recommendations.extend(without_lyrics[:remaining])
            
            recommendations = final_recommendations[:top_k * 3]  # 返回更多结果给用户选择（至少15首）
            
            if not recommendations:
                print("警告：搜索到歌曲但计算相似度后无推荐结果")
        else:
            print(f"警告：QQ音乐API未返回任何搜索结果，关键词: {keywords}, 主题: {themes}")
            # 使用本地推荐系统作为备用
            recommendations = self.recommender.recommend_songs(
                query_lyrics, top_k, user_preferences
            )
            
            # 添加推荐理由
            for rec in recommendations:
                rec['explanation'] = self.recommender.explain_recommendation(
                    query_lyrics, rec['song']
                )
            
            print(f"使用本地推荐系统，返回 {len(recommendations)} 个推荐")
        
        # 为每首推荐歌曲生成外部播放链接（不依赖API获取音频URL）
        for rec in recommendations:
            song = rec.get('song', {})
            title = song.get('title', '')
            artist = song.get('artist', '')
            songmid = song.get('songmid') or song.get('id', '')
            platform = song.get('platform', 'qq')
            
            # 生成多个平台的播放链接
            external_links = {}
            
            # QQ音乐网页版链接（直接播放）
            if songmid and platform == 'qq':
                external_links['qq_music'] = f"https://y.qq.com/n/ryqq/songDetail/{songmid}"
            
            # 网易云音乐链接（优先使用歌曲ID直接播放）
            if title and artist:
                import urllib.parse
                search_query = f"{title} {artist}"
                
                # 如果有网易云ID，直接跳转到歌曲页面（可以直接播放）
                netease_id = song.get('netease_id') or (song.get('id') if platform == 'netease' else None)
                if netease_id:
                    external_links['netease'] = f"https://music.163.com/#/song?id={netease_id}"
                else:
                    # 否则使用搜索（需要用户点击搜索结果）
                    encoded_query = urllib.parse.quote(search_query)
                    external_links['netease'] = f"https://music.163.com/#/search/m/?s={encoded_query}&type=1"
                
                # 酷狗音乐链接（使用搜索，需要用户点击搜索结果）
                encoded_query_kugou = urllib.parse.quote(search_query)
                external_links['kugou'] = f"https://www.kugou.com/yy/html/search.html#searchType=song&searchKeyWord={encoded_query_kugou}"
            
            # 保存外部链接
            if external_links:
                song['external_links'] = external_links
                print(f"为歌曲 {title} 生成外部链接: {list(external_links.keys())}")
        
        result = {
            'query_lyrics': query_lyrics,
            'recommendations': [
                {
                    'song': rec['song'],
                    'similarity': round(rec.get('similarity', 0.8), 3),
                    'explanation': rec.get('explanation', '基于歌词相似度的推荐'),
                    'reasons': rec.get('reasons', {}),
                    'platform': rec.get('platform', 'local'),
                    'details': rec.get('details', {}),
                    'has_lyrics': bool(rec.get('song', {}).get('lyrics'))
                }
                for rec in recommendations
            ],
            'total': len(recommendations),
            'with_lyrics': len([r for r in recommendations if r.get('song', {}).get('lyrics')]),
            'without_lyrics': len([r for r in recommendations if not r.get('song', {}).get('lyrics')])
        }
        
        # 保存推荐历史
        self._save_history(query_lyrics, result, user_id)
        
        return result
    
    def _extract_themes_from_lyrics(self, lyrics: str) -> ListType[str]:
        """从歌词中提取主题"""
        import sys
        import os
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)
        
        from nlp_engine.theme import ThemeExtractor
        extractor = ThemeExtractor()
        themes = extractor.classify_theme(lyrics)
        return [t['theme'] for t in themes[:3]]  # 返回前3个主题
    
    def _is_original_song(self, song: Dict, search_rank: int = 0) -> bool:
        """识别是否为原唱歌曲"""
        title = song.get('title', '').lower()
        artist = song.get('artist', '').lower()
        
        # 翻唱标记关键词
        cover_keywords = ['翻唱', 'cover', 'cover版', 'cover version', '翻唱版', 
                         'live', '现场', 'live版', '现场版', 'remix', 'remix版',
                         '伴奏', 'instrumental', '纯音乐', 'demo', 'demo版',
                         '其他', 'others', 'Various Artists', '群星']
        
        # 检查标题或艺术家是否包含翻唱标记
        for keyword in cover_keywords:
            if keyword in title or keyword in artist:
                return False
        
        # 知名原唱歌手列表（这些歌手的版本更可能是原唱）
        original_artists = ['周深', '周杰伦', '林俊杰', '王力宏', '陈奕迅', '张学友', 
                           '邓紫棋', '毛不易', '薛之谦', '李荣浩', '许嵩', '汪苏泷',
                           '张杰', '华晨宇', '李健', '朴树', '许巍', '老狼']
        
        # 如果艺术家是知名原唱歌手，更可能是原唱
        if any(oa.lower() in artist for oa in original_artists):
            return True
        
        # 搜索结果前3个通常更可能是原唱（音乐平台通常把原唱排在前面）
        if search_rank < 3:
            return True
        
        # 如果标题和艺术家都不包含翻唱标记，且排名靠前，认为是原唱
        return search_rank < 5
    
    def _extract_phrases(self, lyrics: str) -> ListType[str]:
        """提取关键短语（2-3字组合）"""
        import jieba
        words = list(jieba.cut(lyrics))
        phrases = []
        
        # 提取2字短语
        for i in range(len(words) - 1):
            if len(words[i]) > 0 and len(words[i+1]) > 0:
                phrase = words[i] + words[i+1]
                if len(phrase) >= 2:
                    phrases.append(phrase)
        
        # 提取3字短语
        for i in range(len(words) - 2):
            if all(len(words[i+j]) > 0 for j in range(3)):
                phrase = ''.join(words[i:i+3])
                if len(phrase) >= 3:
                    phrases.append(phrase)
        
        # 统计频率，返回高频短语
        from collections import Counter
        phrase_counter = Counter(phrases)
        return [p for p, _ in phrase_counter.most_common(5)]
    
    def _calculate_keyword_similarity(self, keywords: ListType[str], lyrics: str) -> float:
        """计算关键词相似度（改进版：支持部分匹配和子串匹配）"""
        if not keywords or not lyrics:
            return 0.0
        
        import jieba
        lyrics_words = set(jieba.cut(lyrics))
        lyrics_text = lyrics.lower()  # 转换为小写用于子串匹配
        
        matched_count = 0
        for kw in keywords:
            kw_lower = kw.lower()
            # 完全匹配
            if kw in lyrics_words or kw_lower in lyrics_text:
                matched_count += 1
            # 部分匹配（关键词作为子串）
            elif any(kw_lower in word.lower() or word.lower() in kw_lower for word in lyrics_words if len(word) > 1):
                matched_count += 0.5
        
        return matched_count / len(keywords) if keywords else 0.0
    
    def _calculate_theme_similarity(self, themes: ListType[str], lyrics: str) -> float:
        """计算主题相似度（使用缓存优化）"""
        # 使用缓存键避免重复计算
        cache_key = f"theme_{hash(lyrics[:100])}"  # 使用歌词前100字符的hash作为缓存键
        if cache_key in self._similarity_cache:
            cached_themes = self._similarity_cache[cache_key]
        else:
            import sys
            import os
            backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            if backend_dir not in sys.path:
                sys.path.insert(0, backend_dir)
            
            from nlp_engine.theme import ThemeExtractor
            # 复用主题提取器实例（如果已缓存）
            if self._theme_extractor_cache is None:
                self._theme_extractor_cache = ThemeExtractor()
            extractor = self._theme_extractor_cache
            
            lyrics_themes = extractor.classify_theme(lyrics)
            cached_themes = [t['theme'] for t in lyrics_themes]
            # 缓存结果（限制缓存大小，避免内存溢出）
            if len(self._similarity_cache) < 1000:
                self._similarity_cache[cache_key] = cached_themes
        
        matched = sum(1 for theme in themes if theme in cached_themes)
        return matched / len(themes) if themes else 0.0
    
    def _generate_explanation(self, query_lyrics: str, song_lyrics: str, 
                             keywords: ListType[str], themes: ListType[str] = None) -> str:
        """生成推荐理由"""
        reasons = []
        if keywords:
            reasons.append(f"关键词'{keywords[0]}'匹配")
        if themes:
            reasons.append(f"主题'{themes[0]}'相似")
        reasons.append("歌词内容相似")
        
        return "、".join(reasons) if reasons else "基于歌词相似度的推荐"
    
    def _calculate_similarity(self, lyrics1: str, lyrics2: str) -> float:
        """计算两段歌词的相似度（改进版：支持短语匹配，使用缓存优化）"""
        if not lyrics1 or not lyrics2:
            return 0.0
        
        # 使用缓存键避免重复计算
        cache_key = f"sim_{hash(lyrics1[:50] + lyrics2[:50])}"
        if cache_key in self._similarity_cache:
            return self._similarity_cache[cache_key]
        
        import jieba
        from collections import Counter
        
        # 分词
        words1 = set(jieba.cut(lyrics1))
        words2 = set(jieba.cut(lyrics2))
        
        # 过滤停用词
        stopwords = {'的', '了', '在', '是', '我', '你', '他', '她', '它', '这', '那', '有', '和', '与', '或', '着', '也', '都', '就', '而', '但', '却', '又', '还', '只', '才', '可', '能', '会', '要', '将', '已', '被', '为', '对', '向', '从', '到', '于', '把', '给', '跟', '让', '使', '由', '以', '及', '等', '或', '与', '和'}
        words1 = {w for w in words1 if len(w) > 1 and w not in stopwords}
        words2 = {w for w in words2 if len(w) > 1 and w not in stopwords}
        
        # 计算Jaccard相似度
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        jaccard_sim = intersection / union if union > 0 else 0.0
        
        # 额外检查：如果歌词1的关键短语在歌词2中出现，增加相似度
        lyrics1_lower = lyrics1.lower()
        lyrics2_lower = lyrics2.lower()
        
        # 提取2-4字短语
        phrases1 = []
        for i in range(len(lyrics1) - 1):
            for length in [2, 3, 4]:
                if i + length <= len(lyrics1):
                    phrase = lyrics1[i:i+length].strip()
                    if len(phrase) >= 2 and phrase not in stopwords:
                        phrases1.append(phrase.lower())
        
        # 检查短语匹配
        phrase_matches = sum(1 for phrase in set(phrases1) if phrase in lyrics2_lower)
        phrase_bonus = min(phrase_matches * 0.1, 0.3)  # 最多增加0.3
        
        result = min(jaccard_sim + phrase_bonus, 1.0)
        # 缓存结果（限制缓存大小）
        if len(self._similarity_cache) < 1000:
            self._similarity_cache[cache_key] = result
        return result
    
    def _extract_keywords_from_lyrics(self, lyrics: str) -> ListType[str]:
        """从歌词中提取关键词"""
        import jieba
        import jieba.analyse
        
        keywords = jieba.analyse.extract_tags(lyrics, topK=5, withWeight=False)
        return keywords if keywords else []
    
    def build_knowledge_graph(self, songs: List[Dict] = None) -> Dict:
        """构建知识图谱"""
        if songs is None:
            songs = self.recommender.song_database
        
        graph = self.recommender.build_knowledge_graph(songs)
        
        return graph
    
    def get_user_preferences(self, user_id: int) -> Dict:
        """获取用户偏好"""
        from app.models import User
        
        user = User.query.get(user_id)
        if user and user.preferences:
            return json.loads(user.preferences)
        return {}
    
    def update_user_preferences(self, user_id: int, preferences: Dict):
        """更新用户偏好"""
        from app.models import User
        
        user = User.query.get(user_id)
        if user:
            user.preferences = json.dumps(preferences, ensure_ascii=False)
            db.session.commit()
    
    def _save_history(self, query_lyrics: str, result: Dict, user_id: int = None):
        """保存推荐历史（包含所有信息，包括音频URL）"""
        try:
            # 确保result中包含所有信息，包括音频URL
            history_data = {
                'query_lyrics': query_lyrics,
                'recommendations': result.get('recommendations', []),
                'total': result.get('total', 0),
                'with_lyrics': result.get('with_lyrics', 0),
                'without_lyrics': result.get('without_lyrics', 0),
                'created_at': result.get('created_at')  # 如果有时间戳也保存
            }
            
            history = RecommendationHistory(
                user_id=user_id,
                query_lyrics=query_lyrics,
                recommendations=json.dumps(history_data, ensure_ascii=False)
            )
            db.session.add(history)
            db.session.commit()
            print(f"成功保存推荐历史，包含 {len(result.get('recommendations', []))} 个推荐")
        except Exception as e:
            db.session.rollback()
            print(f"保存推荐历史失败: {e}")
            import traceback
            traceback.print_exc()
    
    def get_history(self, user_id: int = None, limit: int = 10) -> List[Dict]:
        """获取推荐历史"""
        query = RecommendationHistory.query
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        histories = query.order_by(RecommendationHistory.created_at.desc()).limit(limit).all()
        return [h.to_dict() for h in histories]

