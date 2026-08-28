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

from typing import Any, Mapping, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.matchmaking.domain.searches import (
    CandidateBand,
    InclusionReason,
    SearchCandidateRecord,
    SearchRecord,
    WithheldReason,
)
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

    async def returned_rows_for(
        self, *, search_id: UUID, searcher_id: UUID
    ) -> tuple[SearchCandidateRecord, ...]:
        """This searcher's own ``RETURNED`` rows, in position order.

        **The two filters are the authorization rule**, not an optimisation: the
        join on ``search.searcher_id`` is what makes a stranger's ``search_id``
        answer empty, and the band predicate is what makes layer 3 unreachable
        from anywhere. Neither is a clause a caller may pass — there is no
        argument for either.
        """

        rows = await self._session.execute(
            select(SearchCandidateORM)
            .join(SearchORM, SearchORM.id == SearchCandidateORM.search_id)
            .where(
                SearchCandidateORM.search_id == search_id,
                SearchORM.searcher_id == searcher_id,
                SearchCandidateORM.band == CandidateBand.RETURNED.value,
            )
            .order_by(SearchCandidateORM.position)
        )
        return tuple(_candidate_record(row) for row in rows.scalars())


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
    )


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
    )


def _mappings(stored: Sequence[Any]) -> tuple[Mapping[str, Any], ...]:
    """The opaque blobs, read back as the mappings they were written as.

    Deliberately unvalidated. A row stamped with a ruleset nobody runs any more
    must still read, and a schema here would be the one thing standing between a
    five-year-old search and the reader trying to explain it.
    """

    return tuple(dict(entry) for entry in stored)
