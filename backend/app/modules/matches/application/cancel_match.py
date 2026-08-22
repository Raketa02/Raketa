"""End a match, and say which of the four stories it was.

**One command, four announcements, and that is the point.** ADR-0034 keeps four
cancellation flags rather than one because *"they are four different stories and
the player deserves to know which one happened"* — and that is also why Matches
can keep no history at all: *why did this match cancel* is answered by the record
itself. Collapsing them into a single ``MatchCancelled`` carrying a reason string
would be the generic event the same decision forbids, wearing an enum.

Two of the four are **receipts** rather than decisions (``INCOMPLETE``,
``CHECKPOINT``): the situation already derives from the clock and the record, and
the flag records only that the refund, the court release and the notice
completed. So a downed timekeeper delays the money and never the truth.
"""

from __future__ import annotations

from app.application.ports import UnitOfWork
from app.kernel import Clock, Instant, exhaustive, instant

from app.modules.matches.application.commands import (
    CancellationCause,
    CancelMatchCommand,
)
from app.modules.matches.domain.errors import MatchNotFound
from app.modules.matches.domain.match import Match
from app.modules.matches.domain.ports import MatchRepository


def _record_the_cancellation(
    cause: CancellationCause, *, on: Match, at: Instant
) -> None:
    """Fan the one command out to the four aggregate writes it can be.

    ``exhaustive`` in the tail is what makes a fifth cause a **type** error
    rather than a silent no-op: a match that ended for a reason nobody wrote a
    branch for would be a match that quietly stayed open.
    """

    match cause:
        case CancellationCause.CLUB:
            on.cancel_by_club(at=at)
        case CancellationCause.WEATHER:
            on.cancel_for_weather(at=at)
        case CancellationCause.INCOMPLETE:
            on.settle_incomplete_cancellation(at=at)
        case CancellationCause.CHECKPOINT:
            on.settle_checkpoint_cancellation(at=at)
        case _:  # pragma: no cover - `exhaustive` never returns
            exhaustive(cause)


class CancelMatch:
    def __init__(
        self, matches: MatchRepository, uow: UnitOfWork, clock: Clock
    ) -> None:
        self._matches = matches
        self._uow = uow
        self._clock = clock

    async def execute(self, command: CancelMatchCommand) -> Match:
        match = await self._matches.get(command.match_id)
        if match is None:
            raise MatchNotFound()

        _record_the_cancellation(
            command.cause, on=match, at=instant(self._clock.now())
        )
        stored = await self._matches.save(match)
        await self._uow.commit()
        return stored
