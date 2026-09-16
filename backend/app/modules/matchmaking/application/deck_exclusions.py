"""The four reads behind the deck's exclusions, held once and asked by two
surfaces.

The deal holds people out for four reasons that are statements about one
player's own deck and not about the city (``deck.py``): a live pass
suppression, a yes already sent, a card already dealt, and a court the two of
them share or lately shared. The **radar** applies none of them to who it draws
(``docs/adr/0174`` §3) — and still needs three of the four, because the chip on
its envelope is *N want to play you* **computed by the deck's own rule**
(§5): post-gate over the deck's gates, minus the passed, the cooling-off and
the already-mutual. Two surfaces asking the same four stores with two copies of
the reads would be the first place the two chips could come to disagree, so the
reads are here, once, and each use case holds one of these.

**Postures, per read** — which is the whole of *the gate is the cache; the
evidence is the row* seen from one class. Suppression is the cache and fails
soft: an outage answers *nobody*, which repeats a card rather than emptying a
deal, and what the viewer's last *Show them again* cleared is subtracted off the
durable pass record, never off the cache. Already asked is the durable interest
ledger, read over this player's own outgoing rows. Already dealt is the search
record, bounded by ``DEALT_MEMORY`` or the reset, and it is the one read a
reading declines — nothing on the radar is held out for having been dealt, and
the chip ignores the memory by ``holds_out_a_yes``'s own rule. Cooling off is
``games``' record through a port that fails soft like the cache.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping, final
from uuid import UUID

from app.engines.matchfit.ruleset import Ruleset
from app.kernel import Instant, Sport
from app.modules.matchmaking.application.outward_reads import read_demand
from app.modules.matchmaking.domain.deck import (
    DeckExclusions,
    cleared_by_reset,
    cooling_off,
    dealt_memory_from,
)
from app.modules.matchmaking.domain.deck_reset import DeckResetLedger
from app.modules.matchmaking.domain.interest import InterestLedger
from app.modules.matchmaking.domain.ledgers import SuppressionLedger
from app.modules.matchmaking.domain.passes import PassLedger
from app.modules.matchmaking.domain.ports import SharedCourt, SharedCourtQuery
from app.modules.matchmaking.domain.search_store import SearchStore


@final
@dataclass(frozen=True, slots=True)
class HeldOut:
    """What a deal's reads answered, and the pass record they were read against.

    ``passed_at`` rides beside the exclusions because the deal reads it a
    second time — the re-show flag is derived from the pass record against the
    same ``now`` — and a second load would be a second answer.
    """

    exclusions: DeckExclusions
    #: The latest pass per person, off the durable record.
    passed_at: Mapping[UUID, datetime]


@final
class DeckExclusionReads:
    """The deck's four reads, wired once from the stores the deal holds."""

    def __init__(
        self,
        *,
        ruleset: Ruleset,
        searches: SearchStore,
        suppression: SuppressionLedger,
        interest: InterestLedger,
        passes: PassLedger,
        courts: SharedCourtQuery,
        resets: DeckResetLedger,
    ) -> None:
        self._ruleset = ruleset
        self._searches = searches
        self._suppression = suppression
        self._interest = interest
        self._passes = passes
        self._courts = courts
        self._resets = resets

    async def for_a_deal(
        self,
        *,
        searcher_id: UUID,
        sport: Sport,
        in_box: tuple[UUID, ...],
        now: Instant,
    ) -> HeldOut:
        """Whom the deck's rule holds out of this viewer's deal, over this box —
        all four, the dealt memory included, which is what *a spent deal deals
        again* buys."""

        return await self._read(
            searcher_id=searcher_id,
            sport=sport,
            in_box=in_box,
            now=now,
            with_the_dealt_memory=True,
        )

    async def for_the_chip(
        self,
        *,
        searcher_id: UUID,
        sport: Sport,
        in_box: tuple[UUID, ...],
        now: Instant,
    ) -> DeckExclusions:
        """The three of the four that decide *N want to play you*, for a reading.

        The dealt memory is not read: nothing on the radar is held out for
        having been dealt, the chip ignores the memory by ``holds_out_a_yes``'s
        own rule, and a read nobody consults is a query per reading for nothing.
        """

        held = await self._read(
            searcher_id=searcher_id,
            sport=sport,
            in_box=in_box,
            now=now,
            with_the_dealt_memory=False,
        )
        return held.exclusions

    async def _read(
        self,
        *,
        searcher_id: UUID,
        sport: Sport,
        in_box: tuple[UUID, ...],
        now: Instant,
        with_the_dealt_memory: bool,
    ) -> HeldOut:
        passed_at = await self._passes.last_passed_at(
            passer_id=searcher_id, sport=sport, candidate_ids=in_box
        )
        reset_at = await self._resets.latest_at(player_id=searcher_id, sport=sport)
        suppressed = await self._suppression.suppressed_for(
            passer_id=searcher_id, candidate_ids=in_box
        )
        outgoing = await self._interest.outgoing(player_id=searcher_id, now=now)
        dealt: frozenset[UUID] = frozenset()
        if with_the_dealt_memory:
            dealt = await self._searches.dealt_since(
                searcher_id=searcher_id,
                sport=sport,
                since=dealt_memory_from(now, reset_at=reset_at),
            )
        no_courts: tuple[SharedCourt, ...] = ()
        courts = await read_demand(
            SharedCourtQuery,
            lambda: self._courts.shared_courts(searcher_id),
            stood_down=no_courts,
        )
        return HeldOut(
            exclusions=DeckExclusions(
                suppressed=suppressed - cleared_by_reset(passed_at, reset_at=reset_at),
                already_asked=frozenset(
                    yes.to_player_id for yes in outgoing if yes.sport is sport
                ),
                already_dealt=dealt,
                cooling_off=cooling_off(
                    courts,
                    now=now,
                    days=self._ruleset.interest.deck_cool_off_days,
                    reset_at=reset_at,
                ),
            ),
            passed_at=passed_at,
        )
