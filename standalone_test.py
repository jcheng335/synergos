import os
import sys
import json
import asyncio
import logging
from dotenv import load_dotenv

# Add the synergos directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'synergos')))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set up the OpenAI API key
load_dotenv('env.txt')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

if not OPENAI_API_KEY:
    OPENAI_API_KEY = input("Enter your OpenAI API key: ")
    if not OPENAI_API_KEY:
        logger.error("No OpenAI API key provided")
        exit(1)

os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY

# Import after setting environment variables
try:
    from synergos.agents.agent_base import AgentBase
    from synergos.agents.question_generator_agent import QuestionGeneratorAgent
except ImportError as e:
    logger.error(f"Import error: {e}")
    logger.info("Searching for agent modules...")
    for root, dirs, files in os.walk('synergos'):
        if 'agents' in dirs:
            logger.info(f"Found agents directory at {os.path.join(root, 'agents')}")
        if 'question_generator_agent.py' in files:
            logger.info(f"Found question_generator_agent.py at {os.path.join(root, 'question_generator_agent.py')}")

    sys.exit(1)

async def test_question_generator():
    """Test the QuestionGeneratorAgent with mock data"""
    logger.info("Initializing QuestionGeneratorAgent")
    agent = QuestionGeneratorAgent()
    
    # Sample resume data
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
    
    # Sample job data
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
    
    # Load competencies from file
    competencies = []
    try:
        with open('competencies.json', 'r') as f:
            competencies_data = json.load(f)
            competencies = [comp['name'] for comp in competencies_data]
    except Exception as e:
        logger.warning(f"Error loading competencies: {e}")
        competencies = ["Technical Expertise", "Problem Solving", "Communication", "Leadership", "Adaptability"]
    
    # Prepare data for the agent
    data = {
        "resume_analysis": resume_data,
        "job_analysis": job_data,
        "competencies": competencies
    }
    
    # Generate initial questions
    logger.info("Generating initial interview questions...")
    try:
        result = await agent.process(data, task="generate_initial_questions")
        
        print("\n=== Initial Questions ===")
        if "questions" in result and result["questions"]:
            for i, q in enumerate(result["questions"], 1):
                if isinstance(q, dict):
                    print(f"{i}. {q.get('question', '')}")
                    if "type" in q:
                        print(f"   Type: {q.get('type', '')}")
                    if "assesses" in q:
                        print(f"   Assesses: {q.get('assesses', '')}")
                    if "look_for" in q:
                        print(f"   Look for: {q.get('look_for', '')}")
                else:
                    print(f"{i}. {q}")
                print()
        else:
            print("No questions generated.")
            
        # Generate competency questions
        logger.info("Generating competency-focused questions...")
        comp_result = await agent.process(data, task="generate_competency_questions")
        
        print("\n=== Competency Questions ===")
        if "questions" in comp_result and comp_result["questions"]:
            for i, q in enumerate(comp_result["questions"], 1):
                if isinstance(q, dict):
                    print(f"{i}. {q.get('question', '')}")
                    if "competency" in q:
                        print(f"   Competency: {q.get('competency', '')}")
                    if "look_for" in q:
                        print(f"   Look for: {q.get('look_for', '')}")
                else:
                    print(f"{i}. {q}")
                print()
        else:
            print("No competency questions generated.")
            
    except Exception as e:
        logger.error(f"Error in question generation: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_question_generator()) 