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
from app.modules.challenges.domain.friendly_choice import FriendlyChoiceQuery
from app.modules.challenges.domain.game_of_court import GameOfCourtQuery
from app.modules.challenges.domain.planned_game import PlannedGameHandover
from app.modules.challenges.domain.seatable_game import SeatableGameQuery
from app.modules.challenges.domain.settled_game import SettledGameQuery
from app.modules.challenges.infrastructure.games_game_of_court import (
    GamesGameOfCourt,
)
from app.modules.challenges.infrastructure.games_planned_game import (
    GamesPlannedGame,
)
from app.modules.challenges.infrastructure.games_seatable_game import (
    GamesSeatableGame,
)
from app.modules.challenges.infrastructure.games_settled_game import (
    GamesSettledGame,
)
from app.modules.challenges.infrastructure.profile_friendly_choice import (
    ProfileFriendlyChoice,
)
from app.modules.games.application.call_off_game import CallOffGame
from app.modules.games.application.dismiss_game import DismissGameOfCourt
from app.modules.games.application.open_planned_game import OpenPlannedGame
from app.modules.games.application.vacate_seat import VacateSeat
from app.modules.conversations.application.a_room_of_yours import ARoomOfYours
from app.modules.conversations.application.destroy_ended_conversations import (
    DestroyEndedConversations,
)
from app.modules.conversations.application.lifetime import Lifetime
from app.modules.conversations.application.membership import Membership
from app.modules.conversations.application.tell_the_room import TellTheRoom
from app.modules.conversations.domain.ports import (
    AccountHoldQuery as ConversationAccountHoldQuery,
    ArrangingCourt,
    ConversationDirectory,
    ConversationRepository,
    MemberFaces,
    PlayedCourt,
)
from app.modules.conversations.domain.live import (
    NudgePublisher,
    NudgeSubscriber,
    TypingHeartbeat,
    TypingRoster,
)
from app.modules.conversations.application.follow_conversation import (
    FollowConversation,
)
from app.modules.conversations.infrastructure.fail_soft_nudges import (
    FailSoftNudgePublisher,
)
from app.modules.conversations.infrastructure.fail_soft_typing import (
    FailSoftTypingHeartbeat,
    FailSoftTypingRoster,
)
from app.modules.conversations.infrastructure.redis_live_channel import (
    RedisNudgePublisher,
    RedisNudgeSubscriber,
)
from app.modules.conversations.infrastructure.redis_typing_presence import (
    RedisTypingHeartbeat,
    RedisTypingRoster,
)
from app.modules.conversations.infrastructure.absent_providers import (
    NobodyIsFollowing,
    NoHoldsExist as NoConversationHoldsExist,
)
from app.modules.conversations.infrastructure.challenges_arranging_court import (
    ChallengesArrangingCourt,
)
from app.modules.conversations.infrastructure.event_sourced_conversation_repository import (  # noqa: E501
    EventSourcedConversationRepository,
)
from app.modules.conversations.infrastructure.games_played_court import (
    GamesPlayedCourt,
)
from app.modules.conversations.infrastructure.profile_member_faces import (
    ProfileMemberFaces,
)
from app.modules.conversations.infrastructure.sqlalchemy_conversation_directory import (  # noqa: E501
    SqlAlchemyConversationDirectory,
)
from app.modules.games.domain.ports import (
    AgreedMoment,
    ConfirmedResultLedger,
    CourtPairing,
    GameDirectory,
    GameHistoryQuery,
    GameRepository,
    OpponentVarietyQuery,
    PlayerNames,
    SeatableCourt,
)
from app.modules.games.infrastructure.event_sourced_confirmed_results import (
    EventSourcedConfirmedResults,
)
from app.modules.games.infrastructure.event_sourced_game_history import (
    EventSourcedGameHistory,
)
from app.modules.games.infrastructure.event_sourced_seatable_court import (
    EventSourcedSeatableCourt,
)
from app.modules.plans.infrastructure.games_agreed_moment import PlansAgreedMoment
from app.modules.games.infrastructure.event_sourced_game_repository import (
    EventSourcedGameRepository,
)
from app.modules.games.infrastructure.users_names import UsersNames
from app.modules.matchmaking.infrastructure.games_shared_courts import (
    GamesSharedCourts,
)
from app.modules.matchmaking.infrastructure.games_match_history import (
    GamesPlayedAndChallengesAnswered,
)
from app.modules.challenges.domain.ports import (
    AccountHoldQuery as ChallengeAccountHoldQuery,
    ChallengeDirectory,
    ChallengeHistoryQuery,
    ChallengeRepository,
    CourtPairingQuery,
    LapsingChallengeQuery,
    LeftCourtQuery,
    OpenChallengeQuery,
    OriginSearchQuery,
    PlayerNames as ChallengePlayerNames,
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
from app.modules.challenges.infrastructure.event_sourced_left_court_query import (
    EventSourcedLeftCourtQuery,
)
from app.modules.challenges.infrastructure.users_names import (
    UsersNames as ChallengeUsersNames,
)
from app.modules.challenges.infrastructure.event_sourced_open_challenge_query import (
    EventSourcedOpenChallengeQuery,
)
from app.modules.matchmaking.domain.ports import (
    AccountHoldQuery,
    AccountStatusQuery,
    AtStakeQuery,
    HalfBuiltCourtQuery,
    MatchHistoryQuery,
    PlayerScoreQuery,
    SharedCourtQuery,
)
from app.modules.matchmaking.application.fail_closed_gates import (
    FailClosedGates,
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
from app.modules.matchmaking.domain.deck_reset import DeckResetLedger
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
from app.modules.player_score.infrastructure.three_strands_from_the_record import (
    ThreeStrandsFromTheRecord,
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
from app.modules.matchmaking.infrastructure.sqlalchemy_deck_reset_ledger import (
    SqlAlchemyDeckResetLedger,
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
from app.modules.matchmaking.infrastructure.challenges_half_built_court import (
    ChallengesHalfBuiltCourts,
)
from app.modules.matchmaking.infrastructure.challenges_match_history import (
    ChallengesButNobodyHasPlayed,
)
from app.modules.matchmaking.infrastructure.challenges_mutual_challenge import (
    ChallengesMutualChallenge,
)
from app.modules.matchmaking.application.pair_with_a_court import PairWithACourt
from app.modules.matchmaking.application.search_workbench import SearchWorkbench
from app.modules.matchmaking.domain.candidate_snapshot import CandidateSource
from app.modules.matchmaking.infrastructure.challenge_court_cards import (
    ChallengeCourtCards,
    NoCourtCanBePriced,
)
from app.modules.matchmaking.infrastructure.games_court_pairing import (
    GamesCourtPairing,
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
from app.modules.plans.application.read_plans import ReadPlans
from app.modules.plans.domain.ports import (
    AccountHoldQuery as PlanAccountHoldQuery,
    PlanDirectory,
    PlannableCourts,
    PlanRepository,
)
from app.modules.plans.infrastructure.absent_providers import (
    NoHoldsExist as NoPlanHoldsExist,
)
from app.modules.plans.infrastructure.event_sourced_plan_repository import (
    EventSourcedPlanDirectory,
    EventSourcedPlanRepository,
)
from app.modules.plans.infrastructure.plannable_courts import (
    ChallengesAndGamesPlannableCourts,
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
from app.modules.player_record.infrastructure.games_subject_form import (
    GamesSubjectForm,
)
from app.modules.player_record.infrastructure.games_subject_variety import (
    GamesSubjectVariety,
)
from app.modules.player_record.infrastructure.published_subject_sportsmanship import (
    PublishedSubjectSportsmanship,
)
from app.modules.player_record.infrastructure.rating_subject_ratings import (
    RatingSubjectRatings,
)
from app.modules.player_record.infrastructure.score_subject_reliability import (
    ScoreSubjectReliability,
)
from app.modules.player_record.domain.ports import (
    PriorDisclosure,
    RecordGates,
    RecordPhotoLink,
    SubjectForm,
    SubjectIdentitySource,
    SubjectRatings,
    SubjectReliability,
    SubjectSportsmanship,
    SubjectVariety,
)
from app.modules.player_record.infrastructure.disclosures import (
    ChallengesTheyShare,
    GamesTheyPlayed,
    SearchesThatShowedThem,
)
from app.modules.player_record.infrastructure.live_record_gates import (
    LiveRecordGates,
)
from app.modules.player_record.infrastructure.presigned_record_photo import (
    PresignedRecordPhoto,
)
from app.modules.player_record.infrastructure.subject_identities import (
    ProfileAndAccountIdentity,
)
from app.modules.sportsmanship.domain.ports import (
    PublishedSportsmanshipQuery,
    SettledCourts,
    SportsmanshipLedger,
)
from app.modules.sportsmanship.infrastructure.games_settled_courts import (
    GamesSettledCourts,
)
from app.modules.sportsmanship.infrastructure.sqlalchemy_standing_answers import (
    StandingAnswersAboutThem,
)
from app.modules.sportsmanship.infrastructure.sqlalchemy_sportsmanship_ledger import (
    SqlAlchemySportsmanshipLedger,
)
from app.modules.users.application.set_tester_mark import SetTesterMark
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


def build_set_tester_mark(
    session: AsyncSession,
    *,
    runtime: EventRuntime | None = None,
) -> SetTesterMark:
    """The tester mark, reached by ``make tester`` and never by a route
    (``docs/adr/0180`` §9) — wired here so the command gets the wiring a request
    would, rather than a second opinion about it."""

    resolved = runtime or get_event_runtime()
    return SetTesterMark(
        users=build_user_repository(session),
        event_store=build_domain_event_store(session, runtime=resolved),
        uow=build_unit_of_work(session),
        clock=build_clock(),
        events=build_event_publisher(session, runtime=resolved),
    )


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


def build_left_court_query(session: AsyncSession) -> LeftCourtQuery:
    """The candidate set the hour loop opens — over the log, and with no codec,
    on the lapse read's argument (``docs/adr/0175`` §3)."""
    return EventSourcedLeftCourtQuery(session)


def build_challenge_names(session: AsyncSession) -> ChallengePlayerNames:
    """*What is this person called* — the one thing a challenge **list** borrows.

    The second line in this file building a names adapter, and the second
    ``UsersNames`` class behind it: ``challenges`` and ``games`` each declare
    the port because neither may import the other, so the two are aliased apart
    here rather than one context signing the other's (``docs/adr/0143`` §7).
    """
    return ChallengeUsersNames(build_user_repository(session))


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


def build_court_pairing_query(
    *,
    session: AsyncSession,
    clock: Clock,
    unit_of_work: UnitOfWork,
    event_store: DomainEventStore,
    events: DomainEventPublisher,
    settings: Settings,
    store: Redis | None,
    candidates: CandidateSource | None,
) -> CourtPairingQuery:
    """Who the people on a court are, and what the reader makes of each of them.

    The second outward demand ``challenges`` makes of the matcher and the second
    line here where the two meet — ``build_origin_search_query``'s shape, one
    screen later (``docs/adr/0143`` §4). It is the **expensive** one: a search
    context bound live, the whole Fit stack run over the court, a card assembled
    per person and a photograph signed for each, so it is wired to a route a tap
    opens and never to a list.

    **Everything it needs is a whole workbench**, because the pairing is
    recomputed through the same code path a search runs rather than replayed from
    a record — which is the only shape under which a challenge born of a search
    and one born of a mutual yes render the same way, and the only one under
    which *Match score for you* is true.

    ``candidates`` is ``None`` in a process with no index, and ``store`` is
    ``None`` where the ephemeral store never came up. Neither is a refusal here:
    both reach the reader as *the pairing could not be read*, because answering a
    challenge is not gated on the matcher.

    **Two entry points and one assembly.** This one is the route's, over the
    connections a request holds; :func:`build_court_pairing_query_over` is the
    same wiring over the two seams a demands suite supplies itself, so what the
    suite exercises is what ships rather than a second construction of it.
    """

    if candidates is None or store is None:
        return NoCourtCanBePriced()
    return build_court_pairing_query_over(
        workbench=build_court_pairing_workbench(
            session=session,
            clock=clock,
            unit_of_work=unit_of_work,
            event_store=event_store,
            events=events,
            settings=settings,
            exposure=build_exposure_ledger(store),
            candidates=candidates,
        ),
        settings=settings,
    )


def build_court_pairing_query_over(
    *, workbench: SearchWorkbench, settings: Settings
) -> CourtPairingQuery:
    """The adapter itself, over a workbench the caller already holds.

    **A workbench is taken rather than built, because a caller may already have
    one.** A seed run assembles one for its searches and then reads a challenge
    screen through it; building a second over the same session would be four
    objects over one table, which is the thing ``app/seeds/paths.py`` says in as
    many words about its own stores.
    """

    storage = build_photo_storage(settings)
    return ChallengeCourtCards(
        pairing=PairWithACourt(
            workbench=workbench,
            ruleset=build_ruleset(),
            engine=build_match_fit_engine(),
        ),
        photos=build_card_photo_links(storage=storage, settings=settings),
    )


def build_game_court_pairing(
    *,
    session: AsyncSession,
    clock: Clock,
    unit_of_work: UnitOfWork,
    event_store: DomainEventStore,
    events: DomainEventPublisher,
    settings: Settings,
    store: Redis | None,
    candidates: CandidateSource | None,
) -> CourtPairing:
    """What the matcher makes of a game's court, for the reader (``docs/adr/0161``).

    The one outward demand ``games`` makes of the matcher, and the third line
    here where a court is priced for somebody already on it —
    ``build_court_pairing_query``'s shape, one screen later. It is wired to a
    route a tap opens and never to a list, for the same reason that one is: the
    whole Fit stack runs over the court.

    ``candidates`` is ``None`` in a process with no index, and ``store`` is
    ``None`` where the ephemeral store never came up. Neither is a refusal, and
    neither is a null object either: the forecast needs the matcher and the
    seats and the stakes do not, so a process with no index still names every
    Level on the court and prices it, and draws no forecast. That is the
    adapter with no arranger, and not a second class.

    **Two entry points and one assembly**, as beside it: this one is the
    route's, over the connections a request holds, and
    :func:`build_game_court_pairing_over` is the same wiring over a workbench a
    caller already holds.
    """

    if candidates is None or store is None:
        return build_game_court_pairing_over(session=session, workbench=None)
    return build_game_court_pairing_over(
        session=session,
        workbench=build_court_pairing_workbench(
            session=session,
            clock=clock,
            unit_of_work=unit_of_work,
            event_store=event_store,
            events=events,
            settings=settings,
            exposure=build_exposure_ledger(store),
            candidates=candidates,
        ),
    )


def build_game_court_pairing_over(
    *, session: AsyncSession, workbench: SearchWorkbench | None
) -> CourtPairing:
    """The adapter itself, over a workbench the caller already holds — or none.

    Three things composed and none of them new: the pairing use case the
    challenge card is built on, the at-stake rule read forward, and ``rating``'s
    published read for the seats — the last two over the session, exactly as
    the workbench's own at-stake read is. ``workbench`` is ``None`` where this
    process cannot price a court, and the two session reads are built
    regardless, because they need no workbench.
    """

    return GamesCourtPairing(
        arranger=(
            None
            if workbench is None
            else PairWithACourt(
                workbench=workbench,
                ruleset=build_ruleset(),
                engine=build_match_fit_engine(),
            )
        ),
        at_stake=build_at_stake_query(session),
        ratings=build_rated_player_query(session),
    )


def build_court_pairing_workbench(
    *,
    session: AsyncSession,
    clock: Clock,
    unit_of_work: UnitOfWork,
    event_store: DomainEventStore,
    events: DomainEventPublisher,
    settings: Settings,
    exposure: ExposureLedger,
    candidates: CandidateSource,
) -> SearchWorkbench:
    """A workbench for a caller that holds no other reason to have one.

    The two seams a demands suite supplies for itself: the candidate index is the
    **process's** rather than the request's (``docs/adr/0112``), and the exposure
    ledger is Redis, which no test in this repository needs running.

    Everything else is built from the session, because this caller shares none of
    it with anything — which is exactly what makes it safe to build here and
    exactly why a caller who *does* share passes their own workbench instead.
    """

    storage = build_photo_storage(settings)
    return SearchWorkbench(
                clock=clock,
                ruleset=build_ruleset(),
                searches=build_search_store(session),
                unit_of_work=unit_of_work,
                candidates=candidates,
                profiles=build_player_profile_repository(
                    event_store=event_store, events=events
                ),
                ratings=build_skill_rating_repository(
                    event_store=event_store, events=events
                ),
                declarations=build_play_intent_declaration_repository(
                    event_store=event_store, events=events
                ),
                blocks=build_block_query(session),
                holds=build_account_hold_query(session),
                account_status=build_account_status_query(session),
                history=build_match_history_query(session),
                player_scores=build_player_score_query(session),
                at_stake=build_at_stake_query(session),
                exposure=exposure,
                interest=build_interest_ledger(session),
                cards=build_player_card_source(
                    session=session,
                    event_store=event_store,
                    events=events,
                    storage=storage,
                ),
        records=build_player_record_source(session),
        absent_terms=build_absent_terms(),
        # **Nothing is recorded and nothing is measured.** The meter reports the
        # scoring stage of a *search*, and this is not one.
        meter=None,
    )


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
            settled_games=build_settled_game_query(session, runtime=runtime),
            safety=build_court_safety(session),
            clock=build_clock(),
            planned_games=build_planned_game_handover(session, runtime=runtime),
            friendly_choices=build_friendly_choice_query(session, runtime=runtime),
        )
    )


def build_friendly_choice_query(
    session: AsyncSession,
    *,
    runtime: EventRuntime | None = None,
) -> FriendlyChoiceQuery:
    """*Which of these two declared* for fun *in this sport?* — what the mutual
    mint reads to decide the kind of game it opens (``docs/adr/0169`` §8).

    Built on ``player_profile``'s own declaration repository rather than on the
    matcher's ``mode_for_intent``: the arrow runs ``matchmaking -> challenges``
    and never back, and the two mappings answer different questions anyway —
    that one picks a weight vector and lets *no preference* inherit the fun
    ruler, this one honours a stated wish and lets *no preference* choose
    nothing.

    **A second declaration repository inside one unit of work** beside whatever
    the request built, and safe for ``build_settled_game_query``'s reason: it
    only ever **reads**, and two readers may hold a version of one stream.
    """
    return ProfileFriendlyChoice(
        build_play_intent_declaration_repository(
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
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
    return ThreeStrandsFromTheRecord(
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


def build_planned_game_handover(
    session: AsyncSession,
    *,
    runtime: EventRuntime | None = None,
) -> PlannedGameHandover:
    """The game a completed line-up opens or re-seats, the seat a departure
    vacates, the game a deserting departure or the hour calls off, and the
    dismissal a reader records on it from the Chats row, recorded inline
    (``docs/adr/0162``, ``docs/adr/0163``, ``docs/adr/0175``).

    It wraps four ``games`` use cases rather than an aggregate: what a game born
    of a completed line-up *is* belongs to that context, and the adapter is a
    translation of one sentence into another — four times.

    **One repository for all four**, because they run in one transaction and
    each loads the stream it appends to; **no unit of work here**, because the
    hand-over joins the transaction of the acceptance, the departure, the
    sweep or the dismissal that caused it, so the use case appends and
    publishes and the caller commits — the boundary stays a decision about the
    command.
    """
    games = build_game_repository(
        session=session,
        event_store=build_domain_event_store(session, runtime=runtime),
        events=build_event_publisher(session, runtime=runtime),
    )
    return GamesPlannedGame(
        OpenPlannedGame(games=games),
        VacateSeat(games=games),
        CallOffGame(games=games),
        DismissGameOfCourt(games=games),
    )


def build_agreed_moment(
    session: AsyncSession,
    *,
    runtime: EventRuntime | None = None,
) -> AgreedMoment:
    """*When has this game been agreed for?* — the Plan's answer to ``games``'
    demand (``docs/adr/0162`` §4), keyed by the challenge the game was opened
    from, which is the plan's own id (``docs/adr/0164`` §1).

    Over the Plan's repository rather than its directory, because the question
    is about one court and ``load`` answers an unwritten plan — whose moment is
    ``None`` — rather than nothing.
    """
    return PlansAgreedMoment(
        build_plan_repository(
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        )
    )


def build_seatable_court(
    session: AsyncSession,
    *,
    runtime: EventRuntime | None = None,
) -> SeatableCourt:
    """*May a seat on this challenge's court still be left, or taken?* —
    ``games``' answer, over its repository and the Plan's moment.

    A second game repository inside one unit of work, beside the hand-over's,
    on ``build_settled_game_query``'s argument: this one only ever reads, and
    the hand-over's is the only writer.
    """
    return EventSourcedSeatableCourt(
        games=build_game_repository(
            session=session,
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
        moments=build_agreed_moment(session, runtime=runtime),
    )


def build_seatable_game_query(
    session: AsyncSession,
    *,
    runtime: EventRuntime | None = None,
) -> SeatableGameQuery:
    """The read half of the departure's seam, in ``challenges``' own words:
    the adapter translates ``games``' published answer and decides nothing."""
    return GamesSeatableGame(build_seatable_court(session, runtime=runtime))


def build_game_of_court_query(
    session: AsyncSession,
    *,
    runtime: EventRuntime | None = None,
) -> GameOfCourtQuery:
    """*Which of these courts have a game, and which game?* — the challenge
    read's fourth question on the arrow ``challenges -> games``
    (``docs/adr/0172`` §4), wired the way the settled read is and for its
    reason: the join is the repository's, nothing is written through it, and a
    second reading repository inside one unit of work is safe because the
    hand-over's is the only writer.
    """
    return GamesGameOfCourt(
        build_game_repository(
            session=session,
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        )
    )


def build_settled_game_query(
    session: AsyncSession,
    *,
    runtime: EventRuntime | None = None,
) -> SettledGameQuery:
    """*Is anything more going to happen to the game this challenge opened?*

    The read half of the seam above, wired the same way and for the same reason:
    what *settled* means belongs to ``games``, and which implementation answers
    belongs here (``docs/adr/0152`` §5).

    It is built on the aggregate repository rather than on a read port, because
    the join it needs — one challenge to one game — is already there for the
    opening's idempotence. Nothing is written through it, and it commits nothing.

    **It is a second game repository inside one unit of work**, beside the one
    ``build_planned_game_handover`` makes, and that is safe here for a reason
    rather than by luck: a repository's per-unit-of-work state is the version
    bookkeeping behind optimistic concurrency, and this one only ever **reads**.
    Two readers may hold a version of one stream; what must not happen is two
    *writers* holding one, and the hand-over's repository is the only writer —
    it opens a game, or since ``docs/adr/0162`` re-seats or vacates a seat on
    one, and nothing built here appends beside it. Sharing one would mean a
    builder taking another builder's product, which is not the shape any port is
    wired in here.
    """
    return GamesSettledGame(
        build_game_repository(
            session=session,
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
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


def build_player_names(session: AsyncSession) -> PlayerNames:
    """*What is this person called* — the one thing ``games`` borrows about one.

    Built from ``users``' own repository rather than from the session, so this
    line stays a choice of implementation and the fold behind it stays with the
    context that owns it (``docs/adr/0141``).
    """
    return UsersNames(build_user_repository(session))


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


def build_plannable_courts(
    session: AsyncSession,
    *,
    runtime: EventRuntime | None = None,
) -> PlannableCourts:
    """*Which courts is this player arranging, and which are history* —
    ``challenges`` and ``games`` folded together, on the Plan's side of both
    arrows (``docs/adr/0164`` §3).

    The one thing the Plan reads about a court, and the read that decides
    whether a write may land. Built here rather than at the surface for the
    reason ``build_arranging_court`` is: which contexts answer *who is on this
    court and is it still being arranged* is a wiring choice, and a read path
    that reached into either itself would put a second author on it. It is
    folded rather than projected for the reason every read in those contexts
    is: ``open_to_planning`` and ``whole`` are standings, and a stored one would
    be wrong for the whole gap between a deadline passing and anything noticing.

    **A second game repository inside one unit of work**, on
    ``build_settled_game_query``'s argument: this one only ever reads.
    """
    return ChallengesAndGamesPlannableCourts(
        challenges=build_challenge_directory(session, runtime=runtime),
        games=build_game_repository(
            session=session,
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
    )


def build_plan_repository(
    *,
    event_store: DomainEventStore,
    events: DomainEventPublisher,
) -> PlanRepository:
    """Per unit of work, for the reason every aggregate repository here is: it
    remembers the stream versions it loaded.

    **It takes no session**, unlike ``conversations``' — there is no row to lock
    and no lookup by payload, because a plan's stream id *is* its challenge's.
    """
    return EventSourcedPlanRepository(event_store=event_store, events=events)


def build_plan_directory(
    session: AsyncSession,
    *,
    runtime: EventRuntime | None = None,
) -> PlanDirectory:
    """*Which of these courts have a plan written* — one ``IN`` over the
    aggregate ids.

    It reads the rows itself rather than folding through the repository, which is
    the opposite of the conversation directory beside it and for a stated reason:
    nothing appends to a plan read from here, so there is no stream version for a
    second reader to disagree about.
    """
    return EventSourcedPlanDirectory(session, (runtime or get_event_runtime()).codec)


def build_plan_hold_query(session: AsyncSession) -> PlanAccountHoldQuery:
    """``cases`` does not exist, so nothing can hold an account.

    **The fourth line in this file that says so.** Each context declares its own
    hold port because none may import another to ask a safety question; on the
    day ``cases`` ships, all four change to the same adapter.
    """
    return NoPlanHoldsExist()


def build_read_plans(
    session: AsyncSession,
    *,
    clock: Clock,
    runtime: EventRuntime | None = None,
) -> ReadPlans:
    """*One row for every court you may plan, written or not.*

    Assembled here rather than at the surface because a seed run reads it too,
    and the two must be reading the same thing.
    """
    return ReadPlans(
        plans=build_plan_directory(session, runtime=runtime),
        courts=build_plannable_courts(session, runtime=runtime),
        clock=clock,
    )


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


def build_half_built_court_query(session: AsyncSession) -> HalfBuiltCourtQuery:
    """The court a fill names, answered by ``challenges`` and translated.

    **One provider and one contract**, unlike the history port beside it: every
    fact on this read is a challenge fact, so nothing composes with it.

    The clock is built here rather than taken, for the reason the history's is:
    *is this court still being arranged* is a fact about the instant the read
    happens, and a caller holding one could hold a stale one.
    """
    return ChallengesHalfBuiltCourts(
        build_challenge_history_query(session), build_clock()
    )


def build_shared_court_query(session: AsyncSession) -> SharedCourtQuery:
    """The courts the deck's cool-off reads, answered by ``games`` and translated.

    **One provider and one contract**: every fact on this read is a game fact —
    who is on the court, and whether it is behind them yet — so nothing
    composes with it, and it reads ``games``' own directory rather than a
    second published port (``docs/adr/0169`` §6).

    The clock is built here rather than taken, for the reason the history's is:
    *is this court still ahead of them* is a fact about the instant the read
    happens, and a caller holding one could hold a stale one.
    """
    return GamesSharedCourts(build_game_directory(session), build_clock())


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


def build_opponent_variety_query(
    session: AsyncSession,
    *,
    runtime: EventRuntime | None = None,
) -> OpponentVarietyQuery:
    """*How widely does this person spread their games* — over the whole record.

    The same class as the history read and a **separate port**, which is the
    whole of the fence: this fold is unbounded, and a caller holding it as part
    of the port a search already carries could call it inside a walk over five
    hundred candidates. Typed narrowly here, it reaches only the surface that
    opens one person at a time.
    """
    return EventSourcedGameHistory(session, (runtime or get_event_runtime()).codec)


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


def build_subject_ratings(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> SubjectRatings:
    """Every sport a record's subject is rated in, in the record's own words.

    Built over ``rating``'s **read** port and never its repository, which is the
    whole reason that port exists: a repository remembers stream versions so a
    rating it found can be moved, and a sheet drawing a number must not be able
    to. The translation lives in ``player_record``'s infrastructure, which is
    where every borrowed fact is renamed on this platform.
    """

    return RatingSubjectRatings(build_rated_player_query(session, runtime=runtime))


def build_subject_form(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> SubjectForm:
    """The run of five for one sport, over ``games``' published history.

    The same query the player card's run is drawn from, asked its per-sport
    question — so a record and a card cannot come to two answers about what a
    counted result is.
    """

    return GamesSubjectForm(build_game_history_query(session, runtime=runtime))


def build_subject_variety(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> SubjectVariety:
    """How widely a record's subject spreads their games, over their whole record.

    Built over ``games``' **variety port** and never over the history read beside
    it, which is the fence rather than tidiness: this fold is unbounded, and the
    narrow type is what stops it being reachable from a caller that walks five
    hundred candidates.
    """

    return GamesSubjectVariety(
        build_opponent_variety_query(session, runtime=runtime)
    )


def build_subject_reliability(session: AsyncSession) -> SubjectReliability:
    """What the platform watched a record's subject do — the pill and its rows.

    Built over ``player_score``'s **published** read and never over the two folds
    underneath it, which is the same fence every other row here takes: the blend
    a player is shown is that context's arithmetic, and a second caller reaching
    past it to ``games`` and ``challenges`` would be a second author of what the
    number means.
    """

    return ScoreSubjectReliability(build_published_score_query(session))


def build_subject_sportsmanship(
    session: AsyncSession,
) -> SubjectSportsmanship:
    """What other players said about a record's subject — the figure and its
    count, whoever is reading (``docs/adr/0179`` §5).

    Built over ``sportsmanship``'s **published** port and never over the ledger
    beside it, which is the same fence every other row here takes: the ledger is
    that context's store and a sheet holding it could write through it.
    """

    return PublishedSubjectSportsmanship(build_published_sportsmanship(session))


def build_settled_courts(session: AsyncSession) -> SettledCourts:
    """*Is this a settled court of mine, and who else was on it* — over ``games``.

    The adapter lives in ``sportsmanship``'s own infrastructure, which is the
    shape ``games`` takes for ``PlayerNames``: a provider publishes what it
    knows about its own subject, and the context that wants it narrower does the
    narrowing. It is built over the directory rather than beside it, so the
    court a card is drawn for is folded from the same read of the log the games
    list already runs.
    """
    return GamesSettledCourts(build_game_directory(session))


def build_sportsmanship_ledger(session: AsyncSession) -> SportsmanshipLedger:
    """The answered cards, and one standing answer per pair of people.

    It writes and never commits, so it is built per request beside the unit of
    work the use case commits through — the lifetime every durable ledger in this
    codebase is given.
    """
    return SqlAlchemySportsmanshipLedger(session)


def build_published_sportsmanship(
    session: AsyncSession,
) -> PublishedSportsmanshipQuery:
    """What other players said about somebody — the figure and its count.

    Built over the session and never over the ledger beside it, which is the
    fence rather than tidiness: the ledger writes, and a read a sheet performs
    has no business holding a port a use case commits through. It reads the same
    rows the ledger writes, which is what a published fold is.
    """
    return StandingAnswersAboutThem(session)


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


def build_deck_reset_ledger(session: AsyncSession) -> DeckResetLedger:
    """The durable record of every *Show them again*, over the caller's session.

    **No fail-soft wrapper**, and for the opposite reason to the pass's: this
    row is not the evidence beside a gate, it is what three courtesies read to
    know they have been cleared. A reset that could be lost would re-hide the
    people a player just asked to see — the *empty the deck* failure every soft
    ledger here is soft in order to avoid — so it is a table, read in the deal's
    own transaction, and a reset whose row could not be written is a reset that
    did not happen, which the route says.
    """

    return SqlAlchemyDeckResetLedger(session)


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



# --------------------------------------------------------------------------
# The player record — one route out, and every port inward
# --------------------------------------------------------------------------
#
# This context stores nothing (``docs/adr/0159``), so there is no repository
# here and never will be: every builder below composes somebody else's published
# port into a demand this one declared in its own words.


def build_subject_identity_source(
    *,
    session: AsyncSession,
    event_store: DomainEventStore,
    events: DomainEventPublisher,
    storage: PhotoStorage,
) -> SubjectIdentitySource:
    """Who a person is, from the two contexts that own the answer.

    The same three providers ``build_player_card_source`` composes, asked about
    one player rather than twenty — and built over their **own ports** for that
    builder's reason: a walk over the profile streams written here would be a
    second implementation of how a profile is folded.
    """

    return ProfileAndAccountIdentity(
        users=build_user_repository(session),
        profiles=build_player_profile_repository(
            event_store=event_store, events=events
        ),
        photos=storage,
    )


def build_record_photo_link(
    *, storage: PhotoStorage, settings: Settings
) -> RecordPhotoLink:
    """A record's photograph, addressed for one response.

    **The window is read here**, from the one setting every photo link on this
    platform is signed for, so a record, a card and ``GET /photos/{id}`` cannot
    come to three answers about how long a link may live.
    """

    return PresignedRecordPhoto(
        storage=storage, valid_for_minutes=settings.PHOTO_URL_VALID_FOR_MINUTES
    )


def build_search_disclosure(session: AsyncSession) -> PriorDisclosure:
    """*A search of mine returned them* — over the record that says so."""

    return SearchesThatShowedThem(build_search_store(session))


def build_challenge_disclosure(session: AsyncSession) -> PriorDisclosure:
    """*We are both seated in a live challenge* — over ``challenges``' directory.

    The strand that runs the other way from a search: a court is sent off the
    organiser's search, so without this the person who was *asked* could not open
    the record of the person who asked them.
    """

    return ChallengesTheyShare(build_challenge_directory(session))


def build_game_disclosure(session: AsyncSession) -> PriorDisclosure:
    """*We were on a court together* — over ``games``' directory."""

    return GamesTheyPlayed(build_game_directory(session))


def build_record_gates(
    *, gates: FailClosedGates, holds: AccountHoldQuery
) -> RecordGates:
    """The four that fail closed, plus the reader's own hold.

    The four are **not built here**: they are ``matchmaking``'s collaborator,
    already assembled per request wherever a surface shows one player to another,
    and this line composes rather than copies. A second spelling of a safety gate
    is the defect the whole rule exists to prevent.
    """

    return LiveRecordGates(gates=gates, holds=holds)


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


# --------------------------------------------------------------------------
# Conversations
# --------------------------------------------------------------------------


def build_conversation_repository(
    *,
    session: AsyncSession,
    event_store: DomainEventStore,
    events: DomainEventPublisher,
) -> ConversationRepository:
    """Per unit of work, for the same reason every aggregate repository is —
    **and for one more.**

    It remembers the stream versions it loaded, like every other; and it takes
    the session as well as the store because two of its three reads take the
    conversation row's **lock**, which is where a gapless sequence is minted
    (``docs/adr/0147`` §2). A repository outliving its transaction would be one
    holding a lock nothing is going to release.
    """
    return EventSourcedConversationRepository(
        event_store=event_store, events=events, session=session
    )


def build_conversation_directory(
    *,
    session: AsyncSession,
    conversations: ConversationRepository,
) -> ConversationDirectory:
    """*Which rooms are these* — the lookup on the rows, folded through the
    repository.

    It is handed the repository rather than building one, because the aggregates
    it answers with carry stream versions somebody may be about to append
    against: two repositories in one transaction would be two answers to *what
    version have I seen*.
    """
    return SqlAlchemyConversationDirectory(
        session=session, conversations=conversations
    )


def build_arranging_court(
    session: AsyncSession,
    *,
    runtime: EventRuntime | None = None,
) -> ArrangingCourt:
    """Half of *one rule read against two records*, answered by ``challenges``.

    Built here rather than at the surface for the reason every adapter is: which
    context answers *who has agreed to be on this court* is a wiring choice, and
    a read path that reached into ``challenges`` itself would put a second author
    on it.
    """
    return ChallengesArrangingCourt(
        challenges=build_challenge_repository(
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
        directory=build_challenge_directory(session, runtime=runtime),
    )


def build_played_court(
    session: AsyncSession,
    *,
    runtime: EventRuntime | None = None,
) -> PlayedCourt:
    """The other half, answered by ``games``."""
    return GamesPlayedCourt(
        build_game_repository(
            session=session,
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        )
    )


def build_member_faces(
    session: AsyncSession,
    *,
    settings: Settings,
    runtime: EventRuntime | None = None,
) -> MemberFaces:
    """A name from ``users``, a face from the Player profile, a link from the
    store.

    **The third names adapter in this file**, and the first that carries a
    photograph beside the name: ``docs/adr/0148`` §6 made one affordable here
    where ``docs/adr/0143`` refused it, because a room is destroyed rather than
    kept.

    Built over the **three providers' own ports** rather than over the session,
    which is what keeps this context from becoming a second reader of somebody
    else's schema — and it is why a Player profile arrives as a stream folded
    through the event store: where a photograph lives is that context's business.

    The window is the platform's one photo window, so a room and
    ``GET /photos/{id}`` cannot come to two answers about how long a link lives.
    """
    return ProfileMemberFaces(
        users=build_user_repository(session),
        profiles=build_player_profile_repository(
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
        photos=build_photo_storage(settings),
        photo_link_minutes=settings.PHOTO_URL_VALID_FOR_MINUTES,
    )


def build_conversation_hold_query(
    session: AsyncSession,
) -> ConversationAccountHoldQuery:
    """``cases`` does not exist, so nothing can hold an account.

    **The third line in this file that says so.** Each context declares its own
    hold port because none may import another to ask a safety question; on the
    day ``cases`` ships, all three change to the same adapter.
    """
    return NoConversationHoldsExist()


def build_membership(
    session: AsyncSession,
    *,
    arranging: ArrangingCourt | None = None,
    runtime: EventRuntime | None = None,
) -> Membership:
    """*The people who have agreed to be on this court right now* — one rule,
    over both records.

    ``arranging`` is takeable because the list read needs the same port for a
    second question — *which challenges has this player accepted a seat on* —
    and two courts over one session would be two aggregate repositories each
    remembering its own stream versions. One per request, handed in.
    """
    return Membership(
        arranging=arranging or build_arranging_court(session, runtime=runtime),
        played=build_played_court(session, runtime=runtime),
    )


def build_lifetime(
    session: AsyncSession,
    *,
    arranging: ArrangingCourt | None = None,
    runtime: EventRuntime | None = None,
) -> Lifetime:
    """*Which of these rooms are over* — the game's clock off the room's own
    stream, and the challenge's end off ``challenges`` (``docs/adr/0164`` §6).

    ``arranging`` is takeable for the reason ``build_membership``'s is: a
    request asks the same port for membership, for the list's *find*, and now
    for *is it over*, and three courts over one session would be three aggregate
    repositories each remembering its own stream versions. One per request,
    handed in.
    """
    return Lifetime(
        arranging=arranging or build_arranging_court(session, runtime=runtime)
    )


def build_a_room_of_yours(
    *,
    conversations: ConversationRepository,
    membership: Membership,
    lifetime: Lifetime,
    clock: Clock,
) -> ARoomOfYours:
    """*This room, if you are in it* — the seam every act on one room shares.

    Built from the three collaborators rather than from a session, because all
    are already request-scoped and a second copy of any would be a second answer
    to *who is in this* or *is this over*.

    **The clock is the fourth, and it is what makes the lifetime a read.** A room
    past its end answers ``conversation_not_found`` whether or not the sweep has
    run (``docs/adr/0153`` §5). *Over* is decided in ``Lifetime`` — the one
    seam the list and the sweep decide it through too — and this is the one seam
    every act on **one** room passes through, so the refusal has a single place.
    """
    return ARoomOfYours(
        conversations=conversations,
        membership=membership,
        lifetime=lifetime,
        clock=clock,
    )


def build_destroy_ended_conversations(
    session: AsyncSession,
    *,
    clock: Clock,
    runtime: EventRuntime | None = None,
) -> DestroyEndedConversations:
    """The sweep, wired the way a request is. **Destroyed, not delisted.**

    ``clock`` is **required and never defaulted**, like every other clock-taking
    builder here. Its two callers want different answers and both are legitimate:
    the job wants the wall clock, and a seed run wants the one declared instant
    the rest of its fixture is dated against (``docs/adr/0029``, and
    ``app/seeds/clock.py``'s own argument). A default would make one of those the
    answer somebody inherited rather than the one they wrote.

    The repository and the directory are **one pair over one session**, as every
    other reader of the two is: the directory folds through the repository, so a
    second one would be a second set of remembered stream versions.

    **It reads ``challenges`` too**, through the lifetime seam every read
    decides a room's end through: a room without a game is over when its
    challenge is (``docs/adr/0164`` §6), and a sweep that folded the room's own
    stream alone would never delete one.
    """
    resolved = runtime or get_event_runtime()
    conversations = build_conversation_repository(
        session=session,
        event_store=build_domain_event_store(session, runtime=resolved),
        events=build_event_publisher(session, runtime=resolved),
    )
    return DestroyEndedConversations(
        directory=build_conversation_directory(
            session=session, conversations=conversations
        ),
        conversations=conversations,
        lifetime=build_lifetime(session, runtime=resolved),
        unit_of_work=build_unit_of_work(session),
        clock=clock,
    )


def build_tell_the_room(
    session: AsyncSession,
    *,
    nudges: NudgePublisher,
    runtime: EventRuntime | None = None,
) -> TellTheRoom:
    """The outbox subscriber that writes system lines. **Per delivery batch.**

    It is built over the batch's own session — the one ``EventBatch`` marks the
    outbox row published in — so a line and the delivery that caused it commit
    together. That is why this is not registered once for the process the way
    every logging handler is.

    **The publisher is handed in and has no default**, unlike every optional
    collaborator above it. A delivery that is live and a delivery that is not are
    both legitimate — an API process is the first, a seed run and a command-line
    drain are the second — and the difference is not one this file can read off a
    session. A default would make *this room is not live* the answer somebody
    inherited rather than the one they wrote.
    """
    conversations = build_conversation_repository(
        session=session,
        event_store=build_domain_event_store(session, runtime=runtime),
        events=build_event_publisher(session, runtime=runtime),
    )
    played = build_played_court(session, runtime=runtime)
    return TellTheRoom(
        conversations=conversations,
        directory=build_conversation_directory(
            session=session, conversations=conversations
        ),
        arranging=build_arranging_court(session, runtime=runtime),
        played=played,
        nudges=nudges,
    )


def build_nudge_publisher(client: Redis) -> NudgePublisher:
    """*Tell whoever is listening that a room moved* — **wrapped, always.**

    The composition root never hands out an unwrapped publisher, on
    ``build_exposure_ledger``'s argument one section up: the entry is already
    durable in Postgres when this is called, so a bus that is down costs a room
    its liveness and may never cost anybody their message. An unwrapped one would
    make that a discipline at two call sites instead of a property of the type.

    **On the command client, not the subscriber's.** A ``PUBLISH`` is a
    request/response command and belongs on the pool every command path draws
    from; it is the subscription that cannot live there (``docs/adr/0147`` §5).
    """

    return FailSoftNudgePublisher(RedisNudgePublisher(client))


def build_nobody_is_following() -> NudgePublisher:
    """*This delivery is not live*, said out loud. **A seed run and a CLI drain.**

    Constructed here rather than reached for at those two call sites, because
    this file is where an adapter is built and `tests/unit/test_seed_runner.py`
    holds `app/seeds/` to it: a seed module importing an adapter's internals is
    the shape that walk refuses, whatever the adapter does.

    It is the correct answer for a run with no phone attached, and not a degraded
    one — which is why it is a different builder from the fail-soft publisher
    above rather than the same one with a missing store.
    """

    return NobodyIsFollowing()


def build_nudge_subscriber(client: Redis) -> NudgeSubscriber:
    """*Everything published about this room* — **and it is not wrapped.**

    The asymmetry with the publisher above is the design (``docs/adr/0147`` §8):
    a subscription **is** the liveness, so it fails loud and the stream closes.
    A chat that is not live has to look not-live, and a connection held open
    delivering nothing looks up to date.

    The client is the subscriber's own — no read deadline, because on a
    subscription waiting *is* the operation (#342).
    """

    return RedisNudgeSubscriber(client)


def build_typing_heartbeat(client: Redis) -> TypingHeartbeat:
    """*This player is typing* — **wrapped, always**, and on the command client.

    Wrapped for ``build_nudge_publisher``'s reason and a stronger version of it:
    a nudge that is lost costs a room its liveness, and a heartbeat that is lost
    costs one second of a courtesy. An unwrapped one would make that a discipline
    at a call site instead of a property of the type.

    On the pool every command path draws from, bounded at both ends. Nothing here
    subscribes to anything (``docs/adr/0156`` §3): presence is written to the
    store and read back off it, and it never touches the bus.
    """

    return FailSoftTypingHeartbeat(RedisTypingHeartbeat(client))


def build_typing_roster(client: Redis) -> TypingRoster:
    """*Who is typing in this room* — **wrapped too, and that is the departure.**

    The nudge ports fail in opposite directions and this pair does not
    (``docs/adr/0156`` §6). A subscription **is** the room's liveness, so it fails
    loud and the stream closes; a roster is a courtesy asked once a second by
    every open conversation screen, on the client with a two-second read
    deadline — so failing it loud would let a merely slow store close every
    healthy stream on the platform. It reports nobody typing instead, which is
    what a quiet room reports.

    **One wrapper per stream, and that is load-bearing rather than incidental.**
    It complains on the transition into failure rather than on every read, and it
    is this builder's per-request lifetime that makes *once per stream per
    outage* the shape of that.
    """

    return FailSoftTypingRoster(RedisTypingRoster(client))


def build_follow_conversation(
    *,
    rooms: ARoomOfYours,
    nudges: NudgeSubscriber,
    typists: TypingRoster,
) -> FollowConversation:
    """*Follow this room until the token that opened it expires.*

    Built from the collaborators rather than a session, for
    ``build_a_room_of_yours``' reason: the gate is a read like every other read
    on this context, and the stream that follows it touches no database at all.

    **Three collaborators and two stores.** The subscription is the bus's and the
    roster is the ephemeral store's, on two different clients for two different
    reasons — see the two builders above.
    """

    return FollowConversation(
        rooms=rooms, nudges=nudges, typists=typists, clock=build_clock()
    )
