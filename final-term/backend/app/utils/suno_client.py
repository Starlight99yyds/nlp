"""
Suno API 客户端
用于根据歌词生成歌曲
"""
import os
import requests
import time
from typing import Dict, List, Optional
from enum import Enum


class SunoModel(Enum):
    """Suno 模型版本"""
    CHIRP_BLUEJAY = "chirp-bluejay"
    CHIRP_AUK = "chirp-auk"
    CHIRP_V4_5 = "chirp-v4-5"
    CHIRP_V4 = "chirp-v4"
    CHIRP_V3_5 = "chirp-v3-5"
    CHIRP_V3 = "chirp-v3"


class SunoClient:
    """Suno API 客户端"""
    
    def __init__(self, api_key: str = None, base_url: str = None):
        # 优先使用传入的api_key，否则从环境变量读取
        if api_key:
            self.api_key = api_key
        else:
            # 确保加载环境变量（从.env文件）
            try:
                from dotenv import load_dotenv
                # 尝试从backend目录加载.env文件
                import sys
                backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                env_path = os.path.join(backend_dir, '.env')
                load_dotenv(dotenv_path=env_path, override=False)  # 不覆盖已存在的环境变量
                load_dotenv()  # 也尝试从当前目录加载
            except ImportError:
                pass  # dotenv可能未安装，继续使用系统环境变量
            except Exception:
                pass  # 如果.env文件不存在，继续使用系统环境变量
            
            # 从环境变量读取（支持系统环境变量和.env文件）
            # 尝试多种方式读取，处理可能的编码问题（如BOM字符）
            self.api_key = os.environ.get('SUNO_API_KEY', '')
            
            # 如果直接读取失败，尝试从所有环境变量中查找（处理BOM等编码问题）
            if not self.api_key:
                for key, value in os.environ.items():
                    # 检查键名（忽略大小写和BOM字符）
                    key_clean = key.strip('\ufeff').strip().upper()
                    if key_clean == 'SUNO_API_KEY' and value:
                        self.api_key = value
                        break
        
        self.base_url = base_url or os.environ.get('SUNO_BASE_URL', 'https://api.defapi.org')
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def generate_music(self, 
                       lyrics: str,
                       title: str = None,
                       tags: str = None,
                       make_instrumental: bool = False,
                       model: SunoModel = SunoModel.CHIRP_V4_5,
                       custom_mode: bool = True,
                       negative_tags: str = None,
                       callback_url: str = None) -> Dict:
        """生成音乐
        
        Args:
            lyrics: 歌词内容（custom_mode=True时必需）
            title: 歌曲标题（custom_mode=True时推荐）
            tags: 风格标签，如 "pop, cheerful, summer"
            make_instrumental: 是否生成纯音乐（无歌词）
            model: 使用的模型版本
            custom_mode: 是否使用自定义模式（True=使用歌词，False=使用描述）
            negative_tags: 要排除的标签
            callback_url: 回调URL（任务完成时通知）
        
        Returns:
            包含 task_id 的字典
        """
        if not self.api_key:
            # 尝试再次从环境变量读取（可能环境变量在初始化后才设置）
            try:
                from dotenv import load_dotenv
                # 尝试从backend目录加载.env文件
                backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                env_path = os.path.join(backend_dir, '.env')
                if os.path.exists(env_path):
                    load_dotenv(dotenv_path=env_path, override=False)
                load_dotenv()  # 也尝试从当前目录加载
            except ImportError:
                pass
            except Exception:
                pass
            
            self.api_key = os.environ.get('SUNO_API_KEY', '')
            if not self.api_key:
                # 提供更详细的错误信息
                error_msg = (
                    "Suno API key is required. Set SUNO_API_KEY environment variable.\n\n"
                    "解决方案：\n"
                    "1. 在backend目录下创建.env文件，添加：SUNO_API_KEY=your_api_key_here\n"
                    "2. 或者在系统环境变量中设置SUNO_API_KEY\n"
                    "3. 设置后请重启后端服务"
                )
                raise ValueError(error_msg)
        
        url = f"{self.base_url}/api/suno/generate"
        
        # 构建请求参数
        params = {
            "mv": model.value,
            "custom_mode": custom_mode,
            "make_instrumental": make_instrumental
        }
        
        if custom_mode:
            if not lyrics:
                raise ValueError("lyrics is required when custom_mode=True")
            params["prompt"] = lyrics
            if title:
                params["title"] = title
            if tags:
                params["tags"] = tags
            if negative_tags:
                params["negative_tags"] = negative_tags
        else:
            # 灵感模式：使用描述而不是歌词
            if not lyrics:
                raise ValueError("lyrics/description is required")
            params["prompt"] = lyrics
        
        if callback_url:
            params["callback_url"] = callback_url
        
        try:
            response = requests.post(url, json=params, headers=self.headers, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            if result.get('code') != 0:
                raise Exception(f"Suno API error: {result.get('message', 'Unknown error')}")
            
            return {
                'task_id': result['data']['task_id'],
                'message': result.get('message', 'ok')
            }
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to call Suno API: {str(e)}")
    
    def query_task(self, task_id: str) -> Dict:
        """查询任务状态
        
        Args:
            task_id: 任务ID
        
        Returns:
            任务状态和结果
        """
        if not self.api_key:
            raise ValueError("Suno API key is required")
        
        url = f"{self.base_url}/api/task/query"
        params = {'task_id': task_id}
        
        try:
            response = requests.get(url, params=params, headers=self.headers, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            if result.get('code') != 0:
                raise Exception(f"Suno API error: {result.get('message', 'Unknown error')}")
            
            # 如果任务完成，直接返回结果数组
            if isinstance(result.get('data'), list):
                return {
                    'status': 'success',
                    'clips': result['data']
                }
            
            # 如果任务进行中，返回状态信息
            data = result.get('data', {})
            return {
                'status': data.get('status', 'unknown'),
                'task_id': data.get('task_id'),
                'clips': data.get('result', []),
                'status_reason': data.get('status_reason', {}),
                'consumed': data.get('consumed', '0'),
                'created_at': data.get('created_at')
            }
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to query Suno task: {str(e)}")
    
    def wait_for_completion(self, task_id: str, max_wait_time: int = 300, 
                           poll_interval: int = 5) -> Dict:
        """等待任务完成
        
        Args:
            task_id: 任务ID
            max_wait_time: 最大等待时间（秒）
            poll_interval: 轮询间隔（秒）
        
        Returns:
            完成的任务结果
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            result = self.query_task(task_id)
            status = result.get('status')
            
            if status == 'success':
                return result
            elif status == 'failed':
                raise Exception(f"Task failed: {result.get('status_reason', 'Unknown error')}")
            elif status == 'in_progress':
                # 移除频繁的print输出，只在必要时输出
                # print(f"Task {task_id} is in progress, waiting...")
                time.sleep(poll_interval)
            else:
                # 移除频繁的print输出
                # print(f"Unknown status: {status}, waiting...")
                time.sleep(poll_interval)
        
        raise TimeoutError(f"Task {task_id} did not complete within {max_wait_time} seconds")
    
    def generate_music_sync(self, 
                           lyrics: str,
                           title: str = None,
                           tags: str = None,
                           make_instrumental: bool = False,
                           model: SunoModel = SunoModel.CHIRP_V4_5,
                           custom_mode: bool = True,
                           negative_tags: str = None,
                           max_wait_time: int = 300) -> Dict:
        """同步生成音乐（等待完成）
        
        Args:
            lyrics: 歌词内容
            title: 歌曲标题
            tags: 风格标签
            make_instrumental: 是否生成纯音乐
            model: 使用的模型版本
            custom_mode: 是否使用自定义模式
            negative_tags: 要排除的标签
            max_wait_time: 最大等待时间（秒）
        
        Returns:
            完成的任务结果，包含生成的音频URL等信息
        """
        # 提交生成任务
        task_result = self.generate_music(
            lyrics=lyrics,
            title=title,
            tags=tags,
            make_instrumental=make_instrumental,
            model=model,
            custom_mode=custom_mode,
            negative_tags=negative_tags
        )
        
        task_id = task_result['task_id']
        
        # 等待任务完成
        result = self.wait_for_completion(task_id, max_wait_time=max_wait_time)
        
        return result

