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
For detecting actual start and finish dates:

#### Start Status Indicators
- "In Progress"
- "Code review"

#### Finish Status Indicators
- "Deployed AC"
- "Ready for deployment"

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
3. Cloud deployment (e.g., Google Cloud Run)

### 10.3 Resource Requirements
- **Memory**: Minimum 512MB RAM
- **Disk Space**: Minimum 1GB
- **CPU**: Minimum 1 vCPU

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
3. `documentation/implementation_plan.md`: System architecture
4. `documentation/deployment_guide.md`: Deployment instructions
5. `documentation/PRD.md`: This Product Requirements Document

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
