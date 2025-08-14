import json
import logging
import os
import re
from collections import Counter

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .agent_base import AgentBase
import boto3
from boto3.dynamodb.conditions import Key, Attr
from synergos.dynamo_db import (
    get_competencies, 
    get_questions_by_competency,
    get_all_preset_questions,
    update_question_feedback
)

logger = logging.getLogger(__name__)

# Initialize DynamoDB connection
dynamodb = boto3.resource('dynamodb',
    region_name=os.environ.get('AWS_REGION', 'us-east-1'),
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
)

# Cache for table references
_tables = {}

def get_table(table_name):
    """Get a DynamoDB table reference with caching"""
    if table_name not in _tables:
        _tables[table_name] = dynamodb.Table(table_name)
    return _tables[table_name]

# Competency operations
def get_competencies():
    """Get all competencies"""
    table = get_table('Competencies')
    response = table.scan()
    return response.get('Items', [])

def get_competency(competency_id):
    """Get a competency by ID"""
    table = get_table('Competencies')
    response = table.get_item(Key={'id': competency_id})
    return response.get('Item')

def get_competency_by_name(name):
    """Get a competency by name"""
    table = get_table('Competencies')
    response = table.query(
        IndexName='NameIndex',
        KeyConditionExpression=Key('name').eq(name)
    )
    items = response.get('Items', [])
    return items[0] if items else None

# Question operations
def get_questions_by_competency(competency_name, limit=2):
    """Get questions for a specific competency"""
    table = get_table('Questions')
    response = table.query(
        IndexName='CompetencyIndex',
        KeyConditionExpression=Key('competency_name').eq(competency_name),
        Limit=limit
    )
    return response.get('Items', [])

def get_all_preset_questions():
    """Get all preset questions"""
    table = get_table('Questions')
    response = table.scan(
        FilterExpression=Attr('is_active').eq(True)
    )
    return response.get('Items', [])

def update_question_feedback(question_id, feedback_value):
    """Update question feedback"""
    table = get_table('Questions')
    table.update_item(
        Key={'id': question_id},
        UpdateExpression="SET feedback_score = feedback_score + :val, popularity = popularity + :one",
        ExpressionAttributeValues={
            ':val': feedback_value,
            ':one': 1
        }
    )

