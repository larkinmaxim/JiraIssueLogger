"""
Jira Logger with BigQuery Integration

This FastAPI application provides endpoints to:
1. Update status of Jira issues in BigQuery
2. Collect details for issues in "closed" or "deployed pd" status with empty details
3. Collect/update details for issues in "deployed ac" status
4. Configure SSL certificate settings

The application prevents duplicates in the BigQuery table by using MERGE operations.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to sys.path to allow importing from jira_logger
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import FastAPI app
from jira_logger.api import app
from jira_logger.api.middleware import setup_middleware
from jira_logger.config.environment import configure_environment
from jira_logger.config.settings import get_settings, get_data_dirs

# Import API endpoints to register them with the app
import jira_logger.api.endpoints

# Configure environment
configure_environment()

# Set up middleware
setup_middleware(app)

# Create data directories
data_dirs = get_data_dirs()

# Get settings
settings = get_settings()

# Export SSL settings for use in other modules
from jira_logger.config.settings import get_ssl_settings

SSL_SETTINGS = get_ssl_settings()
SSL_SETTINGS["last_updated"] = os.environ.get("SSL_SETTINGS_LAST_UPDATED", "")

# Main entry point
if __name__ == "__main__":
    import uvicorn

    # Get API settings
    host = settings.api_host
    port = settings.api_port

    # Run the API server
    uvicorn.run(
        "jira_logger.main:app",
        host=host,
        port=port,
        reload=True,
        log_level=settings.log_level.lower(),
    )
