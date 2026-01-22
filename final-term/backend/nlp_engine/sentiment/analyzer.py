"""
情感分析模块
提供逐句情感检测、情感强度分析和整体情感基调判断
使用更丰富的情感词汇
"""
import jieba
from snownlp import SnowNLP
import numpy as np
from typing import List, Dict, Tuple


class SentimentAnalyzer:
    """情感分析器"""
    
    # 丰富的情感词汇库
    EMOTION_WORDS = {
        'joyful': ['快乐', '开心', '喜悦', '欢快', '兴奋', '愉悦', '欣喜', '畅快', '爽朗', '明媚'],
        'melancholic': ['忧郁', '悲伤', '哀伤', '凄凉', '落寞', '惆怅', '伤感', '悲凉', '凄美', '黯然'],
        'romantic': ['浪漫', '温柔', '甜蜜', '温馨', '缠绵', '深情', '柔情', '缱绻', '旖旎', '缠绵'],
        'passionate': ['激情', '热烈', '炽热', '狂热', '奔放', '激昂', '澎湃', '燃烧', '沸腾', '狂热'],
        'peaceful': ['平静', '安宁', '宁静', '祥和', '恬淡', '淡泊', '静谧', '悠然', '舒缓', '平和'],
        'nostalgic': ['怀旧', '怀念', '追忆', '回忆', '缅怀', '思念', '眷恋', '留恋', '回味', '追思'],
        'hopeful': ['希望', '期待', '憧憬', '向往', '期盼', '展望', '希冀', '渴望', '盼望', '期待'],
        'lonely': ['孤独', '寂寞', '孤单', '孤寂', '落单', '形单影只', '孑然', '孤身', '独处', '孤零'],
        'energetic': ['活力', '朝气', '蓬勃', '生机', '活力四射', '充满活力', '精神', '振奋', '昂扬', '蓬勃'],
        'mysterious': ['神秘', '深邃', '幽深', '玄妙', '奥秘', '神秘莫测', '深不可测', '幽玄', '玄奥', '神秘'],
        'dreamy': ['梦幻', '朦胧', '迷离', '虚幻', '缥缈', '如幻', '似梦', '迷蒙', '恍惚', '梦幻'],
        'powerful': ['力量', '强大', '有力', '强劲', '雄浑', '磅礴', '震撼', '强烈', '威猛', '雄壮']
    }
    
    def __init__(self):
        self.positive_threshold = 0.6
        self.negative_threshold = 0.4
    
    def _detect_emotion_type(self, sentence: str) -> str:
        """检测情感类型（更细致的分类，改进算法）"""
        words = jieba.cut(sentence)
        word_list = list(words)
        
        # 扩展情感词汇库，增加更多情感类型
        extended_emotions = {
            'joyful': ['快乐', '开心', '喜悦', '欢快', '兴奋', '愉悦', '欣喜', '畅快', '爽朗', '明媚', '欢乐', '高兴', '愉快'],
            'melancholic': ['忧郁', '悲伤', '哀伤', '凄凉', '落寞', '惆怅', '伤感', '悲凉', '凄美', '黯然', '难过', '痛苦', '伤心'],
            'romantic': ['浪漫', '温柔', '甜蜜', '温馨', '缠绵', '深情', '柔情', '缱绻', '旖旎', '爱恋', '心动', '情意'],
            'passionate': ['激情', '热烈', '炽热', '狂热', '奔放', '激昂', '澎湃', '燃烧', '沸腾', '狂热', '热情'],
            'peaceful': ['平静', '安宁', '宁静', '祥和', '恬淡', '淡泊', '静谧', '悠然', '舒缓', '平和', '安静', '宁静'],
            'nostalgic': ['怀旧', '怀念', '追忆', '回忆', '缅怀', '思念', '眷恋', '留恋', '回味', '追思', '往事', '过去'],
            'hopeful': ['希望', '期待', '憧憬', '向往', '期盼', '展望', '希冀', '渴望', '盼望', '期待', '梦想'],
            'lonely': ['孤独', '寂寞', '孤单', '孤寂', '落单', '形单影只', '孑然', '孤身', '独处', '孤零', '独自'],
            'energetic': ['活力', '朝气', '蓬勃', '生机', '活力四射', '充满活力', '精神', '振奋', '昂扬', '蓬勃', '活跃'],
            'mysterious': ['神秘', '深邃', '幽深', '玄妙', '奥秘', '神秘莫测', '深不可测', '幽玄', '玄奥', '神秘', '未知'],
            'dreamy': ['梦幻', '朦胧', '迷离', '虚幻', '缥缈', '如幻', '似梦', '迷蒙', '恍惚', '梦幻', '梦境'],
            'powerful': ['力量', '强大', '有力', '强劲', '雄浑', '磅礴', '震撼', '强烈', '威猛', '雄壮', '强大'],
            'warm': ['温暖', '暖和', '温馨', '暖意', '和煦', '暖阳', '温情', '暖心'],
            'cool': ['清凉', '清爽', '凉爽', '清冷', '冷静', '冷静', '淡然'],
            'sad': ['难过', '伤心', '痛苦', '悲伤', '哀痛', '痛心', '心碎'],
            'angry': ['愤怒', '生气', '恼火', '愤慨', '怒火', '气愤'],
            'calm': ['冷静', '镇定', '沉着', '平静', '淡定', '从容'],
            'excited': ['激动', '兴奋', '振奋', '激昂', '热血', '澎湃']
        }
        
        emotion_scores = {}
        for emotion_type, emotion_words in extended_emotions.items():
            # 计算匹配度，考虑词频和权重
            score = 0
            for word in word_list:
                if word in emotion_words:
                    score += 1
            if score > 0:
                emotion_scores[emotion_type] = score
        
        # 同时使用SnowNLP进行情感分析
        s = SnowNLP(sentence)
        nlp_score = s.sentiments
        
        # 结合关键词匹配和NLP分析
        if emotion_scores:
            # 如果关键词匹配度高，优先使用关键词结果
            max_emotion = max(emotion_scores.items(), key=lambda x: x[1])[0]
            max_score = emotion_scores[max_emotion]
            
            # 如果关键词匹配度足够高，直接返回
            if max_score >= 2:
                return self._translate_emotion(max_emotion)
            
            # 如果NLP分数与关键词结果一致，使用关键词结果
            emotion_category = self._get_emotion_category(max_emotion)
            if (emotion_category == 'positive' and nlp_score >= 0.5) or \
               (emotion_category == 'negative' and nlp_score < 0.5):
                return self._translate_emotion(max_emotion)
        
        # 如果没有匹配到关键词或结果不一致，使用NLP结果
        if nlp_score >= 0.75:
            return '欢快愉悦'
        elif nlp_score >= 0.65:
            return '积极向上'
        elif nlp_score >= 0.55:
            return '平和中性'
        elif nlp_score >= 0.45:
            return '平静安宁'
        elif nlp_score >= 0.35:
            return '忧郁悲伤'
        elif nlp_score >= 0.25:
            return '低沉消极'
        else:
            return '悲伤痛苦'
    
    def _get_emotion_category(self, emotion_type: str) -> str:
        """获取情感类别"""
        positive_emotions = ['joyful', 'hopeful', 'energetic', 'romantic', 'warm', 'excited']
        negative_emotions = ['melancholic', 'lonely', 'sad', 'angry']
        
        if emotion_type in positive_emotions:
            return 'positive'
        elif emotion_type in negative_emotions:
            return 'negative'
        else:
            return 'neutral'
    
    def _translate_emotion(self, emotion_type: str) -> str:
        """翻译情感类型为中文"""
        translations = {
            'joyful': '欢快愉悦',
            'melancholic': '忧郁悲伤',
            'romantic': '浪漫温柔',
            'passionate': '激情热烈',
            'peaceful': '平静安宁',
            'nostalgic': '怀旧追忆',
            'hopeful': '充满希望',
            'lonely': '孤独寂寞',
            'energetic': '活力四射',
            'mysterious': '神秘深邃',
            'dreamy': '梦幻迷离',
            'powerful': '力量磅礴',
            'warm': '温暖和煦',
            'cool': '清凉冷静',
            'sad': '悲伤难过',
            'angry': '愤怒激昂',
            'calm': '冷静从容',
            'excited': '激动兴奋'
        }
        return translations.get(emotion_type, '中性平和')
    
    def analyze_sentence(self, sentence: str) -> Dict:
        """分析单句情感"""
        s = SnowNLP(sentence)
        sentiment_score = s.sentiments
        
        # 判断情感类别
        if sentiment_score >= self.positive_threshold:
            category = 'positive'
        elif sentiment_score <= self.negative_threshold:
            category = 'negative'
        else:
            category = 'neutral'
        
        # 检测更细致的情感类型
        emotion_type = self._detect_emotion_type(sentence)
        
        return {
            'sentence': sentence,
            'score': float(sentiment_score),
            'category': category,
            'emotion_type': emotion_type,
            'intensity': abs(sentiment_score - 0.5) * 2  # 强度：0-1
        }
    
    def analyze_lyrics(self, lyrics: str) -> Dict:
        """分析整首歌词的情感"""
        # 按行分割歌词
        lines = [line.strip() for line in lyrics.split('\n') if line.strip()]
        
        sentence_analyses = []
        for line in lines:
            analysis = self.analyze_sentence(line)
            sentence_analyses.append(analysis)
        
        # 计算整体统计
        scores = [a['score'] for a in sentence_analyses]
        avg_score = np.mean(scores) if scores else 0.5
        
        # 情感变化曲线数据
        timeline = [{'index': i, 'score': a['score'], 'category': a['category'], 
                    'emotion_type': a['emotion_type']} 
                   for i, a in enumerate(sentence_analyses)]
        
        # 情感分布统计（按情感类型）
        emotion_counts = {}
        for analysis in sentence_analyses:
            emotion = analysis['emotion_type']
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        # 整体基调判断（改进算法，考虑权重和情感强度）
        if emotion_counts:
            # 计算加权平均，考虑情感强度
            weighted_emotions = {}
            for analysis in sentence_analyses:
                emotion = analysis['emotion_type']
                intensity = analysis['intensity']
                weighted_emotions[emotion] = weighted_emotions.get(emotion, 0) + intensity
            
            if weighted_emotions:
                # 选择加权得分最高的情感
                overall_tone = max(weighted_emotions.items(), key=lambda x: x[1])[0]
            else:
                # 如果没有加权得分，使用频率最高的
                overall_tone = max(emotion_counts.items(), key=lambda x: x[1])[0]
        else:
            # 如果没有情感分布，使用NLP分数判断
            if avg_score >= 0.7:
                overall_tone = '欢快愉悦'
            elif avg_score >= 0.6:
                overall_tone = '积极向上'
            elif avg_score <= 0.3:
                overall_tone = '忧郁悲伤'
            elif avg_score <= 0.4:
                overall_tone = '低沉消极'
            else:
                overall_tone = '平和中性'
        
        # 情感得分说明：基于SnowNLP的情感分析，0-1之间，0.5为中性，越接近1越积极，越接近0越消极
        score_explanation = f"情感得分基于文本情感分析模型计算，范围0-1，{avg_score:.2f}表示{'非常积极' if avg_score >= 0.7 else '较为积极' if avg_score >= 0.6 else '中性偏积极' if avg_score >= 0.55 else '中性' if 0.45 <= avg_score <= 0.55 else '中性偏消极' if avg_score >= 0.4 else '较为消极' if avg_score >= 0.3 else '非常消极'}"
        
        # 传统分类统计（用于兼容）
        category_counts = {
            'positive': sum(1 for a in sentence_analyses if a['category'] == 'positive'),
            'negative': sum(1 for a in sentence_analyses if a['category'] == 'negative'),
            'neutral': sum(1 for a in sentence_analyses if a['category'] == 'neutral')
        }
        
        return {
            'sentence_analyses': sentence_analyses,
            'overall_score': float(avg_score),
            'overall_tone': overall_tone,
            'score_explanation': score_explanation,
            'timeline': timeline,
            'category_distribution': category_counts,
            'emotion_distribution': emotion_counts,
            'intensity_curve': [a['intensity'] for a in sentence_analyses]
        }



