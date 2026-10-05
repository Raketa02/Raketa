"""**The club is paid after the game is played** (#548; the mechanics §12.6,
§16.11, §16.12; the screens B7, B9).

Two things a club has of its payouts:

- **the decision**, the payouts job's (``club-payouts``): at the close of every
  club day, everything a club's games over by then left it — played, or called
  off with what that gives back decided, and nothing about their money still on
  its way — and that no payout carried yet, is decided as one payout
  (``domain/club_payout.py``). **The money moves after the commit, from the
  outbox** (``handlers/send_club_payouts.py``), as a refund's does: the provider
  is never asked from here;
- **the list**, the Money page's: the payouts on the club's account, as the
  provider says they stand.

**Safe beside itself with no lock**: a club day's payout is one stream, a game
is carried once, and whatever another process reached first is counted and
stepped over.
"""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass
from datetime import date
from typing import final
from uuid import UUID

from app.application.events import EventStreamVersionConflict
from app.application.ports import UnitOfWork
from app.kernel import Clock, Instant, instant, invariant
from app.modules.clubs.domain.court_hours import day_closes_at, last_closed_day
from app.modules.payments.domain.club_payout import (
    ClubPayout,
    payout_id_for,
    releasable,
)
from app.modules.payments.domain.ports import (
    ClubPayoutRepository,
    GamesOver,
    SeatChargeRepository,
    Sellers,
)
from app.modules.payments.domain.provider import PaymentProvider, Payout


@final
@dataclass(frozen=True, slots=True)
class PayoutsDecided:
    """How many payouts one run decided, and how many another process reached
    first."""

    decided: int
    conflicts: int


@final
class DecideClubPayouts:
    def __init__(
        self,
        *,
        payouts: ClubPayoutRepository,
        charges: SeatChargeRepository,
        games: GamesOver,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._payouts = payouts
        self._charges = charges
        self._games = games
        self._uow = uow
        self._clock = clock

    async def execute(self) -> PayoutsDecided:
        now = instant(self._clock.now())
        day = last_closed_day(now)
        decided = conflicts = 0
        # The games of every day closed by now: the day a payout is for is
        # the one whose close decided it, and a game of a day still open
        # waits for that day's close.
        owed = await self._payouts.owed(starting_before=day_closes_at(day))
        for club_id in sorted(owed):
            try:
                if await self._decide(club_id, owed[club_id], day=day, now=now):
                    await self._uow.commit()
                    decided += 1
                else:
                    await self._uow.rollback()
            except EventStreamVersionConflict:
                await self._uow.rollback()
                conflicts += 1
        return PayoutsDecided(decided=decided, conflicts=conflicts)

    async def _decide(
        self, club_id: UUID, games: Collection[UUID], *, day: date, now: Instant
    ) -> bool:
        if await self._payouts.load(payout_id_for(club_id, day)) is not None:
            # Paid for this day already: the rest waits for the next close.
            return False
        over = await self._games.over(games, at=now)
        charges_of = {game: await self._charges.of_game(game) for game in sorted(over)}
        owed = releasable(charges_of, over=over)
        if owed is None:
            return False
        # The money is where the shares were taken: the club's one account.
        accounts = {
            charge.account_id for game in owed.game_ids for charge in charges_of[game]
        }
        invariant(len(accounts) == 1, f"{club_id}'s games paid on {accounts}")
        await self._payouts.save(
            ClubPayout.decided(
                club_id=club_id, account_id=accounts.pop(), day=day, owed=owed, at=now
            )
        )
        return True


@final
class ReadClubPayouts:
    """The payouts on a club's account, newest first, as the provider says they
    stand — the Money page's list. A club with no account has none."""

    def __init__(self, *, sellers: Sellers, provider: PaymentProvider) -> None:
        self._sellers = sellers
        self._provider = provider

    async def execute(self, club_id: UUID, *, limit: int) -> tuple[Payout, ...]:
        seller = (await self._sellers.of([club_id])).get(club_id)
        if seller is None or seller.account_id is None:
            return ()
        return await self._provider.payouts(seller.account_id, limit=limit)
