"""
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
