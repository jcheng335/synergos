#!/usr/bin/env python3
"""
Synergos Interview Companion - Entry Point
AI-powered interview tool with real-time transcription, STAR analysis, and question generation
"""

import os
import sys

# Add the app_code directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app_code'))

from app import app

if __name__ == '__main__':
    # Get port from environment or default to 8080
    port = int(os.environ.get('PORT', 8080))
    
    # Run the application
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False
    )