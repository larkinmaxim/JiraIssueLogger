"""
Jira Logger with BigQuery Integration

This FastAPI application provides endpoints to:
1. Update status of Jira issues in BigQuery
2. Collect details for issues in "closed" or "deployed pd" status with empty details
3. Collect/update details for issues in "deployed ac" status
4. Configure SSL certificate settings

The application prevents duplicates in the BigQuery table by using MERGE operations.
"""

import os
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

# Import existing Jira API code
from jira_api_helper import fetch_jira_issue_data, detect_actual_dates
from parser import calculate_duration, connect_to_jira_api, extract_jira_data
from netskope_certificate import configure_ssl_verification, find_netskope_certificate

# Create FastAPI app
app = FastAPI(
    title="Jira Logger",
    description="API for logging Jira issues to BigQuery",
    version="1.0.0",
)

# Define status constants
VALID_STATUSES = ["in progress", "deployed ac", "deployed pd", "closed"]

# SSL Certificate settings
SSL_SETTINGS = {
    "use_ssl_verification": True,
    "certificate_path": os.environ.get("SSL_CERT_PATH", find_netskope_certificate()),
    "last_updated": datetime.utcnow().isoformat(),
}

# Define BigQuery table schema
SCHEMA = [
    bigquery.SchemaField("issue_key", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("summary", "STRING"),
    bigquery.SchemaField("status", "STRING"),
    bigquery.SchemaField("project_ticket", "STRING"),
    bigquery.SchemaField("planned_dev_start", "TIMESTAMP"),
    bigquery.SchemaField("planned_dev_finish", "TIMESTAMP"),
    bigquery.SchemaField("planned_duration", "FLOAT"),
    bigquery.SchemaField("actual_start", "TIMESTAMP"),
    bigquery.SchemaField("actual_finish", "TIMESTAMP"),
    bigquery.SchemaField("actual_duration", "FLOAT"),
    bigquery.SchemaField("details_updated_at", "TIMESTAMP"),
    bigquery.SchemaField("last_updated_at", "TIMESTAMP"),
]

# Initialize BigQuery client
bigquery_client = bigquery.Client()

# Define dataset and table names
DATASET_ID = "jira_data"
TABLE_ID = "jira_issues"
TABLE_REF = f"{DATASET_ID}.{TABLE_ID}"


# Pydantic models for request/response validation
class JiraIssue(BaseModel):
    issue_key: str
    summary: str
    status: str
    project_ticket: Optional[str] = None
    planned_dev_start: Optional[str] = None
    planned_dev_finish: Optional[str] = None
    planned_duration: Optional[float] = None
    actual_start: Optional[str] = None
    actual_finish: Optional[str] = None
    actual_duration: Optional[float] = None
    details_updated_at: Optional[str] = None


class UpdateRequest(BaseModel):
    save_raw_response: bool = False
    raw_response_dir: str = "jira_raw_responses"


class UpdateResponse(BaseModel):
    updated_count: int
    inserted_count: int
    error_count: int
    errors: List[str] = []


# Helper functions
def ensure_bigquery_table_exists():
    """Ensure the BigQuery dataset and table exist, creating them if necessary."""
    # Check if dataset exists, create if not
    try:
        bigquery_client.get_dataset(DATASET_ID)
    except NotFound:
        dataset = bigquery.Dataset(f"{bigquery_client.project}.{DATASET_ID}")
        dataset.location = "US"  # Set the dataset location
        bigquery_client.create_dataset(dataset)
        print(f"Created dataset {DATASET_ID}")

    # Check if table exists, create if not
    try:
        bigquery_client.get_table(TABLE_REF)
    except NotFound:
        table = bigquery.Table(f"{bigquery_client.project}.{TABLE_REF}", schema=SCHEMA)
        bigquery_client.create_table(table)
        print(f"Created table {TABLE_REF}")


def fetch_jira_issues(jql_query: str) -> List[Dict[str, Any]]:
    """
    Fetch Jira issues using the existing code from get_jira_issues_example.py

    Args:
        jql_query: JQL query to filter issues

    Returns:
        List of Jira issues
    """
    # This is a simplified version - in production, you'd reuse more code from get_jira_issues_example.py
    import requests
    from dotenv import load_dotenv

    # Load environment variables
    load_dotenv()

    # Get Jira credentials from environment variables
    jira_url = os.getenv("JIRA_BASE_URL", "https://support.transporeon.com")
    api_token = os.getenv("JIRA_API_TOKEN")

    # Validate required credentials
    if not api_token:
        raise ValueError("JIRA_API_TOKEN must be set in the .env file")

    # Configure SSL verification based on settings
    bypass_verify = not SSL_SETTINGS["use_ssl_verification"]
    cert_path = SSL_SETTINGS["certificate_path"]
    verify, _ = configure_ssl_verification(
        cert_path=cert_path, bypass_verify=bypass_verify
    )

    # API endpoint for searching issues
    search_api_endpoint = f"{jira_url}/rest/api/2/search"

    # Set up the request headers
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_token}",
    }

    # Prepare the request payload
    payload = {
        "jql": jql_query,
        "startAt": 0,
        "maxResults": 100,  # Adjust as needed
        "fields": [
            "summary",
            "status",
            "project",
            "issuetype",
            "customfield_11491",  # Project ticket
            "customfield_21500",  # Start Date
            "customfield_27491",  # End date
            "customfield_15990",  # Planned dev start
            "customfield_15994",  # Planned dev finish
            "created",
            "updated",
        ],
    }

    # Make the API request
    try:
        response = requests.post(
            search_api_endpoint,
            headers=headers,
            json=payload,
            verify=verify,
        )

        # Check if the request was successful
        response.raise_for_status()

        # Parse the JSON response
        data = response.json()

        # Process the results
        issues = []
        for issue in data.get("issues", []):
            issue_key = issue["key"]
            fields = issue["fields"]

            # Extract relevant fields
            summary = fields.get("summary", "")
            status = fields.get("status", {}).get("name", "").lower()

            # Extract custom fields
            project_ticket = fields.get("customfield_11491", "")
            start_date = fields.get("customfield_21500", "")
            end_date = fields.get("customfield_27491", "")
            planned_dev_start = fields.get("customfield_15990", "")
            planned_dev_finish = fields.get("customfield_15994", "")

            # Add to issues list
            issues.append(
                {
                    "issue_key": issue_key,
                    "summary": summary,
                    "status": status,
                    "project_ticket": project_ticket,
                    "planned_dev_start": planned_dev_start,
                    "planned_dev_finish": planned_dev_finish,
                    "planned_duration": calculate_duration(
                        planned_dev_start, planned_dev_finish
                    ),
                    "start_date": start_date,
                    "end_date": end_date,
                }
            )

        return issues

    except Exception as e:
        print(f"Error fetching Jira issues: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error fetching Jira issues: {str(e)}"
        )


