#!/usr/bin/env python3
"""
WSGI entry point for production deployment
"""

import os
import sys

# Add the app_code directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app_code'))

from app import app

# For Gunicorn/production
application = app

if __name__ == "__main__":
    application.run()