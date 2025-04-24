import os
import sys
import requests
import json
import ssl
import warnings
from dotenv import load_dotenv

# Add the parent directory to Python path to import local modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import Netskope certificate utilities
from netskope_certificate import (
    find_netskope_certificate,
    configure_ssl_verification,
    print_ssl_debug_info,
)

# Suppress SSL warnings for testing
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

# Load environment variables from .env file
load_dotenv()

# Get Jira credentials from environment variables
jira_url = os.getenv("JIRA_BASE_URL", "https://support.transporeon.com")
api_token = os.getenv("JIRA_API_TOKEN")

# Validate required credentials
if not api_token:
    raise ValueError("JIRA_API_TOKEN must be set in the .env file")

# Find Netskope SSL certificate
netskope_cert_path = find_netskope_certificate()

# Print detailed SSL debug information
print("Detailed SSL Configuration Debug:")
print(f"Netskope Certificate Path: {netskope_cert_path}")
print(f"SSL Default Verify Paths: {ssl.get_default_verify_paths()}")
print(f"Environment SSL_CERT_FILE: {os.environ.get('SSL_CERT_FILE', 'Not set')}")
print(f"Environment SSL_CERT_DIR: {os.environ.get('SSL_CERT_DIR', 'Not set')}")
print(
    f"Environment REQUESTS_CA_BUNDLE: {os.environ.get('REQUESTS_CA_BUNDLE', 'Not set')}"
)

# Print SSL debug information
print_ssl_debug_info(netskope_cert_path)

# Configure SSL verification with bypass option for testing
verify, ca_bundle = configure_ssl_verification(netskope_cert_path, bypass_verify=True)

# JQL query matching your criteria
jql_query = 'project in (EI) AND issuetype = Project AND "Project ticket" is not EMPTY and "Start Date" is not empty and "End date" is not empty AND (status != "Open"))'

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
        "created",
        "updated",
    ],
}

# Make the API request
try:
    print("\nAttempting to connect to Jira API...")
    print(f"API Endpoint: {search_api_endpoint}")
    print(f"SSL Verification: {verify}")
    print(f"CA Bundle: {ca_bundle}")

    response = requests.post(
        search_api_endpoint,
        headers=headers,
        json=payload,
        verify=verify,  # Use Netskope SSL verification
        cert=ca_bundle,  # Use Netskope certificate if available
    )

    # Check if the request was successful
    response.raise_for_status()

    # Parse the JSON response
    data = response.json()

    # Process the results
    print(f"\nFound {len(data['issues'])} matching issues:")

    for issue in data["issues"]:
        issue_key = issue["key"]
        fields = issue["fields"]

        # Extract relevant fields
        summary = fields.get("summary", "No summary")
        status = fields.get("status", {}).get("name", "Unknown status")

        # Extract custom fields
        project_ticket = fields.get("customfield_11491", "N/A")
        start_date = fields.get("customfield_21500", "N/A")
        end_date = fields.get("customfield_27491", "N/A")

        # Print issue details
        print(f"\nIssue: {issue_key}")
        print(f"Summary: {summary}")
        print(f"Status: {status}")
        print(f"Project Ticket: {project_ticket}")
        print(f"Start Date: {start_date}")
        print(f"End Date: {end_date}")

    # Optionally save all data to a file
    with open("jira_ei_tasks.json", "w") as f:
        json.dump(data, f, indent=2)

except requests.exceptions.SSLError as ssl_err:
    print(f"\nSSL Verification Error: {ssl_err}")
    print(f"Netskope Certificate Path: {netskope_cert_path}")
    print("Troubleshooting Steps:")
    print("1. Verify the SSL certificate configuration")
    print("2. Check network proxy settings")
    print("3. Ensure the Netskope certificate is valid and accessible")
except requests.exceptions.HTTPError as err:
    print(f"\nHTTP Error: {err}")
    print(f"Response content: {err.response.text}")
except requests.exceptions.RequestException as err:
    print(f"\nError making request: {err}")
except Exception as e:
    print(f"\nUnexpected error: {e}")
    import traceback

    traceback.print_exc()
