import os
import sys
import logging
import subprocess
import shutil
from pathlib import Path

# Configure logging with file output
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "deployment.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def copy_credentials():
    """Copy real credentials from synergos/env.txt to root env.txt"""
    source = os.path.join("synergos", "env.txt")
    target = "env.txt"
    
    if not os.path.exists(source):
        logger.error(f"Source credentials file {source} not found")
        return False
    
    try:
        shutil.copy2(source, target)
        logger.info(f"Successfully copied credentials from {source} to {target}")
        return True
    except Exception as e:
        logger.error(f"Failed to copy credentials: {str(e)}")
        return False

def setup_environment():
    """Set environment variables from env.txt"""
    try:
        with open("env.txt", "r") as f:
            for line in f:
                if "=" in line and not line.strip().startswith("#"):
                    key, value = line.strip().split("=", 1)
                    os.environ[key] = value
                    # Log key name but not the value for security
                    logger.info(f"Set environment variable: {key}")
        
        # Explicitly set Flask variables
        os.environ["FLASK_ENV"] = "production"
        os.environ["FLASK_DEBUG"] = "0"
        
        return True
    except Exception as e:
        logger.error(f"Failed to set environment variables: {str(e)}")
        return False

def check_requirements():
    """Run check_requirements.py to ensure all dependencies are installed"""
    try:
        logger.info("Checking and installing requirements...")
        result = subprocess.run([sys.executable, "check_requirements.py"], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE,
                               text=True)
        
        if result.returncode != 0:
            logger.error(f"Requirements check failed: {result.stderr}")
            return False
            
        logger.info("Requirements check completed successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to check requirements: {str(e)}")
        return False

def setup_python_path():
    """Setup Python path to include necessary directories"""
    # Add synergos directory to path
    synergos_path = os.path.abspath("synergos")
    if synergos_path not in sys.path:
        sys.path.insert(0, synergos_path)
        logger.info(f"Added {synergos_path} to Python path")
    
    # Add current directory to path
    current_path = os.path.abspath(".")
    if current_path not in sys.path:
        sys.path.insert(0, current_path)
        logger.info(f"Added {current_path} to Python path")
    
    return True

def run_application():
    """Run the application with the correct Python path"""
    try:
        # First check if synergos/app.py exists
        app_path = os.path.join("synergos", "app.py")
        if not os.path.exists(app_path):
            logger.error(f"Application file {app_path} not found")
            
            # Try alternative path
            alt_path = "app.py"
            if os.path.exists(alt_path):
                app_path = alt_path
                logger.info(f"Using alternative application path: {alt_path}")
            else:
                logger.error("Could not find app.py in any expected location")
                return False
        
        logger.info(f"Starting application from {app_path}...")
        os.environ["PYTHONPATH"] = os.pathsep.join(sys.path)
        
        # Use subprocess to run the app with the correct environment
        process = subprocess.run(
            [sys.executable, app_path],
            env=os.environ,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if process.returncode != 0:
            logger.error(f"Application failed to start: {process.stderr}")
            return False
            
        return True
    except Exception as e:
        logger.error(f"Failed to run application: {str(e)}")
        return False

def deploy():
    """Main deployment function"""
    logger.info("Starting deployment with real credentials...")
    
    # Copy credentials
    if not copy_credentials():
        logger.error("Failed to setup credentials. Aborting deployment.")
        return False
    
    # Setup environment variables
    if not setup_environment():
        logger.error("Failed to setup environment variables. Aborting deployment.")
        return False
    
    # Setup Python path
    if not setup_python_path():
        logger.error("Failed to setup Python path. Aborting deployment.")
        return False
    
    # Check requirements
    if not check_requirements():
        logger.warning("Requirements check had issues but continuing...")
    
    # Run the application
    if not run_application():
        logger.error("Failed to start the application. See logs for details.")
        
        # Try running the run_app_production.py script instead
        logger.info("Trying alternative startup method...")
        try:
            subprocess.run([sys.executable, "run_app_production.py"])
            return True
        except Exception as e:
            logger.error(f"Alternative startup method failed: {str(e)}")
            return False
    
    return True

if __name__ == "__main__":
    try:
        success = deploy()
        if success:
            logger.info("Deployment completed successfully")
        else:
            logger.error("Deployment failed")
            sys.exit(1)
    except Exception as e:
        logger.critical(f"Unhandled exception during deployment: {str(e)}")
        sys.exit(1) 