#!/usr/bin/env python3
import os
import sys

print("Starting test...")
print(f"Current directory: {os.getcwd()}")
print(f"Directory contents: {os.listdir('.')}")
print(f"Python path: {sys.path}")

# Check if synergos directory exists
if os.path.exists('synergos'):
    print("synergos/ directory found")
    print(f"synergos/ contents: {os.listdir('synergos')}")
    
    # Check for app.py
    if os.path.exists('synergos/app.py'):
        print("synergos/app.py found")
    else:
        print("ERROR: synergos/app.py NOT found")
else:
    print("ERROR: synergos/ directory NOT found")

# Try importing
try:
    from synergos.app import app
    print("Successfully imported app")
    print(f"App type: {type(app)}")
except ImportError as e:
    print(f"ERROR importing app: {e}")

print("Test complete")