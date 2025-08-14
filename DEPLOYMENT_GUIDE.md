# Synergos Interview Companion - Deployment Guide

## Overview

Synergos is an AI-powered interview companion tool that provides:
- Real-time transcription using AWS Nova Sonic
- STAR method analysis of candidate responses
- Dynamic question generation based on resume and job description
- Emotional analysis and sentiment detection
- Follow-up question suggestions

## Quick Start (Local Development)

1. **Clone and Setup**
   ```bash
   git clone https://github.com/jcheng335/synergos.git
   cd synergos
   cd synergos  # Main application directory
   pip install -r requirements.txt
   ```

2. **Configure API Keys**
   - Start the application: `python app.py`
   - Open http://localhost:8080
   - Click "Configure API Keys" button
   - Enter your OpenAI API key and AWS credentials

3. **Test the Application**
   - Upload a resume (PDF/DOCX/TXT)
   - Upload or paste a job description
   - Generate tailored interview questions
   - Start recording for real-time transcription and analysis

## Production Deployment

### Docker Deployment (Recommended)

1. **Build and Run**
   ```bash
   # Build the container
   docker build -t synergos .
   
   # Run with docker-compose
   docker-compose -f docker-compose.production.yml up -d
   ```

2. **Access the Application**
   - Open http://localhost:8080
   - Configure API keys through the web interface

### Manual Deployment

1. **Server Requirements**
   - Python 3.11+
   - 2GB+ RAM
   - Port 8080 available

2. **Install Dependencies**
   ```bash
   cd synergos
   pip install -r requirements.txt
   ```

3. **Run with Gunicorn**
   ```bash
   gunicorn --bind 0.0.0.0:8080 --workers 4 --timeout 120 wsgi:application
   ```

## Environment Configuration

### Required AWS Permissions

Your AWS credentials need the following permissions:
- `bedrock:InvokeModel` (for Nova Sonic)
- `dynamodb:Scan`, `dynamodb:Query` (optional, for competencies storage)

### OpenAI Requirements

- OpenAI API key with access to:
  - GPT-3.5-turbo or GPT-4
  - Text completion models

## Features

### Core Functionality

1. **Resume Analysis**
   - Upload resume in PDF, DOCX, or TXT format
   - Automatic extraction and parsing
   - Competency mapping

2. **Job Description Processing**
   - Upload job posting files or paste URLs
   - Requirement extraction
   - Competency analysis

3. **Question Generation**
   - Dynamic questions based on resume + job description
   - STAR method focused questions
   - Competency-specific inquiries

4. **Real-time Transcription**
   - AWS Nova Sonic integration for speaker diarization
   - Emotion and sentiment analysis
   - Confidence scoring

5. **Response Analysis**
   - STAR framework evaluation
   - Competency assessment
   - Follow-up question generation

### AWS Nova Integration

The application uses AWS Nova Sonic for:
- Real-time speech-to-text with speaker identification
- Emotional analysis (confidence, enthusiasm, nervousness)
- Sentiment analysis
- Prosody analysis for speech patterns

Note: Nova integration includes fallback to mock responses for testing when Nova API is not available.

## API Endpoints

### Core Endpoints

- `GET /` - Main application interface
- `POST /api/set_api_keys` - Configure API credentials
- `GET /api/get_api_key_status` - Check API configuration status

### File Processing

- `POST /api/upload_resume` - Upload and process resume
- `POST /api/upload_job_posting` - Upload job description
- `POST /api/process_job_posting_url` - Process job posting URL

### Interview Management

- `POST /api/prepare_interview_questions` - Generate questions
- `GET /api/get_introductory_questions` - Get standard intro questions
- `GET /api/get_recommended_questions` - Get competency-based questions

### Nova Integration

- `POST /api/get-nova-credentials` - Initialize Nova session
- `POST /api/nova-real-time-diarization` - Process audio chunks
- `POST /api/end-nova-session` - End transcription session

### Analysis

- `POST /api/summarize_response` - Analyze candidate responses
- `POST /api/generate_followup_questions` - Generate follow-up questions

## Security Considerations

1. **API Key Management**
   - Keys are stored in browser session only
   - Not persisted on server
   - Configure through secure HTTPS in production

2. **File Uploads**
   - 50MB maximum file size
   - Supported formats: PDF, DOCX, TXT
   - Files processed in memory, not stored permanently

3. **Network Security**
   - Run behind reverse proxy (nginx) in production
   - Enable HTTPS/TLS
   - Configure proper CORS headers

## Monitoring and Logging

- Application logs stored in `logs/app.log`
- Health check endpoint: `/api/get_api_key_status`
- Monitor Docker container health with built-in health checks

## Troubleshooting

### Common Issues

1. **Nova Integration Not Working**
   - Check AWS credentials and permissions
   - Verify Nova Sonic is available in your region
   - Application will fallback to mock responses

2. **API Key Issues**
   - Use the web interface to configure keys
   - Check OpenAI key has sufficient credits
   - Verify AWS credentials have required permissions

3. **File Upload Problems**
   - Ensure file size under 50MB
   - Check file format is supported
   - Verify sufficient disk space

### Debug Mode

For development, run with debug enabled:
```bash
cd synergos
python app.py  # Debug mode is enabled by default
```

## Support

For issues or questions:
- Check application logs in `logs/app.log`
- Verify API key configuration
- Ensure all dependencies are installed

## Version Information

- **Current Version**: 2.0.0
- **Python**: 3.11+
- **Flask**: 2.3.3+
- **OpenAI**: 1.6.1+
- **AWS SDK**: 1.28.44+