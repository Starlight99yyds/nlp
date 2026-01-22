from app import db
from datetime import datetime

class AnalysisHistory(db.Model):
    __tablename__ = 'analysis_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    lyrics = db.Column(db.Text, nullable=False)
    sentiment_result = db.Column(db.Text)  # JSON格式
    theme_result = db.Column(db.Text)  # JSON格式
    rhythm_result = db.Column(db.Text)  # JSON格式
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'lyrics': self.lyrics,
            'sentiment_result': self.sentiment_result,
            'theme_result': self.theme_result,
            'rhythm_result': self.rhythm_result,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class GenerationHistory(db.Model):
    __tablename__ = 'generation_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    prompt = db.Column(db.Text, nullable=False)
    generated_lyrics = db.Column(db.Text, nullable=False)
    style = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'prompt': self.prompt,
            'generated_lyrics': self.generated_lyrics,
            'style': self.style,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class RecommendationHistory(db.Model):
    __tablename__ = 'recommendation_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    query_lyrics = db.Column(db.Text)
    recommendations = db.Column(db.Text)  # JSON格式
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'query_lyrics': self.query_lyrics,
            'recommendations': self.recommendations,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

