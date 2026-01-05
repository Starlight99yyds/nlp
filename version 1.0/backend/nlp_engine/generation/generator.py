"""
歌词生成模块
智能歌词生成、上下文感知建议、风格转换
"""
import random
import jieba
from typing import List, Dict, Optional
from ..theme.extractor import ThemeExtractor
from ..sentiment.analyzer import SentimentAnalyzer


class LyricsGenerator:
    """歌词生成器"""
    
    # 风格模板
    STYLE_TEMPLATES = {
        '流行': {
            'structure': ['主歌', '副歌', '主歌', '副歌', '桥段', '副歌'],
            'keywords': ['爱', '心', '梦', '你', '我', '世界', '时间']
        },
        '古风': {
            'structure': ['主歌', '副歌', '主歌', '副歌'],
            'keywords': ['月', '风', '花', '雪', '江湖', '天涯', '相思', '离愁']
        },
        '摇滚': {
            'structure': ['主歌', '副歌', '主歌', '副歌', 'solo', '副歌'],
            'keywords': ['自由', '力量', '燃烧', '疯狂', '释放', '激情']
        },
        '抒情': {
            'structure': ['主歌', '副歌', '主歌', '副歌', '副歌'],
            'keywords': ['温柔', '回忆', '思念', '安静', '温暖', '拥抱']
        }
    }
    
    def __init__(self):
        self.theme_extractor = ThemeExtractor()
        self.sentiment_analyzer = SentimentAnalyzer()
    
    def generate_by_theme(self, theme: str, emotion: str = '中性', length: int = 4) -> str:
        """根据主题生成歌词"""
        # 获取主题相关关键词
        theme_keywords = self.theme_extractor.THEME_KEYWORDS.get(theme, [])
        
        # 生成歌词片段（模板方法）
        lines = []
        for i in range(length):
            # 组合关键词生成句子
            if theme_keywords:
                keyword = random.choice(theme_keywords)
                line = self._generate_line_with_keyword(keyword, emotion)
            else:
                line = self._generate_generic_line(emotion)
            lines.append(line)
        
        return '\n'.join(lines)
    
    def generate_by_context(self, previous_lines: List[str], emotion: str = '中性') -> str:
        """基于上下文生成下一句"""
        if not previous_lines:
            return self._generate_generic_line(emotion)
        
        # 分析前文主题和情感
        context_text = '\n'.join(previous_lines)
        themes = self.theme_extractor.classify_theme(context_text)
        sentiment = self.sentiment_analyzer.analyze_lyrics(context_text)
        
        # 选择主要主题
        main_theme = themes[0]['theme'] if themes else '通用'
        theme_keywords = self.theme_extractor.THEME_KEYWORDS.get(main_theme, [])
        
        # 生成符合上下文的句子
        if theme_keywords:
            keyword = random.choice(theme_keywords)
            return self._generate_line_with_keyword(keyword, emotion)
        else:
            return self._generate_generic_line(emotion)
    
    def generate_full_song(self, style: str = '流行', theme: str = '爱情', 
                          emotion: str = '积极') -> Dict:
        """生成完整歌曲结构"""
        template = self.STYLE_TEMPLATES.get(style, self.STYLE_TEMPLATES['流行'])
        structure = template['structure']
        
        song_parts = {}
        for part in structure:
            if part == '主歌':
                lines = [self.generate_by_theme(theme, emotion, 4) for _ in range(2)]
                song_parts[part] = '\n'.join(lines)
            elif part == '副歌':
                lines = [self.generate_by_theme(theme, emotion, 4)]
                song_parts[part] = '\n'.join(lines)
            elif part == '桥段':
                lines = [self.generate_by_theme(theme, '中性', 2)]
                song_parts[part] = '\n'.join(lines)
            else:
                song_parts[part] = self.generate_by_theme(theme, emotion, 2)
        
        # 组合成完整歌词
        full_lyrics = '\n\n'.join([f'[{part}]\n{content}' for part, content in song_parts.items()])
        
        return {
            'lyrics': full_lyrics,
            'structure': structure,
            'style': style,
            'theme': theme
        }
    
    def optimize_rhyme(self, line: str, target_rhyme: str) -> List[str]:
        """押韵优化建议"""
        # 获取同韵词建议（简化版）
        suggestions = []
        
        # 这里应该使用韵母词典，简化处理
        rhyme_words = self._get_rhyme_words(target_rhyme)
        
        for word in rhyme_words[:5]:
            # 替换最后一个字
            new_line = line[:-1] + word
            suggestions.append(new_line)
        
        return suggestions
    
    def convert_style(self, lyrics: str, target_style: str) -> str:
        """风格转换"""
        # 分析原歌词
        themes = self.theme_extractor.classify_theme(lyrics)
        main_theme = themes[0]['theme'] if themes else '通用'
        
        # 获取目标风格关键词
        target_template = self.STYLE_TEMPLATES.get(target_style, self.STYLE_TEMPLATES['流行'])
        target_keywords = target_template['keywords']
        
        # 替换关键词（简化版）
        converted_lines = []
        lines = lyrics.split('\n')
        for line in lines:
            if line.strip():
                # 尝试融入目标风格关键词
                if target_keywords and random.random() > 0.5:
                    keyword = random.choice(target_keywords)
                    converted_line = line + ' ' + keyword
                else:
                    converted_line = line
                converted_lines.append(converted_line)
        
        return '\n'.join(converted_lines)
    
    def _generate_line_with_keyword(self, keyword: str, emotion: str) -> str:
        """使用关键词生成句子"""
        templates = {
            '积极': [
                f'心中充满{keyword}',
                f'{keyword}让我勇敢',
                f'追寻{keyword}的梦想',
                f'{keyword}照亮前路'
            ],
            '消极': [
                f'失去{keyword}的痛',
                f'{keyword}已远去',
                f'怀念{keyword}的时光',
                f'{keyword}不再回来'
            ],
            '中性': [
                f'关于{keyword}的故事',
                f'{keyword}在记忆中',
                f'想起{keyword}的时候',
                f'{keyword}如风般'
            ]
        }
        
        templates_list = templates.get(emotion, templates['中性'])
        return random.choice(templates_list)
    
    def _generate_generic_line(self, emotion: str) -> str:
        """生成通用句子"""
        generic_lines = {
            '积极': ['阳光洒满大地', '希望在前方', '梦想在飞翔', '未来充满可能'],
            '消极': ['夜色笼罩一切', '回忆如潮水', '孤独的夜晚', '时间在流逝'],
            '中性': ['时光静静流淌', '记忆中的画面', '平凡的日子里', '生活的片段']
        }
        
        lines = generic_lines.get(emotion, generic_lines['中性'])
        return random.choice(lines)
    
    def _get_rhyme_words(self, rhyme: str) -> List[str]:
        """获取同韵字（简化版）"""
        # 实际应使用韵母词典
        common_rhymes = {
            'a': ['啊', '他', '她', '它', '那', '大', '家'],
            'i': ['你', '里', '起', '地', '意', '气', '力'],
            'u': ['路', '处', '度', '苦', '数', '树', '住']
        }
        return common_rhymes.get(rhyme, ['的', '了', '在', '是', '有'])







