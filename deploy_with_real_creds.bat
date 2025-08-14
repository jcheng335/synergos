@echo off
echo ===================================
echo SYNERGOS DEPLOYMENT (Real Credentials)
echo ===================================

echo Copying real credentials from synergos/env.txt...
copy synergos\env.txt env.txt /Y

echo Setting up environment...
python check_requirements.py

echo Starting application with real credentials...
set FLASK_ENV=production
set FLASK_DEBUG=0
python run_app_production.py

pause 