from datetime import datetime, timezone, timedelta


# ICT (Indochina Time) is UTC+7
ICT = timezone(timedelta(hours=7))


def utc_to_ict(dt: datetime) -> datetime:
    """
    Convert UTC datetime to ICT (Indochina Time, UTC+7)

    Args:
        dt: datetime object (can be naive or timezone-aware)

    Returns:
        datetime object in ICT timezone
    """
    if dt is None:
        return None

    # If datetime is naive (no timezone info), assume it's UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    # Convert to ICT
    return dt.astimezone(ICT)


def format_time_ict(dt: datetime, format_str: str = '%H:%M') -> str:
    """
    Format datetime as ICT time string

    Args:
        dt: datetime object (can be naive or timezone-aware)
        format_str: strftime format string (default: '%H:%M')

    Returns:
        Formatted time string in ICT timezone
    """
    if dt is None:
        return ""

    ict_time = utc_to_ict(dt)
    return ict_time.strftime(format_str)


def format_datetime_ict(dt: datetime, format_str: str = '%d/%m/%Y %I:%M %p') -> str:
    """
    Format datetime as ICT datetime string

    Args:
        dt: datetime object (can be naive or timezone-aware)
        format_str: strftime format string (default: '%d/%m/%Y %I:%M %p')

    Returns:
        Formatted datetime string in ICT timezone
    """
    if dt is None:
        return ""

    ict_time = utc_to_ict(dt)
    return ict_time.strftime(format_str)
