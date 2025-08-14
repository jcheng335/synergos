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

def setup_env_variables():
    """Load environment variables from env.txt"""
    env_path = Path("env.txt")
    if not env_path.exists():
        logger.error("env.txt file not found. Please create an env.txt file with your API keys.")
        return False
    
    try:
        with open(env_path, "r") as f:
            for line in f:
                if line.strip() and "=" in line:
                    key, value = line.strip().split("=", 1)
                    if "your_" in value or value == "" or "sk-1234" in value:
                        logger.warning(f"⚠️ {key} contains placeholder value. Please update with real credentials.")
                    os.environ[key] = value
        return True
    except Exception as e:
        logger.error(f"Failed to load environment variables: {str(e)}")
        return False

def check_api_keys():
    """Check if required API keys are set properly"""
    required_keys = [
        "OPENAI_API_KEY", 
        "AWS_ACCESS_KEY_ID", 
        "AWS_SECRET_ACCESS_KEY", 
        "AWS_DEFAULT_REGION", 
        "AZURE_SPEECH_KEY", 
        "AZURE_SPEECH_REGION"
    ]
    
    missing = []
    for key in required_keys:
        if key not in os.environ or "your_" in os.environ[key] or os.environ[key] == "":
            missing.append(key)
    
    if missing:
        logger.error(f"Missing or invalid API keys: {', '.join(missing)}")
        logger.error("Please update env.txt with correct values")
        return False
    
    return True

def setup_folders():
    """Create necessary folders if they don't exist"""
    folders = ["logs", "tmp"]
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
            logger.info(f"Created {folder} directory")

def setup_dynamodb(skip_on_error=True):
    """Set up DynamoDB tables"""
    result = run_script("setup_dynamodb.py")
    if not result and not skip_on_error:
        return False
    return True

def deploy_local():
    """Deploy the application locally"""
    # Set up environment
    if not setup_env_variables():
        logger.error("Failed to set up environment variables")
        return
    
    # Create necessary folders
    setup_folders()
    
    # Check requirements
    if not run_script("check_requirements.py"):
        logger.error("Failed to install required packages. Exiting.")
        return
    
    # Check API keys
    if not check_api_keys():
        logger.warning("⚠️ Continuing with placeholder API keys. Some features may not work.")
    
    # Set up DynamoDB tables
    if not setup_dynamodb(skip_on_error=True):
        logger.warning("DynamoDB setup failed. Some features may not work.")
    
    # Explicitly disable Flask debugger
    os.environ['FLASK_DEBUG'] = '0'
    os.environ['FLASK_ENV'] = 'production'
    
    # Run the application using production runner
    logger.info("Starting the application in production mode...")
    try:
        subprocess.run([sys.executable, "run_app_production.py"])
    except Exception as e:
        logger.error(f"Error starting the application: {str(e)}")

def deploy_docker():
    """Deploy using Docker Compose"""
    if not os.path.exists(os.path.join("synergos", "docker-compose.yml")):
        logger.error("docker-compose.yml not found in synergos directory")
        return
    
    # Set up environment
    if not setup_env_variables():
        logger.error("Failed to set up environment variables")
        return
    
    # Run docker-compose
    try:
        os.chdir("synergos")
        logger.info("Building Docker containers...")
        subprocess.run(["docker-compose", "build"], check=True)
        
        logger.info("Starting Docker containers...")
        subprocess.run(["docker-compose", "up", "-d"], check=True)
        
        logger.info("Application is now running in Docker containers")
        logger.info("Access the application at http://localhost:5000")
        logger.info("To stop: docker-compose down")
    except subprocess.CalledProcessError as e:
        logger.error(f"Docker deployment failed: {str(e)}")
    except FileNotFoundError:
        logger.error("Docker or docker-compose not installed. Please install Docker Desktop.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--docker":
        deploy_docker()
    else:
        deploy_local() 