from sqlalchemy import Column, String, Text, Boolean
from synergos.models.base import BaseModel
from synergos.extensions import db

class EmailTemplate(BaseModel):
    """Email template model for automated communications"""
    __tablename__ = 'email_templates'
    
    name = Column(String(255), nullable=False, unique=True)
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    template_type = Column(String(50), nullable=False)  # invitation, scheduling, follow-up, rejection, offer
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<EmailTemplate {self.name}>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'subject': self.subject,
            'body': self.body,
            'template_type': self.template_type,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 