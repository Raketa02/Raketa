"""One request returns the whole screen.

**One read per compose.** The clock is read once and every stamp on the answer
comes from that one reading, which is what makes a compose a single statement
about a single instant rather than three regions that half-disagree.

**Regions are filled one ticket at a time and the envelope never moves.** The
route shipped with all three empty so the client could compile against it; what
is real here today is the shape of the answer, the resolution of ``all``, the
stamps, **the enrolled strip**, **the ranked shelves** and **shelves 4 and 5**.
The offers region is the cascade's (``Raketa02/Raketa#83``).

**The shelves are emitted in the server's fixed order** and nothing about that
order is a fact about the viewer: the ranked pair first, then the two arrival
shelves, with the door taking the ranked pair's position when she holds no
rating at the sport she named. ADR-0070 put shelf presence and shelf order on the
server precisely so both can move without a client release.

**Every ask pays the full funnel.** There is no player feed cache — it was the
answer to a load shape that no longer exists, and it is the only place on this
screen that could serve a stale answer to a direct question.

**A sport the viewer holds no rating at is a door and never an empty screen.**
It is composed here, into the shelves list, in the position the ranked shelves
would occupy — never inferred by the phone from what is missing, which would
fire wrongly on any day the city genuinely has nothing in a sport she is rated
at (ADR-0084).
"""

from __future__ import annotations

from app.kernel import Clock, Instant, Sport

from app.modules.now.application.commands import ComposeNowQuery
from app.modules.now.application.compose_enrolled import ComposeEnrolled
from app.modules.now.application.compose_shelves import ComposeShelves
from app.modules.now.application.new_arrivals import ComposeNewArrivals
from app.modules.now.domain.ports import ParkedRuns, RatedSports
from app.modules.now.domain.screen import (
    Block,
    Door,
    NowScreen,
    OffersRegion,
    ShelvesRegion,
    Stamp,
)
from app.modules.now.domain.vocabulary import DoorCode

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

    def __init__(
        self,
        *,
        rated_sports: RatedSports,
        parked_runs: ParkedRuns,
        new_arrivals: ComposeNewArrivals,
        shelves: ComposeShelves,
        enrolled: ComposeEnrolled,
        clock: Clock,
    ) -> None:
        self._rated_sports = rated_sports
        self._parked_runs = parked_runs
        self._new_arrivals = new_arrivals
        self._shelves = shelves
        self._enrolled = enrolled
        self._clock = clock

    async def execute(self, query: ComposeNowQuery) -> NowScreen:
        now = self._clock.now()
        stamp = stamp_at(now)
        sports = await self._resolve(query)
        door = await self._door(query)

        return NowScreen(
            offers=OffersRegion(stamp=stamp),
            your_matches=await self._enrolled.compose(
                viewer=query.player_id,
                # The **named chip**, not the resolved set. ADR-0084 filters the
                # strip along with the shelves and `all` hides nothing; passing
                # `sports` here would hide a match she has paid for the moment
                # she is unrated at its sport.
                sport=query.sport.sport,
                now=now,
                stamp=stamp,
            ),
            shelves=ShelvesRegion(
                stamp=stamp,
                shelves=await self._blocks(
                    query=query, sports=sports, now=now, stamp=stamp, door=door
                ),
            ),
            sports=sports,
            # The ledger is modelled and this line still has no composer, which
            # is a gap named rather than filled: the debt line's own ticket is
            # `Raketa02/Raketa#92`, and composing it here would be writing the
            # answer that ticket exists to decide — in particular *blocked* is a
            # server boolean about acts nothing in v1 can yet refuse. The
            # *shape* of a player who owes nothing is already correct, so the
            # day it lands the change is where the amount comes from.
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

    async def _door(self, query: ComposeNowQuery) -> Door | None:
        """The way into a questionnaire, when the filter names a sport she lacks.

        **Only a named chip can produce one.** ``all`` is *the sports she holds a
        rating at*, so it names no sport she is unrated at and there is nothing
        for a door to be about — including for a player holding no rating at all,
        whose screen is empty because her city is not the subject. ADR-0084 puts
        her in the run itself rather than on Now.

        The rating is asked **at the one sport**, not as the set: a named chip is
        the busiest path on the sport bar, and it should not pay a replay of
        every rating she holds to learn whether she holds this one.

        The parked-run read happens **only when a door is being drawn**. A player
        rated at the sport is answered and gone before the second read exists,
        which is why the two are sequential here rather than gathered.
        """

        sport = query.sport.sport
        if sport is None:
            return None
        if await self._rated_sports.holds(player_id=query.player_id, sport=sport):
            return None

        parked = await self._parked_runs.parked_at(
            player_id=query.player_id, sport=sport
        )
        return Door(code=DoorCode.RUN_PARKED if parked else DoorCode.NO_RUN_YET)

    async def _blocks(
        self,
        *,
        query: ComposeNowQuery,
        sports: frozenset[Sport],
        now: Instant,
        stamp: Stamp,
        door: Door | None,
    ) -> tuple[Block, ...]:
        """The server's fixed order: the ranked pair, then the two arrival shelves.

        **The door takes the ranked shelves' position rather than sitting above
        them**, and that is the distinction that matters now they exist: a door
        means *Best fit for you* / *Same level* and *Full, but worth waiting for*
        are **absent**, not empty and not beneath it — a player with no rating at
        squash cannot be ranked against squash matches, so there is nothing for
        them to hold. The door and the ranked pair are therefore alternatives and
        never neighbours, which is what makes composing the ranked pair
        unconditional here safe: ``ComposeShelves`` answers nothing at all for a
        sport she cannot be ranked at, so the two can never both appear.

        *New on Raketa* and *New clubs* compose either way, and under a door that
        is the point rather than a leftover: the clubs are the argument for
        spending the two minutes, so they belong under the ask.

        **Composition's own passes — the repeat guard and emphasis — are not
        here.** Both read across shelves rather than within one, so they run over
        this list once it exists (``Raketa02/Raketa#77``), which is the same
        argument ADR-0032 makes for order and ADR-0037 for emphasis.
        """

        ranked = await self._shelves.compose(
            viewer=query.player_id, sports=sports, now=now, stamp=stamp
        )
        arrivals = await self._new_arrivals.compose(
            viewer=query.player_id,
            sports=sports,
            now=now,
            stamp=stamp,
            # Nobody stores a player's city (#102, ADR-0063), so every compose
            # files under the unknown one. It is threaded rather than invented
            # downstream so that the day the fact has a source, this line is the
            # whole change.
            city=None,
        )
        if door is not None:
            return (door, *arrivals)
        return (*ranked, *arrivals)
