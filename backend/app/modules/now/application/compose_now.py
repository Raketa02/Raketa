"""One request returns the whole screen.

**One read per compose.** The clock is read once and every stamp on the answer
comes from that one reading, which is what makes a compose a single statement
about a single instant rather than three regions that half-disagree.

**This ships the route with the regions empty**, and that is deliberate rather
than unfinished: it unblocks the client against a *compiled* contract, and every
later ticket fills a region without touching the envelope. What is real here and
not a placeholder is the shape of the answer, the resolution of ``all``, and the
stamps.

**Every ask pays the full funnel.** There is no player feed cache — it was the
answer to a load shape that no longer exists, and it is the only place on this
screen that could serve a stale answer to a direct question.
"""

from __future__ import annotations

from app.kernel import Clock, Instant, Sport

from app.modules.now.application.commands import ComposeNowQuery
from app.modules.now.domain.ports import RatedSports
from app.modules.now.domain.screen import (
    EnrolledRegion,
    NowScreen,
    OffersRegion,
    ShelvesRegion,
    Stamp,
)

#: Milliseconds, which is enough resolution that two composes a player could tell
#: apart never tie, and coarse enough to stay a comfortable integer in every
#: client's number type. A millisecond epoch reads as ``1 771 200 000 000`` — well
#: inside the 2^53 a JavaScript number holds exactly, and it stays inside it for
#: the next two hundred and fifty thousand years.
_MILLISECONDS = 1000


def stamp_at(moment: Instant) -> Stamp:
    """The stamp a compose or an update made at this instant carries.

    Derived from **when the answer was composed**, not from the record's version,
    and that is the choice the race turns on. The scenario the stamps exist for is
    a pull and a tap racing: a compose composed *before* the action, landing
    *after* it. Two record versions cannot order those two answers — the compose
    read the same version the action was about to bump — where the composition
    instant orders them exactly.

    It also survives the case a version cannot see at all: a card whose situation
    changed because a threshold passed and nobody wrote anything. The ladder is a
    function of the record *and the clock*, so a stamp that ignores the clock
    would let a genuinely newer card be rejected as stale.
    """

    return int(moment.timestamp() * _MILLISECONDS)


class ComposeNow:
    """Compose the whole of Now for one viewer, at one instant."""

    def __init__(self, *, rated_sports: RatedSports, clock: Clock) -> None:
        self._rated_sports = rated_sports
        self._clock = clock

    async def execute(self, query: ComposeNowQuery) -> NowScreen:
        now = self._clock.now()
        stamp = stamp_at(now)
        sports = await self._resolve(query)

        return NowScreen(
            offers=OffersRegion(stamp=stamp),
            your_matches=EnrolledRegion(stamp=stamp),
            shelves=ShelvesRegion(stamp=stamp),
            sports=sports,
            # Money is not modelled yet, so nothing can owe anything and the line
            # is absent rather than present at zero. When the ledger lands, the
            # only change here is where the amount comes from — the *shape* of a
            # player who owes nothing is already correct.
            debt=None,
        )

    async def _resolve(self, query: ComposeNowQuery) -> frozenset[Sport]:
        """What the filter names, in sports.

        ``all`` is **the sports the player holds a rating at** and not the four
        the registry knows: a shelf called *Best fit for you* that ranks squash
        matches for somebody who has never held a racket is a claim about
        inventory wearing the words of a claim about her.

        A named sport resolves to itself whether or not she is rated at it. That
        is not an oversight — tapping a chip for a sport she has no rating at is
        the moment the app owes her a door into that questionnaire, and a filter
        that quietly resolved to nothing would make the door indistinguishable
        from an empty city.
        """

        one = query.sport.sport
        if one is not None:
            return frozenset({one})
        return await self._rated_sports.for_player(query.player_id)
