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

**Never a fallback list.** When the engine raises, the feature is down and this
use case says so. A hand-rolled backend ranker arriving as a hotfix is how a
second, worse, unexplainable ranking implementation enters the system for ever.

**An empty shortlist is an answer.** It is recorded exactly like any other search
with ``n_returned = 0``, returned as a `200`, and the pool it came from is
described on every search rather than only on the empty ones — because a thin
pool and a broken floor are indistinguishable without that description.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, replace
from typing import Collection, Mapping, final
from uuid import UUID

from app.application.ports import UnitOfWork
from app.engines.matchfit.core import SearchMode, Term
from app.engines.matchfit.ruleset import Ruleset
from app.engines.matchfit.scoring import MatchFit
from app.kernel import Clock, Instant, InvariantViolated, Sport
from app.modules.blocks.domain.errors import BlockStateUnavailable
from app.modules.blocks.domain.ports import BlockQuery
from app.modules.matchmaking.application.commands import RunShortlistSearchCommand
from app.modules.matchmaking.application.outward_reads import read_demand
from app.modules.matchmaking.domain.cards import CardIdentity, PlayerCardSource
from app.modules.matchmaking.domain.candidate_index import Partition
from app.modules.matchmaking.domain.candidate_snapshot import (
    CandidateSnapshot,
    CandidateSource,
)
from app.modules.matchmaking.domain.errors import (
    AccountHeld,
    GateDataUnavailable,
    IndexTooStale,
    MatchmakingUnavailable,
    PlayerProfileNotCommitted,
    PlayIntentNotDeclared,
    SearchNotRecorded,
    SportNotRated,
)
from app.modules.matchmaking.domain.geography import Point
from app.modules.matchmaking.domain.ledgers import ExposureLedger, week_of
from app.modules.matchmaking.domain.ports import (
    AccountHoldQuery,
    AccountStatusQuery,
    AtStake,
    AtStakeQuery,
    MatchHistoryQuery,
    OpenChallenge,
    PairwiseCounterpart,
    PlayerScoreQuery,
    PlayerScoreReading,
)
from app.modules.matchmaking.domain.search_context import (
    LiveGateFacts,
    LiveTermFacts,
    SearchContext,
    SearcherFacts,
)
from app.modules.matchmaking.domain.search_store import SearchStore
from app.modules.matchmaking.domain.searches import (
    CandidateBand,
    PoolDescription,
    SearchCandidateRecord,
    SearchInitiation,
    SearchRecord,
    SearchSurface,
    SortOption,
    StagedCounts,
)
from app.modules.matchmaking.domain.shortlist import (
    Scored,
    Shortlist,
    ids_in_box,
    run,
)
from app.modules.matchmaking.domain.sorting import sorts_available
from app.modules.matchmaking.application.record_rows import (
    liveness_reason_codes,
    liveness_signal_inputs,
    modifier_rows,
    term_rows,
)
from app.modules.player_profile.domain.availability import window_of
from app.modules.player_profile.domain.ports import (
    PlayerProfileRepository,
    PlayIntentDeclarationRepository,
)
from app.modules.rating.domain.ports import SkillRatingRepository
from app.shared.ids import new_uuid


@final
@dataclass(frozen=True, slots=True)
class AnsweredCandidate:
    """One returned row, with the two field families the backend attaches.

    ``card`` and ``at_stake`` have a **different author** from everything else on
    the row — they are read after ``matchfit`` returns, over the twenty rows that
    survived rather than over the pool — and they ride the same seam for the same
    reason: neither is a fact the scorer is allowed to see, and neither may be
    computed by the client.
    """

    scored: Scored
    card: CardIdentity
    #: ``None`` in for-fun, where a counted result is **meaningless** rather than
    #: unavailable, and ``None`` today in competitive, because the result-update
    #: rule does not exist. The card draws no block either way.
    at_stake: AtStake | None


@final
@dataclass(frozen=True, slots=True)
class ShortlistAnswer:
    """What the route renders: the record, the rows, and the honest sort list."""

    record: SearchRecord
    rows: tuple[AnsweredCandidate, ...]
    sorts_available: tuple[SortOption, ...]


