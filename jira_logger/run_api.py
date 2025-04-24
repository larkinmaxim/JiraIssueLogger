"""
Run script for the Jira Logger FastAPI application.

This script provides a convenient way to start the FastAPI server.
"""

import os
import sys
import argparse
from pathlib import Path

# Add the parent directory to sys.path to allow importing from jira_logger
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import settings
from jira_logger.config.settings import get_settings


def parse_args():
    """
    Parse command line arguments.

    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Run the Jira Logger API server")

    parser.add_argument(
        "--host",
        type=str,
        help="Host to bind the server to",
    )

    parser.add_argument(
        "--port",
        type=int,
        help="Port to bind the server to",
    )

    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload on code changes",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        choices=["debug", "info", "warning", "error", "critical"],
        help="Logging level",
    )

    return parser.parse_args()


def main():
    """
    Main function to run the API server.
    """
    # Parse command line arguments
    args = parse_args()

    # Get settings
    settings = get_settings()

    # Override settings with command line arguments
    host = args.host or settings.api_host
    port = args.port or settings.api_port
    reload = args.reload
    log_level = args.log_level or settings.log_level.lower()

    # Print server information
    print(f"Starting Jira Logger API server on http://{host}:{port}")
    print(f"API documentation will be available at http://{host}:{port}/docs")

    # Run the server
    import uvicorn

    uvicorn.run(
        "jira_logger.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
    )


if __name__ == "__main__":
    main()
