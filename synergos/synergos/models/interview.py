from sqlalchemy import Column, String, Text, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from synergos.models.base import BaseModel
from synergos.extensions import db

class Interview(BaseModel):
    """Interview model for tracking interviews"""
    __tablename__ = 'interviews'
    
    candidate_id = Column(String(36), ForeignKey('candidates.id'), nullable=False)
    job_id = Column(String(36), ForeignKey('jobs.id'), nullable=False)
    
    interview_type = Column(String(50), default='initial')  # initial, technical, behavioral, final
    scheduled_time = Column(DateTime)
    completed_time = Column(DateTime)
    duration_minutes = Column(Float)
    notes = Column(Text)
    recording_url = Column(String(512))
    transcript = Column(Text)
    status = Column(String(50), default='scheduled')  # scheduled, completed, cancelled, no-show
    
    # Overall scores
    technical_score = Column(Float)
    communication_score = Column(Float)
    culture_fit_score = Column(Float)
    overall_score = Column(Float)
    
    # Feedback
    interviewer_feedback = Column(Text)
    recommendation = Column(String(50))  # proceed, reject, consider
    
    # Relationships
    candidate = relationship('Candidate', back_populates='interviews')
    job = relationship('Job', back_populates='interviews')
    questions = relationship('InterviewQuestion', back_populates='interview', cascade='all, delete-orphan')
    responses = relationship('InterviewResponse', back_populates='interview', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Interview {self.interview_type} for {self.candidate_id} - {self.job_id}>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'candidate_id': self.candidate_id,
            'job_id': self.job_id,
            'interview_type': self.interview_type,
            'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
            'completed_time': self.completed_time.isoformat() if self.completed_time else None,
            'duration_minutes': self.duration_minutes,
            'status': self.status,
            'technical_score': self.technical_score,
            'communication_score': self.communication_score,
            'culture_fit_score': self.culture_fit_score,
            'overall_score': self.overall_score,
            'recommendation': self.recommendation,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class InterviewQuestion(BaseModel):
    """Model for questions asked during an interview"""
    __tablename__ = 'interview_questions'
    
    interview_id = Column(String(36), ForeignKey('interviews.id'), nullable=False)
    question_id = Column(String(36), ForeignKey('questions.id'))
    text = Column(Text, nullable=False)
    asked_at = Column(DateTime)
    asked_by = Column(String(255), default='interviewer')  # interviewer, system
    is_follow_up = Column(Boolean, default=False)
    parent_question_id = Column(String(36), ForeignKey('interview_questions.id'))
    
    # Relationships
    interview = relationship('Interview', back_populates='questions')
    question = relationship('Question')
    responses = relationship('InterviewResponse', back_populates='question', cascade='all, delete-orphan')
    follow_ups = relationship('InterviewQuestion', 
                             backref=db.backref('parent_question', remote_side=[id]),
                             cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<InterviewQuestion {self.text[:30]}...>"


class InterviewResponse(BaseModel):
    """Model for responses to interview questions"""
    __tablename__ = 'interview_responses'
    
    interview_id = Column(String(36), ForeignKey('interviews.id'), nullable=False)
    question_id = Column(String(36), ForeignKey('interview_questions.id'), nullable=False)
    text = Column(Text)
    response_start = Column(DateTime)
    response_end = Column(DateTime)
    
    # STAR analysis components
    situation = Column(Text)
    task = Column(Text)
    action = Column(Text)
    result = Column(Text)
    
    # Scores
    clarity_score = Column(Float)
    relevance_score = Column(Float)
    completeness_score = Column(Float)
    overall_score = Column(Float)
    
    # Relationships
    interview = relationship('Interview', back_populates='responses')
    question = relationship('InterviewQuestion', back_populates='responses')
    competencies = relationship('Competency', secondary='response_competencies')
    
    def __repr__(self):
        return f"<InterviewResponse for question {self.question_id}>"


# Association table for responses and competencies
response_competencies = db.Table(
    'response_competencies',
    BaseModel.metadata,
    Column('response_id', String(36), ForeignKey('interview_responses.id')),
    Column('competency_id', String(36), ForeignKey('competencies.id'))
) 