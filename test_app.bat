@echo off
echo Setting environment variables for testing...
set AWS_ACCESS_KEY_ID=dummy-key
set AWS_SECRET_ACCESS_KEY=dummy-secret
set AWS_DEFAULT_REGION=us-east-1
set OPENAI_API_KEY=sk-dummy-key
set FLASK_ENV=development
set FLASK_DEBUG=1
set MOCK_SERVICES=true

echo Running the app in test mode...
python start_app.py

pause 