"""The Notifications context's two streams (#549; ``docs/adr/0189`` §5; the
mechanics §17.2).

**Notification preferences** — one stream per player, filed under the player's
own id and born by being used: the three choices a player switches, and the
phones a push reaches.

**A player's notices of one day** — one stream per player per day in Kraków
(``notices.day_id_for``): what the player was told that day, and what was
gathered into a notice already given. A day is the unit the caps are counted
in, so a second process telling the same player on the same day collides on the
stream rather than going past a cap.

**A notice records facts, never words.** The game it is about, the club, the
hour, the money and the people it names travel as ids and numbers; the words a
phone shows are drawn from them when it is pushed and when the list is read, so
a name is the person's name as it stands and a sentence can be reworded without
rewriting anybody's history.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class NotificationChoiceSwitched:
    """A player switched one of the three choices — ``YOU_COMPLETE_IT``,
    ``CHALLENGES_FOR_YOU`` or ``FILL_IN_ALERTS`` — on or off."""

    player_id: UUID
    choice: str
    on: bool
    occurred_at: datetime


@dataclass(frozen=True)
class PushDeviceRegistered:
    """A phone signed in as this player asked to be pushed to. ``device`` is
    the SHA-256 of its Expo push token (``preferences.device_of``) — **never the
    token**, which would let anybody holding it push to the phone and so may
    not enter the event store or the outbox (ADR-0184 §4): the token waits in
    ``push_devices`` alone, written beside this event and deleted with it."""

    player_id: UUID
    device: str
    occurred_at: datetime


@dataclass(frozen=True)
class PushDeviceRemoved:
    """A phone is no longer pushed to as this player: it signed out, another
    account registered it, a newer phone took its place, or the push service
    said it is gone."""

    player_id: UUID
    device: str
    occurred_at: datetime


@dataclass(frozen=True)
class NoticeGiven:
    """**The player was told** — pushed to every phone they registered and
    listed in their recent notices.

    ``kind`` is the ``NoticeKind`` code and ``key`` what makes it this notice
    and no other, so the same thing is never told twice. ``game_id`` is the
    game it is about — its proposal's id, which its booking takes — and
    ``opens`` the screen a tap opens it on. ``people`` are the players it
    names (who left, who posted), ``amount_grosze`` the money it says and
    ``reason`` the code it says why with; each is ``None`` or empty where the
    kind says none.
    """

    notice_id: UUID
    player_id: UUID
    #: The day in Kraków, ``YYYY-MM-DD`` — the stream's own.
    day: str
    kind: str
    key: str
    game_id: UUID
    pool_id: UUID
    sport: str
    #: ``COMPETITIVE`` or ``FOR_FUN``.
    game_kind: str
    club_id: UUID
    starts_at: datetime
    #: ``BOOKING``, ``PROPOSAL`` or ``DECK``.
    opens: str
    amount_grosze: int | None
    people: tuple[UUID, ...]
    reason: str | None
    occurred_at: datetime

    def __post_init__(self) -> None:
        # JSON hands a list of strings back; the codec coerces a bare ``UUID``
        # hint and nothing inside a tuple.
        object.__setattr__(
            self, "people", tuple(UUID(str(person)) for person in self.people)
        )


@dataclass(frozen=True)
class NoticeBundled:
    """**Gathered, not pushed**: the day's notices of this kind reached their
    cap, so this one joined ``notice_id`` — the day's last of the kind — and
    the list says how many it holds now. ``key`` and ``game_id`` are the one
    gathered."""

    notice_id: UUID
    player_id: UUID
    day: str
    kind: str
    key: str
    game_id: UUID
    occurred_at: datetime
