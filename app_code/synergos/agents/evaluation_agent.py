import logging
import json
from synergos.agents.agent_base import AgentBase

logger = logging.getLogger(__name__)

class EvaluationAgent(AgentBase):
    """
    Agent responsible for comprehensive post-interview evaluation.
    Analyzes interview responses against STAR format, job requirements,
    and competency expectations to generate detailed assessment reports.
    Enhanced with Nova Sonic emotional analysis capabilities.
    Also detects contradictions, unclear responses, and suggests follow-up questions.
    """
    
    async def process(self, data, task="evaluate_interview", **kwargs):
        """Process evaluation request based on specified task"""
        method_map = {
            "evaluate_interview": self._evaluate_interview,
            "evaluate_star_format": self._evaluate_star_format,
            "evaluate_competencies": self._evaluate_competencies,
            "generate_summary_report": self._generate_summary_report,
            "comprehensive_evaluation": self._comprehensive_evaluation,
            "evaluate_emotional_response": self._evaluate_emotional_response,
            "analyze_speech_confidence": self._analyze_speech_confidence,
            "generate_emotional_pattern_report": self._generate_emotional_pattern_report,
            "detect_contradictions": self._detect_contradictions,
            "identify_unclear_responses": self._identify_unclear_responses,
            "suggest_followup_questions": self._suggest_followup_questions
        }
        
        if task not in method_map:
            raise ValueError(f"Unknown task '{task}' for EvaluationAgent")
        
        return await method_map[task](data, **kwargs)
    
    async def _evaluate_interview(self, data, **kwargs):
        """
        Evaluate entire interview, including all questions and responses
        
        Args:
            data: Must contain 'transcript' or 'responses' and 'questions'
            
        Returns:
            dict: Interview evaluation results
        """
        # Extract data
        transcript = data.get('transcript')
        responses = data.get('responses', [])
        questions = data.get('questions', [])
        emotional_data = data.get('emotional_data', [])  # Nova Sonic emotional analysis
        
        # If only transcript provided, extract Q&A
        if transcript and not (responses and questions):
            # Logic to extract Q&A from transcript would go here
            pass
        
        # Evaluate each response individually
        response_evaluations = []
        for idx, response in enumerate(responses):
            question = questions[idx] if idx < len(questions) else None
            
            # Get emotional data for this response if available
            response_emotional_data = None
            if idx < len(emotional_data):
                response_emotional_data = emotional_data[idx]
                
            eval_result = await self._evaluate_single_response(
                response, 
                question, 
                emotional_data=response_emotional_data
            )
            response_evaluations.append(eval_result)
        
        # Generate overall interview assessment
        star_evaluation = await self._evaluate_star_format({"responses": responses})
        competency_evaluation = await self._evaluate_competencies({
            "responses": responses, 
            "job_requirements": data.get('job_requirements'),
            "emotional_data": emotional_data
        })
        
        # Generate emotional pattern report if emotional data available
        emotional_patterns = None
        if emotional_data:
            emotional_patterns = await self._generate_emotional_pattern_report({
                "emotional_data": emotional_data,
                "questions": questions,
                "responses": responses
            })
        
        # Detect contradictions across all responses
        contradictions = await self._detect_contradictions({
            "responses": responses,
            "questions": questions
        })
        
        # Identify unclear or vague responses
        unclear_responses = await self._identify_unclear_responses({
            "responses": responses,
            "questions": questions
        })
        
        # Suggest follow-up questions
        followup_questions = await self._suggest_followup_questions({
            "responses": responses,
            "questions": questions,
            "contradictions": contradictions,
            "unclear_responses": unclear_responses,
            "star_evaluation": star_evaluation
        })
        
        # Compile results
        evaluation = {
            "overall_score": self._calculate_overall_score(response_evaluations),
            "response_evaluations": response_evaluations,
            "star_format_adherence": star_evaluation,
            "competency_alignment": competency_evaluation,
            "strengths": self._identify_strengths(response_evaluations),
            "areas_for_improvement": self._identify_areas_for_improvement(response_evaluations),
            "emotional_assessment": emotional_patterns,
            "contradictions": contradictions,
            "unclear_responses": unclear_responses,
            "suggested_followup_questions": followup_questions,
            "overall_recommendation": self._generate_recommendation(
                response_evaluations, 
                star_evaluation, 
                competency_evaluation,
                emotional_patterns,
                contradictions,
                unclear_responses
            )
        }
        
        return evaluation
    
    async def _evaluate_single_response(self, response, question, emotional_data=None):
        """Evaluate a single response to a question, now with emotional data"""
        # Construct prompt for analysis, including emotional data if available
        emotional_context = ""
        if emotional_data:
            emotional_context = f"""
            Emotional Analysis Data:
            {json.dumps(emotional_data, indent=2)}
            
            Consider this emotional data in your evaluation. Pay special attention to:
            - Confidence markers when discussing technical abilities
            - Hesitation patterns when describing experience
            - Emotional tone shifts during the response
            - Prosody indicators like speaking pace and emphasis
            """
        
        messages = [
            {"role": "system", "content": "You are an expert interview evaluator specializing in STAR format analysis with emotional intelligence capabilities."},
            {"role": "user", "content": f"""
            Please evaluate this interview response to the question provided.
            
            Question: {question}
            
            Response: {response}
            {emotional_context}
            
            Evaluate the following:
            1. STAR Format: Does the response include Situation, Task, Action, and Result elements?
            2. Completeness: Did the candidate fully answer the question?
            3. Relevance: How relevant was the response to the question?
            4. Specificity: Did the candidate provide specific examples?
            5. Communication: How clearly was the response articulated?
            {f"6. Emotional Congruence: Did the emotional tone match the content of the response?" if emotional_data else ""}
            {f"7. Confidence Assessment: Did the candidate display confidence when discussing key achievements?" if emotional_data else ""}
            
            Provide a score from 1-10 for each aspect and brief justification.
            Return your analysis in JSON format.
            """}
        ]
        
        # Call LLM for response evaluation
        evaluation_text = self._call_llm(messages)
        
        # Parse result
        try:
            # Extract JSON from the response
            json_start = evaluation_text.find('{')
            json_end = evaluation_text.rfind('}') + 1
            json_str = evaluation_text[json_start:json_end]
            evaluation = json.loads(json_str)
        except Exception as e:
            logger.error(f"Error parsing response evaluation: {str(e)}")
            evaluation = {
                "star_format": {"score": 0, "feedback": "Error analyzing response"},
                "completeness": {"score": 0, "feedback": "Error analyzing response"},
                "relevance": {"score": 0, "feedback": "Error analyzing response"},
                "specificity": {"score": 0, "feedback": "Error analyzing response"},
                "communication": {"score": 0, "feedback": "Error analyzing response"},
                "overall": {"score": 0, "feedback": "Error analyzing response"}
            }
            
            # Add emotional fields if emotional data was provided
            if emotional_data:
                evaluation["emotional_congruence"] = {"score": 0, "feedback": "Error analyzing emotional data"}
                evaluation["confidence_assessment"] = {"score": 0, "feedback": "Error analyzing confidence"}
        
        # Add raw emotional data for reference
        if emotional_data:
            evaluation["raw_emotional_data"] = emotional_data
            
        return evaluation
    
    async def _evaluate_star_format(self, data, **kwargs):
        """
        Evaluate how well responses adhere to the STAR format
        
        Args:
            data: Must contain 'responses'
            
        Returns:
            dict: STAR format evaluation results
        """
        responses = data.get('responses', [])
        emotional_data = data.get('emotional_data', [])
        
        # Add emotional context if available
        emotional_context = ""
        if emotional_data:
            emotional_context = f"""
            Emotional Analysis Data:
            {json.dumps(emotional_data, indent=2)}
            
            Use this emotional data to enhance your analysis. Pay special attention to:
            - Confidence levels when describing actions taken
            - Emotional shifts when discussing results
            - Hesitation patterns when explaining situations
            """
        
        # Construct prompt for STAR analysis
        messages = [
            {"role": "system", "content": "You are an expert in evaluating interview responses using the STAR method."},
            {"role": "user", "content": f"""
            Please analyze these interview responses for STAR method adherence.
            
            Responses:
            {json.dumps(responses, indent=2)}
            {emotional_context}
            
            For each response, identify:
            1. Situation: Was a specific situation clearly described? (score 1-10)
            2. Task: Was the candidate's specific responsibility or goal clearly defined? (score 1-10)
            3. Action: Were specific actions the candidate took clearly described? (score 1-10)
            4. Result: Were concrete outcomes or achievements clearly stated? (score 1-10)
            
            Provide an overall STAR adherence score (1-10) and recommendations for improvement.
            {f"Also note any emotional indicators that enhance or detract from the STAR narrative." if emotional_data else ""}
            
            Return your analysis in JSON format.
            """}
        ]
        
        # Call LLM for STAR analysis
        star_result_text = self._call_llm(messages)
        
        # Parse result
        try:
            # Extract JSON from the response
            json_start = star_result_text.find('{')
            json_end = star_result_text.rfind('}') + 1
            json_str = star_result_text[json_start:json_end]
            star_evaluation = json.loads(json_str)
        except Exception as e:
            logger.error(f"Error parsing STAR evaluation: {str(e)}")
            star_evaluation = {
                "overall_star_score": 0,
                "situation_score": 0,
                "task_score": 0,
                "action_score": 0,
                "result_score": 0,
                "recommendations": "Unable to analyze STAR format adherence"
            }
            
            # Add emotional field if emotional data was provided
            if emotional_data:
                star_evaluation["emotional_indicators"] = "Unable to analyze emotional indicators"
        
        return star_evaluation
    
    async def _evaluate_competencies(self, data, **kwargs):
        """
        Evaluate responses against required competencies and job requirements
        
        Args:
            data: Must contain 'responses' and 'job_requirements'
            
        Returns:
            dict: Competency evaluation results
        """
        responses = data.get('responses', [])
        job_requirements = data.get('job_requirements', {})
        competencies = data.get('required_competencies', [])
        emotional_data = data.get('emotional_data', [])
        
        # Add emotional context if available
        emotional_context = ""
        if emotional_data:
            emotional_context = f"""
            Emotional Analysis Data:
            {json.dumps(emotional_data, indent=2)}
            
            Use this emotional data to enhance your competency assessment. Pay special attention to:
            - Confidence levels when discussing technical competencies
            - Emotional engagement when describing past experiences
            - Consistent emotional patterns that may indicate strengths or weaknesses
            """
        
        # Construct prompt for competency analysis
        messages = [
            {"role": "system", "content": "You are an expert in evaluating job candidates against required competencies."},
            {"role": "user", "content": f"""
            Please analyze these interview responses against the job requirements and competencies.
            
            Responses:
            {json.dumps(responses, indent=2)}
            
            Job Requirements:
            {json.dumps(job_requirements, indent=2)}
            
            Required Competencies:
            {json.dumps(competencies, indent=2)}
            {emotional_context}
            
            For each competency, evaluate:
            1. Evidence: What evidence in the responses demonstrates this competency?
            2. Strength: How strongly is this competency demonstrated? (score 1-10)
            3. Gaps: What aspects of this competency are missing or weak?
            {f"4. Emotional Alignment: Does the candidate's emotional state align with discussing this competency?" if emotional_data else ""}
            
            Provide an overall competency alignment score (1-10) and summary.
            Return your analysis in JSON format.
            """}
        ]
        
        # Call LLM for competency analysis
        competency_result_text = self._call_llm(messages)
        
        # Parse result
        try:
            # Extract JSON from the response
            json_start = competency_result_text.find('{')
            json_end = competency_result_text.rfind('}') + 1
            json_str = competency_result_text[json_start:json_end]
            competency_evaluation = json.loads(json_str)
        except Exception as e:
            logger.error(f"Error parsing competency evaluation: {str(e)}")
            competency_evaluation = {
                "overall_competency_score": 0,
                "competency_evaluations": [],
                "summary": "Unable to analyze competency alignment"
            }
        
        return competency_evaluation
    
    async def _evaluate_emotional_response(self, data, **kwargs):
        """
        Evaluate emotional aspects of a response using Nova Sonic data
        
        Args:
            data: Must contain 'response' and 'emotional_data'
            
        Returns:
            dict: Emotional evaluation results
        """
        response = data.get('response', '')
        emotional_data = data.get('emotional_data', {})
        question = data.get('question', '')
        
        if not emotional_data:
            return {
                "error": "No emotional data provided",
                "emotional_assessment": {
                    "authenticity_score": 0,
                    "confidence_score": 0,
                    "engagement_score": 0,
                    "emotional_congruence_score": 0,
                    "overall_emotional_score": 0,
                    "assessment": "No emotional data available for assessment"
                }
            }
        
        # Construct prompt for emotional analysis
        messages = [
            {"role": "system", "content": "You are an expert in evaluating emotional aspects of interview responses."},
            {"role": "user", "content": f"""
            Please analyze the emotional aspects of this interview response.
            
            Question: {question}
            
            Response: {response}
            
            Emotional Data:
            {json.dumps(emotional_data, indent=2)}
            
            Evaluate the following:
            1. Authenticity: Does the emotional response seem genuine? (score 1-10)
            2. Confidence: Does the candidate display appropriate confidence? (score 1-10)
            3. Engagement: Is the candidate emotionally engaged with the topic? (score 1-10)
            4. Emotional Congruence: Does the emotional tone match the content? (score 1-10)
            5. Stress Indicators: Is there evidence of undue stress or anxiety? (score 1-10)
            
            Provide an overall emotional assessment score (1-10) and summary.
            Return your analysis in JSON format.
            """}
        ]
        
        # Call LLM for emotional analysis
        emotional_result_text = self._call_llm(messages)
        
        # Parse result
        try:
            # Extract JSON from the response
            json_start = emotional_result_text.find('{')
            json_end = emotional_result_text.rfind('}') + 1
            json_str = emotional_result_text[json_start:json_end]
            emotional_evaluation = json.loads(json_str)
        except Exception as e:
            logger.error(f"Error parsing emotional evaluation: {str(e)}")
            emotional_evaluation = {
                "authenticity_score": 0,
                "confidence_score": 0,
                "engagement_score": 0,
                "emotional_congruence_score": 0,
                "stress_indicators_score": 0,
                "overall_emotional_score": 0,
                "assessment": "Error analyzing emotional response"
            }
        
        return {
            "emotional_assessment": emotional_evaluation,
            "raw_emotional_data": emotional_data
        }
    
    async def _analyze_speech_confidence(self, data, **kwargs):
        """
        Analyze confidence patterns in speech using Nova Sonic data
        
        Args:
            data: Must contain 'emotional_data' with prosody and confidence markers
            
        Returns:
            dict: Confidence analysis results
        """
        emotional_data = data.get('emotional_data', {})
        topic = data.get('topic', '')  # The topic being discussed (e.g., "technical skills")
        
        if not emotional_data:
            return {
                "error": "No emotional data provided",
                "confidence_assessment": {
                    "overall_confidence_score": 0,
                    "confidence_pattern": "No data available",
                    "hesitation_analysis": "No data available",
                    "assessment": "No emotional data available for assessment"
                }
            }
        
        # Construct prompt for confidence analysis
        messages = [
            {"role": "system", "content": "You are an expert in analyzing speech confidence patterns in interviews."},
            {"role": "user", "content": f"""
            Please analyze the confidence patterns in this speech data.
            
            Topic: {topic}
            
            Emotional Data:
            {json.dumps(emotional_data, indent=2)}
            
            Analyze the following:
            1. Overall Confidence: How confident does the speaker sound? (score 1-10)
            2. Confidence Pattern: Is confidence consistent or does it vary by topic?
            3. Hesitation Analysis: Are there specific patterns of hesitation?
            4. Emphasis Patterns: What words or concepts receive emphasis?
            5. Authenticity Assessment: Does the confidence feel genuine?
            
            Provide an overall confidence assessment and summary.
            Return your analysis in JSON format.
            """}
        ]
        
        # Call LLM for confidence analysis
        confidence_result_text = self._call_llm(messages)
        
        # Parse result
        try:
            # Extract JSON from the response
            json_start = confidence_result_text.find('{')
            json_end = confidence_result_text.rfind('}') + 1
            json_str = confidence_result_text[json_start:json_end]
            confidence_analysis = json.loads(json_str)
        except Exception as e:
            logger.error(f"Error parsing confidence analysis: {str(e)}")
            confidence_analysis = {
                "overall_confidence_score": 0,
                "confidence_pattern": "Error analyzing confidence",
                "hesitation_analysis": "Error analyzing hesitations",
                "emphasis_patterns": "Error analyzing emphasis",
                "authenticity_assessment": "Error analyzing authenticity",
                "assessment": "Error analyzing confidence patterns"
            }
        
        return {
            "confidence_assessment": confidence_analysis,
            "raw_emotional_data": emotional_data
        }
    
    async def _generate_emotional_pattern_report(self, data, **kwargs):
        """
        Generate a report on emotional patterns throughout the interview
        
        Args:
            data: Must contain 'emotional_data' array for multiple responses
            
        Returns:
            dict: Emotional pattern report
        """
        emotional_data = data.get('emotional_data', [])
        questions = data.get('questions', [])
        responses = data.get('responses', [])
        
        if not emotional_data:
            return {
                "error": "No emotional data provided",
                "emotional_patterns": {
                    "overall_emotional_assessment": "No data available",
                    "patterns": [],
                    "insights": "No emotional data available for assessment"
                }
            }
        
        # Prepare questions and responses context
        qa_context = []
        for i in range(min(len(questions), len(responses))):
            qa_context.append({
                "question": questions[i],
                "response_summary": responses[i][:200] + "..." if len(responses[i]) > 200 else responses[i]
            })
        
        # Construct prompt for emotional pattern analysis
        messages = [
            {"role": "system", "content": "You are an expert in analyzing emotional patterns in interview responses."},
            {"role": "user", "content": f"""
            Please analyze the emotional patterns throughout this interview.
            
            Questions and Responses:
            {json.dumps(qa_context, indent=2)}
            
            Emotional Data Sequence:
            {json.dumps(emotional_data, indent=2)}
            
            Analyze the following:
            1. Overall Emotional Pattern: How did emotions evolve throughout the interview?
            2. Topic-Specific Emotions: Were certain topics associated with specific emotions?
            3. Confidence Patterns: How did confidence vary across different questions?
            4. Stress Indicators: Were there signs of stress or discomfort on particular topics?
            5. Authenticity Assessment: Which responses seemed most and least authentic emotionally?
            
            Provide an overall assessment of emotional patterns and what they might indicate.
            Return your analysis in JSON format.
            """}
        ]
        
        # Call LLM for emotional pattern analysis
        pattern_result_text = self._call_llm(messages)
        
        # Parse result
        try:
            # Extract JSON from the response
            json_start = pattern_result_text.find('{')
            json_end = pattern_result_text.rfind('}') + 1
            json_str = pattern_result_text[json_start:json_end]
            pattern_analysis = json.loads(json_str)
        except Exception as e:
            logger.error(f"Error parsing emotional pattern analysis: {str(e)}")
            pattern_analysis = {
                "overall_emotional_assessment": "Error analyzing emotional patterns",
                "patterns": [],
                "insights": "Error generating emotional pattern insights"
            }
        
        return {
            "emotional_patterns": pattern_analysis
        }
    
    async def _generate_summary_report(self, data, **kwargs):
        """
        Generate comprehensive interview summary report for interviewer
        
        Args:
            data: Must contain evaluation results and interview data
            
        Returns:
            dict: Summary report
        """
        interview_data = data.get('interview_data', {})
        evaluation_results = data.get('evaluation_results', {})
        emotional_data = data.get('emotional_data', [])
        
        # Add emotional context if available
        emotional_context = ""
        if emotional_data or 'emotional_assessment' in evaluation_results:
            emotional_context = """
            Be sure to incorporate the emotional analysis in your summary, including:
            - How confidence varied by topic
            - Authenticity markers in the responses
            - Emotional congruence with content
            - Stress or hesitation patterns and what they might indicate
            """
        
        # Construct prompt for summary report
        messages = [
            {"role": "system", "content": "You are an expert in creating concise yet comprehensive interview summary reports."},
            {"role": "user", "content": f"""
            Please create a comprehensive post-interview summary report based on the interview data and evaluation results.
            
            Interview Data:
            {json.dumps(interview_data, indent=2)}
            
            Evaluation Results:
            {json.dumps(evaluation_results, indent=2)}
            {emotional_context}
            
            The report should include:
            1. Executive Summary: Brief overview of candidate and overall assessment
            2. STAR Format Analysis: How well the candidate structured responses
            3. Competency Assessment: Evaluation against key competencies
            4. Strengths and Weaknesses: Key strengths and areas for improvement
            5. Job Fit: Assessment of fit with the role requirements
            6. Recommendation: Clear hiring recommendation
            7. Follow-up Questions: Suggested questions for future interviews if needed
            {f"8. Emotional Intelligence Assessment: Analysis of emotional patterns and authenticity" if emotional_data or 'emotional_assessment' in evaluation_results else ""}
            
            Make the report concise but informative for a busy hiring manager.
            Return your report in JSON format.
            """}
        ]
        
        # Call LLM for summary generation
        report_text = self._call_llm(messages)
        
        # Parse result
        try:
            # Extract JSON from the response
            json_start = report_text.find('{')
            json_end = report_text.rfind('}') + 1
            json_str = report_text[json_start:json_end]
            summary_report = json.loads(json_str)
        except Exception as e:
            logger.error(f"Error parsing summary report: {str(e)}")
            summary_report = {
                "executive_summary": "Error generating summary report",
                "recommendation": "Unable to provide recommendation"
            }
        
        return summary_report
    
    async def _comprehensive_evaluation(self, data, **kwargs):
        """
        Perform comprehensive evaluation combining all analysis types
        
        Args:
            data: Must contain complete interview data, job requirements, etc.
            
        Returns:
            dict: Comprehensive evaluation results
        """
        # Extract emotional data if available
        emotional_data = data.get('emotional_data', [])
        
        # Run all evaluation types
        interview_eval = await self._evaluate_interview(data)
        star_eval = await self._evaluate_star_format(data)
        competency_eval = await self._evaluate_competencies(data)
        
        # Run emotional pattern analysis if emotional data is available
        emotional_patterns = None
        if emotional_data:
            emotional_patterns = await self._generate_emotional_pattern_report(data)
        
        # Combine results for summary report
        evaluation_results = {
            "interview_evaluation": interview_eval,
            "star_format_evaluation": star_eval,
            "competency_evaluation": competency_eval
        }
        
        # Add emotional patterns if available
        if emotional_patterns:
            evaluation_results["emotional_patterns"] = emotional_patterns
        
        # Generate summary report
        report_data = {
            "interview_data": data,
            "evaluation_results": evaluation_results
        }
        
        # Add emotional data if available
        if emotional_data:
            report_data["emotional_data"] = emotional_data
            
        report = await self._generate_summary_report(report_data)
        
        # Return comprehensive results
        return {
            "evaluation_details": evaluation_results,
            "summary_report": report
        }
    
    def _calculate_overall_score(self, response_evaluations):
        """Calculate overall score from individual response evaluations"""
        if not response_evaluations:
            return 0
        
        total = 0
        count = 0
        for eval in response_evaluations:
            if 'overall' in eval and 'score' in eval['overall']:
                total += eval['overall']['score']
                count += 1
        
        return round(total / count, 1) if count > 0 else 0
    
    def _identify_strengths(self, response_evaluations):
        """Identify candidate strengths from response evaluations"""
        strengths = []
        high_score_threshold = 7
        
        # Analyze high-scoring aspects across responses
        for eval in response_evaluations:
            # Check STAR format elements
            for aspect in ['star_format', 'completeness', 'relevance', 'specificity', 'communication', 
                          'emotional_congruence', 'confidence_assessment']:
                if aspect in eval and 'score' in eval[aspect] and eval[aspect]['score'] >= high_score_threshold:
                    strength = f"Strong {aspect.replace('_', ' ')}: {eval[aspect].get('feedback', '')}"
                    if strength not in strengths:
                        strengths.append(strength)
        
        return strengths
    
    def _identify_areas_for_improvement(self, response_evaluations):
        """Identify areas for improvement from response evaluations"""
        improvement_areas = []
        low_score_threshold = 5
        
        # Analyze low-scoring aspects across responses
        for eval in response_evaluations:
            # Check STAR format elements
            for aspect in ['star_format', 'completeness', 'relevance', 'specificity', 'communication',
                         'emotional_congruence', 'confidence_assessment']:
                if aspect in eval and 'score' in eval[aspect] and eval[aspect]['score'] <= low_score_threshold:
                    area = f"Needs improvement in {aspect.replace('_', ' ')}: {eval[aspect].get('feedback', '')}"
                    if area not in improvement_areas:
                        improvement_areas.append(area)
        
        return improvement_areas
    
    def _generate_recommendation(self, response_evaluations, star_evaluation, 
                               competency_evaluation, emotional_patterns=None,
                               contradictions=None, unclear_responses=None):
        """Generate overall recommendation based on all evaluation aspects"""
        # Calculate scores
        overall_score = self._calculate_overall_score(response_evaluations)
        star_score = star_evaluation.get('overall_star_score', 0)
        competency_score = competency_evaluation.get('overall_competency_score', 0)
        
        # Emotional indicators if available
        emotional_factors = ""
        if emotional_patterns:
            emotional_score = emotional_patterns.get('overall_emotional_score', 0)
            emotional_factors = f" Emotional assessment indicates a score of {emotional_score}/10."
        
        # Check for contradictions and unclear responses
        credibility_issues = ""
        if contradictions and len(contradictions) > 0:
            credibility_issues += f" Found {len(contradictions)} contradictions in responses."
        
        if unclear_responses and len(unclear_responses) > 0:
            credibility_issues += f" Identified {len(unclear_responses)} unclear or vague responses requiring clarification."
        
        # Generate recommendation text
        if overall_score >= 8:
            recommendation = f"Strong candidate with an overall score of {overall_score}/10. " + \
                            f"Excellent STAR format adherence ({star_score}/10) and " + \
                            f"competency alignment ({competency_score}/10).{emotional_factors}{credibility_issues} " + \
                            "Recommended for next round."
        elif overall_score >= 6:
            recommendation = f"Decent candidate with an overall score of {overall_score}/10. " + \
                            f"Good STAR format adherence ({star_score}/10) and " + \
                            f"competency alignment ({competency_score}/10).{emotional_factors}{credibility_issues} " + \
                            "Consider for next round after addressing concerns."
        else:
            recommendation = f"Below expectations with an overall score of {overall_score}/10. " + \
                            f"Poor STAR format adherence ({star_score}/10) and " + \
                            f"competency alignment ({competency_score}/10).{emotional_factors}{credibility_issues} " + \
                            "Not recommended to proceed."
        
        return recommendation
    
    async def _detect_contradictions(self, data, **kwargs):
        """
        Detect contradictions across all responses
        
        Args:
            data: Must contain 'responses' and 'questions'
            
        Returns:
            list: Detected contradictions with details
        """
        responses = data.get('responses', [])
        questions = data.get('questions', [])
        
        if len(responses) <= 1:
            # Need at least two responses to detect contradictions
            return []
        
        # Combine questions and responses for context
        qa_pairs = []
        for i in range(min(len(questions), len(responses))):
            qa_pairs.append({
                "question": questions[i],
                "response": responses[i],
                "index": i
            })
        
        # Construct prompt for contradiction detection
        messages = [
            {"role": "system", "content": "You are an expert interview evaluator specialized in detecting contradictions and inconsistencies in candidate responses."},
            {"role": "user", "content": f"""
            Please analyze the following interview questions and responses to identify any contradictions or inconsistencies.
            
            Q&A Pairs:
            {json.dumps(qa_pairs, indent=2)}
            
            Your task:
            1. Compare all responses carefully to find contradictions or inconsistencies
            2. Focus on factual contradictions (e.g., years of experience, roles, responsibilities)
            3. Note inconsistencies in described skills, experiences, or achievements
            4. Look for changes in the candidate's claims across different questions
            
            Return your findings in JSON format with the following structure:
            {{
                "contradictions": [
                    {{
                        "description": "Brief description of the contradiction",
                        "response1": {{
                            "index": response_index_number,
                            "excerpt": "relevant excerpt from the response"
                        }},
                        "response2": {{
                            "index": response_index_number,
                            "excerpt": "relevant excerpt from the response"
                        }},
                        "severity": "high|medium|low",
                        "explanation": "Explanation of why these statements are contradictory"
                    }}
                ]
            }}
            
            If no contradictions are found, return an empty list.
            """}
        ]
        
        # Call LLM for contradiction detection
        result_text = self._call_llm(messages)
        
        # Parse result
        try:
            # Extract JSON from the response
            json_start = result_text.find('{')
            json_end = result_text.rfind('}') + 1
            json_str = result_text[json_start:json_end]
            result = json.loads(json_str)
            contradictions = result.get('contradictions', [])
        except Exception as e:
            logger.error(f"Error parsing contradiction detection results: {str(e)}")
            contradictions = []
        
        return contradictions
    
    async def _identify_unclear_responses(self, data, **kwargs):
        """
        Identify unclear, vague, or ambiguous responses
        
        Args:
            data: Must contain 'responses' and 'questions'
            
        Returns:
            list: Unclear responses with details
        """
        responses = data.get('responses', [])
        questions = data.get('questions', [])
        
        if not responses:
            return []
        
        # Combine questions and responses for context
        qa_pairs = []
        for i in range(min(len(questions), len(responses))):
            qa_pairs.append({
                "question": questions[i],
                "response": responses[i],
                "index": i
            })
        
        # Construct prompt for unclear response detection
        messages = [
            {"role": "system", "content": "You are an expert interview evaluator specialized in identifying vague, ambiguous, or unclear responses that require clarification."},
            {"role": "user", "content": f"""
            Please analyze the following interview questions and responses to identify any that are unclear, vague, or ambiguous.
            
            Q&A Pairs:
            {json.dumps(qa_pairs, indent=2)}
            
            Your task:
            1. Identify responses that lack specificity or concreteness
            2. Find answers that use vague language without clear examples
            3. Highlight responses where the candidate avoided directly answering the question
            4. Note answers with ambiguous terminology or jargon without explanation
            5. Identify responses where the meaning is unclear or could be interpreted in multiple ways
            
            Return your findings in JSON format with the following structure:
            {{
                "unclear_responses": [
                    {{
                        "index": response_index_number,
                        "question": "original question",
                        "unclear_excerpt": "the unclear or vague part of the response",
                        "issue_type": "vague|ambiguous|evasive|jargon|incomplete",
                        "explanation": "Brief explanation of why this response is unclear",
                        "clarification_needed": "What specific information needs clarification"
                    }}
                ]
            }}
            
            If no unclear responses are found, return an empty list.
            """}
        ]
        
        # Call LLM for unclear response detection
        result_text = self._call_llm(messages)
        
        # Parse result
        try:
            # Extract JSON from the response
            json_start = result_text.find('{')
            json_end = result_text.rfind('}') + 1
            json_str = result_text[json_start:json_end]
            result = json.loads(json_str)
            unclear_responses = result.get('unclear_responses', [])
        except Exception as e:
            logger.error(f"Error parsing unclear response detection results: {str(e)}")
            unclear_responses = []
        
        return unclear_responses
    
    async def _suggest_followup_questions(self, data, **kwargs):
        """
        Suggest followup questions based on contradictions, unclear responses, and STAR analysis
        
        Args:
            data: Must contain responses, questions, and may contain contradictions, 
                  unclear_responses, and star_evaluation
            
        Returns:
            dict: Suggested follow-up questions categorized by type
        """
        responses = data.get('responses', [])
        questions = data.get('questions', [])
        contradictions = data.get('contradictions', [])
        unclear_responses = data.get('unclear_responses', [])
        star_evaluation = data.get('star_evaluation', {})
        
        if not responses:
            return {"error": "No responses provided to suggest follow-up questions"}
        
        # Prepare context for follow-up question generation
        context = {
            "qa_pairs": [],
            "contradictions": contradictions,
            "unclear_responses": unclear_responses,
            "star_evaluation": star_evaluation
        }
        
        # Combine questions and responses
        for i in range(min(len(questions), len(responses))):
            context["qa_pairs"].append({
                "question": questions[i],
                "response": responses[i],
                "index": i
            })
        
        # Construct prompt for follow-up question suggestions
        messages = [
            {"role": "system", "content": "You are an expert interview coach specialized in generating insightful follow-up questions to deepen conversations and clarify candidate responses."},
            {"role": "user", "content": f"""
            Please suggest follow-up questions based on the interview context provided.
            
            Interview Context:
            {json.dumps(context, indent=2)}
            
            Your task:
            1. Generate follow-up questions for contradictions, if any exist
            2. Suggest clarification questions for unclear responses, if any exist
            3. Create STAR-specific follow-up questions to address missing elements (situation, task, action, result)
            4. Propose 2-3 general deep-dive questions that explore interesting aspects of the candidate's responses
            
            Return your suggestions in JSON format with the following structure:
            {{
                "contradiction_questions": [
                    {{
                        "contradiction_index": index_in_contradictions_list,
                        "question": "Tactfully worded follow-up question",
                        "explanation": "What this question aims to clarify"
                    }}
                ],
                "clarification_questions": [
                    {{
                        "response_index": index_of_unclear_response,
                        "question": "Clarification question",
                        "explanation": "What this question aims to clarify"
                    }}
                ],
                "star_questions": [
                    {{
                        "response_index": index_of_response,
                        "missing_element": "situation|task|action|result",
                        "question": "STAR-focused follow-up question",
                        "explanation": "Why this element needs more information"
                    }}
                ],
                "general_questions": [
                    {{
                        "response_index": index_of_response_it_relates_to,
                        "question": "Deep-dive follow-up question",
                        "explanation": "Why this is an interesting area to explore"
                    }}
                ]
            }}
            """}
        ]
        
        # Call LLM for follow-up question suggestions
        result_text = self._call_llm(messages)
        
        # Parse result
        try:
            # Extract JSON from the response
            json_start = result_text.find('{')
            json_end = result_text.rfind('}') + 1
            json_str = result_text[json_start:json_end]
            followup_questions = json.loads(json_str)
        except Exception as e:
            logger.error(f"Error parsing follow-up question suggestions: {str(e)}")
            followup_questions = {
                "contradiction_questions": [],
                "clarification_questions": [],
                "star_questions": [],
                "general_questions": [
                    {
                        "response_index": 0,
                        "question": "Could you tell me more about that experience?",
                        "explanation": "Generic follow-up to encourage elaboration"
                    }
                ]
            }
        
        return followup_questions 