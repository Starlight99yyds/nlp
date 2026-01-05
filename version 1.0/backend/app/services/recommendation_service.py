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
        """推荐歌曲（改进算法：基于主题、关键词和歌词相似度）"""
        # 提取关键词和主题
        keywords = self._extract_keywords_from_lyrics(query_lyrics)
        themes = self._extract_themes_from_lyrics(query_lyrics)
        
        # 从多个关键词和主题搜索，增加多样性
        all_songs = []
        seen_song_ids = set()
        
        try:
            # 1. 使用关键词搜索
            for keyword in keywords[:3]:  # 使用前3个关键词
                songs = self.music_api.search_songs(keyword, platform='netease', limit=top_k * 2)
                for song in songs:
                    song_key = f"{song.get('title', '')}_{song.get('artist', '')}"
                    if song_key not in seen_song_ids:
                        seen_song_ids.add(song_key)
                        all_songs.append(song)
            
            # 2. 使用主题搜索
            for theme in themes[:2]:  # 使用前2个主题
                songs = self.music_api.search_songs(theme, platform='netease', limit=top_k * 2)
                for song in songs:
                    song_key = f"{song.get('title', '')}_{song.get('artist', '')}"
                    if song_key not in seen_song_ids:
                        seen_song_ids.add(song_key)
                        all_songs.append(song)
            
            # 3. 如果关键词和主题搜索结果不足，使用完整歌词的关键短语搜索
            if len(all_songs) < top_k * 2:
                phrases = self._extract_phrases(query_lyrics)
                for phrase in phrases[:2]:
                    songs = self.music_api.search_songs(phrase, platform='netease', limit=top_k)
                    for song in songs:
                        song_key = f"{song.get('title', '')}_{song.get('artist', '')}"
                        if song_key not in seen_song_ids:
                            seen_song_ids.add(song_key)
                            all_songs.append(song)
        except Exception as e:
            print(f"音乐平台API调用失败: {e}")
        
        # 如果API有结果，计算综合相似度并排序
        if all_songs:
            recommendations = []
            for song in all_songs[:top_k * 3]:  # 取前3倍数量用于计算相似度
                # 获取歌词
                lyrics = self.music_api.get_song_lyrics(song['id'], 'netease')
                if lyrics:
                    song['lyrics'] = lyrics
                    # 计算综合相似度（关键词相似度 + 主题相似度 + 歌词内容相似度）
                    keyword_sim = self._calculate_keyword_similarity(keywords, lyrics)
                    theme_sim = self._calculate_theme_similarity(themes, lyrics)
                    content_sim = self._calculate_similarity(query_lyrics, lyrics)
                    
                    # 综合得分
                    overall_similarity = (keyword_sim * 0.3 + theme_sim * 0.3 + content_sim * 0.4)
                    
                    recommendations.append({
                        'song': song,
                        'similarity': overall_similarity,
                        'explanation': self._generate_explanation(query_lyrics, lyrics, keywords, themes),
                        'platform': 'netease',
                        'details': {
                            'keyword_similarity': keyword_sim,
                            'theme_similarity': theme_sim,
                            'content_similarity': content_sim
                        }
                    })
            
            # 按相似度排序，取前top_k个
            recommendations.sort(key=lambda x: x['similarity'], reverse=True)
            recommendations = recommendations[:top_k]
        else:
            # 使用本地推荐系统
            recommendations = self.recommender.recommend_songs(
                query_lyrics, top_k, user_preferences
            )
            
            # 添加推荐理由
            for rec in recommendations:
                rec['explanation'] = self.recommender.explain_recommendation(
                    query_lyrics, rec['song']
                )
        
        result = {
            'query_lyrics': query_lyrics,
            'recommendations': [
                {
                    'song': rec['song'],
                    'similarity': rec.get('similarity', 0.8),
                    'explanation': rec.get('explanation', '基于歌词相似度的推荐'),
                    'reasons': rec.get('reasons', {}),
                    'platform': rec.get('platform', 'local'),
                    'details': rec.get('details', {})
                }
                for rec in recommendations
            ]
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
        """计算关键词相似度"""
        import jieba
        lyrics_words = set(jieba.cut(lyrics))
        matched = sum(1 for kw in keywords if kw in lyrics_words)
        return matched / len(keywords) if keywords else 0.0
    
    def _calculate_theme_similarity(self, themes: ListType[str], lyrics: str) -> float:
        """计算主题相似度"""
        import sys
        import os
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)
        
        from nlp_engine.theme import ThemeExtractor
        extractor = ThemeExtractor()
        lyrics_themes = extractor.classify_theme(lyrics)
        lyrics_theme_names = [t['theme'] for t in lyrics_themes]
        
        matched = sum(1 for theme in themes if theme in lyrics_theme_names)
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
        """计算两段歌词的相似度"""
        import jieba
        from collections import Counter
        
        # 分词
        words1 = set(jieba.cut(lyrics1))
        words2 = set(jieba.cut(lyrics2))
        
        # 过滤停用词
        stopwords = {'的', '了', '在', '是', '我', '你', '他', '她', '它', '这', '那', '有', '和', '与', '或'}
        words1 = {w for w in words1 if len(w) > 1 and w not in stopwords}
        words2 = {w for w in words2 if len(w) > 1 and w not in stopwords}
        
        # 计算Jaccard相似度
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def _generate_explanation(self, query_lyrics: str, song_lyrics: str, keywords: ListType[str]) -> str:
        """生成推荐理由"""
        if keywords:
            return f"基于关键词'{keywords[0]}'的推荐，歌词主题相似"
        return "基于歌词内容和主题的相似度推荐"
    
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
        """保存推荐历史"""
        try:
            history = RecommendationHistory(
                user_id=user_id,
                query_lyrics=query_lyrics,
                recommendations=json.dumps(result, ensure_ascii=False)
            )
            db.session.add(history)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"保存推荐历史失败: {e}")
    
    def get_history(self, user_id: int = None, limit: int = 10) -> List[Dict]:
        """获取推荐历史"""
        query = RecommendationHistory.query
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        histories = query.order_by(RecommendationHistory.created_at.desc()).limit(limit).all()
        return [h.to_dict() for h in histories]

