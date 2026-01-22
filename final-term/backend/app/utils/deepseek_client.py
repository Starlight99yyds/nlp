"""
DeepSeek API客户端
用于高级歌词生成和优化
"""
import os
from typing import List, Dict, Optional
from openai import OpenAI

class DeepSeekClient:
    """DeepSeek API客户端"""
    
    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or os.environ.get('DEEPSEEK_API_KEY', '')
        self.base_url = base_url or os.environ.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
        
        # 初始化OpenAI客户端（兼容DeepSeek API）
        if self.api_key:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=60.0  # 60秒超时
            )
        else:
            self.client = None
    
    def extract_title_from_idea(self, user_idea: str) -> Optional[str]:
        """从用户想法中提取歌名（可选，不强求）"""
        if not user_idea:
            return None
        
        import re
        # 匹配明确的歌名表达方式（只在用户明确提到时才提取）
        patterns = [
            r'歌名[是：:]([^，。\n]+)',
            r'标题[是：:]([^，。\n]+)',
            r'《([^》]+)》',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, user_idea)
            if match:
                title = match.group(1).strip()
                # 清理可能的标点符号
                title = re.sub(r'[，。！？、\s]+$', '', title)
                if title and len(title) <= 50:  # 歌名不应该太长
                    return title
        
        return None
    
    def generate_lyrics_with_title(self, prompt: str, style: str = None, theme: str = None, 
                       emotion: str = None, length: Optional[int] = 16, 
                       context: List[str] = None, user_idea: str = None, 
                       is_new_generation: bool = True) -> tuple:
        """生成歌词并生成合适的歌名
        
        Returns:
            (lyrics, title): 歌词和歌名的元组
        """
        # 生成歌词
        lyrics = self.generate_lyrics(prompt, style, theme, emotion, length, context, user_idea, is_new_generation)
        
        # 使用DeepSeek根据歌词内容和用户想法生成合适的歌名
        extracted_title = self._generate_title_from_lyrics(lyrics, theme, style, user_idea)
        
        return lyrics, extracted_title
    
    def _generate_title_from_lyrics(self, lyrics: str, theme: str = None, style: str = None, user_idea: str = None) -> Optional[str]:
        """使用DeepSeek从歌词生成歌名"""
        if not self.api_key or not self.client:
            return None
        
        prompt = "请为以下歌词创作一个合适的歌名，要求：\n"
        prompt += "1. 歌名应该简洁有力，2-8个字\n"
        prompt += "2. 歌名应该能够概括歌词的主题和情感\n"
        prompt += "3. 只输出歌名，不要添加任何解释或说明\n"
        
        if theme:
            prompt += f"主题：{theme}\n"
        if style:
            prompt += f"风格：{style}\n"
        if user_idea:
            prompt += f"用户想法：{user_idea}\n"
        
        prompt += f"\n歌词：\n{lyrics[:500]}\n\n请只输出歌名，不要其他内容。"
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {'role': 'system', 'content': '你是一位专业的歌词创作专家，擅长为歌词创作合适的歌名。'},
                    {'role': 'user', 'content': prompt}
                ],
                temperature=0.7,
                max_tokens=50,
                stream=False
            )
            
            title = response.choices[0].message.content.strip()
            # 清理可能的标点符号和多余内容
            import re
            title = re.sub(r'[《》"\'【】\[\]()（）\s]+', '', title)
            title = re.sub(r'[，。！？、：:]+$', '', title)
            # 如果标题太长，截取前20个字符
            if len(title) > 20:
                title = title[:20]
            
            return title if title else None
        except Exception as e:
            print(f"生成歌名失败: {e}")
            return None
    
    def generate_lyrics(self, prompt: str, style: str = None, theme: str = None, 
                       emotion: str = None, length: Optional[int] = 16, 
                       context: List[str] = None, user_idea: str = None, 
                       is_new_generation: bool = True) -> str:
        """生成歌词
        
        Args:
            is_new_generation: 是否为全新生成，True时确保每次都是独立的创作
        """
        if not self.api_key or not self.client:
            return self._fallback_generate(prompt, style, theme, emotion, length)
        
        messages = self._build_messages(prompt, style, theme, emotion, length, context, user_idea, is_new_generation)
        
        try:
            # 根据长度计算需要的token数（每行约20-30个token，加上一些缓冲）
            # 如果不限制长度，使用足够大的值以确保生成完整歌词
            if length:
                effective_length = length
                estimated_tokens = max(2000, effective_length * 30 + 500)
            else:
                # 不限制长度时，使用足够大的token数（约100行歌词，3000+ tokens）
                estimated_tokens = 4000  # 足够生成完整歌词
            
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                temperature=0.8,
                max_tokens=estimated_tokens,  # 根据长度动态调整token数
                stream=False
            )
            
            lyrics = response.choices[0].message.content
            
            # 移除解释部分（如果包含"调性"、"节奏"、"创作说明"等关键词，只保留歌词部分）
            import re
            # 查找可能的解释部分（通常在歌词后面，包含"调性"、"节奏"、"风格"、"创作说明"等词）
            explanation_patterns = [
                r'调性[：:].*',
                r'节奏[：:].*',
                r'风格[：:].*',
                r'特点[：:].*',
                r'说明[：:].*',
                r'解释[：:].*',
                r'注[：:].*',
                r'创作说明[：:].*',
                r'创作思路[：:].*',
                r'创作[：:].*',
            ]
            for pattern in explanation_patterns:
                lyrics = re.sub(pattern, '', lyrics, flags=re.IGNORECASE | re.DOTALL)
            
            # 移除"创作说明："之后的所有内容
            if '创作说明' in lyrics or '创作思路' in lyrics:
                # 找到"创作说明"或"创作思路"的位置，删除之后的所有内容
                for marker in ['创作说明', '创作思路', '创作：']:
                    idx = lyrics.find(marker)
                    if idx != -1:
                        lyrics = lyrics[:idx].strip()
                        break
            
            # 处理歌词格式：遵循模板格式
            lyrics = lyrics.strip()
            
            import re
            # 提取标题（**《标题》**格式）
            title = None
            title_match = re.search(r'\*\*《([^》]+)》\*\*', lyrics)
            if title_match:
                title = title_match.group(1)
            
            # 按行处理
            lines = lyrics.split('\n')
            processed_lines = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    processed_lines.append('')
                    continue
                
                # 跳过创作思路等说明性内容
                if any(keyword in line for keyword in ['创作说明', '创作思路', '调性', '节奏', '风格说明', '特点：']):
                    break
                
                # 检查是否是加粗的标题行（**《标题》**）
                title_bold_match = re.match(r'^\*\*《([^》]+)》\*\*\s*$', line)
                if title_bold_match:
                    # 保留标题，但提取标题内容
                    title = title_bold_match.group(1)
                    processed_lines.append(f'**《{title}》**')
                    continue
                
                # 检查是否是加粗的结构标记行（**主歌1**、**副歌**等）
                structure_bold_match = re.match(r'^\*\*((?:主歌|副歌|预副歌|桥段|间奏|尾奏|前奏|Intro|Verse|Chorus|Bridge|Outro|Interlude)\d*)\*\*\s*$', line)
                if structure_bold_match:
                    # 保留加粗的结构标记
                    structure_marker = structure_bold_match.group(1)
                    processed_lines.append(f'**{structure_marker}**')
                    continue
                
                # 检查是否是纯结构标记行（主歌1，没有加粗）
                structure_match = re.match(r'^((?:主歌|副歌|预副歌|桥段|间奏|尾奏|前奏|Intro|Verse|Chorus|Bridge|Outro|Interlude)\d*)\s*$', line)
                if structure_match:
                    # 转换为加粗格式
                    structure_marker = structure_match.group(1)
                    processed_lines.append(f'**{structure_marker}**')
                    continue
                
                # 检查行首是否有结构标记（如"主歌1 夜空之中..."或"**主歌1** 夜空之中..."）
                structure_prefix_match = re.match(r'^(?:\*\*)?((?:主歌|副歌|预副歌|桥段|间奏|尾奏|前奏|Intro|Verse|Chorus|Bridge|Outro|Interlude)\d*)(?:\*\*)?\s+(.+)$', line)
                if structure_prefix_match:
                    # 有结构标记，提取标记和内容
                    structure_marker = structure_prefix_match.group(1)
                    content = structure_prefix_match.group(2)
                    processed_lines.append(f'**{structure_marker}**')
                    # 处理内容部分：将所有空格分隔的词语都转换为单独的行
                    content = re.sub(r'\s{2,}', ' ', content)
                    content_parts = [part.strip() for part in content.split() if part.strip()]
                    processed_lines.extend(content_parts)
                else:
                    # 普通歌词行，将空格分隔的内容转换为换行
                    line = re.sub(r'\s{2,}', '\n', line)
                    # 处理单个空格（中文字符之间）
                    for _ in range(100):  # 限制循环次数
                        new_line = re.sub(r'([\u4e00-\u9fa5])\s+([\u4e00-\u9fa5])', r'\1\n\2', line)
                        if new_line == line:
                            break
                        line = new_line
                    # 按换行分割并添加
                    line_parts = [lp.strip() for lp in line.split('\n') if lp.strip()]
                    processed_lines.extend(line_parts)
            
            lyrics = '\n'.join(processed_lines)
            
            # 过滤掉不需要的标题格式（但保留**《标题》**格式）
            title_patterns = [
                r'^《.*》\s*$',  # 标题格式：《歌名》（不加粗）
                r'^【.*】\s*$',  # 标题格式：【歌名】
                r'^#{1,6}\s*《.*》\s*$',  # Markdown标题格式：# 《歌名》
                r'^#{1,6}\s*【.*】\s*$',  # Markdown标题格式：# 【歌名】
                r'^歌名[：:]\s*《.*》\s*$',  # 歌名格式：歌名：《星轨证词》
                r'^歌名[：:]\s*.*\s*$',  # 歌名格式：歌名：星轨证词
            ]
            
            # 确保每行一句，并在每行后添加 <br/> 标签以确保换行
            final_lines = []
            for line in lyrics.split('\n'):
                line = line.strip()
                if not line:
                    final_lines.append('')  # 保留空行
                    continue
                # 跳过不需要的标题格式（但保留**《标题》**格式）
                is_title = False
                for pattern in title_patterns:
                    if re.match(pattern, line, re.IGNORECASE):
                        is_title = True
                        break
                if is_title:
                    continue
                # 如果一行包含多句（有多个句号、问号、感叹号），分割成多行
                if len(re.findall(r'[。！？]', line)) > 1:
                    parts = re.split(r'([。！？])', line)
                    current = ''
                    for i in range(0, len(parts), 2):
                        if i+1 < len(parts):
                            current += parts[i] + parts[i+1]
                            if current.strip():
                                final_lines.append(current.strip() + ' <br/>')
                                current = ''
                        elif parts[i].strip():
                            current = parts[i]
                    if current.strip():
                        final_lines.append(current.strip() + ' <br/>')
                else:
                    # 每行歌词后添加 <br/> 确保换行
                    final_lines.append(line + ' <br/>')
            
            return '\n'.join(final_lines)
        except Exception as e:
            error_msg = str(e)
            # 检查是否是余额不足错误
            if "402" in error_msg or "Insufficient Balance" in error_msg or "余额" in error_msg.lower():
                print(f"DeepSeek API余额不足，已切换到本地生成模式: {error_msg}")
            else:
                print(f"DeepSeek API调用失败，已切换到本地生成模式: {error_msg}")
            return self._fallback_generate(prompt, style, theme, emotion, length)
    
    def convert_style(self, lyrics: str, target_style: str) -> str:
        """风格转换（整体转换，不是简单加词）"""
        if not self.api_key or not self.client:
            return lyrics  # 如果没配置API，返回原歌词
        
        prompt = f"""请将以下歌词整体转换为{target_style}风格。要求：
1. 保持原歌词的核心意思和情感
2. 改变表达方式、用词、句式结构，使其符合{target_style}风格的特点
3. 保持歌词的完整性和连贯性
4. 不要只是在原歌词后面加词，而是整体改写
5. **重要：每行歌词必须单独一行，使用换行符分隔，不要将所有歌词放在同一行**

原歌词：
{lyrics}

请直接输出转换后的完整歌词，每行一句，使用换行符分隔，不要添加任何解释或标记。"""
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {'role': 'system', 'content': '你是一位专业的歌词创作和风格转换专家。'},
                    {'role': 'user', 'content': prompt}
                ],
                temperature=0.7,
                max_tokens=2000,
                stream=False
            )
            
            converted = response.choices[0].message.content
            # 确保歌词有换行，每行一句
            converted = converted.strip()
            
            # 移除创作说明
            if '创作说明' in converted or '创作思路' in converted:
                # 找到"创作说明"的位置，删除之后的所有内容
                for marker in ['创作说明', '创作思路', '创作：']:
                    idx = converted.find(marker)
                    if idx != -1:
                        converted = converted[:idx].strip()
                        break
            
            # 处理换行：确保每行一句
            import re
            lines = []
            for line in converted.split('\n'):
                line = line.strip()
                if not line:
                    continue
                # 跳过创作说明行
                if '创作说明' in line or '创作思路' in line or line.startswith('创作：'):
                    break
                # 如果一行包含多句（有多个句号、问号、感叹号），分割成多行
                if len(re.findall(r'[。！？]', line)) > 1:
                    # 按句号、问号、感叹号分割
                    parts = re.split(r'([。！？])', line)
                    current = ''
                    for i in range(0, len(parts), 2):
                        if i+1 < len(parts):
                            current += parts[i] + parts[i+1]
                            if current.strip():
                                lines.append(current.strip())
                                current = ''
                        elif parts[i].strip():
                            current = parts[i]
                    if current.strip():
                        lines.append(current.strip())
                else:
                    lines.append(line)
            
            # 如果还是没有换行，尝试按逗号、顿号等分割
            if len(lines) == 1 and len(lines[0]) > 50:
                # 按逗号、顿号分割
                line = lines[0]
                parts = re.split(r'([，、])', line)
                lines = []
                current = ''
                for i in range(0, len(parts), 2):
                    if i+1 < len(parts):
                        current += parts[i] + parts[i+1]
                        if len(current) > 20:  # 如果累积到一定长度，换行
                            lines.append(current.strip())
                            current = ''
                    elif parts[i].strip():
                        current = parts[i]
                if current.strip():
                    lines.append(current.strip())
            
            return '\n'.join(lines)
        except Exception as e:
            error_msg = str(e)
            if "402" in error_msg or "Insufficient Balance" in error_msg or "余额" in error_msg.lower():
                print(f"DeepSeek API余额不足，风格转换失败，返回原歌词: {error_msg}")
            else:
                print(f"风格转换失败，返回原歌词: {error_msg}")
            return lyrics
    
    def continue_conversation(self, previous_lyrics: str, user_feedback: str) -> str:
        """继续对话，根据用户反馈修改歌词"""
        if not self.api_key or not self.client:
            return previous_lyrics
        
        prompt = f"""以下是之前生成的歌词：

{previous_lyrics}

用户反馈：{user_feedback}

请根据用户的反馈，对歌词进行修改和完善。

**重要要求：**
1. 每行歌词必须单独一行，使用换行符分隔
2. 不要将所有歌词放在同一行
3. 保持歌词的格式和结构
4. 直接输出修改后的完整歌词，不要添加任何解释或标记"""
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {'role': 'system', 'content': '你是一位专业的歌词创作专家，擅长根据用户反馈优化歌词。'},
                    {'role': 'user', 'content': prompt}
                ],
                temperature=0.8,
                max_tokens=2000,
                stream=False
            )
            
            improved = response.choices[0].message.content
            # 确保歌词有换行，每行一句
            improved = improved.strip()
            
            # 移除创作说明
            if '创作说明' in improved or '创作思路' in improved:
                # 找到"创作说明"的位置，删除之后的所有内容
                for marker in ['创作说明', '创作思路', '创作：']:
                    idx = improved.find(marker)
                    if idx != -1:
                        improved = improved[:idx].strip()
                        break
            
            # 处理歌词格式：确保每行一句，不使用空格分隔（与generate_lyrics保持一致）
            import re
            # 按行处理，确保结构标记后的内容都单独提行
            lines = improved.split('\n')
            processed_lines = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    processed_lines.append('')
                    continue
                
                # 检查是否是纯结构标记行（如"主歌1"）
                structure_match = re.match(r'^((?:主歌|副歌|预副歌|桥段|间奏|尾奏|前奏|Intro|Verse|Chorus|Bridge|Outro|Interlude)\d*)$', line)
                if structure_match:
                    # 纯结构标记，单独一行
                    processed_lines.append(line)
                    continue
                
                # 检查行首是否有结构标记（如"主歌1 夜空之中 沉默着..."）
                structure_prefix_match = re.match(r'^((?:主歌|副歌|预副歌|桥段|间奏|尾奏|前奏|Intro|Verse|Chorus|Bridge|Outro|Interlude)\d*)\s+(.+)$', line)
                if structure_prefix_match:
                    # 有结构标记，提取标记和内容
                    structure_marker = structure_prefix_match.group(1)
                    content = structure_prefix_match.group(2)
                    processed_lines.append(structure_marker)
                    # 处理内容部分：将所有空格分隔的词语都转换为单独的行
                    # 先处理多个连续空格
                    content = re.sub(r'\s{2,}', ' ', content)
                    # 按空格分割，每个词语单独一行
                    content_parts = [part.strip() for part in content.split() if part.strip()]
                    processed_lines.extend(content_parts)
                else:
                    # 普通行（没有结构标记），将空格分隔的内容转换为换行
                    # 先处理多个连续空格
                    line = re.sub(r'\s{2,}', '\n', line)
                    # 然后处理单个空格（中文字符之间）
                    for _ in range(100):  # 限制循环次数
                        new_line = re.sub(r'([\u4e00-\u9fa5])\s+([\u4e00-\u9fa5])', r'\1\n\2', line)
                        if new_line == line:
                            break
                        line = new_line
                    # 按换行分割并添加
                    line_parts = [lp.strip() for lp in line.split('\n') if lp.strip()]
                    processed_lines.extend(line_parts)
            
            improved = '\n'.join(processed_lines)
            
            # 保留结构标记（如"（主歌1）"、"（副歌2）"等），只移除标题
            title_patterns = [
                r'^《.*》\s*$',  # 标题格式：《歌名》
                r'^【.*】\s*$',  # 标题格式：【歌名】
                r'^#{1,6}\s*《.*》\s*$',  # Markdown标题格式：# 《歌名》
                r'^#{1,6}\s*【.*】\s*$',  # Markdown标题格式：# 【歌名】
                r'^歌名[：:]\s*《.*》\s*$',  # 歌名格式：歌名：《星轨证词》
                r'^歌名[：:]\s*.*\s*$',  # 歌名格式：歌名：星轨证词
            ]
            
            # 确保每行一句，并在每行后添加 <br/> 标签以确保换行
            final_lines = []
            for line in improved.split('\n'):
                line = line.strip()
                if not line:
                    final_lines.append('')  # 保留空行
                    continue
                # 跳过标题行（但不跳过结构标记）
                is_title = False
                for pattern in title_patterns:
                    if re.match(pattern, line, re.IGNORECASE):
                        is_title = True
                        break
                if is_title:
                    continue
                # 如果一行包含多句（有多个句号、问号、感叹号），分割成多行
                if len(re.findall(r'[。！？]', line)) > 1:
                    parts = re.split(r'([。！？])', line)
                    current = ''
                    for i in range(0, len(parts), 2):
                        if i+1 < len(parts):
                            current += parts[i] + parts[i+1]
                            if current.strip():
                                final_lines.append(current.strip() + ' <br/>')
                                current = ''
                        elif parts[i].strip():
                            current = parts[i]
                    if current.strip():
                        final_lines.append(current.strip() + ' <br/>')
                else:
                    # 每行歌词后添加 <br/> 确保换行
                    final_lines.append(line + ' <br/>')
            
            return '\n'.join(final_lines)
        except Exception as e:
            error_msg = str(e)
            if "402" in error_msg or "Insufficient Balance" in error_msg or "余额" in error_msg.lower():
                print(f"DeepSeek API余额不足，对话继续失败，返回原歌词: {error_msg}")
            else:
                print(f"对话继续失败，返回原歌词: {error_msg}")
            return previous_lyrics
    
    def _build_messages(self, prompt: str, style: str, theme: str, emotion: str, 
                       length: Optional[int], context: List[str], user_idea: str, is_new_generation: bool = True) -> List[Dict]:
        """构建消息列表
        
        Args:
            is_new_generation: 是否为全新生成（True时忽略context，确保每次都是独立的）
        """
        system_prompt = "你是一位专业的歌词创作专家，擅长创作各种风格和主题的歌词。每次创作都是全新的、独立的作品，不受之前任何创作的影响。你能够深入理解用户的需求，包括从用户想法中提取歌名、主题、情感等关键信息。"
        
        user_prompt = "请创作一首全新的歌词，要求如下：\n"
        
        # 如果是全新生成，明确说明不要参考任何历史
        if is_new_generation:
            user_prompt += "注意：这是一次全新的创作，请完全独立创作，不要参考或延续任何之前的歌词内容。\n"
        
        if user_idea:
            user_prompt += f"用户想法：{user_idea}\n"
            user_prompt += "**重要：请仔细理解用户的想法和需求，根据用户的描述创作符合其期望的歌词。**\n"
        
        if theme:
            user_prompt += f"主题：{theme}\n"
        
        if style:
            user_prompt += f"风格：{style}\n"
        
        if emotion:
            user_prompt += f"情感基调：{emotion}\n"
        
        # 只有在明确需要基于上下文时（如继续对话功能），才使用context
        if context and not is_new_generation:
            if isinstance(context, list) and len(context) > 0:
                user_prompt += f"\n上下文（前文）：\n" + "\n".join(context) + "\n"
                user_prompt += "请基于上下文继续创作，保持连贯性和风格一致。\n"
            elif isinstance(context, str) and context.strip():
                user_prompt += f"\n上下文（前文）：\n{context}\n"
                user_prompt += "请基于上下文继续创作，保持连贯性和风格一致。\n"
        
        # 统一的格式要求
        user_prompt += "\n**严格遵循以下输出格式模板：**\n"
        user_prompt += "1. **第一行必须是加粗的标题**：使用 **《歌名》** 格式（例如：**《星火为眸》**）\n"
        user_prompt += "2. **结构标记单独一行并使用加粗**：每行结构标记使用 **主歌1**、**副歌**、**预副歌**、**桥段** 等格式，单独占一行\n"
        user_prompt += "3. **歌词每句一行，不加粗**：每句歌词单独一行，不使用加粗格式\n"
        user_prompt += "4. **不要输出任何创作思路、说明、解释等额外内容**\n"
        user_prompt += "\n**示例格式：**\n"
        user_prompt += "**《星火为眸》**\n"
        user_prompt += "**主歌1**\n"
        user_prompt += "夜空之中\n"
        user_prompt += "沉默着\n"
        user_prompt += "听不到\n"
        user_prompt += "我微弱的脉搏\n"
        user_prompt += "**副歌**\n"
        user_prompt += "请以星火为眸\n"
        user_prompt += "凝视这具躯壳\n"
        user_prompt += "\n"
        
        if length:
            user_prompt += f"长度：**必须严格生成{length}行完整歌词**（不包括标题行，但包括结构标记行），不能多也不能少\n"
            user_prompt += "\n**重要要求：**\n"
            user_prompt += "1. **必须严格生成{length}行完整歌词（不包括标题行），一行不多，一行不少**\n".format(length=length)
            user_prompt += "2. **必须生成完整的歌词，不能中途停止或截断**\n"
            user_prompt += "3. 每行歌词必须单独一行，使用换行符（\\n）分隔\n"
            user_prompt += "4. 不要使用空格分隔歌词，必须使用换行符\n"
            user_prompt += "5. 每句歌词独占一行\n"
            user_prompt += "6. **结构标记（如\"**主歌1**\"、\"**副歌**\"等）单独一行，计入总行数**\n"
            user_prompt += "7. 请根据用户的想法和需求，创作符合用户期望的歌词内容\n"
            user_prompt += "8. **只输出歌词内容，严格按照格式模板，不要添加任何解释、调性说明、节奏说明、风格说明、创作思路等额外内容**\n"
            user_prompt += "9. **最后请确认输出的歌词行数（不包括标题行）正好是{length}行（包括结构标记），且歌词完整**\n".format(length=length)
        else:
            user_prompt += "长度：**不限制长度，生成完整歌词**\n"
            user_prompt += "\n**重要要求：**\n"
            user_prompt += "1. **生成完整的歌词，不能中途停止或截断**\n"
            user_prompt += "2. 每行歌词必须单独一行，使用换行符（\\n）分隔\n"
            user_prompt += "3. 不要使用空格分隔歌词，必须使用换行符\n"
            user_prompt += "4. 每句歌词独占一行\n"
            user_prompt += "5. **结构标记（如\"**主歌1**\"、\"**副歌**\"等）单独一行**\n"
            user_prompt += "6. 请根据用户的想法和需求，创作符合用户期望的完整歌词内容\n"
            user_prompt += "7. **只输出歌词内容，严格按照格式模板，不要添加任何解释、调性说明、节奏说明、风格说明、创作思路等额外内容**\n"
        
        if prompt:
            user_prompt = prompt
        
        return [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ]
    
    def _fallback_generate(self, prompt: str, style: str, theme: str, 
                          emotion: str, length: int) -> str:
        """备用生成方法（当API不可用时，使用本地生成器）"""
        import sys
        import os
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)
        
        from nlp_engine.generation import LyricsGenerator
        generator = LyricsGenerator()
        
        # 使用本地生成器
        if theme:
            emotion = emotion or '中性'
            return generator.generate_by_theme(theme, emotion, length)
        else:
            # 如果没有主题，生成通用歌词
            lines = []
            templates = [
                '在时光的河流中',
                '寻找那失去的梦',
                '回忆如风般掠过',
                '留下淡淡的痕迹',
                '心中的那份执着',
                '永远不会改变',
                '即使前路漫漫',
                '也要勇敢前行',
                '相信明天会更好',
                '阳光总会到来',
                '在黑暗中寻找',
                '那一束光明',
                '让希望指引方向',
                '让梦想照亮前路',
                '无论多么艰难',
                '都要坚持到底'
            ]
            for i in range(length):
                lines.append(templates[i % len(templates)])
            return "\n".join(lines)

