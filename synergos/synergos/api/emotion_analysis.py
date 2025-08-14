import logging
from flask import request, jsonify
from synergos.api import api_bp
from synergos.agents import orchestrator

# Set up logging
logger = logging.getLogger(__name__)

@api_bp.route('/analyze_response_emotions', methods=['POST'])
async def analyze_response_emotions():
    """
    Analyze the emotional aspects of an interview response
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required data
        if 'response' not in data or 'emotional_data' not in data:
            return jsonify({
                "error": "Both response text and emotional data are required"
            }), 400
        
        # Get evaluation agent
        evaluation_agent = orchestrator.agent_registry.get_agent("evaluation")
        
        # Process emotional evaluation
        results = await evaluation_agent.process(data, task='evaluate_emotional_response')
        
        return jsonify({
            "success": True,
            "message": "Emotional analysis completed",
            "results": results
        })
        
    except Exception as e:
        logger.error(f"Error in emotional analysis: {str(e)}")
        return jsonify({"error": f"Failed to analyze emotions: {str(e)}"}), 500

@api_bp.route('/analyze_confidence', methods=['POST'])
async def analyze_confidence():
    """
    Analyze confidence patterns in speech
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required data
        if 'emotional_data' not in data:
            return jsonify({
                "error": "Emotional data is required"
            }), 400
        
        # Get evaluation agent
        evaluation_agent = orchestrator.agent_registry.get_agent("evaluation")
        
        # Process confidence analysis
        results = await evaluation_agent.process(data, task='analyze_speech_confidence')
        
        return jsonify({
            "success": True,
            "message": "Confidence analysis completed",
            "results": results
        })
        
    except Exception as e:
        logger.error(f"Error in confidence analysis: {str(e)}")
        return jsonify({"error": f"Failed to analyze confidence: {str(e)}"}), 500

@api_bp.route('/emotional_pattern_report', methods=['POST'])
async def emotional_pattern_report():
    """
    Generate a report on emotional patterns throughout an interview
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required data
        if 'emotional_data' not in data:
            return jsonify({
                "error": "Emotional data is required"
            }), 400
        
        # Get evaluation agent
        evaluation_agent = orchestrator.agent_registry.get_agent("evaluation")
        
        # Generate emotional pattern report
        results = await evaluation_agent.process(data, task='generate_emotional_pattern_report')
        
        return jsonify({
            "success": True,
            "message": "Emotional pattern report generated",
            "results": results
        })
        
    except Exception as e:
        logger.error(f"Error generating emotional pattern report: {str(e)}")
        return jsonify({"error": f"Failed to generate emotional pattern report: {str(e)}"}), 500

@api_bp.route('/enhanced_interview_evaluation', methods=['POST'])
async def enhanced_interview_evaluation():
    """
    Perform a comprehensive interview evaluation with emotional analysis
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required data
        if not ('transcript' in data or ('responses' in data and 'questions' in data)):
            return jsonify({
                "error": "Either transcript or both responses and questions are required"
            }), 400
            
        if 'emotional_data' not in data:
            return jsonify({
                "warning": "No emotional data provided - evaluation will be limited"
            }), 200
        
        # Execute interview evaluation workflow with emotional data
        results = await orchestrator.execute_workflow('interview_evaluation', data)
        
        return jsonify({
            "success": True,
            "message": "Enhanced interview evaluation completed",
            "results": results
        })
        
    except Exception as e:
        logger.error(f"Error in enhanced interview evaluation: {str(e)}")
        return jsonify({"error": f"Failed to evaluate interview: {str(e)}"}), 500 