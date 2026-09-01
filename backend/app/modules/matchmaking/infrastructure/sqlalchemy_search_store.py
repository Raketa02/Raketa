"""``SearchStore`` over SQLAlchemy. **It adds rows and it never commits.**

The transaction boundary is a decision about the *command*, exactly as it is for
every repository in this backend — and here it is a load-bearing one: the record
is committed **before** the response returns, by the use case, in the request's
own transaction. A store that committed for itself would take that decision away
from the one place that has to make it.

**No update and no delete.** ``docs/adr/0104`` §3 leaves erasure as the only path
that ever removes a row, and erasure does not exist. A method for it here would
be a method somebody reaches for.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.engines.matchfit.core import SearchMode
from app.kernel import Sport, iso_weekday
from app.modules.matchmaking.domain.ports import AtStake
from app.modules.matchmaking.domain.relaxation import (
    RelaxationAsk,
    Rung,
    RungOffer,
)
from app.modules.matchmaking.domain.search_store import SearchModeReading
from app.modules.matchmaking.domain.searches import (
    CandidateBand,
    CombinationBand,
    InclusionReason,
    LineupRecord,
    RecordedCombination,
    PoolDescription,
    RecordedCard,
    SearchCandidateRecord,
    SearchInitiation,
    SearchRecord,
    SearchSurface,
    StagedCounts,
    WithheldReason,
)
from app.modules.player_profile.domain.availability import (
    AvailabilityGrid,
    Window,
    window_of,
)
from app.modules.player_profile.domain.play_intent import PlayIntent
from app.modules.matchmaking.infrastructure.search_model import (
    SearchCandidateORM,
    SearchORM,
)


class SqlAlchemySearchStore:
    """The durable half of ``docs/adr/0104``, over the request's own session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(self, search: SearchRecord) -> None:
        """Add the search row and every candidate row, in one flush.

        Added rather than committed: the caller commits, and it does so before
        returning the answer whose identity this row *is*.
        """

        self._session.add(_search_row(search))
        for candidate in search.candidates:
            self._session.add(_candidate_row(search.id, candidate))
        await self._session.flush()

    async def find(
        self, *, search_id: UUID, searcher_id: UUID
    ) -> SearchRecord | None:
        """This searcher's own search, with its ``RETURNED`` rows in position order.

        **The two filters are the authorization rule**, not an optimisation: the
        predicate on ``searcher_id`` is what makes a stranger's ``search_id``
        answer nothing, and the band predicate is what makes layer 3 unreachable
        from anywhere. Neither is a clause a caller may pass — there is no
        argument for either.
        """

        found = await self._session.execute(
            select(SearchORM).where(
                SearchORM.id == search_id,
                SearchORM.searcher_id == searcher_id,
            )
        )
        search = found.scalar_one_or_none()
        if search is None:
            return None
        rows = await self._session.execute(
            select(SearchCandidateORM)
            .where(
                SearchCandidateORM.search_id == search_id,
                SearchCandidateORM.band == CandidateBand.RETURNED.value,
            )
            .order_by(SearchCandidateORM.position)
        )
        return _search_record(
            search, tuple(_candidate_record(row) for row in rows.scalars())
        )

    async def widenings_taken(
        self, *, searcher_id: UUID, sport: Sport, radius_km: int
    ) -> int:
        """How often this searcher has already widened to this radius.

        It counts the **radius** and not the rung: rung B on a 10 km profile and
        rung C on a 7 km one both land on 15 km, and what the offer to save it
        would write is the number, not the letter.
        """

        counted = await self._session.execute(
            select(func.count())
            .select_from(SearchORM)
            .where(
                SearchORM.searcher_id == searcher_id,
                SearchORM.sport == sport.value,
                SearchORM.rung_taken.is_not(None),
                SearchORM.pool_description["radius_km_used"].as_integer()
                == radius_km,
            )
        )
        return int(counted.scalar_one())

    async def dealt_since(
        self, *, searcher_id: UUID, sport: Sport, since: datetime
    ) -> frozenset[UUID]:
        """Everybody this player has been **dealt** since a moment, in this sport.

        Two predicates and no third: the surface, because a shortlist row is not
        a card and passing on the deck is not what happened to it; and the band,
        because a near miss was dealt to nobody. Ids only — the deal needs a set
        to hold people out with, and a method that returned rows would be a
        second way to read a search record.
        """

        rows = await self._session.scalars(
            select(SearchCandidateORM.player_id)
            .join(SearchORM, SearchORM.id == SearchCandidateORM.search_id)
            .where(
                SearchORM.searcher_id == searcher_id,
                SearchORM.sport == sport.value,
                SearchORM.surface == SearchSurface.DECK.value,
                SearchORM.at >= since,
                SearchCandidateORM.band == CandidateBand.RETURNED.value,
            )
        )
        return frozenset(rows)

    async def modes_since(
        self, *, since: datetime, limit: int
    ) -> tuple[SearchModeReading, ...]:
        """Every search run since a moment, newest first. **Four columns.**

        The drift loop's whole read. It selects the columns rather than the ORM
        row so that *what the detector may see* is visible in one line here — a
        loop handed whole records would be one refactor away from reading a
        candidate.
        """

        rows = await self._session.execute(
            select(
                SearchORM.searcher_id,
                SearchORM.sport,
                SearchORM.mode,
                SearchORM.at,
            )
            .where(SearchORM.at >= since)
            .order_by(SearchORM.at.desc())
            .limit(limit)
        )
        return tuple(
            SearchModeReading(
                searcher_id=searcher_id,
                sport=Sport(sport),
                mode=None if mode is None else SearchMode(mode),
                at=_utc(at),
            )
            for searcher_id, sport, mode, at in rows.all()
        )


