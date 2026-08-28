"""Turning the answer into the response, and omitting what does not apply.

**Every omitted field is omitted here, by not being passed.** The route is
declared ``response_model_exclude_unset=True``, so a field this module does not
name is absent from the JSON — which is the whole mechanism behind
``docs/adr/0106`` §4's first spelling. A field this module passes as ``None`` is
the *second* spelling and means a measured nothing.

**Nothing here computes.** The Fit, its terms, the concerns, the modifiers and
the reason codes all arrive decided; the card and the at-stake block arrive
attached. What is left is naming fields — and a renderer that did arithmetic
would be a second implementation of a domain rule in the one layer nobody tests
for it.
"""

from __future__ import annotations

from typing import Any

from app.engines.matchfit.core import Term
from app.modules.matchmaking.application.record_rows import (
    evidence_payload,
    liveness_reason_codes,
    modifier_rows,
)
from app.modules.matchmaking.application.run_shortlist_search import (
    AnsweredCandidate,
    ShortlistAnswer,
)
from app.modules.matchmaking.domain.geography import whole_kilometres
from app.modules.matchmaking.domain.searches import SearchRecord
from app.modules.matchmaking.presentation.schemas import (
    CandidateSchema,
    ConcernSchema,
    OptimisedFor,
    PlayerCardSchema,
    PoolSchema,
    SearchEnvelope,
    ShortlistResponse,
)


def render(answer: ShortlistAnswer) -> ShortlistResponse:
    """The whole response, from the answer the use case produced."""

    return ShortlistResponse(
        search=_envelope(answer),
        candidates=[_candidate(row) for row in answer.rows],
    )


def _envelope(answer: ShortlistAnswer) -> SearchEnvelope:
    record: SearchRecord = answer.record
    pool = record.pool_description
    return SearchEnvelope(
        search_id=record.id,
        at=record.at,
        surface=record.surface,
        mode=record.mode,
        ruleset_version=record.ruleset_version,
        engine_version=record.engine_version,
        # A shortlist optimises for the person who asked, always. The field is
        # on the envelope rather than implied by the surface because a line-up
        # with seats locked is the case where it is not, and one renderer should
        # read one fact.
        optimised_for=OptimisedFor.SEARCHER,
        index_stale=record.index_stale,
        pool=PoolSchema(
            sport=pool.sport,
            radius_km_used=pool.radius_km_used,
            players_in_range=pool.players_in_range,
            window=pool.window,
            post_gate=pool.post_gate,
        ),
        radius_clamp=record.radius_clamp_bit,
        sorts_available=list(answer.sorts_available),
    )


def _candidate(row: AnsweredCandidate) -> CandidateSchema:
    scored = row.scored
    fields: dict[str, Any] = {
        "player_id": scored.player_id,
        "fit": scored.modified.points,
        "player_card": _card(row),
        "concerns": [ConcernSchema(term=term) for term in scored.fit.concerns],
        "terms": [
            {
                "term": term.term,
                "weight": term.weight,
                "value": term.value,
                "contribution": term.contribution,
                "evidence": evidence_payload(term.evidence),
            }
            for term in scored.fit.terms
        ],
        "degraded_terms": list(scored.fit.degraded_terms),
        "modifiers": list(modifier_rows(scored.modified.modifiers)),
        "liveness_reasons": list(liveness_reason_codes(scored.liveness)),
    }
    if Term.DISTANCE not in scored.fit.degraded_terms:
        # Omitted rather than sent as zero when the term stood down, which is
        # what lets *Closest* sort a stood-down row last instead of first.
        fields["distance_km"] = whole_kilometres(scored.generated.distance_km)
    if scored.inclusion_reason is not None:
        # Only a reason that **admits** somebody crosses. The two that reorder
        # stay in the store: one ships as a Liveness reason instead, and the
        # other is a third party's unpopularity the searcher is owed no version
        # of.
        fields["inclusion_reason"] = scored.inclusion_reason
    if row.at_stake is not None:
        fields["at_stake"] = {
            "win_delta": row.at_stake.win_delta,
            "loss_delta": row.at_stake.loss_delta,
        }
    return CandidateSchema.model_validate(fields)


def _card(row: AnsweredCandidate) -> PlayerCardSchema:
    """The card, from what the index already held plus the two reads beside it.

    ``counted_games`` is never passed: the games ledger has no provider in this
    build, so the field does not apply and a zero would be an invented one.
    """

    indexed = row.scored.generated.row
    fields: dict[str, Any] = {
        "nickname": row.card.nickname,
        "area_code": row.scored.fenced.area_code,
        "social_tags": list(indexed.social_tags),
        "level": indexed.mu,
        "band": indexed.band,
    }
    if row.card.photo_id is not None:
        fields["photo_id"] = row.card.photo_id
    return PlayerCardSchema.model_validate(fields)
