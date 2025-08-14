from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from celery import Celery

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

# Configure Celery
celery_app = Celery(
    'synergos',
    broker='redis://redis:6379/0',
    backend='redis://redis:6379/0',
    include=['synergos.tasks.resume_analysis', 
             'synergos.tasks.job_analysis',
             'synergos.tasks.interview_analysis',
             'synergos.tasks.email_generation']
) 