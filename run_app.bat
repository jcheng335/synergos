@echo off
echo ===================================
echo SYNERGOS Local Test Environment
echo ===================================

if "%OPENAI_API_KEY%"=="" (
    set /p OPENAI_API_KEY="Enter your OpenAI API Key: "
)

if "%OPENAI_API_KEY%"=="" (
    echo Error: No OpenAI API key provided
    exit /b 1
)

set AWS_ACCESS_KEY_ID=mock-aws-key
set AWS_SECRET_ACCESS_KEY=mock-aws-secret
set AWS_DEFAULT_REGION=us-east-1
set FLASK_ENV=development
set FLASK_DEBUG=1
set MOCK_SERVICES=true

echo Starting application in development mode...
python synergos/app.py 