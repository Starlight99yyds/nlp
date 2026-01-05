"""
分析服务
整合情感、主题、韵律分析
"""
import json
from typing import Dict, List
import sys
import os

# 添加backend目录到路径
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from nlp_engine.sentiment import SentimentAnalyzer
from nlp_engine.theme import ThemeExtractor
from nlp_engine.rhythm import RhythmAnalyzer
from app.models import AnalysisHistory
from app import db


class AnalysisService:
    """分析服务类"""
    
    def __init__(self):
        self.sentiment_analyzer = SentimentAnalyzer()
        self.theme_extractor = ThemeExtractor()
        self.rhythm_analyzer = RhythmAnalyzer()
    
    def analyze_lyrics(self, lyrics: str, user_id: int = None) -> Dict:
        """完整分析歌词"""
        # 情感分析
        sentiment_result = self.sentiment_analyzer.analyze_lyrics(lyrics)
        
        # 主题分析
        theme_result = self.theme_extractor.analyze_theme(lyrics)
        
        # 韵律分析
        rhythm_result = self.rhythm_analyzer.analyze_rhythm(lyrics)
        
        # 结构分析
        structure_result = self._analyze_structure(lyrics)
        
        # 综合结果
        result = {
            'sentiment': sentiment_result,
            'theme': theme_result,
            'rhythm': rhythm_result,
            'structure': structure_result,
            'summary': self._generate_summary(sentiment_result, theme_result, rhythm_result)
        }
        
        # 保存分析历史
        self._save_history(lyrics, result, user_id)
        
        return result
    
    def _analyze_structure(self, lyrics: str) -> Dict:
        """分析歌曲结构"""
        lines = [line.strip() for line in lyrics.split('\n') if line.strip()]
        
        # 简单结构识别：通过重复度判断副歌
        line_freq = {}
        for line in lines:
            line_freq[line] = line_freq.get(line, 0) + 1
        
        # 找出重复的句子（可能是副歌）
        repeated_lines = [line for line, freq in line_freq.items() if freq > 1]
        
        structure = {
            'total_lines': len(lines),
            'unique_lines': len(set(lines)),
            'repetition_rate': round(len(repeated_lines) / len(lines), 2) if lines else 0,
            'likely_chorus': repeated_lines[:3] if repeated_lines else [],
            'estimated_sections': self._estimate_sections(lines)
        }
        
        return structure
    
    def _estimate_sections(self, lines: List[str]) -> List[Dict]:
        """估算段落结构"""
        sections = []
        current_section = {'type': '主歌', 'start': 0, 'lines': []}
        
        for i, line in enumerate(lines):
            current_section['lines'].append(line)
            
            # 每4-6行作为一个段落
            if len(current_section['lines']) >= 4:
                current_section['end'] = i
                sections.append(current_section)
                current_section = {'type': '主歌', 'start': i + 1, 'lines': []}
        
        if current_section['lines']:
            current_section['end'] = len(lines) - 1
            sections.append(current_section)
        
        return sections
    
    def _generate_summary(self, sentiment: Dict, theme: Dict, rhythm: Dict) -> str:
        """生成分析摘要"""
        summary_parts = []
        
        # 情感摘要
        summary_parts.append(f"整体情感基调：{sentiment['overall_tone']}（得分：{sentiment['overall_score']:.2f}）")
        
        # 主题摘要
        if theme['themes']:
            main_theme = theme['themes'][0]
            summary_parts.append(f"主要主题：{main_theme['theme']}（匹配度：{main_theme['score']}）")
        
        # 韵律摘要
        summary_parts.append(f"押韵模式：{rhythm['rhyme_pattern']['pattern']}，质量评分：{rhythm['overall_score']}")
        
        return "；".join(summary_parts)
    
    def _save_history(self, lyrics: str, result: Dict, user_id: int = None):
        """保存分析历史"""
        try:
            history = AnalysisHistory(
                user_id=user_id,
                lyrics=lyrics,
                sentiment_result=json.dumps(result['sentiment'], ensure_ascii=False),
                theme_result=json.dumps(result['theme'], ensure_ascii=False),
                rhythm_result=json.dumps(result['rhythm'], ensure_ascii=False)
            )
            db.session.add(history)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"保存分析历史失败: {e}")
    
    def get_history(self, user_id: int = None, limit: int = 10) -> List[Dict]:
        """获取分析历史"""
        query = AnalysisHistory.query
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        histories = query.order_by(AnalysisHistory.created_at.desc()).limit(limit).all()
        return [h.to_dict() for h in histories]

