"""
Google Cloud Connection Test Script

This script tests the basic connection to Google Cloud APIs without using BigQuery.
It checks if the credentials are set up correctly and if the network connection to
Google Cloud APIs is working.
"""

import os
import sys
import ssl
import json
import warnings
import traceback
import socket
import urllib.request
from urllib.error import URLError, HTTPError


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f" {text} ".center(80, "="))
    print("=" * 80 + "\n")


def print_step(step_num, text):
    """Print a formatted step."""
    print(f"\n[Step {step_num}] {text}")
    print("-" * 80)


def check_credentials():
    """Check if Google Cloud credentials are set up."""
    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

    if not creds_path:
        print("❌ GOOGLE_APPLICATION_CREDENTIALS environment variable is not set.")
        print("Please run setup_google_cloud.py to set up your credentials.")
        return False, None

    if not os.path.exists(creds_path):
        print(f"❌ Credentials file not found at: {creds_path}")
        print("Please run setup_google_cloud.py to set up your credentials.")
        return False, None

    print(f"✅ Found credentials file at: {creds_path}")

    # Try to load and validate the credentials file
    try:
        with open(creds_path, "r") as f:
            creds_data = json.load(f)

        # Check if the required fields are present
        required_fields = [
            "type",
            "project_id",
            "private_key_id",
            "private_key",
            "client_email",
        ]
        missing_fields = [field for field in required_fields if field not in creds_data]

        if missing_fields:
            print(
                f"❌ Credentials file is missing required fields: {', '.join(missing_fields)}"
            )
            return False, None

        print(f"✅ Credentials file is valid")
        print(f"   Project ID: {creds_data.get('project_id')}")
        print(f"   Client Email: {creds_data.get('client_email')}")

        return True, creds_data
    except json.JSONDecodeError:
        print(f"❌ Credentials file is not valid JSON")
        return False, None
    except Exception as e:
        print(f"❌ Error reading credentials file: {str(e)}")
        return False, None


def check_network_connectivity():
    """Check if the network connection to Google Cloud APIs is working."""
    print_step(2, "Checking network connectivity")

    # List of Google Cloud API endpoints to check
    endpoints = [
        "www.googleapis.com",
        "bigquery.googleapis.com",
        "storage.googleapis.com",
    ]

    all_successful = True

    for endpoint in endpoints:
        try:
            print(f"   Testing connection to {endpoint}...")
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((endpoint, 443))
            s.close()
            print(f"   ✅ Successfully connected to {endpoint}")
        except Exception as e:
            print(f"   ❌ Failed to connect to {endpoint}: {str(e)}")
            all_successful = False

    return all_successful


def test_http_request():
    """Test HTTP request to Google Cloud APIs."""
    print_step(3, "Testing HTTP request to Google Cloud APIs")

    # Disable SSL verification warnings
    warnings.filterwarnings("ignore", message="Unverified HTTPS request")

    # Disable SSL certificate verification
    ssl._create_default_https_context = ssl._create_unverified_context

    # Set environment variables for requests
    os.environ["REQUESTS_CA_BUNDLE"] = ""
    os.environ["HTTPS_PROXY"] = ""

    # URLs to test
    urls = [
        "https://www.googleapis.com/discovery/v1/apis",
    ]

    all_successful = True

    for url in urls:
        try:
            print(f"   Testing HTTP request to {url}...")
            req = urllib.request.Request(url)
            response = urllib.request.urlopen(req, timeout=10)

            if response.getcode() == 200:
                print(f"   ✅ Successfully made HTTP request to {url}")
                print(f"      Response code: {response.getcode()}")
            else:
                print(
                    f"   ⚠️ HTTP request to {url} returned non-200 status code: {response.getcode()}"
                )
                all_successful = False

        except HTTPError as e:
            print(f"   ❌ HTTP Error: {e.code} - {e.reason}")
            all_successful = False
        except URLError as e:
            print(f"   ❌ URL Error: {str(e)}")
            all_successful = False
        except Exception as e:
            print(f"   ❌ Error making HTTP request: {str(e)}")
            traceback.print_exc()
            all_successful = False

    return all_successful


