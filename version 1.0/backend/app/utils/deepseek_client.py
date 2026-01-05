"""
DeepSeek API客户端
用于高级歌词生成和优化
"""
import requests
import json
import os
from typing import List, Dict, Optional

class DeepSeekClient:
    """DeepSeek API客户端"""
    
    def __init__(self, api_key: str = None, api_url: str = None):
        self.api_key = api_key or os.environ.get('DEEPSEEK_API_KEY', '')
        self.api_url = api_url or os.environ.get('DEEPSEEK_API_URL', 'https://api.deepseek.com/v1/chat/completions')
    
    def generate_lyrics(self, prompt: str, style: str = None, theme: str = None, 
                       emotion: str = None, length: int = 16, 
                       context: List[str] = None, user_idea: str = None) -> str:
        """生成歌词"""
        if not self.api_key:
            return self._fallback_generate(prompt, style, theme, emotion, length)
        
        messages = self._build_messages(prompt, style, theme, emotion, length, context, user_idea)
        
        try:
            response = requests.post(
                self.api_url,
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'deepseek-chat',
                    'messages': messages,
                    'temperature': 0.8,
                    'max_tokens': 2000
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                lyrics = result['choices'][0]['message']['content']
                return lyrics.strip()
            else:
                print(f"DeepSeek API错误: {response.status_code}, {response.text}")
                return self._fallback_generate(prompt, style, theme, emotion, length)
        except Exception as e:
            print(f"DeepSeek API调用失败: {e}")
            return self._fallback_generate(prompt, style, theme, emotion, length)
    
    def convert_style(self, lyrics: str, target_style: str) -> str:
        """风格转换（整体转换，不是简单加词）"""
        if not self.api_key:
            return lyrics  # 如果没配置API，返回原歌词
        
        prompt = f"""请将以下歌词整体转换为{target_style}风格。要求：
1. 保持原歌词的核心意思和情感
2. 改变表达方式、用词、句式结构，使其符合{target_style}风格的特点
3. 保持歌词的完整性和连贯性
4. 不要只是在原歌词后面加词，而是整体改写

原歌词：
{lyrics}

请直接输出转换后的完整歌词，不要添加任何解释或标记。"""
        
        try:
            response = requests.post(
                self.api_url,
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'deepseek-chat',
                    'messages': [
                        {'role': 'system', 'content': '你是一位专业的歌词创作和风格转换专家。'},
                        {'role': 'user', 'content': prompt}
                    ],
                    'temperature': 0.7,
                    'max_tokens': 2000
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                converted = result['choices'][0]['message']['content']
                return converted.strip()
            else:
                return lyrics
        except Exception as e:
            print(f"风格转换失败: {e}")
            return lyrics
    
    def continue_conversation(self, previous_lyrics: str, user_feedback: str) -> str:
        """继续对话，根据用户反馈修改歌词"""
        if not self.api_key:
            return previous_lyrics
        
        prompt = f"""以下是之前生成的歌词：

{previous_lyrics}

用户反馈：{user_feedback}

请根据用户的反馈，对歌词进行修改和完善。直接输出修改后的完整歌词，不要添加解释。"""
        
        try:
            response = requests.post(
                self.api_url,
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'deepseek-chat',
                    'messages': [
                        {'role': 'system', 'content': '你是一位专业的歌词创作专家，擅长根据用户反馈优化歌词。'},
                        {'role': 'user', 'content': prompt}
                    ],
                    'temperature': 0.8,
                    'max_tokens': 2000
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                improved = result['choices'][0]['message']['content']
                return improved.strip()
            else:
                return previous_lyrics
        except Exception as e:
            print(f"对话继续失败: {e}")
            return previous_lyrics
    
    def _build_messages(self, prompt: str, style: str, theme: str, emotion: str, 
                       length: int, context: List[str], user_idea: str) -> List[Dict]:
        """构建消息列表"""
        system_prompt = "你是一位专业的歌词创作专家，擅长创作各种风格和主题的歌词。"
        
        user_prompt = "请创作一首歌词，要求如下：\n"
        
        if user_idea:
            user_prompt += f"用户想法：{user_idea}\n"
        
        if theme:
            user_prompt += f"主题：{theme}\n"
        
        if style:
            user_prompt += f"风格：{style}\n"
        
        if emotion:
            user_prompt += f"情感基调：{emotion}\n"
        
        if context:
            user_prompt += f"\n上下文（前文）：\n" + "\n".join(context) + "\n"
            user_prompt += "请基于上下文继续创作，保持连贯性。\n"
        
        user_prompt += f"长度：约{length}行\n"
        user_prompt += "\n请直接输出歌词内容，每行一句，不要添加任何解释或标记。"
        
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

