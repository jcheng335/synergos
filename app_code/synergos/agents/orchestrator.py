import uuid
import logging
import asyncio
from synergos.extensions import celery_app

# Set up logging
logger = logging.getLogger(__name__)

class AgentOrchestrator:
    """
    Orchestrates multi-agent workflows by coordinating different agents
    to accomplish complex tasks through defined pipelines.
    """
    
    def __init__(self, agent_registry):
        """
        Initialize the orchestrator.
        
        Args:
            agent_registry: Registry of available agents
        """
        self.agent_registry = agent_registry
        self.workflows = {
            'resume_review': self._workflow_resume_review,
            'job_analysis': self._workflow_job_analysis,
            'interview_processing': self._workflow_interview_processing,
            'interview_evaluation': self._workflow_interview_evaluation,
            'candidate_evaluation': self._workflow_candidate_evaluation,
            'email_generation': self._workflow_email_generation,
            'complete_onboarding': self._workflow_complete_onboarding,
            'generate_interview_questions': self._workflow_generate_interview_questions
        }
    
    async def execute_workflow(self, workflow_name, data, **kwargs):
        """
        Execute a predefined workflow by name.
        
        Args:
            workflow_name (str): Name of the workflow to execute
            data (dict): Data required for the workflow
            **kwargs: Additional parameters for the workflow
            
        Returns:
            dict: The workflow results
        """
        if workflow_name not in self.workflows:
            raise ValueError(f"Workflow '{workflow_name}' not found")
        
        workflow_func = self.workflows[workflow_name]
        return await workflow_func(data, **kwargs)
    
    def execute_workflow_async(self, workflow_name, data, **kwargs):
        """
        Execute a workflow asynchronously as a Celery task.
        
        Args:
            workflow_name (str): Name of the workflow to execute
            data (dict): Data required for the workflow
            **kwargs: Additional parameters for the workflow
            
        Returns:
            AsyncResult: Celery task result
        """
        from synergos.tasks.workflow_tasks import execute_workflow_task
        return execute_workflow_task.delay(workflow_name, data, kwargs)
    
    async def _workflow_resume_review(self, data, **kwargs):
        """
        Workflow for analyzing a resume.
        
        Args:
            data: Must contain 'resume_text' or 'resume_file_path'
            
        Returns:
            dict: Resume analysis results
        """
        logger.info("Starting resume review workflow")
        
        # Get resume agent
        resume_agent = self.agent_registry.get_agent("resume")
        
        # Process resume
        resume_results = await resume_agent.process(data)
        
        # Get job agent if job details are provided
        if 'job_id' in data or 'job_details' in data:
            job_agent = self.agent_registry.get_agent("job")
            job_data = {'job_id': data.get('job_id')} if 'job_id' in data else {'job_details': data.get('job_details')}
            job_results = await job_agent.process(job_data)
            
            # Merge results for match assessment
            match_data = {
                'resume_analysis': resume_results,
                'job_analysis': job_results
            }
            match_results = await resume_agent.process(match_data, task='match_assessment')
            resume_results['job_match'] = match_results
        
        logger.info("Resume review workflow completed")
        return resume_results
    
    async def _workflow_job_analysis(self, data, **kwargs):
        """
        Workflow for analyzing a job posting.
        
        Args:
            data: Must contain 'job_text', 'job_file_path', or 'job_url'
            
        Returns:
            dict: Job analysis results
        """
        logger.info("Starting job analysis workflow")
        
        # Get job agent
        job_agent = self.agent_registry.get_agent("job")
        
        # Process job
        job_results = await job_agent.process(data)
        
        logger.info("Job analysis workflow completed")
        return job_results
    
    async def _workflow_interview_processing(self, data, **kwargs):
        """
        Workflow for processing interview data.
        
        Args:
            data: Must contain 'transcript' or 'audio_file_path'
            
        Returns:
            dict: Interview analysis results
        """
        logger.info("Starting interview processing workflow")
        
        # Get interview agent
        interview_agent = self.agent_registry.get_agent("interview")
        
        # Process interview
        interview_results = await interview_agent.process(data)
        
        # Run STAR analysis on responses if needed
        if kwargs.get('run_star_analysis', True) and 'responses' in interview_results:
            star_agent = self.agent_registry.get_agent("star")
            
            star_analyses = []
            for i, response in enumerate(interview_results['responses']):
                question = interview_results['questions'][i] if i < len(interview_results.get('questions', [])) else ""
                star_data = {
                    'response': response,
                    'question': question
                }
                star_result = await star_agent.process(star_data)
                star_analyses.append(star_result)
            
            interview_results['star_analyses'] = star_analyses
        
        # Run evaluation to detect contradictions and unclear responses
        if kwargs.get('detect_contradictions', True) and 'responses' in interview_results:
            evaluation_agent = self.agent_registry.get_agent("evaluation")
            
            # Prepare data for contradiction detection
            eval_data = {
                'responses': interview_results.get('responses', []),
                'questions': interview_results.get('questions', [])
            }
            
            # Detect contradictions
            contradictions = await evaluation_agent.process(eval_data, task='detect_contradictions')
            interview_results['contradictions'] = contradictions
            
            # Identify unclear responses
            unclear_responses = await evaluation_agent.process(eval_data, task='identify_unclear_responses')
            interview_results['unclear_responses'] = unclear_responses
        
        # Add resume context if available
        if 'candidate_id' in data or 'resume_analysis' in data:
            resume_agent = self.agent_registry.get_agent("resume")
            
            if 'resume_analysis' in data:
                resume_data = data['resume_analysis']
            else:
                # Get resume data for the candidate
                resume_data = await resume_agent.process({'candidate_id': data['candidate_id']})
                
            interview_results['resume_context'] = resume_data
        
        # Generate follow-up questions with enhanced context
        if kwargs.get('generate_followups', True):
            followup_agent = self.agent_registry.get_agent("followup_question")
            
            # Basic followups without contradiction information
            basic_followups = await interview_agent.process(
                interview_results, 
                task='generate_followup_questions'
            )
            
            # Generate followups using contradiction information if available
            enhanced_followups = []
            if 'contradictions' in interview_results and interview_results['contradictions']:
                for contradiction in interview_results['contradictions']:
                    contradiction_data = {
                        'contradictions': [contradiction]
                    }
                    contradiction_followup = await followup_agent.process(
                        contradiction_data,
                        task='generate_contradiction_followup'
                    )
                    enhanced_followups.extend(contradiction_followup.get('questions', []))
            
            # Generate followups for unclear responses if available
            if 'unclear_responses' in interview_results and interview_results['unclear_responses']:
                for unclear in interview_results['unclear_responses']:
                    unclear_data = {
                        'response': interview_results['responses'][unclear.get('index', 0)],
                        'question': interview_results['questions'][unclear.get('index', 0)] if 'questions' in interview_results else ""
                    }
                    clarification_followup = await followup_agent.process(
                        unclear_data,
                        task='generate_clarification'
                    )
                    enhanced_followups.extend(clarification_followup.get('unclear_points', []))
            
            # Generate STAR-focused followups if STAR analysis is available
            if 'star_analyses' in interview_results:
                for i, star_analysis in enumerate(interview_results['star_analyses']):
                    if i < len(interview_results.get('responses', [])):
                        star_data = {
                            'response': interview_results['responses'][i],
                            'question': interview_results['questions'][i] if i < len(interview_results.get('questions', [])) else "",
                            'star_analysis': star_analysis
                        }
                        star_followup = await followup_agent.process(
                            star_data,
                            task='generate_star_followup'
                        )
                        enhanced_followups.extend(star_followup.get('questions', []))
            
            # Combine all followup types
            interview_results['followup_questions'] = {
                'basic': basic_followups.get('followup_questions', []),
                'enhanced': enhanced_followups
            }
        
        # Generate evaluation if needed
        if kwargs.get('generate_evaluation', True):
            evaluation = await interview_agent.process(
                interview_results,
                task='evaluate_interview'
            )
            interview_results['evaluation'] = evaluation
        
        logger.info("Interview processing workflow completed")
        return interview_results
    
    async def _workflow_interview_evaluation(self, data, **kwargs):
        """
        Workflow for post-interview evaluation.
        
        Args:
            data: Must contain interview transcript, questions, and responses
            
        Returns:
            dict: Comprehensive evaluation results
        """
        logger.info("Starting interview evaluation workflow")
        
        # Get evaluation agent
        evaluation_agent = self.agent_registry.get_agent("evaluation")
        
        # Get job data if provided
        job_data = {}
        if 'job_id' in data:
            job_agent = self.agent_registry.get_agent("job")
            job_data = await job_agent.process({'job_id': data['job_id']})
            data['job_requirements'] = job_data
        elif 'job_requirements' in data or 'job_details' in data:
            if 'job_requirements' in data:
                job_data = data['job_requirements']
            else:
                job_data = data['job_details']
            data['job_requirements'] = job_data
        
        # Process comprehensive evaluation
        evaluation_results = await evaluation_agent.process(
            data, 
            task='comprehensive_evaluation'
        )
        
        logger.info("Interview evaluation workflow completed")
        return evaluation_results
    
    async def _workflow_candidate_evaluation(self, data, **kwargs):
        """
        Workflow for comprehensive candidate evaluation.
        
        Args:
            data: Must contain 'candidate_id' or 'candidate_details'
            
        Returns:
            dict: Candidate evaluation results
        """
        logger.info("Starting candidate evaluation workflow")
        
        # Get agents
        resume_agent = self.agent_registry.get_agent("resume")
        job_agent = self.agent_registry.get_agent("job")
        interview_agent = self.agent_registry.get_agent("interview")
        evaluation_agent = self.agent_registry.get_agent("evaluation")
        
        # Get candidate data
        candidate_id = data.get('candidate_id')
        candidate_details = data.get('candidate_details', {})
        
        results = {
            'candidate_id': candidate_id,
            'evaluations': []
        }
        
        # Process resume if available
        if 'resume_text' in data or 'resume_file_path' in data:
            resume_results = await resume_agent.process({
                'resume_text': data.get('resume_text'),
                'resume_file_path': data.get('resume_file_path')
            })
            results['resume_analysis'] = resume_results
        
        # Process job if available
        if 'job_id' in data or 'job_details' in data:
            job_data = {'job_id': data.get('job_id')} if 'job_id' in data else {'job_details': data.get('job_details')}
            job_results = await job_agent.process(job_data)
            results['job_analysis'] = job_results
        
        # Process interviews if available
        if 'interviews' in data and data['interviews']:
            interview_results = []
            for interview in data['interviews']:
                result = await interview_agent.process(interview)
                interview_results.append(result)
            results['interview_analyses'] = interview_results
            
            # Evaluate each interview
            interview_evaluations = []
            for interview in interview_results:
                eval_data = {
                    'responses': interview.get('responses', []),
                    'questions': interview.get('questions', []),
                    'transcript': interview.get('transcript', ''),
                    'job_requirements': results.get('job_analysis', {})
                }
                eval_result = await evaluation_agent.process(eval_data, task='comprehensive_evaluation')
                interview_evaluations.append(eval_result)
            results['interview_evaluations'] = interview_evaluations
        
        # Generate final evaluation
        if 'resume_analysis' in results and 'job_analysis' in results:
            match_data = {
                'resume_analysis': results['resume_analysis'],
                'job_analysis': results['job_analysis']
            }
            
            if 'interview_analyses' in results:
                match_data['interview_analyses'] = results['interview_analyses']
            
            # Use evaluation agent instead of resume agent for comprehensive evaluation
            final_evaluation = await evaluation_agent.process(match_data, task='comprehensive_evaluation')
            results['final_evaluation'] = final_evaluation
        
        logger.info("Candidate evaluation workflow completed")
        return results
    
    async def _workflow_email_generation(self, data, **kwargs):
        """
        Workflow for generating emails based on candidate status.
        
        Args:
            data: Must contain 'candidate_id' and 'email_type'
            
        Returns:
            dict: Generated email content
        """
        logger.info("Starting email generation workflow")
        
        # Get email agent
        email_agent = self.agent_registry.get_agent("email")
        
        # Process email request
        email_results = await email_agent.process(data)
        
        logger.info("Email generation workflow completed")
        return email_results
    
    async def _workflow_complete_onboarding(self, data, **kwargs):
        """
        Comprehensive workflow for the entire onboarding process.
        
        Args:
            data: Must contain job and candidate information
            
        Returns:
            dict: Complete onboarding results
        """
        logger.info("Starting complete onboarding workflow")
        
        results = {}
        
        # Step 1: Job Analysis
        job_results = await self._workflow_job_analysis({
            'job_text': data.get('job_text'),
            'job_file_path': data.get('job_file_path'),
            'job_url': data.get('job_url')
        })
        results['job_analysis'] = job_results
        
        # Step 2: Resume Analysis
        resume_results = await self._workflow_resume_review({
            'resume_text': data.get('resume_text'),
            'resume_file_path': data.get('resume_file_path'),
            'job_details': job_results
        })
        results['resume_analysis'] = resume_results
        
        # Step 2.5: Generate Initial Interview Questions
        competencies = data.get('competencies', [])
        preset_questions = data.get('preset_questions', [])
        
        question_data = {
            'resume_analysis': resume_results,
            'job_analysis': job_results,
            'competencies': competencies,
            'preset_questions': preset_questions
        }
        
        interview_questions = await self._workflow_generate_interview_questions(question_data)
        results['interview_questions'] = interview_questions
        
        # Step 3: Interview Processing (if interview data provided)
        if 'transcript' in data or 'audio_file_path' in data:
            interview_data = {
                'transcript': data.get('transcript'),
                'audio_file_path': data.get('audio_file_path'),
                'job_details': job_results,
                'candidate_details': {'resume_analysis': resume_results},
                'initial_questions': interview_questions.get('questions', [])
            }
            interview_results = await self._workflow_interview_processing(interview_data)
            results['interview_analysis'] = interview_results
            
            # Step 3.5: Interview Evaluation (detailed post-interview analysis)
            evaluation_data = {
                'responses': interview_results.get('responses', []),
                'questions': interview_results.get('questions', []),
                'transcript': interview_results.get('transcript', ''),
                'job_requirements': job_results,
                'resume_analysis': resume_results
            }
            evaluation_results = await self._workflow_interview_evaluation(evaluation_data)
            results['interview_evaluation'] = evaluation_results
        
        # Step 4: Final Evaluation
        evaluation_data = {
            'resume_analysis': resume_results,
            'job_analysis': job_results
        }
        
        if 'interview_analysis' in results:
            evaluation_data['interview_analyses'] = [results['interview_analysis']]
        
        evaluation_results = await self._workflow_candidate_evaluation(evaluation_data)
        results['final_evaluation'] = evaluation_results.get('final_evaluation')
        
        # Step 5: Email Generation (if requested)
        if kwargs.get('generate_email', True):
            email_type = kwargs.get('email_type', 'follow_up')
            email_data = {
                'candidate_name': data.get('candidate_name'),
                'candidate_email': data.get('candidate_email'),
                'job_title': job_results.get('title'),
                'company': job_results.get('company'),
                'email_type': email_type,
                'evaluation': results.get('final_evaluation')
            }
            email_results = await self._workflow_email_generation(email_data)
            results['email'] = email_results
        
        logger.info("Complete onboarding workflow completed")
        return results
    
    async def _workflow_generate_interview_questions(self, data, **kwargs):
        """
        Workflow for generating tailored interview questions based on resume, job, and competencies.
        
        Args:
            data: Must contain 'job_analysis' and 'resume_analysis'. 
                  'job_analysis' should contain 'top_competencies'.

        Returns:
            dict: Generated interview questions (intro, competency sets, resume-based).
        """
        logger.info("Starting question generation workflow")

        # Get required agents
        question_generator = self.agent_registry.get_agent("question_generator")

        # Expect job_analysis and resume_analysis to be passed in directly
        resume_results = data.get('resume_analysis', {})
        job_results = data.get('job_analysis', {})

        if not resume_results:
             logger.warning("Resume analysis data not provided to question generation workflow.")
        if not job_results:
             logger.warning("Job analysis data not provided to question generation workflow.")
        if not job_results.get('top_competencies'):
             logger.warning("Job analysis data missing 'top_competencies' for competency questions.")

        # Prepare data for question generation
        # The agent's process method expects these keys
        question_data = {
            'resume_analysis': resume_results,
            'job_analysis': job_results,
            # Pass other relevant data if needed by agent methods, e.g., competencies if separate
            # 'competencies': data.get('competencies', []) 
        }

        # Call the agent with the default task to get all question types
        logger.info("Calling QuestionGeneratorAgent to get all question types...")
        all_questions_result = await question_generator.process(question_data, task='get_all_questions')

        # Structure the final result (might be slightly different from agent's raw output if needed)
        result = {
            'introduction_questions': all_questions_result.get('introduction_questions', []),
            'competency_question_sets': all_questions_result.get('competency_questions', []),
            'resume_based_questions': all_questions_result.get('resume_based_questions', []),
            'context': {
                'resume_used': bool(resume_results),
                'job_used': bool(job_results),
                'top_competencies_found': bool(job_results.get('top_competencies'))
            }
        }

        logger.info(f"Question generation workflow completed.")
        return result 