def _search_row(search: SearchRecord) -> SearchORM:
    pool = search.pool_description
    return SearchORM(
        id=search.id,
        searcher_id=search.searcher_id,
        sport=search.sport.value,
        mode=None if search.mode is None else search.mode.value,
        intent_read=(
            None if search.intent_read is None else search.intent_read.value
        ),
        surface=search.surface.value,
        initiation=search.initiation.value,
        at=search.at,
        engine_version=search.engine_version,
        ruleset_version=search.ruleset_version,
        snapshot_version=search.snapshot_version,
        trace_id=search.trace_id,
        index_stale=search.index_stale,
        n_generated=search.counts.n_generated,
        excluded_by_gate=dict(search.counts.excluded_by_gate),
        n_scored=search.counts.n_scored,
        n_cleared_floor=search.counts.n_cleared_floor,
        n_returned=search.counts.n_returned,
        n_near_miss_recorded=search.counts.n_near_miss_recorded,
        best_withheld_fit=search.best_withheld_fit,
        # ``search-telemetry.md``'s own shape, window included, because an
        # analyst reading this column cannot call ``window_of`` in SQL. **The
        # window inside it is the analyst's copy and no reader takes it**: the
        # record re-derives that one field from ``searcher_grid`` and ``at``, so
        # the wire has a single source and a label written today cannot outlive
        # the rule that made it. The rest of the blob is read back as written.
        pool_description={
            "sport": pool.sport.value,
            "radius_km_used": pool.radius_km_used,
            "players_in_range": pool.players_in_range,
            "window": pool.window.value,
            "post_gate": pool.post_gate,
        },
        searcher_grid=list(search.searcher_grid),
        searcher_slot_count=search.searcher_slot_count,
        searcher_area_code=search.searcher_area_code,
        radius_clamp_bit=search.radius_clamp_bit,
        rung_offers=(
            None
            if search.rung_offers is None
            else [_offer_blob(offer) for offer in search.rung_offers]
        ),
        offered_by_search_id=search.offered_by_search_id,
        rung_taken=None if search.rung_taken is None else search.rung_taken.value,
        latency_ms_by_stage=dict(search.latency_ms_by_stage),
        n_excluded_by_suppression=search.n_excluded_by_suppression,
        lineup=None if search.lineup is None else _lineup_blob(search.lineup),
    )


