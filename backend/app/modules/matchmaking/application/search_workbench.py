"""What every surface does the same way, around the stage that differs.

**Stages 1 to 6 are shared by every surface and only the terminal stage
differs** (``shortlist.py``). The same is true one layer out, in the I/O: reading
the searcher live from the aggregates, binding one snapshot with every live gate
fact, attaching the two field families the scorer may not see, writing the record
and committing it before the answer goes anywhere, and noting exposure
afterwards. A shortlist and a deal differ in what they *ask for* and in how they
*order* — not in any of that.

So it is here, once, and the two use cases hold one of these rather than a copy
of it. Two implementations of *bind a search context* would be two answers to
which reads fail closed, and the one that drifted would be the one that quietly
softened a gate.

**What is deliberately not here** is everything a surface decides for itself: the
mode (a shortlist takes it from the request, a deck reads a declaration), the
exclusions, the order, the relaxation ladder — which does not reach the deck at
all — and the prompts. A workbench that decided any of those would be the second
implementation this one exists to prevent, wearing a helpful name.

**The order the caller must keep is still the caller's**, and it is stated in
each use case: read the searcher, bind once, run the pipeline, record and commit,
then write exposure *after* the commit. This class makes each step available; it
does not make them happen in that order, because the order is the thing each
surface is answerable for.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Collection, Mapping, final
from uuid import UUID

from app.application.ports import UnitOfWork
from app.engines.matchfit.core import SearchMode, Term
from app.engines.matchfit.ruleset import Ruleset
from app.kernel import Clock, Instant, Sport, invariant
from app.modules.blocks.domain.ports import BlockQuery
from app.modules.matchmaking.application.outward_reads import (
    live_block_set,
    read_demand,
)
from app.modules.matchmaking.domain.cards import (
    CardIdentity,
    CardRecord,
    PlayerCardSource,
    PlayerRecordSource,
)
from app.modules.matchmaking.domain.candidate_index import Partition
from app.modules.matchmaking.domain.candidate_snapshot import (
    CandidateSnapshot,
    CandidateSource,
)
from app.modules.matchmaking.domain.index_staleness import IndexFreshness
from app.modules.matchmaking.domain.errors import (
    RungOfferNotFound,
    IndexTooStale,
    PlayerProfileNotCommitted,
    PlayIntentNotDeclared,
    SearchNotRecorded,
    SportNotRated,
)
from app.modules.matchmaking.domain.geography import Point
from app.modules.matchmaking.domain.interest import InterestLedger
from app.modules.matchmaking.domain.relaxation import Rung, RungOffer
from app.modules.matchmaking.domain.scale_triggers import ScoringInstrument
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
    RecordedCard,
    SearchCandidateRecord,
    SearchInitiation,
    SearchRecord,
    SearchSurface,
)
from app.modules.matchmaking.domain.shortlist import Scored, ids_in_box
from app.modules.matchmaking.application.record_rows import (
    liveness_reason_codes,
    liveness_signal_inputs,
    modifier_rows,
    term_rows,
)
from app.modules.player_profile.domain.availability import (
    AvailabilityGrid,
    AvailabilitySlot,
)
from app.modules.player_profile.domain.play_intent import PlayIntent
from app.modules.player_profile.domain.ports import (
    PlayerProfileRepository,
    PlayIntentDeclarationRepository,
)
from app.modules.rating.domain.ports import SkillRatingRepository
from app.shared.domain.errors import AccountHeld


@final
@dataclass(frozen=True, slots=True)
class AskedFor:
    """The two asks this one search runs on, and where they came from.

    **On the workbench rather than in a use case**, because two surfaces take a
    rung offer — the shortlist and the line-up — and *reading what was asked for*
    is not what they disagree about. What each surface decides for itself is
    whether to **price** a ladder, which is the expensive half and stays theirs.

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
class AnsweredCandidate:
    """One returned row, with the two field families the backend attaches.

    ``card``, ``record`` and ``at_stake`` have a **different author** from
    everything else on the row — they are read after ``matchfit`` returns, over
    the twenty rows that survived rather than over the pool — and they ride the
    same seam for the same reason: none of them is a fact the scorer is allowed
    to see, and none may be computed by the client.
    """

    scored: Scored
    card: CardIdentity
    #: What the platform watched them do on court, or ``None`` where it has
    #: watched nothing. **An absence and never a nought**: somebody with no
    #: counted game has not lost five.
    record: CardRecord | None
    #: Their **published** Player Score, or ``None`` where the platform has
    #: watched nothing — read at assembly time and **not** off the fence, which
    #: is ``docs/adr/0140`` §6: the engine's own reading is a separate read for a
    #: separate purpose, bounded by the box where this one is bounded by the
    #: shortlist. Reaching into ``Scored`` for it would make the card's figure a
    #: consequence of whatever the reliability term happens to carry.
    player_score: int | None
    #: ``None`` in for-fun, where a counted result is **meaningless** rather than
    #: unavailable. In competitive it is the rating engine's own update rule read
    #: forward (``docs/adr/0139``), and ``None`` only where one of the two holds
    #: no rating in this sport.
    at_stake: AtStake | None

    def recorded_card(self) -> RecordedCard:
        """The card as it was shown, from the sources that assembled it.

        The nickname, the photo id and that photo's on-court verdict come from
        ``users``, the Player profile and the photo store through
        :class:`PlayerCardSource`; the area, the tags, the Level and its band are
        already on the index row, because those are facts a player changes about
        themselves. Assembled once, here, and **both the response and the
        read-back render this one** — so the card on the wire and the card in the
        record cannot disagree about what was shown.

        The verdict is copied down like every other fact and **never re-read on
        the way back out** (``docs/adr/0138``): it costs a store round trip, and
        a read-back that paid it would answer with the shield the backfill has
        since earned rather than the one the searcher saw.

        **The record block comes from two more providers and neither is the
        index** (``docs/adr/0111``: the index holds only what a player changes
        about themselves, and none of these is that). The counted games and the
        run of form are ``games``' through :class:`PlayerRecordSource`; the
        Player Score is ``player_score``'s through ``PlayerScoreQuery``. Both
        arrive **already read**, on :class:`AnsweredCandidate`, because assembly
        is a mapping and the reads are the workbench's.

        **Nought counted games is not a figure, it is an absence.** ``games``
        answers a measured zero and the card does not print one: on this surface
        *no games* and *no record* would be two spellings of one thing, and the
        whole discipline of the card is that absence has one.
        """

        indexed = self.scored.generated.row
        return RecordedCard(
            nickname=self.card.nickname,
            photo_id=self.card.photo_id,
            review=self.card.review,
            area_code=self.scored.fenced.area_code,
            social_tags=tuple(indexed.social_tags),
            level=indexed.mu,
            band=indexed.band,
            # **Read off the row, never recomputed** — see
            # `CandidateRow.range_low` for why assembly may not derive it.
            range_low=indexed.range_low,
            range_high=indexed.range_high,
            player_score=self.player_score,
            counted_games=None if self.record is None else self.record.counted_games,
            last_five=() if self.record is None else self.record.last_five,
        )


