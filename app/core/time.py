from datetime import datetime, timezone


def utcnow() -> datetime:
    """Naive UTC now — same semantics as the deprecated datetime.utcnow()."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
