"""
旋律API路由
歌词+旋律搭配功能
"""
from flask import Blueprint, request, jsonify
import json

bp = Blueprint('melody', __name__)

@bp.route('/generate', methods=['POST'])
def generate_melody():
    """生成旋律建议"""
    data = request.get_json()
    lyrics = data.get('lyrics', '')
    style = data.get('style', '流行')
    
    if not lyrics:
        return jsonify({'error': '歌词不能为空'}), 400
    
    try:
        # 分析歌词的节奏和情感
        lines = [line.strip() for line in lyrics.split('\n') if line.strip()]
        
        # 生成旋律建议（简化版，实际应使用音乐生成模型）
        melody_suggestions = {
            'tempo': '中速（120 BPM）',
            'key': 'C大调',
            'time_signature': '4/4',
            'structure': {
                'intro': '4小节',
                'verse': f'{len(lines) * 2}小节',
                'chorus': '8小节',
                'bridge': '4小节',
                'outro': '4小节'
            },
            'instrumentation': ['钢琴', '吉他', '鼓', '贝斯'],
            'mood': '根据歌词情感自动匹配',
            'suggestions': [
                '建议使用简单的和弦进行，突出歌词内容',
                '副歌部分可以增加和声层次',
                '根据情感变化调整节奏强度'
            ]
        }
        
        return jsonify({'success': True, 'data': melody_suggestions}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/match', methods=['POST'])
def match_melody():
    """匹配现有旋律"""
    data = request.get_json()
    lyrics = data.get('lyrics', '')
    melody_description = data.get('melody_description', '')
    
    if not lyrics:
        return jsonify({'error': '歌词不能为空'}), 400
    
    try:
        # 旋律匹配逻辑（简化版）
        match_result = {
            'compatibility': 0.85,
            'suggestions': [
                '歌词节奏与旋律匹配良好',
                '建议在副歌部分加强旋律的起伏',
                '可以考虑在桥段部分改变调性'
            ],
            'adjustments': {
                'tempo': '保持当前速度',
                'key': '可以尝试转调到G大调',
                'dynamics': '建议在情感高潮处增强音量'
            }
        }
        
        return jsonify({'success': True, 'data': match_result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500





