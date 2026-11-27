"""The Club payout aggregate — event-sourced, one stream per club per day it is
paid for (#548; the mechanics §12.6, §16.11).

**The club is paid after the game is played.** Every share a player pays is
taken on the club's own account — the club is the seller — and **waits there**:
until a game starts, somebody leaving or the club's own cancel gives money back
out of it. Once a game is **over** — played, or called off with everybody given
back — and **nothing about its money is still on its way**, what it left the club
is the club's to have. At the **close of a club day** (``last_closed_day``),
everything owed and not yet paid out is decided in **one payout**: one a day at
most, as a normal payout would be, and one email.

**What is owed, game by game**: every share taken, less what was given back,
less the provider's card fee on it (``SeatCharge.net_grosze``) — below nought
for a game given back whole, whose fees the club bears. **Never an estimate**
(#641): a share whose fee is not yet known is not settled, so its game waits
for the provider to say it. A day whose games left
less than nothing pays nothing out: they wait, and are netted against the next
day that leaves the club something, so a payout never sends more than the
club's games left it.

**Its id is the club and the day**, so a second process deciding the same day
collides on the stream and is stepped over — the job needs no lock.

**Rakieta decides, the provider acts** — the same two kinds of fact as a refund's:
the payout is decided in the job's transaction, and made at the provider from
the outbox after the commit, under the payout's own key — so a provider that
cannot take it yet leaves a decision that delivery retries, never money sent
with nothing written.
"""

from __future__ import annotations

from collections.abc import Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date
from typing import Final
from uuid import UUID, uuid5

from app.kernel import Instant, instant, invariant
from app.modules.payments.domain.events import ClubPayoutDecided, ClubPayoutSent
from app.modules.payments.domain.provider import Payout
from app.modules.payments.domain.seat_charge import SeatCharge
from app.shared.domain import DomainEvent
from app.shared.domain.events import EventRecorder

#: What a club day's payout id is drawn under — fixed for ever, since a stored
#: stream is found by it.
_PAYOUTS: Final = UUID("6f1d3c52-0b3e-4b8e-9c8e-5a0c2f7d5480")


def payout_id_for(club_id: UUID, day: date) -> UUID:
    """The payout decided at the close of ``day`` for the club — one at most."""

    return uuid5(_PAYOUTS, f"{club_id}:{day.isoformat()}")


@dataclass(frozen=True, slots=True)
class Releasable:
    """What a club may be paid now: the games, and what they left it."""

    game_ids: tuple[UUID, ...]
    amount_grosze: int


def releasable(
    charges_of: Mapping[UUID, Sequence[SeatCharge]], *, over: Collection[UUID]
) -> Releasable | None:
    """What the club is owed of the games not yet paid out, ``charges_of``
    each one: every game **over** whose every share is **settled** — and
    ``None`` while that comes to nothing, or less."""

    games = tuple(
        sorted(
            game_id
            for game_id, charges in charges_of.items()
            if game_id in over and all(charge.settled for charge in charges)
        )
    )
    amount = sum(
        # Settled, so what is the club's of it is known (#641).
        invariant(charge.net_grosze, f"{charge.charge_id} settled, net unknown")
        for game in games
        for charge in charges_of[game]
    )
    if not games or amount <= 0:
        return None
    return Releasable(game_ids=games, amount_grosze=amount)


@dataclass
class ClubPayout:
    """One payout of a club's money, for the games it carries."""

    payout_id: UUID
    club_id: UUID
    account_id: str
    day: date
    amount_grosze: int
    game_ids: tuple[UUID, ...]
    decided_at: Instant
    #: The provider's payout, once it took it.
    provider_payout_id: str | None = None
    arrives_at: Instant | None = None
    sent_at: Instant | None = None
    version: int = 0
    _events: EventRecorder = field(
        default_factory=EventRecorder, init=False, repr=False, compare=False
    )

    @classmethod
    def decided(
        cls,
        *,
        club_id: UUID,
        account_id: str,
        day: date,
        owed: Releasable,
        at: Instant,
    ) -> "ClubPayout":
        invariant(owed.amount_grosze > 0, f"a payout of {owed.amount_grosze}")
        event = ClubPayoutDecided(
            payout_id=payout_id_for(club_id, day),
            club_id=club_id,
            account_id=account_id,
            day=day.isoformat(),
            amount_grosze=owed.amount_grosze,
            game_ids=owed.game_ids,
            occurred_at=at,
        )
        payout = cls._born(event)
        payout._events.record(event)
        return payout

    @classmethod
    def from_history(cls, events: Iterable[DomainEvent]) -> "ClubPayout":
        history = iter(events)
        opening = next(history)
        invariant(
            isinstance(opening, ClubPayoutDecided),
            f"a club payout stream opens {opening!r}",
        )
        assert isinstance(opening, ClubPayoutDecided)
        payout = cls._born(opening)
        for event in history:
            payout._apply(event)
        return payout

    @classmethod
    def _born(cls, opening: ClubPayoutDecided) -> "ClubPayout":
        return cls(
            payout_id=opening.payout_id,
            club_id=opening.club_id,
            account_id=opening.account_id,
            day=date.fromisoformat(opening.day),
            amount_grosze=opening.amount_grosze,
            game_ids=opening.game_ids,
            decided_at=instant(opening.occurred_at),
            version=1,
        )

    def pull_events(self) -> list[DomainEvent]:
        return self._events.pull()

    @property
    def is_sent(self) -> bool:
        return self.provider_payout_id is not None

    def sent(self, payout: Payout, *, at: Instant) -> bool:
        """The provider took it. Nothing is recorded for one already sent."""

        if self.is_sent:
            return False
        invariant(
            payout.amount_grosze == self.amount_grosze,
            f"{self.payout_id} sent as {payout.amount_grosze}",
        )
        event = ClubPayoutSent(
            payout_id=self.payout_id,
            club_id=self.club_id,
            provider_payout_id=payout.payout_id,
            arrives_at=payout.arrives_at,
            occurred_at=at,
        )
        self._apply(event)
        self._events.record(event)
        return True

    def _apply(self, event: DomainEvent) -> None:
        if isinstance(event, ClubPayoutSent):
            self.provider_payout_id = event.provider_payout_id
            self.arrives_at = instant(event.arrives_at)
            self.sent_at = instant(event.occurred_at)
        else:
            raise TypeError(f"Unsupported club payout event {event!r}")
        self.version += 1