# API Endpoints
@app.get("/")
async def root():
    """Root endpoint to check if the API is running."""
    return {"message": "Jira Logger API is running"}


@app.post("/api/update-status", response_model=UpdateResponse)
async def update_status(request: UpdateRequest = UpdateRequest()):
    """
    Update status of existing issues and add new ones.

    This endpoint:
    1. Fetches all Jira issues with statuses in the specified array
    2. Updates status for existing issues in BigQuery
    3. Adds new issues not yet in the table
    """
    # Ensure BigQuery table exists
    ensure_bigquery_table_exists()

    # Construct JQL query to fetch issues with valid statuses
    status_clause = " OR ".join([f'status = "{status}"' for status in VALID_STATUSES])
    jql_query = f'project in (EI) AND issuetype = Project AND "Project ticket" is not EMPTY and "Start Date" is not empty and "End date" is not empty AND ({status_clause})'

    try:
        # Fetch issues from Jira
        issues = fetch_jira_issues(jql_query)

        if not issues:
            return UpdateResponse(updated_count=0, inserted_count=0, error_count=0)

        # Prepare data for BigQuery
        rows_to_insert = []
        current_timestamp = datetime.utcnow().isoformat()

        for issue in issues:
            row = {
                "issue_key": issue["issue_key"],
                "summary": issue["summary"],
                "status": issue["status"],
                "project_ticket": issue["project_ticket"],
                "planned_dev_start": issue["planned_dev_start"],
                "planned_dev_finish": issue["planned_dev_finish"],
                "planned_duration": issue["planned_duration"],
                "last_updated_at": current_timestamp,
            }
            rows_to_insert.append(row)

        # Create a temporary table for the new data
        temp_table_id = (
            f"{DATASET_ID}.temp_issues_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        job_config = bigquery.LoadJobConfig(
            schema=SCHEMA,
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        )

        # Load data into temporary table
        job = bigquery_client.load_table_from_json(
            rows_to_insert, temp_table_id, job_config=job_config
        )
        job.result()  # Wait for the job to complete

        # Perform MERGE operation to update existing records and insert new ones
        merge_query = f"""
        MERGE `{TABLE_REF}` T
        USING `{temp_table_id}` S
        ON T.issue_key = S.issue_key
        WHEN MATCHED THEN
          UPDATE SET 
            T.status = S.status,
            T.summary = S.summary,
            T.project_ticket = S.project_ticket,
            T.planned_dev_start = S.planned_dev_start,
            T.planned_dev_finish = S.planned_dev_finish,
            T.planned_duration = S.planned_duration,
            T.last_updated_at = S.last_updated_at
        WHEN NOT MATCHED THEN
          INSERT (issue_key, summary, status, project_ticket, planned_dev_start, planned_dev_finish, planned_duration, last_updated_at)
          VALUES (issue_key, summary, status, project_ticket, planned_dev_start, planned_dev_finish, planned_duration, last_updated_at)
        """

        merge_job = bigquery_client.query(merge_query)
        merge_result = merge_job.result()

        # Clean up temporary table
        bigquery_client.delete_table(temp_table_id)

        # Get counts of updated and inserted rows
        # Note: This is an approximation as BigQuery doesn't provide exact counts
        count_query = f"""
        SELECT
          COUNTIF(operation = 'UPDATE') as updated_count,
          COUNTIF(operation = 'INSERT') as inserted_count
        FROM `{bigquery_client.project}.{DATASET_ID}.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
        WHERE job_id = '{merge_job.job_id}'
        """

        count_job = bigquery_client.query(count_query)
        count_result = list(count_job.result())

        if count_result:
            updated_count = count_result[0].get("updated_count", 0)
            inserted_count = count_result[0].get("inserted_count", 0)
        else:
            # Fallback if we can't get exact counts
            updated_count = len(issues)
            inserted_count = 0

        return UpdateResponse(
            updated_count=updated_count, inserted_count=inserted_count, error_count=0
        )

    except Exception as e:
        return UpdateResponse(
            updated_count=0, inserted_count=0, error_count=1, errors=[str(e)]
        )