#: The stage every surface runs the engine inside, and the one trigger 1 is
#: read over. Named once because two spellings of it would be a search row and
#: an instrument measuring two different things under one word.
PIPELINE_STAGE = "pipeline"


@final
class SearchWorkbench:
    """The reads, the writes and the two attachments every surface shares."""

    def __init__(
        self,
        *,
        clock: Clock,
        ruleset: Ruleset,
        searches: SearchStore,
        unit_of_work: UnitOfWork,
        profiles: PlayerProfileRepository,
        ratings: SkillRatingRepository,
        declarations: PlayIntentDeclarationRepository,
        candidates: CandidateSource,
        blocks: BlockQuery,
        holds: AccountHoldQuery,
        account_status: AccountStatusQuery,
        history: MatchHistoryQuery,
        player_scores: PlayerScoreQuery,
        at_stake: AtStakeQuery,
        exposure: ExposureLedger,
        interest: InterestLedger,
        cards: PlayerCardSource,
        records: PlayerRecordSource,
        absent_terms: frozenset[Term],
        meter: ScoringInstrument | None = None,
    ) -> None:
        self._clock = clock
        self._ruleset = ruleset
        self._searches = searches
        self._uow = unit_of_work
        self._profiles = profiles
        self._ratings = ratings
        self._declarations = declarations
        self._candidates = candidates
        self._blocks = blocks
        self._holds = holds
        self._account_status = account_status
        self._history = history
        self._player_scores = player_scores
        self._at_stake = at_stake
        self._exposure = exposure
        self._interest = interest
        self._cards = cards
        self._records = records
        self._absent_terms = absent_terms
        self._meter = meter

    @property
    def clock(self) -> Clock:
        """The one clock a surface may read ``now`` from.

        Exposed rather than injected twice, so that the moment a search is
        stamped with and the moment its ledger reads are bounded by cannot be two
        readings of two clocks.
        """

        return self._clock

    def timed(self, into: dict[str, int], stage: str) -> "Timed":
        """Time one stage into the map that becomes ``latency_ms_by_stage``."""

        return Timed(into, stage)

    def scoring(self, into: dict[str, int]) -> "Timed":
        """Time the **scoring call** — the stage trigger 1 is read over.

        The same span ``latency_ms_by_stage["pipeline"]`` already records, and
        deliberately so: ``scale-posture.md`` §4's *histogram around the scoring
        call* and the search row's own operational half must be one measurement,
        or the day they disagree there is no way to tell which of them is the
        cost of a search.

        Every surface calls this instead of ``timed(stages, "pipeline")``, so a
        surface that is added later is instrumented by using the workbench —
        which is the only thing that keeps a per-worker instrument complete.
        """

        return Timed(into, PIPELINE_STAGE, meter=self._meter)

    # -- the index, bound once ------------------------------------------------

    def bound_snapshot(
        self, sport: Sport, now: Instant
    ) -> tuple[CandidateSnapshot, IndexFreshness]:
        """This process's index for one sport, or a refusal about its lag.

        **Bound once, here, and never re-read** (``docs/adr/0112``): after this
        line a refresh rebinds the source's own pointer and cannot move the
        container a running search is holding.

        Past twenty-four hours the ladder refuses rather than serving, and the
        refusal stands on **quality rather than safety** — every fact staleness
        can cost is a fact about who is *worth* meeting, because the facts that
        must be live never enter the index at all (``docs/adr/0111``). Between
        fifteen minutes and a day the search is served and the flag recorded,
        which is why the freshness travels back rather than being consumed here.
        """

        snapshot = self._candidates.snapshot(Partition.for_sport(sport))
        freshness = snapshot.freshness_at(now)
        if not freshness.serves:
            raise IndexTooStale(
                "the candidate index is more than a day behind the log"
            )
        return snapshot, freshness

    # -- the searcher's own facts -------------------------------------------

    async def searcher_facts(
        self,
        *,
        player_id: UUID,
        sport: Sport,
        mode_of: Callable[[PlayIntent], SearchMode],
    ) -> SearcherFacts:
        """Read live from the aggregates, in the order the refusals are owed.

        The profile first, because without one there is no radius, no grid and no
        area and every later read would be answering about a search that cannot
        be run.

        **The mode is a function of the declaration, and each surface says which
        function**, because that is exactly what the two surfaces disagree about.
        A shortlist's is a constant — which tab you are on, decided before
        anything was read — and the deck's is
        ``matchmaking/domain/deck.py``'s ``mode_for_intent``, mapping the viewer's
        own declaration and never selecting a third vector. Passing a function
        rather than a value is what keeps it **one read**: the declaration the
        mode was chosen from is the declaration recorded as ``intent_read``, and
        there is no second load for the two to disagree across.
        """

        profile = await self._profiles.load(player_id)
        if profile is None:
            raise PlayerProfileNotCommitted(
                "the searcher has not committed a player profile"
            )
        ratings = await self._ratings.find_all_for(player_id=player_id)
        rated = next((r for r in ratings if r.sport is sport), None)
        if rated is None:
            raise SportNotRated(
                f"the searcher holds no rating for {sport.value}"
            )
        declaration = await self._declarations.load(
            player_id=player_id, sport=sport
        )
        if declaration is None:
            raise PlayIntentNotDeclared(
                f"the searcher has not declared a Play intent for "
                f"{sport.value}"
            )
        return SearcherFacts(
            player_id=player_id,
            sport=sport,
            mode=mode_of(declaration.intent),
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

    async def refuse_a_held_searcher(self, searcher_id: UUID) -> None:
        """**The hold points both ways.** A held player can still sign in."""

        held = await read_demand(
            AccountHoldQuery, lambda: self._holds.held_among([searcher_id])
        )
        if searcher_id in held:
            raise AccountHeld("this account is under a hold")

    # -- what one search was asked for ---------------------------------------

    async def asked_for(
        self,
        searcher: SearcherFacts,
        *,
        availability_override: tuple[tuple[int, str], ...] | None,
        offered_by_search_id: UUID | None,
        rung: Rung | None,
    ) -> AskedFor:
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

        # **``edited`` and never ``of_cells``.** The floor of one ticked cell
        # binds *the answer a player is asked for* at commit, and an improvised
        # week is a later edit of it — so a player who clears their week
        # searches, exactly as ``availability.py`` says they may. Building this
        # through the commit path's constructor enforced the floor one layer
        # past where that module puts it, and refused them a `400`.
        grid = (
            searcher.grid
            if availability_override is None
            else AvailabilityGrid.edited(availability_override)
        )
        if rung is None and offered_by_search_id is None:
            return AskedFor(grid=grid, radius_km=searcher.radius_km)
        if rung is None or offered_by_search_id is None:
            raise RungOfferNotFound(
                "a rung and the search that offered it travel together"
            )
        offer = await self._cited_offer(searcher, offered_by_search_id, rung)
        # The ask decides which payload is there, and ``RungOffer``'s own
        # invariant is what makes that a fact rather than a hope: a ``RADIUS``
        # rung holds a radius and no slot, and a ``TIMES`` rung the reverse.
        if offer.radius_km is not None:
            return AskedFor(
                grid=grid,
                radius_km=offer.radius_km,
                rung_taken=rung,
                offered_by_search_id=offered_by_search_id,
            )
        invariant(
            offer.slot is not None,
            f"a {offer.ask.value} rung offering neither a radius nor a slot",
        )
        slot = AvailabilitySlot.from_code(offer.slot or "")
        return AskedFor(
            # A set, so a client that also sent the widened grid as its override
            # lands in exactly the same place as one that sent nothing.
            grid=AvailabilityGrid.of((*grid.slots, slot)),
            radius_km=searcher.radius_km,
            rung_taken=rung,
            offered_by_search_id=offered_by_search_id,
        )

    async def _cited_offer(
        self, searcher: SearcherFacts, search_id: UUID, rung: Rung
    ) -> RungOffer:
        """The offer this search claims to be accepting, from the row that made it.

        Four ways this refuses, and they are one code on purpose: the search does
        not exist, it belongs to somebody else, it computed no offers, or it
        offered no such rung. Telling them apart would answer *does this
        ``search_id`` exist* for a stranger's id, which is the question the
        read-back's own 404 already declines to answer.
        """

        cited = await self._searches.find(
            search_id=search_id, searcher_id=searcher.player_id
        )
        if cited is not None and cited.sport is searcher.sport:
            for offer in cited.rung_offers or ():
                if offer.rung is rung:
                    return offer
        raise RungOfferNotFound(f"no rung {rung.value} was offered by that search")

    # -- binding the context -------------------------------------------------

    def population(
        self, searcher: SearcherFacts, snapshot: CandidateSnapshot
    ) -> tuple[UUID, ...]:
        """Everybody the bounding box admits. **Walked once, and handed on.**

        Every live read below is a set read *over a population*, and this is the
        population they are all about. It is returned to the caller rather than
        kept private because a surface with exclusions of its own — the deck —
        asks its own ledgers about exactly these people, and a second walk would
        be a second chance for two answers to be about two different sets.
        """

        return ids_in_box(
            snapshot,
            centre=searcher.area,
            radius_km=searcher.radius_km,
            excluding=searcher.player_id,
        )

    async def bind(
        self,
        searcher: SearcherFacts,
        snapshot: CandidateSnapshot,
        now: Instant,
        *,
        in_box: tuple[UUID, ...],
        surface: SearchSurface,
        initiation: SearchInitiation,
        for_a_newcomer: bool,
        completing_challenge_id: UUID | None,
    ) -> SearchContext:
        """Every live fact, resolved **once per search as a set**, never per row.

        The population every read is about is the one the bounding box admits,
        which :meth:`population` walked and the caller passes in. Three of the
        outward reads fail
        **closed** and four fail **soft**, and which is which is not this
        method's opinion — it is the posture each port declared, applied by
        ``read_demand``. The two ledgers below are the module's own and carry
        their posture in the wrapper around them; the interest ledger is the
        module's own too and is **durable**, so it fails like the record does.

        ``completing_challenge_id`` is the **one** challenge the open-challenge
        gate steps aside for (``docs/adr/0150`` §3). It is **stated by every
        caller and never defaulted**, which is ``standing_of``'s rule one context
        over: a surface added later has to say which challenge it is exempting,
        rather than inheriting an answer from a default nobody chose. It is an
        argument rather than a condition reconstructed here: a reader asking why
        this search can see the people it is arranging with finds the answer in
        the call. The
        gate is not weakened and its meaning does not move — it still excludes
        everybody the searcher is arranging with, **except the people already
        sitting on the court this search exists to finish**, which is the same
        rule read correctly. The other three surfaces pass ``None`` and get the
        gate they always had.
        """

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
        # **A durable read, beside two lossy ones, and it does not fail soft.**
        # The ledgers below may answer nothing and cost a search its spread; this
        # one may not, because it is the only read that can *admit* somebody. A
        # yes silently unread is a person the product guaranteed a place to and
        # then dropped, which is the failure ``docs/adr/0127`` made the lift flat
        # to keep visible. It lives in this module's own database, so if it
        # cannot be read the record cannot be written either.
        said_lets_play = await self._interest.days_ago_towards(
            player_id=searcher.player_id,
            sport=searcher.sport,
            senders=in_box,
            now=now,
        )
        week = week_of(now)
        shown = await self._exposure.times_shown(
            sport=searcher.sport, week=week, player_ids=in_box
        )
        busy = await self._exposure.busy_threshold(sport=searcher.sport, week=week)
        # The absorption tally is read on a newcomer's search and on no other,
        # because that is the only search the cap can bind in — and skipping the
        # read is why the empty mapping on every other search means *not asked*
        # rather than *nobody has absorbed anything*.
        absorption: Mapping[UUID, int] = {}
        if for_a_newcomer:
            absorption = await self._exposure.times_shown_to_a_newcomer(
                sport=searcher.sport, week=week, player_ids=in_box
            )
        return SearchContext(
            searcher=searcher,
            surface=surface,
            initiation=initiation,
            now=now,
            snapshot=snapshot,
            gates=LiveGateFacts(
                blocked_player_ids=frozenset(str(one) for one in blocked),
                held_player_ids=frozenset(str(one) for one in held),
                unshowable_player_ids=frozenset(str(one) for one in unshowable),
                open_challenge_ids=frozenset(
                    str(challenge.counterpart_id)
                    for challenge in challenges
                    # **The exemption is a smaller set, never a gate that fired
                    # and was ignored.** ``GATE_ROSTER`` is unchanged, the
                    # histogram still counts ten codes, and a court member
                    # excluded for any of the other nine still falls out.
                    if challenge.challenge_id != completing_challenge_id
                ),
            ),
            terms=LiveTermFacts(
                counterparts=_by_player(counterparts),
                open_challenge_counts=loads,
                player_scores=dict(scores),
                times_shown=shown,
                interest_days_ago=said_lets_play,
                newcomer_appearances=absorption,
                busy_threshold=busy,
            ),
            ruleset=self._ruleset,
            absent_terms=self._absent_terms,
        )

    # -- the two families with a different author ----------------------------

    async def attach(
        self, returned: tuple[Scored, ...], context: SearchContext
    ) -> tuple[AnsweredCandidate, ...]:
        """The player card and the at-stake block, after the scorer returned.

        A row whose card cannot be assembled is dropped **here**, before the
        record is built, so that ``n_returned`` and the number of ``RETURNED``
        rows written agree — which is the whole of what makes ``n_returned`` a
        redaction detector later.

        **Three batched reads over the surviving rows, and never one per row** —
        the shape every set read in this module has. All three run after the
        floor, so each is bounded by twenty players even when the pool was five
        hundred.

        **The Player Score is read again here, and the second read is the
        decision rather than an oversight** (``docs/adr/0140`` §6). The engine
        already read it through the same port when the context was bound, but
        *that* read is a separate read for a separate purpose and is **bounded by
        the box**: it prices a term over everybody who might be scored. This one
        is bounded by the shortlist and prints a number. Taking the card's figure
        off ``Scored.fenced`` instead would make what a player is shown a
        consequence of whatever the reliability term happens to carry, and the
        day that record is narrowed the card would quietly stop saying anything.
        """

        wanted = [UUID(row.player_id) for row in returned]
        identities = await self._cards.identities_for(wanted)
        records = await self._records.records_for(wanted)
        # **Not through ``read_demand``**, like the two reads above it and unlike
        # every read the *context* binds. A stood-down term is a search with one
        # fewer term in it; a stood-down card block would publish *the platform
        # has watched nothing of these twenty people*, which is a claim. An
        # outage refuses here, exactly as an unreadable nickname does.
        scores = await self._player_scores.readings_for(wanted)
        rows: list[AnsweredCandidate] = []
        for row in returned:
            player_id = UUID(row.player_id)
            card = identities.get(player_id)
            if card is None:
                continue
            rows.append(
                AnsweredCandidate(
                    scored=row,
                    card=card,
                    # Absent for everybody the platform has watched play
                    # nothing, which is most people — and an absence rather than
                    # a nought all the way to the wire.
                    record=records.get(player_id),
                    # Absent for everybody the platform has watched nothing of,
                    # which is the same absence and never a nought.
                    player_score=(
                        reading.published_score
                        if (reading := scores.get(player_id)) is not None
                        else None
                    ),
                    at_stake=await self.at_stake_for(row, context),
                )
            )
        return tuple(rows)

    async def at_stake_for(
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

    def recorded(
        self,
        row: Scored,
        band: CandidateBand,
        position: int,
        *,
        card: RecordedCard | None,
        at_stake: AtStake | None,
        suppression_lapsed: bool | None = None,
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
            degraded_terms=tuple(
                stood.term.value for stood in row.fit.degraded_terms
            ),
            degraded_reasons=tuple(
                stood.reason.value for stood in row.fit.degraded_terms
            ),
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
            # Set on a dealt card and ``None`` everywhere else, which the record
            # asserts as a biconditional: a shortlist row is not a card, and a
            # near miss was dealt to nobody.
            suppression_lapsed=suppression_lapsed,
        )

    def recorded_rows(
        self,
        returned: tuple[AnsweredCandidate, ...],
        near_misses: tuple[Scored, ...],
        *,
        lapsed: Mapping[str, bool] | None = None,
    ) -> tuple[SearchCandidateRecord, ...]:
        """Both bands of one record, in position order. **The band split, once.**

        Every surface writes these two bands the same way and neither may write
        them differently: a returned row carries the card it was shown with, and
        a near miss carries none — which is the biconditional
        :class:`SearchCandidateRecord` asserts, and the reason it cannot simply
        be *the rows, with some fields blank*. Written twice, the second copy is
        where a near miss eventually acquires a card and layer 3 acquires a way
        out of the building.

        ``lapsed`` is the deck's one addition, keyed by player id because
        :meth:`attach` drops a row whose card could not be assembled and the
        association has to survive that. ``None`` — rather than an empty mapping
        — is *this surface does not deal cards*, and it is what makes the column
        null on a shortlist instead of a measured ``false``.
        """

        return tuple(
            self.recorded(
                row.scored,
                CandidateBand.RETURNED,
                position,
                card=row.recorded_card(),
                at_stake=row.at_stake,
                suppression_lapsed=(
                    None if lapsed is None else lapsed[row.scored.player_id]
                ),
            )
            for position, row in enumerate(returned, start=1)
        ) + tuple(
            self.recorded(
                row,
                CandidateBand.NEAR_MISS,
                position,
                # A near miss was shown to nobody, so there is no card to
                # record, no counted game to price and no re-show to note:
                # none of the three was ever read for this row.
                card=None,
                at_stake=None,
            )
            for position, row in enumerate(near_misses, start=1)
        )

    async def record(self, record: SearchRecord) -> None:
        """Write it, and commit it, **before** the answer goes anywhere."""

        try:
            await self._searches.record(record)
            await self._uow.commit()
        except Exception as failure:
            raise SearchNotRecorded(
                "the search could not be recorded, so it is not returned"
            ) from failure

    async def note_exposure(
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


def _by_player(
    counterparts: Collection[PairwiseCounterpart],
) -> Mapping[UUID, PairwiseCounterpart]:
    return {counterpart.player_id: counterpart for counterpart in counterparts}


class Timed:
    """Milliseconds spent in one stage, recorded on the search row.

    The operational half of the telemetry, and the one part of the record that is
    about the machine rather than about the people. A context manager rather than
    a decorator so that a stage is a *span of this method*, which is what the
    column means.
    """

    def __init__(
        self,
        into: dict[str, int],
        stage: str,
        meter: ScoringInstrument | None = None,
    ) -> None:
        self._into = into
        self._stage = stage
        self._meter = meter
        self._started = 0.0

    def __enter__(self) -> "Timed":
        self._started = time.monotonic()
        return self

    def __exit__(self, *_: object) -> None:
        elapsed = (time.monotonic() - self._started) * 1000.0
        # **The row is rounded and the instrument is not.** A search row stores
        # whole milliseconds, which is the resolution that column has always
        # had; a p99 over integers would read 0 ms for every shortlist on a fast
        # worker and put the trigger permanently to sleep.
        self._into[self._stage] = int(elapsed)
        if self._meter is not None:
            self._meter.observe_scoring(elapsed)
