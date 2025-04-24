"""
Jira Issue Parser with Netskope SSL Certificate Support

This script uses the netskope_certificate library for SSL certificate handling
in Netskope environments, providing robust SSL verification and configuration.

Key Features:
- Flexible SSL certificate configuration
- Advanced certificate validation
- Supports Netskope SSL interception scenarios
"""

import json
import datetime
import requests
import os
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
LOG_LEVEL = "INFO"  # Can be "INFO", "DEBUG", "WARN"


def log(message, level="INFO"):
    """
    Logging function with configurable log levels
    """
    log_levels = {"WARN": 3, "INFO": 2, "DEBUG": 1}
    current_level = log_levels.get(LOG_LEVEL, 2)
    message_level = log_levels.get(level, 2)

    if message_level >= current_level:
        print(f"[{level}] {message}")


def calculate_duration(start_date, end_date):
    """
    Calculate duration in days between two dates, excluding weekends

    Args:
        start_date (str): Start date in ISO format
        end_date (str): End date in ISO format

    Returns:
        float: Number of weekdays between start and end dates, or None if dates are invalid
    """
    if not start_date or not end_date:
        return None

    try:
        start = datetime.datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        end = datetime.datetime.fromisoformat(end_date.replace("Z", "+00:00"))

        # Initialize duration tracking
        total_days = 0
        current = start

        # Iterate through each day
        while current <= end:
            # Check if current day is a weekday (Monday = 0, Sunday = 6)
            if current.weekday() < 5:  # Monday to Friday
                # Add 1 day per weekday
                total_days += 1

            # Move to next day
            current += datetime.timedelta(days=1)

        return round(total_days, 2)
    except (ValueError, TypeError):
        return None


# Import SSL settings from main.py if available
try:
    from jira_logger.main import SSL_SETTINGS
except ImportError:
    # Default SSL settings if main.py is not available
    SSL_SETTINGS = {
        "use_ssl_verification": True,
        "certificate_path": os.environ.get(
            "SSL_CERT_PATH", find_netskope_certificate()
        ),
        "last_updated": datetime.datetime.utcnow().isoformat(),
    }


def connect_to_jira_api(
    issue_key,
    bypass_ssl_verify=None,
    save_raw_response=False,
    raw_response_dir="jira_logger/data/jira_raw_responses",
):
    """
    Connect to Jira REST API and fetch issue data

    Args:
        issue_key (str): The Jira issue key to retrieve
        bypass_ssl_verify (bool, optional): Bypass SSL certificate verification.
            If None, uses the global SSL_SETTINGS. Defaults to None.
        save_raw_response (bool, optional): Whether to save the raw JSON response to a file.
            Defaults to False.
        raw_response_dir (str, optional): Directory to save raw responses.
            Defaults to "jira_logger/data/jira_raw_responses".

    Returns:
        dict: JSON data of the Jira issue
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

    # Determine SSL verification settings
    if bypass_ssl_verify is None:
        # Use global SSL settings
        bypass_verify = not SSL_SETTINGS["use_ssl_verification"]
        cert_path = SSL_SETTINGS["certificate_path"]
    else:
        # Use provided bypass_ssl_verify parameter
        bypass_verify = bypass_ssl_verify
        cert_path = find_netskope_certificate()

    # Print SSL debug information
    print_ssl_debug_info(cert_path)

    # Configure SSL verification
    verify, _ = configure_ssl_verification(
        cert_path=cert_path, bypass_verify=bypass_verify
    )

    try:
        # Use the custom CA bundle or bypass verification based on settings
        response = requests.get(url, headers=headers, verify=verify)
        response.raise_for_status()

        # Get the JSON response
        json_data = response.json()

        # Save raw response if requested
        if save_raw_response:
            # Create directory if it doesn't exist
            os.makedirs(raw_response_dir, exist_ok=True)

            # Create a filename with timestamp to avoid overwriting
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{raw_response_dir}/{issue_key}_{timestamp}.json"

            # Save the raw response to a file
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)

            log(f"Saved raw response to {filename}", "INFO")

        return json_data
    except requests.exceptions.SSLError as ssl_err:
        print("SSL Certificate Verification Failed:")
        print(f"Error Details: {ssl_err}")
        print("\nTroubleshooting Steps:")
        print("1. Verify the REQUESTS_CA_BUNDLE path is correct")
        print("2. Ensure the certificate is in valid PEM format")
        print("3. Check file permissions and accessibility")
        print("\nTemporary Solutions:")
        print("- Set REQUESTS_CA_BUNDLE to a valid certificate path")
        print(
            "- Use bypass_ssl_verify=True for testing (NOT recommended for production)"
        )
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to Jira API: {e}")
        return None


def detect_actual_dates(jira_data):
    """
    Advanced detection of actual start and finish dates from changelog

    Args:
        jira_data (dict): Jira issue data

    Returns:
        dict: Detected actual start and finish dates with detection method
    """
    if not jira_data:
        return {
            "start": None,
            "finish": None,
            "start_method": None,
            "finish_method": None,
        }

    # Collect all status changes
    status_changes = []
    for history in jira_data.get("changelog", {}).get("histories", []):
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


def extract_jira_data(jira_data):
    """
    Extract planned and actual dates from Jira issue data

    Args:
        jira_data (dict): JSON data of the Jira issue

    Returns:
        dict: Extracted dates and milestones
    """
    if not jira_data:
        return None

    # Extract planned dates
    planned_dev_start = jira_data.get("fields", {}).get("customfield_15990")
    planned_dev_finish = jira_data.get("fields", {}).get("customfield_15994")

    # Detect actual dates using advanced method
    actual_dates = detect_actual_dates(jira_data)

    # Format results
    result = {
        "Planned": {
            "Planned start": planned_dev_start,
            "Planned finish": planned_dev_finish,
            "Planned duration": calculate_duration(
                planned_dev_start, planned_dev_finish
            ),
        },
        "Actual": {
            "Actual start": actual_dates["start"],
            "Actual finish": actual_dates["finish"],
            "Actual duration": calculate_duration(
                actual_dates["start"], actual_dates["finish"]
            ),
            "Start method": actual_dates["start_method"],
            "Finish method": actual_dates["finish_method"],
        },
    }

    return result


# Usage example
if __name__ == "__main__":
    # Prompt user to input the issue key
    issue_key = input("Enter the Jira issue key (e.g., EI-1234): ").strip()

    if not issue_key:
        print("No issue key provided. Exiting.")
        exit(1)

    # Ask if user wants to save the raw response
    save_raw = (
        input("Do you want to save the raw response? (y/n): ").strip().lower() == "y"
    )

    # Fetch Jira issue data
    # Set bypass_ssl_verify=False to use SSL certificate verification
    jira_data = connect_to_jira_api(
        issue_key, bypass_ssl_verify=True, save_raw_response=save_raw
    )

    if jira_data:
        result = extract_jira_data(jira_data)

        if result:
            print("\nPlanned:")
            print(f"  Planned start: {result['Planned']['Planned start']}")
            print(f"  Planned finish: {result['Planned']['Planned finish']}")
            print(f"  Planned duration: {result['Planned']['Planned duration']} days")
            print("\nActual:")
            print(f"  Actual start: {result['Actual']['Actual start']}")
            print(f"  Actual finish: {result['Actual']['Actual finish']}")
            print(f"  Actual duration: {result['Actual']['Actual duration']} days")
            print(f"  Start method: {result['Actual']['Start method']}")
            print(f"  Finish method: {result['Actual']['Finish method']}")
        else:
            print("Could not extract data from the Jira issue.")
    else:
        print("Failed to retrieve Jira issue data.")