class JobAnalysisAgent(AgentBase):
    """
    Agent for analyzing job descriptions, extracting key competencies,
    and prioritizing them based on relevance to the role.
    
    This agent works closely with the QuestionGeneratorAgent to provide
    contextualized competency recommendations.
    """
    
    def __init__(self, config=None):
        super().__init__(config)
        self.competencies = []
        self.competency_descriptions = {}
        self.competency_keywords = {}
        self.load_competencies()
        
        # Keep cached semantic embeddings for competencies
        self._competency_embeddings = None
        self._vectorizer = None
    
    def load_competencies(self):
        """Load competencies from DynamoDB"""
        try:
            competency_items = get_competencies()
            
            # Process competency data into a usable format
            for comp in competency_items:
                name = comp.get('name', '')
                if name:
                    self.competencies.append(name)
                    self.competency_descriptions[name] = comp.get('description', '')
                    self.competency_keywords[name] = comp.get('keywords', [])
                    
                    # If no explicit keywords, extract some from the description
                    if not self.competency_keywords[name] and self.competency_descriptions[name]:
                        # Extract potential keywords from description
                        desc = self.competency_descriptions[name].lower()
                        # Remove common words
                        stop_words = ['the', 'and', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'are']
                        words = re.findall(r'\b\w+\b', desc)
                        keywords = [w for w in words if len(w) > 3 and w not in stop_words]
                        self.competency_keywords[name] = list(set(keywords))
            
            logger.info(f"Loaded {len(self.competencies)} competencies from DynamoDB")
        except Exception as e:
            logger.error(f"Error loading competencies from DynamoDB: {str(e)}")
            # Fallback to file if DynamoDB fails
            if os.path.exists('competencies.json'):
                with open('competencies.json', 'r') as f:
                    competency_data = json.load(f)
                    
                # Process competency data into a usable format
                for comp in competency_data:
                    name = comp.get('name', '')
                    if name:
                        self.competencies.append(name)
                        self.competency_descriptions[name] = comp.get('description', '')
                        self.competency_keywords[name] = comp.get('keywords', [])
                        
                        # If no explicit keywords, extract some from the description
                        if not self.competency_keywords[name] and self.competency_descriptions[name]:
                            # Extract potential keywords from description
                            desc = self.competency_descriptions[name].lower()
                            # Remove common words
                            stop_words = ['the', 'and', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'are']
                            words = re.findall(r'\b\w+\b', desc)
                            keywords = [w for w in words if len(w) > 3 and w not in stop_words]
                            self.competency_keywords[name] = list(set(keywords))
                
                logger.info(f"Loaded {len(self.competencies)} competencies from file")
    
    async def process(self, data, task="analyze_job", **kwargs):
        """
        Process a job description to extract and prioritize competencies.
        
        Args:
            data: Dictionary containing job information
            task: The specific task to perform
            
        Returns:
            Dict with analysis results
        """
        if task == "analyze_job":
            return await self._analyze_job(data, **kwargs)
        elif task == "prioritize_competencies":
            return await self._prioritize_competencies(data, **kwargs)
        elif task == "get_preset_questions":
            return await self._get_preset_questions(data, **kwargs)
        else:
            return {"error": f"Unknown task: {task}"}
    
    async def _analyze_job(self, data, **kwargs):
        """
        Analyze a job description to extract key competencies and requirements.
        
        Args:
            data: Must contain 'job_description' or 'responsibilities'
            
        Returns:
            dict: Analysis results with tagged responsibilities and competencies
        """
        job_description = data.get('job_description', '')
        responsibilities = data.get('responsibilities', [])
        
        # If no explicit responsibilities but we have a job description, extract them
        if not responsibilities and job_description:
            responsibilities = self._extract_responsibilities(job_description)
        
        if not responsibilities:
            return {
                "error": "No job responsibilities found for analysis",
                "tagged_responsibilities": [],
                "top_competencies": []
            }
        
        # Tag responsibilities with competencies
        tagged_responsibilities, competency_scores = self._tag_responsibilities(responsibilities)
        
        # Get top competencies with weightings
        weighted_competencies = self._weight_competencies(competency_scores, responsibilities)
        
        # Include additional context from job description for better recommendations
        role_seniority = self._detect_seniority(job_description)
        role_type = self._detect_role_type(job_description)
        
        return {
            "tagged_responsibilities": tagged_responsibilities,
            "top_competencies": weighted_competencies,
            "role_context": {
                "seniority": role_seniority,
                "role_type": role_type
            }
        }
    
    def _extract_responsibilities(self, job_description):
        """Extract responsibilities from a full job description text"""
        responsibilities = []
        
        # Look for section headers like "Responsibilities:" or "Duties:"
        responsibility_sections = re.split(
            r'\b(responsibilities|duties|what you\'ll do|job duties|key responsibilities|essential functions)\b[:]*',
            job_description, 
            flags=re.IGNORECASE
        )
        
        if len(responsibility_sections) > 1:
            # Get the text after the header
            resp_text = responsibility_sections[2].strip()
            
            # Find the next section header
            next_section = re.search(
                r'\b(requirements|qualifications|what you\'ll need|skills|about you|who you are)\b[:]*',
                resp_text,
                flags=re.IGNORECASE
            )
            
            if next_section:
                resp_text = resp_text[:next_section.start()].strip()
            
            # Split into bullet points if they exist
            if '•' in resp_text or '*' in resp_text or '-' in resp_text:
                # Handle bullet points
                bullet_items = re.split(r'[\n\r]\s*[•*\-]\s*', resp_text)
                for item in bullet_items:
                    if item.strip():
                        responsibilities.append(item.strip())
            else:
                # Split by sentences or newlines
                sentences = re.split(r'[\.\n\r]+', resp_text)
                for sentence in sentences:
                    if len(sentence.strip()) > 20:  # Ignore short fragments
                        responsibilities.append(sentence.strip())
        
        # If we couldn't extract anything, use line-by-line approach
        if not responsibilities:
            lines = job_description.split('\n')
            for line in lines:
                clean_line = line.strip()
                # Identify likely responsibility statements
                if clean_line and len(clean_line) > 20 and not clean_line.endswith(':'):
                    # Lines starting with bullets or having action verbs
                    if (clean_line.startswith('•') or clean_line.startswith('-') or clean_line.startswith('*') or 
                        re.match(r'^[A-Z][a-z]+ing\b', clean_line) or re.match(r'^[A-Z][a-z]+e\b', clean_line)):
                        responsibilities.append(clean_line.lstrip('•*- '))
        
        return responsibilities
    
    def _tag_responsibilities(self, responsibilities):
        """
        Tag responsibilities with relevant competencies using semantic matching.
        Returns tagged responsibilities and competency scores.
        """
        tagged_responsibilities = []
        competency_scores = Counter()
        
        # Initialize TF-IDF vectorizer if not already
        if self._vectorizer is None:
            # Prepare corpus with competency descriptions
            corpus = [self.competency_descriptions.get(comp, comp) for comp in self.competencies]
            self._vectorizer = TfidfVectorizer(stop_words='english')
            self._competency_embeddings = self._vectorizer.fit_transform(corpus)
        
        # Process each responsibility
        for responsibility in responsibilities:
            resp_clean = responsibility.lower()
            tags = set()  # Use set to avoid duplicates
            
            # 1. Exact keyword matching
            for comp_name, keywords in self.competency_keywords.items():
                for keyword in keywords:
                    if keyword.lower() in resp_clean:
                        tags.add(comp_name)
                        competency_scores[comp_name] += 2  # Higher weight for exact matches
            
            # 2. Semantic matching
            resp_vector = self._vectorizer.transform([resp_clean])
            similarities = cosine_similarity(resp_vector, self._competency_embeddings)[0]
            
            # Get top 2 semantic matches if they meet threshold
            semantic_matches = [(self.competencies[i], similarities[i]) 
                               for i in similarities.argsort()[-3:][::-1] 
                               if similarities[i] > 0.3]  # Threshold
            
            for comp_name, score in semantic_matches:
                tags.add(comp_name)
                # Scale score to be comparable with keyword matches
                competency_scores[comp_name] += score * 1.5
            
            # Add fallback if no matches
            if not tags:
                tags.add("General")
                competency_scores["General"] += 1
            
            # Add to tagged responsibilities
            tagged_responsibilities.append({
                "responsibility": responsibility,
                "tags": list(tags)
            })
        
        return tagged_responsibilities, competency_scores
    
    def _weight_competencies(self, competency_scores, responsibilities):
        """
        Weight competencies based on frequency, importance, and relevance.
        Returns list of competencies with weights.
        """
        if not competency_scores:
            return []
        
        # Calculate total score for normalization
        total_score = sum(competency_scores.values())
        
        # Adjust weights based on additional factors
        weighted_competencies = []
        for comp, score in competency_scores.most_common(8):  # Get top 8 initially
            if comp == "General" and len(competency_scores) > 1:
                continue  # Skip General if we have other options
            
            # Calculate normalized weight (0-100 scale)
            weight = int((score / total_score) * 100) if total_score > 0 else 0
            
            # Only include if weight is significant
            if weight >= 10:  # At least 10% relevance
                weighted_competencies.append({
                    "name": comp,
                    "weight": weight,
                    "description": self.competency_descriptions.get(comp, "")
                })
        
        # Ensure we return at least 3 and at most 5 competencies
        if len(weighted_competencies) < 3 and "General" in competency_scores:
            weighted_competencies.append({
                "name": "General",
                "weight": 10,
                "description": "General skills and competencies"
            })
        
        return weighted_competencies[:5]  # Return top 5 max
    
    def _detect_seniority(self, job_description):
        """Detect the seniority level of the role from the job description"""
        job_text = job_description.lower()
        
        # Define seniority patterns
        seniority_patterns = {
            "executive": ["executive", "chief", "cxo", "vice president", "vp", "head of", "director"],
            "senior": ["senior", "sr.", "lead", "principal", "manager", "experienced"],
            "mid": ["mid-level", "intermediate", "associate", "ii", "iii"],
            "junior": ["junior", "jr.", "entry level", "entry-level", "assistant", "i"]
        }
        
        # Check for matches
        matches = {}
        for level, patterns in seniority_patterns.items():
            count = sum(1 for pattern in patterns if pattern in job_text)
            matches[level] = count
        
        # Determine the most likely level
        if not any(matches.values()):
            return "mid"  # Default to mid-level
        
        return max(matches.items(), key=lambda x: x[1])[0]
    
    def _detect_role_type(self, job_description):
        """Detect the type of role from the job description"""
        job_text = job_description.lower()
        
        # Define role type patterns
        role_patterns = {
            "technical": ["engineer", "developer", "programmer", "architect", "technical", "data scientist"],
            "management": ["manager", "director", "lead", "supervisor", "head"],
            "business": ["analyst", "consultant", "specialist", "coordinator", "associate"],
            "creative": ["designer", "writer", "content", "creative", "artist"],
            "operations": ["operations", "logistics", "support", "service", "maintenance"]
        }
        
        # Check for matches
        matches = {}
        for role_type, patterns in role_patterns.items():
            count = sum(1 for pattern in patterns if pattern in job_text)
            matches[role_type] = count
        
        # Determine the most likely role type
        if not any(matches.values()):
            return "general"  # Default
        
        return max(matches.items(), key=lambda x: x[1])[0]
    
    async def _prioritize_competencies(self, data, **kwargs):
        """
        Prioritize competencies based on job requirements and context.
        
        Args:
            data: Must contain 'competencies' and 'job_analysis'
            
        Returns:
            dict: Prioritized competencies with recommended questions
        """
        competencies = data.get('competencies', [])
        job_analysis = data.get('job_analysis', {})
        
        if not competencies or not job_analysis:
            return {
                "error": "Missing competencies or job analysis data",
                "prioritized_competencies": []
            }
        
        # Get role context
        role_context = job_analysis.get('role_context', {})
        seniority = role_context.get('seniority', 'mid')
        role_type = role_context.get('role_type', 'general')
        
        # Adjust competency priorities based on role context
        prioritized = []
        
        # Start with top competencies from job analysis
        top_comps = job_analysis.get('top_competencies', [])
        
        for comp in top_comps:
            comp_name = comp.get('name')
            comp_weight = comp.get('weight', 50)
            
            # Adjust weight based on seniority and role type
            adjusted_weight = comp_weight
            
            # Seniority adjustments
            if seniority == "executive" and comp_name in ["Strategic Mindset", "Drives Results", "Decision Quality"]:
                adjusted_weight += 15
            elif seniority == "senior" and comp_name in ["Develops Talent", "Collaborates", "Plans and Aligns"]:
                adjusted_weight += 10
            elif seniority == "junior" and comp_name in ["Being Resilient", "Action Oriented", "Customer Focus"]:
                adjusted_weight += 10
                
            # Role type adjustments
            if role_type == "technical" and comp_name in ["Decision Quality", "Resourcefulness"]:
                adjusted_weight += 10
            elif role_type == "management" and comp_name in ["Develops Talent", "Directs Work"]:
                adjusted_weight += 15
            elif role_type == "business" and comp_name in ["Strategic Mindset", "Customer Focus"]:
                adjusted_weight += 10
                
            prioritized.append({
                "name": comp_name,
                "description": comp.get('description', ''),
                "weight": min(adjusted_weight, 100)  # Cap at 100
            })
        
        # Sort by adjusted weight
        prioritized.sort(key=lambda x: x['weight'], reverse=True)
        
        return {
            "prioritized_competencies": prioritized
        }
    
    async def _get_preset_questions(self, data, **kwargs):
        """
        Get preset questions for the prioritized competencies from DynamoDB.
        
        Args:
            data: Must contain 'competencies' 
            
        Returns:
            dict: Preset questions for each competency
        """
        competencies = data.get('competencies', [])
        if not competencies:
            return {
                "error": "No competencies provided",
                "preset_questions": []
            }
        
        preset_questions = []
        
        # Get questions for each competency
        for comp in competencies:
            comp_name = comp if isinstance(comp, str) else comp.get('name', '')
            if not comp_name:
                continue
                
            # Get questions for this competency - aim to get 2 per competency
            questions = get_questions_by_competency(comp_name, limit=2)
            
            if questions:
                for q in questions:
                    preset_questions.append({
                        "id": q['id'],
                        "question": q['question_text'],
                        "competency": q['competency_name'],
                        "competency_description": q.get('competency_description', ''),
                        "is_preset": True
                    })
            else:
                # No preset questions for this competency, log it
                logger.warning(f"No preset questions found for competency: {comp_name}")
        
        return {
            "preset_questions": preset_questions
        }

