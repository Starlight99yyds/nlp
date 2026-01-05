"""
推荐系统模块
个性化推荐、可解释推荐、相似度分析
"""
from typing import List, Dict, Optional
from ..theme.extractor import ThemeExtractor
from ..sentiment.analyzer import SentimentAnalyzer
from ..rhythm.analyzer import RhythmAnalyzer
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class MusicRecommender:
    """音乐推荐器"""
    
    def __init__(self):
        self.theme_extractor = ThemeExtractor()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.rhythm_analyzer = RhythmAnalyzer()
        self.vectorizer = TfidfVectorizer(max_features=100)
        self.song_database = []  # 存储歌曲数据库
    
    def add_song_to_database(self, song: Dict):
        """添加歌曲到数据库"""
        self.song_database.append(song)
    
    def calculate_similarity(self, lyrics1: str, lyrics2: str) -> float:
        """计算两首歌词的相似度"""
        # 主题相似度
        themes1 = self.theme_extractor.classify_theme(lyrics1)
        themes2 = self.theme_extractor.classify_theme(lyrics2)
        theme_sim = self._theme_similarity(themes1, themes2)
        
        # 情感相似度
        sent1 = self.sentiment_analyzer.analyze_lyrics(lyrics1)
        sent2 = self.sentiment_analyzer.analyze_lyrics(lyrics2)
        sent_sim = 1 - abs(sent1['overall_score'] - sent2['overall_score'])
        
        # 文本相似度
        text_sim = self._text_similarity(lyrics1, lyrics2)
        
        # 综合相似度
        overall_sim = (theme_sim * 0.4 + sent_sim * 0.3 + text_sim * 0.3)
        
        return round(overall_sim, 3)
    
    def recommend_songs(self, query_lyrics: str, top_k: int = 5, 
                       user_preferences: Optional[Dict] = None) -> List[Dict]:
        """推荐相似歌曲"""
        if not self.song_database:
            return []
        
        similarities = []
        for song in self.song_database:
            sim = self.calculate_similarity(query_lyrics, song.get('lyrics', ''))
            
            # 考虑用户偏好
            if user_preferences:
                preference_boost = self._calculate_preference_boost(song, user_preferences)
                sim = sim * (1 + preference_boost * 0.2)
            
            similarities.append({
                'song': song,
                'similarity': sim,
                'reasons': self._generate_reasons(query_lyrics, song.get('lyrics', ''))
            })
        
        # 排序并返回top_k
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        
        return similarities[:top_k]
    
    def explain_recommendation(self, query_lyrics: str, recommended_song: Dict) -> str:
        """生成推荐理由"""
        reasons = self._generate_reasons(query_lyrics, recommended_song.get('lyrics', ''))
        
        explanation_parts = []
        if reasons.get('theme_match'):
            explanation_parts.append(f"主题相似：都涉及{reasons['theme_match']}")
        if reasons.get('sentiment_match'):
            explanation_parts.append(f"情感相似：{reasons['sentiment_match']}")
        if reasons.get('style_match'):
            explanation_parts.append(f"风格相似：{reasons['style_match']}")
        
        if explanation_parts:
            return "；".join(explanation_parts)
        else:
            return "基于歌词内容的综合相似度推荐"
    
    def build_knowledge_graph(self, songs: List[Dict]) -> Dict:
        """构建音乐知识图谱"""
        # 提取实体和关系
        artists = set()
        themes = set()
        styles = set()
        
        for song in songs:
            if 'artist' in song:
                artists.add(song['artist'])
            if 'theme' in song:
                themes.add(song['theme'])
            if 'style' in song:
                styles.add(song['style'])
        
        # 构建关系
        relationships = []
        for song in songs:
            if 'artist' in song and 'theme' in song:
                relationships.append({
                    'source': song['artist'],
                    'target': song['theme'],
                    'type': '创作主题'
                })
            if 'theme' in song and 'style' in song:
                relationships.append({
                    'source': song['theme'],
                    'target': song['style'],
                    'type': '主题风格'
                })
        
        return {
            'nodes': [
                {'id': artist, 'type': 'artist', 'label': artist} for artist in artists
            ] + [
                {'id': theme, 'type': 'theme', 'label': theme} for theme in themes
            ] + [
                {'id': style, 'type': 'style', 'label': style} for style in styles
            ],
            'relationships': relationships
        }
    
    def _theme_similarity(self, themes1: List[Dict], themes2: List[Dict]) -> float:
        """计算主题相似度"""
        if not themes1 or not themes2:
            return 0.0
        
        theme_names1 = {t['theme'] for t in themes1}
        theme_names2 = {t['theme'] for t in themes2}
        
        intersection = theme_names1 & theme_names2
        union = theme_names1 | theme_names2
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        try:
            vectors = self.vectorizer.fit_transform([text1, text2])
            similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
            return float(similarity)
        except:
            return 0.0
    
    def _calculate_preference_boost(self, song: Dict, preferences: Dict) -> float:
        """计算用户偏好加成"""
        boost = 0.0
        
        if 'preferred_themes' in preferences:
            if song.get('theme') in preferences['preferred_themes']:
                boost += 0.5
        
        if 'preferred_styles' in preferences:
            if song.get('style') in preferences['preferred_styles']:
                boost += 0.5
        
        return boost
    
    def _generate_reasons(self, lyrics1: str, lyrics2: str) -> Dict:
        """生成相似原因"""
        themes1 = self.theme_extractor.classify_theme(lyrics1)
        themes2 = self.theme_extractor.classify_theme(lyrics2)
        
        common_themes = [t['theme'] for t in themes1 if t['theme'] in [t2['theme'] for t2 in themes2]]
        
        sent1 = self.sentiment_analyzer.analyze_lyrics(lyrics1)
        sent2 = self.sentiment_analyzer.analyze_lyrics(lyrics2)
        
        reasons = {}
        if common_themes:
            reasons['theme_match'] = '、'.join(common_themes[:2])
        
        if abs(sent1['overall_score'] - sent2['overall_score']) < 0.2:
            reasons['sentiment_match'] = f"情感基调相似（{sent1['overall_tone']} vs {sent2['overall_tone']}）"
        
        return reasons







