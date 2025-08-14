@echo off
echo ===================================
echo SYNERGOS Application Deployment Tool
echo ===================================

if "%1"=="--docker" (
    echo Deploying with Docker...
    python deploy.py --docker
) else (
    echo Deploying locally...
    python deploy.py
)

pause 