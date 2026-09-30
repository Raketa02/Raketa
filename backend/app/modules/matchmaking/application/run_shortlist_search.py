"""*Find me a game* — one tap, one search, and the record written before the answer.

**The order of the four things this use case does is load-bearing.**

1. It reads the **searcher's own facts** from the aggregates. Never from the
   index, whose copy may lag, and never from the request, which would be a gate
   evaluated on a lie.
2. It binds one **immutable snapshot** and every live gate fact into a
   ``SearchContext``. After this line nothing else is read, so a refresh cannot
   move the index underneath a running search.
3. It runs the **pipeline**, which is pure over that context.
4. It writes the **record and commits it, before the response returns**. If that
   fails, the search fails: the ``search_id`` *is* the answer's identity
   (``docs/adr/0104``), and a shortlist returned without its row is a permanently
   missing row of the denominator this engine is judged by.

**Steps 1, 2 and most of 4 are ``search_workbench.py``'s**, because a deal does
them identically and two implementations of *bind a search context* would be two
answers to which reads fail closed. **What is here is the shortlist's own**: the
mode it takes from the request, the ladder, the prompts and the order.

**Never a fallback list.** When the engine raises, the feature is down and this
use case says so. A hand-rolled backend ranker arriving as a hotfix is how a
second, worse, unexplainable ranking implementation enters the system for ever.

**An empty shortlist is an answer.** It is recorded exactly like any other search
with ``n_returned = 0``, returned as a `200`, and the pool it came from is
described on every search rather than only on the empty ones — because a thin
pool and a broken floor are indistinguishable without that description.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, replace
from typing import final
from uuid import UUID

from app.engines.matchfit.ruleset import Ruleset
from app.engines.matchfit.scoring import MatchFit
from app.kernel import InvariantViolated, Sport
from app.modules.matchmaking.application.commands import RunShortlistSearchCommand
from app.modules.matchmaking.application.search_workbench import (
    AskedFor,
    SearchWorkbench,
)
from app.modules.matchmaking.domain.declines import (
    PromptDeclineLedger,
    silence_began,
    suppresses,
)
from app.modules.matchmaking.domain.errors import (
    MatchmakingUnavailable,
)
from app.modules.matchmaking.domain.search_context import (
    SearchContext,
)
from app.modules.matchmaking.domain.prompts import (
    REPEATED_WIDENINGS,
    Prompt,
    PromptLedger,
    RaisedPrompt,
    improvised_week,
)
from app.modules.matchmaking.domain.relaxation import (
    Rung,
    radius_ladder,
)
from app.modules.matchmaking.domain.search_store import SearchStore
from app.modules.matchmaking.domain.searches import (
    PoolDescription,
    SearchInitiation,
    SearchRecord,
    SearchSurface,
    SortOption,
    StagedCounts,
)
from app.modules.matchmaking.domain.shortlist import (
    Shortlist,
    run,
)
from app.modules.matchmaking.domain.sorting import of_scored, sorts_available
from app.modules.matchmaking.domain.widening import (
    Ladder,
    ladder_for,
    nothing_priced,
)
from app.modules.player_profile.domain.weekly_hours import (
    WeeklyHours,
    window_of,
)
from app.shared.ids import new_uuid


logger = logging.getLogger(__name__)


@final
@dataclass(frozen=True, slots=True)
class ShortlistAnswer:
    """What the route renders: **the record, and the honest sort list.**

    There is deliberately no second copy of the rows. The record is the answer's
    identity (``docs/adr/0104``), so rendering anything else would be rendering
    something the read-back an hour later could not reproduce — and the two
    routes would drift the way two serialisers of one shape always do. The
    renderer reads ``record.returned``, which is the one way a candidate leaves a
    record at all.

    ``sorts_available`` is beside it rather than on it because it is not a fact
    about the search: it is a statement about *these rows*, recomputed over
    whatever the reader is actually shown, and a read-back that withheld half the
    list must not go on offering a control that would now reorder nothing.
    """

    record: SearchRecord
    sorts_available: tuple[SortOption, ...]
    #: The questions this search raises and does not answer. Beside the record
    #: rather than on it for the same reason as the sorts: a prompt is a fact
    #: about *now* — the grid you improvised a moment ago, the widening you keep
    #: taking, the drift a loop noticed yesterday — and a read-back a month later
    #: must not re-ask a question whose answer has since been given.
    prompts: tuple[RaisedPrompt, ...] = ()


@final
class RunShortlistSearch:
    """The shortlist, end to end."""

    def __init__(
        self,
        *,
        workbench: SearchWorkbench,
        ruleset: Ruleset,
        engine: MatchFit,
        searches: SearchStore,
        prompts: PromptLedger,
        declines: PromptDeclineLedger,
    ) -> None:
        self._work = workbench
        self._ruleset = ruleset
        self._engine = engine
        self._searches = searches
        self._prompts = prompts
        self._declines = declines

    async def execute(self, command: RunShortlistSearchCommand) -> ShortlistAnswer:
        now = self._work.clock.now()
        stages: dict[str, int] = {}

        with self._work.timed(stages, "read_searcher"):
            declared = await self._work.searcher_facts(
                player_id=command.searcher_id,
                sport=command.sport,
                # A constant function of the declaration: a shortlist's mode is
                # which tab the player is on, decided before anything was read.
                mode_of=lambda _: command.mode,
            )
        await self._work.refuse_a_held_searcher(declared.player_id)

        # **What this one search runs on**, which is the profile's own answer
        # unless the player asked otherwise: a grid they improvised on the search
        # screen, or the widening a rung offer promised them. Applied here, once,
        # so that everything downstream — the box, the radius gate, the distance
        # term, the availability denominator, the window and the recorded grid —
        # reads one set of facts and cannot disagree about what was asked for.
        asked = await self._work.asked_for(
            declared,
            availability_override=command.availability_override,
            offered_by_search_id=command.offered_by_search_id,
            rung=command.rung,
        )
        searcher = replace(declared, grid=asked.grid, radius_km=asked.radius_km)

        snapshot, freshness = self._work.bound_snapshot(command.sport, now)

        # *Is this a newcomer's search* is decided once, here, and handed to
        # both halves of the absorption tally. The read skips and the write
        # happens on one answer, so the bucket cannot be read on a search that
        # will not add to it, or added to on a search that never read it.
        for_a_newcomer = searcher.is_new_at(now)

        with self._work.timed(stages, "read_gates"):
            context = await self._work.bind(
                searcher,
                snapshot,
                now,
                in_box=self._work.population(searcher, snapshot),
                surface=SearchSurface.SHORTLIST,
                initiation=SearchInitiation.HUMAN,
                for_a_newcomer=for_a_newcomer,
                # **No challenge to except**: this surface names none, and the
                # open-challenge gate excludes everybody the searcher is
                # arranging with, exactly as it always has.
                completing_challenge_id=None,
            )

        with self._work.scoring(stages):
            try:
                shortlist = run(context, self._engine)
            except InvariantViolated as broken:
                raise MatchmakingUnavailable(
                    f"the matcher refused to answer: {broken}"
                ) from broken

        with self._work.timed(stages, "attach"):
            rows = await self._work.attach(shortlist.returned, context)

        returned = tuple(row.scored for row in rows)
        with self._work.timed(stages, "relaxation"):
            ladder = self._ladder(context, shortlist, asked, shown=len(rows))
        record = SearchRecord(
            id=new_uuid(),
            searcher_id=searcher.player_id,
            sport=command.sport,
            mode=command.mode,
            intent_read=None,
            surface=SearchSurface.SHORTLIST,
            initiation=SearchInitiation.HUMAN,
            at=now,
            engine_version=self._engine.version,
            ruleset_version=self._ruleset.version,
            snapshot_version=snapshot.snapshot_version,
            trace_id=command.trace_id,
            index_stale=freshness.records_staleness,
            counts=_counts(shortlist, len(returned)),
            best_withheld_fit=shortlist.best_withheld_fit,
            pool_description=PoolDescription(
                sport=command.sport,
                radius_km_used=searcher.radius_km,
                players_in_range=shortlist.players_in_range,
                window=window_of(searcher.grid, context.today),
            ),
            searcher_grid=searcher.grid.codes,
            searcher_slot_count=len(searcher.grid),
            searcher_area_code=searcher.area_code,
            # **Set on every search, and not only where the offers were
            # computed.** The bit's job is to count the searchers already at the
            # slider's ceiling, and a searcher at 50 km who got twenty results
            # is one of them — recording ``false`` for them because nobody
            # needed a rung would undercount the exact population the column
            # exists to find. It costs no re-run: the ladder's arithmetic is
            # pure, and only the *counts* on it are expensive.
            radius_clamp_bit=radius_ladder(searcher.radius_km).clamped,
            rung_offers=None if ladder is None else ladder.offers,
            offered_by_search_id=asked.offered_by_search_id,
            rung_taken=asked.rung_taken,
            latency_ms_by_stage=stages,
            candidates=self._work.recorded_rows(rows, shortlist.near_misses),
        )
        await self._work.record(record)
        await self._work.note_exposure(
            command.sport, now, returned, for_a_newcomer
        )
        return ShortlistAnswer(
            record=record,
            sorts_available=sorts_available(
                tuple(of_scored(row) for row in returned),
                surface=SearchSurface.SHORTLIST,
            ),
            # After the commit, deliberately. A prompt is a courtesy read over a
            # row that now exists — *how often have I taken this widening* counts
            # this search too — and a question the platform could not ask is
            # never a reason to fail a search that ran.
            prompts=await self._raised(command, asked, profile_grid=declared.grid),
        )

    # -- the ladder ----------------------------------------------------------

    def _ladder(
        self,
        context: SearchContext,
        shortlist: Shortlist,
        asked: AskedFor,
        *,
        shown: int,
    ) -> Ladder | None:
        """Every rung available to this searcher, priced — or nothing at all.

        ``MIN_SHORTLIST`` **decides only whether this runs**. It triggers no
        widening, changes no threshold and reaches no gate: past it the engine
        computes what relaxing the searcher's own asks would be worth, and the
        player takes one or does not (``docs/adr/0099`` §3).

        The count it reads is the rows the response actually carries — after a
        card that could not be assembled dropped one — because that is the list
        the player is looking at when they decide whether they want another
        option.

        **What a rung is priced against is a different number, on purpose.** The
        trigger asks *is this list short*, in rows shown; a rung asks *would
        widening add anybody*, in people above the floor. Those are two
        populations and comparing them would be the arithmetic error: a rung's
        count is only ever set beside ``n_cleared_floor``, which is the same
        measurement taken at the same place.

        **One climb per search screen.** A search that is itself a taken rung
        prices no further rung. The widening is the searcher's own radius by the
        time this reads it, so a ladder priced here would be a ladder off the
        widening — and four taps from 8 km would land on the 50 km ceiling
        without the player being asked once. ``relaxation.py``'s *there is no
        third radius rung* is that sentence, and this is where it is enforced:
        two rungs is the whole ladder, and ×2.0 of the searcher's saved radius is
        the furthest any accepted offer reaches.

        **By climb and not by ask.** The guard reads ``rung_taken`` rather than
        *did the radius move*, so a **times** rung ends the ladder too, and
        neither reason for that is about distance. *One climb per search screen*
        is the rule, and A then B is two climbs on one screen. And rung A can
        **evict** (``widening.py``): pricing a radius rung against a grid the
        engine has just widened would price it over a population the player never
        chose. All three rungs travel on the offer and their order is a
        recommendation rather than a lock (``docs/adr/0099`` §2), so a player who
        wants distance takes the radius rung — they are not made to spend their
        one climb on the cheapest.

        The refusal is an **empty ladder and never nothing**, because the two
        spellings already mean different things on the wire: ``null`` is *your
        list was long enough that nobody priced a rung*, which is false about a
        short list. Nothing new is recorded for it — the record's own
        ``rung_taken`` sits beside the empty list and is what says why it is
        empty.
        """

        if shown >= self._ruleset.floors.min_shortlist:
            return None
        if asked.rung_taken is not None:
            return nothing_priced(context.searcher.radius_km)
        try:
            return ladder_for(
                context,
                self._engine,
                strict_above_floor=shortlist.counts.n_cleared_floor,
            )
        except InvariantViolated as broken:
            raise MatchmakingUnavailable(
                f"the matcher refused to price a rung: {broken}"
            ) from broken

    # -- the prompts ---------------------------------------------------------

    async def _raised(
        self,
        command: RunShortlistSearchCommand,
        asked: AskedFor,
        *,
        profile_grid: WeeklyHours,
    ) -> tuple[RaisedPrompt, ...]:
        """Every question this search raises. **None of them changes a value.**

        Two are facts about this search and are free here; two were computed by a
        loop and are one lookup. The order is the vocabulary's own, so a client
        rendering the first one it understands gets the same one twice for the
        same search.

        **And every one of them passes one gate on the way out.** A player who
        said *not now* is not asked again for thirty days, keyed on the
        question's own identity and never on the value it quoted — so the filter
        is over the assembled list rather than folded into each raiser, which is
        what makes it one place instead of four.
        """

        raised: list[RaisedPrompt] = []
        week = improvised_week(asked=asked.grid, profile=profile_grid)
        if week is not None:
            raised.append(week)
        if await self._keeps_taking_this_widening(command, asked):
            raised.append(
                RaisedPrompt(
                    prompt=Prompt.KEEP_THIS_RADIUS, radius_km=asked.radius_km
                )
            )
        standing = await self._prompts.raised_for(
            player_id=command.searcher_id, sport=command.sport
        )
        for prompt in (Prompt.UPDATE_PLAY_INTENT, Prompt.REFRESH_YOUR_TIMES):
            if prompt not in standing:
                continue
            if prompt is Prompt.UPDATE_PLAY_INTENT:
                raised.append(
                    RaisedPrompt(
                        prompt=prompt,
                        mode=standing[prompt] or command.mode.value,
                    )
                )
            else:
                raised.append(RaisedPrompt(prompt=prompt))
        if not raised:
            # Nothing to filter, so nothing to ask the table about — the same
            # short-circuit ``last_passed_at`` makes one file over, for the same
            # reason: a read here would be a query asking the database which of
            # no questions have been declined, on the majority of searches.
            return ()
        silenced = await self._silenced(
            player_id=command.searcher_id, sport=command.sport
        )
        return tuple(question for question in raised if question.prompt not in silenced)

    async def _silenced(self, *, player_id: UUID, sport: Sport) -> frozenset[Prompt]:
        """Which of these questions the player has already answered *not now*.

        **One gate, at the one place every prompt converges**, rather than four
        checks at four raisers: the two loops go on raising into a ledger that
        expires, which is what keeps them what their docstrings say they are —
        *notice, leave a prompt, never act* — and a fifth prompt added in two
        years inherits this filter structurally.

        It is a read over a **durable** row and not over the ephemeral ledger
        beside it, because a decline is a player's answer and a suppression held
        in a TTL is thirty days of evidence that TTL then destroys
        (``declines.py``).

        **A gate that cannot be evaluated stays quiet**, which is the opposite
        collapse from the ledgers wrapped in ``fail_soft_ledgers.py`` and is
        forced two ways. This whole block runs *after* a committed search, so
        raising here would fail a search that already ran and was recorded; and
        of the two degraded outcomes — *ask somebody who said no* and *say
        nothing* — the second is what the rest of this block already does when a
        ledger is unreachable. So the degraded answer is **every** prompt
        silenced, which the filter above renders as no prompt at all — the
        prompts a decline can silence, which is what a table full of declines
        would have said at worst, rather than the whole union.
        """

        try:
            return await self._declines.suppressed_for(
                player_id=player_id,
                sport=sport,
                since=silence_began(self._work.clock.now()),
            )
        except Exception:
            # Warning rather than error, on the wrapper's own reasoning: nothing
            # is broken for the player and the search they asked for is on its
            # way. What it must not be is silent — a platform that quietly
            # stopped offering to keep a widening looks exactly like a platform
            # nobody accepts the offer from, which is one of the two rates these
            # rows exist to measure.
            logger.warning(
                "prompt declines unreadable, raising no prompt",
                extra={"searcher_id": str(player_id)},
                exc_info=True,
            )
            return frozenset(prompt for prompt in Prompt if suppresses(prompt))

    async def _keeps_taking_this_widening(
        self, command: RunShortlistSearchCommand, asked: AskedFor
    ) -> bool:
        """Whether this radius has been taken often enough to be worth keeping.

        It counts **this** radius and not any widening, and it counts this search
        too — the row is already committed — so the threshold is a plain
        *how many times*, with no off-by-one hiding in a comment.
        """

        if asked.rung_taken is None or asked.rung_taken is Rung.A:
            return False
        taken = await self._searches.widenings_taken(
            searcher_id=command.searcher_id,
            sport=command.sport,
            radius_km=asked.radius_km,
        )
        return taken >= REPEATED_WIDENINGS

def _counts(shortlist: Shortlist, n_returned: int) -> StagedCounts:
    """The staged counts, with ``n_returned`` taken from the rows actually sent.

    It is the count **after** a card could not be assembled, not before, because
    the column's second job is detecting an erasure that removed a candidate row
    from a search that survived — and a detector seeded with a number that never
    matched would report a redaction on the day it shipped.
    """

    return replace(shortlist.counts, n_returned=n_returned)


