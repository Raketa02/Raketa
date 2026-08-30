"""⚡ *Fill the seats* — the four, the forecast, and the reason it won.

**The same order as the shortlist, because it is the same rule.** Read the
searcher live, bind one snapshot and every live gate fact, run the pipeline,
record and commit before the answer goes anywhere, then note exposure. Steps 1, 2
and most of 4 are ``search_workbench.py``'s; what is here is the line-up's own.

Three things are the line-up's own, and each is here because a shortlist has no
use for it:

*The pairwise mask.* A four contains six pairs and the searcher is in three of
them (``docs/adr/0116``), so before anything is enumerated this makes **one bulk
block query over the ``K`` ids** and precomputes admissibility over every
candidate pair. It **fails closed**: a line-up that cannot evaluate the mask
refuses rather than seating four people on an unread gate.

*The enumeration.* ``argmax G`` over the combinations, each judged at its own best
arrangement, with the floor binding every seat the engine fills.

*Layer 4.* The winning combination and the runner-up, the three counters and the
deepest Fit rank reached — written before the answer is returned and returned by
no route, exactly like the near-miss band beside it.

**A partial line-up is a `200`.** A four can be impossible where candidates are
plentiful, and *three of four* is an honest answer with a provisional forecast on
it rather than an error. A seat is never filled below the quality floor to
complete a four, a newcomer least of all (``docs/adr/0099``).

**Optimising for the group is stated rather than discovered.** With seats locked
the engine is no longer optimising for the searcher, who may end up with a worse
individual match than an empty court would have given them, so the envelope says
``optimised_for: GROUP`` and the screen can say so too.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from itertools import combinations
from typing import final
from uuid import UUID

from app.engines.matchfit.grouping import (
    Arranged,
    GroupScore,
    PairAdmissibility,
    Seating,
)
from app.engines.matchfit.ruleset import Ruleset
from app.engines.matchfit.scoring import MatchFit
from app.engines.matchfit.v1 import seat
from app.kernel import InvariantViolated, invariant
from app.modules.blocks.domain.ports import BlockQuery
from app.modules.matchmaking.application.commands import RunLineupSearchCommand
from app.modules.matchmaking.application.outward_reads import live_block_pairs
from app.modules.matchmaking.application.record_rows import group_term_rows
from app.modules.matchmaking.application.search_workbench import SearchWorkbench
from app.modules.matchmaking.domain.errors import (
    LockedSeatNotAvailable,
    MatchmakingUnavailable,
)
from app.modules.matchmaking.domain.fence import (
    combine_group_sigma,
    searcher_of,
)
from app.modules.matchmaking.domain.lineups import (
    LineupPool,
    LineupSeat,
    UnfilledReason,
    guests_for,
    mask_over,
    max_fit_rank,
    no_shared_slots,
    pool_for,
    roster,
    seated_from,
    single_seat,
    unfilled_reason,
)
from app.modules.matchmaking.domain.relaxation import radius_ladder
from app.modules.matchmaking.domain.searches import (
    CombinationBand,
    LineupRecord,
    PoolDescription,
    RecordedCombination,
    SearchInitiation,
    SearchRecord,
    SearchSurface,
    SortOption,
)
from app.modules.matchmaking.domain.prompts import (
    RaisedPrompt,
    improvised_week,
)
from app.modules.matchmaking.domain.shortlist import Scored
from app.modules.matchmaking.domain.sorting import sorts_available
from app.modules.player_profile.domain.availability import window_of
from app.shared.ids import new_uuid


@final
@dataclass(frozen=True, slots=True)
class LineupAnswer:
    """What the route renders: the record, the court, and the three ways round.

    The record is the answer's identity, exactly as it is for a shortlist, and
    the seated rows are read off it — so the card in the response and the card in
    the record cannot disagree about what was shown.

    ``seats``, ``arrangements`` and ``group_reason`` are beside it rather than on
    it for the reason the sorts are: they are a statement about *this* answer,
    and layer 4 — which holds the objective that produced them — never leaves the
    building.
    """

    record: SearchRecord
    sorts_available: tuple[SortOption, ...]
    #: The current court: the best arrangement, seat by seat.
    seats: tuple[LineupSeat, ...]
    #: Every way round, each with its own forecast and its own seating.
    arrangements: tuple[tuple[Arranged, tuple[LineupSeat, ...]], ...]
    #: The best by ``G``. **``None`` when no objective was computed** — a
    #: line-up with an open seat, or a singles line-up, where ``G`` was struck by
    #: argument. Naming the min-gap arrangement *best* there would give one field
    #: two meanings on exactly the responses where a builder needs the first.
    best: Arranged | None
    #: The one the court is drawn as: the best where there is one, the evenest
    #: where there is not.
    drawn: Arranged | None
    evenest: Arranged | None
    group_reason: str | None
    #: ``NO_SHARED_SLOTS`` when the four-way week is empty. **A dock, never a
    #: refusal** — nobody is removed from the court for it.
    dock: UnfilledReason | None
    optimised_for_group: bool
    #: The questions this line-up raises and does not answer. ⚡ consumed the
    #: improvised week exactly as *Find me a game* did, so it owes the same offer
    #: to keep it — the omission was an oversight rather than a decision. There
    #: is no widening prompt here: the ladder is priced by the shortlist, and a
    #: line-up takes a rung without ever counting one.
    prompts: tuple[RaisedPrompt, ...] = ()


@final
class RunLineupSearch:
    """The line-up, end to end."""

    def __init__(
        self,
        *,
        workbench: SearchWorkbench,
        ruleset: Ruleset,
        engine: MatchFit,
        blocks: BlockQuery,
    ) -> None:
        self._work = workbench
        self._ruleset = ruleset
        self._engine = engine
        self._blocks = blocks

    async def execute(self, command: RunLineupSearchCommand) -> LineupAnswer:
        now = self._work.clock.now()
        stages: dict[str, int] = {}

        with self._work.timed(stages, "read_searcher"):
            declared = await self._work.searcher_facts(
                player_id=command.searcher_id,
                sport=command.sport,
                mode_of=lambda _: command.mode,
            )
        await self._work.refuse_a_held_searcher(declared.player_id)

        asked = await self._work.asked_for(
            declared,
            availability_override=command.availability_override,
            offered_by_search_id=command.offered_by_search_id,
            rung=command.rung,
        )
        searcher = replace(declared, grid=asked.grid, radius_km=asked.radius_km)
        snapshot, freshness = self._work.bound_snapshot(command.sport, now)
        for_a_newcomer = searcher.is_new_at(now)

        # **The surface is derived, never sent.** A line-up and filling seats
        # differ only by locked seats, which is a property of the request, so
        # ``search.surface`` records which of the two happened without the
        # client having chosen a route (``the-two-contracts.md`` §1).
        surface = (
            SearchSurface.FILL_SEATS
            if command.locked_seats
            else SearchSurface.LINEUP
        )
        with self._work.timed(stages, "read_gates"):
            context = await self._work.bind(
                searcher,
                snapshot,
                now,
                in_box=self._work.population(searcher, snapshot),
                surface=surface,
                initiation=SearchInitiation.HUMAN,
                for_a_newcomer=for_a_newcomer,
            )

        with self._work.scoring(stages):
            try:
                pool = pool_for(context, self._engine)
            except InvariantViolated as broken:
                raise MatchmakingUnavailable(
                    f"the matcher refused to answer: {broken}"
                ) from broken

        locked = self._locked(pool, command.locked_seats)
        guests = guests_for(command.sport)
        fenced = searcher_of(context)
        with self._work.timed(stages, "seat"):
            try:
                if guests == 1:
                    # **A singles line-up asks no pairwise question**, so it
                    # makes no bulk block query and builds no mask. There is one
                    # pair in a two and it was gated at generation; a mask here
                    # would be ``O(K²)`` work over pairs no court will ever hold.
                    seating = single_seat(
                        fenced,
                        seated_from(pool.rows),
                        self._ruleset,
                        combine_group_sigma,
                        locked=seated_from(locked, locked=True),
                    )
                else:
                    with self._work.timed(stages, "mask"):
                        admissible = mask_over(
                            pool.rows,
                            context,
                            await live_block_pairs(
                                self._blocks,
                                [UUID(row.player_id) for row in pool.rows],
                            ),
                        )
                    self._refuse_locked_seats_that_clash(locked, admissible)
                    seating = seat(
                        fenced,
                        seated_from(pool.rows),
                        self._ruleset,
                        combine_group_sigma,
                        admissible,
                        locked=seated_from(locked, locked=True),
                    )
            except InvariantViolated as broken:
                raise MatchmakingUnavailable(
                    f"the matcher refused to seat a four: {broken}"
                ) from broken

        reason = unfilled_reason(pool, seating, context, guests=guests)
        seated_rows = self._rows_for(pool, seating)
        with self._work.timed(stages, "attach"):
            rows = await self._work.attach(seated_rows, context)

        returned = tuple(row.scored for row in rows)
        record = SearchRecord(
            id=new_uuid(),
            searcher_id=searcher.player_id,
            sport=command.sport,
            mode=command.mode,
            intent_read=None,
            surface=surface,
            initiation=SearchInitiation.HUMAN,
            at=now,
            engine_version=self._engine.version,
            ruleset_version=self._ruleset.version,
            snapshot_version=snapshot.snapshot_version,
            trace_id=command.trace_id,
            index_stale=freshness.records_staleness,
            counts=replace(pool.counts, n_returned=len(returned)),
            best_withheld_fit=pool.best_withheld_fit,
            pool_description=PoolDescription(
                sport=command.sport,
                radius_km_used=searcher.radius_km,
                players_in_range=pool.players_in_range,
                window=window_of(searcher.grid, context.today),
            ),
            searcher_grid=searcher.grid.codes,
            searcher_slot_count=len(searcher.grid),
            radius_clamp_bit=radius_ladder(searcher.radius_km).clamped,
            # **The ladder does not run here.** ``MIN_SHORTLIST`` counts rows in
            # a list somebody reads, and a line-up returns seats; pricing a rung
            # against *how many people would clear the floor* would answer a
            # question about a shortlist this search never produced.
            rung_offers=None,
            offered_by_search_id=asked.offered_by_search_id,
            rung_taken=asked.rung_taken,
            latency_ms_by_stage=stages,
            lineup=_layer_four(pool, seating),
            candidates=self._work.recorded_rows(rows, pool.near_misses),
        )
        await self._work.record(record)
        await self._work.note_exposure(command.sport, now, returned, for_a_newcomer)
        searcher_id = str(searcher.player_id)
        # **What the court is drawn as.** The best by ``G`` where there is one,
        # and the evenest where there is not — an incomplete four has no
        # objective, so *which way round is this being shown* falls to the only
        # question balance can still answer.
        drawn = seating.best or seating.evenest
        week = improvised_week(asked=asked.grid, profile=declared.grid)
        return LineupAnswer(
            record=record,
            # After the commit, like the shortlist's: the sheet rides on the
            # response of the route that used the week, so the search has
            # already run by the time the question appears and there is nothing
            # left for an answer — or a dismissal — to block.
            prompts=() if week is None else (week,),
            sorts_available=sorts_available((), surface=surface),
            seats=roster(
                None if drawn is None else drawn.arrangement,
                searcher_id=searcher_id,
                guests=guests,
                reason=reason,
            ),
            arrangements=tuple(
                (
                    one,
                    roster(
                        one.arrangement,
                        searcher_id=searcher_id,
                        guests=guests,
                        reason=reason,
                    ),
                )
                for one in seating.arrangements
            ),
            best=seating.best,
            drawn=drawn,
            evenest=seating.evenest,
            group_reason=None if seating.reason is None else seating.reason.value,
            dock=(
                UnfilledReason.NO_SHARED_SLOTS
                if no_shared_slots(fenced, seating)
                else None
            ),
            optimised_for_group=bool(command.locked_seats),
        )

    def _locked(
        self, pool: LineupPool, locked_seats: tuple[UUID, ...]
    ) -> tuple[Scored, ...]:
        """The hand-seated rows, **from this search's own pool or not at all.**

        A locked seat is a person the searcher chose, and the only people they
        could have chosen are people this backend showed them. Somebody who is no
        longer in the pool has been removed by a gate — a block taken since, a
        hold, a safety preference, a level that has moved — and the answer to
        *seat them anyway* is no.

        It **refuses rather than quietly dropping the seat**: a four that came
        back without the person the searcher put in it, and with somebody else
        there instead, is the builder lying about what it was asked to do.
        """

        rows: list[Scored] = []
        for player_id in locked_seats:
            row = pool.by_id(str(player_id))
            if row is None:
                raise LockedSeatNotAvailable(
                    "one of the seated players is no longer available for this "
                    "line-up"
                )
            rows.append(row)
        return tuple(rows)

    def _refuse_locked_seats_that_clash(
        self, locked: tuple[Scored, ...], admissible: PairAdmissibility
    ) -> None:
        """**Hand-seating is not a way past a gate** (``docs/adr/0116``).

        :meth:`_locked` proves each of them is somebody this search can still
        see; this proves they can see **each other**. The two questions are
        different and only the second is new in a four: `a` and `b` may each have
        passed all ten gates against the searcher while `a` blocked `b` last
        month, and a builder that seated them anyway would put a block on a court
        for ninety minutes.

        It refuses under the same code and names nobody, for the reason a
        withheld row names no gate: saying *which two* would tell a searcher that
        one of them blocked the other.
        """

        for one, other in combinations(locked, 2):
            if not admissible(one.player_id, other.player_id):
                raise LockedSeatNotAvailable(
                    "two of the players you seated cannot share a court"
                )

    def _rows_for(
        self, pool: LineupPool, seating: Seating
    ) -> tuple[Scored, ...]:
        """The seated, as the rows the record and the card were built from.

        In **seat order** rather than in Fit order, because ``position`` on a
        recorded row is where somebody was shown and on this surface that is
        where they were seated.

        Every seated player came out of this pool — the enumeration draws from
        it and the locked seats were resolved against it — so a lookup that
        missed would mean the two had come apart, and it says so rather than
        returning a court with a person quietly removed from it.
        """

        return tuple(
            invariant(
                pool.by_id(one.player_id),
                f"{one.player_id} was seated and is not in the pool they were "
                f"drawn from",
            )
            for one in seating.seated
        )


def _layer_four(pool: LineupPool, seating: Seating) -> LineupRecord:
    """Layer 4, assembled once. **Two rows, and no route returns either.**

    The winner and the runner-up come back whole because the deciding margin is
    computed over their contributions, and a margin is not reproducible from a
    code. The counters come from the enumeration itself, which is the only place
    ``docs/adr/0116``'s falsifier — *how many combinations the pairwise gate
    refused* — exists at all.
    """

    rows = tuple(
        _combination(band, score)
        for band, score in (
            (CombinationBand.WINNER, seating.winner),
            (CombinationBand.RUNNER_UP, seating.runner_up),
        )
        if score is not None
    )
    return LineupRecord(
        combinations=seating.counts.combinations,
        refused_by_gate=seating.counts.refused_by_gate,
        refused_by_floor=seating.counts.refused_by_floor,
        max_fit_rank_seated=max_fit_rank(pool, seating),
        rows=rows,
    )


def _combination(band: CombinationBand, score: GroupScore) -> RecordedCombination:
    """One scored four, with the whole ``G`` breakdown behind it."""

    # The **value** form: a scored combination is a complete four, and the
    # narrowing comes off the raise rather than off an ``assert`` that
    # ``python -O`` would strip in exactly the deployment where it mattered.
    partner = invariant(
        score.arrangement.partner,
        "a scored combination with nobody beside the searcher",
    )
    return RecordedCombination(
        band=band,
        members=tuple(UUID(one.player_id) for one in score.arrangement.seated),
        partner_id=UUID(partner.player_id),
        terms=group_term_rows(score),
        degraded_terms=tuple(term.value for term in score.degraded_terms),
        side_gap=score.side_gap,
        forecast_pct=score.forecast.pct,
    )


__all__ = ["LineupAnswer", "RunLineupSearch"]
