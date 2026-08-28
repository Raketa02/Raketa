"""Request-scoped declarations for the matchmaking context.

*When* each adapter is built and how long it lives, never *what* — every
concrete class comes from `app.bootstrap.composition`, and
`tests/unit/test_composition_root.py` fails this file if it imports one.

**The ephemeral ledgers are declared here and not per use case**, exactly as
`get_block_query` is and for the same reason: every Play surface reads them, and
a surface deciding for itself where a gate comes from is how one of them ends up
wired to a different answer. It also puts the seam where the test suite can hold
it — `tests/conftest.py` overrides all three with in-memory ledgers, so **no test
in this suite needs Redis running**.

**`SearchWorkbench` is declared on the same argument, one layer up.** Every
surface does the same reads and the same writes around the stage that differs, so
the shortlist and the deck take one of these rather than fifteen collaborators
each — and what is left in each factory below is exactly what that surface
decides for itself.

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
    build_interest_ledger,
    build_match_fit_engine,
    build_match_history_query,
    build_pass_ledger,
    build_player_card_source,
    build_player_score_query,
    build_ruleset,
    build_search_store,
    build_prompt_ledger,
    build_suppression_ledger,
)
from app.infrastructure.redis_client import get_redis
from app.modules.blocks.presentation.dependencies import BlockQueryDep
from app.modules.matchmaking.application.express_interest import ExpressInterest
from app.modules.matchmaking.application.record_pass import RecordPass
from app.modules.matchmaking.application.read_back_search import ReadBackSearch
from app.modules.matchmaking.application.read_interest import ReadInterest
from app.modules.matchmaking.application.run_deck_deal import RunDeckDeal
from app.modules.matchmaking.application.run_shortlist_search import RunShortlistSearch
from app.modules.matchmaking.application.search_workbench import SearchWorkbench
from app.modules.matchmaking.domain.candidate_snapshot import CandidateSource
from app.modules.matchmaking.domain.errors import MatchmakingUnavailable
from app.modules.matchmaking.domain.interest import InterestLedger
from app.modules.matchmaking.domain.ledgers import ExposureLedger, SuppressionLedger
from app.modules.matchmaking.domain.passes import PassLedger
from app.modules.matchmaking.domain.ports import AccountHoldQuery, AccountStatusQuery
from app.modules.matchmaking.domain.prompts import PromptLedger
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


def get_prompt_ledger(store: EphemeralStoreDep) -> PromptLedger:
    return build_prompt_ledger(store)


PromptLedgerDep = Annotated[PromptLedger, Depends(get_prompt_ledger)]


def get_interest_ledger(db: DbSession) -> InterestLedger:
    """The durable *Let's play* ledger. **Per request, over the request's session.**

    Declared beside the three ephemeral ledgers and built from a different place
    on purpose: those are Redis and this is a table, and the seam is what makes
    that swap invisible to a route. Three surfaces read it today — the search's
    lift, the two interest routes — so all three wire to this line rather than
    each deciding where a ledger comes from.
    """

    return build_interest_ledger(db)


InterestLedgerDep = Annotated[InterestLedger, Depends(get_interest_ledger)]


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


def get_account_hold_query(db: DbSession) -> AccountHoldQuery:
    """Whether an account is under a live hold. **Declared, like every gate.**

    It is a line here rather than a call inside a use case's factory for the
    reason ``get_block_query`` is: both surfaces that evaluate this gate — the
    search and its read-back — should wire to one declaration, and a gate the
    test suite cannot reach is a gate whose fail-closed posture is asserted only
    in prose.
    """

    return build_account_hold_query(db)


AccountHoldQueryDep = Annotated[AccountHoldQuery, Depends(get_account_hold_query)]


def get_account_status_query(db: DbSession) -> AccountStatusQuery:
    """The set of accounts that may not be shown. Candidate-side, fails closed."""

    return build_account_status_query(db)


AccountStatusQueryDep = Annotated[
    AccountStatusQuery, Depends(get_account_status_query)
]


def get_search_workbench(
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
    holds: AccountHoldQueryDep,
    account_status: AccountStatusQueryDep,
    exposure: ExposureLedgerDep,
    interest: InterestLedgerDep,
) -> SearchWorkbench:
    """Everything every Play surface reads and writes, assembled per request.

    Declared once rather than per use case, which is the same reason the two
    ledgers above are declared here: **every surface reads them**, and a second
    surface deciding for itself where a gate comes from is how one of them ends
    up wired to a different answer.

    The five outward ports and the store are per-request because they read the
    request's own session; the engine and the ruleset are process-wide, because a
    scorer holds no state and a ruleset is a frozen dataset. The candidate source
    is the **process's** (``docs/adr/0112``).

    ``absent_terms`` is derived from the Player Score adapter this root just
    chose rather than declared, so the day that adapter changes, this changes
    with it and nothing else does.
    """

    player_scores = build_player_score_query(db)
    return SearchWorkbench(
        clock=clock,
        ruleset=build_ruleset(),
        searches=build_search_store(db),
        unit_of_work=uow,
        candidates=candidates,
        profiles=profiles,
        ratings=ratings,
        declarations=declarations,
        blocks=blocks,
        holds=holds,
        account_status=account_status,
        history=build_match_history_query(db),
        player_scores=player_scores,
        at_stake=build_at_stake_query(db),
        exposure=exposure,
        interest=interest,
        cards=build_player_card_source(
            session=db, event_store=event_store, events=events
        ),
        absent_terms=build_absent_terms(player_scores),
    )


SearchWorkbenchDep = Annotated[SearchWorkbench, Depends(get_search_workbench)]


def get_run_shortlist_search(
    db: DbSession,
    workbench: SearchWorkbenchDep,
    prompts: PromptLedgerDep,
) -> RunShortlistSearch:
    """The shortlist use case: the workbench, plus what only a list has.

    Three collaborators beyond the shared ones, and each is a thing a deal does
    not do — the ladder needs the ruleset and the engine to price a rung, the
    citation check needs the store, and the prompts need the ledger they were
    left in.
    """

    return RunShortlistSearch(
        workbench=workbench,
        ruleset=build_ruleset(),
        engine=build_match_fit_engine(),
        searches=build_search_store(db),
        prompts=prompts,
    )


RunShortlistSearchDep = Annotated[
    RunShortlistSearch, Depends(get_run_shortlist_search)
]


def get_pass_ledger(db: DbSession) -> PassLedger:
    """The durable record of every pass. **Per request, over the session.**

    Declared beside the suppression ledger and built from a different place on
    purpose: that one is Redis and fails soft, this one is a table and does not.
    The gate is the cache; the evidence is the row.
    """

    return build_pass_ledger(db)


PassLedgerDep = Annotated[PassLedger, Depends(get_pass_ledger)]


def get_run_deck_deal(
    db: DbSession,
    workbench: SearchWorkbenchDep,
    suppression: SuppressionLedgerDep,
    interest: InterestLedgerDep,
    passes: PassLedgerDep,
) -> RunDeckDeal:
    """The deck, assembled per request. **Three ledgers the shortlist has not.**

    The suppression cache and the pass record are the deck's alone — a pass
    reaches no other surface — and the interest ledger is here for the deck's own
    *already asked* exclusion, which is a read of the player's **own outgoing**
    rows rather than the lift's read of incoming ones the workbench makes.

    There is no prompt ledger: a deal raises no question, because the two a
    search can raise are about a grid it improvised and a widening it keeps
    taking, and a deck does neither.
    """

    return RunDeckDeal(
        workbench=workbench,
        ruleset=build_ruleset(),
        engine=build_match_fit_engine(),
        searches=build_search_store(db),
        suppression=suppression,
        interest=interest,
        passes=passes,
    )


RunDeckDealDep = Annotated[RunDeckDeal, Depends(get_run_deck_deal)]


def get_record_pass(
    db: DbSession,
    clock: ClockDep,
    uow: UnitOfWorkDep,
    suppression: SuppressionLedgerDep,
    passes: PassLedgerDep,
) -> RecordPass:
    """*Not today*, assembled per request. **Two stores, in that order.**

    It holds a ruleset and no engine: the one number it reads is
    ``PASS_SUPPRESS``, and nothing here scores anybody. It holds the **search
    store** because the origin key is proved against a record rather than trusted
    from a request.
    """

    return RecordPass(
        clock=clock,
        ruleset=build_ruleset(),
        passes=passes,
        suppression=suppression,
        searches=build_search_store(db),
        unit_of_work=uow,
    )


RecordPassDep = Annotated[RecordPass, Depends(get_record_pass)]


def get_read_back_search(
    db: DbSession,
    candidates: CandidateSourceDep,
    profiles: PlayerProfileRepositoryDep,
    blocks: BlockQueryDep,
    holds: AccountHoldQueryDep,
    account_status: AccountStatusQueryDep,
) -> ReadBackSearch:
    """The read-back, assembled per request. **Six collaborators, no engine.**

    It reads a record and re-evaluates four gates; it never scores, so there is
    no ruleset here and no ``MatchFit``. The absence is the point — a use case
    holding a scorer is a use case that can quietly start re-ranking a stored
    answer, which is the one thing an immutable record may not do.

    The candidate source is the process's, exactly as it is for a search: the
    mutual gender gate reads the other side's preference off the index row, so a
    process with no index cannot evaluate that gate and says so with the same
    503 rather than withholding everybody.
    """

    return ReadBackSearch(
        searches=build_search_store(db),
        profiles=profiles,
        candidates=candidates,
        blocks=blocks,
        holds=holds,
        account_status=account_status,
    )


ReadBackSearchDep = Annotated[ReadBackSearch, Depends(get_read_back_search)]


def get_express_interest(
    db: DbSession,
    clock: ClockDep,
    uow: UnitOfWorkDep,
    interest: InterestLedgerDep,
) -> ExpressInterest:
    """*Let's play*, assembled per request.

    It holds a ruleset and no engine: the two numbers it reads —
    ``INTEREST_TTL`` and ``OUTSTANDING_INTEREST_CAP`` — are ruleset rows, and
    nothing here scores anybody. It holds the **search store** because the origin
    key is proved against a record rather than trusted from a request.
    """

    return ExpressInterest(
        clock=clock,
        ruleset=build_ruleset(),
        interest=interest,
        searches=build_search_store(db),
        unit_of_work=uow,
    )


ExpressInterestDep = Annotated[ExpressInterest, Depends(get_express_interest)]


def get_read_interest(
    clock: ClockDep,
    interest: InterestLedgerDep,
    blocks: BlockQueryDep,
) -> ReadInterest:
    """The interest read, assembled per request. **Three collaborators.**

    The block query is here because ``docs/adr/0095``'s rule reaches every
    surface that shows one player to another, and a mutual row names a person. It
    fails closed, which is why it is wired rather than optional.
    """

    return ReadInterest(
        clock=clock,
        ruleset=build_ruleset(),
        interest=interest,
        blocks=blocks,
    )


ReadInterestDep = Annotated[ReadInterest, Depends(get_read_interest)]
