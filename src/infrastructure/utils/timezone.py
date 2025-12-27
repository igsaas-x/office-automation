"""
Timezone utilities for converting between UTC and ICT (Cambodia timezone)
"""
from datetime import datetime, timedelta, timezone


# Cambodia uses Indochina Time (ICT) which is UTC+7
ICT = timezone(timedelta(hours=7))


def utc_to_ict(utc_datetime: datetime) -> datetime:
    """
    Convert UTC datetime to ICT (Cambodia timezone)

    Args:
        utc_datetime: Datetime in UTC (timezone-naive or timezone-aware)

    Returns:
        Datetime in ICT timezone (timezone-aware)
    """
    if utc_datetime is None:
        return None

    # If timezone-naive, assume it's UTC
    if utc_datetime.tzinfo is None:
        utc_datetime = utc_datetime.replace(tzinfo=timezone.utc)

    # Convert to ICT
    return utc_datetime.astimezone(ICT)


def format_ict_datetime(utc_datetime: datetime, format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
    """
    Convert UTC datetime to ICT and format as string

    Args:
        utc_datetime: Datetime in UTC
        format_str: Format string for strftime

    Returns:
        Formatted datetime string in ICT timezone
    """
    if utc_datetime is None:
        return "N/A"

    ict_datetime = utc_to_ict(utc_datetime)
    return ict_datetime.strftime(format_str)


def format_ict_time(utc_datetime: datetime) -> str:
    """
    Convert UTC datetime to ICT time only (HH:MM format)

    Args:
        utc_datetime: Datetime in UTC

    Returns:
        Formatted time string in ICT timezone (HH:MM)
    """
    return format_ict_datetime(utc_datetime, '%H:%M')


def format_ict_date(utc_datetime: datetime) -> str:
    """
    Convert UTC datetime to ICT date only (YYYY-MM-DD format)

    Args:
        utc_datetime: Datetime in UTC

    Returns:
        Formatted date string in ICT timezone
    """
    return format_ict_datetime(utc_datetime, '%Y-%m-%d')
