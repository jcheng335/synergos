# Synergos Interview Companion - Production Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app_code/ ./app_code/
COPY app_wrapper.py app_wrapper.py
COPY wsgi.py wsgi.py
COPY run.py run.py
COPY openai_client_fix.py openai_client_fix.py
COPY db_config.py db_config.py

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8080


# Set environment variable for Python path
ENV PYTHONPATH=/app:/app/app_code
ENV PORT=8080

# Run with gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "120", "app_wrapper:application"]