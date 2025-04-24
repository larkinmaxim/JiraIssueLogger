"""
Environment Configuration Module

This module provides environment-specific configuration settings.
"""

import os
import json
from enum import Enum
from typing import Dict, Any, Optional

from jira_logger.config.settings import get_settings


class Environment(str, Enum):
    """
    Enum for environment types.
    """

    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


def get_environment() -> Environment:
    """
    Get the current environment.

    Returns:
        Environment: The current environment
    """
    env_name = os.environ.get("ENVIRONMENT", "development").lower()

    if env_name in ("prod", "production"):
        return Environment.PRODUCTION
    elif env_name in ("test", "testing"):
        return Environment.TESTING
    else:
        return Environment.DEVELOPMENT


def is_development() -> bool:
    """
    Check if the current environment is development.

    Returns:
        bool: True if the current environment is development
    """
    return get_environment() == Environment.DEVELOPMENT


def is_testing() -> bool:
    """
    Check if the current environment is testing.

    Returns:
        bool: True if the current environment is testing
    """
    return get_environment() == Environment.TESTING


def is_production() -> bool:
    """
    Check if the current environment is production.

    Returns:
        bool: True if the current environment is production
    """
    return get_environment() == Environment.PRODUCTION


def get_environment_settings() -> Dict[str, Any]:
    """
    Get environment-specific settings.

    Returns:
        dict: Environment-specific settings
    """
    env = get_environment()
    settings = get_settings()

    # Common settings
    env_settings = {
        "environment": env,
        "debug": not is_production(),
    }

    # Environment-specific settings
    if env == Environment.DEVELOPMENT:
        env_settings.update(
            {
                "use_ssl_verification": False,
                "log_level": "DEBUG",
            }
        )
    elif env == Environment.TESTING:
        env_settings.update(
            {
                "use_ssl_verification": True,
                "log_level": "INFO",
            }
        )
    elif env == Environment.PRODUCTION:
        env_settings.update(
            {
                "use_ssl_verification": True,
                "log_level": "INFO",
            }
        )

    return env_settings


def configure_environment():
    """
    Configure the environment.

    This function sets up environment-specific configuration.
    """
    env = get_environment()
    env_settings = get_environment_settings()

    # Set up logging
    from jira_logger.utils.logging import get_logger

    logger = get_logger("jira_logger.environment")
    logger.info(f"Environment: {env}")
    logger.info(f"Debug mode: {env_settings['debug']}")

    # Set up SSL verification
    if not env_settings["use_ssl_verification"]:
        import warnings

        warnings.filterwarnings("ignore", message="Unverified HTTPS request")
        logger.warning("SSL verification is disabled")
