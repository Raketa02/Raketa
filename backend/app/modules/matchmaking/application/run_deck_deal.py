"""The Players deal — one deal, and everything the deck decides for itself.

**The order is the shortlist's order**, and it is load-bearing for the same
reasons: read the searcher live, bind one snapshot with every live gate fact, run
the pipeline, write the record and commit it before the answer goes anywhere,
then note exposure. All of that is ``search_workbench.py``'s.

**What is the deck's own is five things, and each of them is a refusal of
something the shortlist does.**

*It takes no mode and reads no declaration* (``docs/adr/0169`` §2). Every deal
scores under the fun ruler, for every viewer, declared or not — the deck is a
discovery surface, and *who would I like to play with?* is not a question about
the kind of evening — so ``play_intent_not_declared`` is never raised here. The
**declaration as it stood** is still what the record keeps, for history: for a
viewer who never declared, as it stood is nothing.

*It excludes four populations the shortlist does not.* Passed within
``PASS_SUPPRESS``, already asked, already dealt, and **cooling off** — somebody
the viewer has a court with, or had one with inside ``deck_cool_off_days``
(``docs/adr/0169`` §6). None of them is a gate — a gate is a statement about the
city and these are statements about one player's own deck — and the first is
**counted onto the record**, because it is the only thing that tells *your own
passes emptied your deck* apart from *the pool is empty*. **Three of the four
read the viewer's last *Show them again*** (``docs/adr/0169`` §5): one moment
off the reset ledger, applied to the pass record, the search record and the
courts each in its own way, so that a reset clears them together and touches
none of them.

*The relaxation ladder does not reach it* (``docs/adr/0099``). There are no rung
offers on a deal and no offer for a later one to cite, so ``rung_offers`` is
``None`` — *the offers were not computed at all*, which is the truth here rather
than a convenient spelling of it.

*A spent deal deals again.* A new request is a new search with a new
``search_id``, the same exclusions plus everybody dealt within
:data:`~app.modules.matchmaking.domain.deck.DEALT_MEMORY`. **Exhausting a deal is
not exhausting the pool**: the honest empty state belongs to a fresh deal that
came back with nothing, never to a player who has seen ten of forty.

*It says two numbers no other surface can* (``docs/adr/0169`` §4, §5): how many
eligible people are beyond this hand, and how many people are waiting on the
viewer. Both ride on the deal and on nothing else — they are as fresh as the
hand, and a read-back a month later would print a count about a pool that has
moved on.

**Suppression fails soft and that is the whole point of it being a cache.** A
deal during a Redis outage may repeat a card the player passed on last week; the
alternative reading — *exclude what we could not check* — empties the deck in a
city that has people in it. The durable pass record is untouched either way. The
cool-off's read fails soft for the same reason, and it is a port rather than a
cache.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from typing import Mapping, final
from uuid import UUID

from app.engines.matchfit.ruleset import Ruleset
from app.engines.matchfit.scoring import MatchFit
from app.kernel import Instant, InvariantViolated
from app.modules.matchmaking.application.commands import RunDeckDealCommand
from app.modules.matchmaking.application.search_workbench import (
    AnsweredCandidate,
    SearchWorkbench,
)
from app.modules.matchmaking.application.outward_reads import read_demand
from app.modules.matchmaking.domain.deck import (
    INHERITED_ON_THE_DECK,
    Deal,
    DeckExclusions,
    cleared_by_reset,
    cooling_off,
    deal,
    dealt_memory_from,
)
from app.modules.matchmaking.domain.deck_reset import DeckResetLedger
from app.modules.matchmaking.domain.candidate_snapshot import CandidateSnapshot
from app.modules.matchmaking.domain.errors import MatchmakingUnavailable
from app.modules.matchmaking.domain.index_staleness import IndexFreshness
from app.modules.matchmaking.domain.interest import InterestLedger
from app.modules.matchmaking.domain.ledgers import SuppressionLedger
from app.modules.matchmaking.domain.passes import (
    PassLedger,
    suppression_lapsed_at,
)
from app.modules.matchmaking.domain.ports import SharedCourt, SharedCourtQuery
from app.modules.matchmaking.domain.prompts import (
    RaisedPrompt,
    improvised_week,
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
    """What the route renders: **the record, and the question the week raises.**

    **The same three fields :class:`ShortlistAnswer` holds**, and they are the
    same fields for a reason rather than by coincidence: both surfaces render
    through one function, so a deal that carried a shape of its own could not be
    read back through it. What differs is what each says — ``sorts_available`` is
    empty here by the rule in ``sorting.py`` rather than by this class being
    different: a deck is one card at a time, so there is no list in the player's
    hand for a control to reorder.

    ``prompts`` used to be missing here on the argument that *a deck improvises
    no grid and takes no widening*, and half of that was circular: the deck
    raised no grid prompt because it accepted no grid. It accepts one now, so it
    asks. **The widening half stands** — the relaxation ladder still does not
    reach the deck, so ``KEEP_THIS_RADIUS`` has nothing to count here.
    """

    record: SearchRecord
    sorts_available: tuple[SortOption, ...]
    #: The people eligible after every deck exclusion who are not in this hand
    #: (``docs/adr/0169`` §5). On the answer and not on the record, because it
    #: is true of the moment the hand was dealt and of no later one.
    remaining: int
    #: How many people have a live yes towards the viewer that would be dealt
    #: (``docs/adr/0169`` §4). A count and never a list: the ledger has no read
    #: that names them and this answer carries nothing that could.
    want_to_play_you: int
    #: The questions this deal raises and does not answer. At most one: the week
    #: it ran on, when that is not the week on the profile.
    prompts: tuple[RaisedPrompt, ...] = ()


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
        courts: SharedCourtQuery,
        resets: DeckResetLedger,
    ) -> None:
        self._work = workbench
        self._ruleset = ruleset
        self._engine = engine
        self._searches = searches
        self._suppression = suppression
        self._interest = interest
        self._passes = passes
        self._courts = courts
        self._resets = resets

    async def execute(self, command: RunDeckDealCommand) -> DeckAnswer:
        now = self._work.clock.now()
        stages: dict[str, int] = {}

        with self._work.timed(stages, "read_searcher"):
            declared = await self._work.searcher_facts_under(
                player_id=command.searcher_id,
                sport=command.sport,
                # **The deck's whole mode story, in one line.** One ruler for
                # everybody, and the declaration is loaded only to be recorded.
                ruler=INHERITED_ON_THE_DECK,
            )
        await self._work.refuse_a_held_searcher(declared.player_id)

        # **The week this one deal runs on**, which is the profile's own unless
        # the player edited it on the Play screen. No rung and no citation: the
        # relaxation ladder does not reach the deck, so the only ask that can
        # move anything here is the grid.
        asked = await self._work.asked_for(
            declared,
            availability_override=command.availability_override,
            offered_by_search_id=None,
            rung=None,
        )
        searcher = replace(declared, grid=asked.grid)

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
                # **No challenge to except**: this surface names none, and the
                # open-challenge gate excludes everybody the searcher is
                # arranging with, exactly as it always has.
                completing_challenge_id=None,
            )

        with self._work.timed(stages, "read_deck_exclusions"):
            passed_at = await self._passes.last_passed_at(
                passer_id=command.searcher_id,
                sport=command.sport,
                candidate_ids=in_box,
            )
            reset_at = await self._resets.latest_at(
                player_id=command.searcher_id, sport=command.sport
            )
            exclusions = await self._exclusions(
                command, in_box, now, passed_at=passed_at, reset_at=reset_at
            )
            re_shows = self._re_shows(passed_at, now)

        with self._work.scoring(stages):
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
        week = improvised_week(asked=asked.grid, profile=declared.grid)
        return DeckAnswer(
            record=record,
            sorts_available=sorts_available(
                tuple(of_scored(row.scored) for row in rows),
                surface=SearchSurface.DECK,
            ),
            remaining=dealt.remaining,
            want_to_play_you=dealt.want_to_play_you,
            # After the commit, like the shortlist's. The sheet rides on the
            # response of the route that used the week, so *Match me* has
            # already dealt by the time the question appears.
            prompts=() if week is None else (week,),
        )

    # -- the four the deck adds to the gates ---------------------------------

    async def _exclusions(
        self,
        command: RunDeckDealCommand,
        in_box: tuple[UUID, ...],
        now: Instant,
        *,
        passed_at: Mapping[UUID, datetime],
        reset_at: Instant | None,
    ) -> DeckExclusions:
        """Whom this deal holds out, and where each answer comes from.

        Four reads, four stores, three different postures — which is the whole
        of *the gate is the cache; the evidence is the row* seen from one method.

        **Suppression** is the cache and it fails soft: an outage answers
        *nobody*, which repeats a card rather than emptying a deal. What the
        viewer's last *Show them again* cleared is subtracted from it off the
        **pass record**, never off the cache — the keys are left to lapse, and
        a reset that had to reach the cache could fail soft and lie.
        **Already asked** is the durable interest ledger, read over this player's
        own outgoing yeses — their own rows, so it is not an inbox — and it lapses
        with the yes, which is how ``INTEREST_TTL`` expiry *returns a person to
        the deck*; the reset does not touch it. **Already dealt** is the search
        record itself, bounded by ``DEALT_MEMORY`` or by the reset, whichever is
        later, which is what makes a spent deal deal again and *deal everyone
        again* true. **Cooling off** is ``games``' record, read through a port
        in the matcher's words that fails soft like the cache does
        (``docs/adr/0169`` §6): the courts still ahead, and the ones behind the
        two of them inside the window and since the reset.
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
            since=dealt_memory_from(now, reset_at=reset_at),
        )
        no_courts: tuple[SharedCourt, ...] = ()
        courts = await read_demand(
            SharedCourtQuery,
            lambda: self._courts.shared_courts(command.searcher_id),
            stood_down=no_courts,
        )
        return DeckExclusions(
            suppressed=suppressed - cleared_by_reset(passed_at, reset_at=reset_at),
            already_asked=frozenset(
                yes.to_player_id
                for yes in outgoing
                if yes.sport is command.sport
            ),
            already_dealt=dealt,
            cooling_off=cooling_off(
                courts,
                now=now,
                days=self._ruleset.interest.deck_cool_off_days,
                reset_at=reset_at,
            ),
        )

    def _re_shows(
        self, passed_at: Mapping[UUID, datetime], now: Instant
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

        **A reset re-show is not flagged here, on purpose.** The flag says *the
        window lapsed*, and after *Show them again* it has not: the card is dealt
        with its pass inside the window. Which re-shows a reset caused is
        answered by the reset ledger beside the pass record — a deal after the
        reset moment, of somebody passed on before it — and that is the sample
        ``docs/adr/0169`` §5 says the falsifier now has to exclude.
        """

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

        ``mode`` is ``None``, which the record's own invariant asserts is a
        biconditional on the surface, and ``intent_read`` is the declaration as
        it stood — ``None`` for a viewer who never made one, and set on no other
        surface — which the invariant asserts too; the table asserts both again
        in check constraints, because one refuses a row this build could write
        and the other refuses a row any writer could.

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
            searcher_area_code=searcher.area_code,
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
