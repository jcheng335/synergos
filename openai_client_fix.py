# This patch fixes the OpenAI client initialization issue
import os
import openai
import logging
import importlib.util
import httpx  # Import httpx

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Get the OpenAI version
openai_version = openai.__version__
logger.info(f"OpenAI version detected: {openai_version}")

def get_patched_client(api_key=None):
    """
    Creates an OpenAI client with the provided API key,
    handling compatibility issues with different versions and proxy issues.
    
    Args:
        api_key: OpenAI API key (will fall back to env variable if None)
    
    Returns:
        Initialized OpenAI client or None if initialization fails.
    """
    # If no API key provided, try to get from environment
    if api_key is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.warning("No OpenAI API key provided or found in environment")
            return None  
    
    logger.info("Initializing OpenAI client")
    
    # For OpenAI SDK v1.x
    if openai_version.startswith('1.'):
        try:
            # Import OpenAI class
            from openai import OpenAI
            
            # Create an httpx client that explicitly ignores system proxies
            # This helps prevent the "unexpected keyword argument 'proxies'" error
            # if environment variables (HTTP_PROXY, HTTPS_PROXY) are set.
            httpx_client = httpx.Client(proxies=None, verify=False)
            
            # Standard initialization for v1.x, passing the custom httpx client
            client = OpenAI(api_key=api_key, http_client=httpx_client)
            logger.info("Successfully initialized OpenAI client using standard v1.x method with custom httpx client (no proxies)")
            return client
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI v1.x client: {str(e)}")
            # Fallback attempt without custom httpx client, in case httpx itself is the issue
            try:
                from openai import OpenAI
                client = OpenAI(api_key=api_key)
                logger.warning("Initialization with custom httpx client failed, retrying with default httpx settings.")
                logger.info("Successfully initialized OpenAI client using standard v1.x method (default httpx)")
                return client
            except Exception as e2:
                logger.error(f"Failed to initialize OpenAI v1.x client on retry: {str(e2)}")
                return None
    
    # For OpenAI SDK v0.x (legacy)
    else:
        logger.info("Using legacy OpenAI SDK (v0.x) initialization")
        try:
            openai.api_key = api_key
            # In v0.x, the module itself was often used as the client
            return openai 
        except Exception as e:
            logger.error(f"Failed to initialize legacy OpenAI v0.x client: {str(e)}")
            return None

# To use this in app.py:
# from openai_client_fix import get_patched_client
# client = get_patched_client(openai_api_key)
