"""
Test script for the Jira Logger API endpoints.

This script:
1. Imports the FastAPI app from jira_logger.api
2. Explicitly imports the endpoints from jira_logger.api.endpoints
3. Makes a simple GET request to the root endpoint to test if it's working
"""

import sys
import requests
from pathlib import Path

# Add the parent directory to sys.path to allow importing from jira_logger
parent_dir = str(Path(__file__).parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import the FastAPI app
from jira_logger.api import app

# Explicitly import the endpoints to register them with the app
import jira_logger.api.endpoints


# Test the API by making a request to the root endpoint
def test_root_endpoint():
    print("Testing the root endpoint...")
    try:
        response = requests.get("http://localhost:8000/")
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_root_endpoint()
