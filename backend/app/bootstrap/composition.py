"""Adapter construction, with no web framework in it.

Every port a use case depends on is built here by a plain function whose
arguments are a database session, the settings, or ports built by the functions
above it. Nothing in this module imports FastAPI, and nothing in it reads a
request.

**The rule this module exists to make true: an adapter is a function of a
session and configuration, and only the *declaration* of that function ever
belonged to the web layer.** Before it, every adapter was constructed inside a
`Depends` callable, so anything that is not an HTTP request — a seed run, a
worker, a management command — had two options, and both are bad. Boot the API
to create data, or hand-copy the wiring into a second composition root. A
hand-copied composition root drifts from the real one silently: it keeps
working, and it stops being the thing production runs.

`app/api/dependencies.py` and each module's `presentation/dependencies.py` are
now thin callers over these functions. They declare *when* an adapter is built
and how long it lives; this module decides *what* is built. A test asserts the
split structurally — those modules import no adapter — because the failure mode
is one line of convenience in a `Depends` callable, and nothing about a green
suite would look different afterwards.

Sharing is the caller's business, deliberately. Each function returns a new
instance, and every adapter here is a stateless wrapper over the session, so
two instances over one session are interchangeable. Under FastAPI the sharing
comes free: it caches each dependency for the life of a request, so the store
one repository is given is the store the other is given. A caller outside a
request that wants the same guarantee builds a port once and passes it on, the
way `build_assessment_repository` takes its two.
"""

from __future__ import annotations

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.application.ports import DomainEventPublisher, DomainEventStore, UnitOfWork
from app.bootstrap.events import EventRuntime, get_event_runtime
from app.core.config import Settings
from app.engines.assessment import AssessmentEngine
from app.engines.matchfit.core import Term
from app.engines.matchfit.ruleset import Ruleset
from app.engines.matchfit.scoring import MatchFit
from app.engines.matchfit.v1 import MatchFitV1
from app.engines.racketskill.v3 import RacketSkillEngineV3
from app.infrastructure.clock import SystemClock
from app.infrastructure.database.unit_of_work import AsyncSqlAlchemyUnitOfWork
from app.kernel import Clock
from app.modules.auth.domain.ports import (
    PasswordHasher,
    RefreshTokenRepository,
    TokenService,
)
from app.modules.auth.infrastructure.jwt_token_service import JwtTokenService
from app.modules.auth.infrastructure.password_hasher import BcryptPasswordHasher
from app.modules.auth.infrastructure.sqlalchemy_refresh_token_repository import (
    SqlAlchemyRefreshTokenRepository,
)
from app.modules.blocks.domain.ports import BlockQuery, BlockRepository
from app.modules.blocks.infrastructure.event_sourced_block_query import (
    EventSourcedBlockQuery,
)
from app.modules.blocks.infrastructure.event_sourced_block_repository import (
    EventSourcedBlockRepository,
)
from app.modules.matchmaking.domain.ports import (
    AccountHoldQuery,
    AccountStatusQuery,
    AtStakeQuery,
    MatchHistoryQuery,
    PlayerScoreQuery,
)
from app.modules.matchmaking.application.roll_exposure import RollExposure
from app.modules.matchmaking.domain.cards import PlayerCardSource
from app.modules.matchmaking.domain.ledgers import ExposureLedger, SuppressionLedger
from app.modules.matchmaking.domain.prompts import PromptLedger
from app.modules.matchmaking.domain.search_store import SearchStore
from app.modules.matchmaking.infrastructure.fail_soft_ledgers import (
    FailSoftExposureLedger,
    FailSoftPromptLedger,
    FailSoftSuppressionLedger,
)
from app.modules.matchmaking.infrastructure.redis_ledgers import (
    RedisExposureLedger,
    RedisPromptLedger,
    RedisSuppressionLedger,
)
from app.modules.matchmaking.infrastructure.rebuild_candidate_index import (
    RebuildCandidateIndex,
)
from app.modules.matchmaking.infrastructure.absent_providers import (
    NoHoldsExist,
    NoMatchHistoryExists,
    NoPlayerScoresExist,
    NoResultUpdateRuleExists,
)
from app.modules.matchmaking.infrastructure.candidate_index_tail import (
    CandidateIndexTail,
)
from app.modules.matchmaking.infrastructure.candidate_snapshot_source import (
    DatabaseCandidateSource,
)
from app.modules.matchmaking.infrastructure.snapshot_horizon import (
    DialectSnapshotHorizon,
    NoSnapshotHorizon,
    PostgresSnapshotHorizon,
    SnapshotHorizon,
)
from app.modules.matchmaking.infrastructure.rulesets import LIVE_RULESET
from app.modules.matchmaking.infrastructure.player_card_source import (
    PlayerCardIdentities,
)
from app.modules.matchmaking.infrastructure.sqlalchemy_search_store import (
    SqlAlchemySearchStore,
)
from app.modules.matchmaking.infrastructure.users_account_status import (
    UsersAccountStatus,
)
from app.modules.player_profile.domain.ports import (
    PlayIntentDeclarationRepository,
    ImageTranscoder,
    PhotoReview,
    PhotoStorage,
    PlayerProfileRepository,
)
from app.modules.player_profile.infrastructure.event_sourced_play_intent_declaration_repository import (  # noqa: E501
    EventSourcedPlayIntentDeclarationRepository,
)
from app.modules.player_profile.infrastructure.event_sourced_player_profile_repository import (  # noqa: E501
    EventSourcedPlayerProfileRepository,
)
from app.modules.player_profile.infrastructure.clip_photo_review import (
    ClipSidecarPhotoReview,
)
from app.modules.player_profile.infrastructure.pillow_image_transcoder import (
    PillowImageTranscoder,
)
from app.modules.player_profile.infrastructure.s3_photo_storage import S3PhotoStorage
from app.modules.rating.domain.ports import AssessmentRepository, SkillRatingRepository
from app.modules.rating.infrastructure.event_sourced_assessment_repository import (
    EventSourcedAssessmentRepository,
)
from app.modules.rating.infrastructure.event_sourced_skill_rating_repository import (
    EventSourcedSkillRatingRepository,
)
from app.modules.users.domain.ports import UserRepository
from app.modules.users.infrastructure.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)

