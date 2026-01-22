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
from app.utils.suno_client import SunoClient, SunoModel
import os


class GenerationService:
    """生成服务类"""
    
    def __init__(self):
        self.generator = LyricsGenerator()
        self.deepseek_client = DeepSeekClient()
        # 确保环境变量已加载
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
        
        # 从环境变量读取 Suno API Key（不提供默认值，确保安全性）
        suno_api_key = os.environ.get('SUNO_API_KEY', '')
        self.suno_client = SunoClient(api_key=suno_api_key)
    
    def generate_by_theme(self, theme: str, emotion: Optional[str] = None, 
                         length: Optional[int] = None, user_idea: Optional[str] = None, user_id: int = None) -> Dict:
        """根据主题生成歌词"""
        # 使用DeepSeek生成更高质量的歌词
        prompt = f"创作一首关于{theme}主题的歌词"
        if emotion:
            prompt += f"，情感基调为{emotion}"
        if length:
            prompt += f"，**必须严格生成{length}行**，不能多也不能少"
        else:
            prompt += "，生成完整歌词，必须包含完整的结构（主歌、副歌等），每个结构标记后都必须有对应的歌词内容，不能中途停止或留下空的结构标记，可以包含\"主歌\"、\"副歌\"等结构标记"
        
        # 如果不限制长度，使用较大的默认长度
        effective_length = length if length else 32
        
        lyrics, title = self.deepseek_client.generate_lyrics_with_title(
            prompt=prompt,
            theme=theme,
            emotion=emotion,
            length=effective_length,
            user_idea=user_idea,
            is_new_generation=True  # 确保每次都是全新生成
        )
        
        # 清理歌词中的标题行、创作说明和说明性文字
        import re
        # 兜底：如果模型把标题写进了歌词里（例如 "# 《xxx》"），这里统一当作标题行删除
        # 注意：如果 DeepSeek 已经生成了 title，这里不覆盖 title，只负责清理歌词里的多余标题行
        lyrics_lines = lyrics.split('\n')
        cleaned_lines = []
        skip_until_lyrics = False  # 标记是否遇到说明性文字，需要跳过
        first_line_removed = False  # 标记是否已删除第一行的标题
        
        for i, line in enumerate(lyrics_lines):
            line = line.strip()
            if not line:
                # 如果遇到空行且之前有说明性文字，可能说明部分结束，开始歌词部分
                if skip_until_lyrics:
                    skip_until_lyrics = False
                continue
            
            # 检查是否是说明性文字（如"好的，根据您的想法..."）
            is_explanation = False
            explanation_patterns = [
                r'^好的[，,]?\s*根据.*',
                r'^根据.*为您创作',
                r'^为您创作.*',
                r'^以下.*歌词',
                r'^这是一首.*',
                r'^歌名[：:]\s*《.*》',
                r'^歌名[：:]\s*.*',
            ]
            for pattern in explanation_patterns:
                if re.match(pattern, line, re.IGNORECASE):
                    is_explanation = True
                    skip_until_lyrics = True
                    break
            
            # 如果正在跳过说明部分，继续跳过
            if skip_until_lyrics and not is_explanation:
                # 检查是否开始真正的歌词（通常是结构标记或歌词内容）
                if re.match(r'^(主歌|副歌|预副歌|桥段|间奏|尾奏|前奏|Intro|Verse|Chorus|Bridge|Outro|Interlude)', line, re.IGNORECASE):
                    skip_until_lyrics = False
                elif re.match(r'^[（(](主歌|副歌|预副歌|桥段|间奏|尾奏|前奏)', line, re.IGNORECASE):
                    skip_until_lyrics = False
                else:
                    # 如果这行看起来像歌词（有中文字符且不是说明），停止跳过
                    if re.search(r'[\u4e00-\u9fa5]', line) and not any(p in line for p in ['创作', '说明', '歌名', '根据', '为您']):
                        skip_until_lyrics = False
                    else:
                        continue
            
            if is_explanation:
                continue
            
            # 跳过标题行（但保留**《标题》**格式）
            is_title_line = False
            # 检查是否是加粗的标题行（**《标题》**）- 保留这种格式
            if re.match(r'^\*\*《.*》\*\*\s*$', line):
                # 保留加粗的标题行，不删除
                pass
            elif title:
                # 移除可能的标点符号后比较
                line_no_heading = re.sub(r'^#{1,6}\s*', '', line).strip()
                line_clean = re.sub(r'[《》"\'【】\[\]()（）\s\*]+', '', line_no_heading)
                title_clean = re.sub(r'[《》"\'【】\[\]()（）\s]+', '', title)
                if line_clean == title_clean or line_no_heading == title or line_no_heading == f'《{title}》':
                    is_title_line = True
            # 首先检查是否是标题格式（《...》或【...】）- 删除不加粗的标题格式
            # 同时兼容 Markdown 标题：# 《...》
            if re.match(r'^#{1,6}\s*《.*》\s*$', line) or re.match(r'^#{1,6}\s*【.*】\s*$', line):
                is_title_line = True
            if re.match(r'^《.*》\s*$', line) or re.match(r'^【.*】\s*$', line):
                is_title_line = True
            # 检查是否是"歌名：《...》"格式
            if re.match(r'^歌名[：:]\s*《.*》\s*$', line) or re.match(r'^歌名[：:]\s*.*\s*$', line):
                is_title_line = True
            
            # 删除不需要的标题格式的行（但保留**《标题》**格式）
            if is_title_line:
                continue
            
            # 跳过创作说明
            if '创作说明' in line or '创作思路' in line or line.startswith('创作：'):
                break  # 遇到创作说明，停止处理后续内容
            
            # 如果不是标题行，添加到清理后的列表
            cleaned_lines.append(line)
        
        lyrics = '\n'.join(cleaned_lines)
        
        # 如果指定了长度，验证和调整行数（排除标题，但保留结构标记）
        if length:
            lyrics = self._adjust_lyrics_length_with_structure(lyrics, length, title)
        else:
            # 不限制长度时，保留所有内容（包括结构标记），但已清理标题
            pass
        
        # 构建历史记录的提示词，包含所有用户需求
        history_prompt_parts = ['主题生成']
        history_prompt_parts.append(f'主题：{theme}')
        if emotion:
            history_prompt_parts.append(f'情感：{emotion}')
        if user_idea:
            history_prompt_parts.append(f'想法：{user_idea[:30]}...' if len(user_idea) > 30 else f'想法：{user_idea}')
        if length:
            history_prompt_parts.append(f'长度：{length}行')
        else:
            history_prompt_parts.append('长度：不限制')
        history_prompt = ' | '.join(history_prompt_parts)
        
        result = {
            'lyrics': lyrics,
            'title': title,
            'theme': theme,
            'emotion': emotion or '未指定',
            'length': length
        }
        
        self._save_history(history_prompt, lyrics, theme, user_id)
        
        return result
    
    def generate_by_context(self, previous_lines: List[str], 
                           emotion: Optional[str] = None, length: Optional[int] = None,
                           theme: Optional[str] = None, style: Optional[str] = None,
                           user_idea: Optional[str] = None, user_id: int = None) -> Dict:
        """基于上下文生成（只生成新创作的歌词，不重复输出上文）"""
        # 检查上下文是否有效
        if not previous_lines or (isinstance(previous_lines, list) and len(previous_lines) == 0):
            return {
                'lyrics': '请提供您希望我继续创作的歌词片段或主题',
                'context': previous_lines,
                'emotion': emotion or '未指定',
                'error': '上下文为空'
            }
        
        # 确保previous_lines是列表格式
        if isinstance(previous_lines, str):
            previous_lines = [line.strip() for line in previous_lines.split('\n') if line.strip()]
        elif isinstance(previous_lines, list):
            previous_lines = [line.strip() for line in previous_lines if line.strip()]
        
        if not previous_lines or len(previous_lines) == 0:
            return {
                'lyrics': '请提供您希望我继续创作的歌词片段或主题',
                'context': previous_lines,
                'emotion': emotion or '未指定',
                'error': '上下文为空'
            }
        
        # 计算需要新生成的行数（如果指定了长度，总行数减去已有行数；否则不限制）
        context_length = len(previous_lines)
        if length:
            new_lines_needed = max(1, length - context_length)  # 至少生成1行新歌词
        else:
            new_lines_needed = None  # 不限制长度
        
        # 使用DeepSeek生成新的歌词，只生成新创作的部分
        context_text = '\n'.join(previous_lines)
        
        # 构建包含所有用户需求的提示词
        prompt_parts = ["请基于以下歌词继续创作，要求："]
        prompt_parts.append("1. **只输出新创作的歌词**，不要重复输出用户提供的歌词")
        prompt_parts.append("2. 新创作的歌词应该与用户提供的歌词在风格和主题上保持一致")
        prompt_parts.append("3. 保持连贯性和风格一致")
        prompt_parts.append("4. **每行歌词必须单独一行，使用换行符分隔**")
        if new_lines_needed:
            prompt_parts.append(f"5. **必须严格生成{new_lines_needed}行新歌词**，不能多也不能少")
        else:
            prompt_parts.append("5. 生成完整歌词，必须包含完整的结构（主歌、副歌等），每个结构标记后都必须有对应的歌词内容，不能中途停止或留下空的结构标记，可以包含\"主歌\"、\"副歌\"等结构标记，不限制长度")
        
        # 添加用户自定义的需求
        if theme:
            prompt_parts.append(f"6. 主题要求：{theme}")
        if style:
            prompt_parts.append(f"7. 风格要求：{style}")
        if emotion:
            prompt_parts.append(f"8. 情感基调：{emotion}")
        if user_idea:
            prompt_parts.append(f"9. 用户想法：{user_idea}")
        
        prompt_parts.append(f"\n用户提供的歌词（作为上下文参考，不要重复输出）：")
        prompt_parts.append(context_text)
        if new_lines_needed:
            prompt_parts.append(f"\n请只输出新创作的{new_lines_needed}行歌词，每行一句，使用换行符分隔。不要包含用户提供的歌词。")
        else:
            prompt_parts.append(f"\n请只输出新创作的歌词，每行一句，使用换行符分隔。可以包含\"主歌\"、\"副歌\"等结构标记，但每个结构标记后都必须有对应的歌词内容，不能留下空的结构标记。不要包含用户提供的歌词。")
        
        prompt = '\n'.join(prompt_parts)
        
        # 如果不限制长度，使用较大的默认长度
        effective_length = new_lines_needed if new_lines_needed else 32
        
        new_lyrics = self.deepseek_client.generate_lyrics(
            prompt=prompt,
            context=previous_lines,
            theme=theme,
            style=style,
            emotion=emotion,
            length=effective_length,
            user_idea=user_idea,
            is_new_generation=False  # 基于上下文，需要延续
        )
        
        # 处理新生成的歌词格式
        if new_lyrics:
            import re
            # 确保每行歌词单独一行
            new_lines = [line.strip() for line in new_lyrics.split('\n') if line.strip()]
            # 如果某行太长（超过50字符且没有标点），尝试按标点分割
            processed_lines = []
            for line in new_lines:
                if len(line) > 50 and not any(p in line for p in ['。', '！', '？', '，', '、']):
                    # 尝试按常见分隔符分割
                    parts = re.split(r'([，。！？、])', line)
                    for i in range(0, len(parts), 2):
                        if i+1 < len(parts):
                            processed_lines.append(parts[i] + parts[i+1])
                        elif parts[i].strip():
                            processed_lines.append(parts[i])
                else:
                    processed_lines.append(line)
            
            # 如果指定了长度，调整新生成歌词的行数（不传递title，因为这是新生成的部分，不包含标题）
            if new_lines_needed:
                new_lyrics_lines = self._adjust_lyrics_length_with_structure('\n'.join(processed_lines), new_lines_needed, None).split('\n')
            else:
                # 不限制长度时，保留所有生成的内容（包括结构标记）
                new_lyrics_lines = [line.strip() for line in processed_lines if line.strip()]
            
            # 将用户提供的歌词和新创作的歌词拼接
            full_lyrics = previous_lines + new_lyrics_lines
            # 如果指定了长度，确保总行数符合要求（如果超过，截取；如果不足，补充新创作的部分）
            if length and len(full_lyrics) > length:
                # 如果总行数超过，优先保留用户提供的歌词，然后保留新创作的部分
                full_lyrics = previous_lines + new_lyrics_lines[:length - len(previous_lines)]
            elif length and len(full_lyrics) < length:
                # 如果总行数不足，补充新创作的部分
                remaining = length - len(full_lyrics)
                # 使用最后几行新创作的歌词作为模板补充
                if new_lyrics_lines:
                    template = new_lyrics_lines[-1] if new_lyrics_lines else "继续前行"
                    for i in range(remaining):
                        # 简单补充，避免调用API
                        supplement_line = f"{template}（续{i+1}）"
                        full_lyrics.append(supplement_line)
            
            lyrics = '\n'.join(full_lyrics)
        else:
            # 如果生成失败，至少返回用户提供的歌词，如果指定了长度则补充到目标长度
            if length and len(previous_lines) < length:
                remaining = length - len(previous_lines)
                last_line = previous_lines[-1] if previous_lines else "继续前行"
                for i in range(remaining):
                    previous_lines.append(f"{last_line}（续{i+1}）")
            if length:
                lyrics = '\n'.join(previous_lines[:length])
            else:
                lyrics = '\n'.join(previous_lines)
        
        # 根据完整歌词和用户想法生成合适的歌名
        lyrics_for_title = lyrics[:500]  # 使用前500字符
        extracted_title = self.deepseek_client._generate_title_from_lyrics(lyrics_for_title, theme, style, user_idea)
        
        # 清理歌词中的标题行（避免重复显示）
        import re
        lyrics_lines = lyrics.split('\n')
        cleaned_lines = []
        for line in lyrics_lines:
            line = line.strip()
            if not line:
                continue
            # 跳过标题行（《歌名》格式或纯歌名）
            is_title_line = False
            if extracted_title:
                # 移除可能的标点符号后比较
                line_clean = re.sub(r'[《》"\'【】\[\]()（）\s]+', '', line)
                title_clean = re.sub(r'[《》"\'【】\[\]()（）\s]+', '', extracted_title)
                if line_clean == title_clean or line == extracted_title or line == f'《{extracted_title}》':
                    is_title_line = True
            # 检查是否是标题格式
            if re.match(r'^《.*》\s*$', line) or re.match(r'^【.*】\s*$', line):
                is_title_line = True
            if not is_title_line:
                cleaned_lines.append(line)
        lyrics = '\n'.join(cleaned_lines)
        
        # 如果指定了长度，最终验证和调整总行数（排除标题，但保留结构标记）
        if length:
            lyrics = self._adjust_lyrics_length_with_structure(lyrics, length, extracted_title)
        else:
            # 不限制长度时，只移除标题，保留所有内容（包括结构标记）
            if extracted_title:
                lyrics_lines = self._get_lyrics_lines_only(lyrics, extracted_title)
                lyrics = '\n'.join(lyrics_lines)
        
        # 构建历史记录的提示词，包含所有用户需求
        history_prompt_parts = ['上下文生成']
        if theme:
            history_prompt_parts.append(f'主题：{theme}')
        if style:
            history_prompt_parts.append(f'风格：{style}')
        if emotion:
            history_prompt_parts.append(f'情感：{emotion}')
        if user_idea:
            history_prompt_parts.append(f'想法：{user_idea[:30]}...' if len(user_idea) > 30 else f'想法：{user_idea}')
        if length:
            history_prompt_parts.append(f'长度：{length}行')
        else:
            history_prompt_parts.append('长度：不限制')
        history_prompt = ' | '.join(history_prompt_parts)
        
        result = {
            'lyrics': lyrics,  # 返回完整歌词（用户输入的 + 新生成的）
            'title': extracted_title,  # 返回提取的歌名
            'context': previous_lines,
            'emotion': emotion or '未指定',
            'theme': theme or '未指定',
            'style': style or '未指定',
            'length': length
        }
        
        # 保存生成历史，使用完整的用户需求信息
        self._save_history(history_prompt, lyrics, style or '通用', user_id)
        
        return result
    
    def generate_full_song(self, style: str = '流行', theme: str = '爱情',
                          emotion: Optional[str] = None, user_idea: Optional[str] = None,
                          length: Optional[int] = None, user_id: int = None) -> Dict:
        """生成完整歌曲"""
        # 使用DeepSeek生成完整歌曲
        prompt = f"创作一首完整的{style}风格歌曲"
        if theme:
            prompt += f"，主题为{theme}"
        if user_idea:
            prompt += f"，用户想法：{user_idea}"
        if length:
            prompt += f"，**必须严格生成{length}行**，不能多也不能少"
        else:
            prompt += "，生成完整歌词，必须包含完整的结构（主歌、副歌等），每个结构标记后都必须有对应的歌词内容，不能中途停止或留下空的结构标记，可以包含\"主歌\"、\"副歌\"等结构标记"
        
        # 如果不限制长度，使用较大的默认长度
        effective_length = length if length else 32
        
        lyrics, title = self.deepseek_client.generate_lyrics_with_title(
            prompt=prompt,
            style=style,
            theme=theme,
            emotion=emotion,
            length=effective_length,  # 使用有效长度
            user_idea=user_idea,
            is_new_generation=True  # 确保每次都是全新生成
        )
        
        # 清理歌词中的标题行、创作说明和说明性文字
        import re
        lyrics_lines = lyrics.split('\n')
        cleaned_lines = []
        skip_until_lyrics = False  # 标记是否遇到说明性文字，需要跳过
        first_line_removed = False  # 标记是否已删除第一行的标题
        
        for i, line in enumerate(lyrics_lines):
            line = line.strip()
            if not line:
                # 如果遇到空行且之前有说明性文字，可能说明部分结束，开始歌词部分
                if skip_until_lyrics:
                    skip_until_lyrics = False
                continue
            
            # 检查是否是说明性文字（如"好的，根据您的想法..."）
            is_explanation = False
            explanation_patterns = [
                r'^好的[，,]?\s*根据.*',
                r'^根据.*为您创作',
                r'^为您创作.*',
                r'^以下.*歌词',
                r'^这是一首.*',
                r'^歌名[：:]\s*《.*》',
                r'^歌名[：:]\s*.*',
            ]
            for pattern in explanation_patterns:
                if re.match(pattern, line, re.IGNORECASE):
                    is_explanation = True
                    skip_until_lyrics = True
                    break
            
            # 如果正在跳过说明部分，继续跳过
            if skip_until_lyrics and not is_explanation:
                # 检查是否开始真正的歌词（通常是结构标记或歌词内容）
                if re.match(r'^(主歌|副歌|预副歌|桥段|间奏|尾奏|前奏|Intro|Verse|Chorus|Bridge|Outro|Interlude)', line, re.IGNORECASE):
                    skip_until_lyrics = False
                elif re.match(r'^[（(](主歌|副歌|预副歌|桥段|间奏|尾奏|前奏)', line, re.IGNORECASE):
                    skip_until_lyrics = False
                else:
                    # 如果这行看起来像歌词（有中文字符且不是说明），停止跳过
                    if re.search(r'[\u4e00-\u9fa5]', line) and not any(p in line for p in ['创作', '说明', '歌名', '根据', '为您']):
                        skip_until_lyrics = False
                    else:
                        continue
            
            if is_explanation:
                continue
            
            # 跳过标题行（但保留**《标题》**格式）
            is_title_line = False
            # 检查是否是加粗的标题行（**《标题》**）- 保留这种格式
            if re.match(r'^\*\*《.*》\*\*\s*$', line):
                # 保留加粗的标题行，不删除
                pass
            elif title:
                # 移除可能的标点符号后比较
                line_clean = re.sub(r'[《》"\'【】\[\]()（）\s\*]+', '', line)
                title_clean = re.sub(r'[《》"\'【】\[\]()（）\s]+', '', title)
                if line_clean == title_clean or line == title or line == f'《{title}》':
                    is_title_line = True
            # 检查是否是标题格式（《...》或【...】）- 删除不加粗的标题格式
            if re.match(r'^《.*》\s*$', line) or re.match(r'^【.*】\s*$', line):
                is_title_line = True
            # 检查是否是"歌名：《...》"格式
            if re.match(r'^歌名[：:]\s*《.*》\s*$', line) or re.match(r'^歌名[：:]\s*.*\s*$', line):
                is_title_line = True
            
            # 删除不需要的标题格式的行（但保留**《标题》**格式）
            if is_title_line:
                continue
            
            # 跳过创作说明
            if '创作说明' in line or '创作思路' in line or line.startswith('创作：'):
                break  # 遇到创作说明，停止处理后续内容
            
            # 如果不是标题行，添加到清理后的列表
            cleaned_lines.append(line)
        
        lyrics = '\n'.join(cleaned_lines)
        
        # 如果指定了长度，验证和调整行数（排除标题，但保留结构标记）
        if length:
            lyrics = self._adjust_lyrics_length_with_structure(lyrics, length, title)
        else:
            # 不限制长度时，保留所有内容（包括结构标记），但已清理标题
            pass
        
        # 构建历史记录的提示词，包含所有用户需求
        history_prompt_parts = ['完整生成']
        if theme:
            history_prompt_parts.append(f'主题：{theme}')
        if style:
            history_prompt_parts.append(f'风格：{style}')
        if emotion:
            history_prompt_parts.append(f'情感：{emotion}')
        if user_idea:
            history_prompt_parts.append(f'想法：{user_idea[:30]}...' if len(user_idea) > 30 else f'想法：{user_idea}')
        if length:
            history_prompt_parts.append(f'长度：{length}行')
        else:
            history_prompt_parts.append('长度：不限制')
        history_prompt = ' | '.join(history_prompt_parts)
        
        result = {
            'lyrics': lyrics,
            'title': title,
            'structure': ['主歌', '副歌', '主歌', '副歌', '桥段', '副歌'],
            'style': style,
            'theme': theme,
            'length': length
        }
        
        self._save_history(history_prompt, lyrics, style or '通用', user_id)
        
        return result
    
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
        
        # 构建历史记录的提示词
        feedback_summary = user_feedback[:50] + '...' if len(user_feedback) > 50 else user_feedback
        history_prompt = f'继续对话 | 用户反馈：{feedback_summary}'
        
        # 保存生成历史
        self._save_history(history_prompt, improved_lyrics, '继续对话', user_id)
        
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
        """保存生成历史（以纯文本格式保存歌词，不使用标题）"""
        try:
            # 直接保存歌词内容，每行保持原样，不使用markdown标题
            markdown_content = lyrics
            
            history = GenerationHistory(
                user_id=user_id,
                prompt=prompt,
                generated_lyrics=markdown_content,
                style=style
            )
            db.session.add(history)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"保存生成历史失败: {e}")
    
    def _is_structure_marker(self, line: str) -> bool:
        """判断一行是否是结构标记（包含"主歌"、"副歌"等描述的行都不算歌词，不计入长度）"""
        import re
        # 先检查是否是标题（标题不是结构标记）
        title_patterns = [
            r'^\*\*《.*》\*\*\s*$',  # 加粗标题格式：**《标题》**
            r'^《.*》\s*$',  # 标题格式：《歌名》
            r'^【.*】\s*$',  # 标题格式：【歌名】
            r'^#{1,6}\s*《.*》\s*$',  # Markdown标题格式：# 《歌名》
            r'^#{1,6}\s*【.*】\s*$',  # Markdown标题格式：# 【歌名】
            r'^歌名[：:]\s*《.*》\s*$',  # 歌名格式：歌名：《星轨证词》
            r'^歌名[：:]\s*.*\s*$',  # 歌名格式：歌名：星轨证词
        ]
        for pattern in title_patterns:
            if re.match(pattern, line, re.IGNORECASE):
                return False  # 标题不是结构标记
        
        # 检查是否是风格说明（如"（古风/国风）"）- 这些也不计入歌词行数
        if re.match(r'^[（(].*[/／].*[）)]\s*$', line):  # 匹配"（古风/国风）"这样的格式
            return True  # 风格说明不计入歌词行数
        
        # **关键：只要一行中包含"主歌"、"副歌"、"第一段"、"第二段"等结构描述关键词，就认为是结构标记，不计入歌词行数**
        structure_keywords = [
            '主歌', '副歌', '预副歌', '桥段', '间奏', '尾奏', '前奏', '尾声',
            '第一段', '第二段', '第三段', '第四段', '第五段', '第六段',
            '第一段：', '第二段：', '第三段：', '第四段：', '第五段：', '第六段：',
            '主歌：', '副歌：', '预副歌：', '桥段：', '间奏：', '尾奏：', '前奏：', '尾声：',
            'Intro', 'Verse', 'Chorus', 'Bridge', 'Outro', 'Interlude'
        ]
        
        # 移除可能的加粗标记、括号、空格等，检查是否只包含结构关键词
        cleaned_line = re.sub(r'\*\*', '', line).strip()  # 移除加粗标记
        cleaned_line = re.sub(r'^[（(]', '', cleaned_line)  # 移除开头的括号
        cleaned_line = re.sub(r'[）)]\s*$', '', cleaned_line)  # 移除结尾的括号
        cleaned_line = cleaned_line.strip()
        
        # 检查是否完全匹配结构关键词（可能带数字）
        for keyword in structure_keywords:
            # 匹配纯结构标记（如"主歌1"、"副歌"、"**主歌1**"、"（主歌1）"等）
            pattern = rf'^{re.escape(keyword)}\s*\d*\s*$'
            if re.match(pattern, cleaned_line, re.IGNORECASE):
                return True
        
        # 检查原始行是否包含结构关键词
        for keyword in structure_keywords:
            if keyword in line:
                # 移除所有可能的格式标记（加粗、括号、空格、数字），检查是否只剩下结构关键词
                test_line = re.sub(r'\*\*', '', line)  # 移除加粗标记
                test_line = re.sub(r'[（()）]', '', test_line)  # 移除括号
                test_line = re.sub(r'\d+', '', test_line)  # 移除数字
                test_line = re.sub(r'\s+', '', test_line)  # 移除空格
                # 如果移除格式标记后只剩下结构关键词，则认为是结构标记
                if test_line == keyword or test_line == keyword.lower() or test_line == keyword.upper():
                    return True
                # 如果整行主要是结构关键词（可能带数字、括号、加粗标记），没有其他实质性内容，也认为是结构标记
                # 检查行中除了结构关键词、数字、括号、加粗标记、空格外，是否还有其他字符
                content_only = re.sub(r'\*\*', '', line)  # 移除加粗标记
                content_only = re.sub(r'[（()）]', '', content_only)  # 移除括号
                content_only = re.sub(r'\d+', '', content_only)  # 移除数字
                content_only = re.sub(r'\s+', '', content_only)  # 移除空格
                # 如果移除格式后只剩下结构关键词，则认为是结构标记
                if content_only == keyword or content_only == keyword.lower() or content_only == keyword.upper():
                    return True
        
        # 检查是否是结构标记（包括加粗格式和括号格式）
        structure_patterns = [
            r'^\*\*((?:主歌|副歌|预副歌|桥段|间奏|尾奏|前奏|第一段|第二段|第三段|第四段|第五段|第六段|Intro|Verse|Chorus|Bridge|Outro|Interlude)\d*)\*\*\s*$',  # 加粗格式：**主歌1**
            r'^[（(]主歌\s*\d*[）)]?\s*$',
            r'^[（(]副歌\s*\d*[）)]?\s*$',
            r'^[（(]预副歌[）)]?\s*$',
            r'^[（(]桥段[）)]?\s*$',
            r'^[（(]尾声[）)]?\s*$',
            r'^[（(]前奏[）)]?\s*$',
            r'^[（(]间奏[）)]?\s*$',
            r'^[（(]尾奏[）)]?\s*$',
            r'^主歌\s*\d*\s*$',
            r'^副歌\s*\d*\s*$',
            r'^预副歌\s*$',
            r'^桥段\s*$',
            r'^间奏\s*$',
            r'^尾奏\s*$',
            r'^前奏\s*$',
            r'^第一段\s*[：:]*\s*$',  # 第一段、第一段：
            r'^第二段\s*[：:]*\s*$',  # 第二段、第二段：
            r'^第三段\s*[：:]*\s*$',  # 第三段、第三段：
            r'^第四段\s*[：:]*\s*$',  # 第四段、第四段：
            r'^第五段\s*[：:]*\s*$',  # 第五段、第五段：
            r'^第六段\s*[：:]*\s*$',  # 第六段、第六段：
            r'^主歌\s*[：:]*\s*$',  # 主歌、主歌：
            r'^副歌\s*[：:]*\s*$',  # 副歌、副歌：
            r'^预副歌\s*[：:]*\s*$',  # 预副歌、预副歌：
            r'^桥段\s*[：:]*\s*$',  # 桥段、桥段：
            r'^间奏\s*[：:]*\s*$',  # 间奏、间奏：
            r'^尾奏\s*[：:]*\s*$',  # 尾奏、尾奏：
            r'^前奏\s*[：:]*\s*$',  # 前奏、前奏：
            r'^Intro\s*$',
            r'^Verse\s*\d*\s*$',
            r'^Chorus\s*$',
            r'^Bridge\s*$',
            r'^Outro\s*$',
        ]
        for pattern in structure_patterns:
            if re.match(pattern, line, re.IGNORECASE):
                return True
        
        return False
    
    def _is_title_line(self, line: str, title: str = None) -> bool:
        """判断一行是否是标题行"""
        if not line or not title:
            return False
        import re
        line_clean = re.sub(r'^#{1,6}\s*', '', line.strip()).strip()
        title_clean = title.strip()
        # 如果这一行完全匹配标题，或者是标题的变体（去掉书名号等）
        if line_clean == title_clean:
            return True
        # 检查是否包含书名号格式的标题
        title_in_brackets = re.sub(r'[《》【】]', '', title_clean)
        if line_clean == title_in_brackets or line_clean == f"《{title_clean}》" or line_clean == f"【{title_clean}】":
            return True
        return False
    
    def _count_lyrics_lines(self, lyrics: str, title: str = None) -> int:
        """计算歌词的实际行数（严格排除标题、结构标记、风格说明等，只计算实际歌词句子）"""
        if not lyrics:
            return 0
        import re
        lines = [line.strip() for line in lyrics.split('\n') if line.strip()]
        lyrics_lines = []
        for line in lines:
            # 排除标题行
            is_title = False
            if title:
                is_title = self._is_title_line(line, title)
            title_patterns = [
                r'^\*\*《.*》\*\*\s*$',  # 加粗标题格式：**《标题》**
                r'^《.*》\s*$',  # 标题格式：《歌名》
                r'^【.*】\s*$',  # 标题格式：【歌名】
                r'^#{1,6}\s*《.*》\s*$',  # Markdown标题格式：# 《歌名》
                r'^#{1,6}\s*【.*】\s*$',  # Markdown标题格式：# 【歌名】
                r'^歌名[：:]\s*《.*》\s*$',  # 歌名格式：歌名：《星轨证词》
                r'^歌名[：:]\s*.*\s*$',  # 歌名格式：歌名：星轨证词
            ]
            for pattern in title_patterns:
                if re.match(pattern, line, re.IGNORECASE):
                    is_title = True
                    break
            if is_title:
                continue
            
            # 排除结构标记和风格说明
            if self._is_structure_marker(line):
                continue
            
            # 只保留实际歌词句子
            lyrics_lines.append(line)
        return len(lyrics_lines)
    
    def _get_lyrics_lines_only(self, lyrics: str, title: str = None) -> List[str]:
        """获取只包含歌词的行（严格排除标题、结构标记、风格说明等，只返回实际歌词句子）"""
        if not lyrics:
            return []
        import re
        lines = [line.strip() for line in lyrics.split('\n') if line.strip()]
        # 排除结构标记和标题，保留实际歌词
        lyrics_lines = []
        for line in lines:
            # 排除标题行
            is_title = False
            if title:
                is_title = self._is_title_line(line, title)
            title_patterns = [
                r'^\*\*《.*》\*\*\s*$',  # 加粗标题格式：**《标题》**
                r'^《.*》\s*$',  # 标题格式：《歌名》
                r'^【.*】\s*$',  # 标题格式：【歌名】
                r'^#{1,6}\s*《.*》\s*$',  # Markdown标题格式：# 《歌名》
                r'^#{1,6}\s*【.*】\s*$',  # Markdown标题格式：# 【歌名】
                r'^歌名[：:]\s*《.*》\s*$',  # 歌名格式：歌名：《星轨证词》
                r'^歌名[：:]\s*.*\s*$',  # 歌名格式：歌名：星轨证词
            ]
            for pattern in title_patterns:
                if re.match(pattern, line, re.IGNORECASE):
                    is_title = True
                    break
            if is_title:
                continue
            
            # 跳过结构标记和风格说明
            if self._is_structure_marker(line):
                continue
            
            # 只保留实际歌词句子
            lyrics_lines.append(line)
        return lyrics_lines
    
    def _adjust_lyrics_length(self, lyrics: str, target_length: int, title: str = None) -> str:
        """调整歌词行数，确保符合目标长度（只计算实际歌词行数，不包括结构标记和标题）
        
        Args:
            lyrics: 原始歌词
            target_length: 目标行数（只计算实际歌词，不包括结构标记和标题）
            title: 标题（可选，如果提供则排除标题行）
        
        Returns:
            调整后的歌词，实际歌词行数正好等于target_length
        """
        if not lyrics:
            # 如果歌词为空，生成默认歌词
            default_lines = ['在时光的河流中', '寻找那失去的梦', '回忆如风般掠过', '留下淡淡的痕迹']
            return '\n'.join(default_lines[:target_length])
        
        # 获取只包含歌词的行（排除结构标记和标题）
        lyrics_lines = self._get_lyrics_lines_only(lyrics, title)
        current_length = len(lyrics_lines)
        
        if current_length == target_length:
            # 行数正好，返回原歌词（但需要移除标题和结构标记）
            # 保留原始格式，但确保只包含实际歌词
            return '\n'.join(lyrics_lines)
        elif current_length > target_length:
            # 行数过多，截取前target_length行歌词
            return '\n'.join(lyrics_lines[:target_length])
        else:
            # 行数不足，需要补充
            remaining = target_length - current_length
            
            if current_length > 0:
                # 如果已有部分歌词，尝试基于现有内容补充
                # 使用最后几行作为上下文，请求生成更多行
                context_lines = lyrics_lines[-min(3, current_length):]
                
                # 使用DeepSeek补充
                try:
                    context_text = '\n'.join(context_lines)
                    supplement_prompt = f"基于以下歌词继续创作，**必须严格生成{remaining}行完整歌词**，保持风格一致，不能中途停止：\n{context_text}"
                    supplement = self.deepseek_client.generate_lyrics(
                        prompt=supplement_prompt,
                        length=remaining,
                        is_new_generation=False
                    )
                    # 解析补充的歌词（排除结构标记）
                    supplement_lines = self._get_lyrics_lines_only(supplement)
                    # 只取需要的行数
                    lyrics_lines.extend(supplement_lines[:remaining])
                except Exception as e:
                    print(f"补充歌词失败: {e}，使用简单补充")
                    # 如果补充失败，使用简单重复
                    last_line = lyrics_lines[-1] if lyrics_lines else "继续前行"
                    for i in range(remaining):
                        new_line = f"{last_line}（续{i+1}）"
                        lyrics_lines.append(new_line)
            else:
                # 如果完全没有歌词，生成默认歌词
                default_lines = [
                    '在时光的河流中', '寻找那失去的梦', '回忆如风般掠过', '留下淡淡的痕迹',
                    '心中的那份执着', '永远不会改变', '即使前路漫漫', '也要勇敢前行',
                    '相信明天会更好', '阳光总会到来', '在黑暗中寻找', '那一束光明',
                    '让希望指引方向', '让梦想照亮前路', '无论多么艰难', '都要坚持到底'
                ]
                # 如果默认歌词不够，循环使用
                while len(default_lines) < target_length:
                    default_lines.extend(default_lines[:target_length - len(default_lines)])
                lyrics_lines = default_lines[:target_length]
            
            # 确保实际歌词行数正好等于target_length
            lyrics_lines = lyrics_lines[:target_length]
            
            # 如果仍然不足，强制补充到目标长度
            if len(lyrics_lines) < target_length:
                remaining_final = target_length - len(lyrics_lines)
                if lyrics_lines:
                    last_line = lyrics_lines[-1]
                    for i in range(remaining_final):
                        new_line = f"{last_line}（续{i+1}）"
                        lyrics_lines.append(new_line)
                else:
                    default_lines = [
                        '在时光的河流中', '寻找那失去的梦', '回忆如风般掠过', '留下淡淡的痕迹',
                        '心中的那份执着', '永远不会改变', '即使前路漫漫', '也要勇敢前行',
                        '相信明天会更好', '阳光总会到来', '在黑暗中寻找', '那一束光明',
                        '让希望指引方向', '让梦想照亮前路', '无论多么艰难', '都要坚持到底'
                    ]
                    lyrics_lines = default_lines[:target_length]
            
            # 重新组合：保留原有的结构标记，插入调整后的歌词
            result_lines = []
            # 如果有结构标记，在适当位置插入
            if structure_markers:
                # 在结构标记后插入对应数量的歌词
                for marker in structure_markers:
                    result_lines.append(marker)
                    # 将所有歌词放在第一个结构标记后（简化处理）
                    if len(result_lines) == 1 and lyrics_lines:
                        for lyric_line in lyrics_lines:
                            result_lines.append(lyric_line)
            else:
                # 没有结构标记，直接返回歌词
                result_lines = lyrics_lines
            
            return '\n'.join(result_lines)
    
    def _adjust_lyrics_length_with_structure(self, lyrics: str, target_length: int, title: str = None) -> str:
        """调整歌词行数，确保符合目标长度（只计算实际歌词行数，不包括结构标记和标题）
        
        Args:
            lyrics: 原始歌词
            target_length: 目标行数（只计算实际歌词，不包括结构标记和标题）
            title: 标题（可选，如果提供则排除标题行）
        
        Returns:
            调整后的歌词，实际歌词行数正好等于target_length（结构标记保留但不计入长度）
        """
        if not lyrics:
            # 如果歌词为空，生成默认歌词
            default_lines = ['在时光的河流中', '寻找那失去的梦', '回忆如风般掠过', '留下淡淡的痕迹']
            return '\n'.join(default_lines[:target_length])
        
        # 获取所有行（排除标题，但保留结构标记用于显示）
        all_lines = [line.strip() for line in lyrics.split('\n') if line.strip()]
        
        # 排除标题行（兼容 Markdown 标题和加粗标题格式）
        import re
        filtered_lines = []
        for line in all_lines:
            # 检查是否是标题行（包括**《标题》**格式）
            is_title = False
            if title:
                is_title = self._is_title_line(line, title)
            # 检查是否是标题格式
            title_patterns = [
                r'^\*\*《.*》\*\*\s*$',  # 加粗标题格式：**《标题》**
                r'^《.*》\s*$',  # 标题格式：《歌名》
                r'^【.*】\s*$',  # 标题格式：【歌名】
                r'^#{1,6}\s*《.*》\s*$',  # Markdown标题格式：# 《歌名》
                r'^#{1,6}\s*【.*】\s*$',  # Markdown标题格式：# 【歌名】
                r'^歌名[：:]\s*《.*》\s*$',  # 歌名格式：歌名：《星轨证词》
                r'^歌名[：:]\s*.*\s*$',  # 歌名格式：歌名：星轨证词
            ]
            for pattern in title_patterns:
                if re.match(pattern, line, re.IGNORECASE):
                    is_title = True
                    break
            if not is_title:
                filtered_lines.append(line)
        
        all_lines = filtered_lines
        
        # 分离结构标记和实际歌词（严格只计算实际歌词句子）
        structure_markers = []
        lyrics_lines = []
        for line in all_lines:
            # 再次检查是否是标题（双重保险，确保标题不计入）
            is_title = False
            if title:
                is_title = self._is_title_line(line, title)
            title_patterns = [
                r'^\*\*《.*》\*\*\s*$',  # 加粗标题格式：**《标题》**
                r'^《.*》\s*$',  # 标题格式：《歌名》
                r'^【.*】\s*$',  # 标题格式：【歌名】
                r'^#{1,6}\s*《.*》\s*$',  # Markdown标题格式：# 《歌名》
                r'^#{1,6}\s*【.*】\s*$',  # Markdown标题格式：# 【歌名】
                r'^歌名[：:]\s*《.*》\s*$',  # 歌名格式：歌名：《星轨证词》
                r'^歌名[：:]\s*.*\s*$',  # 歌名格式：歌名：星轨证词
            ]
            for pattern in title_patterns:
                if re.match(pattern, line, re.IGNORECASE):
                    is_title = True
                    break
            if is_title:
                continue  # 跳过标题行，不计入歌词行数
            
            # 检查是否是结构标记或风格说明
            if self._is_structure_marker(line):
                structure_markers.append(line)
            else:
                # 只保留实际歌词句子
                lyrics_lines.append(line)
        
        # 当前实际歌词行数（严格只计算实际歌词句子，不包括标题、结构标记、风格说明）
        current_length = len(lyrics_lines)
        
        if current_length == target_length:
            # 行数正好，重新组合结构标记和歌词
            result_lines = []
            lyrics_index = 0
            # 保持原有的结构标记位置
            for line in all_lines:
                if self._is_structure_marker(line):
                    result_lines.append(line)
                elif lyrics_index < len(lyrics_lines):
                    result_lines.append(lyrics_lines[lyrics_index])
                    lyrics_index += 1
            return '\n'.join(result_lines)
        elif current_length > target_length:
            # 行数过多，截取前target_length行歌词（保留结构标记）
            result_lines = []
            lyrics_to_use = lyrics_lines[:target_length]
            lyrics_index = 0
            for line in all_lines:
                if self._is_structure_marker(line):
                    result_lines.append(line)
                elif lyrics_index < len(lyrics_to_use):
                    result_lines.append(lyrics_to_use[lyrics_index])
                    lyrics_index += 1
                if lyrics_index >= len(lyrics_to_use):
                    break
            return '\n'.join(result_lines)
        else:
            # 行数不足，需要补充（只补充实际歌词，不包括结构标记）
            remaining = target_length - current_length
            
            if current_length > 0:
                # 如果已有部分歌词，尝试基于现有内容补充
                # 使用最后几行作为上下文，请求生成更多行
                context_lines = lyrics_lines[-min(3, current_length):]
                
                # 使用DeepSeek补充（添加超时和重试限制）
                try:
                    context_text = '\n'.join(context_lines)
                    supplement_prompt = f"基于以下歌词继续创作，**必须严格生成{remaining}行完整歌词**，保持风格一致，不要包含\"第一段\"、\"第二段\"、\"主歌\"、\"副歌\"等结构标记描述，只生成实际歌词内容，不能中途停止：\n{context_text}"
                    
                    # 限制补充行数，防止无限递归
                    if remaining > 50:
                        print(f"警告：补充行数过多（{remaining}行），限制为50行")
                        remaining = 50
                    
                    supplement = self.deepseek_client.generate_lyrics(
                        prompt=supplement_prompt,
                        length=remaining,
                        is_new_generation=False
                    )
                    # 解析补充的歌词（分离结构标记和实际歌词，同时排除标题）
                    supplement_all_lines = [line.strip() for line in supplement.split('\n') if line.strip()]
                    supplement_lyrics = []
                    for line in supplement_all_lines:
                        # 排除标题行
                        is_title = False
                        title_patterns = [
                            r'^\*\*《.*》\*\*\s*$',  # 加粗标题格式：**《标题》**
                            r'^《.*》\s*$',  # 标题格式：《歌名》
                            r'^【.*】\s*$',  # 标题格式：【歌名】
                            r'^#{1,6}\s*《.*》\s*$',  # Markdown标题格式：# 《歌名》
                            r'^#{1,6}\s*【.*】\s*$',  # Markdown标题格式：# 【歌名】
                            r'^歌名[：:]\s*《.*》\s*$',  # 歌名格式：歌名：《星轨证词》
                            r'^歌名[：:]\s*.*\s*$',  # 歌名格式：歌名：星轨证词
                        ]
                        for pattern in title_patterns:
                            if re.match(pattern, line, re.IGNORECASE):
                                is_title = True
                                break
                        # 只添加实际歌词行（排除标题和结构标记）
                        if not is_title and not self._is_structure_marker(line):
                            supplement_lyrics.append(line)
                    
                    # 只取需要的行数，确保不超过目标长度
                    needed = min(remaining, len(supplement_lyrics))
                    lyrics_lines.extend(supplement_lyrics[:needed])
                    
                    # 如果补充后仍然不足，继续补充直到达到目标
                    while len(lyrics_lines) < target_length:
                        remaining_final = target_length - len(lyrics_lines)
                        # 使用最后几行作为模板，生成类似的歌词
                        if len(lyrics_lines) >= 2:
                            # 基于最后两行的风格生成新行
                            template_line = lyrics_lines[-1]
                            # 尝试生成类似风格的歌词
                            for i in range(min(remaining_final, 5)):  # 每次最多补充5行
                                if len(lyrics_lines) >= target_length:
                                    break
                                # 基于模板生成新行（简化处理）
                                new_line = f"{template_line}（续{len(lyrics_lines) + 1}）"
                                lyrics_lines.append(new_line)
                        else:
                            # 如果歌词太少，使用默认补充
                            default_supplement = ['继续前行', '寻找方向', '勇敢面对', '永不放弃', '坚持到底']
                            for i, line in enumerate(default_supplement):
                                if len(lyrics_lines) >= target_length:
                                    break
                                lyrics_lines.append(line)
                        # 如果已经尝试补充但还不够，跳出循环避免死循环
                        if len(lyrics_lines) < target_length and remaining_final == target_length - len(lyrics_lines):
                            break
                except Exception as e:
                    print(f"补充歌词失败: {e}，使用简单补充")
                    # 如果补充失败，使用简单重复（限制补充行数）
                    last_line = lyrics_lines[-1] if lyrics_lines else "继续前行"
                    for i in range(min(remaining, 20)):  # 最多补充20行，防止无限循环
                        new_line = f"{last_line}（续{i+1}）"
                        lyrics_lines.append(new_line)
            else:
                # 如果完全没有歌词，生成默认歌词
                default_lines = [
                    '在时光的河流中', '寻找那失去的梦', '回忆如风般掠过', '留下淡淡的痕迹',
                    '心中的那份执着', '永远不会改变', '即使前路漫漫', '也要勇敢前行',
                    '相信明天会更好', '阳光总会到来', '在黑暗中寻找', '那一束光明',
                    '让希望指引方向', '让梦想照亮前路', '无论多么艰难', '都要坚持到底'
                ]
                # 如果默认歌词不够，循环使用（添加最大循环次数防止死循环）
                max_iterations = 100
                iteration_count = 0
                while len(default_lines) < target_length and iteration_count < max_iterations:
                    extend_count = min(target_length - len(default_lines), len(default_lines))
                    default_lines.extend(default_lines[:extend_count])
                    iteration_count += 1
                lyrics_lines = default_lines[:target_length]
            
            # 确保实际歌词行数正好等于target_length
            lyrics_lines = lyrics_lines[:target_length]
            
            # 重新组合：保留原有的结构标记，插入调整后的歌词
            result_lines = []
            # 如果有结构标记，在适当位置插入
            if structure_markers:
                # 在结构标记后插入对应数量的歌词
                for marker in structure_markers:
                    result_lines.append(marker)
                    # 将所有歌词放在第一个结构标记后（简化处理）
                    if len(result_lines) == 1 and lyrics_lines:
                        for lyric_line in lyrics_lines:
                            result_lines.append(lyric_line)
            else:
                # 没有结构标记，直接返回歌词
                result_lines = lyrics_lines
            
            return '\n'.join(result_lines)
    
    def _clean_lyrics_structure(self, lyrics: str) -> str:
        """清理歌词中的结构标记（如"主歌"、"副歌"等）
        
        Args:
            lyrics: 原始歌词
        
        Returns:
            清理后的歌词（移除结构标记，保留实际歌词内容）
        """
        import re
        
        # 定义需要移除的结构标记关键词
        structure_keywords = [
            r'主歌\s*\d*',
            r'副歌\s*（?[^）]*）?',
            r'预副歌',
            r'桥段',
            r'尾声',
            r'前奏',
            r'间奏',
            r'尾奏',
            r'Intro',
            r'Verse\s*\d*',
            r'Chorus',
            r'Pre-Chorus',
            r'Bridge',
            r'Outro',
            r'Interlude'
        ]
        
        lines = lyrics.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检查是否是结构标记行（整行都是结构标记）
            is_structure_marker = False
            for pattern in structure_keywords:
                # 检查整行是否匹配结构标记（允许前后有少量字符）
                if re.match(rf'^[\s]*{pattern}[\s]*$', line, re.IGNORECASE):
                    is_structure_marker = True
                    break
                # 检查行首是否有结构标记（如"主歌1"、"副歌（升调）"等）
                if re.match(rf'^{pattern}[\s:：]*', line, re.IGNORECASE):
                    # 移除结构标记部分，保留后面的内容
                    cleaned_line = re.sub(rf'^{pattern}[\s:：]*', '', line, flags=re.IGNORECASE)
                    if cleaned_line.strip():
                        cleaned_lines.append(cleaned_line.strip())
                    is_structure_marker = True
                    break
            
            # 如果不是结构标记，保留这一行
            if not is_structure_marker:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def generate_song_from_lyrics(self, 
                                   lyrics: str,
                                   title: str = None,
                                   tags: str = None,
                                   style: str = None,
                                   voice: str = 'default',
                                   make_instrumental: bool = False,
                                   user_id: int = None,
                                   async_mode: bool = True,
                                   max_wait_time: int = 300) -> Dict:
        """根据歌词生成歌曲（使用 Suno API）
        
        Args:
            lyrics: 歌词内容
            title: 歌曲标题（可选，如果不提供则从歌词中提取）
            tags: 风格标签，如 "pop, cheerful, summer"（可选）
            style: 音乐风格（可选，会转换为tags）
            make_instrumental: 是否生成纯音乐（无歌词）
            user_id: 用户ID
            async_mode: 是否异步模式（True=立即返回task_id，False=等待完成）
            max_wait_time: 最大等待时间（秒，仅异步模式=False时有效）
        
        Returns:
            生成结果，包含 task_id 或完整的音频信息
        """
        if not lyrics:
            raise ValueError("歌词不能为空")
        
        # 清理歌词中的结构标记
        cleaned_lyrics = self._clean_lyrics_structure(lyrics)
        
        # 如果没有提供标题，尝试从歌词中提取
        if not title:
            # 使用清理后的第一行或前几个关键词作为标题
            lines = [line.strip() for line in cleaned_lyrics.split('\n') if line.strip()]
            if lines:
                title = lines[0][:30]  # 使用第一行前30个字符
            else:
                title = "生成的歌曲"
        
        # 如果没有提供tags，根据style生成
        if not tags and style:
            style_tags_map = {
                '流行': 'pop, modern, catchy',
                '摇滚': 'rock, energetic, powerful',
                '抒情': 'ballad, emotional, soft',
                '古风': 'chinese traditional, classical, elegant',
                '民谣': 'folk, acoustic, simple',
                '电子': 'electronic, synth, dance',
                '爵士': 'jazz, smooth, sophisticated',
                '说唱': 'rap, hip-hop, rhythmic'
            }
            tags = style_tags_map.get(style, 'pop, modern')
        
        # 如果没有tags，使用默认值
        if not tags:
            tags = 'pop, modern, catchy'
        
        # 根据语音选择添加相应的tags
        if voice == 'male':
            tags = f"{tags}, male voice, deep voice" if tags else "male voice, deep voice"
        elif voice == 'female':
            tags = f"{tags}, female voice, soft voice" if tags else "female voice, soft voice"
        # default 不添加额外标签
        
        try:
            if async_mode:
                # 异步模式：提交任务并立即返回task_id
                result = self.suno_client.generate_music(
                    lyrics=cleaned_lyrics,  # 使用清理后的歌词
                    title=title,
                    tags=tags,
                    make_instrumental=make_instrumental,
                    model=SunoModel.CHIRP_V4_5,
                    custom_mode=True
                )
                
                # 保存生成历史（保存原始歌词，包含结构标记）
                self._save_song_generation_history(
                    user_id=user_id,
                    lyrics=lyrics,  # 保存原始歌词（包含结构标记）
                    title=title,
                    tags=tags,
                    task_id=result['task_id'],
                    status='pending'
                )
                
                return {
                    'task_id': result['task_id'],
                    'status': 'pending',
                    'message': '歌曲生成任务已提交，请使用 task_id 查询进度',
                    'query_url': f'/api/generation/song/status?task_id={result["task_id"]}'
                }
            else:
                # 同步模式：等待任务完成
                result = self.suno_client.generate_music_sync(
                    lyrics=cleaned_lyrics,  # 使用清理后的歌词
                    title=title,
                    tags=tags,
                    make_instrumental=make_instrumental,
                    model=SunoModel.CHIRP_V4_5,
                    custom_mode=True,
                    max_wait_time=max_wait_time
                )
                
                # 处理结果
                clips = result.get('clips', [])
                if not clips:
                    raise Exception("生成失败：未返回音频文件")
                
                # 提取第一个完成的音频（通常是最完整的）
                completed_clips = [c for c in clips if c.get('status') == 'complete' and c.get('audio_url')]
                if not completed_clips:
                    # 如果没有完成的，使用第一个
                    completed_clips = clips
                
                best_clip = completed_clips[0]
                
                # 保存生成历史
                self._save_song_generation_history(
                    user_id=user_id,
                    lyrics=lyrics,
                    title=title,
                    tags=tags,
                    task_id=result.get('task_id', ''),
                    status='completed',
                    audio_url=best_clip.get('audio_url'),
                    image_url=best_clip.get('image_url'),
                    duration=best_clip.get('duration', 0)
                )
                
                return {
                    'status': 'completed',
                    'title': title,
                    'lyrics': lyrics,
                    'audio_url': best_clip.get('audio_url'),
                    'image_url': best_clip.get('image_url'),
                    'video_url': best_clip.get('video_url'),
                    'duration': best_clip.get('duration', 0),
                    'clips': clips,
                    'tags': tags
                }
        except Exception as e:
            print(f"生成歌曲失败: {e}")
            raise Exception(f"生成歌曲失败: {str(e)}")
    
    def query_song_generation_status(self, task_id: str) -> Dict:
        """查询歌曲生成任务状态
        
        Args:
            task_id: 任务ID
        
        Returns:
            任务状态和结果
        """
        try:
            result = self.suno_client.query_task(task_id)
            return result
        except Exception as e:
            raise Exception(f"查询任务状态失败: {str(e)}")
    
    def _save_song_generation_history(self, user_id: int = None, lyrics: str = None,
                                    title: str = None, tags: str = None,
                                    task_id: str = None, status: str = 'pending',
                                    audio_url: str = None, image_url: str = None,
                                    duration: float = 0):
        """保存歌曲生成历史（以markdown格式保存歌词）"""
        try:
            # 将歌曲生成信息保存到 GenerationHistory
            # 使用 prompt 字段存储任务信息
            prompt = f"歌曲生成: {title or '未命名'}"
            if tags:
                prompt += f" | 标签: {tags}"
            if task_id:
                prompt += f" | 任务ID: {task_id}"
            
            # 构建markdown格式的歌词内容（不使用标题）
            markdown_content = []
            # 直接保存歌词内容，不使用标题
            if lyrics:
                # 将歌词按行分割，每行作为独立的段落
                lyrics_lines = lyrics.split('\n')
                for line in lyrics_lines:
                    if line.strip():
                        markdown_content.append(f"{line.strip()}\n")
                markdown_content.append("\n")
            
            # 添加元数据信息（不使用标题）
            markdown_content.append("---\n\n")
            if tags:
                markdown_content.append(f"- **风格标签**: {tags}\n")
            if status:
                status_text = {'pending': '处理中', 'completed': '已完成', 'failed': '失败'}.get(status, status)
                markdown_content.append(f"- **状态**: {status_text}\n")
            if duration:
                markdown_content.append(f"- **时长**: {duration:.2f} 秒\n")
            if audio_url:
                markdown_content.append(f"- **音频链接**: [{audio_url}]({audio_url})\n")
            if image_url:
                markdown_content.append(f"- **封面图片**: ![封面]({image_url})\n")
            if task_id:
                markdown_content.append(f"- **任务ID**: `{task_id}`\n")
            
            # 同时保存JSON格式的完整数据（用于程序读取）
            import json
            song_data = {
                'lyrics': lyrics,
                'title': title,
                'tags': tags,
                'task_id': task_id,
                'status': status,
                'audio_url': audio_url,
                'image_url': image_url,
                'duration': duration
            }
            
            # 在generated_lyrics中保存markdown格式（供显示）和JSON数据（供程序使用）
            markdown_text = ''.join(markdown_content)
            # 将JSON数据追加到markdown后面，使用分隔符
            full_content = f"{markdown_text}\n\n---\n\n<!-- JSON数据开始 -->\n```json\n{json.dumps(song_data, ensure_ascii=False, indent=2)}\n```\n<!-- JSON数据结束 -->"
            
            # 检查是否已存在相同task_id的记录，如果存在则更新，否则创建新记录
            existing_history = GenerationHistory.query.filter(
                GenerationHistory.prompt.like(f'%{task_id}%')
            ).first() if task_id else None
            
            if existing_history:
                # 更新现有记录
                existing_history.generated_lyrics = full_content
                existing_history.prompt = prompt
                existing_history.style = tags or '歌曲生成'
            else:
                # 创建新记录
                history = GenerationHistory(
                    user_id=user_id,
                    prompt=prompt,
                    generated_lyrics=full_content,
                    style=tags or '歌曲生成'
                )
                db.session.add(history)
            
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"保存歌曲生成历史失败: {e}")
    
    def get_history(self, user_id: int = None, limit: int = 10) -> List[Dict]:
        """获取生成历史"""
        from app.models import GenerationHistory
        
        query = GenerationHistory.query
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        histories = query.order_by(GenerationHistory.created_at.desc()).limit(limit).all()
        return [h.to_dict() for h in histories]