# Function to analyze responsibilities and tag with competencies
def analyze_job_responsibilities(responsibilities):
    """
    Analyze job responsibilities and tag them with relevant competencies.
    Now using DynamoDB for keywords lookup.
    """
    # Track competency counts
    competency_counts = Counter()
    tagged_responsibilities = []
    
    # Get competencies with keywords from DynamoDB
    competencies = get_competencies()
    competency_keyword_map = {}
    
    # Build a lookup map for efficient keyword searching
    for comp in competencies:
        comp_name = comp.get('name')
        keywords = comp.get('keywords', [])
        for keyword in keywords:
            competency_keyword_map[keyword.lower()] = comp_name
    
    # Process each responsibility
    for responsibility in responsibilities:
        lower_resp = responsibility.lower()
        tags = set()  # Use set to avoid duplicates
        
        # Check for keyword matches
        for keyword, comp_name in competency_keyword_map.items():
            if keyword in lower_resp:
                tags.add(comp_name)
                competency_counts[comp_name] += 1
        
        # Add fallback if no matches
        if not tags:
            tags.add("General")
            competency_counts["General"] += 1
        
        # Add to tagged responsibilities
        tagged_responsibilities.append({
            "responsibility": responsibility,
            "tags": list(tags)
        })
    
    # Get top 5 competencies
    top_competencies = [comp for comp, _ in competency_counts.most_common(5)]
    
    # Remove 'General' if it's in top competencies and we have other options
    if "General" in top_competencies and len(competency_counts) > 5:
        top_competencies.remove("General")
        # Add the next competency
        for comp, _ in competency_counts.most_common():
            if comp not in top_competencies and comp != "General":
                top_competencies.append(comp)
                break
        # Keep only top 5
        top_competencies = top_competencies[:5]
    
    return {
        "tagged_responsibilities": tagged_responsibilities,
        "top_competencies": top_competencies
    }

# Function to get recommended questions based on competencies
def get_recommended_questions(top_competencies):
    """
    Get recommended questions based on top competencies.
    Now using DynamoDB for questions lookup.
    """
    recommended_questions = []
    
    for competency in top_competencies:
        # Skip General category
        if competency == "General":
            continue
        
        # Get questions for this competency (limit to 1 for recommendations)
        questions = get_questions_by_competency(competency, limit=1)
        
        if questions and len(questions) > 0:
            # Add the top question
            recommended_questions.append({
                "competency": questions[0]['competency_name'],
                "question": questions[0]['question_text']
            })
    
    return recommended_questions 