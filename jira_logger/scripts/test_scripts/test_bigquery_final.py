"""
Final BigQuery Connection Test Script

This script tests the connection to BigQuery using multiple approaches.
It tries different authentication methods and SSL configurations.
"""

import os
import sys
import time
import ssl
import warnings
import traceback
import socket
import urllib.request
from pathlib import Path
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


def setup_environment():
    """Set up environment variables for SSL and certificates."""
    print_step(1, "Setting up environment variables")

    # Define paths
    netskope_cert_path = r"C:\Netskope Certs\rootcaCert.pem"
    ca_bundle_dir = Path("jira_logger/data/certs")
    ca_bundle_path = ca_bundle_dir / "ca-bundle.pem"

    # Check if Netskope certificate exists
    if not os.path.exists(netskope_cert_path):
        print(f"❌ Netskope certificate not found at: {netskope_cert_path}")
        return False

    print(f"✅ Found Netskope certificate at: {netskope_cert_path}")

    # Check if CA bundle exists
    if not ca_bundle_path.exists():
        print(f"❌ CA bundle not found at: {ca_bundle_path}")
        return False

    print(f"✅ Found CA bundle at: {ca_bundle_path}")

    # Set environment variables
    os.environ["REQUESTS_CA_BUNDLE"] = str(ca_bundle_path.absolute())
    os.environ["SSL_CERT_FILE"] = str(ca_bundle_path.absolute())
    os.environ["CURL_CA_BUNDLE"] = str(ca_bundle_path.absolute())
    os.environ["PYTHONHTTPSVERIFY"] = "1"
    os.environ["GOOGLE_API_USE_CLIENT_CERTIFICATE"] = "true"

    # Disable SSL verification for urllib
    ssl._create_default_https_context = ssl._create_unverified_context

    # Disable SSL verification warnings
    warnings.filterwarnings("ignore", message="Unverified HTTPS request")

    print(f"✅ Environment variables set:")
    print(f"   REQUESTS_CA_BUNDLE={os.environ['REQUESTS_CA_BUNDLE']}")
    print(f"   SSL_CERT_FILE={os.environ['SSL_CERT_FILE']}")
    print(f"   CURL_CA_BUNDLE={os.environ['CURL_CA_BUNDLE']}")
    print(f"   PYTHONHTTPSVERIFY={os.environ['PYTHONHTTPSVERIFY']}")
    print(
        f"   GOOGLE_API_USE_CLIENT_CERTIFICATE={os.environ['GOOGLE_API_USE_CLIENT_CERTIFICATE']}"
    )
    print(f"✅ SSL verification disabled for urllib")
    print(f"✅ SSL verification warnings disabled")

    return True


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


def test_bigquery_connection():
    """Test the connection to BigQuery using multiple approaches."""
    print_header("Final BigQuery Connection Test")

    # Set up environment variables
    if not setup_environment():
        print("❌ Failed to set up environment variables")
        return False

    # Check network connectivity
    network_ok = check_network_connectivity()
    if not network_ok:
        print("❌ Network connectivity issues detected")
        print(
            "   This could be due to firewall settings, proxy configuration, or network restrictions"
        )
        print("   Please check your network settings and try again")
    else:
        print("✅ Network connectivity is working")

    # Test HTTP request
    http_ok = test_http_request()
    if not http_ok:
        print("❌ HTTP request issues detected")
        print(
            "   This could be due to SSL certificate issues, proxy configuration, or network restrictions"
        )
        print("   Please check your network settings and try again")
    else:
        print("✅ HTTP requests are working")

    # Try to connect to BigQuery
    print_step(4, "Testing BigQuery connection")
    print("Attempting to connect to BigQuery...")

    try:
        # Import the library here to avoid import errors if it's not installed
        from google.cloud import bigquery

        # Create a BigQuery client
        print("Creating BigQuery client...")
        client = bigquery.Client()
        print(f"✅ Successfully created BigQuery client")
        print(f"   Project: {client.project}")
        print(f"   Location: {client.location}")

        # Try to list datasets with a timeout
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

                # Try a different approach
                print("\nTrying a different approach...")
                print(
                    "Creating a new BigQuery client with explicit project and location..."
                )

                # Get project ID from environment variable
                project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
                if not project_id:
                    project_id = "tp-pmo-production"  # Default project ID

                # Create a new client with explicit project and location
                client = bigquery.Client(project=project_id, location="US")
                print(
                    f"✅ Successfully created BigQuery client with explicit project and location"
                )
                print(f"   Project: {client.project}")
                print(f"   Location: {client.location}")

                # Try to get a dataset directly
                print("Attempting to get a dataset directly...")
                try:
                    dataset_id = "jira_data"  # Default dataset ID
                    dataset_ref = f"{client.project}.{dataset_id}"
                    dataset = client.get_dataset(dataset_ref)
                    print(f"✅ Successfully got dataset: {dataset.dataset_id}")
                    return True
                except Exception as e:
                    print(f"❌ Error getting dataset: {str(e)}")
                    print(f"   Error type: {type(e).__name__}")

                    # Print detailed error information
                    print("\nDetailed error information:")
                    traceback.print_exc()

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
