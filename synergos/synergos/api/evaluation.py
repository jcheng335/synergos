import logging
from flask import request, jsonify
from synergos.api import api_bp
from synergos.agents import orchestrator

# Set up logging
logger = logging.getLogger(__name__)

@api_bp.route('/evaluate_interview', methods=['POST'])
async def evaluate_interview():
    """
    Perform a comprehensive evaluation of an interview
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
        
        # Execute interview evaluation workflow
        results = await orchestrator.execute_workflow('interview_evaluation', data)
        
        return jsonify({
            "success": True,
            "message": "Interview evaluation completed",
            "results": results
        })
        
    except Exception as e:
        logger.error(f"Error in interview evaluation: {str(e)}")
        return jsonify({"error": f"Failed to evaluate interview: {str(e)}"}), 500


@api_bp.route('/evaluate_response_star', methods=['POST'])
async def evaluate_response_star():
    """
    Evaluate a single response for STAR format adherence
    """
    try:
        data = request.get_json()
        
        if not data or 'response' not in data:
            return jsonify({"error": "Response text is required"}), 400
        
        # Get evaluation agent
        evaluation_agent = orchestrator.agent_registry.get_agent("evaluation")
        
        # Evaluate response
        result = await evaluation_agent.process({
            'responses': [data['response']],
            'questions': [data.get('question', '')]
        }, task='evaluate_star_format')
        
        return jsonify({
            "success": True,
            "message": "STAR format evaluation completed",
            "results": result
        })
        
    except Exception as e:
        logger.error(f"Error in STAR evaluation: {str(e)}")
        return jsonify({"error": f"Failed to evaluate STAR format: {str(e)}"}), 500


@api_bp.route('/generate_interview_summary', methods=['POST'])
async def generate_interview_summary():
    """
    Generate a comprehensive interview summary for the interviewer
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required data
        if not ('evaluation_results' in data or 'interview_data' in data):
            return jsonify({
                "error": "Either evaluation results or interview data are required"
            }), 400
        
        # Get evaluation agent
        evaluation_agent = orchestrator.agent_registry.get_agent("evaluation")
        
        # Generate summary
        result = await evaluation_agent.process(data, task='generate_summary_report')
        
        return jsonify({
            "success": True,
            "message": "Interview summary generated",
            "results": result
        })
        
    except Exception as e:
        logger.error(f"Error generating interview summary: {str(e)}")
        return jsonify({"error": f"Failed to generate interview summary: {str(e)}"}), 500


@api_bp.route('/evaluate_competencies', methods=['POST'])
async def evaluate_competencies():
    """
    Evaluate interview responses against required competencies and job requirements
    """
    try:
        data = request.get_json()
        
        if not data or 'responses' not in data:
            return jsonify({"error": "Interview responses are required"}), 400
        
        # Get evaluation agent
        evaluation_agent = orchestrator.agent_registry.get_agent("evaluation")
        
        # Evaluate competencies
        result = await evaluation_agent.process(data, task='evaluate_competencies')
        
        return jsonify({
            "success": True,
            "message": "Competency evaluation completed",
            "results": result
        })
        
    except Exception as e:
        logger.error(f"Error in competency evaluation: {str(e)}")
        return jsonify({"error": f"Failed to evaluate competencies: {str(e)}"}), 500 