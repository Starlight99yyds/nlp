"""
分析API路由
"""
from flask import Blueprint, request, jsonify
from app.services.analysis_service import AnalysisService

bp = Blueprint('analysis', __name__)
service = AnalysisService()


@bp.route('/analyze', methods=['POST'])
def analyze():
    """分析歌词"""
    data = request.get_json()
    lyrics = data.get('lyrics', '')
    user_id = data.get('user_id')
    
    if not lyrics:
        return jsonify({'error': '歌词不能为空'}), 400
    
    try:
        result = service.analyze_lyrics(lyrics, user_id)
        return jsonify({'success': True, 'data': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/history', methods=['GET'])
def get_history():
    """获取分析历史"""
    user_id = request.args.get('user_id', type=int)
    limit = request.args.get('limit', 10, type=int)
    
    try:
        histories = service.get_history(user_id, limit)
        return jsonify({'success': True, 'data': histories}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/history/<int:history_id>', methods=['GET'])
def get_history_detail(history_id):
    """获取分析历史详情"""
    try:
        from app.models import AnalysisHistory
        from app import db
        
        history = AnalysisHistory.query.get(history_id)
        if not history:
            return jsonify({'error': '记录不存在'}), 404
        
        return jsonify({'success': True, 'data': history.to_dict()}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/history/<int:history_id>', methods=['DELETE'])
def delete_history(history_id):
    """删除分析历史"""
    try:
        from app.models import AnalysisHistory
        from app import db
        
        history = AnalysisHistory.query.get(history_id)
        if not history:
            return jsonify({'error': '记录不存在'}), 404
        
        db.session.delete(history)
        db.session.commit()
        return jsonify({'success': True, 'message': '删除成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/sentiment', methods=['POST'])
def analyze_sentiment():
    """单独分析情感"""
    data = request.get_json()
    lyrics = data.get('lyrics', '')
    
    if not lyrics:
        return jsonify({'error': '歌词不能为空'}), 400
    
    try:
        result = service.sentiment_analyzer.analyze_lyrics(lyrics)
        return jsonify({'success': True, 'data': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/theme', methods=['POST'])
def analyze_theme():
    """单独分析主题"""
    data = request.get_json()
    lyrics = data.get('lyrics', '')
    
    if not lyrics:
        return jsonify({'error': '歌词不能为空'}), 400
    
    try:
        result = service.theme_extractor.analyze_theme(lyrics)
        return jsonify({'success': True, 'data': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/rhythm', methods=['POST'])
def analyze_rhythm():
    """单独分析韵律"""
    data = request.get_json()
    lyrics = data.get('lyrics', '')
    
    if not lyrics:
        return jsonify({'error': '歌词不能为空'}), 400
    
    try:
        result = service.rhythm_analyzer.analyze_rhythm(lyrics)
        return jsonify({'success': True, 'data': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500



