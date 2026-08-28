"""Request-scoped declarations for the matchmaking context.

*When* each adapter is built and how long it lives, never *what* — every
concrete class comes from `app.bootstrap.composition`, and
`tests/unit/test_composition_root.py` fails this file if it imports one.

**The two ledgers were declared before their first caller existed**, exactly as
`get_block_query` was and for the same reason: every Play surface reads them,
none of them was built, and the surfaces should wire to this line rather than
each deciding where a ledger comes from. It also put the seam where the test
suite can hold it — `tests/conftest.py` overrides both with in-memory ledgers, so
**no test in this suite needs Redis running**.

**The candidate source is the process's, not the request's** (`docs/adr/0112`).
It is read off the application rather than built here: a per-request source would
rebuild the container a search is supposed to bind once, which is the whole of
what that ADR buys. When the index is not running in this process there is no
source to bind and the feature is **down** — which is a refusal, not a fallback.

The one infrastructure import here is `get_redis`, which is not an adapter but
the process's connection pool — the same allowance `get_db` has in
`app/api/dependencies.py`, on the same argument.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request
from redis.asyncio import Redis

from app.api.dependencies import (
    ClockDep,
    DbSession,
    DomainEventStoreDep,
    EventPublisherDep,
    UnitOfWorkDep,
)
from app.bootstrap.composition import (
    build_absent_terms,
    build_account_hold_query,
    build_account_status_query,
    build_at_stake_query,
    build_exposure_ledger,
    build_match_fit_engine,
    build_match_history_query,
    build_player_card_source,
    build_player_score_query,
    build_ruleset,
    build_search_store,
    build_suppression_ledger,
)
from app.infrastructure.redis_client import get_redis
from app.modules.blocks.presentation.dependencies import BlockQueryDep
from app.modules.matchmaking.application.run_shortlist_search import RunShortlistSearch
from app.modules.matchmaking.domain.candidate_snapshot import CandidateSource
from app.modules.matchmaking.domain.errors import MatchmakingUnavailable
from app.modules.matchmaking.domain.ledgers import ExposureLedger, SuppressionLedger
from app.modules.player_profile.presentation.dependencies import (
    PlayerProfileRepositoryDep,
    PlayIntentDeclarationRepositoryDep,
)
from app.modules.rating.presentation.dependencies import SkillRatingRepositoryDep

# The pool is the process's, not the request's — `get_redis` takes no request and
# reads no application state. It stays a `Depends` so a test can override it, and
# so that a route asking for a ledger never has to know a client exists.
EphemeralStoreDep = Annotated[Redis, Depends(get_redis)]


def get_exposure_ledger(store: EphemeralStoreDep) -> ExposureLedger:
    return build_exposure_ledger(store)


ExposureLedgerDep = Annotated[ExposureLedger, Depends(get_exposure_ledger)]


def get_suppression_ledger(store: EphemeralStoreDep) -> SuppressionLedger:
    return build_suppression_ledger(store)


SuppressionLedgerDep = Annotated[SuppressionLedger, Depends(get_suppression_ledger)]


def get_candidate_source(request: Request) -> CandidateSource:
    """This process's one index, or a refusal saying it has none.

    **Never a fallback.** A search with no index is not a search with a smaller
    pool — it is a search that cannot answer, and returning an empty shortlist
    would be indistinguishable on the wire from *there is nobody near you*. The
    503 says which.
    """

    source = getattr(request.app.state, "candidate_source", None)
    if source is None:
        raise MatchmakingUnavailable(
            "the candidate index is not running in this process"
        )
    return source


CandidateSourceDep = Annotated[CandidateSource, Depends(get_candidate_source)]


def get_run_shortlist_search(
    db: DbSession,
    clock: ClockDep,
    uow: UnitOfWorkDep,
    event_store: DomainEventStoreDep,
    events: EventPublisherDep,
    candidates: CandidateSourceDep,
    profiles: PlayerProfileRepositoryDep,
    ratings: SkillRatingRepositoryDep,
    declarations: PlayIntentDeclarationRepositoryDep,
    blocks: BlockQueryDep,
    exposure: ExposureLedgerDep,
) -> RunShortlistSearch:
    """The shortlist use case, assembled per request.

    The five outward ports and the store are per-request because they read the
    request's own session; the engine and the ruleset are process-wide, because a
    scorer holds no state and a ruleset is a frozen dataset.

    ``absent_terms`` is derived from the Player Score adapter this root just
    chose rather than declared, so the day that adapter changes, this changes
    with it and nothing else does.
    """

    player_scores = build_player_score_query(db)
    return RunShortlistSearch(
        clock=clock,
        ruleset=build_ruleset(),
        engine=build_match_fit_engine(),
        candidates=candidates,
        searches=build_search_store(db),
        unit_of_work=uow,
        profiles=profiles,
        ratings=ratings,
        declarations=declarations,
        blocks=blocks,
        holds=build_account_hold_query(db),
        account_status=build_account_status_query(db),
        history=build_match_history_query(db),
        player_scores=player_scores,
        at_stake=build_at_stake_query(db),
        exposure=exposure,
        cards=build_player_card_source(
            session=db, event_store=event_store, events=events
        ),
        absent_terms=build_absent_terms(player_scores),
    )


RunShortlistSearchDep = Annotated[
    RunShortlistSearch, Depends(get_run_shortlist_search)
]
