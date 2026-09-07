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
from app.modules.challenges.application.court_safety import CourtSafety
from app.modules.challenges.application.open_from_mutual_interest import (
    OpenChallengeFromMutualInterest,
)
from app.modules.challenges.domain.planned_game import PlannedGameOpening
from app.modules.challenges.infrastructure.games_planned_game import (
    GamesPlannedGame,
)
from app.modules.games.application.open_planned_game import OpenPlannedGame
from app.modules.games.domain.ports import (
    ConfirmedResultLedger,
    GameDirectory,
    GameHistoryQuery,
    GameRepository,
    PlayerHandles,
)
from app.modules.games.infrastructure.event_sourced_confirmed_results import (
    EventSourcedConfirmedResults,
)
from app.modules.games.infrastructure.event_sourced_game_history import (
    EventSourcedGameHistory,
)
from app.modules.games.infrastructure.event_sourced_game_repository import (
    EventSourcedGameRepository,
)
from app.modules.games.infrastructure.users_handles import UsersHandles
from app.modules.matchmaking.infrastructure.games_match_history import (
    GamesPlayedAndChallengesAnswered,
)
from app.modules.challenges.domain.ports import (
    AccountHoldQuery as ChallengeAccountHoldQuery,
    ChallengeDirectory,
    ChallengeHistoryQuery,
    ChallengeRepository,
    LapsingChallengeQuery,
    OpenChallengeQuery,
    OriginSearchQuery,
)
from app.modules.challenges.infrastructure.absent_providers import (
    NoHoldsExist as NoChallengeHoldsExist,
)
from app.modules.challenges.infrastructure.event_sourced_challenge_directory import (
    EventSourcedChallengeDirectory,
)
from app.modules.challenges.infrastructure.event_sourced_challenge_history import (
    EventSourcedChallengeHistory,
)
from app.modules.challenges.infrastructure.event_sourced_challenge_repository import (
    EventSourcedChallengeRepository,
)
from app.modules.challenges.infrastructure.event_sourced_lapsing_challenge_query import (  # noqa: E501
    EventSourcedLapsingChallengeQuery,
)
from app.modules.challenges.infrastructure.event_sourced_open_challenge_query import (
    EventSourcedOpenChallengeQuery,
)
from app.modules.matchmaking.domain.ports import (
    AccountHoldQuery,
    AccountStatusQuery,
    AtStakeQuery,
    MatchHistoryQuery,
    PlayerScoreQuery,
)
from app.modules.matchmaking.application.roll_exposure import RollExposure
from app.modules.matchmaking.domain.cards import (
    CardPhotoLinks,
    PlayerCardSource,
    PlayerRecordSource,
)
from app.modules.matchmaking.domain.declines import PromptDeclineLedger
from app.modules.matchmaking.domain.ledgers import ExposureLedger, SuppressionLedger
from app.modules.matchmaking.domain.prompts import PromptLedger
from app.modules.matchmaking.domain.interest import InterestLedger
from app.modules.matchmaking.domain.passes import PassLedger
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
from app.modules.matchmaking.infrastructure.absent_providers import NoHoldsExist
from app.modules.matchmaking.infrastructure.published_player_scores import (
    PublishedPlayerScores,
)
from app.modules.player_score.domain.ports import PublishedScoreQuery
from app.modules.player_score.infrastructure.two_strands_from_the_record import (
    TwoStrandsFromTheRecord,
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
from app.modules.matchmaking.infrastructure.scale_instruments import (
    ScalePressureProbe,
    ScoringMeter,
    container_memory_limit_bytes,
)
from app.modules.matchmaking.infrastructure.card_photo_links import (
    PresignedCardPhotos,
)
from app.modules.matchmaking.infrastructure.games_card_records import (
    GamesPlayedAndAgreed,
)
from app.modules.matchmaking.infrastructure.player_card_source import (
    PlayerCardIdentities,
)
from app.modules.matchmaking.infrastructure.sqlalchemy_interest_ledger import (
    SqlAlchemyInterestLedger,
)
from app.modules.matchmaking.infrastructure.sqlalchemy_pass_ledger import (
    SqlAlchemyPassLedger,
)
from app.modules.matchmaking.infrastructure.sqlalchemy_prompt_decline_ledger import (
    SqlAlchemyPromptDeclineLedger,
)
from app.modules.matchmaking.infrastructure.sqlalchemy_search_store import (
    SqlAlchemySearchStore,
)
from app.modules.matchmaking.domain.mutual_challenge import (
    MutualChallengeMinting,
)
from app.modules.matchmaking.infrastructure.challenges_match_history import (
    ChallengesButNobodyHasPlayed,
)
from app.modules.matchmaking.infrastructure.challenges_mutual_challenge import (
    ChallengesMutualChallenge,
)
from app.modules.matchmaking.infrastructure.search_court_origin import (
    SearchCourtOrigin,
)
from app.modules.matchmaking.infrastructure.rating_at_stake import (
    RatingResultUpdateRule,
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
from app.modules.rating.application.settle_results import SettleRatingsOnResults
from app.modules.rating.domain.ports import (
    AssessmentRepository,
    RatedPlayerQuery,
    SkillRatingRepository,
)
from app.modules.rating.infrastructure.event_sourced_rated_players import (
    EventSourcedRatedPlayers,
)
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
# Challenges
# --------------------------------------------------------------------------


def build_challenge_repository(
    *,
    event_store: DomainEventStore,
    events: DomainEventPublisher,
) -> ChallengeRepository:
    """Per unit of work, for the same reason every aggregate repository is.

    It remembers the stream versions it loaded, so it must never be longer-lived
    than the transaction it was built beside: one send's versions must never
    answer for another's.
    """
    return EventSourcedChallengeRepository(event_store=event_store, events=events)


def build_open_challenge_query(
    session: AsyncSession,
    *,
    runtime: EventRuntime | None = None,
) -> OpenChallengeQuery:
    """*Are any two of these people already arranging a game?*

    Over the **log**, because the standing is derived from the seats and the
    clock and a projection of it would be a status column with a table around
    it — right until a deadline passed, wrong until something swept it, and
    believed throughout. It takes the codec from the event runtime rather than
    declaring the durable names a second time, for the reason the block query
    does: a re-declared published contract drifts silently.
    """
    return EventSourcedOpenChallengeQuery(
        session, (runtime or get_event_runtime()).codec
    )


def build_challenge_directory(
    session: AsyncSession,
    *,
    runtime: EventRuntime | None = None,
) -> ChallengeDirectory:
    """*What have I been asked, and what have I asked for* — over the log.

    Over the log for the reason the open-challenge query is: there is no standing
    to project, because a standing is a fold of the seats against a clock and a
    stored one would be wrong for the whole gap between a deadline and a sweep.
    """
    return EventSourcedChallengeDirectory(
        session, (runtime or get_event_runtime()).codec
    )


def build_lapsing_challenge_query(session: AsyncSession) -> LapsingChallengeQuery:
    """The candidate set the lapse loop opens — over the log, and with no codec.

    The only read in this context that needs no ``EventCodec``: it answers with
    stream ids and the loop replays each one through the repository, so decoding
    them here would be the same stream read twice.
    """
    return EventSourcedLapsingChallengeQuery(session)


def build_challenge_hold_query(session: AsyncSession) -> ChallengeAccountHoldQuery:
    """``cases`` does not exist, so nothing can hold an account.

    **The second line in this file that says so**, and the duplication is the
    decision rather than an oversight: ``challenges`` declares its own hold port
    because it may not import the matcher, and a shared declaration would mean a
    send reading a safety fact through a context it was split away from. On the
    day ``cases`` ships, this line and ``build_account_hold_query`` change to the
    same adapter.
    """
    return NoChallengeHoldsExist()


def build_court_safety(session: AsyncSession) -> CourtSafety:
    """The four fail-closed gates, over the providers that own each fact.

    Three of the four are somebody else's shipped port — ``blocks``, ``users``
    and ``player_profile`` — and only the hold is answered by an empty provider.
    Assembled here rather than at each surface so that the send and the
    mutual-born mint cannot come to two answers about which reads fail closed.
    """
    return CourtSafety(
        blocks=build_block_query(session),
        holds=build_challenge_hold_query(session),
        accounts=build_user_repository(session),
        profiles=build_player_profile_repository(
            event_store=build_domain_event_store(session),
            events=build_event_publisher(session),
        ),
    )


def build_origin_search_query(session: AsyncSession) -> OriginSearchQuery:
    """What the search a court was built on says about that court.

    An outward demand ``challenges`` makes and the matcher signs, so the adapter
    is the matcher's and this line is where the two meet. The alternative — a
    window and a position on the request body — is the one thing
    ``docs/adr/0100`` has no picker for and the one thing the origin key may not
    take a client's word for.
    """
    return SearchCourtOrigin(build_search_store(session))


def build_mutual_challenge_minting(
    session: AsyncSession,
    *,
    runtime: EventRuntime | None = None,
) -> MutualChallengeMinting:
    """The challenge two yeses that met open, minted inline.

    It wraps a ``challenges`` use case rather than an aggregate: what a
    mutual-born challenge *is* belongs to that context, and the adapter is a
    translation of one sentence into another.

    **No unit of work here.** The mint joins the transaction of the yes that
    caused it, so the use case appends and publishes and the caller commits — the
    boundary stays a decision about the command.
    """
    return ChallengesMutualChallenge(
        OpenChallengeFromMutualInterest(
            challenges=build_challenge_repository(
                event_store=build_domain_event_store(session),
                events=build_event_publisher(session),
            ),
            open_challenges=build_open_challenge_query(session, runtime=runtime),
            safety=build_court_safety(session),
            clock=build_clock(),
            planned_games=build_planned_game_opening(session, runtime=runtime),
        )
    )


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


def build_published_score_query(session: AsyncSession) -> PublishedScoreQuery:
    """``player_score``, over the two contexts that keep a record of anything.

    It is built from the two providers' own published ports rather than from the
    session, so this line stays a choice of implementation and the folds behind
    it stay with the contexts that own them.
    """
    return TwoStrandsFromTheRecord(
        games=build_game_history_query(session),
        challenges=build_challenge_history_query(session),
    )


def build_player_score_query(session: AsyncSession) -> PlayerScoreQuery:
    """``player_score`` ships, so a Player Score is a real answer.

    **The third null object to retire by its own stated fact becoming false**
    (``docs/adr/0095``, ``docs/adr/0140``). ``NoPlayerScoresExist`` said *nobody
    has a Player Score, because nobody has ever been due to play*, and that was
    true until ``games`` recorded a plan that produced a game or did not. Swapping
    it is one row in the register and this line, exactly as ADR-0095 promised.

    **It is also why ``build_absent_terms`` below now takes no argument.** That
    function used to read the adapter this line chose, because *reliability has no
    provider* was a fact about this wiring; there is no longer anything to read,
    so the set is empty and the parameter went with the null object.
    """
    return PublishedPlayerScores(build_published_score_query(session), build_clock())


def build_challenge_history_query(
    session: AsyncSession,
    *,
    runtime: EventRuntime | None = None,
) -> ChallengeHistoryQuery:
    """What ``challenges`` owes the matcher — over the log, like its two siblings.

    Over the log rather than a projection for the reason the open-challenge query
    and the directory are: *open* is a fold of the seats against a clock, and a
    stored standing would be wrong for the whole gap between a deadline passing
    and a sweep noticing it.
    """
    return EventSourcedChallengeHistory(
        session, (runtime or get_event_runtime()).codec
    )


# --------------------------------------------------------------------------
# Games
# --------------------------------------------------------------------------


def build_game_repository(
    *,
    session: AsyncSession,
    event_store: DomainEventStore,
    events: DomainEventPublisher,
) -> GameRepository:
    """Per unit of work, for the same reason every aggregate repository is.

    It takes the session as well as the store, because one of its reads is a
    lookup by payload: *has this challenge already opened a game*, which is what
    makes the opening idempotent inside the accept's own transaction.
    """
    return EventSourcedGameRepository(
        event_store=event_store, events=events, session=session
    )


def build_planned_game_opening(
    session: AsyncSession,
    *,
    runtime: EventRuntime | None = None,
) -> PlannedGameOpening:
    """The game a completed line-up opens, recorded inline.

    It wraps a ``games`` use case rather than an aggregate: what a game born of a
    completed line-up *is* belongs to that context, and the adapter is a
    translation of one sentence into another.

    **No unit of work here.** The opening joins the transaction of the acceptance
    that caused it, so the use case appends and publishes and the caller commits —
    the boundary stays a decision about the command.
    """
    return GamesPlannedGame(
        OpenPlannedGame(
            games=build_game_repository(
                session=session,
                event_store=build_domain_event_store(session, runtime=runtime),
                events=build_event_publisher(session, runtime=runtime),
            )
        )
    )


def build_game_history_query(
    session: AsyncSession,
    *,
    runtime: EventRuntime | None = None,
) -> GameHistoryQuery:
    """What ``games`` owes the rest of the platform — over the log.

    Over the log rather than a projection for the reason every read in
    ``challenges`` is: the standing is a fold of the record against a clock, and
    a stored one would be wrong for the whole gap between a deadline passing and
    anything noticing — with nothing to notice it, because this context has no
    sweep.
    """
    return EventSourcedGameHistory(session, (runtime or get_event_runtime()).codec)


def build_player_handles(session: AsyncSession) -> PlayerHandles:
    """*What is this person called* — the one thing ``games`` borrows about one.

    Built from ``users``' own repository rather than from the session, so this
    line stays a choice of implementation and the fold behind it stays with the
    context that owns it (``docs/adr/0141``).
    """
    return UsersHandles(build_user_repository(session))


def build_game_directory(
    session: AsyncSession,
    *,
    runtime: EventRuntime | None = None,
) -> GameDirectory:
    """*Which games was I on the court of* — the same read, folded whole.

    One class answers both ports so a screen wanting the aggregates and a search
    wanting the counts do not run the same substring match twice. They stay two
    ports: a caller that wants counts has no business holding the aggregates.
    """
    return EventSourcedGameHistory(session, (runtime or get_event_runtime()).codec)


def build_match_history_query(session: AsyncSession) -> MatchHistoryQuery:
    """``challenges`` and ``games``, composed into one bounded read.

    **The one outward port with two providers, and the split is by fact rather
    than by contract** (``docs/adr/0098`` as amended, ``docs/adr/0137``).
    ``ACCEPTED`` and ``DECLINED`` are challenge facts and ``PLAYED`` and
    ``PLANNED_NEVER_PLAYED`` are ``games``', and the seam runs *through*
    ``pairwise_counterparts`` — so the port stays whole and the second provider
    arrives here as a **composition** rather than as a second contract.

    The clock is built here rather than taken, because *open* and *a plan whose
    window has closed* are both facts about the instant the read happens, and a
    caller holding one could hold a stale one.
    """
    return GamesPlayedAndChallengesAnswered(
        challenges=ChallengesButNobodyHasPlayed(
            build_challenge_history_query(session), build_clock()
        ),
        games=build_game_history_query(session),
        clock=build_clock(),
    )


def build_rated_player_query(
    session: AsyncSession,
    *,
    runtime: EventRuntime | None = None,
) -> RatedPlayerQuery:
    """Levels read and never held, over the rating streams.

    Narrower than ``build_skill_rating_repository`` on purpose: that one
    remembers stream versions so a rating it found can be saved, and a reader
    that only wants two floats has no business with the path that could move
    them.
    """
    return EventSourcedRatedPlayers(
        event_store=build_domain_event_store(session, runtime=runtime)
    )


def build_at_stake_query(
    session: AsyncSession,
    *,
    runtime: EventRuntime | None = None,
) -> AtStakeQuery:
    """``rating``'s own result-update rule, read forward (``docs/adr/0139``).

    **The second of the three null objects to retire.** ``NoResultUpdateRuleExists``
    said something true — *nobody's Level has ever moved on a result, because
    nothing moves it* — and stopped being true the day the rule landed, which is
    exactly when a null object is swapped rather than narrowed.

    Built per request, because the adapter memoises the Levels it reads for the
    life of one search and a longer-lived one would be a cache of numbers that
    move.
    """
    return RatingResultUpdateRule(build_rated_player_query(session, runtime=runtime))


def build_confirmed_result_ledger(
    session: AsyncSession,
    *,
    runtime: EventRuntime | None = None,
) -> ConfirmedResultLedger:
    """Confirmed counted results, oldest first — the read with no subscriber.

    A second adapter beside ``EventSourcedGameHistory`` rather than a method on
    it, because it starts from nobody: every read there begins *which streams
    seat this person*, and this one has no player to ask about until it has
    folded the game.
    """
    return EventSourcedConfirmedResults(
        session, (runtime or get_event_runtime()).codec
    )


def build_settle_ratings_on_results(
    session: AsyncSession,
    *,
    runtime: EventRuntime | None = None,
) -> SettleRatingsOnResults:
    """The catch-up, wired the way a request is.

    The clock is built here rather than taken, because *has this result settled*
    is a fact about the instant the run happens and a caller holding one could
    hold a stale one — the same argument the composed match-history read makes.
    """
    resolved = runtime or get_event_runtime()
    event_store = build_domain_event_store(session, runtime=resolved)
    return SettleRatingsOnResults(
        results=build_confirmed_result_ledger(session, runtime=resolved),
        ratings=build_skill_rating_repository(
            event_store=event_store,
            events=build_event_publisher(session, runtime=resolved),
        ),
        uow=build_unit_of_work(session),
        clock=build_clock(),
    )


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


def build_interest_ledger(session: AsyncSession) -> InterestLedger:
    """The durable *Let's play* ledger, over the caller's own session.

    Over the session and never over a connection of its own, for the reason the
    search store is: a yes and the origin key that proves it belong to one
    transaction, and the write is committed by the use case that made both
    decisions.

    **No fail-soft wrapper.** The two Redis ledgers are wrapped where they are
    built, because losing a courtesy costs a search its spread; this one is the
    only read that can *admit* somebody, so a lost answer is a person who was
    guaranteed a place and silently did not get one. It fails the way the record
    beside it does.
    """

    return SqlAlchemyInterestLedger(session)


def build_pass_ledger(session: AsyncSession) -> PassLedger:
    """The durable record of every pass, over the caller's own session.

    **No fail-soft wrapper**, and the contrast with the suppression ledger built
    beside it is the whole design: that one is the *gate* and may be lost for the
    price of a repeated card, and this one is the *evidence* and may not. A pass
    whose row could not be written is a pass that did not happen, and the route
    says so rather than suppressing quietly against nothing.
    """

    return SqlAlchemyPassLedger(session)


def build_prompt_decline_ledger(session: AsyncSession) -> PromptDeclineLedger:
    """The durable record of every *not now*, over the caller's own session.

    **No fail-soft wrapper**, and the contrast with the prompt ledger built below
    is the whole design: that one holds a question a loop left standing and may
    be lost for the price of an offer nobody sees this week, and this one holds a
    player's answer and may not. A decline whose row could not be written is a
    decline that did not happen, and the route says so rather than going quiet
    against nothing.

    The read that consults it degrades on its own, at its one call site, and it
    degrades the other way from everything in ``fail_soft_ledgers.py`` — to
    *every* prompt silenced, which is no prompt at all.
    """

    return SqlAlchemyPromptDeclineLedger(session)


def build_player_card_source(
    *,
    session: AsyncSession,
    event_store: DomainEventStore,
    events: DomainEventPublisher,
    storage: PhotoStorage,
) -> PlayerCardSource:
    """The three card fields the index deliberately does not hold.

    Built over the **three providers' own ports** rather than over the session,
    which is the whole of what keeps the matcher from becoming a second reader of
    somebody else's schema — and it is why this builder takes an event store
    rather than only a connection: a Player profile is a stream, and folding one
    is that context's business.

    The third provider is the photo store, and it arrives here for the same
    reason its neighbour ``build_card_photo_links`` does: what the on-court check
    concluded rides on the object beside the bytes (``docs/adr/0138``), and where
    a photograph lives is the Player profile's business rather than the
    matcher's.
    """
    return PlayerCardIdentities(
        users=build_user_repository(session),
        profiles=build_player_profile_repository(
            event_store=event_store, events=events
        ),
        photos=storage,
    )


def build_player_record_source(session: AsyncSession) -> PlayerRecordSource:
    """The card's record block — what the platform watched this person do.

    Over ``games``' **own published port** rather than its streams, exactly as
    ``build_match_history_query`` above is: the fold that decides whether a game
    counted and whether its result settled belongs to the context that owns the
    log, and a second one written for a card would part company with it on the
    first window that moved.

    The clock is built here rather than taken, for the reason that builder gives:
    both of those are folds against the instant the read happens, and a caller
    holding one could hold a stale one.
    """

    return GamesPlayedAndAgreed(
        games=build_game_history_query(session), clock=build_clock()
    )


def build_card_photo_links(
    *, storage: PhotoStorage, settings: Settings
) -> CardPhotoLinks:
    """The address a card's photograph is drawn from, minted per response.

    Over the **photo provider's own port**, exactly as the card source is over
    theirs: where a photograph lives is that context's business, and a key
    written here would be a second answer to it.

    **The window is read here**, from the one setting every photo link in this
    platform is signed for — so a card and ``GET /photos/{id}`` cannot disagree
    about how long a link may live, and the route that declares this adapter
    does not get to name a number.
    """

    return PresignedCardPhotos(
        storage=storage, valid_for_minutes=settings.PHOTO_URL_VALID_FOR_MINUTES
    )


def build_absent_terms() -> frozenset[Term]:
    """Which terms have no provider **on this platform**, as opposed to for a
    person. **Today: none of them.**

    The evidence gate counts person-specific gaps and never platform-wide
    absence — a fact nobody has about anybody cannot be evidence this person
    failed to produce — so somebody has to say which is which. It is decided
    here because *no provider exists* is a fact about this wiring rather than
    about any ruleset: a ruleset that could declare it would be a weight release
    deciding which contexts are built.

    **It used to be read off the adapter chosen above, and there is nothing left
    to read.** Reliability was the last absent term and ``player_score`` ships
    (``docs/adr/0140``), so the set is empty and the argument that used to decide
    it has gone with the null object it was inspecting. The function stays,
    because *a term the engine weighs before its provider exists* is a live
    situation with a live rule — this is where the next one is declared, and
    ``live_terms`` refuses a name no mode weights, so a stale entry here is a red
    build rather than a quietly narrower gate.
    """
    return frozenset()


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


def build_scoring_meter() -> ScoringMeter:
    """This worker's scoring histogram. **One per process**, like the index.

    Trigger 1 is stated *on one worker over 15 min* (``scale-posture.md`` §4), so
    a per-request meter would measure one request and a meter shared across
    processes would measure a fleet — and neither is the number the trigger is
    written about.
    """

    return ScoringMeter()


def build_scale_pressure_probe(
    *, meter: ScoringMeter, settings: Settings
) -> ScalePressureProbe:
    """The loop-lag monitor that closes this worker's scoring window.

    Built here rather than in ``jobs.py`` for the reason every adapter is: the
    job register says *what* meets *how often* and holds no wiring of its own.

    The interval reaches the probe as well as the ``PeriodicJob``, and it has to
    be the same number in both: the probe's reading is *how much later than the
    interval the loop got back to it*, so a probe told one cadence and scheduled
    on another would report the difference between two settings as contention.
    """

    return ScalePressureProbe(
        meter, interval_seconds=settings.SCALE_PRESSURE_INTERVAL_SECONDS
    )


def build_container_memory_limit() -> int | None:
    """This container's memory limit, or ``None`` where there is not one.

    Read through the root rather than by a job reaching at ``/sys`` itself, and
    read **once** per process by its caller: a limit does not change while a
    container runs, and re-reading a cgroup file every two seconds is a syscall
    per tick to learn the same number.
    """

    return container_memory_limit_bytes()


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