# --------------------------------------------------------------------------
# Cross-cutting adapters
# --------------------------------------------------------------------------


def build_clock() -> Clock:
    return SystemClock()


def build_unit_of_work(session: AsyncSession) -> UnitOfWork:
    return AsyncSqlAlchemyUnitOfWork(session)


def build_domain_event_store(
    session: AsyncSession,
    *,
    runtime: EventRuntime | None = None,
) -> DomainEventStore:
    """The append-only aggregate event stream, over `session`.

    `runtime` defaults to the process's, so a caller holding only a session can
    build one. It stays an argument because the event runtime is the one piece
    of this wiring a caller might legitimately replace — a worker driving a
    narrowed catalog, a test standing up its own dispatcher — and a default is
    not the same as a decision taken for everybody.
    """
    return (runtime or get_event_runtime()).create_domain_event_store_for(
        session=session
    )


def build_event_publisher(
    session: AsyncSession,
    *,
    runtime: EventRuntime | None = None,
) -> DomainEventPublisher:
    """The transactional outbox writer, over `session`. See the store above."""
    return (runtime or get_event_runtime()).create_publisher_for(session=session)


# --------------------------------------------------------------------------
# Auth
# --------------------------------------------------------------------------


def build_password_hasher() -> PasswordHasher:
    return BcryptPasswordHasher()


def build_token_service(settings: Settings) -> TokenService:
    return JwtTokenService(settings)


def build_refresh_token_repository(session: AsyncSession) -> RefreshTokenRepository:
    return SqlAlchemyRefreshTokenRepository(session)


# --------------------------------------------------------------------------
# Users
# --------------------------------------------------------------------------


def build_user_repository(session: AsyncSession) -> UserRepository:
    return SqlAlchemyUserRepository(session)


# --------------------------------------------------------------------------
# Blocks
# --------------------------------------------------------------------------


def build_block_repository(
    *,
    event_store: DomainEventStore,
    events: DomainEventPublisher,
) -> BlockRepository:
    """Per unit of work, for the same reason every aggregate repository is.

    It remembers the stream versions it loaded, so it must never be longer-lived
    than the transaction it was built beside: one request's versions must never
    answer for another's.
    """
    return EventSourcedBlockRepository(event_store=event_store, events=events)


def build_block_query(
    session: AsyncSession,
    *,
    runtime: EventRuntime | None = None,
) -> BlockQuery:
    """The one place a block is read, and the only implementation there will be.

    Over the **log**, because ``docs/adr/0095`` §4 dropped the advisory copy: the
    candidate index holds no block data at all, so there is no projection to
    choose between. It takes the codec from the event runtime rather than
    declaring the durable names a second time, for the reason the candidate index
    tail does — a re-declared published contract drifts silently.

    **Declared before its first caller exists**, deliberately: every surface that
    shows one player to another consults this port (``docs/adr/0095`` §7) and
    none of them is built. This line is what those surfaces wire to rather than
    re-deciding, and it is one line so the re-decision never happens somewhere
    else.
    """
    return EventSourcedBlockQuery(session, (runtime or get_event_runtime()).codec)


