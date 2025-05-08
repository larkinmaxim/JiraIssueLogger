"""
Example script for scheduling API calls to the Jira Logger API.

This script demonstrates how to schedule API calls to the Jira Logger API
using Python's schedule library. This is an alternative to using cron jobs
or cloud-based schedulers.

To use this script:
1. Install the schedule library: pip install schedule
2. Run this script in the background: python -m jira_logger.core.scheduler &
"""

import schedule
import time
import requests
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("api_scheduler.log"), logging.StreamHandler()],
)

logger = logging.getLogger("jira_logger_scheduler")

# API base URL
BASE_URL = "http://localhost:8000"


def call_api_endpoint(endpoint, name):
    """Call an API endpoint and log the result."""
    try:
        logger.info(f"Calling {name} endpoint...")

        # Import SSL settings
        from jira_logger.config.settings import get_ssl_settings

        ssl_settings = get_ssl_settings()
        verify = ssl_settings.get("use_ssl_verification", False)

        # Use SSL settings for the request
        response = requests.post(f"{BASE_URL}/{endpoint}", verify=verify)

        if response.status_code == 200:
            result = response.json()
            logger.info(
                f"{name} completed successfully. Updated: {result.get('updated_count', 0)}, "
                f"Inserted: {result.get('inserted_count', 0)}, "
                f"Errors: {result.get('error_count', 0)}"
            )

            # Log any errors
            if result.get("error_count", 0) > 0 and "errors" in result:
                for error in result["errors"]:
                    logger.error(f"API Error: {error}")
        else:
            logger.error(
                f"API call failed with status code {response.status_code}: {response.text}"
            )

    except Exception as e:
        logger.error(f"Error calling {name} endpoint: {str(e)}")


def update_status_job():
    """Job to update status of Jira issues."""
    call_api_endpoint("api/update-status", "Update Status")


def collect_closed_details_job():
    """Job to collect details for closed/deployed pd issues."""
    call_api_endpoint("api/collect-closed-details", "Collect Closed Details")


def collect_ac_details_job():
    """Job to collect details for deployed ac issues."""
    call_api_endpoint("api/collect-ac-details", "Collect AC Details")


def setup_schedule():
    """Set up the schedule for API calls."""
    # Update status every day at 1:00 AM
    schedule.every().day.at("01:00").do(update_status_job)

    # Collect closed details every day at 1:30 AM
    schedule.every().day.at("01:30").do(collect_closed_details_job)

    # Collect AC details every day at 1:45 AM
    schedule.every().day.at("01:45").do(collect_ac_details_job)

    logger.info("Scheduler initialized with the following jobs:")
    logger.info("- Update Status: Every day at 01:00")
    logger.info("- Collect Closed Details: Every day at 01:30")
    logger.info("- Collect AC Details: Every day at 01:45")


def run_scheduler():
    """Run the scheduler loop."""
    setup_schedule()

    logger.info("Scheduler started. Press Ctrl+C to exit.")

    try:
        # Run all jobs once at startup for testing
        logger.info("Running all jobs once at startup...")
        update_status_job()
        time.sleep(5)  # Wait 5 seconds between jobs
        collect_closed_details_job()
        time.sleep(5)  # Wait 5 seconds between jobs
        collect_ac_details_job()

        # Then run the scheduler
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user.")
    except Exception as e:
        logger.error(f"Scheduler error: {str(e)}")


if __name__ == "__main__":
    run_scheduler()
