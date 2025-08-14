from sqlalchemy import Column, String, Text, Float, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from synergos.models.base import BaseModel
from synergos.extensions import db

class Candidate(BaseModel):
    """Candidate model for job applicants"""
    __tablename__ = 'candidates'
    
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    phone = Column(String(50))
    resume_text = Column(Text)
    resume_file_path = Column(String(512))
    linkedin_url = Column(String(255))
    github_url = Column(String(255))
    portfolio_url = Column(String(255))
    notes = Column(Text)
    
    # Relationships
    interviews = relationship('Interview', back_populates='candidate', cascade='all, delete-orphan')
    applications = relationship('Application', back_populates='candidate', cascade='all, delete-orphan')
    
    # Scores from analysis
    technical_score = Column(Float, default=0.0)
    communication_score = Column(Float, default=0.0)
    cultural_fit_score = Column(Float, default=0.0)
    overall_score = Column(Float, default=0.0)
    
    # Status
    status = Column(String(50), default='new')  # new, contacted, interviewing, offered, hired, rejected
    
    def __repr__(self):
        return f"<Candidate {self.name} ({self.email})>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'linkedin_url': self.linkedin_url,
            'github_url': self.github_url,
            'portfolio_url': self.portfolio_url,
            'technical_score': self.technical_score,
            'communication_score': self.communication_score,
            'cultural_fit_score': self.cultural_fit_score,
            'overall_score': self.overall_score,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Application(BaseModel):
    """Model for job applications (candidate applying to a job)"""
    __tablename__ = 'applications'
    
    candidate_id = Column(String(36), ForeignKey('candidates.id'), nullable=False)
    job_id = Column(String(36), ForeignKey('jobs.id'), nullable=False)
    
    status = Column(String(50), default='applied')  # applied, screening, interviewing, offered, hired, rejected
    match_score = Column(Float, default=0.0)
    
    # Relationships
    candidate = relationship('Candidate', back_populates='applications')
    job = relationship('Job', back_populates='applications')
    
    def __repr__(self):
        return f"<Application {self.candidate_id} for {self.job_id}>" 