def _lineup_blob(lineup: LineupRecord) -> dict[str, Any]:
    """Layer 4, as one opaque object. **Written here and read by no route.**

    Flat counters and a two-element list, in the order the winner and the
    runner-up were compared. The ``G`` breakdown inside each row is the same
    ``terms`` shape the candidate blob uses — stamped with ``ruleset_version``
    and allowed to change with the group vector.
    """

    return {
        "combinations": lineup.combinations,
        "refused_by_gate": lineup.refused_by_gate,
        "refused_by_floor": lineup.refused_by_floor,
        "max_fit_rank_seated": lineup.max_fit_rank_seated,
        "rows": [
            {
                "band": row.band.value,
                "members": [str(one) for one in row.members],
                "partner_id": str(row.partner_id),
                "terms": [dict(term) for term in row.terms],
                "degraded_terms": list(row.degraded_terms),
                "side_gap": row.side_gap,
                "forecast_pct": row.forecast_pct,
            }
            for row in lineup.rows
        ],
    }


def _lineup_record(blob: Mapping[str, Any] | None) -> LineupRecord | None:
    """Layer 4, read back as the record it was written from.

    Read back for the reason the counters and the pool description are: the
    record is one thing, and a reader that assembled half of it would be a
    second, narrower notion of what a search *is*. **What may leave the building
    is decided at the wire**, and no renderer names this.
    """

    if blob is None:
        return None
    return LineupRecord(
        combinations=blob["combinations"],
        refused_by_gate=blob["refused_by_gate"],
        refused_by_floor=blob["refused_by_floor"],
        max_fit_rank_seated=blob["max_fit_rank_seated"],
        rows=tuple(
            RecordedCombination(
                band=CombinationBand(row["band"]),
                members=tuple(UUID(one) for one in row["members"]),
                partner_id=UUID(row["partner_id"]),
                terms=tuple(dict(term) for term in row["terms"]),
                degraded_terms=tuple(row["degraded_terms"]),
                side_gap=row["side_gap"],
                forecast_pct=row["forecast_pct"],
            )
            for row in blob["rows"]
        ),
    )


def _offer_blob(offer: RungOffer) -> dict[str, Any]:
    """One rung offer, whole. **The window is stored with it, and derived once.**

    Unlike the search's own window — re-derived from ``searcher_grid`` on the way
    out — a rung's window belongs to a grid that was never run and is nowhere
    else on this row. It is the offer's own fact, so it is stored as part of the
    offer, and the two live together or the count and its cost could disagree.
    """

    return {
        "rung": offer.rung.value,
        "ask": offer.ask.value,
        "candidates_above_floor": offer.candidates_above_floor,
        "window": offer.window.value,
        "radius_km": offer.radius_km,
        "slot": offer.slot,
    }


def _offer(blob: Mapping[str, Any]) -> RungOffer:
    return RungOffer(
        rung=Rung(blob["rung"]),
        ask=RelaxationAsk(blob["ask"]),
        candidates_above_floor=blob["candidates_above_floor"],
        window=Window(blob["window"]),
        radius_km=blob["radius_km"],
        slot=blob["slot"],
    )


