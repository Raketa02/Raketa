"""The reading — one reading of the reach, and everything the radar decides
for itself.

**The order is the deck's order**, and it is load-bearing for the same reasons:
read the searcher live, bind one snapshot with every live gate fact, run the
pipeline, write the record and commit it before the answer goes anywhere. All
of that is ``search_workbench.py``'s, and the ruler is the deck's own — one
vector for every viewer, the intent term stood down, the declaration recorded
as it stood (``docs/adr/0174`` §3 by way of ADR-0169 §2).

**What is the radar's own is four things, and each is a refusal of something
the deck does.**

*It asks five gates and no judgement* (``docs/adr/0174`` §3). The five are
asked in ``gates.py`` by the surface's name; what happens after them is
``radar.py``'s — everyone admitted is scored, everyone scored is drawn, and
the order is the distance and then the id. None of the deck's exclusions
reaches who is drawn: the passed, the cooling-off, the matched and the already
dealt are all on the map.

*It never counts as dealt* (§4, ADR-0131 bounded). The record it writes is a
``RADAR`` row, and the dealt memory reads ``DECK`` rows and nothing else — so
a look on Monday changes nothing about Tuesday's deck. Only an answer reaches
the deck, and an answer given here names the reading as its origin through
the same resolver a deal's answers use.

*It notes no exposure.* The exposure ledger prices who has been **offered** —
the zero-exposure lift and the busy sink read it to spread the deck's hand —
and a map is not an offer. A reading that wrote it would mark every player in
a dense city *shown* several times a day and end the lift's meaning, which is
a look reaching the deck's order by the back door §4 closes.

*It says one number no other surface but the deck can* (§5): how many people
have a live yes towards the viewer that **the deck would deal**. It is computed
by the deck's own function over a generation run under the deck's own gates
and the deck's own exclusions — the reads shared in ``deck_exclusions.py`` —
so the chip on either pane of Players is one number. The named edge: a liker
whose Level is too far for the deck is drawn here, carries ``INTEREST_LIFT``,
and is not counted.

**Two facts are attached beside the card** (§2): the bearing from the viewer's
drawn spot to each player's, and every sport each is rated in with the Level
held there, read across the index's partitions. Both are recorded on the row,
because a read-back never recomputes.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import final

from app.engines.matchfit.ruleset import Ruleset
from app.engines.matchfit.scoring import MatchFit
from app.kernel import Instant, InvariantViolated
from app.modules.matchmaking.application.commands import RunRadarReadingCommand
from app.modules.matchmaking.application.deck_exclusions import DeckExclusionReads
from app.modules.matchmaking.application.search_workbench import (
    AnsweredCandidate,
    SearchWorkbench,
)
from app.modules.matchmaking.domain.candidate_snapshot import CandidateSnapshot
from app.modules.matchmaking.domain.deck import INHERITED_ON_THE_DECK, waiting
from app.modules.matchmaking.domain.errors import MatchmakingUnavailable
from app.modules.matchmaking.domain.index_staleness import IndexFreshness
from app.modules.matchmaking.domain.radar import Reading, ratings_across, read
from app.modules.matchmaking.domain.relaxation import radius_ladder
from app.modules.matchmaking.domain.search_context import (
    SearchContext,
    SearcherFacts,
)
from app.modules.matchmaking.domain.searches import (
    PoolDescription,
    SearchInitiation,
    SearchRecord,
    SearchSurface,
    SortOption,
)
from app.modules.matchmaking.domain.shortlist import generate
from app.modules.matchmaking.domain.sorting import of_scored, sorts_available
from app.modules.player_profile.domain.weekly_hours import window_of
from app.shared.ids import new_uuid


@final
@dataclass(frozen=True, slots=True)
class RadarAnswer:
    """What the route renders: **the record, and the deck's number.**

    The same fields :class:`DeckAnswer` holds minus two — ``remaining`` and
    ``prompts`` — and the same for a reason: every surface renders through one
    function, so a reading that carried a shape of its own could not be read
    back through it. ``sorts_available`` is empty by ``sorting.py``'s rule; a
    radar has no list to reorder. There is no ``remaining``: a reading draws
    everybody, so nobody is beyond the hand. And there are no prompts: the
    reading takes no week and takes no rung, so it raises no question.
    """

    record: SearchRecord
    sorts_available: tuple[SortOption, ...]
    #: How many people have a live yes towards the viewer that **the deck would
    #: deal** (``docs/adr/0174`` §5) — the deck's own count, on the reading's
    #: envelope, so the chip on either pane is one number. A count and never a
    #: list; omitted at zero on the wire, where the deal sends a measured
    #: nought, because a reading's chip is drawn at one and above.
    want_to_play_you: int


@final
class RunRadarReading:
    """One reading, end to end."""

    def __init__(
        self,
        *,
        workbench: SearchWorkbench,
        ruleset: Ruleset,
        engine: MatchFit,
        held_out: DeckExclusionReads,
    ) -> None:
        self._work = workbench
        self._ruleset = ruleset
        self._engine = engine
        # **The deck's reads, for the deck's number.** The same object the deal
        # holds, over the same four stores, so the chip here is the chip there
        # — and none of them touches who the radar draws.
        self._held_out = held_out

    async def execute(self, command: RunRadarReadingCommand) -> RadarAnswer:
        now = self._work.clock.now()
        stages: dict[str, int] = {}

        with self._work.timed(stages, "read_searcher"):
            searcher = await self._work.searcher_facts_under(
                player_id=command.searcher_id,
                sport=command.sport,
                # One ruler for everybody, the deck's, so one pair prints one
                # Fit on both panes of Players.
                ruler=INHERITED_ON_THE_DECK,
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
                surface=SearchSurface.RADAR,
                initiation=SearchInitiation.HUMAN,
                for_a_newcomer=for_a_newcomer,
                # The open-challenge gate is not asked here at all, so there is
                # no court to except from it; stated rather than defaulted, as
                # every caller must.
                completing_challenge_id=None,
            )

        with self._work.timed(stages, "read_deck_exclusions"):
            # A reading is not a deal: nothing here is held out for having
            # been dealt, and these three decide the chip and nothing else.
            decks_exclusions = await self._held_out.for_the_chip(
                searcher_id=command.searcher_id,
                sport=command.sport,
                in_box=in_box,
                now=now,
            )

        with self._work.scoring(stages):
            try:
                reading = read(context, self._engine)
                # **The deck's number, by the deck's rule.** The same bound
                # context re-read under the deck's surface asks the deck's ten
                # gates; the deck's function then counts the yeses among the
                # people those gates admit that the deck's exclusions leave
                # waiting. A yes the radar draws and the deck would refuse —
                # a Level too far — is drawn and not counted (§5).
                on_the_deck = replace(context, surface=SearchSurface.DECK)
                waiting_on_the_deck = waiting(
                    generate(on_the_deck), on_the_deck, decks_exclusions
                )
            except InvariantViolated as broken:
                raise MatchmakingUnavailable(
                    f"the matcher refused to read the radar: {broken}"
                ) from broken

        with self._work.timed(stages, "attach"):
            rows = await self._attach(reading, context)

        record = self._record(
            command, searcher, context, reading, rows, snapshot, freshness, stages, now
        )
        await self._work.record(record)
        # No exposure is noted: a map is not an offer (see the module's record).
        return RadarAnswer(
            record=record,
            sorts_available=sorts_available(
                tuple(of_scored(row.scored) for row in rows),
                surface=SearchSurface.RADAR,
            ),
            want_to_play_you=waiting_on_the_deck,
        )

    async def _attach(
        self, reading: Reading, context: SearchContext
    ) -> tuple[AnsweredCandidate, ...]:
        """The card and the record block, then the radar's two beside them.

        The workbench attaches what every surface attaches and drops a row
        whose card cannot be assembled; the bearing and the sport chips are
        then put on the rows that survived, keyed by id, so a dropped row
        cannot shift a bearing onto its neighbour.
        """

        answered = await self._work.attach(
            tuple(row.scored for row in reading.rows), context
        )
        bearings = {row.scored.player_id: row.bearing_deg for row in reading.rows}
        chips = ratings_across(
            self._work.partitions_beside(context.snapshot),
            tuple(row.scored.generated.player_uuid for row in answered),
        )
        return tuple(
            replace(
                row,
                bearing_deg=bearings[row.scored.player_id],
                ratings=chips[row.scored.generated.player_uuid],
            )
            for row in answered
        )

    def _record(
        self,
        command: RunRadarReadingCommand,
        searcher: SearcherFacts,
        context: SearchContext,
        reading: Reading,
        rows: tuple[AnsweredCandidate, ...],
        snapshot: CandidateSnapshot,
        freshness: IndexFreshness,
        stages: dict[str, int],
        now: Instant,
    ) -> SearchRecord:
        """One reading's row — a ``RADAR`` search with no mode.

        ``mode`` is ``None`` and ``intent_read`` is the declaration as it
        stood, on the deck's own argument and under the same invariant, which
        now reads *scores under one ruler* rather than *is the deck*.
        ``rung_offers`` is ``None`` — the ladder does not reach the radar any
        more than it reaches the deck — and ``n_excluded_by_suppression`` is
        ``None`` because no suppression reached who was drawn. There is no
        near-miss band: nothing was withheld.
        """

        return SearchRecord(
            id=new_uuid(),
            searcher_id=searcher.player_id,
            sport=command.sport,
            mode=None,
            intent_read=searcher.declared_intent,
            surface=SearchSurface.RADAR,
            initiation=SearchInitiation.HUMAN,
            at=now,
            engine_version=self._engine.version,
            ruleset_version=self._ruleset.version,
            snapshot_version=snapshot.snapshot_version,
            trace_id=command.trace_id,
            index_stale=freshness.records_staleness,
            counts=replace(reading.counts, n_returned=len(rows)),
            best_withheld_fit=reading.best_withheld_fit,
            pool_description=PoolDescription(
                sport=command.sport,
                radius_km_used=searcher.radius_km,
                # **The row count** (``the-radar.md`` §2): on a reading the
                # post-gate pool is the answer, less only a row whose card
                # could not be assembled.
                players_in_range=len(rows),
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
            candidates=self._work.recorded_rows(rows, reading.near_misses),
        )
