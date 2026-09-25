"""A stored moment, read back as the UTC instant it was written as.

Every moment this schema stores is written in UTC into a ``timezone=True``
column — but that is a promise the *database* keeps, and SQLite does not: it
stores the text and hands back a naive ``datetime``, which then raises the first
time it is compared with an aware one. The normalisation belongs at the seam
where a column becomes a domain value, once, rather than in every repository
that reads a moment.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.kernel import Instant, instant


def stored_instant(value: datetime) -> Instant:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return instant(value)


def stored_instant_or_none(value: datetime | None) -> Instant | None:
    return None if value is None else stored_instant(value)
