import os
import logging
import uuid
from flask import request, jsonify, current_app
from synergos.api import api_bp
from synergos.agents import agent_registry, orchestrator
from synergos.models.candidate import Candidate
from synergos.extensions import db
from werkzeug.utils import secure_filename

# Set up logging
logger = logging.getLogger(__name__)

@api_bp.route('/upload_resume', methods=['POST'])
async def upload_resume():
    """
    Upload and analyze a resume
    Accepts PDF, DOCX, or TXT files
    """
    try:
        if 'resume' not in request.files:
            return jsonify({"error": "No resume file provided"}), 400
        
        file = request.files['resume']
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Validate file type
        allowed_extensions = {'pdf', 'docx', 'doc', 'txt'}
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        
        if file_ext not in allowed_extensions:
            return jsonify({"error": f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}"}), 400
        
        # Save file
        filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        
        logger.info(f"Resume saved to {filepath}")
        
        # Process resume
        job_id = request.form.get('job_id')
        data = {'resume_file_path': filepath}
        
        if job_id:
            data['job_id'] = job_id
        
        # Use orchestrator to process resume
        results = await orchestrator.execute_workflow('resume_review', data)
        
        # Create or update candidate in database
        candidate_data = results.get('contact_information', {})
        
        # Check if candidate already exists by email
        candidate_email = candidate_data.get('email')
        candidate = None
        
        if candidate_email:
            candidate = Candidate.query.filter_by(email=candidate_email).first()
        
        if not candidate and candidate_data.get('name'):
            # Create new candidate
            candidate = Candidate(
                name=candidate_data.get('name'),
                email=candidate_email or '',
                phone=candidate_data.get('phone', ''),
                resume_file_path=filepath,
                resume_text=results.get('resume_text', '')
            )
            db.session.add(candidate)
            db.session.commit()
            
            logger.info(f"Created new candidate: {candidate.id}")
        elif candidate:
            # Update existing candidate
            candidate.resume_file_path = filepath
            candidate.resume_text = results.get('resume_text', '')
            if 'job_match' in results:
                candidate.technical_score = results['job_match'].get('skill_match_percentage', 0)
                candidate.overall_score = results['job_match'].get('overall_match_percentage', 0)
            db.session.commit()
            
            logger.info(f"Updated existing candidate: {candidate.id}")
        
        return jsonify({
            "success": True,
            "message": "Resume processed successfully",
            "results": results,
            "candidate_id": candidate.id if candidate else None
        })
        
    except Exception as e:
        logger.error(f"Error processing resume: {str(e)}")
        return jsonify({"error": f"Failed to process resume: {str(e)}"}), 500


@api_bp.route('/process_resume_text', methods=['POST'])
async def process_resume_text():
    """
    Process resume text directly (without file upload)
    """
    try:
        data = request.get_json()
        
        if not data or 'resume_text' not in data:
            return jsonify({"error": "No resume text provided"}), 400
        
        resume_text = data['resume_text']
        job_id = data.get('job_id')
        
        # Process resume
        process_data = {'resume_text': resume_text}
        
        if job_id:
            process_data['job_id'] = job_id
        
        # Use orchestrator to process resume
        results = await orchestrator.execute_workflow('resume_review', process_data)
        
        return jsonify({
            "success": True,
            "message": "Resume text processed successfully",
            "results": results
        })
        
    except Exception as e:
        logger.error(f"Error processing resume text: {str(e)}")
        return jsonify({"error": f"Failed to process resume text: {str(e)}"}), 500


@api_bp.route('/match_resume_to_job', methods=['POST'])
async def match_resume_to_job():
    """
    Match a resume against a job posting
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Get resume data
        resume_id = data.get('resume_id')
        resume_file_path = data.get('resume_file_path')
        resume_text = data.get('resume_text')
        
        # Get job data
        job_id = data.get('job_id')
        job_file_path = data.get('job_file_path')
        job_text = data.get('job_text')
        
        if not ((resume_id or resume_file_path or resume_text) and (job_id or job_file_path or job_text)):
            return jsonify({"error": "Both resume and job data are required"}), 400
        
        # Prepare data for processing
        process_data = {}
        
        # Add resume data
        if resume_id:
            process_data['resume_id'] = resume_id
        elif resume_file_path:
            process_data['resume_file_path'] = resume_file_path
        elif resume_text:
            process_data['resume_text'] = resume_text
        
        # Add job data
        if job_id:
            process_data['job_id'] = job_id
        elif job_file_path:
            process_data['job_file_path'] = job_file_path
        elif job_text:
            process_data['job_text'] = job_text
        
        # Use orchestrator to process resume
        results = await orchestrator.execute_workflow('resume_review', process_data)
        
        return jsonify({
            "success": True,
            "message": "Resume matched to job successfully",
            "results": results
        })
        
    except Exception as e:
        logger.error(f"Error matching resume to job: {str(e)}")
        return jsonify({"error": f"Failed to match resume to job: {str(e)}"}), 500 