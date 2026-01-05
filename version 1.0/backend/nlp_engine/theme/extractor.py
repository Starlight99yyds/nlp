"""
主题提取模块
自动提取关键词、主题聚类、生成词云数据
"""
import jieba
import jieba.analyse
from collections import Counter
from typing import List, Dict, Tuple


class ThemeExtractor:
    """主题提取器"""
    
    # 主题关键词库
    THEME_KEYWORDS = {
        '爱情': ['爱', '恋', '情', '心', '思念', '拥抱', '吻', '温柔', '浪漫', '甜蜜'],
        '励志': ['梦想', '坚持', '努力', '奋斗', '成功', '希望', '未来', '勇敢', '坚强'],
        '怀旧': ['回忆', '过去', '曾经', '青春', '时光', '岁月', '怀念', '往事'],
        '友情': ['朋友', '兄弟', '友谊', '陪伴', '一起', '共同', '支持'],
        '孤独': ['孤独', '寂寞', '独自', '一个人', '空虚', '失落'],
        '自由': ['自由', '飞翔', '天空', '风', '无拘无束', '释放'],
        '悲伤': ['哭', '泪', '痛', '伤', '失去', '离别', '痛苦'],
        '快乐': ['笑', '开心', '快乐', '幸福', '喜悦', '欢乐']
    }
    
    def __init__(self):
        # 加载自定义词典
        jieba.initialize()
    
    def extract_keywords(self, lyrics: str, top_k: int = 20) -> List[Dict]:
        """提取关键词"""
        # 使用TF-IDF提取关键词
        keywords = jieba.analyse.extract_tags(lyrics, topK=top_k, withWeight=True)
        
        return [{'word': word, 'weight': float(weight)} for word, weight in keywords]
    
    def classify_theme(self, lyrics: str) -> List[Dict]:
        """主题分类（改进算法，更准确）"""
        # 分词
        words = jieba.cut(lyrics)
        word_list = [w for w in words if len(w.strip()) > 0]
        word_counter = Counter(word_list)
        total_words = len(word_list)
        
        # 扩展主题关键词库
        extended_themes = {
            '爱情': ['爱', '恋', '情', '心', '思念', '拥抱', '吻', '温柔', '浪漫', '甜蜜', '恋人', '情侣', '相爱', '深情'],
            '励志': ['梦想', '坚持', '努力', '奋斗', '成功', '希望', '未来', '勇敢', '坚强', '拼搏', '追求', '目标'],
            '怀旧': ['回忆', '过去', '曾经', '青春', '时光', '岁月', '怀念', '往事', '从前', '旧时', '记忆'],
            '友情': ['朋友', '兄弟', '友谊', '陪伴', '一起', '共同', '支持', '伙伴', '知己', '同伴'],
            '孤独': ['孤独', '寂寞', '独自', '一个人', '空虚', '失落', '孤单', '孤寂', '落寞'],
            '自由': ['自由', '飞翔', '天空', '风', '无拘无束', '释放', '解脱', '自在'],
            '悲伤': ['哭', '泪', '痛', '伤', '失去', '离别', '痛苦', '难过', '伤心', '哀伤'],
            '快乐': ['笑', '开心', '快乐', '幸福', '喜悦', '欢乐', '高兴', '愉快', '欣喜'],
            '自然': ['山', '海', '风', '雨', '云', '月', '星', '花', '树', '鸟', '自然', '风景'],
            '城市': ['城市', '街道', '霓虹', '灯火', '高楼', '都市', '繁华', '喧嚣'],
            '夜晚': ['夜', '夜晚', '深夜', '星空', '月亮', '黑暗', '寂静', '宁静'],
            '旅行': ['旅行', '远方', '旅程', '出发', '到达', '风景', '探索', '冒险'],
            '成长': ['成长', '长大', '经历', '变化', '成熟', '蜕变', '进步'],
            '离别': ['离别', '分别', '再见', '离开', '远去', '告别', '分离']
        }
        
        theme_scores = {}
        for theme, keywords in extended_themes.items():
            # 计算匹配的关键词数量和权重
            matched_keywords = [kw for kw in keywords if word_counter.get(kw, 0) > 0]
            if matched_keywords:
                # 计算总匹配次数
                total_matches = sum(word_counter.get(kw, 0) for kw in matched_keywords)
                # 计算匹配的关键词比例
                keyword_ratio = len(matched_keywords) / len(keywords)
                # 计算在总词数中的比例
                word_ratio = total_matches / total_words if total_words > 0 else 0
                # 综合得分
                score = total_matches * 0.6 + keyword_ratio * 10 + word_ratio * 100
                theme_scores[theme] = score
        
        # 按分数排序，返回所有有得分的主题
        sorted_themes = sorted(theme_scores.items(), key=lambda x: x[1], reverse=True)
        
        # 归一化得分到0-1范围
        if sorted_themes:
            max_score = sorted_themes[0][1]
            normalized = [{'theme': theme, 'score': round(score / max_score, 2) if max_score > 0 else 0} 
                          for theme, score in sorted_themes]
            return normalized[:10]  # 返回前10个主题
        
        return []
    
    def extract_entities(self, lyrics: str) -> Dict:
        """提取实体（人物、场景等）"""
        words = jieba.cut(lyrics)
        word_list = [w for w in words if len(w.strip()) > 0]
        
        # 简单的人物识别（包含常见人称）
        persons = [w for w in word_list if any(p in w for p in ['你', '我', '他', '她', '我们', '你们'])]
        
        # 场景词（包含常见场景词）
        scene_keywords = ['夜', '雨', '风', '海', '山', '城市', '街', '房间', '窗', '门']
        scenes = [w for w in word_list if any(sk in w for sk in scene_keywords)]
        
        return {
            'persons': list(set(persons))[:10],
            'scenes': list(set(scenes))[:10],
            'emotion_words': self._extract_emotion_words(word_list)
        }
    
    def _extract_emotion_words(self, words: List[str]) -> List[str]:
        """提取情感词"""
        emotion_keywords = []
        for theme, keywords in self.THEME_KEYWORDS.items():
            emotion_keywords.extend(keywords)
        
        return [w for w in words if w in emotion_keywords][:15]
    
    def analyze_theme(self, lyrics: str) -> Dict:
        """完整主题分析"""
        keywords = self.extract_keywords(lyrics)
        themes = self.classify_theme(lyrics)
        entities = self.extract_entities(lyrics)
        
        # 生成词云数据
        wordcloud_data = [{'word': kw['word'], 'size': int(kw['weight'] * 100)} 
                         for kw in keywords[:30]]
        
        return {
            'keywords': keywords,
            'themes': themes,
            'entities': entities,
            'wordcloud_data': wordcloud_data,
            'primary_theme': themes[0]['theme'] if themes else '未知'
        }





