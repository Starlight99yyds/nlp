from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv

# 加载环境变量（从.env文件或系统环境变量）
load_dotenv()

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    # 配置
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # 数据库路径配置
    base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    db_path = os.path.join(base_dir, '..', 'data', 'database.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL', 
        f'sqlite:///{db_path}'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # 优化数据库连接池配置（SQLite 使用 NullPool，其他数据库使用连接池）
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,  # 连接前检查连接是否有效
        'pool_recycle': 3600,   # 连接回收时间（秒）
        'connect_args': {'check_same_thread': False} if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI'] else {}
    }
    
    # 初始化扩展
    CORS(app)
    db.init_app(app)
    
    # 注册蓝图
    from app.api import analysis, generation, recommendation, user
    app.register_blueprint(analysis.bp, url_prefix='/api/analysis')
    app.register_blueprint(generation.bp, url_prefix='/api/generation')
    app.register_blueprint(recommendation.bp, url_prefix='/api/recommendation')
    app.register_blueprint(user.bp, url_prefix='/api/user')
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
    
    return app

