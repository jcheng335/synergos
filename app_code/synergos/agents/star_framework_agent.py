import logging
import json
from synergos.agents.agent_base import AgentBase

logger = logging.getLogger(__name__)

class STARFrameworkAgent(AgentBase):
    """
    Agent responsible for real-time STAR framework analysis.
    Provides immediate feedback on which STAR elements are present/missing
    in candidate responses as they happen.
    """
    
    async def process(self, data, task="analyze_star_components", **kwargs):
        """Process STAR analysis request based on specified task"""
        method_map = {
            "analyze_star_components": self._analyze_star_components,
            "map_response_to_star": self._map_response_to_star,
            "identify_missing_elements": self._identify_missing_elements,
            "generate_star_summary": self._generate_star_summary
        }
        
        if task not in method_map:
            raise ValueError(f"Unknown task '{task}' for STARFrameworkAgent")
        
        return await method_map[task](data, **kwargs)
    
    async def _analyze_star_components(self, data, **kwargs):
        """
        Analyze a response to identify which STAR components are present
        
        Args:
            data: Must contain 'response' and optionally 'question'
            
        Returns:
            dict: STAR component analysis results
        """
        response = data.get('response', '')
        question = data.get('question', '')
        
        if not response:
            return {
                "error": "No response provided for analysis",
                "star_components": {
                    "situation": {"present": False, "confidence": 0, "excerpt": ""},
                    "task": {"present": False, "confidence": 0, "excerpt": ""},
                    "action": {"present": False, "confidence": 0, "excerpt": ""},
                    "result": {"present": False, "confidence": 0, "excerpt": ""}
                }
            }
        
        # Construct prompt for STAR component analysis
        messages = [
            {"role": "system", "content": "You are an expert in analyzing interview responses according to the STAR (Situation, Task, Action, Result) framework. Your job is to identify which STAR components are present in a response and extract relevant excerpts."},
            {"role": "user", "content": f"""
            Please analyze this interview response according to the STAR framework.
            
            Question: {question}
            
            Response: {response}
            
            For each STAR component (Situation, Task, Action, Result):
            1. Determine if it is present in the response (true/false)
            2. Provide a confidence score (0-10) for how clearly this component is articulated
            3. Extract a brief excerpt that best represents this component
            4. For any missing components, set present to false, confidence to 0, and excerpt to empty string
            
            Return your analysis in JSON format with the following structure:
            {{
                "situation": {{"present": boolean, "confidence": number, "excerpt": "string"}},
                "task": {{"present": boolean, "confidence": number, "excerpt": "string"}},
                "action": {{"present": boolean, "confidence": number, "excerpt": "string"}},
                "result": {{"present": boolean, "confidence": number, "excerpt": "string"}}
            }}
            """}
        ]
        
        # Call LLM for STAR component analysis
        analysis_text = self._call_llm(messages)
        
        # Parse result
        try:
            # Extract JSON from the response
            json_start = analysis_text.find('{')
            json_end = analysis_text.rfind('}') + 1
            json_str = analysis_text[json_start:json_end]
            star_components = json.loads(json_str)
        except Exception as e:
            logger.error(f"Error parsing STAR component analysis: {str(e)}")
            star_components = {
                "situation": {"present": False, "confidence": 0, "excerpt": ""},
                "task": {"present": False, "confidence": 0, "excerpt": ""},
                "action": {"present": False, "confidence": 0, "excerpt": ""},
                "result": {"present": False, "confidence": 0, "excerpt": ""}
            }
        
        # Add overall completeness score
        completeness_score = self._calculate_star_completeness(star_components)
        
        return {
            "star_components": star_components,
            "completeness_score": completeness_score,
            "missing_elements": self._identify_missing_star_elements(star_components)
        }
    
    def _calculate_star_completeness(self, star_components):
        """Calculate overall STAR completeness score based on component presence and confidence"""
        total_score = 0
        max_score = 0
        
        for component in ["situation", "task", "action", "result"]:
            if component in star_components:
                if star_components[component]["present"]:
                    total_score += star_components[component]["confidence"]
                max_score += 10
        
        return round((total_score / max_score) * 10, 1) if max_score > 0 else 0
    
    def _identify_missing_star_elements(self, star_components):
        """Identify which STAR elements are missing or weak in the response"""
        missing_elements = []
        
        for component in ["situation", "task", "action", "result"]:
            if component in star_components:
                if not star_components[component]["present"]:
                    missing_elements.append(component)
                elif star_components[component]["confidence"] < 5:
                    missing_elements.append(f"{component} (weak)")
        
        return missing_elements
    
    async def _map_response_to_star(self, data, **kwargs):
        """
        Map segments of a response to specific STAR components
        
        Args:
            data: Must contain 'response' and optionally 'question'
            
        Returns:
            dict: Mapping of response segments to STAR components
        """
        response = data.get('response', '')
        question = data.get('question', '')
        
        if not response:
            return {
                "error": "No response provided for mapping",
                "star_mapping": {}
            }
        
        # Construct prompt for mapping response to STAR
        messages = [
            {"role": "system", "content": "You are an expert in analyzing interview responses according to the STAR framework. Your job is to map sections of a response to specific STAR components."},
            {"role": "user", "content": f"""
            Please map this interview response to the STAR framework components.
            
            Question: {question}
            
            Response: {response}
            
            For each sentence or logical segment in the response, determine which STAR component it belongs to (Situation, Task, Action, Result, or None).
            
            Return your analysis in JSON format with the following structure:
            {{
                "mapping": [
                    {{"segment": "text segment", "component": "situation|task|action|result|none"}},
                    // more segments
                ]
            }}
            """}
        ]
        
        # Call LLM for mapping
        mapping_text = self._call_llm(messages)
        
        # Parse result
        try:
            # Extract JSON from the response
            json_start = mapping_text.find('{')
            json_end = mapping_text.rfind('}') + 1
            json_str = mapping_text[json_start:json_end]
            mapping = json.loads(json_str)
        except Exception as e:
            logger.error(f"Error parsing STAR mapping: {str(e)}")
            mapping = {
                "mapping": []
            }
        
        return {
            "star_mapping": mapping
        }
    
    async def _identify_missing_elements(self, data, **kwargs):
        """
        Identify missing STAR elements and generate suggestions for improvement
        
        Args:
            data: Must contain 'response' and optionally 'question'
            
        Returns:
            dict: Missing elements and improvement suggestions
        """
        # First analyze the STAR components
        analysis_result = await self._analyze_star_components(data)
        star_components = analysis_result.get("star_components", {})
        missing_elements = analysis_result.get("missing_elements", [])
        
        response = data.get('response', '')
        question = data.get('question', '')
        
        if not missing_elements:
            return {
                "missing_elements": [],
                "improvement_suggestions": "No missing STAR elements detected. The response appears complete."
            }
        
        # Construct prompt for improvement suggestions
        messages = [
            {"role": "system", "content": "You are an expert interview coach specializing in the STAR framework. Your job is to suggest improvements for interview responses."},
            {"role": "user", "content": f"""
            Please provide improvement suggestions for this interview response.
            
            Question: {question}
            
            Response: {response}
            
            STAR Analysis:
            {json.dumps(star_components, indent=2)}
            
            Missing or Weak Elements:
            {', '.join(missing_elements)}
            
            For each missing or weak element, suggest how the candidate could improve their response.
            Be specific about what additional information they should provide.
            
            Return your suggestions in JSON format with the following structure:
            {{
                "suggestions": [
                    {{"element": "situation|task|action|result", "suggestion": "improvement suggestion"}}
                ]
            }}
            """}
        ]
        
        # Call LLM for improvement suggestions
        suggestions_text = self._call_llm(messages)
        
        # Parse result
        try:
            # Extract JSON from the response
            json_start = suggestions_text.find('{')
            json_end = suggestions_text.rfind('}') + 1
            json_str = suggestions_text[json_start:json_end]
            suggestions = json.loads(json_str)
        except Exception as e:
            logger.error(f"Error parsing improvement suggestions: {str(e)}")
            suggestions = {
                "suggestions": [{"element": element, "suggestion": "Provide more information about this element."} for element in missing_elements]
            }
        
        return {
            "missing_elements": missing_elements,
            "improvement_suggestions": suggestions.get("suggestions", [])
        }
    
    async def _generate_star_summary(self, data, **kwargs):
        """
        Generate a summary of STAR analysis with improvement suggestions
        
        Args:
            data: Must contain 'response' and optionally 'question'
            
        Returns:
            dict: Summary of STAR analysis with improvement suggestions
        """
        # Get component analysis and missing elements
        analysis_result = await self._analyze_star_components(data)
        missing_result = await self._identify_missing_elements(data)
        
        # Compile results
        summary = {
            "star_components": analysis_result.get("star_components", {}),
            "completeness_score": analysis_result.get("completeness_score", 0),
            "missing_elements": missing_result.get("missing_elements", []),
            "improvement_suggestions": missing_result.get("improvement_suggestions", [])
        }
        
        return summary 