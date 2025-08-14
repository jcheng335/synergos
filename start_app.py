import os
import sys
import logging
import subprocess
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def run_script(script_path):
    """Run a Python script and check if it executed successfully"""
    logger.info(f"Running {script_path}...")
    try:
        result = subprocess.run([sys.executable, script_path], check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running {script_path}: {str(e)}")
        return False

def create_env_file_if_needed():
    """Create env.txt file if it doesn't exist"""
    env_path = Path("env.txt")
    if not env_path.exists():
        logger.info("Creating env.txt file with placeholder values")
        with open(env_path, "w") as f:
            f.write("OPENAI_API_KEY=your_openai_api_key_here\n")
            f.write("AWS_ACCESS_KEY_ID=your_aws_access_key_here\n")
            f.write("AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here\n")
            f.write("AWS_DEFAULT_REGION=us-east-1\n")
        logger.info("Please edit env.txt with your actual API keys")
        return False
    return True

def setup_folders():
    """Create necessary folders if they don't exist"""
    folders = ["logs", "tmp"]
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
            logger.info(f"Created {folder} directory")

def main():
    """Main function to start the application"""
    logger.info("Starting SYNERGOS application setup...")
    
    # Create necessary folders
    setup_folders()
    
    # Check if env.txt exists and create if needed
    if not create_env_file_if_needed():
        logger.warning("Please edit env.txt with your actual API keys and run this script again.")
        return
    
    # Check requirements
    if not run_script("check_requirements.py"):
        logger.error("Failed to install required packages. Exiting.")
        return
    
    # Set up DynamoDB tables
    if not run_script("setup_dynamodb.py"):
        logger.warning("DynamoDB setup had issues. The app may still work with limited functionality.")
    
    # Set PORT environment variable to 8080
    os.environ['PORT'] = '8080'
    logger.info("Setting application to run on port 8080")
    
    # Start the app
    logger.info("Starting the application...")
    app_path = os.path.join("synergos", "app.py")
    subprocess.run([sys.executable, app_path])

if __name__ == "__main__":
    main() 