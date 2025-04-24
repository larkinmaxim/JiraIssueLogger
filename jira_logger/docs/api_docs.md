# Jira Logger API Documentation

This document provides detailed information about the Jira Logger API endpoints, request/response formats, and usage examples.

## API Overview

The Jira Logger API provides endpoints for:
1. Updating the status of Jira issues in BigQuery
2. Collecting details for issues in "closed" or "deployed pd" status
3. Collecting details for issues in "deployed ac" status
4. Configuring SSL certificate settings

## Base URL

When running locally, the API is available at:
```
http://localhost:8000
```

## Authentication

The API does not require authentication for requests. However, it uses the Jira API token and BigQuery credentials configured in the environment variables.

## API Endpoints

### 1. Root Endpoint

**URL**: `/`  
**Method**: GET  
**Description**: Check if the API is running  

#### Response

```json
{
  "message": "Jira Logger API is running"
}
```

### 2. Update Status Endpoint

**URL**: `/api/update-status`  
**Method**: POST  
**Description**: Update status of existing issues and add new ones  

#### Request Body (Optional)

```json
{
  "save_raw_response": false,
  "raw_response_dir": "jira_logger/data/jira_raw_responses"
}
```

#### Response

```json
{
  "updated_count": 5,
  "inserted_count": 2,
  "error_count": 0,
  "errors": []
}
```

### 3. Collect Closed/Deployed PD Details Endpoint

**URL**: `/api/collect-closed-details`  
**Method**: POST  
**Description**: Collect details for issues in "closed" or "deployed pd" status with empty details  

#### Request Body (Optional)

```json
{
  "save_raw_response": false,
  "raw_response_dir": "jira_logger/data/jira_raw_responses"
}
```

#### Response

```json
{
  "updated_count": 3,
  "inserted_count": 0,
  "error_count": 0,
  "errors": []
}
```

### 4. Collect Deployed AC Details Endpoint

**URL**: `/api/collect-ac-details`  
**Method**: POST  
**Description**: Collect/update details for issues in "deployed ac" status  

#### Request Body (Optional)

```json
{
  "save_raw_response": false,
  "raw_response_dir": "jira_logger/data/jira_raw_responses"
}
```

#### Response

```json
{
  "updated_count": 2,
  "inserted_count": 0,
  "error_count": 0,
  "errors": []
}
```

### 5. SSL Certificate Settings Endpoint

#### Get SSL Settings

**URL**: `/api/settings/ssl`  
**Method**: GET  
**Description**: Get the current SSL certificate settings  

##### Response

```json
{
  "use_ssl_verification": true,
  "certificate_path": "C:\\Netskope Certs\\rootcaCert.pem",
  "last_updated": "2025-04-24T15:30:45.123456"
}
```

#### Update SSL Settings

**URL**: `/api/settings/ssl`  
**Method**: POST  
**Description**: Update the SSL certificate settings  

##### Request Body

```json
{
  "use_ssl_verification": true,
  "certificate_path": "C:\\Netskope Certs\\rootcaCert.pem"
}
```

##### Response

```json
{
  "use_ssl_verification": true,
  "certificate_path": "C:\\Netskope Certs\\rootcaCert.pem",
  "last_updated": "2025-04-24T15:35:12.456789"
}
```

## Error Responses

When an error occurs, the API returns a JSON response with an error message:

```json
{
  "updated_count": 0,
  "inserted_count": 0,
  "error_count": 1,
  "errors": ["Error message details"]
}
```

For HTTP errors, the response follows this format:

```json
{
  "detail": "Error message"
}
```

## Usage Examples

### Using curl

#### Check if the API is running

```bash
curl -X GET http://localhost:8000/
```

#### Update status of Jira issues

```bash
curl -X POST http://localhost:8000/api/update-status
```

#### Collect details for closed issues

```bash
curl -X POST http://localhost:8000/api/collect-closed-details
```

#### Collect details for deployed AC issues

```bash
curl -X POST http://localhost:8000/api/collect-ac-details
```

#### Get SSL settings

```bash
curl -X GET http://localhost:8000/api/settings/ssl
```

#### Update SSL settings

```bash
curl -X POST http://localhost:8000/api/settings/ssl \
  -H "Content-Type: application/json" \
  -d '{"use_ssl_verification": true, "certificate_path": "C:\\Netskope Certs\\rootcaCert.pem"}'
```

### Using Python requests

```python
import requests

# Base URL
base_url = "http://localhost:8000"

# Check if the API is running
response = requests.get(f"{base_url}/")
print(response.json())

# Update status of Jira issues
response = requests.post(f"{base_url}/api/update-status")
print(response.json())

# Collect details for closed issues
response = requests.post(f"{base_url}/api/collect-closed-details")
print(response.json())

# Collect details for deployed AC issues
response = requests.post(f"{base_url}/api/collect-ac-details")
print(response.json())

# Get SSL settings
response = requests.get(f"{base_url}/api/settings/ssl")
print(response.json())

# Update SSL settings
ssl_settings = {
    "use_ssl_verification": True,
    "certificate_path": "C:\\Netskope Certs\\rootcaCert.pem"
}
response = requests.post(f"{base_url}/api/settings/ssl", json=ssl_settings)
print(response.json())
```

## Interactive Documentation

When the API is running, you can access the interactive Swagger UI documentation at:

```
http://localhost:8000/docs
```

This provides a user-friendly interface to explore and test the API endpoints.

## Data Models

### JiraIssue

```json
{
  "issue_key": "EI-1234",
  "summary": "Issue summary",
  "status": "deployed ac",
  "project_ticket": "CXPRODELIVERY-5039",
  "planned_dev_start": "2025-03-12T00:00:00.000Z",
  "planned_dev_finish": "2025-04-02T00:00:00.000Z",
  "planned_duration": 15.0,
  "actual_start": "2025-03-19T16:13:27.150+0100",
  "actual_finish": "2025-04-03T15:01:57.044+0200",
  "actual_duration": 11.5,
  "details_updated_at": "2025-04-24T15:35:12.456789"
}
```

### UpdateRequest

```json
{
  "save_raw_response": false,
  "raw_response_dir": "jira_logger/data/jira_raw_responses"
}
```

### UpdateResponse

```json
{
  "updated_count": 5,
  "inserted_count": 2,
  "error_count": 0,
  "errors": []
}
```

### SSLSettingsUpdate

```json
{
  "use_ssl_verification": true,
  "certificate_path": "C:\\Netskope Certs\\rootcaCert.pem"
}
```

### SSLSettingsResponse

```json
{
  "use_ssl_verification": true,
  "certificate_path": "C:\\Netskope Certs\\rootcaCert.pem",
  "last_updated": "2025-04-24T15:35:12.456789"
}
