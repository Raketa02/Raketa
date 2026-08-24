"""The wire shape of *reach me here*: one token, its platform, one setting.

Its own module beside ``seat_schemas.py`` and for the same reason: ``schemas.py``
is the *screen's* contract, and this is a write that composes no screen at all.

**It is the only thing a client ever sends about push**, and it is deliberately
three fields. Whether a player may be interrupted is a fact about her phone that
her phone reads; what she is told about is decided by the cascade and the
ranking; and *what the message says* is the server's one sentence (ADR-0075).
A client that could send a preference here would be holding a rule, which is the
one thing ADR-0053 leaves the phone none of.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.modules.now.domain.push import Platform, TimeSensitiveSetting


class RegisterDeviceRequest(BaseModel):
    """*Reach me here.* Sent on sign-in, on token rotation, and on a settings change.

    **No moment.** When a phone told us is the server's fact; a client-supplied
    one would let a phone with a wrong clock decide which of two registrations
    is newer.
    """

    #: What the transport addresses. Bounded on the wire rather than only in the
    #: column, so an oversized value is a 422 about the request instead of a
    #: database error about a string.
    token: str = Field(min_length=1, max_length=512)

    #: Which fields a message for this phone carries — the **only** thing on
    #: this request that changes what the server does.
    platform: Platform

    #: ``enabled`` / ``disabled`` / ``notSupported``, read from
    #: ``UNNotificationSettings.timeSensitiveSetting`` on iOS 15+ and reported
    #: as ``notSupported`` by anything that has no such setting to read.
    #:
    #: **Nothing branches on it** (ADR-0065). A player who has revoked Time
    #: Sensitive keeps her standby priority, still gets the seat, and still sees
    #: the line when she next looks: demoting her would quietly cost her seats
    #: as a punishment for a settings choice. It is observability — if a large
    #: fraction of players revoke, that record's central judgement was wrong,
    #: and this field is the only way we would ever learn it.
    #:
    #: It is **required**, because a client that omitted it would be reporting
    #: *disabled* by silence, and ``notSupported`` is a fourth value rather than
    #: a synonym for a refusal.
    time_sensitive_setting: TimeSensitiveSetting
