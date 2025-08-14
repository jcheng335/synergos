import os
import logging
import json
from synergos.agents.agent_base import AgentBase
from synergos.models.candidate import Candidate
from synergos.utils.document_processing import extract_text_from_document

# Set up logging
logger = logging.getLogger(__name__)

class ResumeAnalysisAgent(AgentBase):
    """
    Agent responsible for analyzing resumes and matching them against job requirements.
    Uses LLMs to extract skills, experience, education, and other relevant information.
    """
    
    async def process(self, data, task="analyze_resume", **kwargs):
        """
        Process resume data based on the specified task.
        
        Args:
            data: The resume data to process
            task: The specific task to perform (analyze_resume, match_assessment, comprehensive_evaluation)
            **kwargs: Additional parameters for processing
            
        Returns:
            dict: The processing results
        """
        method_map = {
            "analyze_resume": self._analyze_resume,
            "match_assessment": self._assess_job_match,
            "comprehensive_evaluation": self._comprehensive_evaluation
        }
        
        if task not in method_map:
            raise ValueError(f"Unknown task '{task}' for ResumeAnalysisAgent")
        
        return await method_map[task](data, **kwargs)
    
    async def _analyze_resume(self, data, **kwargs):
        """
        Analyze a resume to extract structured information.
        
        Args:
            data: Must contain 'resume_text' or 'resume_file_path'
            
        Returns:
            dict: Structured resume information
        """
        # Check if this is the Evernorth demo
        is_evernorth_demo = kwargs.get('is_evernorth_demo', False) or data.get('is_evernorth_demo', False)
        
        # Get resume text
        resume_text = data.get('resume_text')
        if not resume_text and 'resume_file_path' in data:
            resume_text = extract_text_from_document(data['resume_file_path'])
        
        if not resume_text:
            if is_evernorth_demo:
                # For Evernorth demo, provide a mock resume analysis ONLY if no resume text provided
                logger.info("Using mock resume analysis for Evernorth demo as fallback")
                analysis_result = {
                    "contact_information": {
                        "name": "John Candidate",
                        "email": "john.candidate@example.com",
                        "phone": "(555) 123-4567",
                        "location": "Chicago, IL"
                    },
                    "skills": {
                        "technical_skills": ["Financial Analysis", "Risk Assessment", "Underwriting", "Excel", "SQL", "Data Analysis"],
                        "soft_skills": ["Communication", "Leadership", "Problem Solving", "Critical Thinking"]
                    },
                    "experience": [
                        {
                            "company": "Financial Services Inc.",
                            "title": "Senior Underwriter",
                            "start_date": "2018-01",
                            "end_date": "Present",
                            "duration": "5 years",
                            "description": "Led underwriting for complex financial products",
                            "achievements": ["Reduced risk exposure by 15%", "Increased portfolio profitability by 12%"]
                        },
                        {
                            "company": "Insurance Analytics LLC",
                            "title": "Risk Analyst",
                            "start_date": "2015-03",
                            "end_date": "2017-12",
                            "duration": "2.5 years",
                            "description": "Analyzed insurance risks and developed pricing models",
                            "achievements": ["Developed new risk assessment framework", "Trained team of 5 junior analysts"]
                        }
                    ],
                    "education": [
                        {
                            "school": "University of Chicago",
                            "degree": "MBA",
                            "field": "Finance",
                            "graduation_date": "2015"
                        },
                        {
                            "school": "Illinois State University",
                            "degree": "BS",
                            "field": "Statistics",
                            "graduation_date": "2013"
                        }
                    ],
                    "key_strengths": ["Risk Analysis", "Financial Modeling", "Team Leadership", "Strategic Planning", "Client Communication"],
                    "years_of_relevant_experience": 7,
                    "current_role": "Senior Underwriter",
                    "resume_text": "Mock resume for Evernorth demo"
                }
                
                # Store in agent state
                self.update_state("resume_analysis", analysis_result)
                
                return analysis_result
            else:
                raise ValueError("No resume text provided")
        
        # Construct prompt for analysis
        messages = [
            {"role": "system", "content": "You are an expert resume analyzer. Extract structured information from the resume provided."},
            {"role": "user", "content": f"""
            Please analyze this resume and extract the following information in JSON format:
            
            Resume text:
            {resume_text}
            
            Please extract:
            1. Contact information (name, email, phone, location)
            2. Skills (technical_skills, soft_skills)
            3. Experience (list of jobs with company, title, start_date, end_date, description, achievements)
            4. Education (list of institutions with school, degree, field, graduation_date)
            5. Projects (if any)
            6. Certifications (if any)
            7. Key strengths (up to 5)
            8. Years of relevant experience
            
            Provide the output as a JSON object.
            """}
        ]
        
        # Call LLM for analysis
        analysis_result_text = self._call_llm(messages)
        
        # Try to parse the result as JSON
        try:
            # Extract JSON from the response
            json_start = analysis_result_text.find('{')
            json_end = analysis_result_text.rfind('}') + 1
            json_str = analysis_result_text[json_start:json_end]
            analysis_result = json.loads(json_str)
        except Exception as e:
            logger.error(f"Error parsing resume analysis result: {str(e)}")
            # Fall back to a simpler approach
            analysis_result = {
                "contact_information": {"name": "Unknown", "email": "Unknown"},
                "skills": {"technical_skills": [], "soft_skills": []},
                "experience": [],
                "education": [],
                "key_strengths": [],
                "years_of_relevant_experience": 0
            }
        
        # Add the raw resume text
        analysis_result["resume_text"] = resume_text
        
        # Extract current role from experience if available
        if "experience" in analysis_result and analysis_result["experience"] and isinstance(analysis_result["experience"], list) and len(analysis_result["experience"]) > 0:
            current_job = analysis_result["experience"][0]
            if isinstance(current_job, dict) and "title" in current_job:
                analysis_result["current_role"] = current_job["title"]
        
        # Also extract skills as a flat list for easier processing in the UI
        if "skills" in analysis_result:
            all_skills = []
            if "technical_skills" in analysis_result["skills"] and isinstance(analysis_result["skills"]["technical_skills"], list):
                all_skills.extend(analysis_result["skills"]["technical_skills"])
            if "soft_skills" in analysis_result["skills"] and isinstance(analysis_result["skills"]["soft_skills"], list):
                all_skills.extend(analysis_result["skills"]["soft_skills"])
            analysis_result["skills_list"] = all_skills
        
        # Store in agent state
        self.update_state("resume_analysis", analysis_result)
        
        return analysis_result
    
    async def _assess_job_match(self, data, **kwargs):
        """
        Assess how well a resume matches a job.
        
        Args:
            data: Must contain 'resume_analysis' and 'job_analysis'
            
        Returns:
            dict: Job match assessment
        """
        resume_analysis = data.get('resume_analysis')
        job_analysis = data.get('job_analysis')
        
        if not resume_analysis or not job_analysis:
            raise ValueError("Both resume_analysis and job_analysis are required")
        
        # Construct prompt for matching
        messages = [
            {"role": "system", "content": "You are an expert in matching candidates to job requirements."},
            {"role": "user", "content": f"""
            Please assess how well this candidate matches the job requirements and provide a detailed analysis.
            
            Resume analysis:
            {json.dumps(resume_analysis, indent=2)}
            
            Job analysis:
            {json.dumps(job_analysis, indent=2)}
            
            Provide your assessment in JSON format with the following fields:
            1. overall_match_percentage (0-100)
            2. skill_match_percentage (0-100)
            3. experience_match_percentage (0-100)
            4. education_match_percentage (0-100)
            5. missing_skills (list of important skills not found in the resume)
            6. matching_skills (list of skills that match between the job and resume)
            7. years_experience_assessment (whether the candidate's experience meets the requirements)
            8. strengths (list of the candidate's key strengths for this role)
            9. weaknesses (list of areas where the candidate might not meet the requirements)
            10. recommendation (string: "strong_match", "potential_match", "weak_match")
            
            Provide the output as a JSON object.
            """}
        ]
        
        # Call LLM for analysis
        match_result_text = self._call_llm(messages)
        
        # Try to parse the result as JSON
        try:
            # Extract JSON from the response
            json_start = match_result_text.find('{')
            json_end = match_result_text.rfind('}') + 1
            json_str = match_result_text[json_start:json_end]
            match_result = json.loads(json_str)
        except Exception as e:
            logger.error(f"Error parsing job match result: {str(e)}")
            match_result = {
                "overall_match_percentage": 0,
                "skill_match_percentage": 0,
                "experience_match_percentage": 0,
                "education_match_percentage": 0,
                "recommendation": "unknown"
            }
        
        # Store in agent state
        self.update_state("job_match", match_result)
        
        return match_result
    
    async def _comprehensive_evaluation(self, data, **kwargs):
        """
        Provide a comprehensive evaluation of a candidate based on resume and optional interview.
        
        Args:
            data: Must contain 'resume_analysis' and 'job_analysis', optionally 'interview_analyses'
            
        Returns:
            dict: Comprehensive evaluation
        """
        resume_analysis = data.get('resume_analysis')
        job_analysis = data.get('job_analysis')
        interview_analyses = data.get('interview_analyses', [])
        
        if not resume_analysis or not job_analysis:
            raise ValueError("Both resume_analysis and job_analysis are required")
        
        # Get job match if it's not already in resume_analysis
        if 'job_match' not in resume_analysis:
            job_match = await self._assess_job_match({
                'resume_analysis': resume_analysis,
                'job_analysis': job_analysis
            })
        else:
            job_match = resume_analysis['job_match']
        
        # Construct prompt for evaluation
        messages = [
            {"role": "system", "content": "You are an expert in evaluating candidates for job positions."},
            {"role": "user", "content": f"""
            Please provide a comprehensive evaluation of this candidate based on their resume, job requirements, and interview performance (if available).
            
            Resume analysis:
            {json.dumps(resume_analysis, indent=2)}
            
            Job analysis:
            {json.dumps(job_analysis, indent=2)}
            
            Job match assessment:
            {json.dumps(job_match, indent=2)}
            
            {"Interview analyses:" if interview_analyses else ""}
            {json.dumps(interview_analyses, indent=2) if interview_analyses else ""}
            
            Provide your evaluation in JSON format with the following fields:
            1. overall_score (0-100)
            2. technical_score (0-100)
            3. communication_score (0-100)
            4. cultural_fit_score (0-100)
            5. key_strengths (list of the candidate's key strengths)
            6. areas_of_concern (list of potential issues or gaps)
            7. hiring_recommendation (string: "hire", "consider", "reject")
            8. reasoning (string explaining the recommendation)
            9. suggested_role_fit (string suggesting what roles might be a good fit)
            10. suggested_interview_questions (list of questions if additional interviews are needed)
            
            Provide the output as a JSON object.
            """}
        ]
        
        # Call LLM for analysis
        eval_result_text = self._call_llm(messages)
        
        # Try to parse the result as JSON
        try:
            # Extract JSON from the response
            json_start = eval_result_text.find('{')
            json_end = eval_result_text.rfind('}') + 1
            json_str = eval_result_text[json_start:json_end]
            eval_result = json.loads(json_str)
        except Exception as e:
            logger.error(f"Error parsing evaluation result: {str(e)}")
            eval_result = {
                "overall_score": 0,
                "technical_score": 0,
                "communication_score": 0,
                "cultural_fit_score": 0,
                "hiring_recommendation": "unknown"
            }
        
        # Store in agent state
        self.update_state("comprehensive_evaluation", eval_result)
        
        return eval_result 