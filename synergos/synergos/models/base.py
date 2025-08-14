from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime
from synergos.extensions import db

class BaseModel(db.Model):
    """Base model class for inheritance"""
    __abstract__ = True
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def save(self):
        """Save model to database"""
        db.session.add(self)
        db.session.commit()
        return self
    
    def delete(self):
        """Delete model from database"""
        db.session.delete(self)
        db.session.commit()
        return self
    
    @classmethod
    def get_by_id(cls, id):
        """Get model by ID"""
        return cls.query.filter_by(id=id).first()
    
    @classmethod
    def get_all(cls):
        """Get all models"""
        return cls.query.all() 