#!/usr/bin/env python3
import os
import sys
import subprocess

print("=== Debugging Railway Deployment ===")
print(f"Current directory: {os.getcwd()}")
print(f"Directory contents: {os.listdir('.')}")

# Check for synergos directory
if os.path.exists('synergos'):
    print(f"synergos/ found with contents: {os.listdir('synergos')}")
    
    # Add synergos to path
    sys.path.insert(0, 'synergos')
    
    # Try to import and run
    try:
        from synergos.app import app
        print("Successfully imported app from synergos")
        
        # Run gunicorn
        port = os.environ.get('PORT', '8080')
        cmd = f"gunicorn --bind 0.0.0.0:{port} --chdir synergos wsgi:application"
        print(f"Running: {cmd}")
        subprocess.run(cmd.split())
    except ImportError as e:
        print(f"Import error: {e}")
        sys.exit(1)
else:
    print("ERROR: synergos/ directory not found!")
    print("Available files/dirs:", os.listdir('.'))
    sys.exit(1)