# Synergos Interview Companion

🤖 **AI-Powered Interview Tool with Real-time Transcription and STAR Analysis**

Synergos is a sophisticated interview companion that leverages AWS Nova Sonic for real-time speech transcription with speaker diarization, combined with OpenAI for intelligent analysis of candidate responses using the STAR (Situation, Task, Action, Result) framework.

## ✨ Features

### 🎤 Real-time Transcription
- **AWS Nova Sonic Integration**: Advanced speech-to-text with speaker identification
- **Emotion Detection**: Real-time analysis of confidence, enthusiasm, and nervousness
- **Speaker Diarization**: Automatic separation of interviewer and candidate speech
- **Confidence Scoring**: Quality metrics for transcription accuracy

### 📋 Dynamic Question Generation
- **Resume-based Questions**: Tailored questions based on candidate background
- **Job Description Matching**: Questions aligned with specific role requirements
- **Competency Mapping**: Questions targeting key skills and abilities
- **STAR Framework Focus**: Questions designed to elicit structured responses

### 🧠 Intelligent Analysis
- **STAR Method Evaluation**: Automatic assessment of Situation, Task, Action, Result components
- **Response Summarization**: Key points extraction from candidate answers
- **Follow-up Generation**: Smart follow-up questions based on responses
- **Competency Assessment**: Skills evaluation against job requirements

### 📁 Document Processing
- **Resume Upload**: Support for PDF, DOCX, TXT formats
- **Job Description Processing**: File upload or URL parsing
- **Content Extraction**: Intelligent parsing of key information
- **Competency Analysis**: Automatic mapping to standard competency frameworks

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- OpenAI API key
- AWS credentials with Bedrock access

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/jcheng335/synergos.git
   cd synergos
   ```

2. **Install dependencies**
   ```bash
   cd synergos
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Configure API keys**
   - Open http://localhost:8080
   - Click "Configure API Keys"
   - Enter your OpenAI API key and AWS credentials

## 🔧 Configuration

### API Keys Setup
The application uses a secure web interface for API key configuration:

- **OpenAI API Key**: Required for question generation and response analysis
- **AWS Credentials**: Required for Nova Sonic transcription
- **AWS Region**: Default is us-east-1, configurable per session

### Required AWS Permissions
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel"
            ],
            "Resource": "*"
        }
    ]
}
```

## 🐳 Docker Deployment

### Build and Run
```bash
# Build the image
docker build -t synergos .

# Run with docker-compose
docker-compose -f docker-compose.production.yml up -d
```

### Production Deployment
```bash
# With environment variables
docker run -d \
  -p 8080:8080 \
  --name synergos \
  --restart unless-stopped \
  synergos
```

## 📖 Usage Guide

### 1. Upload Documents
- **Resume**: Upload candidate's resume in PDF, DOCX, or TXT format
- **Job Description**: Upload job posting file or paste URL

### 2. Generate Questions
- System analyzes both documents
- Generates tailored questions based on competency gaps
- Questions focus on STAR method responses

### 3. Conduct Interview
- Click "Start" to begin real-time transcription
- Questions are displayed for the interviewer
- Candidate responses are automatically transcribed and analyzed

### 4. Real-time Analysis
- **Live Transcription**: See speaker-identified text in real-time
- **Emotion Detection**: Monitor candidate confidence and engagement
- **STAR Analysis**: Automatic evaluation of response structure
- **Follow-up Suggestions**: Smart follow-up questions based on responses

## 🏗️ Architecture

### Frontend
- **HTML5/CSS3/JavaScript**: Modern responsive interface
- **Bootstrap 5**: UI component framework
- **Real-time Updates**: WebSocket-based live transcription
- **File Upload**: Drag-and-drop document processing

### Backend
- **Flask**: Python web framework
- **AWS Nova Sonic**: Speech-to-text with diarization
- **OpenAI GPT**: Question generation and response analysis
- **AWS Bedrock**: AI model orchestration

### Integration Flow
```
Resume + Job Description → Competency Analysis → Question Generation
                ↓
Audio Input → Nova Sonic → Speaker Diarization → Emotion Analysis
                ↓
Candidate Response → STAR Analysis → Follow-up Generation
```

## 🔌 API Endpoints

### Core Application
- `GET /` - Main interface
- `POST /api/set_api_keys` - Configure credentials
- `GET /api/get_api_key_status` - Check configuration

### Document Processing
- `POST /api/upload_resume` - Process resume
- `POST /api/upload_job_posting` - Process job description
- `POST /api/process_job_posting_url` - Parse job URL

### Interview Management
- `POST /api/prepare_interview_questions` - Generate questions
- `GET /api/get_recommended_questions` - Get competency questions

### Nova Integration
- `POST /api/get-nova-credentials` - Initialize session
- `POST /api/nova-real-time-diarization` - Process audio
- `POST /api/end-nova-session` - End session

### Analysis
- `POST /api/summarize_response` - Analyze responses
- `POST /api/generate_followup_questions` - Generate follow-ups

## 🔒 Security

### Data Protection
- **No persistent storage**: API keys stored in browser session only
- **Secure transmission**: HTTPS recommended for production
- **File processing**: Documents processed in memory, not stored
- **Session management**: Automatic cleanup of inactive sessions

### Best Practices
- Use environment variables for production secrets
- Deploy behind reverse proxy (nginx)
- Enable CORS policies for your domain
- Monitor API usage and costs

## 📊 Monitoring

### Health Checks
- **Endpoint**: `/api/get_api_key_status`
- **Docker Health**: Built-in container health monitoring
- **Logging**: Comprehensive application logs in `logs/app.log`

### Performance Metrics
- Real-time transcription latency
- API response times
- Model inference performance
- Memory and CPU usage

## 🛠️ Development

### Project Structure
```
synergos/
├── app.py                 # Main Flask application
├── nova_routes.py         # Nova Sonic integration
├── templates/            # HTML templates
├── static/              # CSS, JavaScript, assets
├── requirements.txt     # Python dependencies
└── logs/               # Application logs
```

### Development Setup
```bash
# Development mode with auto-reload
cd synergos
python app.py

# Run with debug logging
FLASK_ENV=development python app.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

### Troubleshooting
- Check `logs/app.log` for detailed error information
- Verify API key configuration through web interface
- Ensure AWS credentials have required permissions
- Confirm Nova Sonic availability in your region

### Common Issues
- **Nova not working**: Application falls back to mock responses
- **File upload errors**: Check file size (50MB max) and format
- **API errors**: Verify keys and check usage limits

## 🔄 Updates

### Version 2.0.0 (Current)
- ✅ AWS Nova Sonic integration
- ✅ Real-time speaker diarization
- ✅ Emotion and sentiment analysis
- ✅ Enhanced STAR framework analysis
- ✅ Secure API key management
- ✅ Docker deployment support

---

**Made with ❤️ for better interviews**

*Synergos helps create more structured, insightful, and effective interview experiences for both interviewers and candidates.*