"""
Check BigQuery API Script

This script checks if the BigQuery API is enabled for the project.
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


def check_bigquery_api_status():
    """
    Check if the BigQuery API is enabled for the project.

    This function attempts to make a simple request to the BigQuery API
    to determine if it's enabled and accessible.
    """
    print_header("BigQuery API Status Check")

    # Check if credentials are set up
    creds_valid, creds_data = check_credentials()
    if not creds_valid:
        return False

    project_id = creds_data.get("project_id")
    print(f"Checking BigQuery API status for project: {project_id}")

    # Try to use the google-cloud-bigquery library directly
    try:
        print("Attempting to use google-cloud-bigquery library...")

        # Import the library here to avoid import errors if it's not installed
        try:
            from google.cloud import bigquery

            print("✅ google-cloud-bigquery library is installed")
        except ImportError:
            print("❌ google-cloud-bigquery library is not installed")
            print("   Please install it with: pip install google-cloud-bigquery")
            return False

        # Create a BigQuery client
        print("Creating BigQuery client...")
        client = bigquery.Client()
        print(f"✅ Successfully created BigQuery client")
        print(f"   Project: {client.project}")
        print(f"   Location: {client.location}")

        # Try to list datasets
        print("Attempting to list datasets...")
        try:
            # Use a shorter timeout to avoid long waits
            datasets = list(client.list_datasets(timeout=5))

            if datasets:
                print(f"✅ Successfully listed {len(datasets)} datasets:")
                for dataset in datasets[
                    :5
                ]:  # Show only first 5 to avoid too much output
                    print(f"   - {dataset.dataset_id}")
                if len(datasets) > 5:
                    print(f"   ... and {len(datasets) - 5} more")
            else:
                print(f"✅ No datasets found in project {client.project}")

            print(f"\n✅ BigQuery API is enabled and accessible")
            return True
        except Exception as e:
            print(f"❌ Error listing datasets: {str(e)}")
            print(f"   Exception type: {type(e).__name__}")

            # Try to get more information about the error
            if "Access Denied" in str(e):
                print(
                    f"❌ Access denied: The service account does not have permission to access BigQuery"
                )
            elif "API has not been used" in str(e) or "API not enabled" in str(e):
                print(f"❌ BigQuery API is not enabled for this project")
                print(f"   Please enable it in the Google Cloud Console")
            else:
                print(f"❌ Unknown error accessing BigQuery API")
                traceback.print_exc()

            return False
    except Exception as e:
        print(f"❌ Error checking BigQuery API status: {str(e)}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    check_bigquery_api_status()
