"""
Script to fix __init__.py files with proper docstrings.

This script writes proper docstrings to all __init__.py files in the jira_logger directory.
"""

import os
import glob

# Define docstrings for each package
DOCSTRINGS = {
    "jira_logger/__init__.py": '''"""
Jira Logger with BigQuery Integration

This package provides functionality to collect Jira issue data and store it in BigQuery.
"""

__version__ = "1.0.0"
''',
    "jira_logger/api/__init__.py": '''"""
API endpoints for the Jira Logger application.

This package contains API-related modules for the Jira Logger application,
including endpoint definitions, request/response models, and middleware.
"""

from fastapi import FastAPI

# Create FastAPI application
app = FastAPI(
    title="Jira Logger API",
    description="API for logging Jira issues to BigQuery",
    version="1.0.0",
)
''',
    "jira_logger/config/__init__.py": '''"""
Configuration for the Jira Logger application.

This package contains configuration modules for the Jira Logger application,
including settings and environment-specific configuration.
"""
''',
    "jira_logger/core/__init__.py": '''"""
Core functionality for the Jira Logger application.

This package contains the core business logic for the Jira Logger application,
including Jira API integration, BigQuery integration, and scheduling.
"""
''',
    "jira_logger/core/bigquery/__init__.py": '''"""
BigQuery integration for the Jira Logger application.

This package contains modules for interacting with Google BigQuery,
including creating datasets and tables, inserting data, and performing queries.
"""
''',
    "jira_logger/core/jira/__init__.py": '''"""
Jira API integration for the Jira Logger application.

This package contains modules for interacting with the Jira API,
including fetching issue data and parsing changelog information.
"""
''',
    "jira_logger/data/__init__.py": '''"""
Data storage for the Jira Logger application.

This package contains data storage directories for the Jira Logger application,
including directories for raw Jira responses and processed Jira issues.
"""
''',
    "jira_logger/data/jira_issues/__init__.py": '''"""
Processed Jira issues storage.

This directory contains processed Jira issues data,
saved with timestamps for analysis and reporting purposes.
"""
''',
    "jira_logger/data/jira_raw_responses/__init__.py": '''"""
Raw Jira API responses storage.

This directory contains raw JSON responses from the Jira API,
saved with timestamps for debugging and troubleshooting purposes.
"""
''',
    "jira_logger/docs/__init__.py": '''"""
Documentation for the Jira Logger application.

This package contains documentation for the Jira Logger application,
including the Product Requirements Document, implementation plan, deployment guide, and API documentation.
"""
''',
    "jira_logger/scripts/__init__.py": '''"""
Scripts for the Jira Logger application.

This package contains standalone scripts for the Jira Logger application,
including scripts to save Jira responses, set up Google Cloud, and test the API.
"""
''',
    "jira_logger/scripts/test_scripts/__init__.py": '''"""
Test scripts for the Jira Logger application.

This package contains test scripts for the Jira Logger application,
including scripts to test the API and BigQuery connection.
"""
''',
    "jira_logger/utils/__init__.py": '''"""
Utility functions for the Jira Logger application.

This package contains utility modules for the Jira Logger application,
including SSL certificate handling, date utilities, and logging configuration.
"""
''',
}


def fix_init_file(file_path):
    """
    Fix an __init__.py file with a proper docstring.

    Args:
        file_path: Path to the file to fix
    """
    try:
        # Get the docstring for this file
        docstring = DOCSTRINGS.get(file_path)
        if docstring:
            # Write the docstring to the file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(docstring)
            print(f"Fixed {file_path}")
        else:
            print(f"No docstring defined for {file_path}")
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")


def main():
    """
    Main function to fix all __init__.py files.
    """
    # Fix each file with a defined docstring
    for file_path in DOCSTRINGS:
        fix_init_file(file_path)


if __name__ == "__main__":
    main()
