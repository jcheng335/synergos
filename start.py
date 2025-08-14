#!/usr/bin/env python3
import os
import sys

print("=== RAILWAY DEBUG ===")
print(f"Current working directory: {os.getcwd()}")
print(f"Files in current directory: {os.listdir('.')}")
print(f"Python path: {sys.path}")

# Check if app_wrapper exists
if os.path.exists('app_wrapper.py'):
    print("✓ app_wrapper.py found")
else:
    print("✗ app_wrapper.py NOT found")

# Check if app_code directory exists
if os.path.exists('app_code'):
    print("✓ app_code directory found")
    print(f"Files in app_code: {os.listdir('app_code')}")
else:
    print("✗ app_code directory NOT found")

# Try to import
try:
    import app_wrapper
    print("✓ app_wrapper module imported successfully")
    print(f"app_wrapper has app: {hasattr(app_wrapper, 'app')}")
    print(f"app_wrapper has application: {hasattr(app_wrapper, 'application')}")
except Exception as e:
    print(f"✗ Failed to import app_wrapper: {e}")

print("=== END DEBUG ===")

# Now try to start the actual app
if __name__ == "__main__":
    try:
        from app_wrapper import application
        import gunicorn.app.wsgiapp
        
        # Start gunicorn programmatically
        sys.argv = ['gunicorn', '--bind', f'0.0.0.0:{os.environ.get("PORT", 8080)}', 'app_wrapper:application']
        gunicorn.app.wsgiapp.run()
    except Exception as e:
        print(f"Failed to start app: {e}")
        sys.exit(1)