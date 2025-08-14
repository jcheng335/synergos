import logging
import json
from synergos.agents.agent_base import AgentBase
# Import the function to get questions from the database
# TODO: Move DB functions to a central utility module
from synergos.agents.job_analysis_agent import get_questions_by_competency

logger = logging.getLogger(__name__)

class QuestionGeneratorAgent(AgentBase):
    """
    Agent responsible for generating and selecting interview questions.
    Provides introductory, competency-based (preset), and resume-based questions.
    """

    async def process(self, data, task="get_all_questions", **kwargs):
        """Process question generation request based on specified task"""
        # Simplified: Default task gets all types. Specific tasks can be added if needed later.
        if task == "get_introduction_questions":
            return await self._get_introduction_questions(data, **kwargs)
        elif task == "get_preset_competency_questions":
            return await self._get_preset_competency_questions(data, **kwargs)
        elif task == "get_resume_based_questions":
            return await self._get_resume_based_questions(data, **kwargs)
        elif task == "get_all_questions":
             # Orchestrate getting all question types
            intro_q = await self._get_introduction_questions(data, **kwargs)
            comp_q = await self._get_preset_competency_questions(data, **kwargs)
            resume_q = await self._get_resume_based_questions(data, **kwargs)
            return {
                "introduction_questions": intro_q.get("questions", []),
                "competency_questions": comp_q.get("competency_question_sets", []),
                "resume_based_questions": resume_q.get("questions", [])
            }
        else:
            logger.warning(f"Unknown task '{task}' for QuestionGeneratorAgent. Defaulting to 'get_all_questions'.")
            # Fallback to generating all questions
            intro_q = await self._get_introduction_questions(data, **kwargs)
            comp_q = await self._get_preset_competency_questions(data, **kwargs)
            resume_q = await self._get_resume_based_questions(data, **kwargs)
            return {
                "introduction_questions": intro_q.get("questions", []),
                "competency_questions": comp_q.get("competency_question_sets", []),
                "resume_based_questions": resume_q.get("questions", [])
            }

    async def _get_introduction_questions(self, data, **kwargs):
        """
        Return a fixed list of standard introductory questions.

        Args:
            data: Not used, but kept for consistency.

        Returns:
            dict: List of standard introductory questions.
        """
        logger.info("Getting standard introductory questions...")
        
        # Return fixed list of questions
        questions = {
            "questions": [
                {
                    "question": "Could you start by walking me through your resume?",
                    "purpose": "Get an overview of the candidate's background from their perspective."
                },
                {
                    "question": "Can you tell me a little bit about yourself?",
                    "purpose": "Allow the candidate to provide a brief personal introduction."
                },
                {
                    "question": "What interests you about this position and our company?",
                    "purpose": "Assess candidate's motivations and research."
                }
            ]
        }
        
        logger.info(f"Returning {len(questions.get('questions',[]))} standard introductory questions.")
        return questions


    async def _get_preset_competency_questions(self, data, **kwargs):
        """
        Fetches 2 preset questions per competency from DB for the top 5 competencies.
        Uses LLM to suggest the best fit based on job/resume context.

        Args:
            data: Must contain 'job_analysis'. Should contain 'resume_analysis'.
                  'job_analysis' must contain 'top_competencies' (list of dicts with 'name').

        Returns:
            dict: {
                    "competency_question_sets": [
                        {
                            "competency_name": "Competency Name",
                            "questions": [
                                {"text": "Question 1 Text", "suggested": true, "reason": "Why suggested"},
                                {"text": "Question 2 Text", "suggested": false, "reason": ""}
                            ]
                        }, ...
                    ]
                  }
        """
        logger.info("Getting preset competency questions...")
        job_analysis = data.get('job_analysis', {})
        resume_analysis = data.get('resume_analysis', {})
        top_competencies = job_analysis.get('top_competencies', []) # Expected: [{'name': 'Comp1', ...}, ...]

        if not top_competencies:
            logger.warning("No top competencies found in job_analysis data.")
            return {"competency_question_sets": []}

        competency_question_sets = []
        num_competencies_to_process = min(len(top_competencies), 5) # Process top 5

        for i in range(num_competencies_to_process):
            comp_info = top_competencies[i]
            competency_name = comp_info.get('name')
            if not competency_name:
                logger.warning(f"Skipping competency at index {i} due to missing name.")
                continue

            logger.debug(f"Fetching preset questions for competency: {competency_name}")
            try:
                # Fetch 2 preset questions from DB
                preset_questions_db = get_questions_by_competency(competency_name, limit=2)

                if not preset_questions_db or len(preset_questions_db) < 2:
                    logger.warning(f"Could not find 2 preset questions for competency '{competency_name}'. Skipping.")
                    # Optionally: Generate questions using LLM as fallback? For now, skip.
                    continue

                # Extract question text (assuming 'question' key in DB items)
                q1_text = preset_questions_db[0].get('question', '')
                q2_text = preset_questions_db[1].get('question', '')

                if not q1_text or not q2_text:
                     logger.warning(f"Missing question text in DB items for competency '{competency_name}'. Skipping.")
                     continue

                # Prepare context for LLM suggestion
                context_parts = [
                    f"Job Competency to Assess: {competency_name}",
                    f"Description: {comp_info.get('description', 'N/A')}",
                ]
                if job_analysis.get('title'):
                     context_parts.append(f"Job Title: {job_analysis['title']}")
                if job_analysis.get('responsibilities'):
                     resp_summary = ", ".join(job_analysis['responsibilities'][:2]) # First 2 responsibilities
                     context_parts.append(f"Key Responsibilities: {resp_summary}...")
                if resume_analysis.get('skills'):
                     skills_summary = ", ".join(resume_analysis['skills'].get('technical_skills', [])[:3]) # Top 3 tech skills
                     context_parts.append(f"Candidate Skills: {skills_summary}...")
                if resume_analysis.get('experience'):
                    exp_summary = resume_analysis['experience'][0].get('title', '') # Most recent title
                    context_parts.append(f"Candidate Recent Role: {exp_summary}")

                context = "\n".join(context_parts)

                # Construct prompt for LLM suggestion
                prompt = f"""
                Context:
                {context}

                Competency: {competency_name}

                Preset Questions:
                1. {q1_text}
                2. {q2_text}

                Based *only* on the provided context, which of these two questions (1 or 2) is slightly better suited to ask the candidate for this specific job and competency?

                Provide your response in JSON format:
                {{
                  "suggested_index": <1 or 2>,
                  "reason": "A brief explanation (1-2 sentences) why this question is a better fit given the context."
                }}
                """

                messages = [
                    {"role": "system", "content": "You are an expert interviewer selecting the most relevant question."},
                    {"role": "user", "content": prompt}
                ]

                suggested_index = 1 # Default suggestion
                reason = "Default suggestion."
                try:
                    llm_response_text = self._call_llm(messages, temperature=0.2) # Lower temp for focused choice
                    json_start = llm_response_text.find('{')
                    json_end = llm_response_text.rfind('}') + 1
                    json_str = llm_response_text[json_start:json_end]
                    llm_response = json.loads(json_str)
                    suggested_index = int(llm_response.get('suggested_index', 1))
                    reason = llm_response.get('reason', "LLM suggestion based on context.")
                    if suggested_index not in [1, 2]: suggested_index = 1 # Sanitize index

                except Exception as llm_err:
                    logger.error(f"Error getting/parsing LLM suggestion for {competency_name}: {llm_err}. Using default.")
                    # Keep default suggestion

                # Format the output set
                question_set = {
                    "competency_name": competency_name,
                    "questions": [
                        {"text": q1_text, "suggested": (suggested_index == 1), "reason": reason if suggested_index == 1 else ""},
                        {"text": q2_text, "suggested": (suggested_index == 2), "reason": reason if suggested_index == 2 else ""}
                    ]
                }
                competency_question_sets.append(question_set)

            except Exception as db_err:
                 logger.error(f"Error processing competency '{competency_name}': {db_err}")
                 continue # Skip to next competency on error

        logger.info(f"Prepared {len(competency_question_sets)} competency question sets.")
        return {"competency_question_sets": competency_question_sets}


    async def _get_resume_based_questions(self, data, **kwargs):
        """
        Generate 2-3 questions specifically targeting the candidate's resume using LLM.

        Args:
            data: Must contain 'resume_analysis'. Should contain 'job_analysis' for context.

        Returns:
            dict: List of resume-based questions.
        """
        logger.info("Generating resume-based questions...")
        resume_analysis = data.get('resume_analysis', {})
        job_analysis = data.get('job_analysis', {}) # Optional context

        if not resume_analysis:
            logger.warning("No resume analysis provided for generating resume-based questions.")
            return {"questions": []}

        # Construct prompt
        prompt_parts = ["Generate interview questions based *specifically* on the candidate's resume details."]

        # Add resume context
        prompt_parts.append("\nCandidate Resume Information:")
        if 'contact_information' in resume_analysis and 'name' in resume_analysis['contact_information']:
            prompt_parts.append(f"Name: {resume_analysis['contact_information']['name']}")
        if 'skills' in resume_analysis:
            skills = resume_analysis['skills']
            technical_skills = skills.get('technical_skills', [])
            soft_skills = skills.get('soft_skills', [])
            prompt_parts.append(f"Technical Skills: {', '.join(technical_skills)}")
            prompt_parts.append(f"Soft Skills: {', '.join(soft_skills)}")
        if 'experience' in resume_analysis:
            prompt_parts.append("Experience Highlights:")
            for job in resume_analysis['experience'][:3]: # Top 3 jobs
                company = job.get('company', 'Unknown Company')
                title = job.get('title', 'Unknown Title')
                duration = job.get('duration', '')
                summary = job.get('summary', '') # Use summary/achievements if available
                prompt_parts.append(f"- {title} at {company} ({duration}). Summary: {summary[:100]}...") # Add summary snippet
        if 'education' in resume_analysis:
             prompt_parts.append("Education:")
             for edu in resume_analysis['education']:
                  prompt_parts.append(f"- {edu.get('degree','')} in {edu.get('field','')} from {edu.get('school','')}")
        if 'projects' in resume_analysis:
            prompt_parts.append("Projects:")
            for proj in resume_analysis['projects'][:2]: # Top 2 projects
                prompt_parts.append(f"- {proj.get('name','')}: {proj.get('description','')[:100]}...")

        # Add optional job context
        if job_analysis.get('title'):
            prompt_parts.append(f"\nTarget Job Title: {job_analysis['title']}")

        prompt_parts.append("""
        Generate 3 open-ended questions that probe deeper into specific aspects mentioned in the candidate's resume above.
        Focus on their experiences, skills, projects, or education in relation to the target job if provided.
        Avoid generic questions. Ask about specific achievements, challenges, or learnings mentioned or implied in the resume.

        Return your questions in JSON format:
        {
            "questions": [
                {
                    "question": "resume-specific question text",
                    "focus": "briefly explain which part of the resume this question targets (e.g., 'Experience at Company X', 'Project Y', 'Skill Z')"
                }
            ]
        }
        """)

        prompt = "\n".join(prompt_parts)

        messages = [
            {"role": "system", "content": "You are an expert interviewer creating specific questions based on resume details."},
            {"role": "user", "content": prompt}
        ]

        try:
            questions_text = self._call_llm(messages)
            json_start = questions_text.find('{')
            json_end = questions_text.rfind('}') + 1
            json_str = questions_text[json_start:json_end]
            questions = json.loads(json_str)
            logger.info(f"Generated {len(questions.get('questions',[]))} resume-based questions.")

        except Exception as e:
            logger.error(f"Error generating/parsing resume-based questions: {str(e)}. Using fallback.")
            # Basic fallback if LLM fails
            fallback_q = "Can you elaborate on your experience listed under [Most Recent Job Title] on your resume?"
            if resume_analysis.get('experience'):
                fallback_q = f"Can you elaborate on your experience as {resume_analysis['experience'][0].get('title','your most recent role')} at {resume_analysis['experience'][0].get('company','your last company')}?"

            questions = {
                "questions": [
                    {"question": fallback_q, "focus": "Most recent experience"},
                    {"question": "Which project listed on your resume are you most proud of, and why?", "focus": "Projects"}
                ]
            }

        return questions

    # Remove old/unused methods like _generate_initial_questions, _generate_competency_questions (LLM based),
    # _generate_technical_questions, _select_preset_questions, _generate_introduction_questions (old name)
    # Keep _call_llm and other base methods inherited or used internally. 