# Product Requirements Document: Jira Logger with BigQuery Integration

## 1. Introduction

### 1.1 Purpose
This document outlines the requirements for the Jira Logger with BigQuery Integration system, which will automatically collect and store Jira issue data in Google BigQuery for reporting and analysis purposes.

### 1.2 Scope
The system will periodically fetch Jira issue data, extract relevant information, and store it in BigQuery while preventing duplicates. It will handle different issue statuses and collect detailed information based on specific criteria.

### 1.3 Definitions and Acronyms
- **Jira**: Issue tracking software
- **BigQuery**: Google Cloud's serverless data warehouse
- **API**: Application Programming Interface
- **SSL**: Secure Sockets Layer
- **Netskope**: Network security platform that may intercept SSL connections

## 2. System Overview

### 2.1 System Architecture
The system consists of a FastAPI application with three main endpoints:
1. Update Status Endpoint: Fetches all Jira issues with specified statuses and updates BigQuery
2. Collect Closed/Deployed PD Details: Collects details for issues in "closed" or "deployed pd" status with empty details
3. Collect Deployed AC Details: Collects/updates details for issues in "deployed ac" status

### 2.2 User Roles and Permissions
- **System Administrator**: Configures and maintains the system
- **Data Analyst**: Consumes the data stored in BigQuery for reporting and analysis

## 3. Jira Integration Requirements

### 3.1 Jira API Endpoints
The system will use the following Jira API endpoints:

| Endpoint                                                       | Purpose                                                                 | Method |
| -------------------------------------------------------------- | ----------------------------------------------------------------------- | ------ |
| `{JIRA_BASE_URL}/rest/api/2/search`                            | Search for issues matching specific criteria                            | POST   |
| `{JIRA_BASE_URL}/rest/api/2/issue/{issueKey}?expand=changelog` | Get detailed information about a specific issue including its changelog | GET    |

### 3.2 Jira Authentication
- **Authentication Method**: Bearer Token
- **API Token Storage**: Environment variable `JIRA_API_TOKEN`
- **Base URL Storage**: Environment variable `JIRA_BASE_URL`

### 3.3 Jira Query Parameters
For the search endpoint, the following JQL query will be used:
```
project in (EI) AND issuetype = Project AND "Project ticket" is not EMPTY and "Start Date" is not empty and "End date" is not empty AND (status = "in progress" OR status = "deployed ac" OR status = "deployed pd" OR status = "closed")
```

### 3.4 Jira Custom Fields
The system will extract the following custom fields from Jira:

| Field Name         | Custom Field ID   | Description                     |
| ------------------ | ----------------- | ------------------------------- |
| Project ticket     | customfield_11491 | Project ticket identifier       |
| Start Date         | customfield_21500 | Project start date              |
| End date           | customfield_27491 | Project end date                |
| Planned dev start  | customfield_15990 | Planned development start date  |
| Planned dev finish | customfield_15994 | Planned development finish date |

## 4. Data Requirements

### 4.1 Data Points to Extract
The system will extract the following data points from Jira issues:

#### Basic Issue Information
- Issue Key (e.g., EI-1234)
- Summary
- Status
- Project Ticket
- Created Date
- Updated Date

#### Planned Dates
- Planned Development Start Date
- Planned Development Finish Date
- Planned Duration (calculated)

#### Actual Dates
- Actual Start Date (derived from status changes)
- Actual Finish Date (derived from status changes)
- Actual Duration (calculated)
- Start Method (how the start date was determined)
- Finish Method (how the finish date was determined)

### 4.2 Status Values
The system will track issues with the following status values:
- "in progress"
- "deployed ac"
- "deployed pd" (current status of EI-6172 as of 2025-04-24)
- "closed"

### 4.2.1 Current Issue Statuses
The system is currently tracking the following issues:
- EI-5967: Status tracked in jira_raw_responses/EI-5967_20250424_134357.json
- EI-6172: "Deployed PD" as of 2025-04-24
- EI-6189: Status tracked in jira_raw_responses/EI-6189_20250424_134359.json

