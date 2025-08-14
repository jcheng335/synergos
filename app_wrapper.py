#!/usr/bin/env python3
"""
Compatibility wrapper for Railway deployment
This file ensures backward compatibility while we transition to the new structure
"""

import os
import sys

# Add app_code to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app_code'))

# Import the actual Flask app
from app import app

# Export for Gunicorn
application = app

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)