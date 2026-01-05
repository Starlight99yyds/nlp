"""
生成服务
歌词生成、优化、风格转换
集成DeepSeek API
"""
import json
from typing import Dict, List, Optional
import sys
import os

# 添加backend目录到路径
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from nlp_engine.generation import LyricsGenerator
from app.models import GenerationHistory
from app import db
from app.utils.deepseek_client import DeepSeekClient


class GenerationService:
    """生成服务类"""
    
    def __init__(self):
        self.generator = LyricsGenerator()
        self.deepseek_client = DeepSeekClient()
    
    def generate_by_theme(self, theme: str, emotion: Optional[str] = None, 
                         length: int = 16, user_id: int = None) -> Dict:
        """根据主题生成歌词"""
        # 使用DeepSeek生成更高质量的歌词
        prompt = f"创作一首关于{theme}主题的歌词"
        if emotion:
            prompt += f"，情感基调为{emotion}"
        prompt += f"，共约{length}行"
        
        lyrics = self.deepseek_client.generate_lyrics(
            prompt=prompt,
            theme=theme,
            emotion=emotion,
            length=length
        )
        
        result = {
            'lyrics': lyrics,
            'theme': theme,
            'emotion': emotion or '未指定',
            'length': length
        }
        
        self._save_history('主题生成', lyrics, theme, user_id)
        
        return result
    
    def generate_by_context(self, previous_lines: List[str], 
                           emotion: Optional[str] = None, user_id: int = None) -> Dict:
        """基于上下文生成（生成更完整的歌词，不只是下一句）"""
        # 使用DeepSeek生成更完整的后续歌词
        prompt = "基于以下上下文，继续创作歌词，保持连贯性和风格一致"
        
        lyrics = self.deepseek_client.generate_lyrics(
            prompt=prompt,
            context=previous_lines,
            emotion=emotion,
            length=8  # 生成8行，更完整
        )
        
        result = {
            'lyrics': lyrics,  # 返回完整歌词而不只是一句
            'context': previous_lines,
            'emotion': emotion or '未指定'
        }
        
        return result
    
    def generate_full_song(self, style: str = '流行', theme: str = '爱情',
                          emotion: Optional[str] = None, user_idea: Optional[str] = None,
                          user_id: int = None) -> Dict:
        """生成完整歌曲"""
        # 使用DeepSeek生成完整歌曲
        prompt = f"创作一首完整的{style}风格歌曲"
        if theme:
            prompt += f"，主题为{theme}"
        if user_idea:
            prompt += f"，用户想法：{user_idea}"
        
        lyrics = self.deepseek_client.generate_lyrics(
            prompt=prompt,
            style=style,
            theme=theme,
            emotion=emotion,
            length=32,  # 生成更长的完整歌词
            user_idea=user_idea
        )
        
        result = {
            'lyrics': lyrics,
            'structure': ['主歌', '副歌', '主歌', '副歌', '桥段', '副歌'],
            'style': style,
            'theme': theme
        }
        
        self._save_history('完整生成', lyrics, style, user_id)
        
        return result
    
    def optimize_rhyme(self, line: str, target_rhyme: str) -> Dict:
        """押韵优化"""
        suggestions = self.generator.optimize_rhyme(line, target_rhyme)
        
        return {
            'original': line,
            'target_rhyme': target_rhyme,
            'suggestions': suggestions
        }
    
    def convert_style(self, lyrics: str, target_style: str, user_id: int = None) -> Dict:
        """风格转换（优先使用DeepSeek API进行整体风格转换）"""
        # 优先使用DeepSeek API
        converted = self.deepseek_client.convert_style(lyrics, target_style)
        
        # 如果API返回原歌词或失败，使用本地生成器作为备用
        if not converted or converted == lyrics or len(converted) < len(lyrics) * 0.5:
            converted = self.generator.convert_style(lyrics, target_style)
        
        result = {
            'original': lyrics,
            'converted': converted,
            'target_style': target_style
        }
        
        return result
    
    def continue_conversation(self, previous_lyrics: str, user_feedback: str, 
                             user_id: int = None) -> Dict:
        """继续对话，根据用户反馈修改歌词"""
        improved_lyrics = self.deepseek_client.continue_conversation(
            previous_lyrics, user_feedback
        )
        
        result = {
            'previous_lyrics': previous_lyrics,
            'improved_lyrics': improved_lyrics,
            'user_feedback': user_feedback
        }
        
        return result
    
    def evaluate_lyrics(self, lyrics: str) -> Dict:
        """综合评估歌词（改进的评估方式）"""
        import sys
        import os
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)
        from nlp_engine.sentiment import SentimentAnalyzer
        from nlp_engine.rhythm import RhythmAnalyzer
        from nlp_engine.theme import ThemeExtractor
        
        analyzer = SentimentAnalyzer()
        rhythm_analyzer = RhythmAnalyzer()
        theme_extractor = ThemeExtractor()
        
        # 情感分析
        sentiment_result = analyzer.analyze_lyrics(lyrics)
        
        # 韵律分析
        rhythm_result = rhythm_analyzer.analyze_rhythm(lyrics)
        
        # 主题分析
        theme_result = theme_extractor.analyze_theme(lyrics)
        
        # 计算综合评分
        scores = {
            '情感表达': sentiment_result['overall_score'],
            '韵律质量': rhythm_result['overall_score'],
            '主题明确度': theme_result['themes'][0]['score'] if theme_result['themes'] else 0.5
        }
        
        overall_score = sum(scores.values()) / len(scores)
        
        # 评估建议
        suggestions = []
        if scores['韵律质量'] < 0.6:
            suggestions.append('建议改进押韵，使歌词更加朗朗上口')
        if scores['情感表达'] < 0.5:
            suggestions.append('建议增强情感表达，使歌词更有感染力')
        if scores['主题明确度'] < 0.6:
            suggestions.append('建议明确主题，使歌词更有聚焦性')
        
        return {
            'overall_score': round(overall_score, 2),
            'scores': scores,
            'sentiment': sentiment_result['overall_tone'],
            'rhythm_pattern': rhythm_result['rhyme_pattern']['pattern'],
            'main_theme': theme_result['themes'][0]['theme'] if theme_result['themes'] else '未明确',
            'suggestions': suggestions,
            'assessment': self._get_assessment(overall_score)
        }
    
    def _get_assessment(self, score: float) -> str:
        """根据评分给出评估"""
        if score >= 0.8:
            return '优秀：歌词质量很高，各方面表现均衡'
        elif score >= 0.6:
            return '良好：歌词质量不错，有改进空间'
        elif score >= 0.4:
            return '一般：歌词基本合格，建议进一步优化'
        else:
            return '待改进：建议重新审视歌词的各个方面'
    
    def _save_history(self, prompt: str, lyrics: str, style: str = None, user_id: int = None):
        """保存生成历史"""
        try:
            history = GenerationHistory(
                user_id=user_id,
                prompt=prompt,
                generated_lyrics=lyrics,
                style=style
            )
            db.session.add(history)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"保存生成历史失败: {e}")
    
    def get_history(self, user_id: int = None, limit: int = 10) -> List[Dict]:
        """获取生成历史"""
        from app.models import GenerationHistory
        
        query = GenerationHistory.query
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        histories = query.order_by(GenerationHistory.created_at.desc()).limit(limit).all()
        return [h.to_dict() for h in histories]

