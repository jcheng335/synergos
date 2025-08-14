from flask import Blueprint

admin_bp = Blueprint('admin', __name__)

# Import routes after creating Blueprint to avoid circular imports
from synergos.admin import routes 