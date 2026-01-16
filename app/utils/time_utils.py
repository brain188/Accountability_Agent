"""
Time Utilities

Helper functions for working with dates, times, and timezones.
"""

import logging
from datetime import datetime, date, timedelta
from typing import Optional, Tuple

import pytz
from pytz import timezone as pytz_timezone

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


def get_timezone(tz_name: Optional[str] = None) -> pytz.tzinfo.BaseTzInfo:
    """
    Get timezone object.
    
    Args:
        tz_name: Timezone name (e.g., 'America/New_York'). 
                If None, uses settings default.
    
    Returns:
        pytz timezone object
    
    Raises:
        pytz.UnknownTimeZoneError: If timezone name is invalid
    """
    if tz_name is None:
        tz_name = settings.timezone
    
    try:
        return pytz_timezone(tz_name)
    except pytz.UnknownTimeZoneError:
        logger.error(f"Unknown timezone: {tz_name}. Using UTC.")
        return pytz.UTC


def get_current_datetime(tz_name: Optional[str] = None) -> datetime:
    """
    Get current datetime in specified timezone.
    
    Args:
        tz_name: Timezone name. If None, uses settings default.
    
    Returns:
        Timezone-aware datetime object
    """
    tz = get_timezone(tz_name)
    return datetime.now(tz)


def get_current_date(tz_name: Optional[str] = None) -> date:
    """
    Get current date in specified timezone.
    
    Args:
        tz_name: Timezone name. If None, uses settings default.
    
    Returns:
        Date object
    """
    return get_current_datetime(tz_name).date()


def localize_datetime(dt: datetime, tz_name: Optional[str] = None) -> datetime:
    """
    Convert naive datetime to timezone-aware datetime.
    
    Args:
        dt: Naive datetime object
        tz_name: Timezone name. If None, uses settings default.
    
    Returns:
        Timezone-aware datetime object
    """
    if dt.tzinfo is not None:
        # Already timezone-aware
        return dt
    
    tz = get_timezone(tz_name)
    return tz.localize(dt)


def is_weekday(check_date: Optional[date] = None, tz_name: Optional[str] = None) -> bool:
    """
    Check if a date is a weekday (Monday-Friday).
    
    Args:
        check_date: Date to check. If None, uses current date.
        tz_name: Timezone name. If None, uses settings default.
    
    Returns:
        True if weekday (Monday-Friday), False otherwise
    """
    if check_date is None:
        check_date = get_current_date(tz_name)
    
    # weekday() returns 0-6 (Monday-Sunday)
    return check_date.weekday() < 5


def get_date_range(
    days_back: int = 1,
    end_date: Optional[date] = None,
    tz_name: Optional[str] = None
) -> Tuple[date, date]:
    """
    Get date range for the past N days.
    
    Args:
        days_back: Number of days to go back
        end_date: End date of range. If None, uses current date.
        tz_name: Timezone name. If None, uses settings default.
    
    Returns:
        Tuple of (start_date, end_date)
    """
    if end_date is None:
        end_date = get_current_date(tz_name)
    
    start_date = end_date - timedelta(days=days_back - 1)
    return start_date, end_date


def get_start_of_day(
    target_date: Optional[date] = None,
    tz_name: Optional[str] = None
) -> datetime:
    """
    Get start of day (00:00:00) for a given date.
    
    Args:
        target_date: Date to get start of. If None, uses current date.
        tz_name: Timezone name. If None, uses settings default.
    
    Returns:
        Timezone-aware datetime at start of day
    """
    if target_date is None:
        target_date = get_current_date(tz_name)
    
    tz = get_timezone(tz_name)
    naive_dt = datetime.combine(target_date, datetime.min.time())
    return tz.localize(naive_dt)


def get_end_of_day(
    target_date: Optional[date] = None,
    tz_name: Optional[str] = None
) -> datetime:
    """
    Get end of day (23:59:59) for a given date.
    
    Args:
        target_date: Date to get end of. If None, uses current date.
        tz_name: Timezone name. If None, uses settings default.
    
    Returns:
        Timezone-aware datetime at end of day
    """
    if target_date is None:
        target_date = get_current_date(tz_name)
    
    tz = get_timezone(tz_name)
    naive_dt = datetime.combine(target_date, datetime.max.time())
    return tz.localize(naive_dt)


def format_date(dt: date, format_str: str = "%Y-%m-%d") -> str:
    """
    Format date to string.
    
    Args:
        dt: Date to format
        format_str: Format string (strftime format)
    
    Returns:
        Formatted date string
    """
    return dt.strftime(format_str)


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime to string.
    
    Args:
        dt: Datetime to format
        format_str: Format string (strftime format)
    
    Returns:
        Formatted datetime string
    """
    return dt.strftime(format_str)


def get_weekday_name(target_date: Optional[date] = None) -> str:
    """
    Get name of weekday for a given date.
    
    Args:
        target_date: Date to check. If None, uses current date.
    
    Returns:
        Weekday name (e.g., 'Monday')
    """
    if target_date is None:
        target_date = get_current_date()
    
    return target_date.strftime("%A")


def get_previous_weekday(
    target_date: Optional[date] = None,
    tz_name: Optional[str] = None
) -> date:
    """
    Get previous weekday (skipping weekends).
    
    Args:
        target_date: Starting date. If None, uses current date.
        tz_name: Timezone name. If None, uses settings default.
    
    Returns:
        Previous weekday date
    """
    if target_date is None:
        target_date = get_current_date(tz_name)
    
    prev_date = target_date - timedelta(days=1)
    
    # Keep going back until we find a weekday
    while not is_weekday(prev_date):
        prev_date -= timedelta(days=1)
    
    return prev_date


def utc_to_local(
    utc_dt: datetime,
    tz_name: Optional[str] = None
) -> datetime:
    """
    Convert UTC datetime to local timezone.
    
    Args:
        utc_dt: UTC datetime
        tz_name: Target timezone name. If None, uses settings default.
    
    Returns:
        Datetime in local timezone
    """
    if utc_dt.tzinfo is None:
        utc_dt = pytz.UTC.localize(utc_dt)
    
    local_tz = get_timezone(tz_name)
    return utc_dt.astimezone(local_tz)


def local_to_utc(
    local_dt: datetime,
    tz_name: Optional[str] = None
) -> datetime:
    """
    Convert local datetime to UTC.
    
    Args:
        local_dt: Local datetime
        tz_name: Source timezone name. If None, uses settings default.
    
    Returns:
        Datetime in UTC
    """
    if local_dt.tzinfo is None:
        local_tz = get_timezone(tz_name)
        local_dt = local_tz.localize(local_dt)
    
    return local_dt.astimezone(pytz.UTC)