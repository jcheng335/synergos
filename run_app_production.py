import os
import sys
sys.path.insert(0, ".")
import openai_client_fix
import sys
import logging
from dotenv import load_dotenv
import importlib.util

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def load_env_variables():
    """Load environment variables from env.txt"""
    try:
        # Check if we're running in mock mode (from environment)
        if os.environ.get('MOCK_SERVICES') == 'true':
            logger.info("Running with MOCK SERVICES enabled - using placeholder credentials")
            return True
            
        # Otherwise, load from env.txt
        load_dotenv('env.txt')
        logger.info("Environment variables loaded from env.txt")
        return True
    except Exception as e:
        logger.error(f"Failed to load environment variables: {str(e)}")
        return False

def mock_services_if_needed():
    """Set up mock services if MOCK_SERVICES is enabled"""
    if os.environ.get('MOCK_SERVICES') == 'true':
        logger.info("Setting up mock services...")
        
        # Create mock competencies.json if it doesn't exist
        if not os.path.exists('competencies.json'):
            try:
                mock_data = {
                    "competencies": [
                        {
                            "name": "Communication",
                            "description": "Ability to convey information clearly",
                            "keywords": ["speak", "communicate", "present", "articulate"]
                        },
                        {
                            "name": "Leadership",
                            "description": "Ability to guide and influence others",
                            "keywords": ["lead", "guide", "direct", "influence"]
                        },
                        {
                            "name": "Problem Solving",
                            "description": "Ability to find solutions to complex issues",
                            "keywords": ["solve", "analyze", "resolve", "solution"]
                        }
                    ]
                }
                with open('competencies.json', 'w') as f:
                    import json
                    json.dump(mock_data, f, indent=2)
                logger.info("Created mock competencies.json file")
            except Exception as e:
                logger.error(f"Failed to create mock competencies.json: {str(e)}")

def run_app():
    """Run the Flask application in production mode"""
    # Force production mode, no debugger
    os.environ['FLASK_DEBUG'] = '0'
    os.environ['FLASK_ENV'] = 'production'
    
    # Set up mock services if needed
    mock_services_if_needed()
    
    # Add synergos directory to Python path to resolve imports
    synergos_dir = os.path.abspath("synergos")
    if synergos_dir not in sys.path:
        sys.path.insert(0, synergos_dir)
        logger.info(f"Added {synergos_dir} to Python path")
    
    # Add the current directory to Python path as well
    current_dir = os.path.abspath(os.getcwd())
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
        logger.info(f"Added {current_dir} to Python path")
    
    # Set the PYTHONPATH environment variable
    os.environ["PYTHONPATH"] = os.pathsep.join(sys.path)
    logger.info(f"PYTHONPATH set to: {os.environ['PYTHONPATH']}")
    
    # Print diagnostic information
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"Python executable: {sys.executable}")
    logger.info(f"Python version: {sys.version}")
    
    # Check module imports early to catch issues
    try:
        logger.info("Testing imports...")
        import flask
        logger.info("Flask import successful")
        
        # Try to import db_config directly
        try:
            import db_config
            logger.info("db_config import successful")
        except ImportError as e:
            logger.warning(f"Could not import db_config: {str(e)}. Will try to create stub module.")
            
            # Create a stub db_config.py in the current directory if necessary
            if not os.path.exists("db_config.py"):
                with open("db_config.py", "w") as f:
                    f.write("""
# Stub db_config.py created by deployment script
import os
import sys
sys.path.insert(0, ".")
import openai_client_fix
import logging

logger = logging.getLogger(__name__)
logger.info("Using stub db_config module")

def get_db():
    logger.info("Stub get_db function called")
    return None

def close_db(e=None):
    logger.info("Stub close_db function called")
    pass
""")
                logger.info("Created stub db_config.py module")
    except ImportError as e:
        logger.error(f"Critical import error: {str(e)}")
    
    # Check if app.py exists in synergos directory
    app_path = os.path.join("synergos", "app.py")
    if os.path.exists(app_path):
        logger.info(f"Running application from {app_path}")
        
        # Import the app module using importlib
        spec = importlib.util.spec_from_file_location("app_module", app_path)
        app_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app_module)
        
        # Access the Flask app object and run it
        if hasattr(app_module, 'app'):
            logger.info("Starting Flask application in production mode")
            app_module.app.run(host="0.0.0.0", port=5000, debug=False)
        else:
            logger.error("Could not find Flask 'app' object in the module")
    else:
        # Try current directory
        alt_path = os.path.join(".", "app.py")
        if os.path.exists(alt_path):
            logger.info(f"Running application from {alt_path}")
            
            # Import the app module using importlib
            spec = importlib.util.spec_from_file_location("app_module", alt_path)
            app_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(app_module)
            
            # Access the Flask app object and run it
            if hasattr(app_module, 'app'):
                logger.info("Starting Flask application in production mode")
                app_module.app.run(host="0.0.0.0", port=5000, debug=False)
            else:
                logger.error("Could not find Flask 'app' object in the module")
        else:
            logger.error("Could not find app.py in expected locations")

if __name__ == "__main__":
    # Show startup banner
    print("=" * 50)
    print("SYNERGOS APPLICATION - PRODUCTION MODE")
    print("=" * 50)
    
    # Check for mock services
    if os.environ.get('MOCK_SERVICES') == 'true':
        print("RUNNING WITH MOCK SERVICES - For testing only!")
        print("API calls to external services will be simulated")
    
    # Load environment variables
    load_env_variables()
    
    # Print startup information
    print("\nStarting server on http://localhost:5000")
    print("Press Ctrl+C to stop the server\n")
    
    # Run the application
    run_app() 