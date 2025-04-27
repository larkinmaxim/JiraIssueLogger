"""
BigQuery Connection Test with SSL Configuration

This script tests the connection to BigQuery with explicit SSL configuration.
It sets all the necessary environment variables for SSL and certificates.
"""

import os
import sys
import time
import ssl
import warnings
import traceback
from pathlib import Path
from google.cloud import bigquery
from google.cloud.exceptions import NotFound


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
        return False

    if not os.path.exists(creds_path):
        print(f"❌ Credentials file not found at: {creds_path}")
        print("Please run setup_google_cloud.py to set up your credentials.")
        return False

    print(f"✅ Found credentials file at: {creds_path}")
    return True


def setup_ssl_certificates():
    """Set up SSL certificates and environment variables."""
    print_step(1, "Setting up SSL certificates")

    # Define paths
    netskope_cert_path = r"C:\Netskope Certs\rootcaCert.pem"
    ca_bundle_dir = Path("jira_logger/data/certs")
    ca_bundle_path = ca_bundle_dir / "ca-bundle.pem"

    # Check if Netskope certificate exists
    if not os.path.exists(netskope_cert_path):
        print(f"❌ Netskope certificate not found at: {netskope_cert_path}")
        print("Please provide the correct path to the Netskope certificate.")
        return False

    print(f"✅ Found Netskope certificate at: {netskope_cert_path}")

    # Create directory if it doesn't exist
    os.makedirs(ca_bundle_dir, exist_ok=True)
    print(f"✅ Directory exists: {ca_bundle_dir}")

    # Create CA bundle if it doesn't exist
    if not ca_bundle_path.exists():
        try:
            # Copy the Netskope certificate to the CA bundle
            import shutil

            shutil.copy2(netskope_cert_path, ca_bundle_path)
            print(f"✅ CA bundle created at: {ca_bundle_path}")
        except Exception as e:
            print(f"❌ Error creating CA bundle: {str(e)}")
            return False
    else:
        print(f"✅ CA bundle already exists at: {ca_bundle_path}")

    # Set environment variables
    os.environ["REQUESTS_CA_BUNDLE"] = str(ca_bundle_path.absolute())
    os.environ["SSL_CERT_FILE"] = str(ca_bundle_path.absolute())
    os.environ["CURL_CA_BUNDLE"] = str(ca_bundle_path.absolute())
    os.environ["PYTHONHTTPSVERIFY"] = "1"
    os.environ["GOOGLE_API_USE_CLIENT_CERTIFICATE"] = "true"

    print(f"✅ Environment variables set:")
    print(f"   REQUESTS_CA_BUNDLE={os.environ['REQUESTS_CA_BUNDLE']}")
    print(f"   SSL_CERT_FILE={os.environ['SSL_CERT_FILE']}")
    print(f"   CURL_CA_BUNDLE={os.environ['CURL_CA_BUNDLE']}")
    print(f"   PYTHONHTTPSVERIFY={os.environ['PYTHONHTTPSVERIFY']}")
    print(
        f"   GOOGLE_API_USE_CLIENT_CERTIFICATE={os.environ['GOOGLE_API_USE_CLIENT_CERTIFICATE']}"
    )

    return True


def test_bigquery_connection():
    """Test the connection to BigQuery."""
    print_header("BigQuery Connection Test with SSL Configuration")

    # Check if credentials are set up
    if not check_credentials():
        return False

    # Set up SSL certificates
    if not setup_ssl_certificates():
        return False

    try:
        # Create a BigQuery client
        print_step(2, "Creating BigQuery client")
        client = bigquery.Client()
        print(f"✅ Successfully created BigQuery client")
        print(f"   Project: {client.project}")
        print(f"   Location: {client.location}")

        # Try to list datasets with a timeout
        print_step(3, "Listing datasets")
        print("Attempting to list datasets (timeout: 30 seconds)...")

        # Set a timeout for the operation
        start_time = time.time()
        timeout = 30  # seconds

        try:
            # Use a separate thread to list datasets
            import threading
            import queue

            result_queue = queue.Queue()

            def list_datasets_thread():
                try:
                    datasets = list(client.list_datasets())
                    result_queue.put(("success", datasets))
                except Exception as e:
                    result_queue.put(("error", e))

            thread = threading.Thread(target=list_datasets_thread)
            thread.daemon = True
            thread.start()

            # Wait for the thread to complete or timeout
            while thread.is_alive() and (time.time() - start_time) < timeout:
                time.sleep(0.1)
                print(".", end="", flush=True)
                if (time.time() - start_time) % 5 < 0.1:
                    print(" Still waiting...", flush=True)

            print()  # New line after dots

            if thread.is_alive():
                print(f"❌ Operation timed out after {timeout} seconds")
                print(
                    "   This could indicate network connectivity issues or API availability problems"
                )
                return False

            # Get the result from the queue
            if not result_queue.empty():
                status, result = result_queue.get()

                if status == "success":
                    datasets = result
                    if datasets:
                        print(f"✅ Successfully listed {len(datasets)} datasets:")
                        for dataset in datasets[:5]:  # Show only first 5
                            print(f"   - {dataset.dataset_id}")
                        if len(datasets) > 5:
                            print(f"   ... and {len(datasets) - 5} more")
                    else:
                        print(f"✅ No datasets found in project {client.project}")

                    print("\n✅ BigQuery connection is working!")
                    return True
                else:
                    error = result
                    print(f"❌ Error listing datasets: {str(error)}")
                    print(f"   Error type: {type(error).__name__}")

                    # Print detailed error information
                    print("\nDetailed error information:")
                    traceback.print_exc()

                    return False
            else:
                print("❌ No result received from the operation")
                return False

        except Exception as e:
            print(f"❌ Error listing datasets: {str(e)}")
            print(f"   Error type: {type(e).__name__}")

            # Print detailed error information
            print("\nDetailed error information:")
            traceback.print_exc()

            return False

    except Exception as e:
        print(f"❌ Error creating BigQuery client: {str(e)}")
        print(f"   Error type: {type(e).__name__}")

        # Print detailed error information
        print("\nDetailed error information:")
        traceback.print_exc()

        return False


if __name__ == "__main__":
    test_bigquery_connection()
