# Synergos Application Deployment Guide

This guide provides multiple options for deploying the Synergos application.

## Preparation Steps

1. Run the deployment preparation script:
   ```
   python deploy_cloud.py
   ```

   This script will:
   - Fix the OpenAI client initialization issue
   - Create an application wrapper (app_wrapper.py)
   - Update requirements.txt
   - Create necessary deployment files

2. Make sure you have the following environment variables set:
   - `OPENAI_API_KEY` - Your OpenAI API key
   - `AWS_ACCESS_KEY_ID` - Your AWS access key
   - `AWS_SECRET_ACCESS_KEY` - Your AWS secret key
   - `AWS_DEFAULT_REGION` - AWS region (default: us-east-1)

## Option 1: Deploy to Render.com (Free Tier)

Render.com provides a free tier for hosting web services, making it perfect for testing.

1. Create a free account on [Render.com](https://render.com)
2. Create a new Web Service
3. Connect to your GitHub repository (push your code to GitHub first)
4. Set the build command: `pip install -r requirements.txt`
5. Set the start command: `gunicorn app_wrapper:app`
6. Add environment variables:
   - `OPENAI_API_KEY`
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_DEFAULT_REGION`
   - `FLASK_ENV=production`
   - `FLASK_DEBUG=0`
   - `MOCK_SERVICES=false` (set to "true" if using mock services)

## Option 2: Docker Deployment

We've included Docker configuration files for containerized deployment.

### Local Docker Deployment

1. Install [Docker](https://www.docker.com/get-started) and Docker Compose
2. Create a `.env` file with your environment variables:
   ```
   OPENAI_API_KEY=your_openai_api_key
   AWS_ACCESS_KEY_ID=your_aws_key
   AWS_SECRET_ACCESS_KEY=your_aws_secret
   AWS_DEFAULT_REGION=us-east-1
   ```
3. Run the application using Docker Compose:
   ```
   docker-compose up -d
   ```
4. Access the application at http://localhost:8080

### Cloud Docker Deployment

You can deploy the Docker container to various cloud platforms:

#### AWS Elastic Container Service (ECS)

1. Create an ECR repository
2. Build and push the Docker image:
   ```
   aws ecr get-login-password | docker login --username AWS --password-stdin <your-ecr-repo-uri>
   docker build -t synergos-app .
   docker tag synergos-app:latest <your-ecr-repo-uri>:latest
   docker push <your-ecr-repo-uri>:latest
   ```
3. Create an ECS cluster and task definition
4. Deploy as a Fargate service

#### Google Cloud Run

1. Enable Cloud Run API in your Google Cloud project
2. Build and push the Docker image:
   ```
   gcloud builds submit --tag gcr.io/<your-project-id>/synergos-app
   ```
3. Deploy to Cloud Run:
   ```
   gcloud run deploy synergos-app --image gcr.io/<your-project-id>/synergos-app --platform managed
   ```
4. Set environment variables in the Cloud Run console

## Option 3: Traditional Web Hosting

You can also deploy to traditional Python web hosting services.

### PythonAnywhere

1. Sign up for [PythonAnywhere](https://www.pythonanywhere.com/)
2. Upload your code (via Git or direct upload)
3. Create a virtual environment and install dependencies
4. Configure a web app with WSGI configuration file:
   ```python
   import sys
   path = '/home/yourusername/synergos'
   if path not in sys.path:
       sys.path.append(path)
   
   from app_wrapper import app as application
   ```

### Heroku

1. Install the [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)
2. Login to Heroku: `heroku login`
3. Create a new Heroku app: `heroku create synergos-app`
4. Push your code: `git push heroku main`
5. Set environment variables:
   ```
   heroku config:set OPENAI_API_KEY=your_openai_api_key
   heroku config:set AWS_ACCESS_KEY_ID=your_aws_key
   heroku config:set AWS_SECRET_ACCESS_KEY=your_aws_secret
   heroku config:set AWS_DEFAULT_REGION=us-east-1
   ```

## Troubleshooting

### OpenAI Client Issues

If you encounter OpenAI client initialization errors:
1. Make sure you're using a compatible version of the OpenAI SDK
2. Try updating the OpenAI SDK: `pip install openai --upgrade`
3. Check that the patching logic in `openai_client_fix.py` is working correctly

### AWS/DynamoDB Issues

If you encounter AWS connection issues:
1. Verify your AWS credentials are correct
2. Check that the AWS region is properly configured
3. For testing, you can set `MOCK_SERVICES=true` to use mock services instead

### General Deployment Issues

1. Check application logs for specific error messages
2. Verify all required environment variables are set
3. Make sure all dependencies are installed correctly

## Testing Your Deployment

Once deployed, you can test the application by:

1. Opening the application URL in a browser
2. Testing the `/api/generate_initial_questions` endpoint with a tool like Postman:
   ```json
   {
     "resume_text": "Experienced software engineer with Python and web development skills",
     "question_type": "initial"
   }
   ```

## Monitoring and Maintenance

- Set up logging to monitor application performance
- Regularly update dependencies to fix security vulnerabilities
- Back up any data regularly if using the application in production 