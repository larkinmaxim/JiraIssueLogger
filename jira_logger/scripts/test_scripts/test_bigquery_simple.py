"""
Simple BigQuery Connection Test Script

This script tests the connection to BigQuery using a minimal approach.
It tries to list datasets in the project without any additional configuration.
"""

import os
import sys
import time
from google.cloud import bigquery


def test_bigquery_connection():
    """Test the connection to BigQuery."""
    print("\n=== Simple BigQuery Connection Test ===\n")

    # Check if credentials are set up
    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_path:
        print("❌ GOOGLE_APPLICATION_CREDENTIALS environment variable is not set.")
        return False

    if not os.path.exists(creds_path):
        print(f"❌ Credentials file not found at: {creds_path}")
        return False

    print(f"✅ Found credentials file at: {creds_path}")

    try:
        # Create a BigQuery client with minimal configuration
        print("\nCreating BigQuery client...")
        client = bigquery.Client()
        print(f"✅ Successfully created BigQuery client")
        print(f"   Project: {client.project}")

        # Try to list datasets with a timeout
        print("\nAttempting to list datasets (timeout: 10 seconds)...")

        # Set a timeout for the operation
        start_time = time.time()
        timeout = 10  # seconds

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
                    return False
            else:
                print("❌ No result received from the operation")
                return False

        except Exception as e:
            print(f"❌ Error listing datasets: {str(e)}")
            print(f"   Error type: {type(e).__name__}")
            return False

    except Exception as e:
        print(f"❌ Error creating BigQuery client: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
        return False


if __name__ == "__main__":
    test_bigquery_connection()
