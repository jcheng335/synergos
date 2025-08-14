import os
import sys
import subprocess
import json

# Configuration
RENDER_SERVICE_NAME = "synergos-interview-app"
RENDER_YAML_PATH = "render.yaml"

def create_render_yaml():
    """Create the render.yaml file for deployment"""
    render_config = {
        "services": [
            {
                "type": "web",
                "name": RENDER_SERVICE_NAME,
                "env": "python",
                "buildCommand": "pip install -r requirements.txt",
                "startCommand": "gunicorn run_app_production:app",
                "envVars": [
                    {
                        "key": "PYTHON_VERSION",
                        "value": "3.9.0"
                    },
                    {
                        "key": "OPENAI_API_KEY", 
                        "sync": "false"
                    },
                    {
                        "key": "AWS_ACCESS_KEY_ID",
                        "sync": "false"
                    },
                    {
                        "key": "AWS_SECRET_ACCESS_KEY",
                        "sync": "false"
                    },
                    {
                        "key": "AWS_DEFAULT_REGION",
                        "value": "us-east-1"
                    },
                    {
                        "key": "FLASK_ENV",
                        "value": "production"
                    },
                    {
                        "key": "FLASK_DEBUG",
                        "value": "0"
                    },
                    {
                        "key": "MOCK_SERVICES",
                        "value": "false"
                    }
                ]
            }
        ]
    }
    
    with open(RENDER_YAML_PATH, 'w') as f:
        json.dump(render_config, f, indent=2)
    
    print(f"Created {RENDER_YAML_PATH} for Render.com deployment")

def fix_openai_client_issue():
    """Fix the OpenAI client initialization issue"""
    # Create a patch file to fix the OpenAI client initialization
    patch_file = "openai_client_fix.py"
    
    with open(patch_file, 'w') as f:
        f.write("""
# This patch fixes the OpenAI client initialization issue
import os
import openai
from openai import OpenAI

# Get the OpenAI version
openai_version = openai.__version__

# Check if OpenAI version has the 'proxies' issue
try:
    import importlib.metadata
    openai_version = importlib.metadata.version('openai')
    print(f"OpenAI version: {openai_version}")
except:
    pass

# Function to monkey patch the OpenAI client if needed
def get_patched_client(api_key):
    # Handle different versions
    if openai_version.startswith('1.'):
        # New SDK style
        try:
            # Try without proxies keyword
            return OpenAI(api_key=api_key)
        except TypeError as e:
            if 'proxies' in str(e):
                # If error is about proxies, try the older style
                client = OpenAI()
                client.api_key = api_key
                return client
            raise
    else:
        # Old SDK style
        openai.api_key = api_key
        return openai

# To use this in app.py:
# from openai_client_fix import get_patched_client
# client = get_patched_client(openai_api_key)
""")
    
    print(f"Created {patch_file} to fix OpenAI client issues")
    
    # Modify run_app_production.py to use the patch
    try:
        with open('run_app_production.py', 'r') as f:
            content = f.read()
        
        # Add import for the patch
        if 'import openai_client_fix' not in content:
            modified_content = content.replace('import os', 'import os\nimport sys\nsys.path.insert(0, ".")\nimport openai_client_fix')
            
            # Write back the changes
            with open('run_app_production.py', 'w') as f:
                f.write(modified_content)
            
            print("Updated run_app_production.py to use the OpenAI client fix")
    except Exception as e:
        print(f"Error modifying run_app_production.py: {e}")

def create_run_app_wrapper():
    """Create a wrapper for the main app to fix the OpenAI client issue"""
    with open('app_wrapper.py', 'w') as f:
        f.write("""
import os
import sys
from openai_client_fix import get_patched_client

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Get API keys
openai_api_key = os.getenv('OPENAI_API_KEY')
if not openai_api_key:
    print("Error: OpenAI API key not found in environment variables")
    sys.exit(1)

# Create a properly configured OpenAI client
openai_client = get_patched_client(openai_api_key)

# Create global variable to be imported by app.py
import builtins
builtins.OPENAI_CLIENT = openai_client

# Import the app
from synergos.app import app as flask_app

# For Gunicorn
app = flask_app

if __name__ == '__main__':
    # Run the app
    flask_app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
""")
    
    print("Created app_wrapper.py as a wrapper for the Flask application")

def create_gitignore():
    """Create a .gitignore file to exclude unnecessary files"""
    with open('.gitignore', 'w') as f:
        f.write("""
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/

# Environment files
.env
env.txt

# Logs
logs/
*.log

# Temporary files
tmp/
.tmp/
temp/

# IDE files
.vscode/
.idea/
*.swp
*.swo

# Local configuration
local_settings.py
""")
    
    print("Created .gitignore file")

def update_requirements():
    """Update requirements.txt to fix dependencies"""
    try:
        with open('requirements.txt', 'r') as f:
            requirements = f.readlines()
        
        # Replace the OpenAI version
        updated_requirements = []
        for line in requirements:
            if line.startswith('openai=='):
                updated_requirements.append('openai>=1.6.1,<2.0.0\n')
            else:
                updated_requirements.append(line)
        
        # Add gunicorn and other deployment requirements if not already present
        deployment_reqs = ['gunicorn', 'python-dotenv']
        for req in deployment_reqs:
            if not any(line.startswith(f"{req}") for line in updated_requirements):
                updated_requirements.append(f"{req}\n")
        
        with open('requirements.txt', 'w') as f:
            f.writelines(updated_requirements)
        
        print("Updated requirements.txt")
    except Exception as e:
        print(f"Error updating requirements.txt: {e}")

def create_procfile():
    """Create a Procfile for web servers"""
    with open('Procfile', 'w') as f:
        f.write("web: gunicorn app_wrapper:app")
    
    print("Created Procfile")

def display_deploy_instructions():
    """Display instructions for deploying to Render.com"""
    print("\n" + "="*60)
    print("DEPLOYMENT INSTRUCTIONS")
    print("="*60)
    print("\n1. Create a free account on Render.com")
    print("2. Install the Render CLI tool (https://render.com/docs/cli)")
    print("3. Login to Render: render login")
    print("4. Deploy with: render deploy")
    print("\nAlternatively, you can manually deploy:")
    print("1. Create a new Git repository and push this code")
    print("2. On Render.com, create a new Web Service")
    print("3. Connect your Git repository")
    print("4. Set the build command: pip install -r requirements.txt")
    print("5. Set the start command: gunicorn app_wrapper:app")
    print("6. Add the following environment variables:")
    print("   - OPENAI_API_KEY=[your key]")
    print("   - AWS_ACCESS_KEY_ID=[your key]")
    print("   - AWS_SECRET_ACCESS_KEY=[your key]")
    print("   - AWS_DEFAULT_REGION=us-east-1")
    print("   - FLASK_ENV=production")
    print("   - FLASK_DEBUG=0")
    print("\nNote: You can use the render.yaml file for faster deployment")
    print("="*60)

def main():
    """Main function to prepare the app for deployment"""
    print("Preparing Synergos application for deployment...")
    
    # Fix OpenAI client issue
    fix_openai_client_issue()
    
    # Create app wrapper
    create_run_app_wrapper()
    
    # Update requirements
    update_requirements()
    
    # Create gitignore
    create_gitignore()
    
    # Create Procfile
    create_procfile()
    
    # Create render.yaml
    create_render_yaml()
    
    # Display deployment instructions
    display_deploy_instructions()
    
    print("\nDeployment preparation completed!")

if __name__ == "__main__":
    main() 