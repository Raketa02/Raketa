"""``Departures`` over the Matches aggregate and the hold ladder.

The one file in Now that knows a departure is a seat vacated on a ``Match``,
that it leaves a ``Vacancy`` beside a ``Departure``, and that a match losing a
paid seat may fall out of a hold tier and give a court back. Everything above it
asks in Now's words and is told the outcome she was quoted at.

**It composes the existing write rather than reassembling it.** ``Match.depart``
already refuses everything that has to be refused — a started match, a terminal
one, ADR-0046's lock, a seat she does not hold, a quote the live outcome has
fallen below — and ``ResolveCourtHold`` is already the only thing allowed to
move ``held_since``. A second implementation of either here would be a second
answer to a question that already has one. This is the shape
``money.SeatsThroughMatches`` takes over the same aggregate, for the same reason:
the port belongs to the context that needs the answer, and the adapter beside it
is the one place that knows whose question it really is.

**It does not commit**, and the ticket rests on that: the seat, the vacancy, the
departure, the hold ladder's answer, every outbox row *and* ADR-0030's
command-log row close together or they do not close at all. A log that could
disagree with the write it describes is the one state that makes a replay
dangerous rather than merely useless.

**It reaches ``matches`` and ``matches`` never reaches back.** Now reads five
contexts and writes to none of its own; this is the first write it drives, and
it is driven through another context's aggregate rather than an aggregate of
Now's. The direction is the same one every other adapter in this package points.
"""

from __future__ import annotations

from uuid import UUID

from app.kernel import Instant, Outcome

from app.modules.matches.application.resolve_court_hold import ResolveCourtHold
from app.modules.matches.domain.errors import MatchNotFound
from app.modules.matches.domain.ports import MatchRepository


class DeparturesThroughMatches:
    """A seat vacated, the hole it leaves, and the court that may follow it."""

    def __init__(self, *, matches: MatchRepository, holds: ResolveCourtHold) -> None:
        self._matches = matches
        self._holds = holds

    async def depart(
        self, *, match_id: UUID, player_id: UUID, quote: Outcome, at: Instant
    ) -> Outcome:
        match = await self._matches.get(match_id)
        if match is None:
            raise MatchNotFound()

        departure = match.depart(player_id, quote=quote, at=at)

        # Before the save and in the same transaction, like every other Matches
        # write: a departure *leaves* a tier, so this is the ask that gives a
        # court back rather than leaving one held for a match that no longer
        # earns it.
        await self._holds.apply(match, at=at)
        await self._matches.save(match)

        # The aggregate's own recomputed outcome, which is what she was actually
        # quoted at — equal or better than the label that crossed the wire, and
        # the value a replay has to hand back.
        return departure.quoted