### 4.2.2 Detailed Issue Information
#### EI-6172
- **Issue Key**: EI-6172
- **Summary**: "EI - CXPROIMP - 295110 - GBFOODS& AFFINITY | Review High-Level EE (Non-ARR) | GBFoods - new delivery field"
- **Status**: "Deployed PD"
- **Project Ticket**: "CXPRODELIVERY-5039"
- **Planned Development Start Date**: "2025-03-12"
- **Planned Development Finish Date**: "2025-04-02"
- **Environment**: "Productive"
- **Description**: Mapping for new customer specific field "Initial delivery date" is needed.
- **Created Date**: "2025-03-13T08:56:31.248+0100"
- **Actual Start Date**: "2025-03-19T16:13:27.150+0100" (Status changed to "In Progress")
- **Actual Finish Date**: "2025-04-03T15:01:57.044+0200" (Status changed to "Deployed PD")
- **Actual Duration**: Approximately 15 working days

### 4.3 Development Status Mapping
The system uses status change events in the Jira issue changelog to determine the actual start and finish dates of development work. This approach provides more accurate tracking than relying solely on planned dates.

#### Start Status Indicators
The system identifies the actual start date by finding the earliest timestamp when an issue transitions to any of these statuses:
- "In Progress" - Indicates development work has actively begun
- "Code review" - In some workflows, issues may skip "In Progress" and go directly to "Code review"

The algorithm searches through the issue's changelog for the first occurrence of a transition to either of these statuses and uses that timestamp as the actual start date.

#### Finish Status Indicators
The system uses only two specific indicators to reliably identify the actual finish date:

1. **Environment Field Change to "Acceptance"**:
   - The most reliable indicator is when the "Environment" field changes to "Acceptance"
   - Example from changelog:
     ```json
     {
       "created": "2025-04-15T15:26:49.030+0200",
       "items": [
         {
           "field": "Environment",
           "fieldtype": "custom",
           "from": "[21188]",
           "fromString": "Integration",
           "to": "[21187]",
           "toString": "Acceptance"
         }
       ]
     }
     ```
   - The timestamp from this environment change event is used as the finish date

2. **"Deployed AC" Status Transition**:
   - When the issue status changes to "Deployed AC", this indicates deployment to the acceptance environment
   - This is used when the Environment field change is not available

The algorithm prioritizes finding the most accurate finish date using the following logic:
1. If an Environment field change to "Acceptance" is found, use that timestamp as the finish date
2. If no Environment field change is found, use the timestamp when the status changed to "Deployed AC"

Other status changes like "Ready for deployment", "Deployed PD", or "Closed" are not considered as finish indicators for the purpose of measuring development time, as they occur after the actual development work is complete and the solution has been deployed to the acceptance environment.

#### Duration Calculation
Once both start and finish dates are determined:
1. The system calculates the duration in days between these dates
2. Weekends (Saturdays and Sundays) are excluded from the calculation
3. The result is stored as "actual_duration" in the BigQuery table

#### Status Change Detection Logic
The parser implements this logic by:
1. Extracting the complete changelog from the Jira issue
2. Filtering for status change events only
3. Mapping each status change to a timestamp
4. Applying the start/finish status rules to determine the actual dates
5. Recording the "method" used to determine each date (which status triggered the selection)

This approach allows for accurate measurement of development time even when issues follow different workflows or have unusual status progression patterns.

## 5. Data Collection Process

### 5.1 Raw Response Collection
The system collects raw JSON responses from the Jira API and saves them to the `jira_raw_responses` directory. This process is handled by the `save_jira_responses.py` script, which:

1. Reads issue keys from the `issue_list.txt` file or command-line arguments
2. Fetches the full issue data from the Jira API for each issue key
3. Saves the raw JSON responses to files with timestamps (e.g., `EI-6172_20250424_134400.json`)
4. Displays basic information about each issue

These raw responses serve as:
- A backup of the original data
- A source for debugging and troubleshooting
- Input for the parser that extracts structured data

### 5.2 Data Extraction and Transformation
The `parser.py` module processes the raw JSON responses and extracts the relevant data points:

1. Basic issue information (key, summary, status, etc.)
2. Planned dates (start, finish, duration)
3. Actual dates (derived from status changes in the changelog)
4. Additional metadata (environment, project ticket, etc.)

The parser uses advanced algorithms to detect actual start and finish dates based on status changes in the issue's changelog.

### 5.3 BigQuery Data Loading
After extraction and transformation, the data is loaded into BigQuery:

1. The system connects to BigQuery using service account credentials
2. It performs upsert operations to update existing records or insert new ones
3. It tracks when details were last updated to prevent unnecessary processing
4. It maintains data consistency by using the issue key as the primary key

## 6. BigQuery Integration Requirements

### 6.1 BigQuery Dataset and Table
- **Dataset ID**: `jira_data`
- **Table ID**: `jira_issues`

