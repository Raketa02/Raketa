"""The Bookings context's one refusal."""

from __future__ import annotations


class CourtTaken(Exception):
    """The court was booked by another game a moment ago — between the read that
    found it free and the write that claimed it. Raised by the repository when
    the store's own uniqueness refuses the second claim; the caller reads the
    courts again."""