# --------------------------------------------------------------------------
# Rating
# --------------------------------------------------------------------------


def build_assessment_engine() -> AssessmentEngine:
    """The concrete engine version is chosen here, and nowhere else.

    Use cases depend on the `AssessmentEngine` abstraction, so a version swap is
    a one-line change — and it is one line rather than one per composition root,
    which is the point of this module. A seed run replaying an onboarding
    assessment gets the version the API is serving, by construction.
    """
    return RacketSkillEngineV3()


def build_assessment_repository(
    *,
    event_store: DomainEventStore,
    events: DomainEventPublisher,
) -> AssessmentRepository:
    """Takes its two ports rather than a session, so a caller decides what is
    shared. The repository remembers the stream versions it loaded, so it is
    never longer-lived than the unit of work it was built beside: one request's
    versions must never answer for another's.
    """
    return EventSourcedAssessmentRepository(event_store=event_store, events=events)


def build_skill_rating_repository(
    *,
    event_store: DomainEventStore,
    events: DomainEventPublisher,
) -> SkillRatingRepository:
    """Per unit of work, for the same reason the assessment's is."""
    return EventSourcedSkillRatingRepository(event_store=event_store, events=events)


# --------------------------------------------------------------------------
# Player profile
# --------------------------------------------------------------------------


def build_photo_storage(settings: Settings) -> PhotoStorage:
    """The object store, wherever it is.

    One class for MinIO and for S3 — see the adapter's docstring. **Which store
    is chosen is one setting, and it is read here**, so a sweep job or a
    management command reaches the same bucket a request does rather than a
    second opinion about where photos live.

    Constructing this opens no connection: an `aioboto3.Session` is credentials
    and a region, and the client that talks is made per call.
    """

    return S3PhotoStorage(
        bucket=settings.PHOTO_STORAGE_BUCKET,
        endpoint_url=settings.PHOTO_STORAGE_ENDPOINT_URL,
        public_endpoint_url=settings.PHOTO_STORAGE_PUBLIC_ENDPOINT_URL,
        region_name=settings.PHOTO_STORAGE_REGION,
        access_key_id=settings.PHOTO_STORAGE_ACCESS_KEY,
        secret_access_key=settings.PHOTO_STORAGE_SECRET_KEY,
    )


def build_image_transcoder() -> ImageTranscoder:
    return PillowImageTranscoder()


def build_photo_review(settings: Settings) -> PhotoReview:
    """The on-court check, as a client of the sidecar that holds the model.

    The concrete reviewer is chosen here and nowhere else, for the same reason
    the engine version is — and this line is the whole of what changed when the
    real check landed: no use case, route or test of the upload path changed
    shape (`docs/adr/0091`, `docs/adr/0129`).

    Constructing this opens no connection and reaches no model. Both arguments
    it takes are operational — where the sidecar is, and how long it may take —
    and neither can change a verdict; the prompts and the threshold are in
    `player_profile/domain/photos.py` where a domain test can see them.
    """

    return ClipSidecarPhotoReview(
        endpoint_url=settings.PHOTO_REVIEW_ENDPOINT_URL,
        timeout_seconds=settings.PHOTO_REVIEW_TIMEOUT_SECONDS,
    )


def build_player_profile_repository(
    *,
    event_store: DomainEventStore,
    events: DomainEventPublisher,
) -> PlayerProfileRepository:
    """Per unit of work, for the same reason the rating repositories are.

    It remembers the stream versions it loaded, so it must never be longer-lived
    than the transaction it was built beside: one request's versions must never
    answer for another's.
    """
    return EventSourcedPlayerProfileRepository(event_store=event_store, events=events)


def build_play_intent_declaration_repository(
    *,
    event_store: DomainEventStore,
    events: DomainEventPublisher,
) -> PlayIntentDeclarationRepository:
    """Per unit of work, for the same reason the profile's is.

    **Declared before its first caller exists**, which is unusual here and is
    deliberate: the aggregate and its durable contract landed with #182 so that
    the index has an event to read, while the write path — the rating tail, the
    search screen's inline offer and ``PUT /api/v1/play-intents/{sport}`` — is
    ADR-0094's own build. This line is what that build wires to rather than
    re-deciding, and it is one line so that the re-decision never happens
    somewhere else.
    """
    return EventSourcedPlayIntentDeclarationRepository(
        event_store=event_store, events=events
    )