### 6.2 BigQuery Table Schema

| Column Name        | Data Type | Mode     | Description                                      |
| ------------------ | --------- | -------- | ------------------------------------------------ |
| issue_key          | STRING    | REQUIRED | Jira issue key (primary key)                     |
| summary            | STRING    | NULLABLE | Issue summary                                    |
| status             | STRING    | NULLABLE | Current issue status                             |
| project_ticket     | STRING    | NULLABLE | Project ticket identifier                        |
| planned_dev_start  | TIMESTAMP | NULLABLE | Planned development start date                   |
| planned_dev_finish | TIMESTAMP | NULLABLE | Planned development finish date                  |
| planned_duration   | FLOAT     | NULLABLE | Planned duration in days (excluding weekends)    |
| actual_start       | TIMESTAMP | NULLABLE | Actual start date (derived from status changes)  |
| actual_finish      | TIMESTAMP | NULLABLE | Actual finish date (derived from status changes) |
| actual_duration    | FLOAT     | NULLABLE | Actual duration in days (excluding weekends)     |
| details_updated_at | TIMESTAMP | NULLABLE | When the details were last updated               |
| last_updated_at    | TIMESTAMP | NULLABLE | When the record was last updated                 |

### 6.3 BigQuery Authentication
- **Authentication Method**: Service Account
- **Credentials Storage**: Environment variable `GOOGLE_APPLICATION_CREDENTIALS` pointing to a JSON key file

### 6.4 Duplicate Prevention Strategy
1. Use `issue_key` as the primary key
2. Use BigQuery's MERGE operations for upserts
3. Selective updates of only the columns that need to be changed
4. Timestamp tracking for when details were last updated

## 7. API Requirements

### 7.1 API Endpoints

#### 7.1.1 Root Endpoint
- **URL**: `/`
- **Method**: GET
- **Description**: Check if the API is running
- **Response**: `{"message": "Jira Logger API is running"}`

#### 7.1.2 Update Status Endpoint
- **URL**: `/api/update-status`
- **Method**: POST
- **Description**: Update status of existing issues and add new ones
- **Response**: JSON object with counts of updated and inserted records

#### 7.1.3 Collect Closed/Deployed PD Details Endpoint
- **URL**: `/api/collect-closed-details`
- **Method**: POST
- **Description**: Collect details for issues in "closed" or "deployed pd" status with empty details
- **Response**: JSON object with counts of updated records

#### 7.1.4 Collect Deployed AC Details Endpoint
- **URL**: `/api/collect-ac-details`
- **Method**: POST
- **Description**: Collect/update details for issues in "deployed ac" status
- **Response**: JSON object with counts of updated records

#### 7.1.5 SSL Certificate Settings Endpoint
- **URL**: `/api/settings`
- **Method**: GET/POST
- **Description**: Get or update SSL certificate settings
- **Request Body** (POST):
  ```json
  {
    "use_ssl_verification": true,
    "certificate_path": "C:\Netskope Certs\rootcaCert.pem"
  }
  ```
- **Response**: Current SSL settings

### 7.2 API Response Format
All API endpoints will return responses in the following format:
```json
{
  "updated_count": 5,
  "inserted_count": 2,
  "error_count": 0,
  "errors": []
}
```

### 7.3 Error Handling
- All errors will be logged and included in the response
- HTTP status codes will be used appropriately (200 for success, 4xx for client errors, 5xx for server errors)
- Detailed error messages will be provided for troubleshooting

## 8. SSL Certificate Requirements

### 8.1 SSL Certificate Handling
- The system will support Netskope SSL certificates for corporate environments
- SSL verification can be enabled or disabled through the API
- Certificate paths can be configured through environment variables or the API

### 8.2 SSL Certificate Configuration
- **Environment Variable**: `SSL_CERT_PATH` (optional)
- **Default Behavior**: Auto-detect Netskope certificate if available
- **Bypass Option**: Allow bypassing SSL verification for testing or when running in cloud environments

## 9. Scheduling Requirements

### 9.1 Execution Frequency
- The system will run daily to update the BigQuery table
- Each endpoint will be called in sequence with appropriate delays

### 9.2 Scheduling Options
1. Python scheduler using the `schedule` library
2. Cron jobs
3. Docker Compose with a dedicated scheduler service
4. Cloud-based schedulers (e.g., Google Cloud Scheduler)

### 9.3 Recommended Schedule
- Update Status: Daily at 1:00 AM
- Collect Closed/Deployed PD Details: Daily at 1:30 AM
- Collect Deployed AC Details: Daily at 1:45 AM

