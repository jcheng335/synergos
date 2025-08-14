from flask import Blueprint

api_bp = Blueprint('api', __name__)

# Import routes after creating Blueprint to avoid circular imports
from synergos.api import resume, job, interview, candidate, workflow, azure, evaluation, emotion_analysis 