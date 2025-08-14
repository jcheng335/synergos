from flask import Blueprint

# Create a blueprint for future integrations (if needed)
integration_bp = Blueprint('integration', __name__)

# This is just a placeholder file 
# It contains a minimal implementation with no Azure dependencies

@integration_bp.route('/health', methods=['GET'])
def health_check():
    return {"status": "ok"} 