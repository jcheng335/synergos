import os
import logging
import json
import uuid
import base64
import boto3
from flask import request, jsonify, Blueprint
from datetime import datetime, timedelta

# Set up logging
logger = logging.getLogger(__name__)

# Create Blueprint for Nova routes
nova_bp = Blueprint('nova', __name__)

# Store active sessions (in a real app, use a proper database)
active_sessions = {}

@nova_bp.route('/api/get-nova-credentials', methods=['POST'])
def get_nova_credentials():
    """Get credentials for Nova Sonic"""
    try:
        aws_region = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')

        # Generate a session ID for tracking
        session_id = str(uuid.uuid4())

        # Store session information
        active_sessions[session_id] = {
            "created_at": datetime.now(),
            "last_activity": datetime.now(),
            "speaker_profiles": {}  # Will store speaker profiles (interviewer/candidate)
        }

        # Clean up old sessions
        cleanup_old_sessions()

        logger.info(f"Created new Nova Sonic session: {session_id}")
        
        # Return credentials to the frontend
        return jsonify({
            "session_id": session_id,
            "region": aws_region
        })

    except Exception as e:
        logger.error(f"Error providing Nova credentials: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@nova_bp.route('/api/nova-real-time-diarization', methods=['POST'])
def nova_real_time_diarization():
    """
    Process real-time audio for diarization with Nova Sonic
    """
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        audio_chunk = data.get('audio_chunk')  # Base64 encoded audio
        timestamp = data.get('timestamp', datetime.now().isoformat())
        
        if not session_id or session_id not in active_sessions:
            return jsonify({"error": "Invalid session ID"}), 400
            
        if not audio_chunk:
            return jsonify({"error": "No audio data provided"}), 400
            
        # Update last activity timestamp
        active_sessions[session_id]["last_activity"] = datetime.now()
        
        # For now, return mock data since Nova Sonic API might not be available
        # In production, you would uncomment the code below to use actual Nova Sonic
        
        # Mock response with speaker diarization
        mock_response = {
            "speakers": [
                {
                    "speaker_id": "speaker_0",
                    "speaker_role": "candidate",
                    "transcript": "I have experience in this area and have worked on similar projects before.",
                    "confidence": 0.85,
                    "emotions": {
                        "confidence": 0.7,
                        "enthusiasm": 0.6,
                        "nervousness": 0.2
                    },
                    "start_time": 0.0,
                    "end_time": 3.5
                }
            ],
            "timestamp": timestamp
        }
        
        # Store result in session
        if "diarization_results" not in active_sessions[session_id]:
            active_sessions[session_id]["diarization_results"] = []
            
        active_sessions[session_id]["diarization_results"].append(mock_response)
        
        return jsonify({
            "success": True,
            "diarization": mock_response
        })
        
        # Uncomment this section when Nova Sonic API is available:
        """
        # Set up AWS Bedrock client
        bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
        )
        
        # Decode audio data
        audio_bytes = base64.b64decode(audio_chunk)
        
        # Call Nova Sonic for real-time diarization with emotional analysis
        request_body = {
            "task": "real_time_diarization_with_emotion",
            "audio": base64.b64encode(audio_bytes).decode('utf-8'),
            "enable_emotion_detection": True,
            "enable_sentiment_analysis": True,
            "enable_prosody_analysis": True,
            "enable_hesitation_detection": True
        }
        
        response = bedrock_runtime.invoke_model(
            modelId='amazon.nova-sonic',
            contentType='application/json',
            accept='application/json',
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read().decode('utf-8'))
        response_body["timestamp"] = timestamp
        
        # Store result in session
        if "diarization_results" not in active_sessions[session_id]:
            active_sessions[session_id]["diarization_results"] = []
            
        active_sessions[session_id]["diarization_results"].append(response_body)
        
        return jsonify({
            "success": True,
            "diarization": response_body
        })
        """
        
    except Exception as e:
        logger.error(f"Error in real-time diarization: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@nova_bp.route('/api/end-nova-session', methods=['POST'])
def end_nova_session():
    """Properly close a Nova Sonic session"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')

        if not session_id:
            return jsonify({"error": "Session ID is required"}), 400

        # Remove session if it exists
        if session_id in active_sessions:
            del active_sessions[session_id]
            logger.info(f"Nova session {session_id} ended")

        return jsonify({"success": True, "message": "Session ended"})

    except Exception as e:
        logger.error(f"Error ending Nova session: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

def cleanup_old_sessions():
    """Remove sessions that have been inactive for too long"""
    current_time = datetime.now()
    expired_sessions = []

    # Find expired sessions (inactive for more than 30 minutes)
    for session_id, session_data in active_sessions.items():
        last_activity = session_data.get("last_activity", session_data.get("created_at"))
        if current_time - last_activity > timedelta(minutes=30):
            expired_sessions.append(session_id)

    # Remove expired sessions
    for session_id in expired_sessions:
        del active_sessions[session_id]
        logger.info(f"Removed expired session: {session_id}")