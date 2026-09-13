from datetime import date, datetime, timedelta, timezone


def utc_now() -> datetime:
    """Return the current UTC datetime."""

    return datetime.now(timezone.utc)


def utc_timestamp() -> int:
    """Return the current UTC time as a Unix timestamp."""

    return int(utc_now().timestamp())


def datetime_to_timestamp(value: datetime) -> int:
    """Convert a datetime to a Unix timestamp."""

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return int(value.timestamp())


def timestamp_to_datetime(timestamp: int) -> datetime:
    """Convert a Unix timestamp to a UTC datetime."""

    return datetime.fromtimestamp(
        timestamp,
        tz=timezone.utc,
    )


def get_today_date() -> date:
    """Return today's UTC date."""

    return utc_now().date()


def get_week_start_date() -> date:
    """Return the current week's Monday date."""

    today = get_today_date()

    return today - timedelta(
        days=today.weekday(),
    )


def get_month_start_date() -> date:
    """Return the first day of the current UTC month."""

    today = get_today_date()

    return today.replace(day=1)


def get_next_day_date(value: date) -> date:
    """Return the date immediately after the given date."""

    return value + timedelta(days=1)


def get_next_week_start_date(value: date | None = None) -> date:
    """Return the Monday starting the week after the given date."""

    start = value if value is not None else get_week_start_date()

    return start + timedelta(days=7)


def get_next_month_start_date(value: date | None = None) -> date:
    """Return the first day of the month after the given date."""

    start = value if value is not None else get_month_start_date()

    if start.month == 12:
        return start.replace(
            year=start.year + 1,
            month=1,
        )

    return start.replace(
        month=start.month + 1,
    )
