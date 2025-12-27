"""
Timezone utilities for converting between UTC and ICT (Cambodia timezone)
"""
from datetime import datetime, timedelta, timezone, date


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


def get_ict_today() -> date:
    """
    Get today's date in ICT timezone

    Returns:
        Today's date in ICT timezone
    """
    now_ict = datetime.now(ICT)
    return now_ict.date()


def ict_date_to_utc_range(ict_date: date) -> tuple[datetime, datetime]:
    """
    Convert an ICT date to UTC datetime range (start and end of day)

    Since the database stores timestamps in UTC, we need to convert
    ICT dates to the equivalent UTC datetime range.

    Example:
        ICT date 2025-12-28
        -> Start: 2025-12-27 17:00:00 UTC (2025-12-28 00:00:00 ICT)
        -> End:   2025-12-28 16:59:59 UTC (2025-12-28 23:59:59 ICT)

    Args:
        ict_date: Date in ICT timezone

    Returns:
        Tuple of (start_datetime_utc, end_datetime_utc)
    """
    # Create start of day in ICT (00:00:00)
    start_ict = datetime.combine(ict_date, datetime.min.time()).replace(tzinfo=ICT)

    # Create end of day in ICT (23:59:59)
    end_ict = datetime.combine(ict_date, datetime.max.time()).replace(tzinfo=ICT)

    # Convert to UTC
    start_utc = start_ict.astimezone(timezone.utc).replace(tzinfo=None)
    end_utc = end_ict.astimezone(timezone.utc).replace(tzinfo=None)

    return start_utc, end_utc
