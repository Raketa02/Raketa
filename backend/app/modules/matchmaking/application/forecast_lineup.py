"""*What would this four leave on court* — the one route that records nothing.

``docs/adr/0108``. The builder lets a player compose a line-up the engine never
scored: tap a seat, swap whoever is in it, and the four on screen is one of
hundreds of combinations, none of them enumerated. The screen's whole claim is a
figure that moves when somebody moves, so at that moment there is a number to
produce and no route to produce it from.

**It is not a search, and that is a fact about it rather than a convenience.** No
candidates are generated, nothing is ranked, scored against the floor, withheld
or explained; there is no ``search_id``, no *Why 78?* and no Origin key.
``docs/adr/0104``'s rule binds **searches**, and re-`POST`ing ``/lineups`` per
swap would enter a six-edit builder session into *searches run* as six searches —
the same reasoning that makes ``POST /searches`` deliberately non-idempotent,
cutting the other way.

**It is bound to a search the caller ran.** Every player named must have appeared
in that search's returned rows. Unbounded, this route is a level-and-band lookup
for any player in the city, reachable by id, which is where the privacy line
spent everywhere else in this design would leak. Bounded, it is a small oracle:
four people the engine already decided to show you, with Levels the cards already
print.

**It re-verifies the fail-closed gates.** A player can hold a shortlist for an
hour and then ask about somebody who blocked them ten minutes ago, and a screen
predicting your evening with a named person is a surface that shows one player to
another (``docs/adr/0095``). A refusal answers exactly as an unknown citation
does, because naming the gate is the trace ADR-0130 says the other side never
sees.

**One implementation produces both figures.** A side with a seat still empty is
read as if the missing player matched the one already there, so *the provisional
figure becomes exactly the final figure the moment the seat fills* is a property
of :func:`~app.engines.matchfit.v1.group.arranged` rather than a hope about two
functions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from app.engines.matchfit.grouping import Arranged, Arrangement, Seated
from app.engines.matchfit.ruleset import Ruleset
from app.engines.matchfit.scoring import MatchFit
from app.engines.matchfit.v1 import arranged
from app.kernel import InvariantViolated, invariant
from app.modules.blocks.domain.ports import BlockQuery
from app.modules.matchmaking.application.commands import ForecastLineupCommand
from app.modules.matchmaking.application.outward_reads import (
    live_block_pairs,
    live_block_set,
    read_demand,
)
from app.modules.matchmaking.application.search_workbench import SearchWorkbench
from app.modules.matchmaking.domain.candidate_index import Partition
from app.modules.matchmaking.domain.candidate_snapshot import CandidateSource
from app.modules.matchmaking.domain.errors import (
    MatchmakingUnavailable,
    SearchNotFound,
)
from app.modules.matchmaking.domain.fence import (
    combine_group_sigma,
    searcher_from,
    seatable_of,
)
from app.modules.matchmaking.domain.lineups import (
    LineupSeat,
    guests_for,
    roster,
    seats_per_side,
)
from app.modules.matchmaking.domain.ports import AccountHoldQuery
from app.modules.matchmaking.domain.search_context import SearcherFacts
from app.modules.matchmaking.domain.search_store import SearchStore


def _uncited() -> SearchNotFound:
    """**One refusal, one sentence, for every way this route says no.**

    The search does not exist, it belongs to somebody else, it was for another
    sport, it never showed one of these people, one of them is under a hold or
    blocked, or two of them are blocked from each other. Six causes and one
    answer, written once here so that no branch can accidentally become more
    specific than the others: telling them apart would answer *does this id
    exist* and *was this person shown to somebody* for a stranger's id, one probe
    at a time, and naming a block is the trace ``docs/adr/0095`` promises the
    other side never sees.
    """

    return SearchNotFound("no search of yours showed all of those players")


@final
@dataclass(frozen=True, slots=True)
class ForecastAnswer:
    """Every way round the composed line-up can sit, each with a forecast.

    **No ``search_id`` and no rows**, because nothing was searched and nothing
    was recorded. What does cross is the pair of version stamps: a forecast with
    no stamp is a number nobody can reproduce, which is the defect
    ``docs/adr/0104`` exists to prevent — arriving through the one route with no
    record to reproduce it from.
    """

    arrangements: tuple[tuple[Arranged, tuple[LineupSeat, ...]], ...]
    #: The arrangement matching the seat order the client sent — what the builder
    #: is currently drawing.
    current: Arranged
    #: The min-gap arrangement. **What *Even it out* selects.**
    evenest: Arranged
    engine_version: str
    ruleset_version: str


@final
class ForecastLineup:
    """The forecast, end to end. **It holds no store it could write to.**"""

    def __init__(
        self,
        *,
        workbench: SearchWorkbench,
        ruleset: Ruleset,
        engine: MatchFit,
        searches: SearchStore,
        candidates: CandidateSource,
        blocks: BlockQuery,
        holds: AccountHoldQuery,
    ) -> None:
        self._work = workbench
        self._ruleset = ruleset
        self._engine = engine
        self._searches = searches
        self._candidates = candidates
        self._blocks = blocks
        self._holds = holds

    async def execute(self, command: ForecastLineupCommand) -> ForecastAnswer:
        invariant(bool(command.players), "a forecast about an empty court")
        await self._refuse_an_uncited_four(command)
        searcher = await self._work.searcher_facts(
            player_id=command.searcher_id,
            sport=command.sport,
            mode_of=lambda _: command.mode,
        )
        await self._work.refuse_a_held_searcher(searcher.player_id)
        await self._refuse_a_gated_four(command)
        seated = self._seated(command, searcher)
        try:
            return self._forecast(command, searcher, seated)
        except InvariantViolated as broken:
            raise MatchmakingUnavailable(
                f"the matcher refused to forecast: {broken}"
            ) from broken

    # -- the bound -----------------------------------------------------------

    async def _refuse_an_uncited_four(
        self, command: ForecastLineupCommand
    ) -> None:
        """``docs/adr/0108`` §3's bound: **every seat came off that search.**

        Four ways this refuses and they are one code, exactly as the rung
        citation's are: the search does not exist, it belongs to somebody else,
        it was for another sport, or it never showed one of these people.
        Separating them would answer *does this ``search_id`` exist* for a
        stranger's id, and *was this person in somebody's shortlist* for a
        stranger's id, which are the two questions the read-back's own 404
        already declines.
        """

        cited = await self._searches.find(
            search_id=command.search_id, searcher_id=command.searcher_id
        )
        shown = (
            frozenset()
            if cited is None or cited.sport is not command.sport
            else frozenset(row.player_id for row in cited.returned)
        )
        if not all(player_id in shown for player_id in command.players):
            raise _uncited()

    async def _refuse_a_gated_four(self, command: ForecastLineupCommand) -> None:
        """Blocks and holds, **live**, over the searcher and the four together.

        Three reads, all fail-closed, and any of them refuses the **whole**
        forecast rather than dropping a seat: a gate that cannot be evaluated
        excludes, and a forecast about three of the four people asked about would
        answer a question nobody put.

        It refuses under the citation's own code and names nothing. Saying *this
        one is blocked* is the trace ``docs/adr/0095`` promises the other side
        never sees, and a screen is the last place it may appear.
        """

        held = await read_demand(
            AccountHoldQuery,
            lambda: self._holds.held_among(list(command.players)),
        )
        blocked = await live_block_set(self._blocks, command.searcher_id)
        between = await live_block_pairs(self._blocks, command.players)
        gated = any(
            player_id in held or player_id in blocked
            for player_id in command.players
        )
        if gated or between:
            raise _uncited()

    # -- the arithmetic ------------------------------------------------------

    def _seated(
        self, command: ForecastLineupCommand, searcher: SearcherFacts
    ) -> tuple[Seated, ...]:
        """The composed seats, fenced, **in the order the client sent them.**

        Their Levels are read from the index rather than off the cited search's
        recorded cards, and the difference matters: the record keeps what was
        *shown*, which is right for a read-back and wrong here, because a
        forecast is a claim about the game these four would play tonight.

        ``fit`` is zero on every seat and nothing reads it. A forecast weighs two
        side strengths and a spread; the objective is what reads a Fit, and the
        objective is not run here — nothing was compared to anything.
        """

        snapshot = self._candidates.snapshot(Partition.for_sport(command.sport))
        rows = {row.player_id: row for row in snapshot.rows}
        seated = []
        for player_id in command.players:
            row = rows.get(str(player_id))
            if row is None:
                raise _uncited()
            seated.append(
                Seated(
                    candidate=seatable_of(row, searcher=searcher),
                    fit=0.0,
                    locked=True,
                )
            )
        return tuple(seated)

    def _forecast(
        self,
        command: ForecastLineupCommand,
        facts: SearcherFacts,
        seated: tuple[Seated, ...],
    ) -> ForecastAnswer:
        """The arrangements, in the order the seats were sent.

        ``Arrangement.all_of`` puts the first player sent in the partner seat, so
        the **first** arrangement is the one the builder is drawing — which is
        what ``is_current`` means, and why the order the client sends its seats
        in is part of the ask rather than incidental.
        """

        searcher = searcher_from(facts, self._work.clock.now())
        per_side = seats_per_side(command.sport)
        ways = tuple(
            arranged(
                searcher,
                one,
                self._ruleset,
                combine_group_sigma,
                seats_per_side=per_side,
            )
            for one in Arrangement.all_of(seated)
        )
        invariant(bool(ways), "a forecast about a court with nobody on it")
        guests = guests_for(command.sport)
        searcher_id = str(command.searcher_id)
        return ForecastAnswer(
            arrangements=tuple(
                (
                    one,
                    roster(
                        one.arrangement,
                        searcher_id=searcher_id,
                        guests=guests,
                        # An open seat here is the **searcher's own**, not a pool
                        # that ran out: nobody looked for anybody, so the line-up
                        # vocabulary does not apply and the forecast says what
                        # happened by being provisional.
                        reason=None,
                    ),
                )
                for one in ways
            ),
            current=ways[0],
            evenest=min(
                ways, key=lambda one: (one.side_gap, one.arrangement.partner_id)
            ),
            engine_version=self._engine.version,
            ruleset_version=self._ruleset.version,
        )


__all__ = ["ForecastAnswer", "ForecastLineup"]
