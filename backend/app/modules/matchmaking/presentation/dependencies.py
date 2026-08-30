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
    SettingsDep,
    UnitOfWorkDep,
)
from app.bootstrap.composition import (
    build_absent_terms,
    build_account_hold_query,
    build_account_status_query,
    build_at_stake_query,
    build_card_photo_links,
    build_exposure_ledger,
    build_interest_ledger,
    build_match_fit_engine,
    build_match_history_query,
    build_mutual_challenge_minting,
    build_pass_ledger,
    build_player_card_source,
    build_player_score_query,
    build_ruleset,
    build_search_store,
    build_prompt_decline_ledger,
    build_prompt_ledger,
    build_suppression_ledger,
)
from app.infrastructure.redis_client import get_redis
from app.modules.blocks.presentation.dependencies import BlockQueryDep
from app.modules.matchmaking.application.express_interest import ExpressInterest
from app.modules.matchmaking.application.forecast_lineup import ForecastLineup
from app.modules.matchmaking.application.record_pass import RecordPass
from app.modules.matchmaking.application.record_prompt_decline import (
    RecordPromptDecline,
)
from app.modules.matchmaking.application.read_back_search import ReadBackSearch
from app.modules.matchmaking.application.read_interest import ReadInterest
from app.modules.matchmaking.application.run_deck_deal import RunDeckDeal
from app.modules.matchmaking.application.run_lineup_search import RunLineupSearch
from app.modules.matchmaking.application.run_shortlist_search import RunShortlistSearch
from app.modules.matchmaking.application.search_workbench import SearchWorkbench
from app.modules.matchmaking.domain.cards import CardPhotoLinks
from app.modules.matchmaking.domain.candidate_snapshot import CandidateSource
from app.modules.matchmaking.domain.declines import PromptDeclineLedger
from app.modules.matchmaking.domain.errors import MatchmakingUnavailable
from app.modules.matchmaking.domain.interest import InterestLedger
from app.modules.matchmaking.domain.ledgers import ExposureLedger, SuppressionLedger
from app.modules.matchmaking.domain.passes import PassLedger
from app.modules.matchmaking.domain.ports import AccountHoldQuery, AccountStatusQuery
from app.modules.matchmaking.domain.prompts import PromptLedger
from app.modules.matchmaking.domain.scale_triggers import ScoringInstrument
from app.modules.player_profile.presentation.dependencies import (
    PhotoStorageDep,
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


def get_scoring_meter(request: Request) -> ScoringInstrument | None:
    """This process's scoring histogram, or ``None`` where there is not one.

    **Never a refusal.** An index a search cannot bind is a search that cannot
    answer; an instrument it cannot report to is a window that stays empty, and
    a platform that returned 503 because it could not measure itself would have
    the priority exactly backwards.
    """

    meter: ScoringInstrument | None = getattr(request.app.state, "scoring_meter", None)
    return meter


ScoringMeterDep = Annotated[ScoringInstrument | None, Depends(get_scoring_meter)]


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


def get_card_photo_links(
    storage: PhotoStorageDep,
    settings: SettingsDep,
) -> CardPhotoLinks:
    """The photograph on a card, signed for this response and no other.

    Declared beside the gates rather than inside a use case, because **every
    Play surface renders a card** and a surface deciding for itself where a link
    comes from is how one of them ends up signing for a different window. It is
    the photo provider's own store, reached through their port — and the window
    is the composition root's to read, so this line says when a signer is built
    and never how long it signs for.
    """

    return build_card_photo_links(storage=storage, settings=settings)


CardPhotoLinksDep = Annotated[CardPhotoLinks, Depends(get_card_photo_links)]


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
    meter: ScoringMeterDep,
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
        meter=meter,
    )


SearchWorkbenchDep = Annotated[SearchWorkbench, Depends(get_search_workbench)]


def get_prompt_decline_ledger(db: DbSession) -> PromptDeclineLedger:
    """The durable record of every *not now*. **Per request, over the session.**

    The same contrast as the pass's, one document over: the prompt ledger built
    beside it is Redis and fails soft, because a question nobody sees this week
    costs nothing; this one is a table, because a player's answer is not a thing
    the platform may forget and then ask again.
    """

    return build_prompt_decline_ledger(db)


