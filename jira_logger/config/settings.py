"""
Application Settings Module

This module provides access to application settings from environment variables
and configuration files.
"""

import os
import json
from pathlib import Path
from functools import lru_cache
from typing import Dict, Any, Optional

from dotenv import load_dotenv
from pydantic import BaseSettings, Field

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """

    # API settings
    api_port: int = Field(default=8000, env="API_PORT")
    api_host: str = Field(default="0.0.0.0", env="API_HOST")

    # Jira settings
    jira_base_url: str = Field(..., env="JIRA_BASE_URL")
    jira_api_token: str = Field(..., env="JIRA_API_TOKEN")

    # Google Cloud settings
    google_application_credentials: str = Field(
        ..., env="GOOGLE_APPLICATION_CREDENTIALS"
    )
    google_cloud_project: Optional[str] = Field(
        default=None, env="GOOGLE_CLOUD_PROJECT"
    )

    # BigQuery settings
    bigquery_dataset_id: str = Field(default="jira_data", env="BIGQUERY_DATASET_ID")
    bigquery_table_id: str = Field(default="jira_issues", env="BIGQUERY_TABLE_ID")

    # SSL settings
    ssl_cert_path: Optional[str] = Field(default=None, env="SSL_CERT_PATH")
    use_ssl_verification: bool = Field(default=True, env="USE_SSL_VERIFICATION")

    # Logging settings
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: Optional[str] = Field(default=None, env="LOG_FILE")

    # Data directory settings
    data_dir: str = Field(default="jira_logger/data", env="DATA_DIR")
    jira_raw_responses_dir: str = Field(
        default="jira_logger/data/jira_raw_responses", env="JIRA_RAW_RESPONSES_DIR"
    )
    jira_issues_dir: str = Field(
        default="jira_logger/data/jira_issues", env="JIRA_ISSUES_DIR"
    )

    class Config:
        """
        Configuration for the Settings class.
        """

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings.

    Returns:
        Settings: Application settings
    """
    return Settings()


def get_ssl_settings() -> Dict[str, Any]:
    """
    Get SSL settings.

    Returns:
        dict: SSL settings
    """
    settings = get_settings()

    from jira_logger.utils.ssl_utils import find_netskope_certificate

    # Use SSL certificate path from settings or find Netskope certificate
    cert_path = settings.ssl_cert_path or find_netskope_certificate()

    return {
        "use_ssl_verification": settings.use_ssl_verification,
        "certificate_path": cert_path,
        "last_updated": None,  # Will be set when used
    }


def get_jira_settings() -> Dict[str, Any]:
    """
    Get Jira settings.

    Returns:
        dict: Jira settings
    """
    settings = get_settings()

    return {
        "base_url": settings.jira_base_url,
        "api_token": settings.jira_api_token,
    }


def get_bigquery_settings() -> Dict[str, Any]:
    """
    Get BigQuery settings.

    Returns:
        dict: BigQuery settings
    """
    settings = get_settings()

    return {
        "dataset_id": settings.bigquery_dataset_id,
        "table_id": settings.bigquery_table_id,
        "credentials_path": settings.google_application_credentials,
        "project_id": settings.google_cloud_project,
    }


def get_data_dirs() -> Dict[str, str]:
    """
    Get data directory paths.

    Returns:
        dict: Data directory paths
    """
    settings = get_settings()

    # Create directories if they don't exist
    for dir_path in [
        settings.data_dir,
        settings.jira_raw_responses_dir,
        settings.jira_issues_dir,
    ]:
        os.makedirs(dir_path, exist_ok=True)

    return {
        "data_dir": settings.data_dir,
        "jira_raw_responses_dir": settings.jira_raw_responses_dir,
        "jira_issues_dir": settings.jira_issues_dir,
    }
