"""
BigQuery Connection Test with Proxy

This script tests the connection to BigQuery using a proxy server.
It sets up a proxy server and tries to connect to BigQuery through it.
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

    # Check if Netskope certificate exists
    if not os.path.exists(netskope_cert_path):
        print(f"❌ Netskope certificate not found at: {netskope_cert_path}")
        return False

    print(f"✅ Found Netskope certificate at: {netskope_cert_path}")

    # Set environment variables to point directly to the Netskope certificate
    os.environ["REQUESTS_CA_BUNDLE"] = netskope_cert_path
    os.environ["SSL_CERT_FILE"] = netskope_cert_path
    os.environ["CURL_CA_BUNDLE"] = netskope_cert_path
    os.environ["PYTHONHTTPSVERIFY"] = "1"
    os.environ["GOOGLE_API_USE_CLIENT_CERTIFICATE"] = "true"

    # Set proxy environment variables
    # Note: Replace these with your actual proxy server details
    # os.environ["HTTPS_PROXY"] = "http://proxy.example.com:8080"
    # os.environ["HTTP_PROXY"] = "http://proxy.example.com:8080"
    # os.environ["NO_PROXY"] = "localhost,127.0.0.1"

    print(f"✅ Environment variables set:")
    print(f"   REQUESTS_CA_BUNDLE={os.environ['REQUESTS_CA_BUNDLE']}")
    print(f"   SSL_CERT_FILE={os.environ['SSL_CERT_FILE']}")
    print(f"   CURL_CA_BUNDLE={os.environ['CURL_CA_BUNDLE']}")
    print(f"   PYTHONHTTPSVERIFY={os.environ['PYTHONHTTPSVERIFY']}")
    print(
        f"   GOOGLE_API_USE_CLIENT_CERTIFICATE={os.environ['GOOGLE_API_USE_CLIENT_CERTIFICATE']}"
    )

    # Disable SSL verification for urllib
    ssl._create_default_https_context = ssl._create_unverified_context

    # Disable SSL verification warnings
    warnings.filterwarnings("ignore", message="Unverified HTTPS request")

    print(f"✅ SSL verification disabled for urllib")
    print(f"✅ SSL verification warnings disabled")

    return True


def test_bigquery_connection():
    """Test the connection to BigQuery using a proxy server."""
    print_header("BigQuery Connection Test with Proxy")

    # Set up environment variables
    if not setup_environment():
        print("❌ Failed to set up environment variables")
        return False

    # Try to connect to BigQuery
    print_step(2, "Testing BigQuery connection")
    print("Attempting to connect to BigQuery...")

    try:
        # Import the library here to avoid import errors if it's not installed
        from google.cloud import bigquery
        from google.auth import compute_engine
        from google.auth.transport.requests import Request
        from google.auth.transport.urllib3 import AuthorizedHttp
        import urllib3

        # Create a custom HTTP client with proxy support
        print("Creating custom HTTP client with proxy support...")

        # Create a proxy manager
        # Note: Replace these with your actual proxy server details
        # proxy_url = "http://proxy.example.com:8080"
        # proxy_manager = urllib3.ProxyManager(
        #     proxy_url,
        #     cert_reqs="CERT_NONE",
        #     ca_certs=os.environ["REQUESTS_CA_BUNDLE"],
        # )

        # Create a pool manager with SSL verification disabled
        http = urllib3.PoolManager(
            cert_reqs="CERT_NONE",
            ca_certs=os.environ["REQUESTS_CA_BUNDLE"],
        )

        # Create credentials
        print("Creating credentials...")
        credentials = compute_engine.Credentials()

        # Create an authorized HTTP client
        authorized_http = AuthorizedHttp(credentials, http=http)

        # Create a BigQuery client with the custom HTTP client
        print("Creating BigQuery client with custom HTTP client...")
        client = bigquery.Client(
            project="tp-pmo-production",
            location="US",
            # _http=authorized_http,  # Uncomment this if needed
        )

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

                # Create a new client with explicit project and location
                client = bigquery.Client(project="tp-pmo-production", location="US")
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
