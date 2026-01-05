"""
用户API路由
"""
from flask import Blueprint, request, jsonify
from app.models import User
from app import db

bp = Blueprint('user', __name__)


@bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    
    if not username:
        return jsonify({'error': '用户名不能为空'}), 400
    
    try:
        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            return jsonify({'error': '用户名已存在'}), 400
        
        user = User(username=username, email=email)
        db.session.add(user)
        db.session.commit()
        
        return jsonify({'success': True, 'data': user.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """获取用户信息"""
    try:
        user = User.query.get_or_404(user_id)
        return jsonify({'success': True, 'data': user.to_dict()}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:user_id>/stats', methods=['GET'])
def get_user_stats(user_id):
    """获取用户统计信息"""
    try:
        user = User.query.get_or_404(user_id)
        
        stats = {
            'total_analyses': len(user.analyses),
            'total_generations': len(user.generations),
            'total_recommendations': len(user.recommendations),
            'preferences': user.preferences
        }
        
        return jsonify({'success': True, 'data': stats}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500