## 10. Deployment Requirements

### 10.1 Environment Variables
The following environment variables must be configured:

| Variable                       | Required | Description                                               |
| ------------------------------ | -------- | --------------------------------------------------------- |
| JIRA_BASE_URL                  | Yes      | Base URL of the Jira instance                             |
| JIRA_API_TOKEN                 | Yes      | API token for Jira authentication                         |
| GOOGLE_APPLICATION_CREDENTIALS | Yes      | Path to Google Cloud service account key file             |
| GOOGLE_CLOUD_PROJECT           | No       | Google Cloud project ID (if not specified in credentials) |
| SSL_CERT_PATH                  | No       | Path to SSL certificate file (if not auto-detected)       |
| API_PORT                       | No       | Port for the FastAPI server (default: 8000)               |
| LOG_LEVEL                      | No       | Logging level (default: INFO)                             |

### 10.2 Deployment Options
1. Local development setup
2. Docker containerization
3. Cloud deployment via GitHub to Google Cloud Run

### 10.3 Resource Requirements
- **Memory**: Minimum 512MB RAM
- **Disk Space**: Minimum 1GB
- **CPU**: Minimum 1 vCPU

### 10.4 Cloud Run Deployment via GitHub
Since the gcloud CLI is not available, the application will be deployed to Google Cloud Run via GitHub. This section outlines the manual steps required to set up and configure the deployment.

#### 10.4.1 Prerequisites
- GitHub repository with the application code
- Google Cloud Platform account with Cloud Run and Cloud Build APIs enabled
- Service account with appropriate permissions

