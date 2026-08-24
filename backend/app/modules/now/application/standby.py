"""Leaving standby: a write that asks nothing and hands Now its update.

ADR-0087's seventh act. It is a **write and not a route with a screen**, and
the ADR's argument is worth keeping in front of the code: a route exists to hold
a consequence, and this act has none. No seat, no money, no cascade, no outcome,
nothing to settle and — decisively — **no position to forfeit**, because the
model already refuses to show one.

**No confirmation and no warning**, for the same reason. A confirmation here
would imply a cost the model says does not exist, which is worse than a mis-tap:
a mis-tap is one tap to undo, and a false warning teaches a player that standby
is something she is giving up.

**No idempotency key.** ADR-0030's command log is for *destructive* commands,
and a repeated delete of a standby place a player no longer holds is the state
she asked for. The route is idempotent by its own nature, which is the case a
key exists to manufacture — so there is no log row, no replay branch and no
``applied`` field. What the departure route needs all three of, this needs none
of, and the difference is that leaving a match spends money.

**The answer is Now's update and nothing else.** There is no screen of its own
to return beside it (ADR-0074's shape is *its own screen's answer **and** Now's
update*, and here the first is empty), so the response is the update alone.

**It is the first act in the product that removes a card.** A queue place is the
whole of what puts that match on her strip, so leaving takes the card with it —
which is ADR-0070's *"the one-card answer must be able to say this card is no
longer on your screen"*, produced for the first time.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.application.ports import UnitOfWork
from app.kernel import Clock, Instant, instant

from app.modules.now.application.compose_enrolled import card_of
from app.modules.now.application.compose_now import stamp_at
from app.modules.now.domain.ports import EnrolledMatches, Standby
from app.modules.now.domain.screen import CardChanged, CardGone, NowUpdate


@dataclass(frozen=True)
class LeaveStandbyCommand:
    """*Take me off this match's queue.*

    Two fields and no third. There is no quote, because nothing is being
    exchanged; no version, because ADR-0074 refused one; and no key, because
    ADR-0030's log is for commands a replay could apply twice.
    """

    player_id: UUID
    match_id: UUID


class LeaveStandby:
    """Leave the queue, and hand Now back the one card that changed."""

    def __init__(
        self,
        *,
        enrolled: EnrolledMatches,
        standby: Standby,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._enrolled = enrolled
        self._standby = standby
        self._uow = uow
        self._clock = clock

    async def execute(self, command: LeaveStandbyCommand) -> NowUpdate:
        """Delete the place, then say what her screen should now hold.

        **The membership is not checked first**, unlike the departure route,
        and that is the acceptance criterion rather than an omission: *deleting
        a standby place the viewer does not hold returns what a success
        returns*. Anybody may queue for any match, so there is no membership to
        be a stranger to — the only 404 is a match id that names nothing, and
        the port raises it.
        """

        now = instant(self._clock.now())
        await self._standby.leave(
            match_id=command.match_id, player_id=command.player_id
        )
        await self._uow.commit()
        return await self._update(command, now=now)

    async def _update(self, command: LeaveStandbyCommand, *, now: Instant) -> NowUpdate:
        """The card as it now stands, or the fact that there is none.

        Read **after** the commit, on the departure route's rule: the answer has
        to describe the record as it stands rather than as the write left it in
        memory. A viewer who was only ever queued is now nothing to this match
        and her card is gone; a viewer who also holds a seat, a departure or a
        live claim keeps hers, recomposed — and the queue place she just dropped
        is the one thing about it that changed.
        """

        stamp = stamp_at(now)
        row = await self._enrolled.one(
            player_id=command.player_id, match_id=command.match_id, now=now
        )
        if row is None:
            return CardGone(match_id=command.match_id)
        return CardChanged(card=card_of(row, now=now, stamp=stamp))