# --------------------------------------------------------------------------
# Matchmaking — the five outward ports
# --------------------------------------------------------------------------
#
# Built before a use case asks for one, deliberately and for the reason the play
# intent repository above is: these are ``docs/adr/0098``'s consumer-driven
# contracts, and the search that reads them arrives later. **This is the live
# wiring**, and it is one line per port so the choice of implementation is made
# here rather than re-made wherever a search is assembled. The register in
# ``app/bootstrap/matcher_demands.py`` is what enrols each of them in the
# contract suite.


def build_account_hold_query(session: AsyncSession) -> AccountHoldQuery:
    """``cases`` does not exist, so nothing can hold an account.

    Takes the session every other builder takes even though this one needs
    nothing, so that swapping in a real adapter when ``cases`` lands changes this
    line and no caller.
    """
    return NoHoldsExist()


def build_account_status_query(session: AsyncSession) -> AccountStatusQuery:
    """Gate 8, live — the only outward port whose provider ships.

    Built over ``users``' own repository rather than over the session directly,
    so the set read stays the provider's and this line stays a choice of
    implementation.
    """
    return UsersAccountStatus(build_user_repository(session))


def build_player_score_query(session: AsyncSession) -> PlayerScoreQuery:
    """``player_score`` does not exist, so nobody has a Player Score."""
    return NoPlayerScoresExist()


def build_match_history_query(session: AsyncSession) -> MatchHistoryQuery:
    """``matches`` does not exist, so nobody has played anybody."""
    return NoMatchHistoryExists()


def build_at_stake_query(session: AsyncSession) -> AtStakeQuery:
    """``rating`` ships; the rule that moves a Level on a result does not."""
    return NoResultUpdateRuleExists()


def build_ruleset() -> Ruleset:
    """Which numbers the matcher runs on. **Chosen here and nowhere else.**

    ``docs/adr/0093`` ships a ruleset with the code and defers the runtime store
    until there is enough traffic for an experiment to mean anything — *its
    arrival changes only where the file is read from, never what the stamp
    guarantees*, and this is the line it changes.

    **Nothing here reads the environment.** A weight is not a setting: it is the
    product's opinion about who a player should meet, which is behaviour a domain
    test can observe, and `local`, `development`, `staging` and `production` run
    the same numbers.
    """
    return LIVE_RULESET


def build_search_store(session: AsyncSession) -> SearchStore:
    """Where the record goes. Over the **request's own** session, always.

    ``docs/adr/0104`` commits it in the request's transaction and before the
    response, so a store built over anything else — a background factory, a
    second session — would be a record that could commit without the search, or
    a search that could return without the record.
    """
    return SqlAlchemySearchStore(session)


def build_player_card_source(
    *,
    session: AsyncSession,
    event_store: DomainEventStore,
    events: DomainEventPublisher,
) -> PlayerCardSource:
    """The two card fields the index deliberately does not hold.

    Built over the **two providers' own ports** rather than over the session,
    which is the whole of what keeps the matcher from becoming a second reader of
    somebody else's schema — and it is why this builder takes an event store
    rather than only a connection: a Player profile is a stream, and folding one
    is that context's business.
    """
    return PlayerCardIdentities(
        users=build_user_repository(session),
        profiles=build_player_profile_repository(
            event_store=event_store, events=events
        ),
    )


def build_absent_terms(player_scores: PlayerScoreQuery) -> frozenset[Term]:
    """Which terms have no provider **on this platform**, as opposed to for a
    person.

    The evidence gate counts person-specific gaps and never platform-wide
    absence — a fact nobody has about anybody cannot be evidence this person
    failed to produce — so somebody has to say which is which. It is decided
    here because *no provider exists* is a fact about this wiring: it is read off
    the adapter this root just chose, so the day ``player_score`` ships and the
    line above changes, this one changes with it and nothing else does.

    A ruleset that could declare it would be a weight release deciding which
    contexts are built, which is why it is not ruleset data.
    """
    return (
        frozenset({Term.RELIABILITY})
        if isinstance(player_scores, NoPlayerScoresExist)
        else frozenset()
    )


def build_match_fit_engine() -> MatchFit:
    """The concrete scorer version is chosen here, and nowhere else.

    The same rule the assessment engine follows (``docs/adr/0015``): a caller
    depends on the ``MatchFit`` abstraction, so swapping ``v1`` for a version
    that computes a term differently is this line and no other. Nothing asks for
    one yet — the search that does arrives with the routes — and it is wired now
    for the reason the five ports above are: a choice of implementation belongs
    in a composition root whether or not a caller has turned up to make it.
    """
    return MatchFitV1()


