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
from app.kernel import Clock, Instant, InvariantViolated, Sport, invariant
from app.modules.blocks.domain.ports import BlockQuery
from app.modules.matchmaking.application.commands import RunShortlistSearchCommand
from app.modules.matchmaking.application.outward_reads import (
    live_block_set,
    read_demand,
)
from app.modules.matchmaking.domain.cards import CardIdentity, PlayerCardSource
from app.modules.matchmaking.domain.candidate_index import Partition
from app.modules.matchmaking.domain.candidate_snapshot import (
    CandidateSnapshot,
    CandidateSource,
)
from app.modules.matchmaking.domain.errors import (
    AccountHeld,
    IndexTooStale,
    MatchmakingUnavailable,
    PlayerProfileNotCommitted,
    PlayIntentNotDeclared,
    RungOfferNotFound,
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
from app.modules.matchmaking.domain.prompts import (
    REPEATED_WIDENINGS,
    Prompt,
    PromptLedger,
    RaisedPrompt,
)
from app.modules.matchmaking.domain.relaxation import (
    Rung,
    RungOffer,
    radius_ladder,
)
from app.modules.matchmaking.domain.search_store import SearchStore
from app.modules.matchmaking.domain.searches import (
    CandidateBand,
    PoolDescription,
    RecordedCard,
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
from app.modules.matchmaking.domain.sorting import of_scored, sorts_available
from app.modules.matchmaking.domain.widening import Ladder, ladder_for
from app.modules.matchmaking.application.record_rows import (
    liveness_reason_codes,
    liveness_signal_inputs,
    modifier_rows,
    term_rows,
)
from app.modules.player_profile.domain.availability import (
    AvailabilityGrid,
    AvailabilitySlot,
    window_of,
)
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

    def recorded_card(self) -> RecordedCard:
        """The card as it was shown, from the two sources that assembled it.

        The nickname and the photo id come from ``users`` through
        :class:`PlayerCardSource`; the area, the tags, the Level and its band are
        already on the index row, because those are facts a player changes about
        themselves. Assembled once, here, and **both the response and the
        read-back render this one** — so the card on the wire and the card in the
        record cannot disagree about what was shown.
        """

        indexed = self.scored.generated.row
        return RecordedCard(
            nickname=self.card.nickname,
            photo_id=self.card.photo_id,
            area_code=self.scored.fenced.area_code,
            social_tags=tuple(indexed.social_tags),
            level=indexed.mu,
            band=indexed.band,
        )


@final
@dataclass(frozen=True, slots=True)
class _AskedFor:
    """The two asks this one search runs on, and where they came from.

    ``rung_taken`` and ``offered_by_search_id`` are set together or not at all:
    **an accepted widen is a new search citing the one that offered it**, and the
    pair is what makes take-up per rung a join over two rows rather than a flag
    on one that could be written without the other.
    """

    grid: AvailabilityGrid
    radius_km: int
    rung_taken: Rung | None = None
    offered_by_search_id: UUID | None = None


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
        prompts: PromptLedger,
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
        self._prompts = prompts
        self._absent_terms = absent_terms

    async def execute(self, command: RunShortlistSearchCommand) -> ShortlistAnswer:
        now = self._clock.now()
        stages: dict[str, int] = {}

        with _Timed(stages, "read_searcher"):
            declared = await self._searcher_facts(command)
        await self._refuse_a_held_searcher(declared.player_id)

        # **What this one search runs on**, which is the profile's own answer
        # unless the player asked otherwise: a grid they improvised on the search
        # screen, or the widening a rung offer promised them. Applied here, once,
        # so that everything downstream — the box, the radius gate, the distance
        # term, the availability denominator, the window and the recorded grid —
        # reads one set of facts and cannot disagree about what was asked for.
        asked = await self._asked_for(command, declared)
        searcher = replace(declared, grid=asked.grid, radius_km=asked.radius_km)

        snapshot = self._candidates.snapshot(Partition.for_sport(command.sport))
        freshness = snapshot.freshness_at(now)
        if not freshness.serves:
            raise IndexTooStale(
                "the candidate index is more than a day behind the log"
            )

        # *Is this a newcomer's search* is decided once, here, and handed to
        # both halves of the absorption tally. The read skips and the write
        # happens on one answer, so the bucket cannot be read on a search that
        # will not add to it, or added to on a search that never read it.
        for_a_newcomer = searcher.is_new_at(now)

        with _Timed(stages, "read_gates"):
            context = await self._context(
                searcher, snapshot, now, command, for_a_newcomer
            )

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
        with _Timed(stages, "relaxation"):
            ladder = self._ladder(context, shortlist, shown=len(rows))
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
            candidates=(
                tuple(
                    self._recorded(
                        row.scored,
                        CandidateBand.RETURNED,
                        position,
                        card=row.recorded_card(),
                        at_stake=row.at_stake,
                    )
                    for position, row in enumerate(rows, start=1)
                )
                + tuple(
                    self._recorded(
                        row,
                        CandidateBand.NEAR_MISS,
                        position,
                        # A near miss was shown to nobody, so there is no card to
                        # record and no counted game to price: neither was ever
                        # read for this row.
                        card=None,
                        at_stake=None,
                    )
                    for position, row in enumerate(shortlist.near_misses, start=1)
                )
            ),
        )
        await self._record(record)
        await self._note_exposure(command.sport, now, returned, for_a_newcomer)
        return ShortlistAnswer(
            record=record,
            sorts_available=sorts_available(
                tuple(of_scored(row) for row in returned)
            ),
            # After the commit, deliberately. A prompt is a courtesy read over a
            # row that now exists — *how often have I taken this widening* counts
            # this search too — and a question the platform could not ask is
            # never a reason to fail a search that ran.
            prompts=await self._raised(command, asked, profile_grid=declared.grid),
        )

    # -- what this one search was asked for ----------------------------------

    async def _asked_for(
        self, command: RunShortlistSearchCommand, searcher: SearcherFacts
    ) -> "_AskedFor":
        """The grid and the radius this search runs on. **Never a profile edit.**

        Two asks can move them, and neither writes anything: a grid the player
        edited on the search screen for this evening, and a rung offer they took.
        The profile keeps its own answers, and the app offers to save either one
        afterwards through the routes that own those fields (``docs/adr/0099``
        §3).

        **The widening is read off the offering search's record and never off the
        request.** That is what keeps *there is no per-search radius input* true:
        the only radius this backend will run a search at is one it published
        itself, on a row it wrote.
        """

        grid = (
            searcher.grid
            if command.availability_override is None
            else AvailabilityGrid.of_cells(command.availability_override)
        )
        if command.rung is None and command.offered_by_search_id is None:
            return _AskedFor(grid=grid, radius_km=searcher.radius_km)
        if command.rung is None or command.offered_by_search_id is None:
            raise RungOfferNotFound(
                "a rung and the search that offered it travel together"
            )
        offer = await self._cited_offer(
            command, command.offered_by_search_id, command.rung
        )
        # The ask decides which payload is there, and ``RungOffer``'s own
        # invariant is what makes that a fact rather than a hope: a ``RADIUS``
        # rung holds a radius and no slot, and a ``TIMES`` rung the reverse.
        if offer.radius_km is not None:
            return _AskedFor(
                grid=grid,
                radius_km=offer.radius_km,
                rung_taken=command.rung,
                offered_by_search_id=command.offered_by_search_id,
            )
        invariant(
            offer.slot is not None,
            f"a {offer.ask.value} rung offering neither a radius nor a slot",
        )
        slot = AvailabilitySlot.from_code(offer.slot or "")
        return _AskedFor(
            # A set, so a client that also sent the widened grid as its override
            # lands in exactly the same place as one that sent nothing.
            grid=AvailabilityGrid.of((*grid.slots, slot)),
            radius_km=searcher.radius_km,
            rung_taken=command.rung,
            offered_by_search_id=command.offered_by_search_id,
        )

    async def _cited_offer(
        self, command: RunShortlistSearchCommand, search_id: UUID, rung: Rung
    ) -> RungOffer:
        """The offer this search claims to be accepting, from the row that made it.

        Four ways this refuses, and they are one code on purpose: the search does
        not exist, it belongs to somebody else, it computed no offers, or it
        offered no such rung. Telling them apart would answer *does this
        ``search_id`` exist* for a stranger's id, which is the question the
        read-back's own 404 already declines to answer.
        """

        cited = await self._searches.find(
            search_id=search_id, searcher_id=command.searcher_id
        )
        if cited is not None and cited.sport is command.sport:
            for offer in cited.rung_offers or ():
                if offer.rung is rung:
                    return offer
        raise RungOfferNotFound(f"no rung {rung.value} was offered by that search")

    # -- the ladder ----------------------------------------------------------

    def _ladder(
        self, context: SearchContext, shortlist: Shortlist, *, shown: int
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
        """

        if shown >= self._ruleset.floors.min_shortlist:
            return None
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
        asked: "_AskedFor",
        *,
        profile_grid: AvailabilityGrid,
    ) -> tuple[RaisedPrompt, ...]:
        """Every question this search raises. **None of them changes a value.**

        Two are facts about this search and are free here; two were computed by a
        loop and are one lookup. The order is the vocabulary's own, so a client
        rendering the first one it understands gets the same one twice for the
        same search.
        """

        raised: list[RaisedPrompt] = []
        if asked.grid != profile_grid:
            raised.append(
                RaisedPrompt(
                    prompt=Prompt.KEEP_THESE_TIMES, slots=asked.grid.codes
                )
            )
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
        return tuple(raised)

    async def _keeps_taking_this_widening(
        self, command: RunShortlistSearchCommand, asked: "_AskedFor"
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
        for_a_newcomer: bool,
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
        blocked = await live_block_set(self._blocks, searcher.player_id)
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
        # The absorption tally is read on a newcomer's search and on no other,
        # because that is the only search the cap can bind in — and skipping the
        # read is why the empty mapping on every other search means *not asked*
        # rather than *nobody has absorbed anything*.
        absorption: Mapping[UUID, int] = {}
        if for_a_newcomer:
            absorption = await self._exposure.times_shown_to_a_newcomer(
                sport=command.sport, week=week, player_ids=in_box
            )
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
                newcomer_appearances=absorption,
                busy_threshold=busy,
            ),
            ruleset=self._ruleset,
            absent_terms=self._absent_terms,
        )

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
        *,
        card: RecordedCard | None,
        at_stake: AtStake | None,
    ) -> SearchCandidateRecord:
        """One row of the record — **the whole row that was shown, not a summary.**

        The card, the at-stake block and the distance are recorded beside the
        breakdown because none of the three can be reconstructed later: a
        nickname changes, a Level moves, a player leaves an area, and a Level
        delta is priced against ratings that keep moving. A read-back that
        re-read them would answer a different search and call it the same one
        (``docs/adr/0109``).
        """

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
            concerns=tuple(term.value for term in row.fit.concerns),
            # ``None`` and never a zero when the term stood down, decided once on
            # ``Scored`` so the recorded row, the response and the sort cannot
            # come to three answers about one distance.
            distance_km=row.shown_distance_km,
            card=card,
            at_stake=at_stake,
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
        self,
        sport: Sport,
        now: Instant,
        returned: tuple[Scored, ...],
        for_a_newcomer: bool,
    ) -> None:
        """Add one appearance each to the week's bucket. **After the commit.**

        The ledger is the *gate* and the row is the *evidence*: this write is a
        courtesy that shapes tomorrow's ordering, and losing it costs a slightly
        duller list. It is deliberately outside the transaction and outside the
        refusal above — a search that ran and was recorded is a search that
        happened, whatever Redis thought.

        **A newcomer's search writes both families**, over the same rows: being
        volunteered into a newcomer's list is being shown, plus one further fact
        about who was looking. Two writes rather than a flag on one, because they
        are two counts and the cap reads only the second.
        """

        week = week_of(now)
        shown = [UUID(row.player_id) for row in returned]
        await self._exposure.record_shown(sport=sport, week=week, player_ids=shown)
        if for_a_newcomer:
            await self._exposure.record_shown_to_a_newcomer(
                sport=sport, week=week, player_ids=shown
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
