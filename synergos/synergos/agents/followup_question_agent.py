import logging
import json
from synergos.agents.agent_base import AgentBase

logger = logging.getLogger(__name__)

class FollowupQuestionAgent(AgentBase):
    """
    Agent responsible for generating contextual follow-up questions
    based on candidate responses, missing STAR elements, or areas needing clarification.
    """
    
    async def process(self, data, task="generate_followup", **kwargs):
        """Process followup question request based on specified task"""
        method_map = {
            "generate_followup": self._generate_followup_questions,
            "generate_star_followup": self._generate_star_followup,
            "generate_clarification": self._generate_clarification_questions,
            "generate_contradiction_followup": self._generate_contradiction_followup
        }
        
        if task not in method_map:
            raise ValueError(f"Unknown task '{task}' for FollowupQuestionAgent")
        
        return await method_map[task](data, **kwargs)
    
    async def _generate_followup_questions(self, data, **kwargs):
        """
        Generate general follow-up questions based on a candidate's response
        
        Args:
            data: Must contain 'response' and optionally 'question' and 'context'
            
        Returns:
            dict: List of follow-up questions with explanations
        """
        response = data.get('response', '')
        question = data.get('question', '')
        context = data.get('context', {})
        
        if not response:
            return {
                "error": "No response provided for generating follow-up questions",
                "questions": []
            }
        
        # Construct prompt for follow-up questions
        messages = [
            {"role": "system", "content": "You are an expert interviewer skilled at asking insightful follow-up questions. Your job is to generate questions that help candidates elaborate on their responses and provide deeper insights."},
            {"role": "user", "content": f"""
            Please generate follow-up questions based on this candidate's response.
            
            Original Question: {question}
            
            Candidate's Response: {response}
            
            Additional Context: {json.dumps(context) if context else "None"}
            
            Generate 2-3 follow-up questions that:
            1. Encourage the candidate to elaborate on interesting points
            2. Ask for specific examples or details if they were vague
            3. Explore the candidate's thought process or decision-making
            4. Probe deeper into their experiences, challenges, or results
            5. Are open-ended and cannot be answered with just "yes" or "no"
            
            For each question, provide a brief explanation of why you're asking it.
            
            Return your questions in JSON format with the following structure:
            {{
                "questions": [
                    {{
                        "question": "follow-up question text",
                        "reasoning": "brief explanation of why this question is valuable"
                    }}
                ]
            }}
            """}
        ]
        
        # Call LLM for follow-up questions
        questions_text = self._call_llm(messages)
        
        # Parse result
        try:
            # Extract JSON from the response
            json_start = questions_text.find('{')
            json_end = questions_text.rfind('}') + 1
            json_str = questions_text[json_start:json_end]
            questions = json.loads(json_str)
        except Exception as e:
            logger.error(f"Error parsing follow-up questions: {str(e)}")
            questions = {
                "questions": [
                    {
                        "question": "Can you tell me more about that experience?",
                        "reasoning": "Generic follow-up to encourage elaboration"
                    }
                ]
            }
        
        return questions
    
    async def _generate_star_followup(self, data, **kwargs):
        """
        Generate follow-up questions targeting missing STAR elements
        
        Args:
            data: Must contain 'response', 'question', and 'star_analysis'
            
        Returns:
            dict: List of STAR-focused follow-up questions
        """
        response = data.get('response', '')
        question = data.get('question', '')
        star_analysis = data.get('star_analysis', {})
        
        if not response or not star_analysis:
            return {
                "error": "Missing response or STAR analysis for generating STAR follow-up questions",
                "questions": []
            }
        
        # Extract missing elements from STAR analysis
        missing_elements = star_analysis.get('missing_elements', [])
        star_components = star_analysis.get('star_components', {})
        
        if not missing_elements:
            return {
                "questions": [
                    {
                        "question": "That was a comprehensive answer. Is there anything else you'd like to add about the results you achieved?",
                        "reasoning": "General follow-up for a complete STAR response"
                    }
                ]
            }
        
        # Construct prompt for STAR-focused follow-up questions
        messages = [
            {"role": "system", "content": "You are an expert interviewer specializing in the STAR technique. Your job is to ask follow-up questions that help candidates provide complete STAR responses."},
            {"role": "user", "content": f"""
            Please generate follow-up questions focusing on missing STAR elements.
            
            Original Question: {question}
            
            Candidate's Response: {response}
            
            STAR Analysis:
            {json.dumps(star_components, indent=2)}
            
            Missing or Weak Elements:
            {', '.join(missing_elements)}
            
            For each missing or weak STAR element, generate a specific follow-up question that:
            1. Guides the candidate to address that specific element
            2. Is phrased in a natural, conversational way
            3. Encourages detailed, specific responses
            
            Return your questions in JSON format with the following structure:
            {{
                "questions": [
                    {{
                        "element": "situation|task|action|result",
                        "question": "follow-up question text",
                        "reasoning": "brief explanation of why this question targets the missing element"
                    }}
                ]
            }}
            """}
        ]
        
        # Call LLM for STAR-focused follow-up questions
        questions_text = self._call_llm(messages)
        
        # Parse result
        try:
            # Extract JSON from the response
            json_start = questions_text.find('{')
            json_end = questions_text.rfind('}') + 1
            json_str = questions_text[json_start:json_end]
            questions = json.loads(json_str)
        except Exception as e:
            logger.error(f"Error parsing STAR follow-up questions: {str(e)}")
            questions = {
                "questions": [
                    {
                        "element": missing_elements[0] if missing_elements else "general",
                        "question": f"Could you tell me more about the {missing_elements[0] if missing_elements else 'situation'}?",
                        "reasoning": f"Addressing missing {missing_elements[0] if missing_elements else 'elements'} in STAR response"
                    }
                ]
            }
        
        return questions
    
    async def _generate_clarification_questions(self, data, **kwargs):
        """
        Generate questions to clarify vague or ambiguous parts of a response
        
        Args:
            data: Must contain 'response' and 'question'
            
        Returns:
            dict: List of clarification questions
        """
        response = data.get('response', '')
        question = data.get('question', '')
        
        if not response:
            return {
                "error": "No response provided for generating clarification questions",
                "questions": []
            }
        
        # Construct prompt for clarification questions
        messages = [
            {"role": "system", "content": "You are an expert interviewer skilled at identifying vague or ambiguous statements in candidate responses and asking clarifying questions. Your job is to pinpoint areas needing clarification and generate targeted questions."},
            {"role": "user", "content": f"""
            Please analyze this candidate response and generate questions to clarify any vague or ambiguous parts.
            
            Original Question: {question}
            
            Candidate's Response: {response}
            
            1. Identify 2-3 statements or claims that are vague, lack specificity, or could be interpreted in multiple ways
            2. For each one, generate a clarification question that:
               - Addresses the specific ambiguity
               - Is phrased in a friendly, non-confrontational way
               - Encourages the candidate to provide concrete details or examples
            
            Return your questions in JSON format with the following structure:
            {{
                "unclear_points": [
                    {{
                        "statement": "excerpt from response that is unclear",
                        "issue": "brief description of why this is vague or needs clarification",
                        "question": "clarification question"
                    }}
                ]
            }}
            """}
        ]
        
        # Call LLM for clarification questions
        questions_text = self._call_llm(messages)
        
        # Parse result
        try:
            # Extract JSON from the response
            json_start = questions_text.find('{')
            json_end = questions_text.rfind('}') + 1
            json_str = questions_text[json_start:json_end]
            clarifications = json.loads(json_str)
        except Exception as e:
            logger.error(f"Error parsing clarification questions: {str(e)}")
            clarifications = {
                "unclear_points": [
                    {
                        "statement": "Part of the response that seems vague",
                        "issue": "Lacks specificity",
                        "question": "Could you provide more specific details about that?"
                    }
                ]
            }
        
        return clarifications
    
    async def _generate_contradiction_followup(self, data, **kwargs):
        """
        Generate follow-up questions for contradictory statements
        
        Args:
            data: Must contain 'contradictions'
            
        Returns:
            dict: List of questions addressing contradictions
        """
        contradictions = data.get('contradictions', [])
        
        if not contradictions:
            return {
                "error": "No contradictions provided for generating follow-up questions",
                "questions": []
            }
        
        # Construct prompt for contradiction follow-up questions
        messages = [
            {"role": "system", "content": "You are an expert interviewer skilled at addressing inconsistencies in candidate responses in a tactful way. Your job is to generate questions that help clarify apparent contradictions without making the candidate feel defensive."},
            {"role": "user", "content": f"""
            Please generate follow-up questions for these apparent contradictions in the candidate's responses.
            
            Contradictions:
            {json.dumps(contradictions, indent=2)}
            
            For each contradiction, generate a question that:
            1. Addresses the inconsistency without directly calling it a contradiction
            2. Is phrased in a curious, non-accusatory way
            3. Gives the candidate an opportunity to reconcile or explain the apparent inconsistency
            4. Maintains a positive, supportive interview atmosphere
            
            Return your questions in JSON format with the following structure:
            {{
                "questions": [
                    {{
                        "contradiction": "brief description of the contradiction",
                        "question": "tactful follow-up question",
                        "reasoning": "explanation of how this question addresses the contradiction"
                    }}
                ]
            }}
            """}
        ]
        
        # Call LLM for contradiction follow-up questions
        questions_text = self._call_llm(messages)
        
        # Parse result
        try:
            # Extract JSON from the response
            json_start = questions_text.find('{')
            json_end = questions_text.rfind('}') + 1
            json_str = questions_text[json_start:json_end]
            questions = json.loads(json_str)
        except Exception as e:
            logger.error(f"Error parsing contradiction follow-up questions: {str(e)}")
            questions = {
                "questions": [
                    {
                        "contradiction": "General inconsistency",
                        "question": "I'd like to understand more about how these experiences connect. Could you elaborate?",
                        "reasoning": "General question to address inconsistency without being confrontational"
                    }
                ]
            }
        
        return questions 