# --------------------------------------------------------------------------
# Matchmaking — the ephemeral store
# --------------------------------------------------------------------------
#
# **Every ledger leaves here wrapped, and that is the point of building them
# here.** Exposure, suppression and the prompts fail soft
# (``the-two-contracts.md`` §8), and
# a posture applied by the composition root is one no caller can be handed
# without. An unwrapped ``RedisExposureLedger`` is a correct adapter and a wrong
# dependency: it raises, and a raise on either of these paths empties a surface
# to protect nobody.
#
# The client is passed in rather than built per ledger. It holds the process's
# one connection pool, opened by the lifespan and closed by it, so a builder
# that reached for its own would be a second pool per request.


def build_exposure_ledger(client: Redis) -> ExposureLedger:
    """Who has been shown to whom this week, failing soft."""

    return FailSoftExposureLedger(RedisExposureLedger(client))


def build_suppression_ledger(client: Redis) -> SuppressionLedger:
    """Whom this player has recently passed on, failing soft."""

    return FailSoftSuppressionLedger(RedisSuppressionLedger(client))


def build_prompt_ledger(client: Redis) -> PromptLedger:
    """The questions a loop left standing for a player, failing soft.

    The softest of the three: an outage here costs one inline offer, on one
    search, and the loop that raised it raises it again tomorrow.
    """

    return FailSoftPromptLedger(RedisPromptLedger(client))


def build_roll_exposure(exposure: ExposureLedger) -> RollExposure:
    """The hourly roll, over whichever ledger it was handed.

    Takes the port rather than the client, so the job is assembled from a ledger
    that already carries its posture — the roll has no branch for *Redis is
    down* and does not need one.
    """

    return RollExposure(exposure=exposure, clock=build_clock())


# --------------------------------------------------------------------------
# Matchmaking — the candidate index
# --------------------------------------------------------------------------
#
# The index has one writer, one per-worker reader and one one-shot repair, and
# all three are built here so that a rebuild run from a ``make`` target gets the
# wiring the API's own tail reader gets rather than a second opinion about it —
# which is the whole reason this module exists (``docs/adr/0110``).


def build_background_session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    """How every background run gets its session. **One spelling, one place.**

    ``expire_on_commit=False`` so a report built from an object survives the
    commit that ends the run, and ``autoflush=False`` because a loop should not
    be issuing statements at moments nobody chose. Both matter to what runs on
    them, so a second copy of this line is a second set of session semantics that
    nothing keeps in step with the first.
    """

    return async_sessionmaker(engine, expire_on_commit=False, autoflush=False)


def build_snapshot_horizon() -> SnapshotHorizon:
    """Whether a hole in the log can be proven permanent, on this database.

    **The two implementations are chosen here**; the dispatcher only routes, per
    session, on the dialect the session is bound to. Never on the environment —
    which holes a reader steps over is behaviour a test can observe, and
    ``docs/adr/0028`` reserves the environment for configuration.
    """

    return DialectSnapshotHorizon(
        by_dialect={"postgresql": PostgresSnapshotHorizon()},
        otherwise=NoSnapshotHorizon(),
    )


def build_candidate_index_tail(*, settings: Settings) -> CandidateIndexTail:
    """The index's only writer.

    It reads the **log**, not the outbox: the outbox orders by
    ``(created_at, id)`` and mints a row id unrelated to the event's, so an
    outbox subscriber could never name the ``sequence_no`` that
    ``snapshot_version`` is (``docs/adr/0110``). Two subscriptions, two
    guarantees.
    """

    runtime = get_event_runtime()
    return CandidateIndexTail(
        codec=runtime.codec,
        catalog=runtime.catalog,
        horizon=build_snapshot_horizon(),
        clock=build_clock(),
        batch_size=settings.CANDIDATE_INDEX_BATCH_SIZE,
    )


def build_candidate_source(
    *, session_factory: async_sessionmaker[AsyncSession]
) -> DatabaseCandidateSource:
    """This worker's own index. **One per process**, and never per request.

    A per-request source would rebuild the container a search was supposed to
    bind once, which is the whole of what ``docs/adr/0112`` buys.
    """

    return DatabaseCandidateSource(
        session_factory=session_factory, empty_at=build_clock().now()
    )


def build_rebuild_candidate_index(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> RebuildCandidateIndex:
    """The repair, reached by a ``make`` target and never by a route.

    A button that drops and rebuilds the index is a button eventually pressed in
    the wrong place.
    """

    return RebuildCandidateIndex(
        session_factory=session_factory,
        tail=build_candidate_index_tail(settings=settings),
        clock=build_clock(),
    )
