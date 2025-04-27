"""
Start script for the Jira Logger API server.

This script:
1. Imports the FastAPI app from jira_logger.api
2. Explicitly imports the endpoints from jira_logger.api.endpoints
3. Starts the API server with the endpoints registered
"""

import os
import sys
from pathlib import Path

# Add the parent directory to sys.path to allow importing from jira_logger
parent_dir = str(Path(__file__).parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import the FastAPI app
from jira_logger.api import app

# Explicitly import the endpoints to register them with the app
import jira_logger.api.endpoints

# Import middleware and environment configuration
from jira_logger.api.middleware import setup_middleware
from jira_logger.config.environment import configure_environment
from jira_logger.config.settings import get_settings, get_data_dirs

# Configure environment
configure_environment()

# Set up middleware
setup_middleware(app)

# Create data directories
data_dirs = get_data_dirs()

# Get settings
settings = get_settings()


def main():
    """
    Main function to run the API server.
    """
    # Get API settings
    host = settings.api_host
    port = 8000  # Using port 8000 as specified
    log_level = settings.log_level.lower()

    # Print server information
    print(f"Starting Jira Logger API server on http://{host}:{port}")
    print(f"API documentation will be available at http://{host}:{port}/docs")

    # Run the server
    import uvicorn

    # Disable reload since we're handling imports manually
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=False,
        log_level=log_level,
    )


if __name__ == "__main__":
    main()