def check_bigquery_api_enabled(project_id):
    """Check if the BigQuery API is enabled for the project."""
    print_step(4, "Checking if BigQuery API is enabled")

    print(f"   Project ID: {project_id}")
    print("   To check if the BigQuery API is enabled, you need to:")
    print("   1. Go to the Google Cloud Console: https://console.cloud.google.com/")
    print("   2. Select your project")
    print("   3. Go to APIs & Services > Dashboard")
    print("   4. Check if 'BigQuery API' is listed in the enabled APIs")
    print("   5. If not, go to APIs & Services > Library")
    print("   6. Search for 'BigQuery API' and enable it")

    print("\n   Since we can't programmatically check this without authentication,")
    print(
        "   please verify manually that the BigQuery API is enabled for your project."
    )

    return None  # Return None since we can't determine this programmatically


def check_service_account_permissions(client_email):
    """Check if the service account has the necessary permissions."""
    print_step(5, "Checking service account permissions")

    print(f"   Service Account: {client_email}")
    print(
        "   To check if the service account has the necessary permissions, you need to:"
    )
    print("   1. Go to the Google Cloud Console: https://console.cloud.google.com/")
    print("   2. Go to IAM & Admin > IAM")
    print("   3. Find your service account in the list")
    print("   4. Check if it has at least the 'BigQuery User' role")
    print("   5. If not, click the edit button and add the necessary roles")

    print("\n   Recommended roles for BigQuery access:")
    print("   - BigQuery User: To run queries and jobs")
    print("   - BigQuery Data Viewer: To view dataset contents")
    print("   - BigQuery Data Editor: To modify dataset contents")
    print("   - BigQuery Job User: To run jobs")

    print("\n   Since we can't programmatically check this without authentication,")
    print(
        "   please verify manually that the service account has the necessary permissions."
    )

    return None  # Return None since we can't determine this programmatically


def test_google_cloud_connection():
    """Test the connection to Google Cloud APIs."""
    print_header("Google Cloud Connection Test")

    # Check if credentials are set up
    creds_valid, creds_data = check_credentials()
    if not creds_valid:
        return False

    # Check network connectivity
    network_ok = check_network_connectivity()
    if not network_ok:
        print("\n⚠️ Network connectivity issues detected")
        print(
            "   This could be due to firewall settings, proxy configuration, or network restrictions"
        )
        print("   Please check your network settings and try again")

    # Test HTTP request
    http_ok = test_http_request()
    if not http_ok:
        print("\n⚠️ HTTP request issues detected")
        print(
            "   This could be due to SSL certificate issues, proxy configuration, or network restrictions"
        )
        print("   Please check your network settings and try again")

    # Check if BigQuery API is enabled
    if creds_data:
        project_id = creds_data.get("project_id")
        client_email = creds_data.get("client_email")

        # Check if BigQuery API is enabled
        check_bigquery_api_enabled(project_id)

        # Check service account permissions
        check_service_account_permissions(client_email)

    # Print summary
    print_header("Test Summary")
    print(f"Credentials: {'✅ Valid' if creds_valid else '❌ Invalid'}")
    print(f"Network Connectivity: {'✅ OK' if network_ok else '❌ Issues detected'}")
    print(f"HTTP Requests: {'✅ OK' if http_ok else '❌ Issues detected'}")

    print("\nBased on the test results, here are the potential issues:")

    if not creds_valid:
        print("1. Your Google Cloud credentials are not valid or not set up correctly.")
        print(
            "   Run jira_logger.scripts.setup_google_cloud to set up your credentials."
        )

    if not network_ok:
        print("2. There are network connectivity issues to Google Cloud APIs.")
        print(
            "   This could be due to firewall settings, proxy configuration, or network restrictions."
        )

    if not http_ok:
        print("3. There are HTTP request issues to Google Cloud APIs.")
        print(
            "   This could be due to SSL certificate issues, proxy configuration, or network restrictions."
        )

    if creds_valid and network_ok and http_ok:
        print("4. Your basic connection to Google Cloud APIs is working correctly.")
        print(
            "   However, you might still have issues with BigQuery specifically due to:"
        )
        print("   - BigQuery API not being enabled for your project")
        print("   - Service account not having the necessary permissions")
        print("   - Service account key being expired or revoked")
        print(
            "\n   Please check the instructions above to verify these settings manually."
        )

    return creds_valid and network_ok and http_ok


if __name__ == "__main__":
    test_google_cloud_connection()
