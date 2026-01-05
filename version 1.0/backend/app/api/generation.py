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
    length = data.get('length', 16)  # 默认16行
    user_id = data.get('user_id')
    
    try:
        result = service.generate_by_theme(theme, emotion, length, user_id)
        return jsonify({'success': True, 'data': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/by-context', methods=['POST'])
def generate_by_context():
    """基于上下文生成（生成更完整的歌词）"""
    data = request.get_json()
    previous_lines = data.get('previous_lines', [])
    emotion = data.get('emotion')  # 可选
    user_id = data.get('user_id')
    
    try:
        result = service.generate_by_context(previous_lines, emotion, user_id)
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
    user_id = data.get('user_id')
    
    try:
        result = service.generate_full_song(style, theme, emotion, user_idea, user_id)
        return jsonify({'success': True, 'data': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/optimize-rhyme', methods=['POST'])
def optimize_rhyme():
    """押韵优化"""
    data = request.get_json()
    line = data.get('line', '')
    target_rhyme = data.get('target_rhyme', '')
    
    if not line or not target_rhyme:
        return jsonify({'error': '参数不完整'}), 400
    
    try:
        result = service.optimize_rhyme(line, target_rhyme)
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



