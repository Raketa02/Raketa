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

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.engines.matchfit.core import SearchMode
from app.kernel import Sport
from app.modules.matchmaking.domain.ports import AtStake
from app.modules.matchmaking.domain.searches import (
    CandidateBand,
    InclusionReason,
    PoolDescription,
    RecordedCard,
    SearchCandidateRecord,
    SearchInitiation,
    SearchRecord,
    SearchSurface,
    StagedCounts,
    WithheldReason,
)
from app.modules.player_profile.domain.availability import Window
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
        pool_description={
            "sport": pool.sport.value,
            "radius_km_used": pool.radius_km_used,
            "players_in_range": pool.players_in_range,
            "window": pool.window.value,
            "post_gate": pool.post_gate,
        },
        searcher_slot_count=search.searcher_slot_count,
        radius_clamp_bit=search.radius_clamp_bit,
        latency_ms_by_stage=dict(search.latency_ms_by_stage),
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
            window=Window(pool["window"]),
            post_gate=pool["post_gate"],
        ),
        searcher_slot_count=row.searcher_slot_count,
        radius_clamp_bit=row.radius_clamp_bit,
        latency_ms_by_stage=dict(row.latency_ms_by_stage),
        candidates=candidates,
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
    }


def _candidate_record(row: SearchCandidateORM) -> SearchCandidateRecord:
    return SearchCandidateRecord(
        band=CandidateBand(row.band),
        position=row.position,
        player_id=row.player_id,
        fit=row.fit,
        terms=tuple(_mappings(row.terms)),
        degraded_terms=tuple(row.degraded_terms),
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
    )


def _mappings(stored: Sequence[Any]) -> tuple[Mapping[str, Any], ...]:
    """The opaque blobs, read back as the mappings they were written as.

    Deliberately unvalidated. A row stamped with a ruleset nobody runs any more
    must still read, and a schema here would be the one thing standing between a
    five-year-old search and the reader trying to explain it.
    """

    return tuple(dict(entry) for entry in stored)
