from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from synergos.models.base import BaseModel
from synergos.extensions import db

class Competency(BaseModel):
    """Competency model for skills and traits"""
    __tablename__ = 'competencies'
    
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    category = Column(String(50))  # technical, soft skill, leadership, etc.
    
    # Relationships
    keywords = relationship('CompetencyKeyword', back_populates='competency', cascade='all, delete-orphan')
    questions = relationship('Question', back_populates='competency')
    
    def __repr__(self):
        return f"<Competency {self.name}>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'keywords': [kw.keyword for kw in self.keywords],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class CompetencyKeyword(BaseModel):
    """Keywords associated with competencies for matching"""
    __tablename__ = 'competency_keywords'
    
    competency_id = Column(String(36), ForeignKey('competencies.id'), nullable=False)
    keyword = Column(String(255), nullable=False)
    
    # Relationships
    competency = relationship('Competency', back_populates='keywords')
    
    def __repr__(self):
        return f"<CompetencyKeyword {self.keyword} for {self.competency_id}>" 