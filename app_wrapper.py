import os
import sys
from dotenv import load_dotenv
from synergos.app import app

# Load environment variables from .env file
load_dotenv()

# Check for OpenAI API key
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("Error: OPENAI_API_KEY not found in environment variables.")
    sys.exit(1)

# Import the get_patched_client for OpenAI
from openai_client_fix import get_patched_client

# Create OpenAI client
OPENAI_CLIENT = get_patched_client(api_key=OPENAI_API_KEY)

# Optional: Import OpenAI client wherever needed in the codebase
import builtins
builtins.OPENAI_CLIENT = OPENAI_CLIENT

# Run the Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), threaded=True)
