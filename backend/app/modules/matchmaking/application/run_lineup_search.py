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

**The answer carries the pool it seated from, and the court names people on
it.** The returned band is ``pool_for``'s top ``K`` by Fit — the seated among
them — and not the seated alone (#407). A court is its answer, but a builder is
also a screen somebody picks from, and *Pick players myself* on a court reached
from a challenge has no list but this record: that journey mints no shortlist,
``POST /forecasts`` and the send both refuse anybody the cited search never
returned, and a plain ``POST /searches`` is gated by the very challenge being
completed — so a record holding only the seated offered that screen the one
person just taken off a seat, or nobody. **Exposure still counts the seated
only**: the court is what was shown, the rest of the pool is shown only if the
player opens the list, and counting what may never be opened would sink two
dozen people per ⚡ under the ±6 adjustment (``the-engine.md`` §8).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from itertools import combinations
from typing import Callable, Sequence, final
from uuid import UUID

from app.engines.matchfit.grouping import (
    Arranged,
    GroupScore,
    PairAdmissibility,
    Seating,
)
from app.engines.matchfit.core import SearchMode
from app.engines.matchfit.ruleset import Ruleset
from app.engines.matchfit.scoring import MatchFit
from app.engines.matchfit.v1 import seat
from app.kernel import InvariantViolated, Sport, invariant
from app.modules.blocks.domain.ports import BlockQuery
from app.modules.matchmaking.application.commands import RunLineupSearchCommand
from app.modules.matchmaking.application.outward_reads import (
    live_block_pairs,
    read_demand,
)
from app.modules.matchmaking.application.record_rows import group_term_rows
from app.modules.matchmaking.application.search_workbench import SearchWorkbench
from app.modules.matchmaking.domain.deck import mode_for_intent
from app.modules.matchmaking.domain.errors import (
    LockedSeatNotAvailable,
    MatchmakingUnavailable,
    TheChallengeIsNotYoursToFill,
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
    who_turned_up,
)
from app.modules.matchmaking.domain.ports import (
    HalfBuiltCourt,
    HalfBuiltCourtQuery,
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
from app.modules.player_profile.domain.play_intent import PlayIntent
from app.shared.ids import new_uuid


@final
@dataclass(frozen=True, slots=True)
class LineupAnswer:
    """What the route renders: the record, the court, and the three ways round.

    The record is the answer's identity, exactly as it is for a shortlist, and
    its returned band is the **pool** the four were drawn from, in Fit order,
    with the seated among them. A seat names a person by id and their row is
    read off the record — so the card in the response and the card in the
    record cannot disagree about what was shown, and a pool opened on this
    record has the rest of the ranking to offer.

    ``seats``, ``arrangements`` and ``group_reason`` are beside it rather than on
    it for the reason the sorts are: they are a statement about *this* answer,
    and layer 4 — which holds the objective that produced them — never leaves the
    building.
    """

    record: SearchRecord
    sorts_available: tuple[SortOption, ...]
    #: The current court, seat by seat: **the evenest arrangement's seating.**
    seats: tuple[LineupSeat, ...]
    #: Every way round, each with its own forecast and its own seating.
    arrangements: tuple[tuple[Arranged, tuple[LineupSeat, ...]], ...]
    #: The best by ``G``. **``None`` when no objective was computed** — a
    #: line-up with an open seat, or a singles line-up, where ``G`` was struck by
    #: argument. Naming the min-gap arrangement *best* there would give one field
    #: two meanings on exactly the responses where a builder needs the first.
    best: Arranged | None
    #: The min-gap arrangement, and **what the court is drawn as** — the two
    #: are one field rather than two, because ``docs/adr/0136`` made them the
    #: same arrangement in both modes and a second field that cannot differ is
    #: only somewhere for them to drift apart. The objective chose the four and
    #: ``group_reason`` says why; which way round they sit is the one question
    #: balance still answers, and opening on any other arrangement would show a
    #: court the player's first tap re-seats.
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
@dataclass(frozen=True, slots=True)
class TheAsk:
    """What one line-up is for, after the challenge — if any — has been read.

    **The five things a fill and an ordinary ⚡ disagree about, resolved
    together.** They all turn on one fact, so they are answered in one place and
    read everywhere else: a use case that asked *was a challenge named* at each
    of the five would be five chances to answer it differently, and the one that
    drifted would be the one that quietly stopped exempting the gate.

    ``mode_of`` is a function rather than a mode because the workbench resolves
    it against the declaration it reads: passing a value would need a second read
    of that declaration, and the two could disagree.
    """

    sport: Sport
    locked_seats: tuple[UUID, ...]
    mode_of: Callable[[PlayIntent], SearchMode]
    #: The one challenge the open-challenge gate steps aside for, or nothing.
    exempt_challenge_id: UUID | None
    #: Everybody who has answered that challenge and left it. Empty otherwise.
    excluding: frozenset[UUID]


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
        courts: HalfBuiltCourtQuery,
    ) -> None:
        self._work = workbench
        self._ruleset = ruleset
        self._engine = engine
        self._blocks = blocks
        self._courts = courts

    async def execute(self, command: RunLineupSearchCommand) -> LineupAnswer:
        now = self._work.clock.now()
        stages: dict[str, int] = {}

        # **The challenge is read before anything else, because it is what the
        # search is *about*.** The sport, the mode and the locked seats are all
        # read off it (``docs/adr/0150`` §2), so a read that happened later would
        # be a search already bound to facts a client sent. From here on nothing
        # asks *was a challenge named* again: ``asked`` is the resolved answer,
        # and one place that resolves it is one place that can be wrong.
        ask = await self._resolve(command)
        sport = ask.sport

        with self._work.timed(stages, "read_searcher"):
            declared = await self._work.searcher_facts(
                player_id=command.searcher_id,
                sport=sport,
                mode_of=ask.mode_of,
            )
        await self._work.refuse_a_held_searcher(declared.player_id)

        asked = await self._work.asked_for(
            declared,
            availability_override=command.availability_override,
            offered_by_search_id=command.offered_by_search_id,
            rung=command.rung,
        )
        searcher = replace(declared, grid=asked.grid, radius_km=asked.radius_km)
        snapshot, freshness = self._work.bound_snapshot(sport, now)
        for_a_newcomer = searcher.is_new_at(now)

        # **The surface is derived, never sent.** A line-up and filling seats
        # differ by locked seats, which is a property of the request, so
        # ``search.surface`` records which of the two happened without the
        # client having chosen a route (``the-two-contracts.md`` §1). A fill
        # from a challenge lands here too and needs no fifth value — and since
        # ``docs/adr/0162`` it may lock nobody, when the court it completes has
        # lost everybody but the filler, so naming the challenge is what makes
        # it a fill rather than the locked seats being non-empty.
        surface = (
            SearchSurface.FILL_SEATS
            if ask.locked_seats or ask.exempt_challenge_id is not None
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
                completing_challenge_id=ask.exempt_challenge_id,
            )

        with self._work.scoring(stages):
            try:
                pool = pool_for(
                    context,
                    self._engine,
                    # **Nobody who has answered this challenge is a candidate for
                    # its own fill** (§4). They were released back into the deck
                    # the moment they declined or lapsed, and without this the
                    # send would refuse — after the player chose them.
                    excluding=ask.excluding,
                )
            except InvariantViolated as broken:
                raise MatchmakingUnavailable(
                    f"the matcher refused to answer: {broken}"
                ) from broken

        locked = self._locked(pool, ask.locked_seats)
        guests = guests_for(sport)
        fenced = searcher_of(context)
        # **Minted here rather than at the record**, because it is what turnout
        # is keyed off: one search, one draw, and the same search re-read draws
        # the same people.
        search_id = new_uuid()
        held = seated_from(locked, locked=True)
        with self._work.timed(stages, "seat"):
            try:
                admissible: PairAdmissibility | None = None
                if guests > 1:
                    # **A singles line-up asks no pairwise question**, so it
                    # makes no bulk block query and builds no mask. There is one
                    # pair in a two and it was gated at generation; a mask here
                    # would be ``O(K²)`` work over pairs no court will ever hold.
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

                def seat_them(rows: Sequence[Scored]) -> Seating:
                    """The one seating call, over whichever pool it is given.

                    The mask is built over ``pool.rows`` and asked about pairs,
                    so it serves any subsequence of it — there is no second mask
                    for the smaller pool and no chance of two disagreeing.
                    """

                    if admissible is None:
                        return single_seat(
                            fenced,
                            seated_from(rows),
                            self._ruleset,
                            combine_group_sigma,
                            locked=held,
                        )
                    return seat(
                        fenced,
                        seated_from(rows),
                        self._ruleset,
                        combine_group_sigma,
                        admissible,
                        locked=held,
                    )

                # **Who turned up tonight** (``lineups.py``'s ``TURNOUT``): the
                # engine still returns the best four, of a pool that is not the
                # same twenty people every night.
                present = who_turned_up(
                    pool.rows, key=str(search_id), guests=guests
                )
                seating = seat_them(present)
                # **Turnout may cost evenness; it may never cost a seat.** A
                # draw that cannot fill a court the whole pool could have filled
                # would be reported as ``POOL_EXHAUSTED``, which is a lie about
                # the pool — and ``unfilled_reason`` reads the whole pool, so it
                # would be answering about people the engine never saw.
                if len(seating.seated) < guests and len(present) != len(pool.rows):
                    seating = seat_them(pool.rows)
            except InvariantViolated as broken:
                raise MatchmakingUnavailable(
                    f"the matcher refused to seat a four: {broken}"
                ) from broken

        reason = unfilled_reason(pool, seating, context, guests=guests)
        seated = self._seated_off_the_pool(pool, seating)
        with self._work.timed(stages, "attach"):
            # **The whole pool, not the seated few.** ``K`` cards rather than
            # three — the same bound a shortlist pays for twenty, and the price
            # of a record *Pick players myself* can draw a list from.
            rows = await self._work.attach(pool.rows, context)

        returned = tuple(row.scored for row in rows)
        # Who actually sat down, among the rows that survived ``attach``: the
        # only rows exposure is noted for, below.
        shown = tuple(row for row in returned if row.player_id in seated)
        record = SearchRecord(
            id=search_id,
            searcher_id=searcher.player_id,
            sport=sport,
            # **The mode the search actually ran under**, read off the searcher
            # the workbench built rather than off the request — which is the only
            # spelling that stays true when the mode was inherited from a
            # challenge or resolved from a declaration. ``intent_read`` stays
            # ``None``: it is non-null **exactly on the deck**, where ``mode`` is
            # null and a declaration is the only record of what was scored. Here
            # a real mode was chosen and recorded, so the row says which.
            mode=searcher.mode,
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
                sport=sport,
                radius_km_used=searcher.radius_km,
                players_in_range=pool.players_in_range,
                window=window_of(searcher.grid, context.today),
            ),
            searcher_grid=searcher.grid.codes,
            searcher_slot_count=len(searcher.grid),
            searcher_area_code=searcher.area_code,
            radius_clamp_bit=radius_ladder(searcher.radius_km).clamped,
            # **The ladder does not run here.** ``MIN_SHORTLIST`` counts rows in
            # a list somebody reads, and a line-up returns seats; pricing a rung
            # against *how many people would clear the floor* would answer a
            # question about a shortlist this search never produced.
            rung_offers=None,
            offered_by_search_id=asked.offered_by_search_id,
            rung_taken=asked.rung_taken,
            latency_ms_by_stage=stages,
            lineup=_layer_four(pool, seating, seated=seated),
            candidates=self._work.recorded_rows(rows, pool.near_misses),
        )
        await self._work.record(record)
        # **The seated only, and never the pool.** The court is what this answer
        # shows; the rest of the pool is drawn only if the player opens the
        # list, and a ⚡ that counted two dozen appearances would sink the top
        # of every ranking a few fills later under the ±6 exposure adjustment
        # (``the-engine.md`` §8). The cost is stated rather than hidden: a list
        # opened off this record is shown and **under**-counted — the opposite
        # error from a shortlist, which counts every row whether or not the
        # player scrolled to it. Neither is a gate, and the two do not cancel.
        await self._work.note_exposure(sport, now, shown, for_a_newcomer)
        searcher_id = str(searcher.player_id)
        week = improvised_week(asked=asked.grid, profile=declared.grid)
        return LineupAnswer(
            record=record,
            # After the commit, like the shortlist's: the sheet rides on the
            # response of the route that used the week, so the search has
            # already run by the time the question appears and there is nothing
            # left for an answer — or a dismissal — to block.
            prompts=() if week is None else (week,),
            sorts_available=sorts_available((), surface=surface),
            # **The court is drawn as the evenest, always** (``docs/adr/0136``).
            # ``G`` chose who is on the court and ``group_reason`` says why;
            # which way round they sit is the question balance answers, and it
            # is the same re-seating *Even it out* would perform by hand a
            # moment later. ``is_best`` keeps its own meaning beside it rather
            # than deciding the drawing.
            seats=roster(
                None if seating.evenest is None else seating.evenest.arrangement,
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
            evenest=seating.evenest,
            group_reason=None if seating.reason is None else seating.reason.value,
            dock=(
                UnfilledReason.NO_SHARED_SLOTS
                if no_shared_slots(fenced, seating)
                else None
            ),
            optimised_for_group=bool(ask.locked_seats),
        )

    async def _resolve(self, command: RunLineupSearchCommand) -> "TheAsk":
        """What this line-up is actually for, resolved once. **One question.**

        A fill and an ordinary ⚡ differ in five places — the sport, the locked
        seats, the mode, the gate's exemption and the pool's exclusion — and all
        five turn on the **same** fact: whether a challenge was named. Asking it
        five times would be five chances to answer it differently, and the one
        that drifted would be the one that quietly stopped exempting the gate.
        So it is asked here, and everything below reads the answer.

        The read **fails closed**, which is what the port declared and why it is
        its own port: a read that stood down would run an ordinary ⚡ over a pool
        that still excludes every person on the court, and hand the player a four
        of strangers where their own line-up should have been.

        The refusal for an id that answers nothing is a **conflict about the
        challenge**, and it names none of the three reasons — no such challenge,
        no seat of yours on it, nobody arranging it any more.
        """

        challenge_id = command.completing_challenge_id
        if challenge_id is None:
            asked_for = invariant(
                command.mode,
                "a line-up that names no challenge and no mode",
            )
            return TheAsk(
                sport=invariant(
                    command.sport,
                    "a line-up with neither a sport nor a challenge to read "
                    "one from",
                ),
                locked_seats=command.locked_seats,
                # A constant: which tab you are on, decided before anything was
                # read at all.
                mode_of=lambda _: asked_for,
                exempt_challenge_id=None,
                excluding=frozenset(),
            )
        court = await read_demand(
            HalfBuiltCourtQuery,
            lambda: self._courts.half_built_court(
                challenge_id=challenge_id, member_id=command.searcher_id
            ),
        )
        if court is None:
            raise TheChallengeIsNotYoursToFill(
                "that challenge is not one of yours to fill"
            )
        return TheAsk(
            sport=court.sport,
            locked_seats=court.seated_ids,
            mode_of=self._mode_of(court),
            exempt_challenge_id=court.challenge_id,
            excluding=court.answered_and_gone,
        )

    def _mode_of(self, court: HalfBuiltCourt) -> Callable[[PlayIntent], SearchMode]:
        """Which weight vector a fill runs under. **Two answers, one read.**

        A function rather than a value, for the workbench's own reason: the
        declaration a mode is chosen from is the declaration recorded beside it,
        and there is no second load for the two to disagree across.

        *A challenge born with a mode* — **it keeps it.** A competitive court
        must not have its last seat filled by a for-fun search, and the mode is
        the court's rather than the filler's. A mutual-born court whose mint
        stamped ``FOR_FUN`` — either of the pair declared the sport *for fun*
        (``docs/adr/0169`` §8) — is born with one and keeps it the same way.

        *A challenge born without one* — deck-born, and a mutual-born court
        neither of whose pair declared *for fun* — resolves one from the
        **filler's** declared Play intent on the rule
        ``mode_for_intent`` keeps, ``NO_PREFERENCE → fun`` (``docs/adr/0150``
        §5). It was the deck's rule when that record was written; the deck now
        runs on one ruler for everybody (``docs/adr/0169`` §2) and the mapping
        lives on here. **No mode picker appears anywhere**, and ADR-0100 keeps
        its silence.
        """

        inherited = court.mode
        if inherited is not None:
            return lambda _: inherited
        return lambda intent: mode_for_intent(intent, self._ruleset.intent)

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

        **On a fill it is reachable and it means something** (``docs/adr/0150``).
        The open-challenge gate steps aside for the challenge being completed, so
        the people who accepted are ordinary rows in this pool; the four
        fail-closed gates are untouched, and the only way this can now fire from
        a challenge is that somebody in the line-up has been blocked, held or
        deactivated since they accepted. That is a true thing to say, and it is
        followed by a re-read rather than by a payload.
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

    def _seated_off_the_pool(
        self, pool: LineupPool, seating: Seating
    ) -> tuple[str, ...]:
        """Who sat down, in the order they were seated — and the proof that
        every one of them came out of the pool.

        The enumeration draws from the pool and the locked seats were resolved
        against it, so a lookup that missed would mean the two had come apart,
        and it says so rather than returning a court naming somebody the pool
        never held. What it does **not** prove is a row on the record:
        ``attach`` still drops a row it cannot build a card for, and a seat
        naming somebody ``candidates`` does not carry is the gap the read-back
        test names rather than one this closes.

        The record's rows are the pool itself, in Fit order, so ``position`` on
        this surface is a place in that list and not a seat — the Fit rank,
        unless a row above was dropped for its card — and the court says
        separately who sat where.
        """

        for one in seating.seated:
            invariant(
                pool.by_id(one.player_id),
                f"{one.player_id} was seated and is not in the pool they were "
                f"drawn from",
            )
        return tuple(one.player_id for one in seating.seated)


def _layer_four(
    pool: LineupPool, seating: Seating, *, seated: tuple[str, ...]
) -> LineupRecord:
    """Layer 4, assembled once. **Two rows, and no route returns any of it.**

    The winner and the runner-up come back whole because the deciding margin is
    computed over their contributions, and a margin is not reproducible from a
    code. The counters come from the enumeration itself, which is the only place
    ``docs/adr/0116``'s falsifier — *how many combinations the pairwise gate
    refused* — exists at all. And the seated are named, because the returned
    band stopped naming them.
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
        # **Who sat down, on the record.** The returned band is the pool now
        # (#407), and a partial line-up or a singles court writes no winner to
        # read the seated off — so the fact rides here, in the order they were
        # seated, beside the deepest rank it already implied.
        seated=tuple(UUID(one) for one in seated),
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
