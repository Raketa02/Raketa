"""The Club's stream and the Club account's.

**Two streams, and the password hash is on only one of them.** A club's facts
are public — searched by every player — and its credentials are not, so the
account is an aggregate of its own (``docs/adr/0182`` §3). The club's stream is
what the search projection is built from, and it never holds a hash.

A club's sports travel as their registry codes, in the registry's order, and
are **forced to a tuple on the way in and out of storage**: the codec hands a
JSON array back as a list, and an event read back must equal the one appended.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class ClubRegistered:
    """A club signed up. The first event on its stream, and the only way one
    begins: nothing about clubs is hard-coded (``docs/adr/0182`` §7)."""

    club_id: UUID
    name: str
    district: str
    city: str
    sports: tuple[str, ...]
    latitude: float
    longitude: float
    occurred_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "sports", tuple(self.sports))


@dataclass(frozen=True)
class ClubDetailsChanged:
    """The desk changed its club's details — **all five, as they now stand**.

    One event for any edit, because the details are edited on one page and
    saved together (``docs/adr/0182`` §5); the fold keeps the latest. A save
    that changes nothing records nothing.
    """

    club_id: UUID
    name: str
    district: str
    city: str
    sports: tuple[str, ...]
    latitude: float
    longitude: float
    occurred_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "sports", tuple(self.sports))


@dataclass(frozen=True)
class ClubAccountOpened:
    """The club's sign-in, created with the club in the same sign-up.

    Carries the hash on the account's own stream, as ``UserRegistered`` does on
    a User's (``docs/adr/0185`` §7) — and never the password.
    """

    account_id: UUID
    club_id: UUID
    email: str
    password_hash: str
    occurred_at: datetime


@dataclass(frozen=True)
class ClubAccountPasswordChanged:
    """The desk set a new password, which **signs the club out everywhere**
    (``docs/adr/0185`` §7).

    Carries the new hash on the account's own stream, as ``ClubAccountOpened``
    carries the first. ``occurred_at`` is the credentials-changed instant: an
    access token the club surface issued before it is refused.
    """

    account_id: UUID
    password_hash: str
    occurred_at: datetime
