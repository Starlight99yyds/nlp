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


@bp.route('/refresh-music-url', methods=['POST'])
def refresh_music_url():
    """刷新音乐播放URL"""
    data = request.get_json()
    songmid = data.get('songmid')
    platform = data.get('platform', 'qq')
    quality = data.get('quality', '128')
    
    print(f"刷新播放URL请求: songmid={songmid}, platform={platform}, quality={quality}")
    
    if not songmid:
        print("错误: songmid为空")
        return jsonify({'error': 'songmid不能为空'}), 400
    
    try:
        if platform == 'qq':
            from app.utils.qq_music_api import QQMusicAPI
            qq_api = QQMusicAPI()
            print(f"开始获取QQ音乐播放URL (songmid={songmid})...")
            music_url = qq_api.get_music_url(songmid, quality=quality)
            
            if music_url:
                print(f"成功获取播放URL: {music_url[:100]}...")
                return jsonify({
                    'success': True,
                    'data': {
                        'music_url': music_url,
                        'songmid': songmid,
                        'platform': platform
                    }
                }), 200
            else:
                print(f"获取播放URL失败: songmid={songmid}")
                return jsonify({'error': '无法获取播放URL，可能是歌曲不存在或需要VIP权限'}), 404
        else:
            print(f"不支持的平台: {platform}")
            return jsonify({'error': f'不支持的平台: {platform}'}), 400
    except Exception as e:
        print(f"刷新URL异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'刷新URL失败: {str(e)}'}), 500


@bp.route('/proxy-music', methods=['GET'])
def proxy_music():
    """代理音乐播放（解决CORS和权限问题）"""
    import requests
    from flask import Response
    
    music_url = request.args.get('url')
    if not music_url:
        return jsonify({'error': 'URL参数不能为空'}), 400
    
    try:
        # 使用正确的请求头访问QQ音乐
        headers = {
            'Referer': 'https://y.qq.com/',
            'Origin': 'https://y.qq.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'identity',  # 不使用压缩，避免问题
            'Connection': 'keep-alive',
            'Range': request.headers.get('Range', '')  # 支持断点续传
        }
        
        print(f"代理请求音乐URL: {music_url[:100]}...")
        
        # 流式传输音频
        response = requests.get(
            music_url,
            headers=headers,
            stream=True,
            timeout=30,
            allow_redirects=True
        )
        
        if response.status_code == 200 or response.status_code == 206:  # 206是部分内容
            # 获取Content-Type
            content_type = response.headers.get('Content-Type', 'audio/mpeg')
            
            # 创建响应，流式传输
            def generate():
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        yield chunk
            
            return Response(
                generate(),
                mimetype=content_type,
                headers={
                    'Content-Type': content_type,
                    'Accept-Ranges': 'bytes',
                    'Cache-Control': 'public, max-age=3600',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
                    'Access-Control-Allow-Headers': 'Range'
                }
            )
        else:
            print(f"代理请求失败: status_code={response.status_code}, url={music_url[:100]}")
            return jsonify({'error': f'无法获取音频，状态码: {response.status_code}'}), response.status_code
            
    except Exception as e:
        print(f"代理音频失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'代理失败: {str(e)}'}), 500


