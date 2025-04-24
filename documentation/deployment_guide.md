# Jira Logger API Deployment Guide

This guide provides instructions for deploying and running the Jira Logger API in different environments.

## Prerequisites

- Python 3.7+
- Google Cloud account with BigQuery access
- Jira API access token
- Docker and Docker Compose (optional, for containerized deployment)

## Local Development Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root with the following variables:

```
JIRA_BASE_URL=https://your-jira-instance.com
JIRA_API_TOKEN=your_api_token
```

### 3. Set Up Google Cloud Credentials

```bash
# Option 1: Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-file.json"

# Option 2: Use gcloud CLI
gcloud auth application-default login
```

### 4. Run the API Server

```bash
python run_api.py
```

The API will be available at http://localhost:8000, and the interactive documentation will be available at http://localhost:8000/docs.

### 5. Test the API

```bash
python test_api.py
```

## Docker Deployment

### 1. Build and Run with Docker Compose

```bash
# Make sure your .env file is set up
docker-compose up -d
```

This will:
- Build the Docker image
- Start the API server on port 8000
- Mount the current directory as a volume for development

### 2. View Logs

```bash
docker-compose logs -f
```

### 3. Stop the Services

```bash
docker-compose down
```

## Production Deployment

For production deployment, consider the following:

### 1. Use a Production-Ready Server

In production, you should use a production-ready ASGI server like Gunicorn with Uvicorn workers:

```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

### 2. Set Up a Reverse Proxy

Use Nginx or another reverse proxy in front of the API server:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. Use Environment Variables for Configuration

In production, set environment variables directly rather than using a .env file:

```bash
export JIRA_BASE_URL=https://your-jira-instance.com
export JIRA_API_TOKEN=your_api_token
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```

## Scheduling API Calls

### Option 1: Using the Python Scheduler

```bash
# Install the schedule library
pip install schedule

# Run the scheduler
python schedule_api_calls.py
```

To run the scheduler in the background:

```bash
nohup python schedule_api_calls.py > scheduler.log 2>&1 &
```

### Option 2: Using Cron Jobs

Add the following to your crontab:

```
# Update status every day at 1:00 AM
0 1 * * * curl -X POST http://localhost:8000/api/update-status

# Collect closed details every day at 1:30 AM
30 1 * * * curl -X POST http://localhost:8000/api/collect-closed-details

# Collect AC details every day at 1:45 AM
45 1 * * * curl -X POST http://localhost:8000/api/collect-ac-details
```

### Option 3: Using Docker Compose for Scheduling

Uncomment the scheduler service in docker-compose.yml:

```yaml
scheduler:
  build: .
  volumes:
    - .:/app
  environment:
    - JIRA_BASE_URL=${JIRA_BASE_URL}
    - JIRA_API_TOKEN=${JIRA_API_TOKEN}
  command: python schedule_api_calls.py
  restart: unless-stopped
  depends_on:
    - jira-logger-api
```

Then run:

```bash
docker-compose up -d
```

## Cloud Deployment Options

### Google Cloud Run

1. Build and push the Docker image:

```bash
gcloud builds submit --tag gcr.io/your-project-id/jira-logger-api
```

2. Deploy to Cloud Run:

```bash
gcloud run deploy jira-logger-api \
  --image gcr.io/your-project-id/jira-logger-api \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars="JIRA_BASE_URL=https://your-jira-instance.com,JIRA_API_TOKEN=your_api_token"
```

### Google Cloud Functions (for scheduling)

You can use Google Cloud Functions to call the API endpoints on a schedule:

1. Create a Cloud Function that calls the API
2. Set up a Cloud Scheduler job to trigger the function on your desired schedule

## Monitoring and Logging

### Application Logs

The application logs are output to the console and can be redirected to a file:

```bash
python run_api.py > api.log 2>&1
```

The scheduler also logs to both the console and a file named `api_scheduler.log`.

### Health Checks

You can use the root endpoint (`/`) as a health check endpoint to monitor the API's availability.

## Troubleshooting

### SSL Certificate Issues

If you encounter SSL certificate issues with the Jira API, check the Netskope certificate configuration:

1. Verify that the Netskope certificate is correctly installed
2. Check the SSL debug information in the logs
3. Try setting `bypass_ssl_verify=True` for testing (not recommended for production)

### BigQuery Connection Issues

If you have issues connecting to BigQuery:

1. Verify that your Google Cloud credentials are correctly set up
2. Check that the service account has the necessary permissions for BigQuery
3. Ensure that the BigQuery API is enabled in your Google Cloud project
