"""``StandbyPlaces``, ``Standby`` and ``StandbyQueue`` over the queue Matches owns.

One class for all three of Now's standby ports, because they are one question
asked in three directions — *what is she queued for*, *who asked about this
match*, and *take her off this one* — and the file that knows a standby place is
a row in the Matches context should be one file. They stay three **ports**
because their readers differ: ``ComposeShelves`` takes the viewer's read alone,
the cascade takes the match's, and a composer holding an object that can delete
a player's queue place is a composer one autocomplete away from doing it.

**This file used to be ``NoStandbyPlaces``**, which answered the empty set for
everybody and said so: *"standby has no store anywhere in the product… so the
honest answer today is the empty set, for every player, always."* It also said
what would change when the store landed — *"one line in the composition root"* —
and that turned out to be exactly right. The rule above it,
``NotOnStandby``, has been written, evaluated and tested the whole time; what
was missing was a table.

**Nothing here refuses anything except an address.** ADR-0087 gives leaving
standby no confirmation, no warning and no key, because nothing is lost: a
repeated delete of a place she no longer holds is the state she asked for. The
one thing that can be wrong is the match id, and that is a 404 about the address
rather than a refusal of the act.
"""

from __future__ import annotations

from uuid import UUID

from app.modules.matches.domain.errors import MatchNotFound
from app.modules.matches.domain.ports import MatchRepository, StandbyPlaces


class StandbyThroughMatches:
    """The queue, read for a screen and written for one tap."""

    def __init__(
        self, *, matches: MatchRepository, standby: StandbyPlaces
    ) -> None:
        self._matches = matches
        self._standby = standby

    async def for_player(self, player_id: UUID) -> frozenset[UUID]:
        """Every match she asked to be told about."""

        return await self._standby.held_by(player_id)

    async def queued_for(self, match_id: UUID) -> frozenset[UUID]:
        """Who asked about this match — **rung 1 of the invitation ladder.**

        Passed straight through, like ``for_player``: the composite key answers
        it off its own left edge, and there is no rule here for the adapter to
        apply. Which of these people the cascade actually tells is
        ``domain/cascade.py``'s, and this does not know a rung exists.
        """

        return await self._standby.queued_for(match_id)

    async def leave(self, *, match_id: UUID, player_id: UUID) -> None:
        """Take her off, after checking there is a match to be off.

        The match is loaded **only** to turn an unknown id into a 404. Nothing
        about the aggregate decides whether a queue place may be removed —
        ADR-0087's *"nothing is lost"* means there is nothing for it to decide —
        so this does not reach ``Match`` for a rule the way ``Departures``
        reaches ``Match.depart`` for five.
        """

        if await self._matches.get(match_id) is None:
            raise MatchNotFound()
        await self._standby.leave(match_id=match_id, player_id=player_id)