@final
class RunShortlistSearch:
    """The shortlist, end to end."""

    def __init__(
        self,
        *,
        clock: Clock,
        ruleset: Ruleset,
        engine: MatchFit,
        candidates: CandidateSource,
        searches: SearchStore,
        unit_of_work: UnitOfWork,
        profiles: PlayerProfileRepository,
        ratings: SkillRatingRepository,
        declarations: PlayIntentDeclarationRepository,
        blocks: BlockQuery,
        holds: AccountHoldQuery,
        account_status: AccountStatusQuery,
        history: MatchHistoryQuery,
        player_scores: PlayerScoreQuery,
        at_stake: AtStakeQuery,
        exposure: ExposureLedger,
        cards: PlayerCardSource,
        absent_terms: frozenset[Term],
    ) -> None:
        self._clock = clock
        self._ruleset = ruleset
        self._engine = engine
        self._candidates = candidates
        self._searches = searches
        self._uow = unit_of_work
        self._profiles = profiles
        self._ratings = ratings
        self._declarations = declarations
        self._blocks = blocks
        self._holds = holds
        self._account_status = account_status
        self._history = history
        self._player_scores = player_scores
        self._at_stake = at_stake
        self._exposure = exposure
        self._cards = cards
        self._absent_terms = absent_terms

    async def execute(self, command: RunShortlistSearchCommand) -> ShortlistAnswer:
        now = self._clock.now()
        stages: dict[str, int] = {}

        with _Timed(stages, "read_searcher"):
            searcher = await self._searcher_facts(command)
        await self._refuse_a_held_searcher(searcher.player_id)

        snapshot = self._candidates.snapshot(Partition.for_sport(command.sport))
        freshness = snapshot.freshness_at(now)
        if not freshness.serves:
            raise IndexTooStale(
                "the candidate index is more than a day behind the log"
            )

        with _Timed(stages, "read_gates"):
            context = await self._context(searcher, snapshot, now, command)

        with _Timed(stages, "pipeline"):
            try:
                shortlist = run(context, self._engine)
            except InvariantViolated as broken:
                raise MatchmakingUnavailable(
                    f"the matcher refused to answer: {broken}"
                ) from broken

        with _Timed(stages, "attach"):
            rows = await self._attach(shortlist.returned, context)

        returned = tuple(row.scored for row in rows)
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
            searcher_slot_count=len(searcher.grid),
            radius_clamp_bit=False,
            latency_ms_by_stage=stages,
            candidates=(
                tuple(
                    self._recorded(row, CandidateBand.RETURNED, position, context)
                    for position, row in enumerate(returned, start=1)
                )
                + tuple(
                    self._recorded(row, CandidateBand.NEAR_MISS, position, context)
                    for position, row in enumerate(shortlist.near_misses, start=1)
                )
            ),
        )
        await self._record(record)
        await self._note_exposure(command.sport, now, returned)
        return ShortlistAnswer(
            record=record,
            rows=rows,
            sorts_available=sorts_available(returned),
        )

    # -- the searcher's own facts -------------------------------------------

    async def _searcher_facts(
        self, command: RunShortlistSearchCommand
    ) -> SearcherFacts:
        """Read live from the aggregates, in the order the refusals are owed.

        The profile first, because without one there is no radius, no grid and no
        area and every later read would be answering about a search that cannot
        be run.
        """

        profile = await self._profiles.load(command.searcher_id)
        if profile is None:
            raise PlayerProfileNotCommitted(
                "the searcher has not committed a player profile"
            )
        ratings = await self._ratings.find_all_for(player_id=command.searcher_id)
        rated = next((r for r in ratings if r.sport is command.sport), None)
        if rated is None:
            raise SportNotRated(
                f"the searcher holds no rating for {command.sport.value}"
            )
        declaration = await self._declarations.load(
            player_id=command.searcher_id, sport=command.sport
        )
        if declaration is None:
            raise PlayIntentNotDeclared(
                f"the searcher has not declared a Play intent for "
                f"{command.sport.value}"
            )
        return SearcherFacts(
            player_id=command.searcher_id,
            sport=command.sport,
            mode=command.mode,
            mu=rated.mu,
            sigma=rated.sigma,
            tags=tuple(tag.value for tag in profile.social_tags.tags),
            grid=profile.availability,
            radius_km=profile.search_radius.kilometres,
            area=Point(
                latitude=profile.location.latitude,
                longitude=profile.location.longitude,
            ),
            gender=profile.gender,
            gender_preference=profile.gender_preference,
            declared_intent=declaration.intent,
            profile_created_at=profile.created_at,
        )

    async def _refuse_a_held_searcher(self, searcher_id: UUID) -> None:
        """**The hold points both ways.** A held player can still sign in."""

        held = await read_demand(
            AccountHoldQuery, lambda: self._holds.held_among([searcher_id])
        )
        if searcher_id in held:
            raise AccountHeld("this account is under a hold")

    # -- binding the context -------------------------------------------------

    async def _context(
        self,
        searcher: SearcherFacts,
        snapshot: CandidateSnapshot,
        now: Instant,
        command: RunShortlistSearchCommand,
    ) -> SearchContext:
        """Every live fact, resolved **once per search as a set**, never per row.

        The population all six reads are about is the one the bounding box
        admits, so the box is walked first to name it. Three of the reads fail
        **closed** and three fail **soft**, and which is which is not this
        method's opinion — it is the posture each port declared, applied by
        ``read_demand``.
        """

        in_box = ids_in_box(
            snapshot,
            centre=searcher.area,
            radius_km=searcher.radius_km,
            excluding=searcher.player_id,
        )
        blocked = await self._blocked(searcher.player_id)
        held = await read_demand(
            AccountHoldQuery, lambda: self._holds.held_among(in_box)
        )
        unshowable = await read_demand(
            AccountStatusQuery,
            lambda: self._account_status.may_not_be_shown(in_box),
        )
        # The stood-down answers are spelled out with their types rather than
        # as bare empties, because a soft read's fallback is a *claim* — *there
        # is no history* — and a claim with no shape is one nothing checks.
        no_challenges: tuple[OpenChallenge, ...] = ()
        no_counterparts: tuple[PairwiseCounterpart, ...] = ()
        no_loads: Mapping[UUID, int] = {}
        no_scores: Mapping[UUID, PlayerScoreReading] = {}
        challenges = await read_demand(
            MatchHistoryQuery,
            lambda: self._history.open_challenges(searcher.player_id),
            stood_down=no_challenges,
        )
        counterparts = await read_demand(
            MatchHistoryQuery,
            lambda: self._history.pairwise_counterparts(searcher.player_id),
            stood_down=no_counterparts,
        )
        loads = await read_demand(
            MatchHistoryQuery,
            lambda: self._history.open_challenge_counts(in_box),
            stood_down=no_loads,
        )
        scores = await read_demand(
            PlayerScoreQuery,
            lambda: self._player_scores.readings_for(in_box),
            stood_down=no_scores,
        )
        week = week_of(now)
        shown = await self._exposure.times_shown(
            sport=command.sport, week=week, player_ids=in_box
        )
        busy = await self._exposure.busy_threshold(sport=command.sport, week=week)
        return SearchContext(
            searcher=searcher,
            surface=SearchSurface.SHORTLIST,
            initiation=SearchInitiation.HUMAN,
            now=now,
            snapshot=snapshot,
            gates=LiveGateFacts(
                blocked_player_ids=frozenset(str(one) for one in blocked),
                held_player_ids=frozenset(str(one) for one in held),
                unshowable_player_ids=frozenset(str(one) for one in unshowable),
                open_challenge_ids=frozenset(
                    str(challenge.counterpart_id) for challenge in challenges
                ),
            ),
            terms=LiveTermFacts(
                counterparts=_by_player(counterparts),
                open_challenge_counts=loads,
                player_scores=dict(scores),
                times_shown=shown,
                busy_threshold=busy,
            ),
            ruleset=self._ruleset,
            absent_terms=self._absent_terms,
        )

    async def _blocked(self, searcher_id: UUID) -> frozenset[UUID]:
        """The searcher's live block set. **Fails closed, like every safety gate.**

        ``BlockQuery`` declares its posture where the port lives rather than in
        the matcher's table, so it is translated here into the matcher's own
        refusal — a 503 about the platform, distinct from the 403 about *you*.
        """

        try:
            return await self._blocks.exclusions_for(searcher_id)
        except BlockStateUnavailable as unavailable:
            raise GateDataUnavailable(
                "the block set could not be evaluated"
            ) from unavailable

    # -- the two families with a different author ----------------------------

    async def _attach(
        self, returned: tuple[Scored, ...], context: SearchContext
    ) -> tuple[AnsweredCandidate, ...]:
        """The player card and the at-stake block, after the scorer returned.

        A row whose card cannot be assembled is dropped **here**, before the
        record is built, so that ``n_returned`` and the number of ``RETURNED``
        rows written agree — which is the whole of what makes ``n_returned`` a
        redaction detector later.
        """

        identities = await self._cards.identities_for(
            [UUID(row.player_id) for row in returned]
        )
        rows: list[AnsweredCandidate] = []
        for row in returned:
            card = identities.get(UUID(row.player_id))
            if card is None:
                continue
            rows.append(
                AnsweredCandidate(
                    scored=row,
                    card=card,
                    at_stake=await self._at_stake_for(row, context),
                )
            )
        return tuple(rows)

    async def _at_stake_for(
        self, row: Scored, context: SearchContext
    ) -> AtStake | None:
        """What a **counted** game against this opponent would be worth.

        Omitted in for-fun by the method's own name rather than by a flag: a
        for-fun game is never counted, so the figure is not
        absent-because-unavailable, it is meaningless, and asking about it is a
        category error.
        """

        if context.searcher.mode is not SearchMode.COMPETITIVE:
            return None
        return await read_demand(
            AtStakeQuery,
            lambda: self._at_stake.counted_game_deltas(
                searcher_id=context.searcher.player_id,
                opponent_id=UUID(row.player_id),
                sport=context.searcher.sport,
            ),
            stood_down=None,
        )

    # -- the record ----------------------------------------------------------

    def _recorded(
        self,
        row: Scored,
        band: CandidateBand,
        position: int,
        context: SearchContext,
    ) -> SearchCandidateRecord:
        floor = self._ruleset.floors.quality_floor
        return SearchCandidateRecord(
            band=band,
            position=position,
            player_id=UUID(row.player_id),
            fit=row.modified.points,
            terms=term_rows(row.fit),
            degraded_terms=tuple(term.value for term in row.fit.degraded_terms),
            modifiers=modifier_rows(row.modified.modifiers),
            liveness_reasons=liveness_reason_codes(row.liveness),
            liveness_signals=liveness_signal_inputs(row),
            shared_count=row.generated.overlap.shared_count,
            their_slot_count=len(row.generated.row.availability),
            days_away=row.generated.overlap.days_away,
            inclusion_reason=row.inclusion_reason,
            withheld_reason=row.withheld_reason,
            missing_terms=row.missing_terms,
            reliability_penalty_applied=row.reliability_penalty_applied,
            reliability_penalty_decisive=row.reliability_penalty_decisive(floor),
        )

    async def _record(self, record: SearchRecord) -> None:
        """Write it, and commit it, **before** the answer goes anywhere."""

        try:
            await self._searches.record(record)
            await self._uow.commit()
        except Exception as failure:
            raise SearchNotRecorded(
                "the search could not be recorded, so it is not returned"
            ) from failure

    async def _note_exposure(
        self, sport: Sport, now: Instant, returned: tuple[Scored, ...]
    ) -> None:
        """Add one appearance each to the week's bucket. **After the commit.**

        The ledger is the *gate* and the row is the *evidence*: this write is a
        courtesy that shapes tomorrow's ordering, and losing it costs a slightly
        duller list. It is deliberately outside the transaction and outside the
        refusal above — a search that ran and was recorded is a search that
        happened, whatever Redis thought.
        """

        await self._exposure.record_shown(
            sport=sport,
            week=week_of(now),
            player_ids=[UUID(row.player_id) for row in returned],
        )


