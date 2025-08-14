# Synergos - AI-Powered Recruiting Assistant

A comprehensive recruitment and onboarding companion powered by AI to streamline the hiring process.

## Features

- **Resume Analysis**: Extract skills, experience, and qualifications automatically
- **Job Posting Analysis**: Identify key requirements and competencies
- **Candidate-Job Matching**: Score candidates against job requirements
- **Interview Support**: Generate tailored questions based on job and resume
- **Real-time Analysis**: Evaluate candidate responses during interviews
- **Follow-up Generation**: Automatically create customized follow-up emails
- **Multi-agent AI System**: Specialized agents for different recruitment tasks

## Technology Stack

- **Backend**: Python, Flask, Celery, Redis, PostgreSQL
- **AI Integration**: OpenAI API, Azure Speech Services, AWS Bedrock
- **Document Processing**: PyPDF, docx2txt, BeautifulSoup
- **Containerization**: Docker, Docker Compose
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Async**: Asyncio for concurrent processing

## System Architecture

The system follows a modern microservices architecture with the following components:

1. **Web API Layer**: Flask-based REST API endpoints
2. **Multi-agent System**: Specialized AI agents for different tasks
3. **Orchestration Layer**: Coordinates workflows across agents
4. **Database Layer**: Persistent storage for candidates, jobs, interviews
5. **Task Queue**: Asynchronous processing with Celery and Redis
6. **Document Processing**: Extraction and analysis of resumes and job descriptions

## Setup and Installation

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-username/synergos.git
cd synergos

# Create .env file with your API keys (sample in env.txt)
cp env.txt .env

# Start the application
docker-compose up -d
```

### Manual Setup

```bash
# Clone the repository
git clone https://github.com/your-username/synergos.git
cd synergos

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with your API keys
cp env.txt .env

# Initialize the database
flask db upgrade

# Run the application
flask run
```

## API Endpoints

### Resume Processing

- `POST /api/upload_resume`: Upload and analyze a resume
- `POST /api/process_resume_text`: Process resume text directly
- `POST /api/match_resume_to_job`: Match a resume against a job posting

### Job Processing

- `POST /api/upload_job_posting`: Upload and analyze a job posting
- `POST /api/process_job_posting_url`: Process a job posting from a URL

### Interview Management

- `POST /api/prepare_interview_questions`: Generate interview questions
- `POST /api/analyze_response_star`: Analyze response using STAR method
- `POST /api/generate_followup_questions`: Generate follow-up questions

### Candidate Management

- `POST /api/generate_recommendation`: Generate hiring recommendation
- `POST /api/candidate_evaluation`: Comprehensive candidate evaluation

## Multi-Agent System

Synergos uses a sophisticated multi-agent system with specialized agents:

1. **Resume Analysis Agent**: Extracts candidate information
2. **Job Analysis Agent**: Analyzes job requirements
3. **Interview Agent**: Generates and analyzes interview questions
4. **Scheduling Agent**: Handles interview scheduling
5. **Email Agent**: Generates follow-up emails and communications

## Development

### Running Tests

```bash
pytest
```

### Creating Database Migrations

```bash
flask db migrate -m "Description of changes"
flask db upgrade
```

## License

MIT License

## Contact

For questions or support, please contact [your-email@example.com](mailto:your-email@example.com). 