#### 10.4.2 Manual Google Cloud Setup Steps
1. **Create a Google Cloud Project** (if not already created):
   - Go to the Google Cloud Console (https://console.cloud.google.com/)
   - Click on "New Project" and provide a name
   - Note the Project ID as it will be needed later

2. **Enable Required APIs**:
   - Navigate to "APIs & Services" > "Library"
   - Search for and enable the following APIs:
     - Cloud Run API
     - Cloud Build API
     - Container Registry API
     - Secret Manager API (if using secrets)
     - BigQuery API

3. **Create a Service Account**:
   - Go to "IAM & Admin" > "Service Accounts"
   - Click "Create Service Account"
   - Provide a name and description
   - Assign the following roles:
     - Cloud Run Admin
     - Cloud Build Editor
     - Storage Admin
     - BigQuery Admin
     - Secret Manager Admin (if using secrets)
   - Create and download the JSON key file

4. **Set Up Cloud Build Trigger**:
   - Go to "Cloud Build" > "Triggers"
   - Click "Create Trigger"
   - Connect to your GitHub repository
   - Configure the trigger:
     - Name: "jira-logger-deploy"
     - Event: "Push to a branch"
     - Source: Select your repository and branch (e.g., "main")
     - Configuration: "Cloud Build configuration file (yaml or json)"
     - Location: "Repository" (if using a cloudbuild.yaml file in your repo)
   - Click "Create"

5. **Configure Secret Manager** (for environment variables):
   - Go to "Security" > "Secret Manager"
   - Click "Create Secret" for each environment variable:
     - JIRA_BASE_URL:
       - Name: "jira-base-url"
       - Secret value: Enter your Jira instance URL (e.g., "https://your-company.atlassian.net")
       - Regions: "Automatic" (or select specific regions if needed)
     - JIRA_API_TOKEN:
       - Name: "jira-api-token"
       - Secret value: Enter your Jira API token
       - Regions: "Automatic" (or select specific regions if needed)
     - GOOGLE_APPLICATION_CREDENTIALS:
       - Name: "google-application-credentials"
       - Secret value: Upload the service account JSON key file created in step 3
       - Regions: "Automatic" (or select specific regions if needed)
   - For each secret, set appropriate permissions:
     - Click on the secret name after creation
     - Go to the "Permissions" tab
     - Click "Add Principal"
     - Add the Cloud Build service account (e.g., "123456789@cloudbuild.gserviceaccount.com")
     - Assign the "Secret Manager Secret Accessor" role
     - Click "Save"
   - Note the secret names and versions as they will be needed in the cloudbuild.yaml file

6. **Create Cloud Run Service**:
   - Go to "Cloud Run" > "Create Service"
   - Choose "Continuously deploy from a repository"
   - Connect to your GitHub repository
   - Configure the service:
     - Service name: "jira-logger-api"
     - Region: Select appropriate region
     - CPU allocation: "CPU is only allocated during request processing"
     - Minimum instances: 0
     - Maximum instances: 1
     - Memory: 512 MiB
     - CPU: 1
     - Request timeout: 300 seconds
   - Configure environment variables:
     - Add environment variables from Secret Manager
   - Set up authentication:
     - Allow unauthenticated invocations (if public access is needed)
     - Or set up appropriate IAM permissions for authenticated access
   - Click "Create"

#### 10.4.3 GitHub Repository Configuration
1. **Create cloudbuild.yaml File**:
   Add a `cloudbuild.yaml` file to your repository with the following content:

   ```yaml
   steps:
   # Build the container image
   - name: 'gcr.io/cloud-builders/docker'
     args: ['build', '-t', 'gcr.io/$PROJECT_ID/jira-logger-api:$COMMIT_SHA', '.']
   
   # Push the container image to Container Registry
   - name: 'gcr.io/cloud-builders/docker'
     args: ['push', 'gcr.io/$PROJECT_ID/jira-logger-api:$COMMIT_SHA']
   
   # Deploy container image to Cloud Run
   - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
     entrypoint: gcloud
     args:
     - 'run'
     - 'deploy'
     - 'jira-logger-api'
     - '--image'
     - 'gcr.io/$PROJECT_ID/jira-logger-api:$COMMIT_SHA'
     - '--region'
     - 'us-central1'  # Change to your preferred region
     - '--platform'
     - 'managed'
     - '--allow-unauthenticated'  # Remove if authentication is required
     - '--set-secrets'
     - 'JIRA_BASE_URL=jira-base-url:latest,JIRA_API_TOKEN=jira-api-token:latest'
   
   images:
   - 'gcr.io/$PROJECT_ID/jira-logger-api:$COMMIT_SHA'
   ```

2. **Update Dockerfile**:
   Ensure your Dockerfile is optimized for Cloud Run:

   ```dockerfile
   FROM python:3.9-slim
   
   WORKDIR /app
   
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   COPY . .
   
   # Cloud Run will set PORT environment variable
   ENV PORT=8080
   
   # Command to run the application
   CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT}
   ```

#### 10.4.4 Deployment Process
1. **Initial Deployment**:
   - Push your code to the GitHub repository
   - The Cloud Build trigger will automatically build and deploy the application
   - Monitor the build process in the Cloud Build console

2. **Subsequent Deployments**:
   - Any push to the configured branch will trigger a new build and deployment
   - The new version will be deployed automatically

3. **Monitoring**:
   - Monitor the Cloud Run service in the Google Cloud Console
   - View logs in the Cloud Logging console

#### 10.4.5 Scheduling in Cloud Run
For scheduling the API calls, set up Cloud Scheduler jobs:

1. **Create Cloud Scheduler Jobs**:
   - Go to "Cloud Scheduler" > "Create Job"
   - For each endpoint (update-status, collect-closed-details, collect-ac-details):
     - Name: "jira-logger-{endpoint-name}"
     - Frequency: "0 1 * * *" (for 1:00 AM daily, adjust as needed)
     - Timezone: Select appropriate timezone
     - Target: "HTTP"
     - URL: "https://{your-cloud-run-service-url}/api/{endpoint-name}"
     - HTTP method: "POST"
     - Auth header: "Add OIDC token" (if authentication is required)
     - Service account: Select the service account with Cloud Run Invoker permissions
   - Click "Create"

## 11. Testing Requirements

### 11.1 Test Scripts
The following test scripts will be provided:
1. `test_api.py`: Test the API endpoints
2. `test_bigquery_connection.py`: Test the BigQuery connection
3. `setup_google_cloud.py`: Set up Google Cloud credentials

### 11.2 Test Cases
1. Verify API endpoints return expected responses
2. Verify BigQuery connection and operations work correctly
3. Verify Jira API connection and data extraction
4. Verify duplicate prevention strategy works correctly
5. Verify SSL certificate handling works correctly

## 12. Documentation Requirements

### 12.1 Documentation Files
The following documentation will be provided:
1. `README.md`: Overview of the project
2. `API_README.md`: API usage details
3. `docs/implementation_plan.md`: System architecture
4. `docs/deployment_guide.md`: Deployment instructions
5. `docs/PRD.md`: This Product Requirements Document

### 12.2 Code Documentation
- All code will be documented with docstrings
- Complex functions will include parameter descriptions and return value descriptions
- Classes will include class-level documentation

## 13. Future Enhancements

### 13.1 Potential Enhancements
1. Web-based dashboard for monitoring data collection
2. Additional Jira fields and custom field mapping
3. Support for multiple Jira projects
4. Advanced filtering options for issue selection
5. Email notifications for failed operations
6. Integration with other data sources
7. Support for other issue tracking systems

## 14. Implementation Timeline

### 14.1 Phase 1: Core Functionality
- Set up FastAPI project structure
- Implement BigQuery client and table creation
- Create base Jira API client

### 14.2 Phase 2: Endpoint Implementation
- Implement Update Status endpoint
- Implement Collect Closed/Deployed PD Details endpoint
- Implement Collect Deployed AC Details endpoint
- Implement SSL Certificate Settings endpoint

### 14.3 Phase 3: Testing and Deployment
- Create test cases for each endpoint
- Implement error handling and logging
- Set up deployment configuration

## 15. Conclusion

This Product Requirements Document outlines the requirements for the Jira Logger with BigQuery Integration system. The system is designed to automatically collect and store Jira issue data in Google BigQuery for reporting and analysis purposes.

As of 2025-04-24, the system is tracking the following issues:
- EI-5967: Status tracked in jira_raw_responses/EI-5967_20250424_134357.json
- EI-6172: "Deployed PD" status
- EI-6189: Status tracked in jira_raw_responses/EI-6189_20250424_134359.json

The raw responses are stored in the `jira_raw_responses` directory and are used by the parser to extract structured data for loading into BigQuery. This document will be updated as new issues are added or existing issues change status.

## 16. Implemented File Structure

The Jira Logger project has been restructured to improve maintainability, scalability, and code organization. The new file structure is as follows:

```
jira_logger/
│
├── api/                          # API-related code
│   ├── __init__.py
│   ├── endpoints.py              # API endpoint definitions
│   ├── models.py                 # Pydantic models for request/response
│   └── middleware.py             # API middleware (error handling, etc.)
│
├── core/                         # Core business logic
│   ├── __init__.py
│   ├── jira/                     # Jira integration
│   │   ├── __init__.py
│   │   ├── client.py             # Jira API client (from jira_api_helper.py)
│   │   └── parser.py             # Jira data parser (from parser.py)
│   │
│   ├── bigquery/                 # BigQuery integration
│   │   ├── __init__.py
│   │   ├── client.py             # BigQuery client
│   │   └── schema.py             # BigQuery table schema definitions
│   │
│   └── scheduler.py              # Scheduling logic (from schedule_api_calls.py)
│
├── utils/                        # Utility functions and helpers
│   ├── __init__.py
│   ├── ssl_utils.py              # SSL certificate handling (from netskope_certificate.py)
│   ├── date_utils.py             # Date manipulation utilities
│   └── logging.py                # Logging configuration
│
├── data/                         # Data storage
│   ├── jira_raw_responses/       # Raw JSON responses from Jira
│   └── jira_issues/              # Processed Jira issues
│
├── scripts/                      # Standalone scripts
│   ├── save_jira_responses.py    # Script to save Jira responses
│   ├── setup_google_cloud.py     # Google Cloud setup script
│   └── test_scripts/             # Test scripts
│       ├── test_api.py
│       └── test_bigquery_connection.py
│
├── docs/                         # Documentation
│   ├── PRD.md                    # Product Requirements Document
│   ├── deployment_guide.md       # Deployment guide
│   ├── implementation_plan.md    # Implementation plan
│   └── api_docs.md               # API documentation
│
├── config/                       # Configuration files
│   ├── __init__.py
│   ├── settings.py               # Application settings
│   └── environment.py            # Environment-specific settings
│
├── main.py                       # Application entry point
└── run_api.py                    # API server runner
```

In the root directory, the following files are maintained for backward compatibility:
- `main.py`: Imports and uses the jira_logger/main.py file
- `run_api.py`: Imports and uses the jira_logger/run_api.py file
- `save_jira_responses.py`: Imports and uses the jira_logger/scripts/save_jira_responses.py file
- `setup_google_cloud.py`: Imports and uses the jira_logger/scripts/setup_google_cloud.py file
- `test_api.py`: Imports and uses the jira_logger/scripts/test_scripts/test_api.py file
- `test_bigquery_connection.py`: Imports and uses the jira_logger/scripts/test_scripts/test_bigquery_connection.py file

This structure makes the codebase more maintainable, scalable, and easier to understand for new developers joining the project.
