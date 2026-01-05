"""
韵律分析模块
检测押韵、分析押韵模式、评估押韵质量
使用pypinyin进行准确的押韵判断
"""
import jieba
from typing import List, Dict, Tuple
import re
try:
    from pypinyin import pinyin, Style, lazy_pinyin
    PYPINYIN_AVAILABLE = True
except ImportError:
    PYPINYIN_AVAILABLE = False
    print("警告: pypinyin未安装，押韵判断可能不准确")


class RhythmAnalyzer:
    """韵律分析器"""
    
    # 韵母表（更完整的韵母分组）
    RHYME_GROUPS = {
        'a': ['a', 'ia', 'ua'],
        'o': ['o', 'uo'],
        'e': ['e', 'ie', 'ue', 'üe'],
        'i': ['i', 'ai', 'ei', 'ui', 'üi'],
        'u': ['u', 'ou', 'iu'],
        'v': ['v', 'ü'],
        'an': ['an', 'ian', 'uan', 'üan'],
        'en': ['en', 'in', 'un', 'ün'],
        'ang': ['ang', 'iang', 'uang'],
        'eng': ['eng', 'ing', 'ong', 'iong'],
        'ao': ['ao', 'iao'],
        'ei': ['ei', 'uei'],
        'ou': ['ou', 'iou']
    }
    
    def __init__(self):
        self.pypinyin_available = PYPINYIN_AVAILABLE
    
    def extract_final_sound(self, word: str) -> str:
        """提取字词的韵母（使用pypinyin）"""
        if len(word) == 0:
            return ''
        
        # 获取最后一个字符
        last_char = word.strip()[-1]
        
        if self.pypinyin_available:
            try:
                # 获取拼音
                pinyin_list = pinyin(last_char, style=Style.FINALS, heteronym=False)
                if pinyin_list and len(pinyin_list) > 0:
                    final = pinyin_list[0][0]
                    # 标准化韵母（去除声调）
                    final = final.replace('ā', 'a').replace('á', 'a').replace('ǎ', 'a').replace('à', 'a')
                    final = final.replace('ē', 'e').replace('é', 'e').replace('ě', 'e').replace('è', 'e')
                    final = final.replace('ī', 'i').replace('í', 'i').replace('ǐ', 'i').replace('ì', 'i')
                    final = final.replace('ō', 'o').replace('ó', 'o').replace('ǒ', 'o').replace('ò', 'o')
                    final = final.replace('ū', 'u').replace('ú', 'u').replace('ǔ', 'u').replace('ù', 'u')
                    final = final.replace('ǖ', 'ü').replace('ǘ', 'ü').replace('ǚ', 'ü').replace('ǜ', 'ü')
                    return final
            except Exception as e:
                print(f"拼音提取失败: {e}")
        
        # 备用方案：返回最后一个字符
        return last_char
    
    def detect_rhyme(self, line1: str, line2: str) -> bool:
        """检测两句是否押韵"""
        if not line1.strip() or not line2.strip():
            return False
        
        final1 = self.extract_final_sound(line1.strip())
        final2 = self.extract_final_sound(line2.strip())
        
        # 如果韵母完全相同
        if final1 == final2:
            return True
        
        # 检查是否在同一韵母组
        for group in self.RHYME_GROUPS.values():
            if final1 in group and final2 in group:
                return True
        
        # 检查韵母相似度（部分匹配）
        if len(final1) >= 2 and len(final2) >= 2:
            # 如果韵母的后半部分相同（如ang和iang）
            if final1[-2:] == final2[-2:]:
                return True
        
        return False
    
    def analyze_rhyme_pattern(self, lyrics: str) -> Dict:
        """分析押韵模式"""
        lines = [line.strip() for line in lyrics.split('\n') if line.strip()]
        
        if len(lines) < 2:
            return {
                'pattern': 'N/A',
                'rhyme_pairs': [],
                'quality_score': 0
            }
        
        # 检测押韵对
        rhyme_pairs = []
        for i in range(len(lines) - 1):
            if self.detect_rhyme(lines[i], lines[i + 1]):
                rhyme_pairs.append((i, i + 1))
        
        # 识别押韵模式
        pattern = self._identify_pattern(lines, rhyme_pairs)
        
        # 计算押韵质量分数
        quality_score = len(rhyme_pairs) / max(len(lines) - 1, 1)
        
        return {
            'pattern': pattern,
            'rhyme_pairs': [{'line1': i, 'line2': j} for i, j in rhyme_pairs],
            'quality_score': round(quality_score, 2),
            'total_lines': len(lines),
            'rhyme_count': len(rhyme_pairs)
        }
    
    def _identify_pattern(self, lines: List[str], rhyme_pairs: List[Tuple]) -> str:
        """识别押韵模式"""
        if len(rhyme_pairs) == 0:
            return '无押韵'
        
        # 简化模式识别
        if len(lines) >= 4:
            # 检查AABB模式
            if (0, 1) in rhyme_pairs and (2, 3) in rhyme_pairs:
                return 'AABB'
            # 检查ABAB模式
            if (0, 2) in rhyme_pairs and (1, 3) in rhyme_pairs:
                return 'ABAB'
            # 检查AAAA模式
            if all((i, i+1) in rhyme_pairs for i in range(min(3, len(lines)-1))):
                return 'AAAA'
        
        return '自由押韵'
    
    def analyze_syllables(self, lyrics: str) -> Dict:
        """分析音节和节奏"""
        lines = [line.strip() for line in lyrics.split('\n') if line.strip()]
        
        syllable_counts = []
        for line in lines:
            # 简单计算：字符数作为音节数近似
            count = len(line.replace(' ', '').replace('，', '').replace('。', ''))
            syllable_counts.append(count)
        
        return {
            'syllable_counts': syllable_counts,
            'avg_syllables': round(sum(syllable_counts) / len(syllable_counts), 2) if syllable_counts else 0,
            'rhythm_consistency': self._calculate_consistency(syllable_counts)
        }
    
    def _calculate_consistency(self, counts: List[int]) -> float:
        """计算节奏一致性"""
        if len(counts) < 2:
            return 1.0
        
        # 计算标准差，值越小越一致
        import numpy as np
        std = np.std(counts)
        max_count = max(counts) if counts else 1
        consistency = max(0, 1 - std / max_count)
        
        return round(consistency, 2)
    
    def analyze_rhythm(self, lyrics: str) -> Dict:
        """完整韵律分析"""
        rhyme_analysis = self.analyze_rhyme_pattern(lyrics)
        syllable_analysis = self.analyze_syllables(lyrics)
        
        return {
            'rhyme_pattern': rhyme_analysis,
            'syllable_analysis': syllable_analysis,
            'overall_score': round((rhyme_analysis['quality_score'] + syllable_analysis['rhythm_consistency']) / 2, 2)
        }



