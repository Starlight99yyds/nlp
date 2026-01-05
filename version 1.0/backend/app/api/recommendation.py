"""
推荐API路由
"""
from flask import Blueprint, request, jsonify
from app.services.recommendation_service import RecommendationService

bp = Blueprint('recommendation', __name__)
service = RecommendationService()


@bp.route('/recommend', methods=['POST'])
def recommend():
    """推荐歌曲"""
    data = request.get_json()
    query_lyrics = data.get('lyrics', '')
    top_k = data.get('top_k', 5)
    user_id = data.get('user_id')
    
    if not query_lyrics:
        return jsonify({'error': '歌词不能为空'}), 400
    
    try:
        # 获取用户偏好
        user_preferences = None
        if user_id:
            user_preferences = service.get_user_preferences(user_id)
        
        result = service.recommend(query_lyrics, top_k, user_id, user_preferences)
        return jsonify({'success': True, 'data': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/knowledge-graph', methods=['GET', 'POST'])
def knowledge_graph():
    """构建知识图谱"""
    if request.method == 'POST':
        data = request.get_json()
        songs = data.get('songs', [])
    else:
        songs = None
    
    try:
        graph = service.build_knowledge_graph(songs)
        return jsonify({'success': True, 'data': graph}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/preferences', methods=['GET', 'POST', 'PUT'])
def preferences():
    """用户偏好管理"""
    user_id = request.args.get('user_id') or request.get_json().get('user_id')
    
    if not user_id:
        return jsonify({'error': '用户ID不能为空'}), 400
    
    try:
        if request.method == 'GET':
            prefs = service.get_user_preferences(user_id)
            return jsonify({'success': True, 'data': prefs}), 200
        elif request.method in ['POST', 'PUT']:
            data = request.get_json()
            preferences = data.get('preferences', {})
            service.update_user_preferences(user_id, preferences)
            return jsonify({'success': True, 'message': '偏好已更新'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/history', methods=['GET'])
def get_history():
    """获取推荐历史"""
    user_id = request.args.get('user_id', type=int)
    limit = request.args.get('limit', 10, type=int)
    
    try:
        histories = service.get_history(user_id, limit)
        return jsonify({'success': True, 'data': histories}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/history/<int:history_id>', methods=['GET'])
def get_history_detail(history_id):
    """获取推荐历史详情"""
    try:
        from app.models import RecommendationHistory
        from app import db
        
        history = RecommendationHistory.query.get(history_id)
        if not history:
            return jsonify({'error': '记录不存在'}), 404
        
        return jsonify({'success': True, 'data': history.to_dict()}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/history/<int:history_id>', methods=['DELETE'])
def delete_history(history_id):
    """删除推荐历史"""
    try:
        from app.models import RecommendationHistory
        from app import db
        
        history = RecommendationHistory.query.get(history_id)
        if not history:
            return jsonify({'error': '记录不存在'}), 404
        
        db.session.delete(history)
        db.session.commit()
        return jsonify({'success': True, 'message': '删除成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500