PromptDeclineLedgerDep = Annotated[
    PromptDeclineLedger, Depends(get_prompt_decline_ledger)
]


def get_run_shortlist_search(
    db: DbSession,
    workbench: SearchWorkbenchDep,
    prompts: PromptLedgerDep,
    declines: PromptDeclineLedgerDep,
) -> RunShortlistSearch:
    """The shortlist use case: the workbench, plus what only a list has.

    Four collaborators beyond the shared ones, and each is a thing a deal does
    not do — the ladder needs the ruleset and the engine to price a rung, the
    citation check needs the store, and the prompts need both the ledger they
    were left in and the record of the ones this player has already answered
    *not now*.

    **The two prompt stores are deliberately different stores**, and this is
    where that shows: one is Redis and fails soft because a lost question costs
    nobody a fact, and the other is a table because a lost decline re-asks
    somebody who has already answered.
    """

    return RunShortlistSearch(
        workbench=workbench,
        ruleset=build_ruleset(),
        engine=build_match_fit_engine(),
        searches=build_search_store(db),
        prompts=prompts,
        declines=declines,
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


def get_record_prompt_decline(
    clock: ClockDep,
    uow: UnitOfWorkDep,
    declines: PromptDeclineLedgerDep,
) -> RecordPromptDecline:
    """*Not now*, assembled per request. **One store, and no second one.**

    It holds no ruleset, no engine and no search store: nothing here scores
    anybody, there is no product number to read — thirty days is ADR-0094's —
    and there is no origin to prove. The row it writes is the gate as well as
    the evidence, so unlike the pass beside it there is no cache to write after
    the commit.
    """

    return RecordPromptDecline(
        clock=clock,
        declines=declines,
        unit_of_work=uow,
    )


RecordPromptDeclineDep = Annotated[
    RecordPromptDecline, Depends(get_record_prompt_decline)
]


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

    And it holds the **mint**, because a mutual yes opens a game inline: *that
    player has left the deck for good, because you now have an open game
    together* is a promise that must not wait for a poller. It is built over this
    request's own session, so the yes and the challenge are one transaction.
    """

    return ExpressInterest(
        clock=clock,
        ruleset=build_ruleset(),
        interest=interest,
        searches=build_search_store(db),
        challenges=build_mutual_challenge_minting(db),
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


def get_run_lineup_search(
    workbench: SearchWorkbenchDep,
    blocks: BlockQueryDep,
) -> RunLineupSearch:
    """The line-up use case: the workbench, plus the gate a shortlist never asked.

    One collaborator beyond the shared ones, and it is the whole of what
    ``docs/adr/0116`` added: a four contains six pairs and the searcher is in
    three of them, so the line-up makes **one bulk block query over the ``K``
    candidate ids** that no other surface has any use for.

    There is no prompt ledger and no search store of its own: the ladder does not
    run here — ``MIN_SHORTLIST`` counts rows in a list somebody reads and a
    line-up returns seats — and the citation check that needs the store lives on
    the workbench, where both surfaces reach it.
    """

    return RunLineupSearch(
        workbench=workbench,
        ruleset=build_ruleset(),
        engine=build_match_fit_engine(),
        blocks=blocks,
    )


RunLineupSearchDep = Annotated[RunLineupSearch, Depends(get_run_lineup_search)]


def get_forecast_lineup(
    db: DbSession,
    workbench: SearchWorkbenchDep,
    candidates: CandidateSourceDep,
    blocks: BlockQueryDep,
    holds: AccountHoldQueryDep,
) -> ForecastLineup:
    """The forecast, assembled per request. **It is handed nothing to write to.**

    It holds a search store to *read* the citation and an engine only for its
    version stamp; there is no unit of work here and no ledger, because
    ``docs/adr/0108`` makes recording nothing a property of this route rather
    than a discipline its author has to keep. The absence is the point: a use
    case holding a writer is a use case that can quietly start writing.
    """

    return ForecastLineup(
        workbench=workbench,
        ruleset=build_ruleset(),
        engine=build_match_fit_engine(),
        searches=build_search_store(db),
        candidates=candidates,
        blocks=blocks,
        holds=holds,
    )


ForecastLineupDep = Annotated[ForecastLineup, Depends(get_forecast_lineup)]
