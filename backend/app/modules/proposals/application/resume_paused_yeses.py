"""**A paused week comes back** (#544; the mechanics §6.6, §19: *your games per
week are booked — your other yeses that week pause; they come back if a game is
called off*).

A booking that filled a player's week paused their other yeses in it
(``fill.py``). When a booked game of theirs stops being theirs — called off at
its cut-off, or left — their week has room again, and each yes it paused counts
once more, soonest first, while the week has room: **the yes they said, not a
new one**. One that comes back as the last seat a game needed **fills it**,
exactly as the yes did when it was said — everybody charged together or nobody
— since that is what the yes was: *if everybody is in, book it and charge my
share*.

**A yes that cannot come back stays paused**, saying nothing: its game filled
without them while it was paused, or ended; the player booked another game at
its hour; their week is full again; or they could no longer be In — gone from
the pool, no method to charge, somebody In they no longer fit. They are free to
say it again from the card.

**Told, from the outbox**, in the transaction that delivers the booking's
``SeatLeft`` or ``CalledOffAtCutOff``, each paused game read locked — a fill on
one that loses its court to another game meets ``CourtJustTaken``, and the
delivery is tried again. **No commit**: the delivery's transaction is the
boundary.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.kernel import Instant
from app.modules.proposals.application.fill import Fill
from app.modules.proposals.application.guards import Guards
from app.modules.proposals.domain.deck import hour_taken, week_of, week_window
from app.modules.proposals.domain.errors import NoLongerFits, PaymentMethodRequired
from app.modules.proposals.domain.ports import (
    BookedGames,
    GamesAndMoneyRepository,
    ProposalDirectory,
    ProposalRepository,
)


@final
class ResumePausedYeses:
    def __init__(
        self,
        *,
        proposals: ProposalRepository,
        directory: ProposalDirectory,
        games_and_money: GamesAndMoneyRepository,
        booked: BookedGames,
        guards: Guards,
        fill: Fill,
    ) -> None:
        self._proposals = proposals
        self._directory = directory
        self._games_and_money = games_and_money
        self._booked = booked
        self._guards = guards
        self._fill = fill

    async def execute(self, player_id: UUID, *, at: Instant) -> int:
        """Bring back every paused yes of this player their week has room for.
        Answers how many came back."""

        settings = await self._games_and_money.load(player_id)
        resumed = 0
        for proposal_id in await self._directory.paused_for(player_id, now=at):
            proposal = await self._proposals.load_for_update(proposal_id)
            if proposal is None or player_id not in proposal.paused:
                continue
            start, end = week_window([week_of(proposal.start)])
            booked = await self._booked.starts_of(player_id, start=start, end=end)
            if len(booked) >= settings.games_per_week or hour_taken(
                proposal.start, booked
            ):
                continue
            try:
                if not await self._guards.in_the_pool(proposal.pool, [player_id]):
                    continue
                await self._guards.refuse_an_unchargeable_yes(player_id)
                await self._guards.refuse_a_yes_that_does_not_fit(
                    player_id, proposal, at=at
                )
                await self._guards.refuse_a_yes_the_post_is_not_for(player_id, proposal)
            except (PaymentMethodRequired, NoLongerFits):
                # They can no longer be In; an unavailability, unlike these,
                # fails the delivery, which is tried again.
                continue
            if not proposal.resume_yes(player_id, at=at):
                continue
            if proposal.open_seats == 0:
                await self._fill.run(proposal, now=at)
            await self._proposals.save(proposal)
            resumed += 1
        return resumed
