"""
生成API路由
"""
from flask import Blueprint, request, jsonify
from app.services.generation_service import GenerationService

bp = Blueprint('generation', __name__)
service = GenerationService()


@bp.route('/by-theme', methods=['POST'])
def generate_by_theme():
    """根据主题生成"""
    data = request.get_json()
    theme = data.get('theme', '爱情')
    emotion = data.get('emotion')  # 可选
    length = data.get('length')  # 可选，如果不提供则不限制长度
    user_idea = data.get('user_idea')  # 用户想法（可能包含歌名）
    user_id = data.get('user_id')
    
    try:
        result = service.generate_by_theme(theme, emotion, length, user_idea, user_id)
        return jsonify({'success': True, 'data': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/by-context', methods=['POST'])
def generate_by_context():
    """基于上下文生成（生成更完整的歌词）"""
    data = request.get_json()
    previous_lines = data.get('previous_lines', [])
    emotion = data.get('emotion')  # 可选
    length = data.get('length')  # 可选，如果不提供则不限制长度（总行数，包含上下文）
    theme = data.get('theme')  # 可选
    style = data.get('style')  # 可选
    user_idea = data.get('user_idea')  # 可选
    user_id = data.get('user_id')
    
    try:
        result = service.generate_by_context(
            previous_lines, 
            emotion, 
            length, 
            theme,
            style,
            user_idea,
            user_id
        )
        return jsonify({'success': True, 'data': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/full-song', methods=['POST'])
def generate_full_song():
    """生成完整歌曲"""
    data = request.get_json()
    style = data.get('style', '流行')
    theme = data.get('theme', '爱情')
    emotion = data.get('emotion')  # 可选
    user_idea = data.get('user_idea')  # 用户想法描述
    length = data.get('length')  # 可选，如果不提供则不限制长度
    user_id = data.get('user_id')
    
    try:
        result = service.generate_full_song(style, theme, emotion, user_idea, length, user_id)
        return jsonify({'success': True, 'data': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/convert-style', methods=['POST'])
def convert_style():
    """风格转换"""
    data = request.get_json()
    lyrics = data.get('lyrics', '')
    target_style = data.get('target_style', '流行')
    user_id = data.get('user_id')
    
    if not lyrics:
        return jsonify({'error': '歌词不能为空'}), 400
    
    try:
        result = service.convert_style(lyrics, target_style, user_id)
        return jsonify({'success': True, 'data': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/continue', methods=['POST'])
def continue_conversation():
    """继续对话，根据用户反馈修改歌词"""
    data = request.get_json()
    previous_lyrics = data.get('previous_lyrics', '')
    user_feedback = data.get('user_feedback', '')
    user_id = data.get('user_id')
    
    if not previous_lyrics or not user_feedback:
        return jsonify({'error': '参数不完整'}), 400
    
    try:
        result = service.continue_conversation(previous_lyrics, user_feedback, user_id)
        return jsonify({'success': True, 'data': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/history', methods=['GET'])
def get_history():
    """获取生成历史"""
    user_id = request.args.get('user_id', type=int)
    limit = request.args.get('limit', 10, type=int)
    
    try:
        histories = service.get_history(user_id, limit)
        return jsonify({'success': True, 'data': histories}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/history/<int:history_id>', methods=['GET'])
def get_history_detail(history_id):
    """获取生成历史详情"""
    try:
        from app.models import GenerationHistory
        from app import db
        
        history = GenerationHistory.query.get(history_id)
        if not history:
            return jsonify({'error': '记录不存在'}), 404
        
        return jsonify({'success': True, 'data': history.to_dict()}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/history/<int:history_id>', methods=['DELETE'])
def delete_history(history_id):
    """删除生成历史"""
    try:
        from app.models import GenerationHistory
        from app import db
        
        history = GenerationHistory.query.get(history_id)
        if not history:
            return jsonify({'error': '记录不存在'}), 404
        
        db.session.delete(history)
        db.session.commit()
        return jsonify({'success': True, 'message': '删除成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/song', methods=['POST'])
def generate_song():
    """根据歌词生成歌曲（使用 Suno API）"""
    data = request.get_json()
    lyrics = data.get('lyrics', '')
    title = data.get('title')
    tags = data.get('tags')
    style = data.get('style')
    voice = data.get('voice', 'default')  # 语音选择：male, female, default
    make_instrumental = data.get('make_instrumental', False)
    user_id = data.get('user_id')
    async_mode = data.get('async_mode', True)  # 默认异步模式
    max_wait_time = data.get('max_wait_time', 300)  # 最大等待时间（秒）
    
    if not lyrics:
        return jsonify({'error': '歌词不能为空'}), 400
    
    try:
        result = service.generate_song_from_lyrics(
            lyrics=lyrics,
            title=title,
            tags=tags,
            style=style,
            voice=voice,
            make_instrumental=make_instrumental,
            user_id=user_id,
            async_mode=async_mode,
            max_wait_time=max_wait_time
        )
        return jsonify({'success': True, 'data': result}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/song/status', methods=['GET'])
def query_song_status():
    """查询歌曲生成任务状态"""
    task_id = request.args.get('task_id')
    user_id = request.args.get('user_id')
    
    if not task_id:
        return jsonify({'error': 'task_id 参数不能为空'}), 400
    
    try:
        result = service.query_song_generation_status(task_id)
        
        # 如果任务完成，更新历史记录
        if result.get('status') == 'success' and result.get('clips'):
            clips = result.get('clips', [])
            # 选择最好的音频（优先选择状态为complete且时长最长的）
            completed_clips = [c for c in clips if c.get('status') == 'complete' and c.get('audio_url')]
            if completed_clips:
                best_clip = max(completed_clips, key=lambda x: x.get('duration', 0))
            else:
                best_clip = clips[0] if clips else None
            
            if best_clip and best_clip.get('audio_url'):
                # 查找并更新对应的历史记录
                from app.models import GenerationHistory
                from app import db
                import re
                import json
                
                # 查找历史记录（不限制user_id，因为可能为None）
                history = GenerationHistory.query.filter(
                    GenerationHistory.prompt.like(f'%{task_id}%')
                ).order_by(GenerationHistory.created_at.desc()).first()
                
                if history:
                    # 解析现有数据
                    lyrics_content = history.generated_lyrics or ''
                    json_match = re.search(r'```json\n([\s\S]*?)\n```', lyrics_content)
                    
                    if json_match:
                        try:
                            song_data = json.loads(json_match.group(1))
                            song_data['status'] = 'completed'
                            # 保存所有可用的音频URL（最多3个最好的）
                            completed_clips = [c for c in clips if c.get('status') == 'complete' and c.get('audio_url')]
                            available_clips = completed_clips if completed_clips else [c for c in clips if c.get('audio_url')]
                            available_clips.sort(key=lambda x: x.get('duration', 0), reverse=True)
                            top_clips = available_clips[:3]
                            
                            # 保存最好的音频作为主要音频
                            song_data['audio_url'] = best_clip.get('audio_url')
                            song_data['duration'] = best_clip.get('duration', 0)
                            # 保存所有可用的音频列表
                            song_data['clips'] = [
                                {
                                    'audio_url': c.get('audio_url'),
                                    'duration': c.get('duration', 0),
                                    'status': c.get('status', 'complete')
                                }
                                for c in top_clips
                            ]
                            
                            # 更新markdown内容
                            markdown_text = lyrics_content.split('---')[0].strip()
                            full_content = f"{markdown_text}\n\n---\n\n<!-- JSON数据开始 -->\n```json\n{json.dumps(song_data, ensure_ascii=False, indent=2)}\n```\n<!-- JSON数据结束 -->"
                            history.generated_lyrics = full_content
                            db.session.commit()
                        except Exception as e:
                            print(f"更新历史记录失败: {e}")
        
        return jsonify({'success': True, 'data': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500



