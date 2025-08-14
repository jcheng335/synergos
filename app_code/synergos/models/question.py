from sqlalchemy import Column, String, Text, Integer, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from synergos.models.base import BaseModel
from synergos.extensions import db

class Question(BaseModel):
    """Question model for interview questions"""
    __tablename__ = 'questions'
    
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50))  # behavioral, technical, intro, preset, etc.
    difficulty = Column(Integer, default=1)  # 1-5 scale
    popularity = Column(Integer, default=0)  # Times this question has been used
    feedback_score = Column(Float, default=0.0)  # Average feedback score
    preset_order = Column(Integer, nullable=True)  # 1 for primary, 2 for secondary preset
    
    competency_id = Column(String(36), ForeignKey('competencies.id'))
    
    # Relationships
    competency = relationship('Competency', back_populates='questions')
    
    def __repr__(self):
        return f"<Question {self.question_text[:30]}...>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'question_text': self.question_text,
            'question_type': self.question_type,
            'difficulty': self.difficulty,
            'popularity': self.popularity,
            'feedback_score': self.feedback_score,
            'preset_order': self.preset_order,
            'competency_id': self.competency_id,
            'competency_name': self.competency.name if self.competency else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 