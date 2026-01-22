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
from app.utils.deepseek_client import DeepSeekClient


class AnalysisService:
    """分析服务类"""
    
    def __init__(self):
        self.sentiment_analyzer = SentimentAnalyzer()
        self.theme_extractor = ThemeExtractor()
        self.rhythm_analyzer = RhythmAnalyzer()
        self.deepseek_client = DeepSeekClient()
    
    def analyze_lyrics(self, lyrics: str, user_id: int = None) -> Dict:
        """完整分析歌词"""
        # 主题分析
        theme_result = self.theme_extractor.analyze_theme(lyrics)
        
        # 使用DeepSeek进行情感分析（完全交给DeepSeek）
        deepseek_analysis = self._deepseek_sentiment_analysis(lyrics)
        
        # 如果DeepSeek分析成功，使用DeepSeek的结果；否则使用本地分析作为备用
        if deepseek_analysis and deepseek_analysis.get('sentiment'):
            sentiment_result = self._format_deepseek_sentiment(deepseek_analysis['sentiment'], lyrics)
        else:
            # 备用：使用本地分析
            sentiment_result = self.sentiment_analyzer.analyze_lyrics(lyrics)
            sentiment_result['source'] = 'local_fallback'
        
        # 如果DeepSeek有主题分析，也添加到结果中，并合并到主题列表
        if deepseek_analysis and deepseek_analysis.get('theme'):
            deepseek_themes = deepseek_analysis['theme']
            theme_result['deepseek_themes'] = deepseek_themes
            
            # 将DeepSeek的主题也添加到themes列表中（如果本地没有检测到）
            if not theme_result.get('themes') or len(theme_result.get('themes', [])) == 0:
                # 如果本地没有检测到主题，使用DeepSeek的主题
                theme_result['themes'] = [{'theme': t, 'score': 0.8} for t in deepseek_themes[:5]]
                theme_result['primary_theme'] = deepseek_themes[0] if deepseek_themes else '未知'
            else:
                # 合并DeepSeek的主题到现有主题列表
                existing_themes = {t['theme'] for t in theme_result.get('themes', [])}
                for dt in deepseek_themes:
                    if dt not in existing_themes:
                        theme_result['themes'].append({'theme': dt, 'score': 0.7})
        
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
    
    def _deepseek_sentiment_analysis(self, lyrics: str) -> Dict:
        """使用DeepSeek API进行情感分析（完全交给DeepSeek）"""
        if not self.deepseek_client.api_key or not self.deepseek_client.client:
            return None
        
        prompt = f"""请对以下歌词进行深入、多元、丰富的情感分析，以JSON格式返回结果。

要求：
1. 情感分析要深入细致，识别多种情感层次和细微差别
2. 不仅要分析整体情感，还要逐句分析每句的情感变化
3. 识别复合情感（如：忧郁中带着希望、孤独中带着坚强等）
4. 分析情感强度变化曲线
5. 识别情感转折点和情感高潮
6. 提供丰富的情感描述，包括情感色彩、情感深度、情感变化等
7. **重要：情感基调（tone）应该包含多个独立的2字词语，用顿号、逗号分隔，例如："希望、浪漫、温柔"或"忧郁、坚强、温暖"。如果必须使用连接词，应该用顿号（、）或逗号（，）分隔多个词语，不要用"与"、"和"等连接词。优先返回3-6个独立的2字词语，例如："希望、浪漫、温柔、怀旧、期待"**
8. **重要：情感类型（emotion_type）应该使用多个独立的2字词语，用顿号、逗号分隔，例如："希望、浪漫、温柔"或"忧郁、坚强、温暖"。优先返回2-4个独立的2字词语**
9. **关键：情感总结（emotion_summary）字段，必须包含3-6个不同的2字情感词语（优先2字，如果没有合适的2字词可以使用3-4字），用顿号（、）分隔，例如："忧郁、希望、浪漫、孤独、温暖"或"怀旧、思念、坚强、期待"。这些词语应该全面概括歌词的情感特征，必须是独立的词语，不要用连接词。**
10. **关键：必须提供 emotion_distribution 字段，包含3-8个不同的情感词语，每个词语必须是2字的中文词语（优先2字，如果确实没有合适的2字词，可以使用3-4字），及其比例（0-1之间的浮点数，总和应该接近1.0）。每个情感词语应该是独立的中文词语，优先使用2字词语，如："忧郁"、"希望"、"浪漫"、"孤独"、"温暖"、"怀旧"、"坚强"、"快乐"、"悲伤"、"思念"、"期待"、"失落"、"甜蜜"、"温馨"、"寂寞"、"回忆"、"怀念"、"积极"、"向上"、"乐观"、"阳光"、"低沉"、"沮丧"、"悲观"、"平和"、"平静"、"淡然"、"愉悦"、"欢快"、"深沉"、"内敛"、"热烈"、"激情"、"宁静"、"安详"、"惆怅"、"落寞"、"明亮"、"柔和"、"生机"、"自然"、"活力"、"自由"、"深邃"、"热情"、"痛苦"、"感动"、"感慨"、"释然"、"坦然"、"坚强"、"温柔"、"梦幻"、"迷离"、"清冷"、"冷静"、"愤怒"、"恼火"、"兴奋"、"振奋"、"热血"、"澎湃"等。不要用复合词或长句子，每个词语必须是独立的2字中文词语（优先2字）。比例应该反映该情感在整首歌词中的占比。**

返回格式：
{{
    "sentiment": {{
        "tone": "主要情感基调（必须用4-12字中文词语或短语，包含3-5个不同的情感维度，体现情感的丰富性和层次感，如：浪漫忧伤交织温柔怀旧、温柔怀旧中带着希望与期待、快乐积极充满活力阳光、孤独坚强中透着温暖思念等，必须包含多个情感词语，不要用单一词汇）",
        "intensity": 情感强度（1-10的整数）,
        "description": "详细的情感描述（3-5句话，要深入分析情感的多层次和丰富性）",
        "overall_score": 整体情感得分（0-1之间的浮点数，0.5为中性，>0.5为积极，<0.5为消极）,
        "emotion_type": "具体情感类型（必须用4-10字中文词语或短语，包含2-4个不同的情感词语，如：忧郁希望浪漫、快乐浪漫温馨、孤独坚强温暖、怀旧温暖思念、悲伤忧郁中带着希望等，必须包含多个情感词语，不要用单一词汇，不要用英文）",
        "emotion_summary": "情感总结（必须包含3-6个不同的2-4字情感词语，用顿号或逗号分隔，例如：忧郁、希望、浪漫、孤独、温暖 或 怀旧、思念、坚强、期待、温馨）",
        "emotion_distribution": {{
            "忧郁": 0.25,
            "希望": 0.20,
            "浪漫": 0.15,
            "孤独": 0.15,
            "温暖": 0.10,
            "怀旧": 0.10,
            "坚强": 0.05
        }},
        "emotion_distribution_proportions": {{
            "忧郁": 0.25,
            "希望": 0.20,
            "浪漫": 0.15,
            "孤独": 0.15,
            "温暖": 0.10,
            "怀旧": 0.10,
            "坚强": 0.05
        }},
        "emotion_layers": ["情感层次1", "情感层次2", "情感层次3"],
        "emotion_transitions": ["情感转折点描述1", "情感转折点描述2"],
        "emotional_highlights": ["情感高潮1", "情感高潮2"],
        "sentence_analyses": [
            {{
                "sentence": "句子1",
                "score": 0.7,
                "category": "positive",
                "emotion_type": "具体情感类型（用2-6字中文词语或短语，可以包含复合情感，如：忧郁希望、快乐浪漫等，不要用单一词汇，不要用英文）",
                "emotion_description": "该句的详细情感描述",
                "intensity": 0.8
            }},
            {{
                "sentence": "句子2",
                "score": 0.3,
                "category": "negative",
                "emotion_type": "具体情感类型",
                "emotion_description": "该句的详细情感描述",
                "intensity": 0.6
            }}
        ]
    }},
    "theme": ["主题1", "主题2", "主题3"]
}}

**特别注意：emotion_distribution 必须包含至少3-8个不同的情感词语（优先2字，如果确实没有合适的2字词，可以使用3-4字），每个情感词语对应一个比例值（0-1之间），所有比例值的总和应该接近1.0。情感词语应该是独立的中文词语，优先使用2字词语，如："忧郁"、"希望"、"浪漫"、"孤独"、"温暖"、"怀旧"、"坚强"、"快乐"、"悲伤"、"思念"、"期待"、"失落"、"甜蜜"、"温馨"、"寂寞"、"回忆"、"怀念"、"积极"、"向上"、"乐观"、"阳光"、"低沉"、"沮丧"、"悲观"、"平和"、"平静"、"淡然"、"愉悦"、"欢快"、"深沉"、"内敛"、"热烈"、"激情"、"宁静"、"安详"、"惆怅"、"落寞"、"明亮"、"柔和"、"生机"、"自然"、"活力"、"自由"、"深邃"、"热情"、"痛苦"、"感动"、"感慨"、"释然"、"坦然"、"坚强"、"温柔"、"梦幻"、"迷离"、"清冷"、"冷静"、"愤怒"、"恼火"、"兴奋"、"振奋"、"热血"、"澎湃"等。每个词语必须是2字的中文词语（优先2字），不要用复合词、短语或长句子。**

歌词内容：
{lyrics}

请直接返回JSON，不要添加任何其他文字。确保分析深入、多元、丰富。"""
        
        try:
            response = self.deepseek_client.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {'role': 'system', 'content': '你是一位资深的歌词情感分析专家，擅长深入、多元、丰富地分析歌词的情感。你能够识别情感的多个层次、细微差别、复合情感、情感转折和情感高潮。请以JSON格式返回详细、深入、多元的分析结果。'},
                    {'role': 'user', 'content': prompt}
                ],
                temperature=0.7,  # 提高temperature以获得更丰富的分析
                max_tokens=3000,  # 增加token数以支持更详细的分析
                stream=False
            )
            
            import json
            result_text = response.choices[0].message.content.strip()
            # 尝试提取JSON（可能包含markdown代码块）
            if '```json' in result_text:
                result_text = result_text.split('```json')[1].split('```')[0].strip()
            elif '```' in result_text:
                result_text = result_text.split('```')[1].split('```')[0].strip()
            
            analysis = json.loads(result_text)
            return analysis
        except Exception as e:
            print(f"DeepSeek情感分析失败: {e}")
            return None
    
    def _simplify_emotion_tone(self, tone: str) -> str:
        """保留情感基调的丰富性，允许3-8字的复合情感描述"""
        if not tone:
            return '中性'
        
        tone_clean = tone.strip()
        
        # 如果已经是合适长度的描述（3-8字），直接返回，保留丰富性
        if 3 <= len(tone_clean) <= 8:
            return tone_clean
        
        # 如果超过8字，尝试提取关键情感词组合（保留2-3个关键词）
        if len(tone_clean) > 8:
            import re
            emotion_keywords = [
                '浪漫', '温柔', '忧伤', '怀旧', '快乐', '孤独', '希望', '期待',
                '悲伤', '忧郁', '甜蜜', '温馨', '寂寞', '思念', '回忆', '怀念',
                '积极', '消极', '平和', '平静', '淡然', '中性', '愉悦', '欢快',
                '深沉', '内敛', '热烈', '激情', '宁静', '安详', '惆怅', '落寞',
                '坚强', '温暖', '明亮', '柔和', '生机', '自然', '活力', '自由',
                '深邃', '热情', '痛苦', '沮丧', '悲观', '交织', '带着', '透着',
                '感动', '感慨', '释然', '坦然', '超然', '淡然', '阳光', '向上'
            ]
            
            found_keywords = []
            for keyword in emotion_keywords:
                if keyword in tone_clean:
                    found_keywords.append(keyword)
            
            # 组合3-5个关键词，形成4-12字的描述
            if found_keywords:
                if len(found_keywords) >= 3:
                    # 尝试组合，保留连接词如"中"、"带着"、"交织"等
                    combined = ''.join(found_keywords[:min(5, len(found_keywords))])
                    if 4 <= len(combined) <= 12:
                        return combined
                    elif len(combined) > 12:
                        # 如果太长，只取前4个关键词
                        return ''.join(found_keywords[:4])
                elif len(found_keywords) >= 2:
                    combined = ''.join(found_keywords[:2])
                    if len(combined) < 4:
                        # 如果太短，添加一个相关词语
                        return combined + '情感'
                    return combined
                else:
                    return found_keywords[0] + '情感'
            
            # 如果没找到关键词，提取前4-12个中文字符
            chinese_chars = re.findall(r'[\u4e00-\u9fa5]', tone_clean)
            if chinese_chars:
                if len(chinese_chars) <= 12:
                    return ''.join(chinese_chars)
                else:
                    return ''.join(chinese_chars[:12])
        
        # 如果太短（少于4字），尝试补充
        if len(tone_clean) < 4:
            return tone_clean + '情感丰富'
        
        return tone_clean
    
    def _format_deepseek_sentiment(self, sentiment_data: Dict, lyrics: str) -> Dict:
        """格式化DeepSeek的情感分析结果，使其与本地分析结果格式兼容"""
        lines = [line.strip() for line in lyrics.split('\n') if line.strip()]
        
        # 翻译情感类型（英文转中文）
        emotion_translations = {
            'melancholic': '忧郁',
            'joyful': '快乐',
            'romantic': '浪漫',
            'lonely': '孤独',
            'hopeful': '希望',
            'nostalgic': '怀旧',
            'sad': '悲伤',
            'happy': '快乐',
            'angry': '愤怒',
            'peaceful': '平和',
            'excited': '兴奋',
            'calm': '平静',
            'aesthetic_refreshing_melancholy': '清新忧郁',
            'aesthetic_transient_melancholy': '短暂忧郁',
            'intense_connection_awe': '强烈连接',
            'intense_paradoxical': '矛盾强烈',
            'intimate_anticipatory': '亲密期待',
            'nostalgic_joyful': '怀旧快乐',
            'romantic_dreamy': '浪漫梦幻',
            'sensual_elusive': '感性难捉',
            'subtle_melancholy': '微妙忧郁'
        }
        
        # 构建句子分析列表
        sentence_analyses = []
        if 'sentence_analyses' in sentiment_data and sentiment_data['sentence_analyses']:
            # 使用DeepSeek返回的详细句子分析
            for sa in sentiment_data['sentence_analyses']:
                emotion_type = sa.get('emotion_type', sentiment_data.get('emotion_type', '中性'))
                # 翻译英文情感类型为中文
                if emotion_type and emotion_type in emotion_translations:
                    emotion_type = emotion_translations[emotion_type]
                elif emotion_type and any(c.isascii() and c.isalpha() for c in emotion_type):
                    # 如果包含英文字母，尝试翻译
                    emotion_type = emotion_translations.get(emotion_type.lower(), emotion_type)
                
                sentence_analyses.append({
                    'sentence': sa.get('sentence', ''),
                    'score': sa.get('score', sentiment_data.get('overall_score', 0.5)),
                    'category': sa.get('category', 'neutral'),
                    'emotion_type': emotion_type,
                    'emotion_description': sa.get('emotion_description', ''),
                    'intensity': sa.get('intensity', abs(sa.get('score', 0.5) - 0.5) * 2)
                })
        else:
            # 如果没有句子分析，为每行创建默认分析
            default_emotion_type = sentiment_data.get('emotion_type', sentiment_data.get('tone', '中性'))
            # 翻译英文情感类型为中文
            if default_emotion_type and default_emotion_type in emotion_translations:
                default_emotion_type = emotion_translations[default_emotion_type]
            elif default_emotion_type and any(c.isascii() and c.isalpha() for c in default_emotion_type):
                default_emotion_type = emotion_translations.get(default_emotion_type.lower(), default_emotion_type)
            
            for line in lines:
                sentence_analyses.append({
                    'sentence': line,
                    'score': sentiment_data.get('overall_score', 0.5),
                    'category': 'positive' if sentiment_data.get('overall_score', 0.5) > 0.5 else 'negative',
                    'emotion_type': default_emotion_type,
                    'emotion_description': '',
                    'intensity': abs(sentiment_data.get('overall_score', 0.5) - 0.5) * 2
                })
        
        # 构建时间线数据
        timeline = []
        for i, sa in enumerate(sentence_analyses):
            emotion_type_timeline = sa.get('emotion_type', sentiment_data.get('tone', '中性'))
            # 翻译英文情感类型为中文
            if emotion_type_timeline and emotion_type_timeline in emotion_translations:
                emotion_type_timeline = emotion_translations[emotion_type_timeline]
            elif emotion_type_timeline and any(c.isascii() and c.isalpha() for c in emotion_type_timeline):
                emotion_type_timeline = emotion_translations.get(emotion_type_timeline.lower(), emotion_type_timeline)
            
            timeline.append({
                'index': i,
                'score': sa.get('score', sentiment_data.get('overall_score', 0.5)),
                'category': sa.get('category', 'neutral'),
                'emotion_type': emotion_type_timeline
            })
        
        overall_tone = sentiment_data.get('tone', '中性')
        emotion_type = sentiment_data.get('emotion_type', overall_tone)
        emotion_summary = sentiment_data.get('emotion_summary', '')
        
        # 保留情感基调的丰富性（4-12字，包含多个情感词语）
        translated_emotion = self._simplify_emotion_tone(overall_tone)
        
        # 如果有emotion_summary，优先使用它作为情感总结
        if emotion_summary:
            # 解析emotion_summary（可能是"忧郁、希望、浪漫"或"忧郁，希望，浪漫"格式）
            import re
            summary_emotions = re.split(r'[，,、]', emotion_summary)
            summary_emotions = [e.strip() for e in summary_emotions if e.strip()]
            # 如果解析成功，使用这些词语组合作为情感类型
            if summary_emotions and len(summary_emotions) >= 2:
                emotion_type = '、'.join(summary_emotions[:4])  # 最多取4个词语
        
        # 翻译emotion_type（如果是英文）
        if emotion_type and emotion_type in emotion_translations:
            emotion_type = emotion_translations[emotion_type]
        elif emotion_type and any(c.isascii() and c.isalpha() for c in emotion_type):
            # 如果包含英文字母，尝试翻译
            emotion_type = emotion_translations.get(emotion_type.lower(), emotion_type)
        
        # 计算category_distribution（情感分布）
        category_counts = {
            'positive': sum(1 for a in sentence_analyses if a.get('category') == 'positive'),
            'negative': sum(1 for a in sentence_analyses if a.get('category') == 'negative'),
            'neutral': sum(1 for a in sentence_analyses if a.get('category') == 'neutral' or a.get('category') not in ['positive', 'negative'])
        }
        
        # 计算emotion_distribution（详细情感类型分布）
        # 优先使用 DeepSeek 返回的 emotion_distribution（如果存在且有效）
        emotion_counts = {}
        if 'emotion_distribution' in sentiment_data and isinstance(sentiment_data['emotion_distribution'], dict):
            # 使用 DeepSeek 返回的情感分布（已经是比例值）
            deepseek_dist = sentiment_data['emotion_distribution']
            # 将比例值转换为计数（基于句子数量），以便与现有逻辑兼容
            total_sentences = len(sentence_analyses) if sentence_analyses else 10
            for emotion, proportion in deepseek_dist.items():
                if isinstance(proportion, (int, float)) and proportion > 0:
                    # 将比例转换为计数（乘以100以保持精度）
                    count = int(proportion * 100)
                    if count > 0:
                        emotion_counts[emotion] = count
        else:
            # 如果没有 DeepSeek 返回的分布，从句子分析中统计
            for analysis in sentence_analyses:
                emotion = analysis.get('emotion_type', translated_emotion)
                # 翻译英文情感类型为中文
                if emotion and emotion in emotion_translations:
                    emotion = emotion_translations[emotion]
                elif emotion and any(c.isascii() and c.isalpha() for c in emotion):
                    # 如果包含英文字母，尝试翻译
                    emotion = emotion_translations.get(emotion.lower(), emotion)
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        # 如果没有句子分析，根据整体得分生成分布
        if sum(category_counts.values()) == 0:
            overall_score = float(sentiment_data.get('overall_score', 0.5))
            if overall_score > 0.6:
                category_counts = {'positive': 1, 'negative': 0, 'neutral': 0}
            elif overall_score < 0.4:
                category_counts = {'positive': 0, 'negative': 1, 'neutral': 0}
            else:
                category_counts = {'positive': 0, 'negative': 0, 'neutral': 1}
        
        # 如果没有emotion_distribution，根据overall_tone生成更丰富的情感分布
        if not emotion_counts:
            import re
            # 解析复合情感（如"忧郁、失望、希望交织"）
            tone_cleaned = translated_emotion.replace('交织', '').replace('混合', '').replace('等', '')
            tone_parts = re.split(r'[、，,，]', tone_cleaned)
            
            for part in tone_parts:
                part = part.strip()
                if part and len(part) > 0:
                    emotion_counts[part] = 1
            
            # 如果解析失败或只有一个情感，根据overall_tone和overall_score生成更丰富的情感分布
            if not emotion_counts or len(emotion_counts) == 1:
                overall_score = float(sentiment_data.get('overall_score', 0.5))
                # 根据情感基调和得分生成多个相关情感
                base_emotion = translated_emotion
                
                # 情感扩展映射：根据基础情感生成相关情感
                emotion_extensions = {
                    '忧郁': ['忧郁', '悲伤', '低沉', '感伤'],
                    '悲伤': ['悲伤', '忧郁', '痛苦', '失落'],
                    '希望': ['希望', '期待', '憧憬', '向往'],
                    '快乐': ['快乐', '愉悦', '欢快', '开心'],
                    '浪漫': ['浪漫', '温柔', '甜蜜', '温馨'],
                    '孤独': ['孤独', '寂寞', '空虚', '落寞'],
                    '怀旧': ['怀旧', '思念', '回忆', '怀念'],
                    '积极': ['积极', '向上', '乐观', '阳光'],
                    '消极': ['消极', '低沉', '沮丧', '悲观'],
                    '中性': ['平和', '平静', '淡然', '中性']
                }
                
                # 查找匹配的情感扩展
                extended_emotions = None
                for key, values in emotion_extensions.items():
                    if key in base_emotion:
                        extended_emotions = values
                        break
                
                if extended_emotions:
                    # 根据得分分配权重
                    if overall_score > 0.7:
                        # 积极情感为主
                        emotion_counts[extended_emotions[0]] = 3
                        if len(extended_emotions) > 1:
                            emotion_counts[extended_emotions[1]] = 2
                    elif overall_score < 0.3:
                        # 消极情感为主
                        emotion_counts[extended_emotions[0]] = 3
                        if len(extended_emotions) > 1:
                            emotion_counts[extended_emotions[1]] = 2
                    else:
                        # 中性或混合情感
                        for i, emotion in enumerate(extended_emotions[:3]):
                            emotion_counts[emotion] = 2 - i
                else:
                    # 如果没有匹配，直接使用overall_tone
                    emotion_counts[translated_emotion] = 1
        
        # 提取情感层次、转折点和高潮（如果DeepSeek提供了）
        emotion_layers = sentiment_data.get('emotion_layers', [])
        emotion_transitions = sentiment_data.get('emotion_transitions', [])
        emotional_highlights = sentiment_data.get('emotional_highlights', [])
        
        # 如果没有提供，尝试从description中提取
        if not emotion_layers and sentiment_data.get('description'):
            # 可以尝试从描述中提取，但这里先保持为空，让DeepSeek直接提供
            pass
        
        # 处理 emotion_distribution：优先使用 DeepSeek 返回的比例值
        final_emotion_distribution = {}
        # 优先使用 emotion_distribution_proportions（如果存在）
        if 'emotion_distribution_proportions' in sentiment_data and isinstance(sentiment_data['emotion_distribution_proportions'], dict):
            deepseek_dist = sentiment_data['emotion_distribution_proportions']
        elif 'emotion_distribution' in sentiment_data and isinstance(sentiment_data['emotion_distribution'], dict):
            deepseek_dist = sentiment_data['emotion_distribution']
        else:
            deepseek_dist = None
        
        if deepseek_dist:
            # 使用 DeepSeek 返回的比例值（0-1之间）
            for emotion, proportion in deepseek_dist.items():
                if isinstance(proportion, (int, float)) and proportion > 0:
                    # 将比例值转换为整数计数（乘以100以保持精度），前端会根据计数计算比例
                    # 确保情感词语是2-4字的中文
                    emotion_clean = str(emotion).strip()
                    # 验证：优先2字，如果确实没有合适的2字词，可以使用3-4字的中文词语
                    if len(emotion_clean) >= 2 and len(emotion_clean) <= 4 and all('\u4e00' <= c <= '\u9fff' for c in emotion_clean):
                        # 优先保留2字词语，如果有3-4字词语，也保留（但会稍后处理）
                        final_emotion_distribution[emotion_clean] = int(proportion * 100)
            
            # 如果 DeepSeek 返回的分布为空或无效，使用从句子分析统计的计数
            if not final_emotion_distribution:
                final_emotion_distribution = emotion_counts
        else:
            # 使用从句子分析统计的计数
            final_emotion_distribution = emotion_counts
        
        return {
            'overall_tone': translated_emotion,
            'overall_score': float(sentiment_data.get('overall_score', 0.5)),
            'emotion_type': emotion_type,
            'emotion_summary': emotion_summary,  # 新增：情感总结（多个词语）
            'description': sentiment_data.get('description', ''),
            'intensity': float(sentiment_data.get('intensity', 5)) / 10.0,  # 转换为0-1范围
            'emotion_layers': emotion_layers,  # 情感层次
            'emotion_transitions': emotion_transitions,  # 情感转折点
            'emotional_highlights': emotional_highlights,  # 情感高潮
            'sentence_analyses': sentence_analyses,
            'timeline': timeline,
            'category_distribution': category_counts,
            'emotion_distribution': final_emotion_distribution,  # 使用处理后的情感分布
            'source': 'deepseek'
        }
    
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

