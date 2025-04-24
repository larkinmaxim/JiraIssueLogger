"""
Logging Configuration Module

This module provides a centralized configuration for logging throughout the application.
"""

import os
import logging
import sys
from pathlib import Path


def setup_logger(name, log_file=None, level=logging.INFO):
    """
    Set up a logger with the specified name, log file, and level.

    Args:
        name (str): The name of the logger
        log_file (str, optional): The path to the log file. Defaults to None.
        level (int, optional): The logging level. Defaults to logging.INFO.

    Returns:
        logging.Logger: The configured logger
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Create file handler if log_file is specified
    if log_file:
        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name, log_file=None, level=None):
    """
    Get a logger with the specified name, log file, and level.

    Args:
        name (str): The name of the logger
        log_file (str, optional): The path to the log file. Defaults to None.
        level (int, optional): The logging level. Defaults to None.

    Returns:
        logging.Logger: The configured logger
    """
    # Get log level from environment variable or use default
    if level is None:
        level_name = os.environ.get("LOG_LEVEL", "INFO")
        level = getattr(logging, level_name.upper(), logging.INFO)

    # Get log file from environment variable if not specified
    if log_file is None:
        log_file = os.environ.get("LOG_FILE")

    return setup_logger(name, log_file, level)


# Create default loggers
api_logger = get_logger("jira_logger.api", "logs/api.log")
jira_logger = get_logger("jira_logger.jira", "logs/jira.log")
bigquery_logger = get_logger("jira_logger.bigquery", "logs/bigquery.log")
scheduler_logger = get_logger("jira_logger.scheduler", "logs/scheduler.log")


class LoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter that adds context information to log messages.
    """

    def __init__(self, logger, extra=None):
        """
        Initialize the logger adapter.

        Args:
            logger (logging.Logger): The logger to adapt
            extra (dict, optional): Extra context information. Defaults to None.
        """
        super().__init__(logger, extra or {})

    def process(self, msg, kwargs):
        """
        Process the log message and add context information.

        Args:
            msg (str): The log message
            kwargs (dict): Keyword arguments for the log message

        Returns:
            tuple: (modified_message, modified_kwargs)
        """
        # Add context information to the message
        context_str = " ".join(f"{k}={v}" for k, v in self.extra.items())
        if context_str:
            msg = f"{msg} [{context_str}]"

        return msg, kwargs


def get_context_logger(name, context=None, log_file=None, level=None):
    """
    Get a logger with context information.

    Args:
        name (str): The name of the logger
        context (dict, optional): Context information. Defaults to None.
        log_file (str, optional): The path to the log file. Defaults to None.
        level (int, optional): The logging level. Defaults to None.

    Returns:
        LoggerAdapter: The configured logger adapter
    """
    logger = get_logger(name, log_file, level)
    return LoggerAdapter(logger, context)
