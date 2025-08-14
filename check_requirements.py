import subprocess
import sys
import pkg_resources
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Define required packages
REQUIRED_PACKAGES = [
    'flask',
    'flask_cors',
    'boto3',
    'openai',
    'python-dotenv',
    'pypdf',
    'requests',
    'bs4'  # BeautifulSoup
]

def check_and_install_packages():
    """Check if required packages are installed and install them if necessary"""
    logger.info("Checking required packages...")
    installed_packages = {pkg.key for pkg in pkg_resources.working_set}
    missing_packages = [pkg for pkg in REQUIRED_PACKAGES if pkg.lower() not in installed_packages]
    
    if missing_packages:
        logger.info(f"Installing missing packages: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_packages)
            logger.info("All required packages installed successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error installing packages: {str(e)}")
            return False
    else:
        logger.info("All required packages are already installed")
    
    return True

if __name__ == "__main__":
    if check_and_install_packages():
        logger.info("Package check completed successfully")
    else:
        logger.error("Failed to install all required packages")
        sys.exit(1) 