"""*Match me* — one deal, and everything the deck decides for itself.

**The order is the shortlist's order**, and it is load-bearing for the same
reasons: read the searcher live, bind one snapshot with every live gate fact, run
the pipeline, write the record and commit it before the answer goes anywhere,
then note exposure. All of that is ``search_workbench.py``'s.

**What is the deck's own is four things, and each of them is a refusal of
something the shortlist does.**

*It takes no mode.* The weight vector is resolved backend-side from the viewer's
own declared Play intent — ``NO_PREFERENCE → fun``, never a third vector — and
the **declaration as it stood** is what the record keeps, so a later change to
the mapping does not rewrite history. The two travel together because they come
from **one read**: the mode is a function of the declaration
:meth:`SearchWorkbench.searcher_facts` applies to the row it just loaded.

*It excludes three populations the shortlist does not.* Passed within
``PASS_SUPPRESS``, already asked, already dealt. None of them is a gate — a gate
is a statement about the city and these are statements about one player's own
deck — and the first is **counted onto the record**, because it is the only thing
that tells *your own passes emptied your deck* apart from *the pool is empty*.

*The relaxation ladder does not reach it* (``docs/adr/0099``). There are no rung
offers on a deal and no offer for a later one to cite, so ``rung_offers`` is
``None`` — *the offers were not computed at all*, which is the truth here rather
than a convenient spelling of it.

*A spent deal deals again.* A new request is a new search with a new
``search_id``, the same exclusions plus everybody dealt within
:data:`~app.modules.matchmaking.domain.deck.DEALT_MEMORY`. **Exhausting a deal is
not exhausting the pool**: the honest empty state belongs to a fresh deal that
came back with nothing, never to a player who has seen ten of forty.

**Suppression fails soft and that is the whole point of it being a cache.** A
deal during a Redis outage may repeat a card the player passed on last week; the
alternative reading — *exclude what we could not check* — empties the deck in a
city that has people in it. The durable pass record is untouched either way.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import final
from uuid import UUID

from app.engines.matchfit.ruleset import Ruleset
from app.engines.matchfit.scoring import MatchFit
from app.kernel import Instant, InvariantViolated
from app.modules.matchmaking.application.commands import RunDeckDealCommand
from app.modules.matchmaking.application.search_workbench import (
    AnsweredCandidate,
    SearchWorkbench,
)
from app.modules.matchmaking.domain.deck import (
    DEALT_MEMORY,
    Deal,
    DeckExclusions,
    deal,
    mode_for_intent,
)
from app.modules.matchmaking.domain.candidate_snapshot import CandidateSnapshot
from app.modules.matchmaking.domain.errors import MatchmakingUnavailable
from app.modules.matchmaking.domain.index_staleness import IndexFreshness
from app.modules.matchmaking.domain.interest import InterestLedger
from app.modules.matchmaking.domain.ledgers import SuppressionLedger
from app.modules.matchmaking.domain.passes import (
    PassLedger,
    suppression_lapsed_at,
)
from app.modules.matchmaking.domain.relaxation import radius_ladder
from app.modules.matchmaking.domain.search_context import (
    SearchContext,
    SearcherFacts,
)
from app.modules.matchmaking.domain.search_store import SearchStore
from app.modules.matchmaking.domain.searches import (
    PoolDescription,
    SearchInitiation,
    SearchRecord,
    SearchSurface,
    SortOption,
)
from app.modules.matchmaking.domain.sorting import of_scored, sorts_available
from app.modules.player_profile.domain.availability import window_of
from app.shared.ids import new_uuid


@final
@dataclass(frozen=True, slots=True)
class DeckAnswer:
    """What the route renders: **the record, and nothing beside it.**

    The same shape :class:`ShortlistAnswer` has, minus the two fields that are
    about a list. There are no ``prompts`` on a deal — the two a search can raise
    are about a grid it improvised and a widening it keeps taking, and a deck does
    neither — and ``sorts_available`` is empty by the rule in ``sorting.py``
    rather than by this class being different: a deck is one card at a time, so
    there is no list in the player's hand for a control to reorder.
    """

    record: SearchRecord
    sorts_available: tuple[SortOption, ...]


@final
class RunDeckDeal:
    """One deal, end to end."""

    def __init__(
        self,
        *,
        workbench: SearchWorkbench,
        ruleset: Ruleset,
        engine: MatchFit,
        searches: SearchStore,
        suppression: SuppressionLedger,
        interest: InterestLedger,
        passes: PassLedger,
    ) -> None:
        self._work = workbench
        self._ruleset = ruleset
        self._engine = engine
        self._searches = searches
        self._suppression = suppression
        self._interest = interest
        self._passes = passes

    async def execute(self, command: RunDeckDealCommand) -> DeckAnswer:
        now = self._work.clock.now()
        stages: dict[str, int] = {}

        with self._work.timed(stages, "read_searcher"):
            searcher = await self._work.searcher_facts(
                player_id=command.searcher_id,
                sport=command.sport,
                # **The deck's whole mode story, in one line.** It is a function
                # of the declaration rather than a value, so the vector this deal
                # runs under and the declaration recorded beside it are one read.
                mode_of=lambda intent: mode_for_intent(intent, self._ruleset.intent),
            )
        await self._work.refuse_a_held_searcher(searcher.player_id)

        snapshot, freshness = self._work.bound_snapshot(command.sport, now)
        for_a_newcomer = searcher.is_new_at(now)
        in_box = self._work.population(searcher, snapshot)

        with self._work.timed(stages, "read_gates"):
            context = await self._work.bind(
                searcher,
                snapshot,
                now,
                in_box=in_box,
                surface=SearchSurface.DECK,
                initiation=SearchInitiation.HUMAN,
                for_a_newcomer=for_a_newcomer,
            )

        with self._work.timed(stages, "read_deck_exclusions"):
            exclusions = await self._exclusions(command, in_box, now)
            re_shows = await self._re_shows(command, in_box, now)

        with self._work.timed(stages, "pipeline"):
            try:
                dealt = deal(
                    context,
                    self._engine,
                    exclusions=exclusions,
                    re_shows=re_shows,
                )
            except InvariantViolated as broken:
                raise MatchmakingUnavailable(
                    f"the matcher refused to deal: {broken}"
                ) from broken

        with self._work.timed(stages, "attach"):
            rows = await self._work.attach(
                tuple(card.scored for card in dealt.cards), context
            )

        record = self._record(
            command, searcher, context, dealt, rows, snapshot, freshness, stages, now
        )
        await self._work.record(record)
        await self._work.note_exposure(
            command.sport,
            now,
            tuple(row.scored for row in rows),
            for_a_newcomer,
        )
        return DeckAnswer(
            record=record,
            sorts_available=sorts_available(
                tuple(of_scored(row.scored) for row in rows),
                surface=SearchSurface.DECK,
            ),
        )

    # -- the three the deck adds to the gates --------------------------------

    async def _exclusions(
        self, command: RunDeckDealCommand, in_box: tuple[UUID, ...], now: Instant
    ) -> DeckExclusions:
        """Whom this deal holds out, and where each answer comes from.

        Three reads, three stores, three different postures — which is the whole
        of *the gate is the cache; the evidence is the row* seen from one method.

        **Suppression** is the cache and it fails soft: an outage answers
        *nobody*, which repeats a card rather than emptying a deal.
        **Already asked** is the durable interest ledger, read over this player's
        own outgoing yeses — their own rows, so it is not an inbox — and it lapses
        with the yes, which is how ``INTEREST_TTL`` expiry *returns a person to
        the deck*. **Already dealt** is the search record itself, bounded by
        ``DEALT_MEMORY``, which is what makes a spent deal deal again.
        """

        suppressed = await self._suppression.suppressed_for(
            passer_id=command.searcher_id, candidate_ids=in_box
        )
        outgoing = await self._interest.outgoing(
            player_id=command.searcher_id, now=now
        )
        dealt = await self._searches.dealt_since(
            searcher_id=command.searcher_id,
            sport=command.sport,
            since=now - DEALT_MEMORY,
        )
        return DeckExclusions(
            suppressed=suppressed,
            already_asked=frozenset(
                yes.to_player_id
                for yes in outgoing
                if yes.sport is command.sport
            ),
            already_dealt=dealt,
        )

    async def _re_shows(
        self, command: RunDeckDealCommand, in_box: tuple[UUID, ...], now: Instant
    ) -> frozenset[UUID]:
        """Which of these cards would be a **re-show**, from the record alone.

        A pass whose window has run out, by its own date against the released
        ``PASS_SUPPRESS``. It excludes nobody — the suppression above did that,
        or failed soft and did not — and it names nobody to a screen: it decides
        one boolean per recorded row, and *pass rate on re-shown profiles* is the
        only falsifier ``PASS_SUPPRESS`` has.

        **It never consults the cache**, which is the whole point of reading a
        durable row here. The cache fails soft, so during an outage a
        live-suppressed player is dealt; a flag derived from *the cache no longer
        holds them* would then call that a re-show, and the falsifier would be
        corrupted at exactly the moment extra re-shows are happening.
        """

        passed_at = await self._passes.last_passed_at(
            passer_id=command.searcher_id,
            sport=command.sport,
            candidate_ids=in_box,
        )
        suppress_days = self._ruleset.interest.pass_suppress_days
        return frozenset(
            player_id
            for player_id, at in passed_at.items()
            if suppression_lapsed_at(at, now, suppress_days)
        )

    # -- the record ----------------------------------------------------------

    def _record(
        self,
        command: RunDeckDealCommand,
        searcher: SearcherFacts,
        context: SearchContext,
        dealt: Deal,
        rows: tuple[AnsweredCandidate, ...],
        snapshot: CandidateSnapshot,
        freshness: IndexFreshness,
        stages: dict[str, int],
        now: Instant,
    ) -> SearchRecord:
        """One deal's row, and the two columns only a deal ever writes.

        ``mode`` is ``None`` and ``intent_read`` is the declaration, which the
        record's own invariant asserts is a biconditional on the surface — and
        the table asserts again in a check constraint, because one refuses a row
        this build could write and the other refuses a row any writer could.

        ``rung_offers`` is ``None`` — *not computed at all*, which is what the
        ladder not reaching the deck means — while ``radius_clamp_bit`` is still
        written, because its job is counting the searchers already at the
        slider's ceiling and a deck player is as much one of those as a searcher.
        """

        lapsed = {
            card.scored.player_id: card.suppression_lapsed for card in dealt.cards
        }
        return SearchRecord(
            id=new_uuid(),
            searcher_id=searcher.player_id,
            sport=command.sport,
            mode=None,
            intent_read=searcher.declared_intent,
            surface=SearchSurface.DECK,
            initiation=SearchInitiation.HUMAN,
            at=now,
            engine_version=self._engine.version,
            ruleset_version=self._ruleset.version,
            snapshot_version=snapshot.snapshot_version,
            trace_id=command.trace_id,
            index_stale=freshness.records_staleness,
            counts=replace(dealt.counts, n_returned=len(rows)),
            best_withheld_fit=dealt.best_withheld_fit,
            pool_description=PoolDescription(
                sport=command.sport,
                radius_km_used=searcher.radius_km,
                players_in_range=dealt.players_in_range,
                window=window_of(searcher.grid, context.today),
            ),
            searcher_grid=searcher.grid.codes,
            searcher_slot_count=len(searcher.grid),
            radius_clamp_bit=radius_ladder(searcher.radius_km).clamped,
            rung_offers=None,
            offered_by_search_id=None,
            rung_taken=None,
            latency_ms_by_stage=stages,
            n_excluded_by_suppression=dealt.n_excluded_by_suppression,
            candidates=self._work.recorded_rows(
                rows, dealt.near_misses, lapsed=lapsed
            ),
        )
