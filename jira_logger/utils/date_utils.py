"""
Date Utility Functions

This module provides utility functions for working with dates and times,
including calculating durations and formatting dates.
"""

import datetime
from typing import Optional, Tuple


def parse_iso_date(date_str: Optional[str]) -> Optional[datetime.datetime]:
    """
    Parse an ISO format date string into a datetime object.

    Args:
        date_str (str): The ISO format date string to parse

    Returns:
        datetime.datetime: The parsed datetime object, or None if parsing fails
    """
    if not date_str:
        return None

    try:
        # Handle both with and without timezone information
        return datetime.datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def format_iso_date(dt: Optional[datetime.datetime]) -> Optional[str]:
    """
    Format a datetime object as an ISO format string.

    Args:
        dt (datetime.datetime): The datetime object to format

    Returns:
        str: The formatted ISO date string, or None if dt is None
    """
    if not dt:
        return None

    return dt.isoformat()


def calculate_duration(
    start_date: Optional[str], end_date: Optional[str]
) -> Optional[float]:
    """
    Calculate duration in days between two dates, excluding weekends.

    Args:
        start_date (str): Start date in ISO format
        end_date (str): End date in ISO format

    Returns:
        float: Number of weekdays between start and end dates, or None if dates are invalid
    """
    if not start_date or not end_date:
        return None

    start = parse_iso_date(start_date)
    end = parse_iso_date(end_date)

    if not start or not end:
        return None

    # Initialize duration tracking
    total_days = 0
    current = start

    # Iterate through each day
    while current <= end:
        # Check if current day is a weekday (Monday = 0, Sunday = 6)
        if current.weekday() < 5:  # Monday to Friday
            # Add 1 day per weekday
            total_days += 1

        # Move to next day
        current += datetime.timedelta(days=1)

    return round(total_days, 2)


def get_date_range(start_date: str, days: int) -> Tuple[str, str]:
    """
    Get a date range starting from a given date and extending for a specified number of days.

    Args:
        start_date (str): Start date in ISO format
        days (int): Number of days in the range

    Returns:
        tuple: (start_date, end_date) in ISO format
    """
    start = parse_iso_date(start_date)

    if not start:
        raise ValueError(f"Invalid start date: {start_date}")

    # Calculate end date (add days, not counting weekends)
    end = start
    days_added = 0

    while days_added < days:
        end += datetime.timedelta(days=1)

        # Only count weekdays
        if end.weekday() < 5:  # Monday to Friday
            days_added += 1

    return start_date, format_iso_date(end)


def is_weekday(date_str: str) -> bool:
    """
    Check if a date is a weekday (Monday to Friday).

    Args:
        date_str (str): Date in ISO format

    Returns:
        bool: True if the date is a weekday, False otherwise
    """
    dt = parse_iso_date(date_str)

    if not dt:
        return False

    return dt.weekday() < 5  # Monday to Friday


def get_current_timestamp() -> str:
    """
    Get the current timestamp in ISO format.

    Returns:
        str: Current timestamp in ISO format
    """
    return datetime.datetime.utcnow().isoformat()


def format_timestamp_for_filename() -> str:
    """
    Format the current timestamp for use in filenames.

    Returns:
        str: Formatted timestamp (YYYYMMDD_HHMMSS)
    """
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
