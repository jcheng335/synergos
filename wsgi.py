#!/usr/bin/env python3
"""
WSGI entry point for production deployment
"""

import os
import sys

# Add the synergos directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'synergos'))

from synergos.app import app

# For Gunicorn/production
application = app

if __name__ == "__main__":
    application.run()