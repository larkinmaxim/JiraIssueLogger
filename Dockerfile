FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create necessary directories if they don't exist
RUN mkdir -p jira_logger/data/jira_issues jira_logger/data/jira_raw_responses

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expose the API port
EXPOSE 8000

# Run the API server by default
CMD ["python", "jira_logger/run_api.py"]
