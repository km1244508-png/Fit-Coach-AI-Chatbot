from datetime import datetime, timezone


def utcnow() -> datetime:
    """UTC 'now' truncated to milliseconds (MongoDB's precision) so values round-trip exactly."""
    now = datetime.now(timezone.utc)
    return now.replace(microsecond=(now.microsecond // 1000) * 1000)


def as_utc(dt: datetime) -> datetime:
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