@app.post("/api/collect-closed-details", response_model=UpdateResponse)
async def collect_closed_details(request: UpdateRequest = UpdateRequest()):
    """
    Collect details for issues in "closed" or "deployed pd" status with empty details.

    This endpoint:
    1. Queries BigQuery for issues with empty details
    2. Fetches detailed information from Jira API
    3. Updates only the details columns in BigQuery
    """
    # Ensure BigQuery table exists
    ensure_bigquery_table_exists()

    try:
        # Query BigQuery for issues with empty details
        query = f"""
        SELECT issue_key
        FROM `{TABLE_REF}`
        WHERE (status = 'closed' OR status = 'deployed pd')
        AND (actual_start IS NULL OR actual_finish IS NULL OR actual_duration IS NULL)
        """

        query_job = bigquery_client.query(query)
        results = list(query_job.result())

        if not results:
            return UpdateResponse(updated_count=0, inserted_count=0, error_count=0)

        # Fetch details for each issue
        updated_issues = []
        errors = []
        current_timestamp = datetime.utcnow().isoformat()

        for row in results:
            issue_key = row.get("issue_key")
            try:
                # Fetch Jira issue data using global SSL settings
                jira_data = connect_to_jira_api(
                    issue_key,
                    bypass_ssl_verify=None,
                    save_raw_response=request.save_raw_response,
                    raw_response_dir=request.raw_response_dir,
                )

                if jira_data:
                    # Extract details
                    details = extract_jira_data(jira_data)

                    if details:
                        # Prepare data for BigQuery
                        updated_issue = {
                            "issue_key": issue_key,
                            "actual_start": details["Actual"]["Actual start"],
                            "actual_finish": details["Actual"]["Actual finish"],
                            "actual_duration": details["Actual"]["Actual duration"],
                            "details_updated_at": current_timestamp,
                        }
                        updated_issues.append(updated_issue)
                    else:
                        errors.append(
                            f"Could not extract details for issue {issue_key}"
                        )
                else:
                    errors.append(f"Failed to retrieve Jira data for issue {issue_key}")

            except Exception as e:
                errors.append(f"Error processing issue {issue_key}: {str(e)}")

        if not updated_issues:
            return UpdateResponse(
                updated_count=0,
                inserted_count=0,
                error_count=len(errors),
                errors=errors,
            )

        # Create a temporary table for the updated data
        temp_table_id = (
            f"{DATASET_ID}.temp_details_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        job_config = bigquery.LoadJobConfig(
            schema=[
                bigquery.SchemaField("issue_key", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("actual_start", "TIMESTAMP"),
                bigquery.SchemaField("actual_finish", "TIMESTAMP"),
                bigquery.SchemaField("actual_duration", "FLOAT"),
                bigquery.SchemaField("details_updated_at", "TIMESTAMP"),
            ],
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        )

        # Load data into temporary table
        job = bigquery_client.load_table_from_json(
            updated_issues, temp_table_id, job_config=job_config
        )
        job.result()  # Wait for the job to complete

        # Perform MERGE operation to update details
        merge_query = f"""
        MERGE `{TABLE_REF}` T
        USING `{temp_table_id}` S
        ON T.issue_key = S.issue_key
        WHEN MATCHED THEN
          UPDATE SET 
            T.actual_start = S.actual_start,
            T.actual_finish = S.actual_finish,
            T.actual_duration = S.actual_duration,
            T.details_updated_at = S.details_updated_at
        """

        merge_job = bigquery_client.query(merge_query)
        merge_job.result()

        # Clean up temporary table
        bigquery_client.delete_table(temp_table_id)

        return UpdateResponse(
            updated_count=len(updated_issues),
            inserted_count=0,
            error_count=len(errors),
            errors=errors,
        )

    except Exception as e:
        return UpdateResponse(
            updated_count=0, inserted_count=0, error_count=1, errors=[str(e)]
        )


@app.post("/api/collect-ac-details", response_model=UpdateResponse)
async def collect_ac_details(request: UpdateRequest = UpdateRequest()):
    """
    Collect/update details for issues in "deployed ac" status.

    This endpoint:
    1. Queries all issues in "deployed ac" status
    2. Gets detailed information from Jira
    3. Updates the details in BigQuery, overwriting existing data if necessary
    """
    # Ensure BigQuery table exists
    ensure_bigquery_table_exists()

    try:
        # Query BigQuery for issues in "deployed ac" status
        query = f"""
        SELECT issue_key
        FROM `{TABLE_REF}`
        WHERE status = 'deployed ac'
        """

        query_job = bigquery_client.query(query)
        results = list(query_job.result())

        if not results:
            return UpdateResponse(updated_count=0, inserted_count=0, error_count=0)

        # Fetch details for each issue
        updated_issues = []
        errors = []
        current_timestamp = datetime.utcnow().isoformat()

        for row in results:
            issue_key = row.get("issue_key")
            try:
                # Fetch Jira issue data using global SSL settings
                jira_data = connect_to_jira_api(
                    issue_key,
                    bypass_ssl_verify=None,
                    save_raw_response=request.save_raw_response,
                    raw_response_dir=request.raw_response_dir,
                )

                if jira_data:
                    # Extract details
                    details = extract_jira_data(jira_data)

                    if details:
                        # Prepare data for BigQuery
                        updated_issue = {
                            "issue_key": issue_key,
                            "actual_start": details["Actual"]["Actual start"],
                            "actual_finish": details["Actual"]["Actual finish"],
                            "actual_duration": details["Actual"]["Actual duration"],
                            "details_updated_at": current_timestamp,
                        }
                        updated_issues.append(updated_issue)
                    else:
                        errors.append(
                            f"Could not extract details for issue {issue_key}"
                        )
                else:
                    errors.append(f"Failed to retrieve Jira data for issue {issue_key}")

            except Exception as e:
                errors.append(f"Error processing issue {issue_key}: {str(e)}")

        if not updated_issues:
            return UpdateResponse(
                updated_count=0,
                inserted_count=0,
                error_count=len(errors),
                errors=errors,
            )

        # Create a temporary table for the updated data
        temp_table_id = (
            f"{DATASET_ID}.temp_ac_details_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        job_config = bigquery.LoadJobConfig(
            schema=[
                bigquery.SchemaField("issue_key", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("actual_start", "TIMESTAMP"),
                bigquery.SchemaField("actual_finish", "TIMESTAMP"),
                bigquery.SchemaField("actual_duration", "FLOAT"),
                bigquery.SchemaField("details_updated_at", "TIMESTAMP"),
            ],
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        )

        # Load data into temporary table
        job = bigquery_client.load_table_from_json(
            updated_issues, temp_table_id, job_config=job_config
        )
        job.result()  # Wait for the job to complete

        # Perform MERGE operation to update details
        merge_query = f"""
        MERGE `{TABLE_REF}` T
        USING `{temp_table_id}` S
        ON T.issue_key = S.issue_key
        WHEN MATCHED THEN
          UPDATE SET 
            T.actual_start = S.actual_start,
            T.actual_finish = S.actual_finish,
            T.actual_duration = S.actual_duration,
            T.details_updated_at = S.details_updated_at
        """

        merge_job = bigquery_client.query(merge_query)
        merge_job.result()

        # Clean up temporary table
        bigquery_client.delete_table(temp_table_id)

        return UpdateResponse(
            updated_count=len(updated_issues),
            inserted_count=0,
            error_count=len(errors),
            errors=errors,
        )

    except Exception as e:
        return UpdateResponse(
            updated_count=0, inserted_count=0, error_count=1, errors=[str(e)]
        )


# SSL Settings models
class SSLSettingsUpdate(BaseModel):
    use_ssl_verification: bool
    certificate_path: Optional[str] = None


class SSLSettingsResponse(BaseModel):
    use_ssl_verification: bool
    certificate_path: Optional[str] = None
    last_updated: str


@app.get("/api/settings/ssl", response_model=SSLSettingsResponse)
async def get_ssl_settings():
    """
    Get the current SSL certificate settings.

    This endpoint returns the current SSL certificate settings, including whether
    SSL verification is enabled and the path to the certificate file.
    """
    return SSLSettingsResponse(
        use_ssl_verification=SSL_SETTINGS["use_ssl_verification"],
        certificate_path=SSL_SETTINGS["certificate_path"],
        last_updated=SSL_SETTINGS["last_updated"],
    )


@app.post("/api/settings/ssl", response_model=SSLSettingsResponse)
async def update_ssl_settings(settings: SSLSettingsUpdate):
    """
    Update the SSL certificate settings.

    This endpoint allows you to enable or disable SSL verification and set the path
    to the certificate file. This is particularly useful when running the application
    locally (where SSL verification might be needed) versus in the cloud (where it
    might not be needed).
    """
    global SSL_SETTINGS

    # Update the settings
    SSL_SETTINGS["use_ssl_verification"] = settings.use_ssl_verification

    if settings.certificate_path:
        # Verify the certificate path exists if provided
        cert_path = Path(settings.certificate_path)
        if not cert_path.exists():
            raise HTTPException(
                status_code=400,
                detail=f"Certificate file not found at: {settings.certificate_path}",
            )
        SSL_SETTINGS["certificate_path"] = str(cert_path)
    elif not settings.use_ssl_verification:
        # If SSL verification is disabled, we don't need a certificate path
        SSL_SETTINGS["certificate_path"] = None

    # Update the last_updated timestamp
    SSL_SETTINGS["last_updated"] = datetime.utcnow().isoformat()

    return SSLSettingsResponse(
        use_ssl_verification=SSL_SETTINGS["use_ssl_verification"],
        certificate_path=SSL_SETTINGS["certificate_path"],
        last_updated=SSL_SETTINGS["last_updated"],
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
