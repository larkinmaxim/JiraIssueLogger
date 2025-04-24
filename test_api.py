"""
Test script for the Jira Logger API endpoints.

This script provides a simple way to test the API endpoints without using a browser.
"""

import requests
import json
import time
from datetime import datetime

# API base URL
BASE_URL = "http://localhost:8000"


def print_response(response):
    """Print the response in a formatted way."""
    print(f"Status Code: {response.status_code}")
    try:
        print("Response:")
        print(json.dumps(response.json(), indent=2))
    except:
        print(f"Raw Response: {response.text}")
    print("-" * 50)


def test_root_endpoint():
    """Test the root endpoint."""
    print("\nTesting Root Endpoint...")
    response = requests.get(f"{BASE_URL}/")
    print_response(response)


def test_update_status():
    """Test the update status endpoint."""
    print("\nTesting Update Status Endpoint...")
    response = requests.post(f"{BASE_URL}/api/update-status")
    print_response(response)


def test_collect_closed_details():
    """Test the collect closed details endpoint."""
    print("\nTesting Collect Closed Details Endpoint...")
    response = requests.post(f"{BASE_URL}/api/collect-closed-details")
    print_response(response)


def test_collect_ac_details():
    """Test the collect AC details endpoint."""
    print("\nTesting Collect AC Details Endpoint...")
    response = requests.post(f"{BASE_URL}/api/collect-ac-details")
    print_response(response)


def run_all_tests():
    """Run all tests in sequence."""
    print(f"Starting API tests at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    try:
        # Test root endpoint
        test_root_endpoint()

        # Test update status endpoint
        test_update_status()

        # Test collect closed details endpoint
        test_collect_closed_details()

        # Test collect AC details endpoint
        test_collect_ac_details()

        print("\nAll tests completed successfully!")

    except requests.exceptions.ConnectionError:
        print("\nERROR: Could not connect to the API server.")
        print("Make sure the API server is running with 'python run_api.py'")

    except Exception as e:
        print(f"\nERROR: An unexpected error occurred: {str(e)}")


if __name__ == "__main__":
    run_all_tests()