def _search_record(
    row: SearchORM, candidates: tuple[SearchCandidateRecord, ...]
) -> SearchRecord:
    """The search row, read back as the record it was written from.

    The counters and the pool description come back too, even though no route
    sends them anywhere: the record is one thing, and a reader that assembled
    half of it would be a second, narrower notion of what a search *is*. What may
    leave the building is decided at the wire, in ``presentation/``, which is the
    only place that decision is written down.
    """

    pool = row.pool_description
    return SearchRecord(
        id=row.id,
        searcher_id=row.searcher_id,
        sport=Sport(row.sport),
        mode=None if row.mode is None else SearchMode(row.mode),
        intent_read=None if row.intent_read is None else PlayIntent(row.intent_read),
        surface=SearchSurface(row.surface),
        initiation=SearchInitiation(row.initiation),
        at=_utc(row.at),
        engine_version=row.engine_version,
        ruleset_version=row.ruleset_version,
        snapshot_version=row.snapshot_version,
        trace_id=row.trace_id,
        index_stale=row.index_stale,
        counts=StagedCounts(
            n_generated=row.n_generated,
            excluded_by_gate=dict(row.excluded_by_gate),
            n_scored=row.n_scored,
            n_cleared_floor=row.n_cleared_floor,
            n_returned=row.n_returned,
            n_near_miss_recorded=row.n_near_miss_recorded,
        ),
        best_withheld_fit=row.best_withheld_fit,
        pool_description=PoolDescription(
            sport=Sport(pool["sport"]),
            radius_km_used=pool["radius_km_used"],
            players_in_range=pool["players_in_range"],
            # **Re-derived, never read back.** ``the-two-contracts.md`` §3: a
            # stored label is how a stale window ships the day ``window_of``
            # changes. The two inputs are both on this row — the grid the search
            # ran on, and the day it ran — so the derivation reproduces the
            # answer that was given rather than the one that would be given now.
            #
            # **``docs/adr/0100`` §8's other half is owed and not built here.**
            # The window is re-derived at *challenge creation* too, from this
            # same grid, and stored on the challenge beside its origin key —
            # which is a demand on ``matches``, a context that does not exist.
            # ``searcher_grid`` is what makes it payable the day it does, and it
            # is recorded now because it is search-time and has no backfill.
            window=window_of(
                AvailabilityGrid.from_codes(row.searcher_grid),
                iso_weekday(_utc(row.at).isoweekday()),
            ),
            post_gate=pool["post_gate"],
        ),
        searcher_grid=tuple(row.searcher_grid),
        searcher_slot_count=row.searcher_slot_count,
        searcher_area_code=row.searcher_area_code,
        radius_clamp_bit=row.radius_clamp_bit,
        rung_offers=(
            None
            if row.rung_offers is None
            else tuple(_offer(blob) for blob in row.rung_offers)
        ),
        offered_by_search_id=row.offered_by_search_id,
        rung_taken=None if row.rung_taken is None else Rung(row.rung_taken),
        latency_ms_by_stage=dict(row.latency_ms_by_stage),
        lineup=_lineup_record(row.lineup),
        candidates=candidates,
        n_excluded_by_suppression=row.n_excluded_by_suppression,
    )


def _utc(value: datetime) -> datetime:
    """A stored moment, read back as the UTC it was written as.

    PostgreSQL's ``timestamptz`` carries the offset and SQLite does not: it
    stores the text and hands back a naive ``datetime``. Attaching UTC here is a
    statement about the storage rather than about the clock — the value was
    written as UTC, so reading it as anything else would move it — and it happens
    at the one seam where a stored column becomes a domain value rather than
    being a fact every reader has to remember.
    """

    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _candidate_row(
    search_id: UUID, candidate: SearchCandidateRecord
) -> SearchCandidateORM:
    return SearchCandidateORM(
        search_id=search_id,
        band=candidate.band.value,
        position=candidate.position,
        player_id=candidate.player_id,
        fit=candidate.fit,
        terms=[dict(term) for term in candidate.terms],
        degraded_terms=list(candidate.degraded_terms),
        degraded_reasons=list(candidate.degraded_reasons),
        modifiers=[dict(modifier) for modifier in candidate.modifiers],
        liveness_reasons=list(candidate.liveness_reasons),
        liveness_signals=dict(candidate.liveness_signals),
        shared_count=candidate.shared_count,
        their_slot_count=candidate.their_slot_count,
        days_away=candidate.days_away,
        inclusion_reason=(
            None
            if candidate.inclusion_reason is None
            else candidate.inclusion_reason.value
        ),
        withheld_reason=(
            None
            if candidate.withheld_reason is None
            else candidate.withheld_reason.value
        ),
        missing_terms=list(candidate.missing_terms),
        reliability_penalty_applied=candidate.reliability_penalty_applied,
        reliability_penalty_decisive=candidate.reliability_penalty_decisive,
        concerns=list(candidate.concerns),
        distance_km=candidate.distance_km,
        player_card=_card_blob(candidate.card),
        at_stake=(
            None
            if candidate.at_stake is None
            else {
                "win_delta": candidate.at_stake.win_delta,
                "loss_delta": candidate.at_stake.loss_delta,
            }
        ),
        suppression_lapsed=candidate.suppression_lapsed,
    )