def _counts(shortlist: Shortlist, n_returned: int) -> StagedCounts:
    """The staged counts, with ``n_returned`` taken from the rows actually sent.

    It is the count **after** a card could not be assembled, not before, because
    the column's second job is detecting an erasure that removed a candidate row
    from a search that survived — and a detector seeded with a number that never
    matched would report a redaction on the day it shipped.
    """

    return replace(shortlist.counts, n_returned=n_returned)


def _by_player(
    counterparts: Collection[PairwiseCounterpart],
) -> Mapping[UUID, PairwiseCounterpart]:
    return {counterpart.player_id: counterpart for counterpart in counterparts}


class _Timed:
    """Milliseconds spent in one stage, recorded on the search row.

    The operational half of the telemetry, and the one part of the record that is
    about the machine rather than about the people. A context manager rather than
    a decorator so that a stage is a *span of this method*, which is what the
    column means.
    """

    def __init__(self, into: dict[str, int], stage: str) -> None:
        self._into = into
        self._stage = stage
        self._started = 0.0

    def __enter__(self) -> "_Timed":
        self._started = time.monotonic()
        return self

    def __exit__(self, *_: object) -> None:
        elapsed = (time.monotonic() - self._started) * 1000.0
        self._into[self._stage] = int(elapsed)
