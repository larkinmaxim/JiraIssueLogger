"""
API Endpoints for Jira Logger

This module defines the FastAPI endpoints for the Jira Logger application.
"""

import os
import datetime
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, BackgroundTasks, Depends

from jira_logger.api import app
from jira_logger.api.models import (
    JiraIssue,
    UpdateRequest,
    UpdateResponse,
    SSLSettingsUpdate,
    SSLSettingsResponse,
)
from jira_logger.core.jira.client import fetch_jira_issue_data
from jira_logger.core.jira.parser import connect_to_jira_api, extract_jira_data
from jira_logger.utils.ssl_utils import (
    configure_ssl_verification,
    find_netskope_certificate,
)
from jira_logger.core.bigquery.client import BigQueryClient

# Define status constants
VALID_STATUSES = ["in progress", "deployed ac", "deployed pd", "closed"]

# SSL Certificate settings
SSL_SETTINGS = {
    "use_ssl_verification": True,
    "certificate_path": os.environ.get("SSL_CERT_PATH", find_netskope_certificate()),
    "last_updated": datetime.datetime.utcnow().isoformat(),
}


def get_bigquery_client():
    """
    Get a BigQuery client.

    Returns:
        BigQueryClient: A BigQuery client
    """
    client = BigQueryClient()
    client.ensure_bigquery_setup()
    return client


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
    # Get BigQuery client
    bigquery_client = get_bigquery_client()

    # Construct JQL query to fetch issues with valid statuses
    status_clause = " OR ".join([f'status = "{status}"' for status in VALID_STATUSES])
    jql_query = f'project in (EI) AND issuetype = Project AND "Project ticket" is not EMPTY and "Start Date" is not empty and "End date" is not empty AND ({status_clause})'

    try:
        # Fetch issues from Jira
        issues = fetch_jira_issues(jql_query)

        if not issues:
            return UpdateResponse(updated_count=0, inserted_count=0, error_count=0)

        # Update issues in BigQuery
        result = bigquery_client.update_issues_status(issues)
        return UpdateResponse(**result)

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
    # Get BigQuery client
    bigquery_client = get_bigquery_client()

    try:
        # Get issues needing details
        issue_keys = bigquery_client.get_issues_needing_details(
            ["closed", "deployed pd"]
        )

        if not issue_keys:
            return UpdateResponse(updated_count=0, inserted_count=0, error_count=0)

        # Fetch details for each issue
        updated_issues = []
        errors = []
        current_timestamp = datetime.datetime.utcnow().isoformat()

        for issue_key in issue_keys:
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

        # Update issues in BigQuery
        result = bigquery_client.update_issue_details(updated_issues)
        result["errors"] = errors
        result["error_count"] = len(errors)
        return UpdateResponse(**result)

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
    # Get BigQuery client
    bigquery_client = get_bigquery_client()

    try:
        # Get issues in "deployed ac" status
        issue_keys = bigquery_client.get_issues_by_status("deployed ac")

        if not issue_keys:
            return UpdateResponse(updated_count=0, inserted_count=0, error_count=0)

        # Fetch details for each issue
        updated_issues = []
        errors = []
        current_timestamp = datetime.datetime.utcnow().isoformat()

        for issue_key in issue_keys:
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

        # Update issues in BigQuery
        result = bigquery_client.update_issue_details(updated_issues)
        result["errors"] = errors
        result["error_count"] = len(errors)
        return UpdateResponse(**result)

    except Exception as e:
        return UpdateResponse(
            updated_count=0, inserted_count=0, error_count=1, errors=[str(e)]
        )


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
        if not os.path.exists(settings.certificate_path):
            raise HTTPException(
                status_code=400,
                detail=f"Certificate file not found at: {settings.certificate_path}",
            )
        SSL_SETTINGS["certificate_path"] = settings.certificate_path
    elif not settings.use_ssl_verification:
        # If SSL verification is disabled, we don't need a certificate path
        SSL_SETTINGS["certificate_path"] = None

    # Update the last_updated timestamp
    SSL_SETTINGS["last_updated"] = datetime.datetime.utcnow().isoformat()

    return SSLSettingsResponse(
        use_ssl_verification=SSL_SETTINGS["use_ssl_verification"],
        certificate_path=SSL_SETTINGS["certificate_path"],
        last_updated=SSL_SETTINGS["last_updated"],
    )


def fetch_jira_issues(jql_query: str) -> List[Dict[str, Any]]:
    """
    Fetch Jira issues using the Jira API.

    Args:
        jql_query: JQL query to filter issues

    Returns:
        List of Jira issues
    """
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
                    "planned_duration": None,  # Will be calculated by BigQuery client
                    "start_date": start_date,
                    "end_date": end_date,
                }
            )

        return issues

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching Jira issues: {str(e)}"
        )