def _card_blob(card: RecordedCard | None) -> dict[str, Any] | None:
    """The card as one blob rather than six columns.

    It is written and read whole, never queried into, and it is the one part of
    the row whose shape belongs to a *response* rather than to the engine — so a
    relational spread of it would be six columns nothing ever selects
    individually, and six chances for a card to be stored half-assembled.

    The ``photo_id`` goes down as text because a blob has no UUID type; it is a
    photo **id and never a URL**, which is the whole of what makes it storable in
    a row kept for ever.
    """

    if card is None:
        return None
    return {
        "nickname": card.nickname,
        "photo_id": None if card.photo_id is None else str(card.photo_id),
        "area_code": card.area_code,
        "social_tags": list(card.social_tags),
        "level": card.level,
        "band": card.band,
        "range_low": card.range_low,
        "range_high": card.range_high,
    }


def _candidate_record(row: SearchCandidateORM) -> SearchCandidateRecord:
    return SearchCandidateRecord(
        band=CandidateBand(row.band),
        position=row.position,
        player_id=row.player_id,
        fit=row.fit,
        terms=tuple(_mappings(row.terms)),
        degraded_terms=tuple(row.degraded_terms),
        degraded_reasons=tuple(row.degraded_reasons),
        modifiers=tuple(_mappings(row.modifiers)),
        liveness_reasons=tuple(row.liveness_reasons),
        liveness_signals=dict(row.liveness_signals),
        shared_count=row.shared_count,
        their_slot_count=row.their_slot_count,
        days_away=row.days_away,
        inclusion_reason=(
            None
            if row.inclusion_reason is None
            else InclusionReason(row.inclusion_reason)
        ),
        withheld_reason=(
            None if row.withheld_reason is None else WithheldReason(row.withheld_reason)
        ),
        missing_terms=tuple(row.missing_terms),
        reliability_penalty_applied=row.reliability_penalty_applied,
        reliability_penalty_decisive=row.reliability_penalty_decisive,
        concerns=tuple(row.concerns),
        distance_km=row.distance_km,
        card=_recorded_card(row.player_card),
        at_stake=(
            None
            if row.at_stake is None
            else AtStake(
                win_delta=row.at_stake["win_delta"],
                loss_delta=row.at_stake["loss_delta"],
            )
        ),
        suppression_lapsed=row.suppression_lapsed,
    )


def _recorded_card(blob: Mapping[str, Any] | None) -> RecordedCard | None:
    if blob is None:
        return None
    photo_id = blob["photo_id"]
    return RecordedCard(
        nickname=blob["nickname"],
        photo_id=None if photo_id is None else UUID(photo_id),
        area_code=blob["area_code"],
        social_tags=tuple(blob["social_tags"]),
        level=blob["level"],
        band=blob["band"],
        # **A hard key, like every other fact on this card.** There is no blob
        # written without a range — the columns arrived with the route that
        # reads them, on a branch with no deployed environment — so a `.get`
        # here would trade a loud `KeyError` for a card that quietly stopped
        # saying how sure anybody was.
        range_low=blob["range_low"],
        range_high=blob["range_high"],
    )


def _mappings(stored: Sequence[Any]) -> tuple[Mapping[str, Any], ...]:
    """The opaque blobs, read back as the mappings they were written as.

    Deliberately unvalidated. A row stamped with a ruleset nobody runs any more
    must still read, and a schema here would be the one thing standing between a
    five-year-old search and the reader trying to explain it.
    """

    return tuple(dict(entry) for entry in stored)
