from app import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    preferences = db.Column(db.Text)  # JSON格式存储用户偏好
    
    # 关系
    analyses = db.relationship('AnalysisHistory', backref='user', lazy=True)
    generations = db.relationship('GenerationHistory', backref='user', lazy=True)
    recommendations = db.relationship('RecommendationHistory', backref='user', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'preferences': self.preferences
        }

