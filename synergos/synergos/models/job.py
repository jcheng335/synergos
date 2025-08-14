from sqlalchemy import Column, String, Text, Float, Integer, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from synergos.models.base import BaseModel
from synergos.extensions import db

class Job(BaseModel):
    """Job model representing job postings"""
    __tablename__ = 'jobs'
    
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    location = Column(String(255))
    description = Column(Text)
    job_posting_url = Column(String(512))
    job_posting_text = Column(Text)
    status = Column(String(50), default='open')  # open, filled, cancelled, expired
    
    # Relationships
    requirements = relationship('JobRequirement', back_populates='job', cascade='all, delete-orphan')
    applications = relationship('Application', back_populates='job', cascade='all, delete-orphan')
    interviews = relationship('Interview', back_populates='job', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Job {self.title} at {self.company}>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'company': self.company,
            'location': self.location,
            'description': self.description,
            'job_posting_url': self.job_posting_url,
            'status': self.status,
            'requirements': [req.to_dict() for req in self.requirements],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class JobRequirement(BaseModel):
    """Model for job requirements/responsibilities"""
    __tablename__ = 'job_requirements'
    
    job_id = Column(String(36), ForeignKey('jobs.id'), nullable=False)
    requirement_type = Column(String(50), default='responsibility')  # responsibility, qualification, preferred, etc.
    description = Column(Text, nullable=False)
    is_required = Column(Boolean, default=True)
    priority = Column(Integer, default=0)  # Higher number = higher priority
    
    # Relationships
    job = relationship('Job', back_populates='requirements')
    competencies = relationship('Competency', secondary='requirement_competencies')
    
    def __repr__(self):
        return f"<JobRequirement {self.requirement_type}: {self.description[:30]}...>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'requirement_type': self.requirement_type,
            'description': self.description,
            'is_required': self.is_required,
            'priority': self.priority,
            'competencies': [comp.name for comp in self.competencies]
        }


# Association table for requirements and competencies
requirement_competencies = Table(
    'requirement_competencies',
    BaseModel.metadata,
    Column('requirement_id', String(36), ForeignKey('job_requirements.id')),
    Column('competency_id', String(36), ForeignKey('competencies.id'))
) 