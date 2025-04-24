# Jira Logger API

A FastAPI application for logging Jira issues to BigQuery with automatic duplicate prevention.

## Overview

This API provides three main endpoints:

1. **Update Status Endpoint**: Fetches all Jira issues with specified statuses and updates BigQuery
2. **Collect Closed/Deployed PD Details**: Collects details for issues in "closed" or "deployed pd" status with empty details
3. **Collect Deployed AC Details**: Collects/updates details for issues in "deployed ac" status

## Prerequisites

- Python 3.7+
- Google Cloud account with BigQuery access
- Jira API access token

## Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Set up environment variables in a `.env` file:

```
JIRA_BASE_URL=https://your-jira-instance.com
JIRA_API_TOKEN=your_api_token
```

3. Set up Google Cloud credentials:

```bash
# Option 1: Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-file.json"

# Option 2: Use gcloud CLI
gcloud auth application-default login
```

## Running the API

Start the API server:

```bash
python run_api.py
```

The API will be available at http://localhost:8000, and the interactive documentation will be available at http://localhost:8000/docs.

## API Endpoints

### Root Endpoint

- **URL**: `/`
- **Method**: GET
- **Description**: Check if the API is running
- **Response**: `{"message": "Jira Logger API is running"}`

### Update Status

- **URL**: `/api/update-status`
- **Method**: POST
- **Description**: Update status of existing issues and add new ones
- **Response**: 
  ```json
  {
    "updated_count": 5,
    "inserted_count": 2,
    "error_count": 0,
    "errors": []
  }
  ```

### Collect Closed/Deployed PD Details

- **URL**: `/api/collect-closed-details`
- **Method**: POST
- **Description**: Collect details for issues in "closed" or "deployed pd" status with empty details
- **Response**: 
  ```json
  {
    "updated_count": 3,
    "inserted_count": 0,
    "error_count": 1,
    "errors": ["Error processing issue EI-1234: Connection error"]
  }
  ```

### Collect Deployed AC Details

- **URL**: `/api/collect-ac-details`
- **Method**: POST
- **Description**: Collect/update details for issues in "deployed ac" status
- **Response**: 
  ```json
  {
    "updated_count": 2,
    "inserted_count": 0,
    "error_count": 0,
    "errors": []
  }
  ```

## BigQuery Integration

The application automatically creates the necessary BigQuery dataset and table if they don't exist. The table schema includes:

- `issue_key` (STRING, PRIMARY KEY)
- `summary` (STRING)
- `status` (STRING)
- `project_ticket` (STRING)
- `planned_dev_start` (TIMESTAMP)
- `planned_dev_finish` (TIMESTAMP)
- `planned_duration` (FLOAT)
- `actual_start` (TIMESTAMP)
- `actual_finish` (TIMESTAMP)
- `actual_duration` (FLOAT)
- `details_updated_at` (TIMESTAMP)
- `last_updated_at` (TIMESTAMP)

## Duplicate Prevention

The application prevents duplicates in the BigQuery table through:

1. Using `issue_key` as the primary key
2. Using BigQuery's MERGE operations for upserts
3. Selective updates of only the columns that need to be changed
4. Timestamp tracking for when details were last updated

## Scheduling

For daily execution, you can set up a cron job or use a scheduler like Google Cloud Scheduler:

```bash
# Example cron job (runs daily at 1 AM)
0 1 * * * curl -X POST http://localhost:8000/api/update-status
30 1 * * * curl -X POST http://localhost:8000/api/collect-closed-details
45 1 * * * curl -X POST http://localhost:8000/api/collect-ac-details
```

## Error Handling

The API includes comprehensive error handling and returns detailed error messages when issues occur. All errors are logged and included in the response.

## SSL Certificate Handling

The application uses the Netskope certificate library for SSL certificate handling, particularly useful in corporate environments with SSL interception.
