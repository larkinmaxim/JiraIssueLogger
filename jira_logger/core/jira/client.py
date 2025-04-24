"""
Jira API Helper Script for Retrieving and Analyzing Issue Changelog Data

This script provides utilities to fetch, save, and analyze Jira issue changelog data
to help understand the complexities of extracting actual start and finish dates.
"""

import json
import os
import datetime
import requests
from dotenv import load_dotenv

from jira_logger.utils.ssl_utils import (
    find_netskope_certificate,
    configure_ssl_verification,
    print_ssl_debug_info,
)

# Load environment variables
load_dotenv()

# Define development-related statuses
DEVELOPMENT_STATUSES = {
    "start": ["In Progress", "Code review"],
    "finish": ["Deployed AC", "Ready for deployment"],
}

# Define logging level
LOG_LEVEL = "DEBUG"  # Can be "INFO", "DEBUG", "WARN"


def log(message, level="INFO"):
    """
    Logging function with configurable log levels
    """
    log_levels = {"WARN": 3, "INFO": 2, "DEBUG": 1}
    current_level = log_levels.get(LOG_LEVEL, 2)
    message_level = log_levels.get(level, 2)

    if message_level >= current_level:
        print(f"[{level}] {message}")


def fetch_jira_issue_data(issue_key, bypass_ssl_verify=True):
    """
    Fetch Jira issue data with expanded changelog

    Args:
        issue_key (str): Jira issue key
        bypass_ssl_verify (bool): SSL verification flag

    Returns:
        dict: Jira issue data or None if fetch fails
    """
    # Retrieve credentials from environment variables
    base_url = os.getenv("JIRA_BASE_URL")
    api_token = os.getenv("JIRA_API_TOKEN")

    if not all([base_url, api_token]):
        raise ValueError(
            "Missing Jira API credentials. Please set JIRA_BASE_URL and JIRA_API_TOKEN in .env file."
        )

    url = f"{base_url}/rest/api/2/issue/{issue_key}?expand=changelog"

    headers = {"Accept": "application/json", "Authorization": f"Bearer {api_token}"}

    # Find Netskope certificate
    netskope_cert_path = find_netskope_certificate()

    # Configure SSL verification
    verify, _ = configure_ssl_verification(
        cert_path=netskope_cert_path, bypass_verify=bypass_ssl_verify
    )

    try:
        response = requests.get(url, headers=headers, verify=verify)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Jira issue data: {e}")
        return None


def save_jira_issue_data(issue_key, data=None):
    """
    Save Jira issue data to a JSON file for later analysis

    Args:
        issue_key (str): Jira issue key
        data (dict, optional): Jira issue data to save. If None, fetches data.
    """
    # Create a 'jira_issues' directory if it doesn't exist
    os.makedirs("jira_logger/data/jira_issues", exist_ok=True)

    # Fetch data if not provided
    if data is None:
        data = fetch_jira_issue_data(issue_key)

    if data:
        # Create filename with timestamp to avoid overwriting
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"jira_logger/data/jira_issues/{issue_key}_{timestamp}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"Saved issue data to {filename}")
        return filename

    return None


def detect_actual_dates(data):
    """
    Advanced detection of actual start and finish dates from changelog

    Args:
        data (dict): Jira issue data

    Returns:
        dict: Detected actual start and finish dates with detection method
    """
    if not data:
        return {
            "start": None,
            "finish": None,
            "start_method": None,
            "finish_method": None,
        }

    # Collect all status changes
    status_changes = []
    for history in data.get("changelog", {}).get("histories", []):
        for item in history.get("items", []):
            if item.get("field") == "status":
                change = {
                    "created": history.get("created"),
                    "from": item.get("fromString"),
                    "to": item.get("toString"),
                }
                status_changes.append(change)

    # Detect start date strategies
    start_strategies = [
        # First development-related status
        next(
            (
                change["created"]
                for change in status_changes
                if change["to"] in DEVELOPMENT_STATUSES["start"]
            ),
            None,
        ),
        # First 'In Progress' after 'Ready for planning'
        next(
            (
                change["created"]
                for i, change in enumerate(status_changes)
                if change["to"] == "In Progress"
                and any(
                    prev["to"] == "Ready for planning" for prev in status_changes[:i]
                )
            ),
            None,
        ),
        # First non-initial status
        status_changes[0]["created"] if status_changes else None,
    ]

    # Detect finish date strategies
    finish_strategies = [
        # Last development-related finish status
        next(
            (
                change["created"]
                for change in reversed(status_changes)
                if change["to"] in DEVELOPMENT_STATUSES["finish"]
            ),
            None,
        ),
        # Last 'Deployed AC' status
        next(
            (
                change["created"]
                for change in reversed(status_changes)
                if change["to"] == "Deployed AC"
            ),
            None,
        ),
        # Last status change
        status_changes[-1]["created"] if status_changes else None,
    ]

    # Select the first non-None strategy
    start_date = next((date for date in start_strategies if date is not None), None)
    finish_date = next((date for date in finish_strategies if date is not None), None)

    # Determine detection methods
    start_method = (
        "First development status"
        if start_date == start_strategies[0]
        else "First 'In Progress' after planning"
        if start_date == start_strategies[1]
        else "First status change"
    )

    finish_method = (
        "Last development finish status"
        if finish_date == finish_strategies[0]
        else "Last 'Deployed AC' status"
        if finish_date == finish_strategies[1]
        else "Last status change"
    )

    # Debug logging
    log(f"Start Strategies: {[str(s) for s in start_strategies]}", "DEBUG")
    log(f"Finish Strategies: {[str(s) for s in finish_strategies]}", "DEBUG")
    log(f"Selected Start Date: {start_date} (Method: {start_method})", "DEBUG")
    log(f"Selected Finish Date: {finish_date} (Method: {finish_method})", "DEBUG")

    return {
        "start": start_date,
        "finish": finish_date,
        "start_method": start_method,
        "finish_method": finish_method,
    }


def analyze_changelog(data):
    """
    Analyze the changelog to understand status transitions

    Args:
        data (dict): Jira issue data
    """
    if not data:
        print("No data to analyze")
        return

    print("\nDetailed Changelog Analysis:")
    print("-" * 40)

    # Collect all status changes
    status_changes = []
    for history in data.get("changelog", {}).get("histories", []):
        for item in history.get("items", []):
            if item.get("field") == "status":
                change = {
                    "created": history.get("created"),
                    "from": item.get("fromString"),
                    "to": item.get("toString"),
                }
                status_changes.append(change)

    # Print status changes
    for change in status_changes:
        print(f"Time: {change['created']}")
        print(f"  From: {change['from']}")
        print(f"  To: {change['to']}")
        print("-" * 20)

    # Detect actual dates
    actual_dates = detect_actual_dates(data)

    print("\nActual Dates Detection:")
    print(
        f"Start Date: {actual_dates['start']} (Method: {actual_dates['start_method']})"
    )
    print(
        f"Finish Date: {actual_dates['finish']} (Method: {actual_dates['finish_method']})"
    )


def main():
    """
    Main function to demonstrate usage
    """
    # Prompt for issue key
    issue_key = input("Enter Jira issue key (e.g., EI-1234): ").strip()

    if not issue_key:
        print("No issue key provided. Exiting.")
        return

    # Fetch and save issue data
    issue_data = fetch_jira_issue_data(issue_key)

    if issue_data:
        # Save the raw data
        save_jira_issue_data(issue_key, issue_data)

        # Analyze the changelog
        analyze_changelog(issue_data)


if __name__ == "__main__":
    main()
