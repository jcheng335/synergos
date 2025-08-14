import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import logging

from synergos.extensions import db, migrate, celery_app
from synergos.api import api_bp
from synergos.admin import admin_bp
from synergos.nova_integration import nova_bp
from synergos.config import config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app(config_name=None):
    """Application factory function to create and configure Flask app"""
    # Load environment variables
    load_dotenv()

    # Create and configure app
    app = Flask(__name__, template_folder="../templates")
    
    # Determine configuration to use
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    # Apply configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    CORS(app, resources={r"/*": {"origins": "*"}})
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Register blueprints
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(nova_bp, url_prefix='/nova')
    
    # Initialize Celery
    celery_app.conf.update(app.config)
    
    # Create tables if they don't exist (for dev only)
    if config_name == 'development':
        with app.app_context():
            db.create_all()
    
    # Log application startup
    logger.info(f"Application started with {config_name} configuration")
    
    return app 