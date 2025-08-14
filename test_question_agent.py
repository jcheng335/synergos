import os
import sys
import json
import asyncio
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import from the Synergos package
sys.path.append(os.path.join(os.path.dirname(__file__), 'synergos'))
from synergos.agents import QuestionGeneratorAgent

# Load environment variables
load_dotenv()

# Set OpenAI API key from environment variable
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

async def test_question_generator():
    """Test the QuestionGeneratorAgent's ability to generate questions"""
    
    # Create an instance of the agent
    agent = QuestionGeneratorAgent()
    
    # Sample resume analysis data
    resume_data = {
        "summary": "Experienced software engineer with 5 years of experience in Python and web development.",
        "experience": [
            {
                "title": "Senior Software Engineer",
                "company": "Tech Solutions Inc.",
                "duration": "2020-2023",
                "description": "Led development of cloud-based applications using Python and AWS."
            },
            {
                "title": "Software Developer",
                "company": "Code Innovations",
                "duration": "2018-2020",
                "description": "Developed web applications using Django and React."
            }
        ],
        "skills": {
            "technical_skills": ["Python", "JavaScript", "AWS", "Django", "React", "SQL"],
            "soft_skills": ["Leadership", "Communication", "Problem-solving"]
        },
        "education": [
            {
                "degree": "Bachelor of Computer Science",
                "university": "State University",
                "year": "2018"
            }
        ]
    }
    
    # Sample job analysis data
    job_data = {
        "title": "Senior Python Developer",
        "company": "Innovative Tech",
        "description": "We are looking for an experienced Python developer to join our team.",
        "requirements": [
            "5+ years of experience with Python",
            "Experience with web frameworks such as Django or Flask",
            "Knowledge of AWS services",
            "Strong problem-solving skills"
        ],
        "responsibilities": [
            "Develop and maintain web applications",
            "Work collaboratively with the team to design solutions",
            "Implement best practices for code quality and security",
            "Mentor junior developers"
        ]
    }
    
    # Sample competencies
    competencies = [
        "Technical Expertise",
        "Problem Solving",
        "Communication",
        "Leadership",
        "Adaptability"
    ]
    
    # Prepare data for the agent
    agent_data = {
        "resume_analysis": resume_data,
        "job_analysis": job_data,
        "competencies": competencies
    }
    
    # Generate initial questions
    logger.info("Generating initial interview questions...")
    questions_result = await agent.process(agent_data, task="generate_initial_questions")
    
    # Print the results
    print("\n=== Initial Questions ===")
    if "questions" in questions_result:
        for i, q in enumerate(questions_result["questions"], 1):
            print(f"{i}. {q.get('question', '')}")
            if "look_for" in q:
                print(f"   Look for: {q.get('look_for', '')}")
            print()
    else:
        print("No questions generated.")
    
    # Generate competency questions
    logger.info("Generating competency-focused questions...")
    competency_result = await agent.process(agent_data, task="generate_competency_questions")
    
    # Print the results
    print("\n=== Competency Questions ===")
    if "questions" in competency_result:
        for i, q in enumerate(competency_result["questions"], 1):
            print(f"{i}. {q.get('question', '')}")
            print(f"   Competency: {q.get('competency', '')}")
            if "look_for" in q:
                print(f"   Look for: {q.get('look_for', '')}")
            print()
    else:
        print("No competency questions generated.")
    
    # Generate technical questions
    logger.info("Generating technical questions...")
    technical_result = await agent.process(agent_data, task="generate_technical_questions")
    
    # Print the results
    print("\n=== Technical Questions ===")
    if "questions" in technical_result:
        for i, q in enumerate(technical_result["questions"], 1):
            print(f"{i}. {q.get('question', '')}")
            print(f"   Assesses: {q.get('assesses', '')}")
            print(f"   Difficulty: {q.get('difficulty', '')}")
            if "look_for" in q:
                print(f"   Look for: {q.get('look_for', '')}")
            print()
    else:
        print("No technical questions generated.")

if __name__ == "__main__":
    # Run the async test function
    asyncio.run(test_question_generator()) 