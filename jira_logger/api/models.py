"""
API Models for Jira Logger

This module defines the Pydantic models used for request and response validation
in the Jira Logger API.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class JiraIssue(BaseModel):
    """Model for a Jira issue."""

    issue_key: str
    summary: str
    status: str
    project_ticket: Optional[str] = None
    planned_dev_start: Optional[str] = None
    planned_dev_finish: Optional[str] = None
    planned_duration: Optional[float] = None
    actual_start: Optional[str] = None
    actual_finish: Optional[str] = None
    actual_duration: Optional[float] = None
    details_updated_at: Optional[str] = None


class UpdateRequest(BaseModel):
    """Model for update request parameters."""

    save_raw_response: bool = False
    raw_response_dir: str = "jira_logger/data/jira_raw_responses"


class UpdateResponse(BaseModel):
    """Model for update response."""

    updated_count: int
    inserted_count: int
    error_count: int
    errors: List[str] = []


class SSLSettingsUpdate(BaseModel):
    """Model for SSL settings update request."""

    use_ssl_verification: bool
    certificate_path: Optional[str] = None


class SSLSettingsResponse(BaseModel):
    """Model for SSL settings response."""

    use_ssl_verification: bool
    certificate_path: Optional[str] = None
    last_updated: str
