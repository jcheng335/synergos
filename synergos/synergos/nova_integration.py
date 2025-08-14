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

@nova_bp.route('/get-nova-credentials', methods=['POST'])
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

@nova_bp.route('/api/register-speaker', methods=['POST'])
def register_speaker():
    """
    Register a speaker profile (interviewer or candidate)
    """
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        speaker_role = data.get('speaker_role')  # 'interviewer' or 'candidate'
        sample_audio = data.get('sample_audio')  # Base64 encoded audio sample
        
        if not session_id or session_id not in active_sessions:
            return jsonify({"error": "Invalid session ID"}), 400
            
        if not speaker_role or speaker_role not in ['interviewer', 'candidate']:
            return jsonify({"error": "Speaker role must be 'interviewer' or 'candidate'"}), 400
            
        if not sample_audio:
            return jsonify({"error": "Audio sample required for speaker registration"}), 400
        
        # Update last activity timestamp
        active_sessions[session_id]["last_activity"] = datetime.now()
        
        # Decode audio data
        audio_bytes = base64.b64decode(sample_audio)
        
        # Set up AWS Bedrock client
        bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
        )
        
        # Call Nova Sonic to create a speaker profile
        response = bedrock_runtime.invoke_model(
            modelId='amazon.nova-sonic',
            contentType='application/json',
            accept='application/json',
            body=json.dumps({
                "task": "create_speaker_profile",
                "audio": base64.b64encode(audio_bytes).decode('utf-8'),
                "speaker_id": speaker_role
            })
        )
        
        response_body = json.loads(response['body'].read().decode('utf-8'))
        
        # Store speaker profile in session
        active_sessions[session_id]["speaker_profiles"][speaker_role] = response_body.get("profile_id")
        
        logger.info(f"Registered {speaker_role} profile for session {session_id}")
        
        return jsonify({
            "success": True,
            "message": f"Successfully registered {speaker_role} voice profile"
        })
        
    except Exception as e:
        logger.error(f"Error registering speaker: {str(e)}")
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
        
        # Set up AWS Bedrock client
        bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
        )
        
        # Decode audio data
        audio_bytes = base64.b64decode(audio_chunk)
        
        # Prepare speaker profiles if available
        speaker_profiles = active_sessions[session_id].get("speaker_profiles", {})
        
        # Call Nova Sonic for real-time diarization with emotional analysis
        request_body = {
            "task": "real_time_diarization_with_emotion",
            "audio": base64.b64encode(audio_bytes).decode('utf-8'),
            "enable_emotion_detection": True,
            "enable_sentiment_analysis": True,
            "enable_prosody_analysis": True,
            "enable_hesitation_detection": True
        }
        
        # Add speaker profiles if available
        if speaker_profiles:
            request_body["speaker_profiles"] = list(speaker_profiles.values())
        
        response = bedrock_runtime.invoke_model(
            modelId='amazon.nova-sonic',
            contentType='application/json',
            accept='application/json',
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read().decode('utf-8'))
        
        # Add timestamp to the result
        response_body["timestamp"] = timestamp
        
        # Store result in session
        if "diarization_results" not in active_sessions[session_id]:
            active_sessions[session_id]["diarization_results"] = []
            
        active_sessions[session_id]["diarization_results"].append(response_body)
        
        # Map speaker IDs to roles for the frontend
        if "speaker_profiles" in active_sessions[session_id] and "speakers" in response_body:
            speaker_id_to_role = {v: k for k, v in active_sessions[session_id]["speaker_profiles"].items()}
            
            for speaker in response_body.get("speakers", []):
                if speaker["speaker_id"] in speaker_id_to_role:
                    speaker["speaker_role"] = speaker_id_to_role[speaker["speaker_id"]]
        
        return jsonify({
            "success": True,
            "diarization": response_body
        })
        
    except Exception as e:
        logger.error(f"Error in real-time diarization: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@nova_bp.route('/api/nova-session-heartbeat', methods=['POST'])
def nova_session_heartbeat():
    """Keep track of active sessions"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')

        if not session_id or session_id not in active_sessions:
            return jsonify({"error": "Invalid session ID"}), 400

        # Update last activity timestamp
        active_sessions[session_id]["last_activity"] = datetime.now()

        return jsonify({"success": True})

    except Exception as e:
        logger.error(f"Error in session heartbeat: {str(e)}")
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

@nova_bp.route('/api/get-session-transcript', methods=['POST'])
def get_session_transcript():
    """Retrieve the full transcript with speaker diarization and emotional analysis"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')

        if not session_id or session_id not in active_sessions:
            return jsonify({"error": "Invalid session ID"}), 400

        # Get diarization results from session
        if "diarization_results" not in active_sessions[session_id]:
            return jsonify({"transcript": [], "message": "No transcript available"})

        # Process the results to include emotional markers
        transcript = active_sessions[session_id]["diarization_results"]
        
        # Add speaker roles for better display
        speaker_id_to_role = {v: k for k, v in active_sessions[session_id].get("speaker_profiles", {}).items()}
        
        for entry in transcript:
            if "speakers" in entry:
                for speaker in entry["speakers"]:
                    if speaker["speaker_id"] in speaker_id_to_role:
                        speaker["speaker_role"] = speaker_id_to_role[speaker["speaker_id"]]

        return jsonify({
            "transcript": transcript,
            "success": True
        })

    except Exception as e:
        logger.error(f"Error retrieving session transcript: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@nova_bp.route('/api/analyze-speech-emotions', methods=['POST'])
def analyze_speech_emotions():
    """
    Analyze specific audio segment for detailed emotional and sentiment analysis
    """
    try:
        data = request.get_json()
        audio_data = data.get('audio')  # Base64 encoded audio
        question = data.get('question', '')  # The question that was asked
        
        if not audio_data:
            return jsonify({"error": "Audio data required"}), 400
        
        # Set up AWS Bedrock client
        bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
        )
        
        # Decode audio data
        audio_bytes = base64.b64decode(audio_data)
        
        # Call Nova Sonic for in-depth emotional analysis
        response = bedrock_runtime.invoke_model(
            modelId='amazon.nova-sonic',
            contentType='application/json',
            accept='application/json',
            body=json.dumps({
                "task": "emotion_analysis",
                "audio": base64.b64encode(audio_bytes).decode('utf-8'),
                "context": {
                    "question": question
                },
                "analyze": {
                    "emotions": True,
                    "sentiment": True,
                    "prosody": True,
                    "hesitation": True,
                    "confidence": True
                }
            })
        )
        
        response_body = json.loads(response['body'].read().decode('utf-8'))
        
        return jsonify({
            "success": True,
            "emotion_analysis": response_body
        })
        
    except Exception as e:
        logger.error(f"Error analyzing speech emotions: {str(e)}")
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