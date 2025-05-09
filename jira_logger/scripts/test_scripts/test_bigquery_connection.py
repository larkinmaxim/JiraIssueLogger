"""
BigQuery Connection Test Script

This script tests the connection to BigQuery and verifies that the credentials
are set up correctly. It creates a temporary test table, inserts some data,
queries the data, and then deletes the table.
"""

import os
import sys
import uuid
import datetime
import warnings
import ssl
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


def test_bigquery_connection():
    """Test the connection to BigQuery."""
    print_header("BigQuery Connection Test")

    # Check if credentials are set up
    if not check_credentials():
        return False

    # Configure SSL verification with Netskope certificate
    print("Configuring SSL verification with Netskope certificate...")

    # Define paths for Netskope certificates
    netskope_cert_paths = [
        r"C:\ProgramData\Netskope\STAgent\data\nscacert.pem",  # Standard Netskope cert path
        r"C:\ProgramData\Netskope\STAgent\data\nscacert_combined.pem",  # Combined cert path
        r"C:\Netskope Certs\rootcaCert.pem",  # Custom cert path
    ]

    # Find the first certificate that exists
    netskope_cert_path = None
    for cert_path in netskope_cert_paths:
        if os.path.exists(cert_path):
            netskope_cert_path = cert_path
            break

    if not netskope_cert_path:
        print(f"❌ Netskope certificate not found at any of the expected locations:")
        for cert_path in netskope_cert_paths:
            print(f"   - {cert_path}")
        return False

    print(f"✅ Found Netskope certificate at: {netskope_cert_path}")

    # Set environment variables for requests library
    os.environ["REQUESTS_CA_BUNDLE"] = netskope_cert_path
    os.environ["SSL_CERT_FILE"] = netskope_cert_path
    os.environ["CURL_CA_BUNDLE"] = netskope_cert_path
    os.environ["NODE_EXTRA_CA_CERTS"] = netskope_cert_path
    os.environ["PYTHONHTTPSVERIFY"] = "1"
    os.environ["GOOGLE_API_USE_CLIENT_CERTIFICATE"] = "true"

    try:
        # Create a BigQuery client
        print_step(1, "Creating BigQuery client")
        client = bigquery.Client()
        print(f"✅ Successfully created BigQuery client")
        print(f"   Project: {client.project}")
        print(f"   Location: {client.location}")

        # List existing datasets
        print_step(2, "Listing existing datasets")
        print(
            f"   This will verify if we can connect to BigQuery and have proper permissions"
        )

        try:
            print(f"   Attempting to list datasets with timeout=10 seconds...")
            try:
                # Use a shorter timeout to avoid long waits
                datasets = list(client.list_datasets(timeout=10))

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

                print(f"\n✅ Basic connection to BigQuery is working!")
            except Exception as e:
                print(f"❌ Error listing datasets: {str(e)}")
                print(f"   Exception type: {type(e).__name__}")
                print(
                    f"   This could be due to network issues, permissions, or service availability."
                )

                # Try to get more information about the error
                import traceback

                print("\nDetailed error information:")
                traceback.print_exc()

                # Check network connectivity
                print("\nChecking network connectivity...")
                try:
                    import socket

                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(2)
                    s.connect(("www.googleapis.com", 443))
                    s.close()
                    print("✅ Network connection to googleapis.com is working")
                except Exception as net_err:
                    print(f"❌ Network connection error: {str(net_err)}")

                return False

            # Ask if user wants to continue with full test
            response = input(
                "\nDo you want to continue with the full test (creating test dataset and tables)? (y/n): "
            )
            if response.lower() != "y":
                print("\nSkipping full test. Basic connection test was successful.")
                return True

            # Continue with full test if user wants to
            print("\nContinuing with full test...")

            # Create a unique dataset ID for testing
            test_id = uuid.uuid4().hex[:8]
            dataset_id = f"jira_logger_test_{test_id}"
            dataset_ref = f"{client.project}.{dataset_id}"

            # Create a test dataset
            print_step(3, f"Creating test dataset: {dataset_id}")
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = "US"
            print(f"   Attempting to create dataset with timeout=30 seconds...")
            try:
                dataset = client.create_dataset(dataset, timeout=30)
                print(f"✅ Successfully created dataset: {dataset_id}")
            except Exception as e:
                print(f"❌ Error creating dataset: {str(e)}")
                print(
                    "   This could be due to network issues, permissions, or service availability."
                )
                return False
        except Exception as e:
            print(f"❌ Error listing datasets: {str(e)}")
            print(
                "   This could be due to network issues, permissions, or service availability."
            )
            return False

        try:
            # Create a test table
            print_step(3, "Creating test table")
            table_id = f"{dataset_id}.test_table"
            schema = [
                bigquery.SchemaField("issue_key", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("summary", "STRING"),
                bigquery.SchemaField("status", "STRING"),
                bigquery.SchemaField("created_at", "TIMESTAMP"),
            ]

            table = bigquery.Table(f"{client.project}.{table_id}", schema=schema)
            table = client.create_table(table, timeout=30)
            print(f"✅ Successfully created table: {table_id}")

            # Insert test data
            print_step(4, "Inserting test data")
            rows_to_insert = [
                {
                    "issue_key": "TEST-001",
                    "summary": "Test issue 1",
                    "status": "in progress",
                    "created_at": datetime.datetime.utcnow().isoformat(),
                },
                {
                    "issue_key": "TEST-002",
                    "summary": "Test issue 2",
                    "status": "deployed ac",
                    "created_at": datetime.datetime.utcnow().isoformat(),
                },
            ]

            errors = client.insert_rows_json(table, rows_to_insert)
            if errors == []:
                print(f"✅ Successfully inserted {len(rows_to_insert)} rows")
            else:
                print(f"❌ Encountered errors while inserting rows: {errors}")
                return False

            # Query the test data
            print_step(5, "Querying test data")
            query = f"SELECT * FROM `{client.project}.{table_id}`"
            query_job = client.query(query)
            results = list(query_job.result())

            if len(results) == len(rows_to_insert):
                print(f"✅ Successfully queried {len(results)} rows")
                for row in results:
                    print(f"   {row.issue_key}: {row.summary} ({row.status})")
            else:
                print(f"❌ Expected {len(rows_to_insert)} rows, but got {len(results)}")
                return False

            # Test MERGE operation
            print_step(6, "Testing MERGE operation")

            # Create a temporary table for the MERGE
            temp_table_id = f"{dataset_id}.temp_table"
            temp_table = bigquery.Table(
                f"{client.project}.{temp_table_id}", schema=schema
            )
            temp_table = client.create_table(temp_table, timeout=30)

            # Insert data into the temporary table
            temp_rows = [
                {
                    "issue_key": "TEST-001",  # Existing issue (will be updated)
                    "summary": "Updated test issue 1",
                    "status": "deployed pd",
                    "created_at": datetime.datetime.utcnow().isoformat(),
                },
                {
                    "issue_key": "TEST-003",  # New issue (will be inserted)
                    "summary": "Test issue 3",
                    "status": "closed",
                    "created_at": datetime.datetime.utcnow().isoformat(),
                },
            ]

            errors = client.insert_rows_json(temp_table, temp_rows)
            if errors != []:
                print(
                    f"❌ Encountered errors while inserting rows to temp table: {errors}"
                )
                return False

            # Perform MERGE operation
            merge_query = f"""
            MERGE `{client.project}.{table_id}` T
            USING `{client.project}.{temp_table_id}` S
            ON T.issue_key = S.issue_key
            WHEN MATCHED THEN
              UPDATE SET 
                T.summary = S.summary,
                T.status = S.status
            WHEN NOT MATCHED THEN
              INSERT (issue_key, summary, status, created_at)
              VALUES (issue_key, summary, status, created_at)
            """

            merge_job = client.query(merge_query)
            merge_job.result()

            # Query the updated data
            query = f"SELECT * FROM `{client.project}.{table_id}` ORDER BY issue_key"
            query_job = client.query(query)
            results = list(query_job.result())

            if len(results) == 3:  # 2 original + 1 new - 0 deleted
                print(f"✅ Successfully performed MERGE operation")
                for row in results:
                    print(f"   {row.issue_key}: {row.summary} ({row.status})")

                # Check if the update worked
                updated_row = next(
                    (r for r in results if r.issue_key == "TEST-001"), None
                )
                if updated_row and updated_row.status == "deployed pd":
                    print(f"✅ Successfully updated existing row")
                else:
                    print(f"❌ Failed to update existing row")
                    return False

                # Check if the insert worked
                new_row = next((r for r in results if r.issue_key == "TEST-003"), None)
                if new_row:
                    print(f"✅ Successfully inserted new row")
                else:
                    print(f"❌ Failed to insert new row")
                    return False
            else:
                print(f"❌ Expected 3 rows after MERGE, but got {len(results)}")
                return False

        finally:
            # Clean up the test dataset
            print_step(7, "Cleaning up test resources")
            client.delete_dataset(dataset_ref, delete_contents=True, not_found_ok=True)
            print(f"✅ Successfully deleted dataset: {dataset_id}")

        print_header("BigQuery Connection Test: SUCCESS")
        print("Your BigQuery connection is working correctly!")
        print("You're ready to use the Jira Logger API with BigQuery.")
        return True

    except Exception as e:
        print(f"\n❌ Error testing BigQuery connection: {str(e)}")
        print("\nTroubleshooting steps:")
        print("1. Make sure your Google Cloud credentials are set up correctly")
        print("2. Make sure the BigQuery API is enabled in your Google Cloud project")
        print("3. Make sure your service account has the necessary permissions")
        print(
            "4. Run jira_logger.scripts.setup_google_cloud to set up your credentials"
        )
        return False


if __name__ == "__main__":
    test_bigquery_connection()
