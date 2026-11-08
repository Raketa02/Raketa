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

from functools import lru_cache

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.application.ports import (
    DomainEventPublisher,
    DomainEventStore,
    Mailer,
    MailQueue,
    PendingMail,
    UnitOfWork,
)
from app.bootstrap.events import EventRuntime, get_event_runtime
from app.core.config import PushProvider, Settings
from app.engines.assessment import AssessmentEngine
from app.engines.matchfit.ruleset import Ruleset
from app.engines.racketskill.v3 import RacketSkillEngineV3
from app.infrastructure.clock import SystemClock
from app.infrastructure.database.unit_of_work import AsyncSqlAlchemyUnitOfWork
from app.infrastructure.events.read_once_event_store import ReadOnceEventStore
from app.infrastructure.mail.smtp_mailer import SmtpMailer
from app.infrastructure.mail.sqlalchemy_mail_queue import SqlAlchemyMailQueue
from app.kernel import Clock
from app.modules.auth.application.one_time_credentials import OneTimeCredentials
from app.modules.auth.domain.ports import (
    CredentialSecrets,
    OneTimeCredentialStore,
    PasswordAccounts,
    PasswordHasher,
    RefreshTokenRepository,
    SessionHolders,
    TokenService,
)
from app.modules.auth.infrastructure.jwt_token_service import JwtTokenService
from app.modules.auth.infrastructure.password_hasher import BcryptPasswordHasher
from app.modules.auth.infrastructure.random_credential_secrets import (
    RandomCredentialSecrets,
)
from app.modules.auth.infrastructure.sqlalchemy_one_time_credential_store import (
    SqlAlchemyOneTimeCredentialStore,
)
from app.modules.auth.infrastructure.sqlalchemy_refresh_token_repository import (
    SqlAlchemyRefreshTokenRepository,
)
from app.modules.administrators.application.sending import InvitationSender
from app.modules.administrators.domain.ports import (
    AccountHolders,
    AdministratorDirectory,
    AdministratorRepository,
    ClubNames,
    InvitationLinks,
    OfficialGroupAssignments,
)
from app.modules.administrators.infrastructure.clubs_club_names import (
    ClubsClubNames,
)
from app.modules.administrators.infrastructure.event_sourced_administrator_repository import (  # noqa: E501
    EventSourcedAdministratorRepository,
)
from app.modules.administrators.infrastructure.sqlalchemy_administrator_directory import (  # noqa: E501
    SqlAlchemyAdministratorDirectory,
)
from app.modules.administrators.infrastructure.users_account_holders import (
    UsersAccountHolders,
)
from app.modules.payments.domain.notices import PaymentNotices
from app.modules.payments.domain.ports import (
    ClubPayoutRepository,
    ConnectedAccounts,
    GamesOver,
    NoticeInbox,
    Payers,
    PaymentCommitments,
    PaymentMethodRepository,
    SeatChargeRepository,
    Sellers,
)
from app.modules.payments.infrastructure.club_accounts import (
    ClubsConnectedAccounts,
    ProviderPaymentsAccounts,
)
from app.modules.payments.domain.provider import PaymentProvider
from app.modules.payments.infrastructure.event_sourced_payment_method_repository import (  # noqa: E501
    EventSourcedPaymentMethodRepository,
)
from app.modules.payments.domain.entered_cards import A_CARD
from app.modules.payments.infrastructure.fake_payments import FakePayments
from app.modules.proposals.application.booking_details import ReadBookingDetails
from app.modules.proposals.application.expire_proposals import ExpireProposals
from app.modules.proposals.application.group_deck import (
    ReadDeckCounts,
    ReadGroupDeck,
)
from app.modules.proposals.application.home import ReadHome
from app.modules.proposals.application.live_yeses import ReadLiveYeses
from app.modules.proposals.application.proposal_details import ReadProposalDetails
from app.modules.proposals.application.rescues import (
    SayNoToARescue,
    JoinARescue,
    ReadFillIn,
    RescueOffers,
    Rescuer,
)
from app.modules.proposals.application.guards import Guards
from app.modules.proposals.application.blocking import WithdrawABlockersYeses
from app.modules.proposals.application.leaving import WithdrawALeaversYeses
from app.modules.proposals.application.making import DealVersion, MakeProposal
from app.modules.proposals.application.members import ReadMembers
from app.modules.proposals.application.friends_card import (
    ReadFriendsCard,
    ReadFriendsCourts,
    ReadFriendsLineUp,
)
from app.modules.proposals.application.friends_games import (
    FriendsGameConfirmation,
    AcceptAFriendsGame,
    Accepting,
    DeclineAFriendsGame,
    CallOffAFriendsGame,
    InviteIntoASeat,
    OpenASeat,
    RunOutTheInvitations,
    SendAFriendsGame,
    WarnTheCovers,
)
from app.modules.proposals.application.posting import (
    PostAGame,
    ReadPosting,
    ReadPostingGrid,
    ReadPostingSlot,
)
from app.modules.proposals.application.propose_games import (
    DealThePoolNow,
    ProposeGames,
)
from app.modules.proposals.application.resume_paused_yeses import ResumePausedYeses
from app.modules.proposals.domain.ports import (
    BalanceForecasts,
    CoversAtTheCutOff,
    FriendsGameBookings,
    SendersCourts,
    FriendRequestsOnHome,
    LevelAsksOnHome,
    RankingOnHome,
    ReaderRelations,
    BookedGameChanges,
    BookedGames,
    BookingTakings,
    LateRefunds,
    ClubBookings,
    ClubDistances,
    PoolOrigins,
    GameBookings,
    PlayerNames as ProposalPlayerNames,
    GameResults,
    CardsToFix,
    CheckedShares,
    HeldShares,
    HoldingTimes,
    PlayerBookings,
    SeatCharges,
    SeatRefunds,
    UndecidedCharges,
    ClubNames as ProposalClubNames,
    ClubTerms,
    CourtHours,
    CourtKinds,
    DeckPeople,
    GamesAndMoneyRepository,
    PlayerFit,
    PlayersInPlay,
    WherePoolsPlay,
    Pools,
    ProposalDirectory,
    ProposalRepository,
    SavedMethods,
    WantedKinds,
)
from app.modules.proposals.infrastructure.club_court_hours import (
    ClubCourtHours,
    DirectoryClubNames,
    SellableClubTerms,
    SellableCourtKinds,
)
from app.modules.proposals.infrastructure.event_sourced_games_and_money_repository import (  # noqa: E501
    EventSourcedGamesAndMoneyRepository,
)
from app.modules.proposals.infrastructure.matcher_balance_forecasts import (
    MatcherBalanceForecasts,
)
from app.modules.proposals.application.answers import (
    ConfirmPayment,
    SayYes,
    WithdrawYes,
)
from app.modules.proposals.application.club_bookings import (
    CancelTheGame,
    MoveTheGame,
    PreviewTheCancel,
    ReadClubBookings,
    ReadFreeCourts,
)
from app.modules.proposals.application.club_money import ReadClubMoney
from app.modules.proposals.application.time_to_pay import RunOutTheTimeToPay
from app.modules.proposals.application.cut_off import TheCutOff
from app.modules.proposals.application.holding import TheHolding
from app.modules.proposals.application.payments_to_confirm import (
    ReadPaymentsToConfirm,
)
from app.modules.proposals.application.fill import Fill
from app.modules.proposals.application.leave_the_game import LeaveTheGame
from app.modules.proposals.infrastructure.bookings import (
    BookingsBookedGames,
    BookingsBookedGameChanges,
    BookingsClubBookings,
    BookingsFriendsGameBookings,
    BookingsGameBookings,
    BookingsGroupBornGames,
    BookingsPlayerBookings,
)
from app.modules.proposals.infrastructure.users_names import UsersPlayerNames
from app.modules.proposals.infrastructure.club_distances import ProfileClubDistances
from app.modules.proposals.infrastructure.game_results import GamesGameResults
from app.modules.bookings.application.at_the_club import (
    CancelTheBooking,
    MoveTheBooking,
)
from app.modules.bookings.application.book_the_game import BookTheGame, FindACourt
from app.modules.bookings.application.friends_games import FriendsGames
from app.modules.bookings.application.leaving import (
    CallOffAtTheCutOff,
    LeaveTheBooking,
    TimeToFixTheCard,
)
from app.modules.bookings.application.rescues import (
    KeepTheSeat,
    RescueTheSeat,
    SayNoToTheSeat,
)
from app.modules.bookings.domain.ports import (
    BookingDirectory,
    BookingHistoryQuery,
    BookingRepository,
    ClubCourtsAtTheHour,
    ClubDesks,
    CourtClosures,
    GameChanges,
    GameOpening,
    SummaryRepository,
)
from app.modules.bookings.infrastructure.booking_history import (
    EventSourcedBookingHistory,
)
from app.modules.bookings.application.daily_summary import SummariseNewBookings
from app.modules.bookings.infrastructure.club_desks import AccountClubDesks
from app.modules.bookings.infrastructure.event_sourced_summary_repository import (  # noqa: E501
    EventSourcedSummaryRepository,
)
from app.modules.bookings.infrastructure.club_courts import (
    BookedCourtHours,
    ClosedByTheCancel,
    SellableClubCourts,
)
from app.modules.bookings.infrastructure.event_sourced_booking_repository import (
    EventSourcedBookingRepository,
    SqlAlchemyBookingDirectory,
)
from app.modules.bookings.infrastructure.games_opening import (
    LeaveAndCallOffTheGame,
    OpenTheGame,
)
from app.modules.bookings.infrastructure.game_clubs import BookedGameClubs
from app.modules.payments.application.handlers.settle_seat_charges import (
    SettleSeatCharges,
)
from app.modules.payments.application.handlers.send_club_payouts import (
    SendClubPayout,
)
from app.modules.payments.application.payouts import (
    DecideClubPayouts,
    ReadClubPayouts,
)
from app.modules.payments.application.refunds import (
    EmailTheSeatTakenRefund,
    GiveTheSharesBack,
    TellTheLateLeaver,
)
from app.modules.payments.application.covers import HoldTheCourt, SettleTheCovers
from app.modules.payments.application.seat_charges import (
    ChargeTheSeats,
    ConfirmSeatCharge,
    HoldTheCheckedShares,
    KeepTheFixedShare,
    LetTheUnfixedShareGo,
    PaymentToConfirmOn,
    ReadReceipts,
    ReadSeatCharge,
    ReleaseCharges,
    TakeTheHeldShares,
)
from app.modules.payments.infrastructure.event_sourced_club_payout_repository import (  # noqa: E501
    EventSourcedClubPayoutRepository,
)
from app.modules.payments.infrastructure.event_sourced_seat_charge_repository import (  # noqa: E501
    EventSourcedSeatChargeRepository,
)
from app.modules.payments.infrastructure.sellers_and_payers import (
    ClubSellers,
    UserPayers,
)
from app.modules.proposals.infrastructure.profile_deck_people import (
    ProfileDeckPeople,
)
from app.modules.proposals.infrastructure.profile_wanted_kinds import (
    ProfileWantedKinds,
)
from app.modules.proposals.infrastructure.event_sourced_proposal_repository import (  # noqa: E501
    EventSourcedProposalRepository,
)
from app.modules.proposals.infrastructure.group_pools import (
    GroupPoolOrigins,
    GroupPools,
)
from app.modules.proposals.infrastructure.group_clubs import GroupClubs
from app.modules.proposals.infrastructure.profile_players_in_play import (
    ProfilePlayersInPlay,
)
from app.modules.proposals.infrastructure.matcher_player_fit import MatcherPlayerFit
from app.modules.proposals.infrastructure.payments import (
    BookedGamesOver,
    LiveYesCommitments,
    PaymentsBookingTakings,
    PaymentsSavedMethods,
    PaymentsLateRefunds,
    PaymentsCardsToFix,
    PaymentsCheckedShares,
    PaymentsHeldShares,
    PaymentsHoldingTimes,
    PaymentsSeatCharges,
    PaymentsSeatRefunds,
    PaymentsUndecidedCharges,
    PaymentsCoversAtTheCutOff,
    PaymentsSendersCourts,
)
from app.modules.proposals.infrastructure.sqlalchemy_proposal_directory import (
    SqlAlchemyProposalDirectory,
)
from app.modules.payments.infrastructure.sqlalchemy_notice_inbox import (
    SqlAlchemyNoticeInbox,
)
from app.modules.payments.infrastructure.stripe_notices import StripeNotices
from app.modules.payments.infrastructure.stripe_payments import StripePayments
from app.modules.notifications.application.pushing import NoticePushes, PushTheNotice
from app.modules.notifications.application.reading import (
    NoticeWords,
    ReadRecentNotices,
)
from app.modules.notifications.application.asking import AskHowDidItGo
from app.modules.notifications.application.get_your_level import TellGetYourLevel
from app.modules.notifications.application.telling import GiveNotice, TellThePlayers
from app.modules.notifications.domain.ports import (
    BellRepository,
    GameCourts,
    Decks,
    EndedHours,
    Friendships,
    GameBriefs,
    GroupJoiners,
    Names,
    NoticeDayRepository,
    NoticeDirectory,
    NotificationPreferencesRepository,
    PaidShares,
    PushNotifications,
    RatedAccounts,
    SeatOffers,
)
from app.modules.notifications.infrastructure.event_sourced_notification_repositories import (  # noqa: E501
    EventSourcedBellRepository,
    EventSourcedNoticeDayRepository,
    EventSourcedNotificationPreferencesRepository,
    SqlAlchemyNoticeDirectory,
)
from app.modules.notifications.infrastructure.push import ExpoPush, RecordingPush
from app.modules.notifications.infrastructure.told_by import (
    BookedAndProposedGames,
    BookedHours,
    DirectoryGroupJoiners,
    FriendsOfTheReader,
    GameStreamCourts,
    PlatformNames,
    ProposalsDecks,
    RatingsRatedAccounts,
    RescueSeatOffers,
    SeatChargeShares,
)
from app.modules.player_profile.application.has_player_profile import (
    HasPlayerProfile,
)
from app.modules.blocks.domain.ports import BlockedFaces, BlockQuery, BlockRepository
from app.modules.blocks.infrastructure.event_sourced_block_query import (
    EventSourcedBlockQuery,
)
from app.modules.blocks.infrastructure.profile_blocked_faces import (
    ProfileBlockedFaces,
)
from app.modules.blocks.infrastructure.event_sourced_block_repository import (
    EventSourcedBlockRepository,
)
from app.modules.clubs.application.password_accounts import ClubPasswordAccounts
from app.modules.clubs.application.session_holders import ClubAccountSessionHolders
from app.modules.clubs.domain.ports import (
    ClubAccountRepository,
    ClubCourtsRepository,
    CourtBookings,
    SellableCourtHours,
    ClubDirectory,
    ClubRepository,
    OfficialGroupSports,
    PaymentsAccounts,
)
from app.modules.clubs.application.hours_exceptions import CloseACourtForAnHour
from app.modules.clubs.application.payments_account import HeedPaymentsAccount
from app.modules.clubs.domain.payments_account import OnboardingPages
from app.modules.clubs.infrastructure.event_sourced_club_account_repository import (
    EventSourcedClubAccountRepository,
)
from app.modules.clubs.infrastructure.event_sourced_club_courts_repository import (
    EventSourcedClubCourtsRepository,
)
from app.modules.clubs.infrastructure.event_sourced_club_repository import (
    EventSourcedClubRepository,
)
from app.modules.clubs.infrastructure.club_courts_sellable_hours import (
    ClubCourtsSellableHours,
)
from app.modules.clubs.infrastructure.profile_club_points import DirectoryClubPoints
from app.modules.clubs.infrastructure.sqlalchemy_club_directory import (
    SqlAlchemyClubDirectory,
)
from app.modules.games.application.call_off_game import (
    CallOffGame,
    CallOffTheWholeGame,
)
from app.modules.groups.domain.ports import (
    GroupAdministrators,
    GroupBornGames,
    GroupCodeMinter,
    GroupDirectory,
    GroupFaces,
    GroupMemberReliability,
    GroupRepository,
    HomeClubs,
    MemberRelations,
    RatedGroupMembers,
    ReaderAreas,
)
from app.modules.friends.application.handlers import (
    AnswerTheAsksForALevel,
    EndFriendshipsOnABlock,
)
from app.modules.friends.application.link import ReadYourFriendLink
from app.modules.friends.application.reads import (
    ReadLevelAsksOnHome,
    ReadLevelAsksWaiting,
    ReadRelations,
    ReadRequestsOnHome,
    ReadRequestsWaiting,
)
from app.modules.friends.application.requests import (
    AcceptFriendRequest,
    AskToBeFriends,
    SetAsideFriendRequest,
)
from app.modules.friends.domain.ports import (
    FriendFaces,
    FriendLevels,
    FriendLinkCodes,
    FriendLinkRepository,
    FriendReliabilities,
    FriendshipDirectory,
    FriendshipRepository,
    AsksWaitingOnALevel,
    LevelAsksOfTheReader,
    LevelsAskedByTheReader,
    ReadersBlocks,
    ReadersGroups,
)
from app.modules.friends.infrastructure.event_sourced_friend_link_repository import (
    EventSourcedFriendLinkRepository,
)
from app.modules.friends.infrastructure.event_sourced_friendship_repository import (
    EventSourcedFriendshipRepository,
)
from app.modules.friends.infrastructure.own_blocks import OwnBlocks
from app.modules.friends.infrastructure.profile_friend_faces import ProfileFriendFaces
from app.modules.friends.infrastructure.published_friend_reliability import (
    PublishedFriendReliability,
)
from app.modules.friends.infrastructure.random_friend_link_codes import (
    RandomFriendLinkCodes,
)
from app.modules.friends.infrastructure.rated_friend_levels import RatedFriendLevels
from app.modules.friends.infrastructure.sqlalchemy_friendship_directory import (
    SqlAlchemyFriendshipDirectory,
)
from app.modules.friends.infrastructure.sqlalchemy_level_ask_directory import (
    SqlAlchemyLevelAskDirectory,
)
from app.modules.proposals.infrastructure.friends import (
    FriendsLevelAsksOnHome,
    FriendsReaderRelations,
    FriendsRequestsOnHome,
)
from app.modules.proposals.infrastructure.rankings import RankingsOnHome
from app.modules.rankings.application.projection import (
    FollowTheSwitch,
    MoveTheRanking,
    RebuildTheRankings,
)
from app.modules.rankings.application.friends_table import TheFriendsTable
from app.modules.rankings.application.general_order import TheGeneralOrder
from app.modules.rankings.application.reads import (
    ReadGeneralPage,
    ReadHomeRanking,
    ReadRanking,
)
from app.modules.rankings.domain.ports import (
    BlocksEitherWay,
    GeneralOrders,
    GeneralSwitches,
    LevelHistory,
    RankedFaces,
    RankingRows,
    RatingHistories,
    ReadersFriends,
    SportLevels,
)
from app.modules.rankings.infrastructure.blocks_either_way import (
    QueriedBlocksEitherWay,
)
from app.modules.rankings.infrastructure.friends_readers_friends import (
    FriendsReadersFriends,
)
from app.modules.rankings.infrastructure.in_memory_general_orders import (
    InMemoryGeneralOrders,
)
from app.modules.rankings.infrastructure.profile_general_switches import (
    ProfileGeneralSwitches,
)
from app.modules.rankings.infrastructure.profile_ranked_faces import (
    ProfileRankedFaces,
)
from app.modules.rankings.infrastructure.redis_general_orders import (
    FailSoftGeneralOrders,
    RedisGeneralOrders,
)
from app.modules.rankings.infrastructure.rated_sport_levels import RatedSportLevels
from app.modules.rankings.infrastructure.rating_stream_histories import (
    RatingStreamHistories,
)
from app.modules.rankings.infrastructure.sqlalchemy_level_history import (
    SqlAlchemyLevelHistory,
)
from app.modules.rankings.infrastructure.sqlalchemy_ranking_rows import (
    SqlAlchemyRankingRows,
)
from app.modules.groups.infrastructure.friends_member_relations import (
    FriendsMemberRelations,
)
from app.modules.groups.infrastructure.friends_readers_groups import (
    DirectoryReadersGroups,
)
from app.modules.groups.infrastructure.administrators_group_administrators import (
    AdministratorsGroupAdministrators,
)
from app.modules.groups.infrastructure.administrators_official_group_assignments import (  # noqa: E501
    GroupsOfficialGroupAssignments,
)
from app.modules.groups.infrastructure.clubs_home_clubs import ClubsHomeClubs
from app.modules.groups.infrastructure.clubs_official_group_sports import (
    GroupsOfficialGroupSports,
)
from app.modules.groups.infrastructure.event_sourced_group_repository import (
    EventSourcedGroupRepository,
)
from app.modules.groups.infrastructure.profile_group_faces import ProfileGroupFaces
from app.modules.groups.infrastructure.profile_reader_areas import ProfileReaderAreas
from app.modules.groups.infrastructure.published_group_member_reliability import (
    PublishedGroupMemberReliability,
)
from app.modules.groups.infrastructure.random_group_codes import RandomGroupCodes
from app.modules.groups.infrastructure.rated_group_members import (
    RatingsRatedGroupMembers,
)
from app.modules.groups.infrastructure.sqlalchemy_group_directory import (
    SqlAlchemyGroupDirectory,
)
from app.modules.games.application.open_planned_game import OpenPlannedGame
from app.modules.games.application.take_a_seat import TakeASeat
from app.modules.games.application.vacate_seat import VacateSeat
from app.modules.conversations.application.a_room_of_yours import ARoomOfYours
from app.modules.conversations.application.destroy_ended_conversations import (
    DestroyEndedConversations,
)
from app.modules.conversations.application.membership import Membership
from app.modules.conversations.application.tell_the_room import TellTheRoom
from app.modules.conversations.domain.ports import (
    AccountHoldQuery as ConversationAccountHoldQuery,
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
    ConfirmedResultLedger,
    CourtPairing,
    GameClubs,
    GameDirectory,
    GameHistoryQuery,
    GameRepository,
    OpponentVarietyQuery,
    PlayerNames,
    ScoredGames,
)
from app.modules.games.infrastructure.event_sourced_confirmed_results import (
    EventSourcedConfirmedResults,
)
from app.modules.games.infrastructure.event_sourced_scored_games import (
    EventSourcedScoredGames,
)
from app.modules.games.infrastructure.event_sourced_game_history import (
    EventSourcedGameHistory,
)
from app.modules.games.infrastructure.event_sourced_game_repository import (
    EventSourcedGameRepository,
)
from app.modules.games.infrastructure.users_names import UsersNames
from app.modules.matchmaking.domain.ports import (
    AccountHoldQuery,
    AccountStatusQuery,
    AtStakeQuery,
)
from app.modules.matchmaking.application.fail_closed_gates import AccountGates
from app.modules.matchmaking.infrastructure.absent_providers import (
    NoHoldsExist,
)
from app.modules.player_score.domain.ports import PublishedScoreQuery
from app.modules.player_score.infrastructure.points_from_the_record import (
    PointsFromTheRecord,
)
from app.modules.matchmaking.infrastructure.rulesets import LIVE_RULESET
from app.modules.matchmaking.infrastructure.games_court_pairing import (
    GamesCourtPairing,
)
from app.modules.matchmaking.infrastructure.rating_at_stake import (
    RatingResultUpdateRule,
)
from app.modules.matchmaking.infrastructure.users_account_status import (
    UsersAccountStatus,
)
from app.modules.player_profile.domain.ports import (
    ClubPoints,
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
from app.modules.player_record.infrastructure.groups_reliability_filters import (
    FiltersInTheGroups,
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
    BlocksByTheReader,
    RelationsOfTheReader,
    PriorDisclosure,
    RecordGates,
    RecordPhotoLink,
    ReliabilityFilters,
    SubjectForm,
    SubjectIdentitySource,
    SubjectRatings,
    SubjectReliability,
    SubjectSportsmanship,
    SubjectVariety,
)
from app.modules.player_record.infrastructure.disclosures import (
    GamesTheyPlayed,
    GroupsTheReaderRuns,
    GroupsTheyShare,
)
from app.modules.player_record.infrastructure.live_record_gates import (
    LiveRecordGates,
)
from app.modules.player_record.infrastructure.friends_relations import (
    FriendsRelationsOfTheReader,
)
from app.modules.player_record.infrastructure.own_blocks import (
    OwnBlocksOfTheReader,
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
from app.modules.users.application.invitation_accounts import InvitationAccounts
from app.modules.users.application.password_accounts import UserPasswordAccounts
from app.modules.users.application.session_holders import UserSessionHolders
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


def _own_or(
    event_store: DomainEventStore | None,
    session: AsyncSession,
    runtime: EventRuntime | None,
) -> DomainEventStore:
    """The store a caller handed in, or this builder's own over ``session``.

    The read-only builders the deck read shares take an optional store so the
    request's ``ReadOnceEventStore`` (#704) reaches every one of them; handed
    none, each builds its own, which is how every other caller is wired. One
    function, so the rule is spelled once and not in each of them.
    """
    return event_store or build_domain_event_store(session, runtime=runtime)


# --------------------------------------------------------------------------
# Auth
# --------------------------------------------------------------------------


def build_password_hasher(settings: Settings) -> PasswordHasher:
    return BcryptPasswordHasher(rounds=settings.BCRYPT_ROUNDS)


def build_token_service(settings: Settings, *, clock: Clock) -> TokenService:
    return JwtTokenService(settings, clock=clock)


def build_refresh_token_repository(session: AsyncSession) -> RefreshTokenRepository:
    return SqlAlchemyRefreshTokenRepository(session)


def build_one_time_credential_store(session: AsyncSession) -> OneTimeCredentialStore:
    """Where one-time credentials live: a plain table, **never** the event store
    (``docs/adr/0184`` §3–§4)."""
    return SqlAlchemyOneTimeCredentialStore(session)


def build_credential_secrets() -> CredentialSecrets:
    """A credential's randomness: the operating system's CSPRNG."""
    return RandomCredentialSecrets()


# --------------------------------------------------------------------------
# Email (docs/adr/0186)
# --------------------------------------------------------------------------


def build_mail_queue(session: AsyncSession) -> MailQueue:
    """Where a use case leaves an email, in its own transaction."""
    return SqlAlchemyMailQueue(session)


def build_pending_mail(session: AsyncSession) -> PendingMail:
    """The worker's side of the same table."""
    return SqlAlchemyMailQueue(session)


def build_mailer(settings: Settings) -> Mailer:
    """The one mailer: SMTP, at the mail catcher locally and at a relay once a
    domain exists. Held by the worker and by nothing a request reaches."""
    return SmtpMailer(
        host=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        security=settings.SMTP_SECURITY,
        username=settings.SMTP_USERNAME,
        password=settings.SMTP_PASSWORD,
        sender=settings.MAIL_SENDER,
        timeout_seconds=settings.SMTP_TIMEOUT_SECONDS,
    )


# --------------------------------------------------------------------------
# Clubs
# --------------------------------------------------------------------------


def build_club_repository(
    session: AsyncSession,
    *,
    event_store: DomainEventStore,
    events: DomainEventPublisher,
) -> ClubRepository:
    """Per unit of work, for the reason every aggregate repository is: it
    remembers the stream versions it loaded.

    **It takes the session as well as the store**, unlike ``blocks``', because
    its ``save`` writes the club's search row in the same transaction as the
    event (``docs/adr/0182`` §2).
    """
    return EventSourcedClubRepository(
        session=session, event_store=event_store, events=events
    )


def build_club_account_repository(
    session: AsyncSession,
    *,
    event_store: DomainEventStore,
    events: DomainEventPublisher,
) -> ClubAccountRepository:
    """The club's sign-in: read from its row, written to its stream and its row
    in one transaction (``docs/adr/0182`` §3)."""
    return EventSourcedClubAccountRepository(
        session=session, event_store=event_store, events=events
    )


def build_club_account_session_holders(
    accounts: ClubAccountRepository,
) -> SessionHolders:
    """Who may renew a **club** session: a Club account that still exists
    (``docs/adr/0185`` §6). Over the repository the request already holds."""
    return ClubAccountSessionHolders(accounts)


def build_club_account_passwords(accounts: ClubAccountRepository) -> PasswordAccounts:
    """Whose password a **club** reset recovers: a Club account's
    (``docs/adr/0184`` §5). Over the repository the request already holds."""
    return ClubPasswordAccounts(accounts)


def build_official_group_sports(session: AsyncSession) -> OfficialGroupSports:
    """What the official groups at a club declare — the one thing a details
    edit is refused over from outside the club (``docs/adr/0182`` §5) —
    answered by the Groups context over its own directory, so the arrow runs
    ``groups → clubs`` only."""
    return GroupsOfficialGroupSports(build_group_directory(session))


def build_club_courts_repository(
    session: AsyncSession,
    *,
    event_store: DomainEventStore,
    events: DomainEventPublisher,
) -> ClubCourtsRepository:
    """A club's courts and terms, one stream per club (``docs/adr/0189`` §5).
    Per unit of work: it remembers the stream versions it loaded. It takes the
    session as well, because its ``save`` writes which club a newly opened
    payments account is (#537)."""
    return EventSourcedClubCourtsRepository(
        session=session, event_store=event_store, events=events
    )


def build_court_bookings(session: AsyncSession) -> CourtBookings:
    """The court hours bookings hold (#541) — answered by the Bookings context
    over its own projection, so the arrow runs ``bookings → clubs`` only."""
    return BookedCourtHours(build_booking_directory(session))


def build_sellable_court_hours(
    session: AsyncSession,
    *,
    runtime: EventRuntime | None = None,
    event_store: DomainEventStore | None = None,
) -> SellableCourtHours:
    """What the Club context publishes about courts: the hours each live club
    can sell, derived from its stream less what bookings hold
    (``docs/adr/0189`` §5). ``event_store`` is the deck read's shared one
    (#704); every other caller gets a store of its own."""
    return ClubCourtsSellableHours(
        courts=build_club_courts_repository(
            session,
            event_store=_own_or(event_store, session, runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
        bookings=build_court_bookings(session),
    )


def build_club_directory(session: AsyncSession) -> ClubDirectory:
    """What the Club context publishes: its clubs, read off the search
    projection (``docs/adr/0182`` §2) and never as an aggregate."""
    return SqlAlchemyClubDirectory(session)


def build_club_points(session: AsyncSession) -> ClubPoints:
    """Where a club is, for a Location area picked as a club in place of a
    reading (``docs/adr/0200`` §10): the Player profile's demand, signed in
    ``clubs/infrastructure/`` over the directory above."""
    return DirectoryClubPoints(build_club_directory(session))


# --------------------------------------------------------------------------
# Payments (docs/adr/0189 §4)
# --------------------------------------------------------------------------


def build_payment_provider(settings: Settings) -> PaymentProvider:
    """The one provider this process moves money through — **one per
    process**, whichever it is.

    The fake is one because a laptop's setups must outlive the request that
    opened them: the phone confirms in one request what another started. Stripe
    is one because its client holds an HTTP session, and a session per request
    is a session leaked per request. Which of the two is configuration
    (``PAYMENTS_PROVIDER``), and a deployed environment refuses the fake.
    """

    if settings.PAYMENTS_PROVIDER == "fake":
        return _the_laptop_s_fake()
    return _stripe_for(settings)


@lru_cache(maxsize=1)
def _the_laptop_s_fake() -> FakePayments:
    """A laptop's phone has no real provider to confirm a setup against, so its
    fake confirms every setup with ``A_CARD`` and finishes a club's onboarding
    the moment its link is made (``fake_payments.py``) — and dates a club's
    payout off the wall clock (#548)."""

    return FakePayments(
        confirms_every_setup_with=A_CARD,
        onboarding_completes=True,
        clock=build_clock(),
    )


#: The process's Stripe client — one, in any process that asks, by the keys it
#: was built over — kept here so the shutdown can close its HTTP session.
_STRIPE_CLIENTS: dict[tuple[str | None, str | None, float], StripePayments] = {}


def _stripe_for(settings: Settings) -> StripePayments:
    key = (
        settings.STRIPE_SECRET_KEY,
        settings.STRIPE_PUBLISHABLE_KEY,
        settings.STRIPE_TIMEOUT_SECONDS,
    )
    if key not in _STRIPE_CLIENTS:
        _STRIPE_CLIENTS[key] = build_stripe_payments(settings)
    return _STRIPE_CLIENTS[key]


async def close_payment_provider() -> None:
    """Close the HTTP session the process's Stripe client opened, if it made
    one — the API's shutdown, after every request and task is done with it."""

    clients = list(_STRIPE_CLIENTS.values())
    _STRIPE_CLIENTS.clear()
    for client in clients:
        await client.close()


def build_fake_payments() -> FakePayments:
    """A fresh fake that confirms nothing until it is told what the phone
    entered — a seed run's, and the demand suite's — dating a payout off the
    wall clock."""

    return FakePayments(clock=build_clock())


def build_stripe_payments(settings: Settings) -> StripePayments:
    """A fresh Stripe adapter over these keys, owning its own HTTP session —
    the demand suite's, which asks it from a new event loop every test."""

    return StripePayments(
        secret_key=settings.STRIPE_SECRET_KEY or "",
        publishable_key=settings.STRIPE_PUBLISHABLE_KEY or "",
        timeout_seconds=settings.STRIPE_TIMEOUT_SECONDS,
    )


def build_payment_notices(settings: Settings) -> PaymentNotices:
    """Stripe's platform webhook, verified with its secret — or, where no secret
    is placed, a reader that refuses every notice as unconfigured."""

    return StripeNotices(secret=settings.STRIPE_WEBHOOK_SECRET)


def build_connected_account_notices(settings: Settings) -> PaymentNotices:
    """Stripe's **Connected accounts** webhook — a club's account, and the
    payments made on it — verified with that endpoint's own secret (#537)."""

    return StripeNotices(secret=settings.STRIPE_CONNECT_WEBHOOK_SECRET)


def build_onboarding_pages(settings: Settings) -> OnboardingPages:
    """Where the provider's hosted pages send a club's desk back to: the club
    website's own pages, under its configured address."""

    return OnboardingPages(settings.CLUB_WEBSITE_URL)


def build_payments_accounts(provider: PaymentProvider) -> PaymentsAccounts:
    """A club's account at the provider, as the Club context asks for it —
    answered by the Payments context, which holds the provider, so the arrow
    runs ``payments → clubs`` only (#537)."""

    return ProviderPaymentsAccounts(provider)


def build_connected_accounts(
    session: AsyncSession,
    *,
    provider: PaymentProvider,
    settings: Settings,
    event_store: DomainEventStore,
    events: DomainEventPublisher,
    clock: Clock,
) -> ConnectedAccounts:
    """What a Connected accounts notice moves: the club's own use case, in the
    notice's transaction — the webhook commits the inbox row and the club's
    record together."""

    return ClubsConnectedAccounts(
        HeedPaymentsAccount(
            clubs=build_club_repository(
                session, event_store=event_store, events=events
            ),
            club_accounts=build_club_account_repository(
                session, event_store=event_store, events=events
            ),
            courts=build_club_courts_repository(
                session, event_store=event_store, events=events
            ),
            payments_accounts=build_payments_accounts(provider),
            mail=build_mail_queue(session),
            pages=build_onboarding_pages(settings),
            clock=clock,
        )
    )


def build_payment_method_repository(
    session: AsyncSession,
    *,
    event_store: DomainEventStore,
    events: DomainEventPublisher,
) -> PaymentMethodRepository:
    """One stream per player (``docs/adr/0189`` §5). Takes the session as well,
    because its ``save`` writes the customer row beside the stream."""

    return EventSourcedPaymentMethodRepository(
        session=session, event_store=event_store, events=events
    )


def build_payment_commitments(session: AsyncSession) -> PaymentCommitments:
    """What could still be charged to a method: the player's live yeses and
    booked games still ahead, answered by the Proposals context over its own
    directory and the bookings', so the arrow runs ``proposals → payments``."""

    return LiveYesCommitments(
        directory=build_proposal_directory(session),
        bookings=build_booking_directory(session),
    )


def build_seat_charge_repository(
    session: AsyncSession,
    *,
    event_store: DomainEventStore,
    events: DomainEventPublisher,
) -> SeatChargeRepository:
    """One stream per seat charge (``docs/adr/0189`` §5). Takes the session as
    well, because its ``save`` writes the ``seat_charges`` row beside it."""
    return EventSourcedSeatChargeRepository(
        session=session, event_store=event_store, events=events
    )


def _seat_charge_repository(
    session: AsyncSession, runtime: EventRuntime | None
) -> SeatChargeRepository:
    return build_seat_charge_repository(
        session,
        event_store=build_domain_event_store(session, runtime=runtime),
        events=build_event_publisher(session, runtime=runtime),
    )


def build_sellers(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> Sellers:
    """A club's name, its account at the provider and its desk — the seller."""
    return ClubSellers(
        directory=build_club_directory(session),
        courts=build_club_courts_repository(
            session,
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
        accounts=build_club_account_repository(
            session,
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
    )


def build_club_payout_repository(
    session: AsyncSession,
    *,
    event_store: DomainEventStore,
    events: DomainEventPublisher,
) -> ClubPayoutRepository:
    """One stream per club per day it is paid for (#548). Takes the session as
    well, because its ``save`` writes the payout's rows beside it."""
    return EventSourcedClubPayoutRepository(
        session=session, event_store=event_store, events=events
    )


def _club_payout_repository(
    session: AsyncSession, runtime: EventRuntime | None
) -> ClubPayoutRepository:
    return build_club_payout_repository(
        session,
        event_store=build_domain_event_store(session, runtime=runtime),
        events=build_event_publisher(session, runtime=runtime),
    )


def build_games_over(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> GamesOver:
    """Which games are over for good — the payouts' demand, answered off the
    bookings as Proposals reads them (#548)."""
    return BookedGamesOver(build_player_bookings(session, runtime=runtime))


def build_decide_club_payouts(
    session: AsyncSession, *, clock: Clock, runtime: EventRuntime | None = None
) -> DecideClubPayouts:
    """One run of the payouts job over this session — the job's, and a
    test's (#548). It decides; the outbox pays out."""
    return DecideClubPayouts(
        payouts=_club_payout_repository(session, runtime),
        charges=_seat_charge_repository(session, runtime),
        games=build_games_over(session, runtime=runtime),
        uow=build_unit_of_work(session),
        clock=clock,
    )


def build_send_club_payout(
    session: AsyncSession,
    *,
    provider: PaymentProvider,
    clock: Clock,
    settings: Settings,
    runtime: EventRuntime | None = None,
) -> SendClubPayout:
    """What a payout's decision leaves at the provider — built per delivery
    run, over the session the delivery commits in and the provider it holds.
    Its email opens the club website's Money page."""
    return SendClubPayout(
        payouts=_club_payout_repository(session, runtime),
        sellers=build_sellers(session, runtime=runtime),
        provider=provider,
        mail=build_mail_queue(session),
        clock=clock,
        money_page=f"{settings.CLUB_WEBSITE_URL.rstrip('/')}/money",
    )


def build_read_club_payouts(
    session: AsyncSession, *, provider: PaymentProvider
) -> ReadClubPayouts:
    """The payouts on a club's account, as the provider says they stand."""
    return ReadClubPayouts(sellers=build_sellers(session), provider=provider)


def build_payers(session: AsyncSession) -> Payers:
    return UserPayers(build_user_repository(session))


def build_charge_the_seats(
    session: AsyncSession,
    *,
    provider: PaymentProvider,
    settings: Settings,
    runtime: EventRuntime | None = None,
) -> ChargeTheSeats:
    """Every seat's share, all or nothing, over ``provider``; its emails open
    the app (``APP_SCHEME``)."""
    return ChargeTheSeats(
        methods=build_payment_method_repository(
            session,
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
        charges=_seat_charge_repository(session, runtime),
        sellers=build_sellers(session, runtime=runtime),
        payers=build_payers(session),
        provider=provider,
        mail=build_mail_queue(session),
        app_link=f"{settings.APP_SCHEME}://",
    )


def build_release_charges(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> ReleaseCharges:
    return ReleaseCharges(charges=_seat_charge_repository(session, runtime))


def build_confirm_seat_charge(
    session: AsyncSession,
    *,
    provider: PaymentProvider,
    runtime: EventRuntime | None = None,
) -> ConfirmSeatCharge:
    return ConfirmSeatCharge(
        charges=_seat_charge_repository(session, runtime), provider=provider
    )


def build_read_seat_charge(
    session: AsyncSession, *, provider: PaymentProvider
) -> ReadSeatCharge:
    return ReadSeatCharge(
        charges=_seat_charge_repository(session, None),
        sellers=build_sellers(session),
        provider=provider,
    )


def build_read_receipts(session: AsyncSession) -> ReadReceipts:
    return ReadReceipts(
        charges=_seat_charge_repository(session, None),
        sellers=build_sellers(session),
    )


def build_settle_seat_charges(
    session: AsyncSession,
    *,
    provider: PaymentProvider,
    clock: Clock,
    runtime: EventRuntime | None = None,
) -> SettleSeatCharges:
    """What a fill's verdict leaves at the provider — built per delivery run,
    over the session the delivery commits in and the provider it holds."""
    return SettleSeatCharges(
        charges=_seat_charge_repository(session, runtime),
        provider=provider,
        clock=clock,
    )


def build_email_the_seat_taken_refund(
    session: AsyncSession, *, settings: Settings, runtime: EventRuntime | None = None
) -> EmailTheSeatTakenRefund:
    """A seat-taken refund emailed once it is made, to the grosz (#641) —
    built per delivery run, over the session the delivery commits in."""
    return EmailTheSeatTakenRefund(
        charges=_seat_charge_repository(session, runtime),
        sellers=build_sellers(session, runtime=runtime),
        payers=build_payers(session),
        mail=build_mail_queue(session),
        app_link=f"{settings.APP_SCHEME}://",
    )


def build_notice_inbox(session: AsyncSession) -> NoticeInbox:
    return SqlAlchemyNoticeInbox(session)


# --------------------------------------------------------------------------
# Proposals (docs/adr/0189 §2, §5)
# --------------------------------------------------------------------------


def build_proposal_repository(
    session: AsyncSession,
    *,
    event_store: DomainEventStore,
    events: DomainEventPublisher,
) -> ProposalRepository:
    """One stream per proposed game. **It takes the session as well as the
    store**, because its ``save`` writes the proposals and proposal-people
    projections in the same transaction, as a group's does."""
    return EventSourcedProposalRepository(
        session=session, event_store=event_store, events=events
    )


def build_proposal_directory(session: AsyncSession) -> ProposalDirectory:
    return SqlAlchemyProposalDirectory(session)


def build_pools(session: AsyncSession) -> Pools:
    """The pools, and who is in each: a group's pool is filed under the group's
    id, and its players are the group's members now — read off the groups' own
    directory, never its table."""
    return GroupPools(session=session, groups=build_group_directory(session))


def build_player_fit(
    session: AsyncSession,
    *,
    runtime: EventRuntime | None = None,
    event_store: DomainEventStore | None = None,
) -> PlayerFit:
    """Whether two people may be on one game, by the matcher's own pair rule
    under the live ruleset: blocks off the log, genders, preferences and
    reliability filters off each profile, Levels off rating's published read,
    and — where a filter is on — everybody's points off ``player_score``'s
    (#661). ``event_store`` is the deck read's shared one (#704); every other
    caller gets a store of its own."""
    store = _own_or(event_store, session, runtime)
    return MatcherPlayerFit(
        blocks=build_block_query(session, runtime=runtime),
        profiles=build_player_profile_repository(
            event_store=store,
            events=build_event_publisher(session, runtime=runtime),
        ),
        ratings=build_rated_player_query(session, runtime=runtime, event_store=store),
        ruleset=build_ruleset(),
        scores=build_published_score_query(session, event_store=store),
    )


def build_court_hours(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> CourtHours:
    """What a club sells at an hour, with its share and book-by, off the hours
    the Club context publishes (``docs/adr/0189`` §5)."""
    return ClubCourtHours(build_sellable_court_hours(session, runtime=runtime))


def build_court_kinds(
    session: AsyncSession,
    *,
    runtime: EventRuntime | None = None,
    event_store: DomainEventStore | None = None,
) -> CourtKinds:
    """The kind of court a card promises — indoor, outdoor or neither — off the
    free courts of its sport at its club and hour (the mechanics §5.2, Q122)."""
    return SellableCourtKinds(
        build_sellable_court_hours(session, runtime=runtime, event_store=event_store)
    )


def build_proposal_club_names(session: AsyncSession) -> ProposalClubNames:
    return DirectoryClubNames(build_club_directory(session))


def build_read_live_yeses(
    session: AsyncSession, *, clock: Clock, runtime: EventRuntime | None = None
) -> ReadLiveYeses:
    """A player's live yeses, each with the kind of court it promises — the
    deck's own free-court read (#706)."""
    return ReadLiveYeses(
        directory=build_proposal_directory(session),
        clubs=build_proposal_club_names(session),
        kinds=build_court_kinds(session, runtime=runtime),
        clock=clock,
    )


def build_saved_methods(
    session: AsyncSession,
    *,
    event_store: DomainEventStore,
    events: DomainEventPublisher,
) -> SavedMethods:
    """Whether a player has a method to charge, off their Payment method stream
    — the one fact a yes needs from payments."""
    return PaymentsSavedMethods(
        build_payment_method_repository(session, event_store=event_store, events=events)
    )


def build_proposal_guards(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> Guards:
    """The checks a version and a yes are held to outside the aggregate: the
    pool, the fit, a method to charge, the kind the player's intent wants
    (Q127) — and, on a post, who it is for (#546)."""
    return Guards(
        pools=build_pools(session),
        fit=build_player_fit(session, runtime=runtime),
        methods=build_saved_methods(
            session,
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
        players=build_players_in_play(session, runtime=runtime),
        members=build_read_members(session, runtime=runtime),
        wanted=build_wanted_kinds(session, runtime=runtime),
    )


def build_make_proposal(
    session: AsyncSession, *, clock: Clock, runtime: EventRuntime | None = None
) -> MakeProposal:
    """The dealer's first act — the engine's (#540), a seed's or a test's; no
    route makes a proposal. Built here so each of them gets the wiring a
    request would, over the session and the clock it holds."""
    return MakeProposal(
        proposals=build_proposal_repository(
            session,
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
        pools=build_pools(session),
        court_hours=build_court_hours(session, runtime=runtime),
        guards=build_proposal_guards(session, runtime=runtime),
        uow=build_unit_of_work(session),
        clock=clock,
    )


def build_deal_version(
    session: AsyncSession, *, clock: Clock, runtime: EventRuntime | None = None
) -> DealVersion:
    """The dealer's second act: one more version of a game still filling."""
    return DealVersion(
        proposals=build_proposal_repository(
            session,
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
        guards=build_proposal_guards(session, runtime=runtime),
        uow=build_unit_of_work(session),
        clock=clock,
    )


def build_withdraw_a_leavers_yeses(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> WithdrawALeaversYeses:
    """What leaving a group does to the leaver's yeses in its pool — built per
    delivery run, over the session the delivery commits in."""
    return WithdrawALeaversYeses(
        proposals=build_proposal_repository(
            session,
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
        directory=build_proposal_directory(session),
        undecided=build_undecided_charges(session, runtime=runtime),
    )


def build_withdraw_a_blockers_yeses(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> WithdrawABlockersYeses:
    """What a block does to the blocker's yeses where the blocked player is In
    (``docs/adr/0193`` §4) — built per delivery run, over the session the
    delivery commits in."""
    return WithdrawABlockersYeses(
        proposals=build_proposal_repository(
            session,
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
        directory=build_proposal_directory(session),
        undecided=build_undecided_charges(session, runtime=runtime),
    )


def build_resume_paused_yeses(
    session: AsyncSession,
    *,
    provider: PaymentProvider,
    settings: Settings,
    runtime: EventRuntime | None = None,
) -> ResumePausedYeses:
    """A paused week back, when a booked game stops being a player's — built
    per delivery run over its session and provider, since a yes that comes back
    as a game's last seat fills it (#544)."""
    proposals = build_proposal_repository(
        session,
        event_store=build_domain_event_store(session, runtime=runtime),
        events=build_event_publisher(session, runtime=runtime),
    )
    return ResumePausedYeses(
        proposals=proposals,
        directory=build_proposal_directory(session),
        games_and_money=build_games_and_money_repository(
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
        booked=build_booked_games(session),
        guards=build_proposal_guards(session, runtime=runtime),
        fill=build_fill(
            session,
            proposals=proposals,
            provider=provider,
            settings=settings,
            runtime=runtime,
        ),
    )


def build_expire_proposals(session: AsyncSession, *, clock: Clock) -> ExpireProposals:
    """One book-by sweep over this session — the job's, and a test's."""
    return ExpireProposals(
        clock=clock,
        proposals=build_proposal_repository(
            session,
            event_store=build_domain_event_store(session),
            events=build_event_publisher(session),
        ),
        directory=build_proposal_directory(session),
        undecided=build_undecided_charges(session),
        unit_of_work=build_unit_of_work(session),
    )


def build_games_and_money_repository(
    *,
    event_store: DomainEventStore,
    events: DomainEventPublisher,
) -> GamesAndMoneyRepository:
    """A player's Games & money, one stream per player under their own id —
    per unit of work, for the reason every aggregate repository is."""
    return EventSourcedGamesAndMoneyRepository(event_store=event_store, events=events)


def build_booked_games(session: AsyncSession) -> BookedGames:
    """The games a player has booked — what *games per week* and *one game per
    hour* count — off the bookings' own projection (#541)."""
    return BookingsBookedGames(build_booking_directory(session))


def build_deck_people(
    session: AsyncSession,
    *,
    settings: Settings,
    runtime: EventRuntime | None = None,
    event_store: DomainEventStore | None = None,
) -> DeckPeople:
    """What a card draws of a person: a name from ``users``, a face and a week
    from the Player profile, a published Level from rating. The window is the
    platform's one photo window. ``event_store`` as ``_own_or`` reads it."""
    store = _own_or(event_store, session, runtime)
    return ProfileDeckPeople(
        users=build_user_repository(session),
        profiles=build_player_profile_repository(
            event_store=store,
            events=build_event_publisher(session, runtime=runtime),
        ),
        photos=build_photo_storage(settings),
        ratings=build_rated_player_query(session, runtime=runtime, event_store=store),
        photo_link_minutes=settings.PHOTO_URL_VALID_FOR_MINUTES,
    )


def build_balance_forecasts(
    session: AsyncSession,
    *,
    runtime: EventRuntime | None = None,
    event_store: DomainEventStore | None = None,
) -> BalanceForecasts:
    """How even a card's game is forecast: the engine's own forecast under the
    live ruleset, over rating's estimates. ``event_store`` as ``_own_or``
    reads it."""
    return MatcherBalanceForecasts(
        ratings=build_rated_player_query(
            session, runtime=runtime, event_store=event_store
        ),
        ruleset=build_ruleset(),
    )


def build_club_terms(
    session: AsyncSession,
    *,
    runtime: EventRuntime | None = None,
    event_store: DomainEventStore | None = None,
) -> ClubTerms:
    """Which clubs sell through Raketa now, and each one's cut-off — off the
    offer the Club context publishes. ``event_store`` as ``_own_or`` reads it."""
    return SellableClubTerms(
        build_sellable_court_hours(session, runtime=runtime, event_store=event_store)
    )


def build_wanted_kinds(
    session: AsyncSession,
    *,
    runtime: EventRuntime | None = None,
    event_store: DomainEventStore | None = None,
) -> WantedKinds:
    """Which kinds of game a player wants in a sport, off their Play intent.
    ``event_store`` as ``_own_or`` reads it."""
    return ProfileWantedKinds(
        build_play_intent_declaration_repository(
            event_store=_own_or(event_store, session, runtime),
            events=build_event_publisher(session, runtime=runtime),
        )
    )


def build_read_group_deck_once(
    session: AsyncSession,
    *,
    settings: Settings,
    clock: Clock,
    booked: BookedGames | None = None,
    runtime: EventRuntime | None = None,
) -> ReadGroupDeck:
    """The Games tab's deck read, **for one request**: every adapter reads
    streams through one store that loads each once (#704, ``docs/adr/0197``
    §2c).

    The read replays a person's profile and rating streams for the pair rule,
    the forecasts and the card's people, and a rescue's candidates again;
    handed one ``ReadOnceEventStore`` they replay each once. It lives as long
    as the object built here, which is the request, and nothing it remembers
    outlives the transaction that read it.

    **Named apart from ``build_read_group_deck`` because the reuse is the
    request's alone.** A use case that appends and reloads must see its own
    events, and so must a reader that lives beside writers: the notifications
    handler asks the deck ``shows`` for every row of an outbox batch, over one
    session, while other handlers in the same batch append to the proposal and
    booking streams. That caller, and the seed's screen assertion, take the
    plain builder; only the routes' reads take this one — the deck's
    dependency, and the deck counts' (``build_read_deck_counts``, #739).
    """
    return build_read_group_deck(
        session,
        settings=settings,
        clock=clock,
        booked=booked,
        runtime=runtime,
        event_store=ReadOnceEventStore(
            build_domain_event_store(session, runtime=runtime)
        ),
    )


def build_read_group_deck(
    session: AsyncSession,
    *,
    settings: Settings,
    clock: Clock,
    booked: BookedGames | None = None,
    runtime: EventRuntime | None = None,
    event_store: DomainEventStore | None = None,
) -> ReadGroupDeck:
    """A reader's group deck over the store itself — the notifications
    handler's (``build_decks``) and the seed's screen assertion; the route
    takes ``build_read_group_deck_once``. ``booked`` is the one port a caller
    may hand in, because a test stands in for the bookings; ``event_store`` is
    the request's read-once store when that builder hands one in, and
    otherwise every adapter here reads the session's own."""
    store = _own_or(event_store, session, runtime)
    return ReadGroupDeck(
        pools=build_pools(session),
        directory=build_proposal_directory(session),
        proposals=build_proposal_repository(
            session,
            event_store=store,
            events=build_event_publisher(session, runtime=runtime),
        ),
        settings=build_games_and_money_repository(
            event_store=store,
            events=build_event_publisher(session, runtime=runtime),
        ),
        wanted=build_wanted_kinds(session, runtime=runtime, event_store=store),
        booked=booked if booked is not None else build_booked_games(session),
        terms=build_club_terms(session, runtime=runtime, event_store=store),
        kinds=build_court_kinds(session, runtime=runtime, event_store=store),
        fit=build_player_fit(session, runtime=runtime, event_store=store),
        forecasts=build_balance_forecasts(session, runtime=runtime, event_store=store),
        people=build_deck_people(
            session, settings=settings, runtime=runtime, event_store=store
        ),
        clubs=build_proposal_club_names(session),
        offers=build_rescue_offers(
            session, booked=booked, runtime=runtime, event_store=store
        ),
        players=build_players_in_play(session, runtime=runtime, event_store=store),
        relations=build_reader_relations(session, runtime=runtime),
        clock=clock,
    )


def build_read_deck_counts(
    session: AsyncSession,
    *,
    settings: Settings,
    clock: Clock,
    booked: BookedGames | None = None,
) -> ReadDeckCounts:
    """The reader's cards per kind across their groups (#739), **for one
    request**: each group's switch read by the route's own deck read, whose
    one ``ReadOnceEventStore`` the groups share — a person on cards in two
    groups is replayed once. Read-only, so nothing beside it appends."""
    return ReadDeckCounts(
        pools=build_pools(session),
        deck=build_read_group_deck_once(
            session, settings=settings, clock=clock, booked=booked
        ),
    )


def build_where_pools_play(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> WherePoolsPlay:
    """Where a pool may play: a group's home club, and the clubs within ten
    kilometres of it — measured between the clubs' own points — or, for an
    official group, what its club's settings allow."""
    return GroupClubs(
        groups=build_group_directory(session),
        clubs=build_club_directory(session),
        sellable=build_sellable_court_hours(session, runtime=runtime),
    )


def build_players_in_play(
    session: AsyncSession,
    *,
    runtime: EventRuntime | None = None,
    event_store: DomainEventStore | None = None,
) -> PlayersInPlay:
    """Each member's Level off rating's estimates and week off their profile —
    what the proposer deals from. ``event_store`` as ``_own_or`` reads it."""
    store = _own_or(event_store, session, runtime)
    return ProfilePlayersInPlay(
        profiles=build_player_profile_repository(
            event_store=store,
            events=build_event_publisher(session, runtime=runtime),
        ),
        ratings=build_rated_player_query(session, runtime=runtime, event_store=store),
    )


def build_propose_games(
    session: AsyncSession,
    *,
    clock: Clock,
    booked: BookedGames | None = None,
    runtime: EventRuntime | None = None,
) -> ProposeGames:
    """The proposer over this session and clock — the job's, a seed's and a
    test's (#540). It deals through the dealer's own acts, built here beside
    it, and weighs a game's evenness by the live ruleset's balance rules.
    ``booked`` is the one port a caller may hand in, as the deck's is, while
    nothing can be booked yet."""
    return ProposeGames(
        pools=build_pools(session),
        where=build_where_pools_play(session, runtime=runtime),
        court_hours=build_court_hours(session, runtime=runtime),
        members=build_read_members(session, booked=booked, runtime=runtime),
        directory=build_proposal_directory(session),
        proposals=build_proposal_repository(
            session,
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
        fit=build_player_fit(session, runtime=runtime),
        make=build_make_proposal(session, clock=clock, runtime=runtime),
        deal=build_deal_version(session, clock=clock, runtime=runtime),
        undecided=build_undecided_charges(session, runtime=runtime),
        uow=build_unit_of_work(session),
        clock=clock,
        balance=build_ruleset().balance,
    )


def build_deal_the_pool_now(
    session: AsyncSession,
    *,
    clock: Clock,
    booked: BookedGames | None = None,
) -> DealThePoolNow:
    """A member's *deal my group now* (#739; ``docs/adr/0201`` §5): the
    proposer the jobs run, over the request's session and clock, behind the
    deck's refusal of a stranger. ``booked`` as the proposer's."""
    return DealThePoolNow(
        pools=build_pools(session),
        proposer=build_propose_games(session, clock=clock, booked=booked),
    )


# --------------------------------------------------------------------------
# The fill (docs/adr/0189 §2, §4–§5; #541)
# --------------------------------------------------------------------------


def build_seat_charges(
    session: AsyncSession,
    *,
    provider: PaymentProvider,
    settings: Settings,
    runtime: EventRuntime | None = None,
) -> SeatCharges:
    """Every seat's share all or nothing, and a refused payment confirmed —
    the Payments context's use cases over the provider this caller holds, so
    a request charges where its requests save cards and a seed at its fake."""
    return PaymentsSeatCharges(
        charge=build_charge_the_seats(
            session, provider=provider, settings=settings, runtime=runtime
        ),
        confirm=build_confirm_seat_charge(session, provider=provider, runtime=runtime),
        to_confirm=PaymentToConfirmOn(
            charges=_seat_charge_repository(session, runtime)
        ),
    )


def build_undecided_charges(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> UndecidedCharges:
    """The charges a game will not be paid with, let go — asks nothing of the
    provider: the cancellation follows the commit, from the outbox."""
    return PaymentsUndecidedCharges(build_release_charges(session, runtime=runtime))


def build_game_bookings(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> GameBookings:
    """A full game's court and its booking, over the Bookings context's own
    use cases."""
    return BookingsGameBookings(
        find=build_find_a_court(session, runtime=runtime),
        book=build_book_the_game(session, runtime=runtime),
    )


def build_booked_game_changes(
    session: AsyncSession, *, settings: Settings, runtime: EventRuntime | None = None
) -> BookedGameChanges:
    """Leaving a booked game, a rescue taking the seat, a no to it or a seat
    kept for a refused rescuer (#640), and the cut-off — over the Bookings
    context's own use cases, the cut-off's email to the club opening its
    Bookings page (#544, #545)."""

    def bookings() -> BookingRepository:
        return build_booking_repository(
            session,
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        )

    return BookingsBookedGameChanges(
        leave=LeaveTheBooking(
            bookings=bookings(), games=build_game_changes(session, runtime=runtime)
        ),
        rescue=RescueTheSeat(
            bookings=bookings(), games=build_game_changes(session, runtime=runtime)
        ),
        say_no=SayNoToTheSeat(bookings=bookings()),
        fix=TimeToFixTheCard(
            bookings=bookings(), games=build_game_changes(session, runtime=runtime)
        ),
        keep=KeepTheSeat(bookings=bookings()),
        call_off=CallOffAtTheCutOff(
            bookings=bookings(),
            games=build_game_changes(session, runtime=runtime),
            desks=build_club_desks(session, runtime=runtime),
            mail=build_mail_queue(session),
            bookings_page=f"{settings.CLUB_WEBSITE_URL.rstrip('/')}/bookings",
        ),
        directory=build_booking_directory(session),
    )


def build_late_refunds(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> LateRefunds:
    """What a leaver after the cut-off would get back if somebody took their
    seat — the share less exactly the fee kept on their payment (#641)."""
    return PaymentsLateRefunds(_seat_charge_repository(session, runtime))


def build_seat_refunds(
    session: AsyncSession, *, settings: Settings, runtime: EventRuntime | None = None
) -> SeatRefunds:
    """A booked game's paid shares given back — decided in the act, refunded
    at the provider from the outbox — and each player emailed (#544); and a
    leaver after the cut-off told what would come back (#641)."""
    charges = _seat_charge_repository(session, runtime)
    sellers = build_sellers(session, runtime=runtime)
    payers = build_payers(session)
    mail = build_mail_queue(session)
    app_link = f"{settings.APP_SCHEME}://"
    return PaymentsSeatRefunds(
        GiveTheSharesBack(
            charges=charges,
            sellers=sellers,
            payers=payers,
            mail=mail,
            app_link=app_link,
        ),
        late_leaver=TellTheLateLeaver(
            charges=charges,
            sellers=sellers,
            payers=payers,
            mail=mail,
            app_link=app_link,
        ),
    )


def build_leave_the_game(
    session: AsyncSession,
    *,
    clock: Clock,
    settings: Settings,
    runtime: EventRuntime | None = None,
) -> LeaveTheGame:
    """*Leave the game* — the hold let go before the cut-off (#637), offered
    to others after it, and the yes withdrawn while a payment is awaited
    (#544, #625)."""
    return LeaveTheGame(
        proposals=build_proposal_repository(
            session,
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
        bookings=build_player_bookings(session, runtime=runtime),
        friends_games=build_friends_game_bookings(session, runtime=runtime),
        games=build_booked_game_changes(session, settings=settings, runtime=runtime),
        refunds=build_seat_refunds(session, settings=settings, runtime=runtime),
        undecided=build_undecided_charges(session, runtime=runtime),
        uow=build_unit_of_work(session),
        clock=clock,
    )


def build_held_shares(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> HeldShares:
    """The shares held for booked games until their cut-off, which takes them
    (#637)."""
    return PaymentsHeldShares(
        TakeTheHeldShares(charges=_seat_charge_repository(session, runtime))
    )


def build_checked_shares(
    session: AsyncSession,
    *,
    provider: PaymentProvider,
    settings: Settings,
    runtime: EventRuntime | None = None,
) -> CheckedShares:
    """The shares checked at their game's fill, held again at their Holding
    time over ``provider`` — the job's own, a console press's, a test's — each
    refused player emailed to fix their card (#639)."""
    return PaymentsCheckedShares(
        HoldTheCheckedShares(
            methods=build_payment_method_repository(
                session,
                event_store=build_domain_event_store(session, runtime=runtime),
                events=build_event_publisher(session, runtime=runtime),
            ),
            charges=_seat_charge_repository(session, runtime),
            sellers=build_sellers(session, runtime=runtime),
            payers=build_payers(session),
            provider=provider,
            mail=build_mail_queue(session),
            app_link=f"{settings.APP_SCHEME}://",
        )
    )


def build_cards_to_fix(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> CardsToFix:
    """A refused holding kept once its card is fixed, or let go when the time
    to fix it runs out — asks nothing of the provider: the cancellation follows
    the commit, from the outbox (#639)."""
    charges = _seat_charge_repository(session, runtime)
    return PaymentsCardsToFix(
        keep=KeepTheFixedShare(charges=charges),
        let_go=LetTheUnfixedShareGo(charges=charges),
    )


def build_holding_times(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> HoldingTimes:
    """When a share only checked at its game's fill is held (#639)."""
    return PaymentsHoldingTimes(_seat_charge_repository(session, runtime))


def build_the_holding(
    session: AsyncSession,
    *,
    clock: Clock,
    provider: PaymentProvider,
    settings: Settings,
    runtime: EventRuntime | None = None,
) -> TheHolding:
    """One holding run over this session — the job's, the console's and a
    test's (#639): every checked share whose Holding time has come, held again
    over ``provider``."""
    return TheHolding(
        proposals=build_proposal_repository(
            session,
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
        bookings=build_player_bookings(session, runtime=runtime),
        games=build_booked_game_changes(session, settings=settings, runtime=runtime),
        checked=build_checked_shares(
            session, provider=provider, settings=settings, runtime=runtime
        ),
        cards=build_cards_to_fix(session, runtime=runtime),
        friends_games=build_friends_game_bookings(session, runtime=runtime),
        uow=build_unit_of_work(session),
        clock=clock,
    )


def build_the_cut_off(
    session: AsyncSession,
    *,
    clock: Clock,
    settings: Settings,
    runtime: EventRuntime | None = None,
) -> TheCutOff:
    """One cut-off run over this session — the job's, and a test's (#544,
    #637): short games called off, full games' held shares taken."""
    return TheCutOff(
        proposals=build_proposal_repository(
            session,
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
        bookings=build_player_bookings(session, runtime=runtime),
        games=build_booked_game_changes(session, settings=settings, runtime=runtime),
        refunds=build_seat_refunds(session, settings=settings, runtime=runtime),
        held=build_held_shares(session, runtime=runtime),
        undecided=build_undecided_charges(session, runtime=runtime),
        friends_games=build_friends_game_bookings(session, runtime=runtime),
        covers=build_covers_at_the_cut_off(session, runtime=runtime),
        uow=build_unit_of_work(session),
        clock=clock,
    )


def build_club_desks(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> ClubDesks:
    """Whom an email to a club goes to — its one sign-in — and its name."""
    return AccountClubDesks(
        accounts=build_club_account_repository(
            session,
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
        directory=build_club_directory(session),
    )


def build_proposal_player_names(session: AsyncSession) -> ProposalPlayerNames:
    """What each player is called — the club's only view of a player on its
    bookings (#547)."""
    return UsersPlayerNames(build_user_repository(session))


def build_fill(
    session: AsyncSession,
    *,
    proposals: ProposalRepository,
    provider: PaymentProvider,
    settings: Settings,
    runtime: EventRuntime | None = None,
) -> Fill:
    """What the last yes does. ``proposals`` is the yes's own repository, so
    the other yeses it withdraws or pauses are appended through the one that
    loaded the game."""
    return Fill(
        proposals=proposals,
        directory=build_proposal_directory(session),
        terms=build_club_terms(session, runtime=runtime),
        bookings=build_game_bookings(session, runtime=runtime),
        charges=build_seat_charges(
            session, provider=provider, settings=settings, runtime=runtime
        ),
        undecided=build_undecided_charges(session, runtime=runtime),
        forecasts=build_balance_forecasts(session, runtime=runtime),
        games_and_money=build_games_and_money_repository(
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
        booked=build_booked_games(session),
        fit=build_player_fit(session, runtime=runtime),
        players=build_players_in_play(session, runtime=runtime),
    )


def build_say_yes(
    session: AsyncSession,
    *,
    clock: Clock,
    provider: PaymentProvider,
    settings: Settings,
    runtime: EventRuntime | None = None,
) -> SayYes:
    """A swipe right — the phone's, a seed's — and, when it is the last, the
    fill over this caller's provider."""
    proposals = build_proposal_repository(
        session,
        event_store=build_domain_event_store(session, runtime=runtime),
        events=build_event_publisher(session, runtime=runtime),
    )
    return SayYes(
        proposals=proposals,
        guards=build_proposal_guards(session, runtime=runtime),
        fill=build_fill(
            session,
            proposals=proposals,
            provider=provider,
            settings=settings,
            runtime=runtime,
        ),
        undecided=build_undecided_charges(session, runtime=runtime),
        uow=build_unit_of_work(session),
        clock=clock,
    )


def build_withdraw_yes(
    session: AsyncSession,
    *,
    clock: Clock,
    runtime: EventRuntime | None = None,
) -> WithdrawYes:
    """*Withdraw* — and *Leave the game* while a payment is awaited (#625)."""
    return WithdrawYes(
        proposals=build_proposal_repository(
            session,
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
        undecided=build_undecided_charges(session, runtime=runtime),
        uow=build_unit_of_work(session),
        clock=clock,
    )


# The club runs its bookings (#547) ------------------------------------------


def build_club_bookings(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> ClubBookings:
    """A club's bookings as its desk reads and runs them, over the Bookings
    context's own use cases: a day of them, the free courts and the move, and
    the cancel (#547) — which a free court may absorb (#672)."""

    def bookings() -> BookingRepository:
        return build_booking_repository(
            session,
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        )

    return BookingsClubBookings(
        bookings=bookings(),
        directory=build_booking_directory(session),
        move=MoveTheBooking(
            bookings=bookings(),
            courts=build_club_courts_at_the_hour(session, runtime=runtime),
        ),
        cancel=CancelTheBooking(
            bookings=bookings(),
            games=build_game_changes(session, runtime=runtime),
            courts=build_club_courts_at_the_hour(session, runtime=runtime),
            closures=build_court_closures(session, runtime=runtime),
        ),
    )


def build_booking_takings(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> BookingTakings:
    """What each booking took from its players and gave back, off its Seat
    charges (#547) — and whether a payout carried it (#548)."""
    return PaymentsBookingTakings(
        _seat_charge_repository(session, runtime),
        _club_payout_repository(session, runtime),
    )


def build_pool_origins(session: AsyncSession) -> PoolOrigins:
    """The group each pool is — a booking's *where it came from* (#547)."""
    return GroupPoolOrigins(build_group_directory(session))


def build_read_club_bookings(
    session: AsyncSession, *, clock: Clock, runtime: EventRuntime | None = None
) -> ReadClubBookings:
    """A day of a club's bookings — the Bookings page (#547)."""
    return ReadClubBookings(
        bookings=build_club_bookings(session, runtime=runtime),
        takings=build_booking_takings(session, runtime=runtime),
        origins=build_pool_origins(session),
        names=build_proposal_player_names(session),
        clock=clock,
    )


def build_read_club_money(
    session: AsyncSession, *, clock: Clock, runtime: EventRuntime | None = None
) -> ReadClubMoney:
    """A month of a club's money — the Money page (#548)."""
    return ReadClubMoney(
        bookings=build_club_bookings(session, runtime=runtime),
        takings=build_booking_takings(session, runtime=runtime),
        clock=clock,
    )


def build_read_free_courts(
    session: AsyncSession, *, clock: Clock, runtime: EventRuntime | None = None
) -> ReadFreeCourts:
    """Where a club may move a game — the Move dialog (#547)."""
    return ReadFreeCourts(
        bookings=build_player_bookings(session, runtime=runtime),
        club=build_club_bookings(session, runtime=runtime),
        clock=clock,
    )


def build_move_the_game(
    session: AsyncSession, *, clock: Clock, runtime: EventRuntime | None = None
) -> MoveTheGame:
    """*Move* — the game onto another free court of its sport at its hour."""
    return MoveTheGame(
        proposals=build_proposal_repository(
            session,
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
        bookings=build_player_bookings(session, runtime=runtime),
        club=build_club_bookings(session, runtime=runtime),
        uow=build_unit_of_work(session),
        clock=clock,
    )


def build_preview_the_cancel(
    session: AsyncSession, *, clock: Clock, runtime: EventRuntime | None = None
) -> PreviewTheCancel:
    """What a cancel with a reason would do now — the Cancel dialog (#672)."""
    return PreviewTheCancel(
        bookings=build_player_bookings(session, runtime=runtime),
        club=build_club_bookings(session, runtime=runtime),
        clock=clock,
    )


def build_cancel_the_game(
    session: AsyncSession,
    *,
    clock: Clock,
    settings: Settings,
    runtime: EventRuntime | None = None,
) -> CancelTheGame:
    """*Cancel* — moved onto a free court that absorbs it (#672), or called
    off: everybody refunded in full, nobody's record, a new card first
    (#547)."""
    return CancelTheGame(
        proposals=build_proposal_repository(
            session,
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
        bookings=build_player_bookings(session, runtime=runtime),
        club=build_club_bookings(session, runtime=runtime),
        refunds=build_seat_refunds(session, settings=settings, runtime=runtime),
        undecided=build_undecided_charges(session, runtime=runtime),
        uow=build_unit_of_work(session),
        clock=clock,
    )


def build_run_out_the_time_to_pay(
    session: AsyncSession,
    *,
    clock: Clock,
    settings: Settings,
    runtime: EventRuntime | None = None,
) -> RunOutTheTimeToPay:
    """One run of the time-to-pay deadline over this session — the job's, the
    console's and a test's (#625, #626)."""
    return RunOutTheTimeToPay(
        proposals=build_proposal_repository(
            session,
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
        directory=build_proposal_directory(session),
        undecided=build_undecided_charges(session, runtime=runtime),
        bookings=build_player_bookings(session, runtime=runtime),
        games=build_booked_game_changes(session, settings=settings, runtime=runtime),
        cards=build_cards_to_fix(session, runtime=runtime),
        uow=build_unit_of_work(session),
        clock=clock,
    )


def build_confirm_payment(
    session: AsyncSession,
    *,
    clock: Clock,
    provider: PaymentProvider,
    settings: Settings,
    runtime: EventRuntime | None = None,
) -> ConfirmPayment:
    """*I confirmed my payment in the app* — the yes again."""
    proposals = build_proposal_repository(
        session,
        event_store=build_domain_event_store(session, runtime=runtime),
        events=build_event_publisher(session, runtime=runtime),
    )
    return ConfirmPayment(
        proposals=proposals,
        guards=build_proposal_guards(session, runtime=runtime),
        fill=build_fill(
            session,
            proposals=proposals,
            provider=provider,
            settings=settings,
            runtime=runtime,
        ),
        charges=build_seat_charges(
            session, provider=provider, settings=settings, runtime=runtime
        ),
        undecided=build_undecided_charges(session, runtime=runtime),
        rescuer=build_rescuer(
            session,
            proposals=proposals,
            provider=provider,
            settings=settings,
            runtime=runtime,
        ),
        bookings=build_player_bookings(session, runtime=runtime),
        games=build_booked_game_changes(session, settings=settings, runtime=runtime),
        cards=build_cards_to_fix(session, runtime=runtime),
        friends=build_friends_game_confirmation(
            session, provider=provider, settings=settings, runtime=runtime
        ),
        uow=build_unit_of_work(session),
        clock=clock,
    )


# --------------------------------------------------------------------------
# Rescues: seats to fill (#545)
# --------------------------------------------------------------------------


def build_rescue_offers(
    session: AsyncSession,
    *,
    booked: BookedGames | None = None,
    runtime: EventRuntime | None = None,
    event_store: DomainEventStore | None = None,
) -> RescueOffers:
    """Who a booked game's open seat is offered to, and its best fits — read
    live over the pool's members (#545). ``booked`` as the deck's, and
    ``event_store`` as ``_own_or`` reads it."""
    store = _own_or(event_store, session, runtime)
    return RescueOffers(
        pools=build_pools(session),
        bookings=build_player_bookings(session, runtime=runtime, event_store=store),
        wanted=build_wanted_kinds(session, runtime=runtime, event_store=store),
        settings=build_games_and_money_repository(
            event_store=store,
            events=build_event_publisher(session, runtime=runtime),
        ),
        booked=booked if booked is not None else build_booked_games(session),
        players=build_players_in_play(session, runtime=runtime, event_store=store),
        fit=build_player_fit(session, runtime=runtime, event_store=store),
        forecasts=build_balance_forecasts(session, runtime=runtime, event_store=store),
    )


def build_rescuer(
    session: AsyncSession,
    *,
    proposals: ProposalRepository,
    provider: PaymentProvider,
    settings: Settings,
    runtime: EventRuntime | None = None,
) -> Rescuer:
    """Taking an open seat — the joiner's share over this caller's provider,
    the leaver's refund, the seat on the booking and its Game (#545).
    ``proposals`` is the caller's, whose row the join locked."""
    return Rescuer(
        bookings=build_player_bookings(session, runtime=runtime),
        offers=build_rescue_offers(session, runtime=runtime),
        guards=build_proposal_guards(session, runtime=runtime),
        methods=build_saved_methods(
            session,
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
        changes=build_booked_game_changes(session, settings=settings, runtime=runtime),
        charges=build_seat_charges(
            session, provider=provider, settings=settings, runtime=runtime
        ),
        refunds=build_seat_refunds(session, settings=settings, runtime=runtime),
        undecided=build_undecided_charges(session, runtime=runtime),
        holding_times=build_holding_times(session, runtime=runtime),
        fill=build_fill(
            session,
            proposals=proposals,
            provider=provider,
            settings=settings,
            runtime=runtime,
        ),
    )


def build_join_a_rescue(
    session: AsyncSession,
    *,
    clock: Clock,
    provider: PaymentProvider,
    settings: Settings,
    runtime: EventRuntime | None = None,
) -> JoinARescue:
    """*I'm in* on an open seat — the phone's, a seed's (#545)."""
    proposals = build_proposal_repository(
        session,
        event_store=build_domain_event_store(session, runtime=runtime),
        events=build_event_publisher(session, runtime=runtime),
    )
    return JoinARescue(
        proposals=proposals,
        friends_games=build_friends_game_bookings(session, runtime=runtime),
        rescuer=build_rescuer(
            session,
            proposals=proposals,
            provider=provider,
            settings=settings,
            runtime=runtime,
        ),
        uow=build_unit_of_work(session),
        clock=clock,
    )


def build_say_no_to_a_rescue(
    session: AsyncSession,
    *,
    clock: Clock,
    settings: Settings,
    runtime: EventRuntime | None = None,
) -> SayNoToARescue:
    """*Not this time* on a Seat open card (#545)."""
    return SayNoToARescue(
        proposals=build_proposal_repository(
            session,
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
        friends_games=build_friends_game_bookings(session, runtime=runtime),
        bookings=build_player_bookings(session, runtime=runtime),
        offers=build_rescue_offers(session, runtime=runtime),
        changes=build_booked_game_changes(session, settings=settings, runtime=runtime),
        uow=build_unit_of_work(session),
        clock=clock,
    )


def build_read_fill_in(
    session: AsyncSession,
    *,
    settings: Settings,
    clock: Clock,
    booked: BookedGames | None = None,
    runtime: EventRuntime | None = None,
) -> ReadFillIn:
    """A group's *Fill in* tab — Seats to fill and its badge (#545)."""
    return ReadFillIn(
        pools=build_pools(session),
        offers=build_rescue_offers(session, booked=booked, runtime=runtime),
        people=build_deck_people(session, settings=settings, runtime=runtime),
        clubs=build_proposal_club_names(session),
        relations=build_reader_relations(session, runtime=runtime),
        clock=clock,
    )


# --------------------------------------------------------------------------
# Posting a game (#546)
# --------------------------------------------------------------------------


def build_read_members(
    session: AsyncSession,
    *,
    booked: BookedGames | None = None,
    runtime: EventRuntime | None = None,
) -> ReadMembers:
    """A pool's members as the proposer reads them — posting's best fits are
    counted from the same reading. ``booked`` as the deck's."""
    return ReadMembers(
        players=build_players_in_play(session, runtime=runtime),
        wanted=build_wanted_kinds(session, runtime=runtime),
        settings=build_games_and_money_repository(
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
        booked=booked if booked is not None else build_booked_games(session),
    )


def build_read_posting(
    session: AsyncSession,
    *,
    booked: BookedGames | None = None,
    runtime: EventRuntime | None = None,
) -> ReadPosting:
    """What every step of posting a game reads: who it is for, the poster's
    best fits and the pool's courts, and the games already happening (#546)."""
    return ReadPosting(
        pools=build_pools(session),
        where=build_where_pools_play(session, runtime=runtime),
        court_hours=build_court_hours(session, runtime=runtime),
        members=build_read_members(session, booked=booked, runtime=runtime),
        fit=build_player_fit(session, runtime=runtime),
        directory=build_proposal_directory(session),
        proposals=build_proposal_repository(
            session,
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
        offers=build_rescue_offers(session, booked=booked, runtime=runtime),
    )


def build_read_posting_grid(
    session: AsyncSession,
    *,
    clock: Clock,
    booked: BookedGames | None = None,
    runtime: EventRuntime | None = None,
) -> ReadPostingGrid:
    """The posting grid — a week of a poster's best fits and courts (#546)."""
    return ReadPostingGrid(
        posting=build_read_posting(session, booked=booked, runtime=runtime),
        clock=clock,
    )


def build_read_posting_slot(
    session: AsyncSession,
    *,
    settings: Settings,
    clock: Clock,
    booked: BookedGames | None = None,
    runtime: EventRuntime | None = None,
) -> ReadPostingSlot:
    """One cell's sheet: the fits free then, the free courts, and what is
    already happening there (#546)."""
    return ReadPostingSlot(
        posting=build_read_posting(session, booked=booked, runtime=runtime),
        forecasts=build_balance_forecasts(session, runtime=runtime),
        people=build_deck_people(session, settings=settings, runtime=runtime),
        clubs=build_proposal_club_names(session),
        distances=build_club_distances(session, runtime=runtime),
        relations=build_reader_relations(session, runtime=runtime),
        clock=clock,
    )


def build_post_a_game(
    session: AsyncSession,
    *,
    clock: Clock,
    booked: BookedGames | None = None,
    runtime: EventRuntime | None = None,
) -> PostAGame:
    """*Post — you're In* — the phone's, a seed's (#546): the post made and
    dealt through the dealer's own act, weighed by the live ruleset."""
    return PostAGame(
        posting=build_read_posting(session, booked=booked, runtime=runtime),
        guards=build_proposal_guards(session, runtime=runtime),
        directory=build_proposal_directory(session),
        make=build_make_proposal(session, clock=clock, runtime=runtime),
        balance=build_ruleset().balance,
        clock=clock,
    )


def build_read_friends_line_up(
    session: AsyncSession,
    *,
    booked: BookedGames | None = None,
    runtime: EventRuntime | None = None,
) -> ReadFriendsLineUp:
    """A fixed line-up on a group's Friends tab, read once (#750): the reader's
    friends, the line-up as the proposer reads its people, the pair rule's
    block mask, and every court the pool's court source offers. ``booked`` as
    the deck's."""
    return ReadFriendsLineUp(
        pools=build_pools(session),
        relations=build_reader_relations(session, runtime=runtime),
        members=build_read_members(session, booked=booked, runtime=runtime),
        fit=build_player_fit(session, runtime=runtime),
        where=build_where_pools_play(session, runtime=runtime),
        court_hours=build_court_hours(session, runtime=runtime),
    )


def build_read_friends_card(
    session: AsyncSession,
    *,
    clock: Clock,
    booked: BookedGames | None = None,
    runtime: EventRuntime | None = None,
) -> ReadFriendsCard:
    """The friends card (#750): the line-up's sides by the engine's own
    forecast, its weeks' overlap and a court — a read, recording nothing."""
    return ReadFriendsCard(
        line_up=build_read_friends_line_up(session, booked=booked, runtime=runtime),
        forecasts=build_balance_forecasts(session, runtime=runtime),
        clubs=build_proposal_club_names(session),
        terms=build_club_terms(session, runtime=runtime),
        clock=clock,
    )


def build_read_friends_courts(
    session: AsyncSession,
    *,
    clock: Clock,
    booked: BookedGames | None = None,
    runtime: EventRuntime | None = None,
) -> ReadFriendsCourts:
    """*Find a court* for a line-up (#750): every court it could take."""
    return ReadFriendsCourts(
        line_up=build_read_friends_line_up(session, booked=booked, runtime=runtime),
        clubs=build_proposal_club_names(session),
        clock=clock,
    )


# --------------------------------------------------------------------------
# A friends game (docs/adr/0202 §5–§6; #751)
# --------------------------------------------------------------------------


def build_friends_game_bookings(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> FriendsGameBookings:
    """A friends game booked at send, its invited seats answered, the sender's
    call-off — over the Bookings context's own use cases, every act after the
    booking's row is locked."""
    bookings = build_booking_repository(
        session,
        event_store=build_domain_event_store(session, runtime=runtime),
        events=build_event_publisher(session, runtime=runtime),
    )
    return BookingsFriendsGameBookings(
        games=FriendsGames(
            bookings=bookings,
            opening=build_game_opening(session, runtime=runtime),
            games=build_game_changes(session, runtime=runtime),
        ),
        bookings=bookings,
        directory=build_booking_directory(session),
    )


def build_senders_courts(
    session: AsyncSession,
    *,
    provider: PaymentProvider,
    settings: Settings,
    runtime: EventRuntime | None = None,
) -> SendersCourts:
    """The whole court on a friends game's sender's card, all or nothing, over
    ``provider`` — the sender's share and a cover per other seat — and the
    most they agreed to recorded with their terms (#751)."""
    return PaymentsSendersCourts(
        HoldTheCourt(
            methods=build_payment_method_repository(
                session,
                event_store=build_domain_event_store(session, runtime=runtime),
                events=build_event_publisher(session, runtime=runtime),
            ),
            charges=_seat_charge_repository(session, runtime),
            sellers=build_sellers(session, runtime=runtime),
            payers=build_payers(session),
            provider=provider,
            mail=build_mail_queue(session),
            app_link=f"{settings.APP_SCHEME}://",
        )
    )


def build_covers_at_the_cut_off(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> CoversAtTheCutOff:
    """Each cover taken or let go at a friends game's cut-off (#751) — asks
    nothing of the provider."""
    return PaymentsCoversAtTheCutOff(
        SettleTheCovers(charges=_seat_charge_repository(session, runtime))
    )


def _the_fill_of_a_friends_game(
    session: AsyncSession,
    *,
    provider: PaymentProvider,
    settings: Settings,
    runtime: EventRuntime | None,
) -> Fill:
    """The fill's own *other yeses*, for a friends game's sender and each
    friend who accepts: every other yes at the hour withdrawn, a full week
    paused."""
    return build_fill(
        session,
        proposals=build_proposal_repository(
            session,
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
        provider=provider,
        settings=settings,
        runtime=runtime,
    )


def build_send_a_friends_game(
    session: AsyncSession,
    *,
    clock: Clock,
    provider: PaymentProvider,
    settings: Settings,
    booked: BookedGames | None = None,
    runtime: EventRuntime | None = None,
) -> SendAFriendsGame:
    """*Send game and pay* (#751): the line-up read as the card reads it, the
    court held on the sender's card over ``provider``, then booked. ``booked``
    as the card's."""
    return SendAFriendsGame(
        line_up=build_read_friends_line_up(session, booked=booked, runtime=runtime),
        forecasts=build_balance_forecasts(session, runtime=runtime),
        terms=build_club_terms(session, runtime=runtime),
        methods=build_saved_methods(
            session,
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
        friends_games=build_friends_game_bookings(session, runtime=runtime),
        bookings=build_player_bookings(session, runtime=runtime),
        courts=build_senders_courts(
            session, provider=provider, settings=settings, runtime=runtime
        ),
        fill=_the_fill_of_a_friends_game(
            session, provider=provider, settings=settings, runtime=runtime
        ),
        uow=build_unit_of_work(session),
        clock=clock,
    )


def build_accepting(
    session: AsyncSession,
    *,
    provider: PaymentProvider,
    settings: Settings,
    booked: BookedGames | None = None,
    runtime: EventRuntime | None = None,
) -> Accepting:
    """An invited friend's accept itself (#751) — their own share held over
    ``provider`` with *Split the cost* — on a game its caller locked."""
    return Accepting(
        friends_games=build_friends_game_bookings(session, runtime=runtime),
        members=build_read_members(session, booked=booked, runtime=runtime),
        methods=build_saved_methods(
            session,
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
        charges=build_seat_charges(
            session, provider=provider, settings=settings, runtime=runtime
        ),
        refunds=build_seat_refunds(session, settings=settings, runtime=runtime),
        undecided=build_undecided_charges(session, runtime=runtime),
        fill=_the_fill_of_a_friends_game(
            session, provider=provider, settings=settings, runtime=runtime
        ),
    )


def build_accept_a_friends_game(
    session: AsyncSession,
    *,
    clock: Clock,
    provider: PaymentProvider,
    settings: Settings,
    booked: BookedGames | None = None,
    runtime: EventRuntime | None = None,
) -> AcceptAFriendsGame:
    """*Accept and pay 25 zł* on a FRIENDS GAME card (#751)."""
    return AcceptAFriendsGame(
        accepting=build_accepting(
            session,
            provider=provider,
            settings=settings,
            booked=booked,
            runtime=runtime,
        ),
        uow=build_unit_of_work(session),
        clock=clock,
    )


def build_decline_a_friends_game(
    session: AsyncSession,
    *,
    clock: Clock,
    runtime: EventRuntime | None = None,
) -> DeclineAFriendsGame:
    """*Not this time* on a FRIENDS GAME card (#751)."""
    return DeclineAFriendsGame(
        friends_games=build_friends_game_bookings(session, runtime=runtime),
        undecided=build_undecided_charges(session, runtime=runtime),
        uow=build_unit_of_work(session),
        clock=clock,
    )


def build_friends_game_confirmation(
    session: AsyncSession,
    *,
    provider: PaymentProvider,
    settings: Settings,
    runtime: EventRuntime | None = None,
) -> FriendsGameConfirmation:
    """A payment confirmed in the app on a friends game (#751) — the send's,
    an accept's again, or a rescuer's join on a seat open to the group (#752)
    — for ``ConfirmPayment``."""
    return FriendsGameConfirmation(
        friends_games=build_friends_game_bookings(session, runtime=runtime),
        accepting=build_accepting(
            session, provider=provider, settings=settings, runtime=runtime
        ),
        rescuer=build_rescuer(
            session,
            proposals=build_proposal_repository(
                session,
                event_store=build_domain_event_store(session, runtime=runtime),
                events=build_event_publisher(session, runtime=runtime),
            ),
            provider=provider,
            settings=settings,
            runtime=runtime,
        ),
        cards=build_cards_to_fix(session, runtime=runtime),
        games=build_booked_game_changes(session, settings=settings, runtime=runtime),
        undecided=build_undecided_charges(session, runtime=runtime),
        uow=build_unit_of_work(session),
    )


def build_call_off_a_friends_game(
    session: AsyncSession,
    *,
    clock: Clock,
    settings: Settings,
    runtime: EventRuntime | None = None,
) -> CallOffAFriendsGame:
    """The sender's *Call it off*, before the cut-off (#751): every hold and
    cover let go."""
    return CallOffAFriendsGame(
        friends_games=build_friends_game_bookings(session, runtime=runtime),
        refunds=build_seat_refunds(session, settings=settings, runtime=runtime),
        undecided=build_undecided_charges(session, runtime=runtime),
        uow=build_unit_of_work(session),
        clock=clock,
    )


def build_run_out_the_invitations(
    session: AsyncSession,
    *,
    clock: Clock,
    runtime: EventRuntime | None = None,
) -> RunOutTheInvitations:
    """One run of the invitations job over this session — the job's, the
    console's and a test's (#751)."""
    return RunOutTheInvitations(
        friends_games=build_friends_game_bookings(session, runtime=runtime),
        undecided=build_undecided_charges(session, runtime=runtime),
        uow=build_unit_of_work(session),
        clock=clock,
    )


def build_invite_into_a_seat(
    session: AsyncSession,
    *,
    clock: Clock,
    booked: BookedGames | None = None,
    runtime: EventRuntime | None = None,
) -> InviteIntoASeat:
    """*Invite a friend* into a friends game's empty seat (#752)."""
    return InviteIntoASeat(
        friends_games=build_friends_game_bookings(session, runtime=runtime),
        relations=build_reader_relations(session, runtime=runtime),
        members=build_read_members(session, booked=booked, runtime=runtime),
        fit=build_player_fit(session, runtime=runtime),
        uow=build_unit_of_work(session),
        clock=clock,
    )


def build_open_a_seat(
    session: AsyncSession, *, clock: Clock, runtime: EventRuntime | None = None
) -> OpenASeat:
    """The sender's *Open to the group*, before the cut-off (#752)."""
    return OpenASeat(
        friends_games=build_friends_game_bookings(session, runtime=runtime),
        uow=build_unit_of_work(session),
        clock=clock,
    )


def build_warn_the_covers(
    session: AsyncSession, *, clock: Clock, runtime: EventRuntime | None = None
) -> WarnTheCovers:
    """One run of the cover warning over this session — the job's, the
    console's and a test's (#752)."""
    return WarnTheCovers(
        friends_games=build_friends_game_bookings(session, runtime=runtime),
        uow=build_unit_of_work(session),
        clock=clock,
    )


# --------------------------------------------------------------------------
# Bookings (docs/adr/0189 §5; #541)
# --------------------------------------------------------------------------


def build_booking_repository(
    session: AsyncSession,
    *,
    event_store: DomainEventStore,
    events: DomainEventPublisher,
) -> BookingRepository:
    """One stream per filled proposal. Takes the session as well, because its
    ``save`` writes the bookings and booking-seats projections beside it."""
    return EventSourcedBookingRepository(
        session=session, event_store=event_store, events=events
    )


def build_summary_repository(
    *, event_store: DomainEventStore, events: DomainEventPublisher
) -> SummaryRepository:
    """One stream per club per day of new bookings, summed up once (#548)."""
    return EventSourcedSummaryRepository(event_store=event_store, events=events)


def build_summarise_new_bookings(
    session: AsyncSession,
    *,
    clock: Clock,
    settings: Settings,
    runtime: EventRuntime | None = None,
) -> SummariseNewBookings:
    """One run of the club's daily summary of new bookings over this session —
    the job's, and a test's (#548). Its email opens the Bookings page."""
    event_store = build_domain_event_store(session, runtime=runtime)
    events = build_event_publisher(session, runtime=runtime)
    return SummariseNewBookings(
        bookings=build_booking_repository(
            session, event_store=event_store, events=events
        ),
        directory=build_booking_directory(session),
        summaries=build_summary_repository(event_store=event_store, events=events),
        desks=build_club_desks(session, runtime=runtime),
        mail=build_mail_queue(session),
        uow=build_unit_of_work(session),
        clock=clock,
        bookings_page=f"{settings.CLUB_WEBSITE_URL.rstrip('/')}/bookings",
    )


def build_booking_directory(session: AsyncSession) -> BookingDirectory:
    return SqlAlchemyBookingDirectory(session)


def build_player_bookings(
    session: AsyncSession,
    *,
    runtime: EventRuntime | None = None,
    event_store: DomainEventStore | None = None,
) -> PlayerBookings:
    """A player's booked games, folded from each booking's stream — Home's and
    the details' (#542). ``event_store`` as ``_own_or`` reads it."""
    return BookingsPlayerBookings(
        directory=build_booking_directory(session),
        bookings=build_booking_repository(
            session,
            event_store=_own_or(event_store, session, runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
    )


def build_game_results(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> GameResults:
    """Where a booked game's ordinary Game stands, off its own aggregate — and
    which games had a score put on their table lately (#613)."""
    return GamesGameResults(
        build_game_repository(
            session=session,
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
        build_scored_games(session),
    )


def build_club_distances(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> ClubDistances:
    """How far a club is from a player's Location area, printed as every
    distance on the platform is."""
    return ProfileClubDistances(
        profiles=build_player_profile_repository(
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
        clubs=build_club_directory(session),
    )


def build_read_home(
    session: AsyncSession,
    *,
    settings: Settings,
    clock: Clock,
    orders: GeneralOrders,
    runtime: EventRuntime | None = None,
) -> ReadHome:
    """Home: the reader's booked games and the ones that need them (#542) —
    and the trophy, read off the kept General order (#770)."""
    return ReadHome(
        bookings=build_player_bookings(session, runtime=runtime),
        results=build_game_results(session, runtime=runtime),
        proposals=build_proposal_repository(
            session,
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
        directory=build_proposal_directory(session),
        people=build_deck_people(session, settings=settings, runtime=runtime),
        clubs=build_proposal_club_names(session),
        games=build_booked_game_changes(session, settings=settings, runtime=runtime),
        holding_times=build_holding_times(session, runtime=runtime),
        relations=build_reader_relations(session, runtime=runtime),
        friend_requests=build_friend_requests_on_home(
            session, settings=settings, clock=clock, runtime=runtime
        ),
        level_asks=build_level_asks_on_home(
            session, settings=settings, runtime=runtime
        ),
        ranking=build_ranking_on_home(session, clock=clock, orders=orders),
        friends_games=build_friends_game_bookings(session, runtime=runtime),
        clock=clock,
    )


def build_friend_requests_on_home(
    session: AsyncSession,
    *,
    settings: Settings,
    clock: Clock,
    runtime: EventRuntime | None = None,
) -> FriendRequestsOnHome:
    """Home's *FRIEND REQUESTS* — Friends' read, signed in
    ``proposals/infrastructure/`` (``docs/adr/0202`` §1)."""
    return FriendsRequestsOnHome(
        build_read_requests_on_home(
            session, settings=settings, clock=clock, runtime=runtime
        )
    )


def build_level_asks_on_home(
    session: AsyncSession,
    *,
    settings: Settings,
    runtime: EventRuntime | None = None,
) -> LevelAsksOnHome:
    """Home's *ASKED FOR A LEVEL* — Friends' read, signed in
    ``proposals/infrastructure/`` (``docs/adr/0202`` §4's 2026-11-07
    amendment, #764)."""
    return FriendsLevelAsksOnHome(
        build_read_level_asks_on_home(session, settings=settings, runtime=runtime)
    )


def build_reader_relations(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> ReaderRelations:
    """The *friend* tag on every face a proposals read draws, and the result's
    *PLAYED WITH* pills — Friends' read, signed in
    ``proposals/infrastructure/`` (``docs/adr/0202`` §2)."""
    return FriendsReaderRelations(build_read_relations(session, runtime=runtime))


def build_read_payments_to_confirm(
    session: AsyncSession,
    *,
    settings: Settings,
    clock: Clock,
    runtime: EventRuntime | None = None,
) -> ReadPaymentsToConfirm:
    """The reader's payments to confirm: games still filling whose share was
    refused, and booked games whose holding was (#639)."""
    return ReadPaymentsToConfirm(
        proposals=build_proposal_repository(
            session,
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
        directory=build_proposal_directory(session),
        bookings=build_player_bookings(session, runtime=runtime),
        games=build_booked_game_changes(session, settings=settings, runtime=runtime),
        clubs=build_proposal_club_names(session),
        clock=clock,
    )


def build_read_booking_details(
    session: AsyncSession,
    *,
    settings: Settings,
    clock: Clock,
    runtime: EventRuntime | None = None,
) -> ReadBookingDetails:
    """A booked game's details, for a player in it (#542)."""
    return ReadBookingDetails(
        bookings=build_player_bookings(session, runtime=runtime),
        proposals=build_proposal_repository(
            session,
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
        results=build_game_results(session, runtime=runtime),
        people=build_deck_people(session, settings=settings, runtime=runtime),
        clubs=build_proposal_club_names(session),
        distances=build_club_distances(session, runtime=runtime),
        late_refunds=build_late_refunds(session, runtime=runtime),
        offers=build_rescue_offers(session, runtime=runtime),
        holding_times=build_holding_times(session, runtime=runtime),
        relations=build_reader_relations(session, runtime=runtime),
        clock=clock,
    )


def build_read_proposal_details(
    session: AsyncSession,
    *,
    settings: Settings,
    clock: Clock,
    runtime: EventRuntime | None = None,
) -> ReadProposalDetails:
    """A game still filling, for anybody dealt it (#542)."""
    return ReadProposalDetails(
        pools=build_pools(session),
        proposals=build_proposal_repository(
            session,
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
        fit=build_player_fit(session, runtime=runtime),
        forecasts=build_balance_forecasts(session, runtime=runtime),
        people=build_deck_people(session, settings=settings, runtime=runtime),
        terms=build_club_terms(session, runtime=runtime),
        kinds=build_court_kinds(session, runtime=runtime),
        clubs=build_proposal_club_names(session),
        distances=build_club_distances(session, runtime=runtime),
        players=build_players_in_play(session, runtime=runtime),
        wanted=build_wanted_kinds(session, runtime=runtime),
        relations=build_reader_relations(session, runtime=runtime),
        clock=clock,
    )


def build_club_courts_at_the_hour(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> ClubCourtsAtTheHour:
    """The courts a club still has for Raketa at an hour, off what the Club
    context publishes it sells."""
    return SellableClubCourts(build_sellable_court_hours(session, runtime=runtime))


def build_court_closures(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> CourtClosures:
    """The court a club's cancel took a game off, closed for the hour (#673)
    through the Club context's own act — in the cancel's transaction."""
    return ClosedByTheCancel(
        CloseACourtForAnHour(
            courts=build_club_courts_repository(
                session,
                event_store=build_domain_event_store(session, runtime=runtime),
                events=build_event_publisher(session, runtime=runtime),
            )
        )
    )


def build_game_opening(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> GameOpening:
    """The ordinary Game a booking opens, through the Games context's own
    opening — in the fill's transaction."""
    return OpenTheGame(
        OpenPlannedGame(
            games=build_game_repository(
                session=session,
                event_store=build_domain_event_store(session, runtime=runtime),
                events=build_event_publisher(session, runtime=runtime),
            )
        )
    )


def build_game_changes(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> GameChanges:
    """What leaving, a rescue and the cut-off do to a booked game's ordinary
    Game — the Games context's own departure, re-seat and call-off (#544,
    #545)."""
    games = build_game_repository(
        session=session,
        event_store=build_domain_event_store(session, runtime=runtime),
        events=build_event_publisher(session, runtime=runtime),
    )
    return LeaveAndCallOffTheGame(
        vacate=VacateSeat(games=games),
        seat=TakeASeat(games=games),
        call_off=CallOffGame(games=games),
        call_off_whole=CallOffTheWholeGame(games=games),
    )


def build_find_a_court(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> FindACourt:
    """The first free court of a full game's sport at its hour."""
    return FindACourt(courts=build_club_courts_at_the_hour(session, runtime=runtime))


def build_book_the_game(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> BookTheGame:
    """The booking, and the ordinary Game it opens — in the fill's
    transaction."""
    return BookTheGame(
        bookings=build_booking_repository(
            session,
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
        games=build_game_opening(session, runtime=runtime),
    )


# --------------------------------------------------------------------------
# Administrators (docs/adr/0184)
# --------------------------------------------------------------------------


def build_administrator_repository(
    session: AsyncSession,
    *,
    event_store: DomainEventStore,
    events: DomainEventPublisher,
) -> AdministratorRepository:
    """Per unit of work, as every aggregate repository is. **It takes the
    session as well as the store**, because its ``save`` writes the
    ``administrators`` row in the same transaction."""
    return EventSourcedAdministratorRepository(
        session=session, event_store=event_store, events=events
    )


def build_administrator_directory(session: AsyncSession) -> AdministratorDirectory:
    return SqlAlchemyAdministratorDirectory(session)


def build_account_holders(
    session: AsyncSession,
    *,
    event_store: DomainEventStore,
    events: DomainEventPublisher,
) -> AccountHolders:
    """The Users behind administratorships: written by ``users`` on its own
    stream — an account opened or cleared by ``InvitationAccounts``, a password
    set by the same ``PasswordAccounts`` *Forgot password?* uses — and *acts as
    a player* read off that stream and the Player profile's."""
    return UsersAccountHolders(
        accounts=InvitationAccounts(
            users=build_user_repository(session),
            event_store=event_store,
            events=events,
        ),
        passwords=build_user_password_accounts(
            session, event_store=event_store, events=events
        ),
        profiles=HasPlayerProfile(
            profiles=build_player_profile_repository(
                event_store=event_store, events=events
            )
        ),
    )


def build_club_names(session: AsyncSession) -> ClubNames:
    """A club's name, off the clubs' published directory."""
    return ClubsClubNames(build_club_directory(session))


def build_official_group_assignments(
    session: AsyncSession,
) -> OfficialGroupAssignments:
    """Which official groups each Administrator was given — the Administrators
    table's *groups* column — answered by the Groups context over its own
    directory, so the arrow runs ``groups → administrators`` only (#510)."""
    return GroupsOfficialGroupAssignments(build_group_directory(session))


def build_invitation_sender(
    session: AsyncSession,
    settings: Settings,
    *,
    accounts: AccountHolders,
    credentials: OneTimeCredentials,
) -> InvitationSender:
    """Where every invitation email is decided and queued — the invite, a
    resend and the club's reset. Its buttons go to the public site's
    ``/invite/<token>`` for somebody with a password to set, and to the app
    for an account that only has to accept; both addresses are settings
    (``docs/adr/0187`` §7). ``credentials`` is the caller's, so a request and a
    seed run issue through the mechanism they already hold."""
    return InvitationSender(
        accounts=accounts,
        credentials=credentials,
        mail=build_mail_queue(session),
        clubs=build_club_names(session),
        links=InvitationLinks(
            site=settings.PUBLIC_SITE_URL, app_scheme=settings.APP_SCHEME
        ),
    )


# --------------------------------------------------------------------------
# Groups
# --------------------------------------------------------------------------


def build_group_repository(
    session: AsyncSession,
    *,
    event_store: DomainEventStore,
    events: DomainEventPublisher,
) -> GroupRepository:
    """Per unit of work, as every aggregate repository is. **It takes the session
    as well as the store**, because its ``save`` writes the groups and
    group-members projections in the same transaction (``docs/adr/0183`` §1)."""
    return EventSourcedGroupRepository(
        session=session, event_store=event_store, events=events
    )


def build_group_directory(session: AsyncSession) -> GroupDirectory:
    return SqlAlchemyGroupDirectory(session)


def build_group_code_minter(session: AsyncSession) -> GroupCodeMinter:
    return RandomGroupCodes(session)


def build_home_clubs(session: AsyncSession) -> HomeClubs:
    """A group's home club, and the clubs a player searches — over the clubs'
    own published directory, never their table."""
    return ClubsHomeClubs(build_club_directory(session))


def build_rated_group_members(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> RatedGroupMembers:
    """The sport dots' ratings, over the rating context's published read — which
    replays and remembers nothing, so a dot cannot move a Level."""
    return RatingsRatedGroupMembers(build_rated_player_query(session, runtime=runtime))


def build_group_faces(
    session: AsyncSession,
    *,
    settings: Settings,
    runtime: EventRuntime | None = None,
) -> GroupFaces:
    """A name from ``users``, a face from the Player profile, a link from the
    store — ``build_member_faces``' three providers, for the Games tab's seats,
    a Join request's asker and, name only, a group's Owner. The window is the
    platform's one photo window."""
    return ProfileGroupFaces(
        users=build_user_repository(session),
        profiles=build_player_profile_repository(
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
        photos=build_photo_storage(settings),
        photo_link_minutes=settings.PHOTO_URL_VALID_FOR_MINUTES,
    )


def build_group_member_reliability(session: AsyncSession) -> GroupMemberReliability:
    """A Members row's *92 Very high*, over ``player_score``'s published read —
    the figure and band a player's record prints, copied and never re-derived."""
    return PublishedGroupMemberReliability(build_published_score_query(session))


def build_group_administrators(session: AsyncSession) -> GroupAdministrators:
    """Who runs each official group now: the account behind its Administrator,
    read off the administrators' own directory while that administratorship is
    active — so a removal takes a group from its administrator on the next read
    (``docs/adr/0184`` §7)."""
    return AdministratorsGroupAdministrators(build_administrator_directory(session))


def build_group_born_games(session: AsyncSession) -> GroupBornGames:
    """The club's *Games* figure: the games booked in each group
    (``docs/adr/0183`` §11 as ``docs/adr/0189`` §8 amends it) — the bookings in
    its pool, which is filed under the group's own id (#542)."""
    return BookingsGroupBornGames(build_booking_directory(session))


def build_reader_areas(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> ReaderAreas:
    """Where the reader is, read off their Player profile's Location area."""
    return ProfileReaderAreas(
        build_player_profile_repository(
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        )
    )


# --------------------------------------------------------------------------
# Users
# --------------------------------------------------------------------------


def build_user_repository(session: AsyncSession) -> UserRepository:
    return SqlAlchemyUserRepository(session)


def build_user_session_holders(session: AsyncSession) -> SessionHolders:
    """Who may renew a **player-app** session: an active User
    (``docs/adr/0185`` §6)."""
    return UserSessionHolders(build_user_repository(session))


def build_user_password_accounts(
    session: AsyncSession,
    *,
    event_store: DomainEventStore,
    events: DomainEventPublisher,
) -> PasswordAccounts:
    """Whose password a **player-app** reset recovers: an active User's
    (``docs/adr/0184`` §5), changed on the User's own stream."""
    return UserPasswordAccounts(
        users=build_user_repository(session), event_store=event_store, events=events
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

    Over the **log**, because ``docs/adr/0095`` §4 dropped the advisory copy, so
    there is no projection to choose between. It takes the codec from the event
    runtime rather than declaring the durable names a second time — a
    re-declared published contract drifts silently.

    One line, so every route onto a court (``PlayerFit``), *Blocked players* and
    the record's *you blocked them* read a block from the same place
    (``docs/adr/0193``).
    """
    return EventSourcedBlockQuery(session, (runtime or get_event_runtime()).codec)


def build_blocked_faces(
    session: AsyncSession,
    *,
    settings: Settings,
    runtime: EventRuntime | None = None,
) -> BlockedFaces:
    """*Blocked players*' faces — a name from ``users``, a face from the Player
    profile, a link from the store: ``build_group_faces``' three providers. The
    window is the platform's one photo window."""
    return ProfileBlockedFaces(
        users=build_user_repository(session),
        profiles=build_player_profile_repository(
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
        photos=build_photo_storage(settings),
        photo_link_minutes=settings.PHOTO_URL_VALID_FOR_MINUTES,
    )


# --------------------------------------------------------------------------
# Friends
# --------------------------------------------------------------------------


def build_friendship_repository(
    session: AsyncSession,
    *,
    event_store: DomainEventStore,
    events: DomainEventPublisher,
) -> FriendshipRepository:
    """Per unit of work, as every aggregate repository is. **It takes the session
    as well as the store**, because its ``save`` rewrites the pair's
    ``friend_relations`` rows in the same transaction (``docs/adr/0202`` §8)."""
    return EventSourcedFriendshipRepository(
        session=session, event_store=event_store, events=events
    )


def build_friendship_directory(session: AsyncSession) -> FriendshipDirectory:
    return SqlAlchemyFriendshipDirectory(session)


def build_readers_blocks(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> ReadersBlocks:
    """Whom the reader blocked — over the one directed read ``BlockQuery`` has,
    so a blocked player's request is hidden from the blocker alone
    (``docs/adr/0202`` §2)."""
    return OwnBlocks(build_block_query(session, runtime=runtime))


def build_readers_groups(session: AsyncSession) -> ReadersGroups:
    """The reader's groups and their members, **signed in
    ``groups/infrastructure/``** over the groups' own directory, so the arrow runs
    ``groups → friends``."""
    return DirectoryReadersGroups(build_group_directory(session))


def build_friend_faces(
    session: AsyncSession,
    *,
    settings: Settings,
    runtime: EventRuntime | None = None,
) -> FriendFaces:
    """A name from ``users``, a face from the Player profile, a link from the
    store — ``build_blocked_faces``' three providers."""
    return ProfileFriendFaces(
        users=build_user_repository(session),
        profiles=build_player_profile_repository(
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
        photos=build_photo_storage(settings),
        photo_link_minutes=settings.PHOTO_URL_VALID_FOR_MINUTES,
    )


def build_friend_levels(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> FriendLevels:
    return RatedFriendLevels(build_rated_player_query(session, runtime=runtime))


def build_friend_reliabilities(session: AsyncSession) -> FriendReliabilities:
    return PublishedFriendReliability(build_published_score_query(session))


def build_read_relations(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> ReadRelations:
    """**The reader's relations, the one read every face is lent**
    (``docs/adr/0202`` §2): Members, the record, the deck, the details, Home,
    Fill in and the result all ask it, each through a port of its own."""
    return ReadRelations(
        directory=build_friendship_directory(session),
        blocks=build_readers_blocks(session, runtime=runtime),
    )


def build_ask_to_be_friends(
    session: AsyncSession, *, clock: Clock, runtime: EventRuntime | None = None
) -> AskToBeFriends:
    """Asking, built over one session for a seed run and a test as the route
    builds it per request."""
    return AskToBeFriends(
        friendships=build_friendship_repository(
            session,
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
        blocks=build_readers_blocks(session, runtime=runtime),
        groups=build_readers_groups(session),
        uow=build_unit_of_work(session),
        clock=clock,
    )


def build_accept_friend_request(
    session: AsyncSession, *, clock: Clock, runtime: EventRuntime | None = None
) -> AcceptFriendRequest:
    return AcceptFriendRequest(
        friendships=build_friendship_repository(
            session,
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
        blocks=build_readers_blocks(session, runtime=runtime),
        uow=build_unit_of_work(session),
        clock=clock,
    )


def build_set_aside_friend_request(
    session: AsyncSession, *, clock: Clock, runtime: EventRuntime | None = None
) -> SetAsideFriendRequest:
    return SetAsideFriendRequest(
        friendships=build_friendship_repository(
            session,
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
        blocks=build_readers_blocks(session, runtime=runtime),
        uow=build_unit_of_work(session),
        clock=clock,
    )


def build_read_requests_on_home(
    session: AsyncSession,
    *,
    settings: Settings,
    clock: Clock,
    runtime: EventRuntime | None = None,
) -> ReadRequestsOnHome:
    """Home's *FRIEND REQUESTS*, and what the bell asks to clear a request's
    row once its card is gone."""
    return ReadRequestsOnHome(
        directory=build_friendship_directory(session),
        blocks=build_readers_blocks(session, runtime=runtime),
        faces=build_friend_faces(session, settings=settings, runtime=runtime),
        levels=build_friend_levels(session, runtime=runtime),
        reliability=build_friend_reliabilities(session),
        groups=build_readers_groups(session),
        clock=clock,
    )


def build_friend_link_repository(
    session: AsyncSession,
    *,
    event_store: DomainEventStore,
    events: DomainEventPublisher,
) -> FriendLinkRepository:
    """Per unit of work. **It takes the session as well as the store**, because
    its ``save`` writes the codes a link carried to ``friend_link_codes`` in the
    same transaction (#748)."""
    return EventSourcedFriendLinkRepository(
        session=session, event_store=event_store, events=events
    )


def build_friend_link_codes(session: AsyncSession) -> FriendLinkCodes:
    return RandomFriendLinkCodes(session)


def build_read_your_friend_link(
    session: AsyncSession, *, clock: Clock, runtime: EventRuntime | None = None
) -> ReadYourFriendLink:
    """The reader's link, made on their first read — built over one session for
    a seed run as the route builds it per request."""
    return ReadYourFriendLink(
        links=build_friend_link_repository(
            session,
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
        codes=build_friend_link_codes(session),
        uow=build_unit_of_work(session),
        clock=clock,
    )


def build_end_friendships_on_a_block(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> EndFriendshipsOnABlock:
    """A block ends a friendship — built per delivery run, over the session the
    delivery commits in."""
    return EndFriendshipsOnABlock(
        build_friendship_repository(
            session,
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        )
    )


def build_levels_asked_by_the_reader(session: AsyncSession) -> LevelsAskedByTheReader:
    """The sports the reader asked each friend for, ``friend_level_asks``, from
    the reader's side — the picker's *Asked* (#749)."""
    return SqlAlchemyLevelAskDirectory(session)


def build_level_asks_of_the_reader(session: AsyncSession) -> LevelAsksOfTheReader:
    """The asks made **of** the reader, waiting and not set aside, from the
    reader's side — for their Home, their bell and their *Not now* (#764)."""
    return SqlAlchemyLevelAskDirectory(session)


def build_read_level_asks_waiting(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> ReadLevelAsksWaiting:
    """Whose asks for a level wait on the reader's Home, and in which sport —
    what the bell keeps a *level asked* row by, and what *Not now* sets aside
    (#764)."""
    return ReadLevelAsksWaiting(
        asks=build_level_asks_of_the_reader(session),
        directory=build_friendship_directory(session),
        blocks=build_readers_blocks(session, runtime=runtime),
        levels=build_friend_levels(session, runtime=runtime),
    )


def build_read_level_asks_on_home(
    session: AsyncSession,
    *,
    settings: Settings,
    runtime: EventRuntime | None = None,
) -> ReadLevelAsksOnHome:
    """Home's *ASKED FOR A LEVEL*, one card per sport, each asker's face
    (#764)."""
    return ReadLevelAsksOnHome(
        waiting=build_read_level_asks_waiting(session, runtime=runtime),
        faces=build_friend_faces(session, settings=settings, runtime=runtime),
    )


def build_asks_waiting_on_a_level(session: AsyncSession) -> AsksWaitingOnALevel:
    """Who is waiting on a friend's level — **handed to the answerer alone**: it
    names who asked somebody else (#749)."""
    return SqlAlchemyLevelAskDirectory(session)


def build_answer_the_asks_for_a_level(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> AnswerTheAsksForALevel:
    """A friend's level answers every ask for it — built per delivery run, over
    the session the delivery commits in (#749)."""
    return AnswerTheAsksForALevel(
        asks=build_asks_waiting_on_a_level(session),
        levels=build_friend_levels(session, runtime=runtime),
        friendships=build_friendship_repository(
            session,
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
    )


def build_ranking_rows(session: AsyncSession) -> RankingRows:
    """The ranking projection, ``ranking_rows`` (#768; ``docs/adr/0203`` §10)."""
    return SqlAlchemyRankingRows(session)


def build_level_history(session: AsyncSession) -> LevelHistory:
    """The level history the chip reads, ``ranking_level_history`` (#769;
    ``docs/adr/0203`` §4, §10)."""
    return SqlAlchemyLevelHistory(session)


def build_rating_histories(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> RatingHistories:
    """The rating's streams, which every ranking row is folded from."""
    return RatingStreamHistories(
        event_store=build_domain_event_store(session, runtime=runtime)
    )


def build_ranked_faces(
    session: AsyncSession,
    *,
    settings: Settings,
    runtime: EventRuntime | None = None,
) -> RankedFaces:
    """A name from ``users``, a face from the Player profile, a link from the
    store — ``build_friend_faces``' three providers."""
    return ProfileRankedFaces(
        users=build_user_repository(session),
        profiles=build_player_profile_repository(
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
        photos=build_photo_storage(settings),
        photo_link_minutes=settings.PHOTO_URL_VALID_FOR_MINUTES,
    )


def build_sport_levels(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> SportLevels:
    """Whether the reader holds a level in a sport, off rating's published
    read."""
    return RatedSportLevels(build_rated_player_query(session, runtime=runtime))


def build_general_orders(client: Redis | None) -> GeneralOrders:
    """Each sport's kept General order, in the ephemeral store — **wrapped,
    always** (#770): an order is a copy the projection can always make, so a
    store that is down holds nothing and keeps nothing, and a read works the
    order out instead. **Kept nowhere where the store never came up** — a
    request then works its order out, as a run with no store does."""
    if client is None:
        return build_general_orders_kept_here()
    return FailSoftGeneralOrders(RedisGeneralOrders(client))


def build_general_orders_kept_here() -> GeneralOrders:
    """Orders kept in this process's memory, **one store per call** — for a
    run with no ephemeral store of its own (a seed run's drain and its screen
    reads), and the in-memory equivalent every test reads through. An API
    process that holds an order after a seed shows it for at most its minute;
    the rebuild forgets the API's in Redis itself."""
    return InMemoryGeneralOrders()


def build_move_the_ranking(
    session: AsyncSession,
    *,
    orders: GeneralOrders,
    runtime: EventRuntime | None = None,
) -> MoveTheRanking:
    """A result's row folded again — built per delivery run, over the session
    the delivery commits in (#768) — and its sport's kept order forgotten in
    the store this run's readers read (#770)."""
    return MoveTheRanking(
        histories=build_rating_histories(session, runtime=runtime),
        rows=build_ranking_rows(session),
        level_history=build_level_history(session),
        orders=orders,
    )


def build_rebuild_the_rankings(
    session: AsyncSession,
    *,
    orders: GeneralOrders,
    runtime: EventRuntime | None = None,
) -> RebuildTheRankings:
    """Every row and level-history point folded from every rating stream, and
    every rated player's *Show me in General* followed — ``make
    rankings-rebuild``."""
    return RebuildTheRankings(
        histories=build_rating_histories(session, runtime=runtime),
        rows=build_ranking_rows(session),
        level_history=build_level_history(session),
        switches=build_general_switches(session, runtime=runtime),
        orders=orders,
        uow=build_unit_of_work(session),
    )


def build_general_switches(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> GeneralSwitches:
    """A player's *Show me in General*, off their profile — **signed in
    ``rankings/infrastructure/``**, so the arrow runs ``rankings →
    player_profile`` (#772)."""
    event_store = build_domain_event_store(session, runtime=runtime)
    return ProfileGeneralSwitches(
        profiles=build_player_profile_repository(
            event_store=event_store,
            events=build_event_publisher(session, runtime=runtime),
        ),
        event_store=event_store,
    )


def build_follow_the_switch(
    session: AsyncSession,
    *,
    orders: GeneralOrders,
    runtime: EventRuntime | None = None,
) -> FollowTheSwitch:
    """*Show me in General* turned, followed by the rows — built per delivery
    run, over the session the delivery commits in — and the kept order of
    every sport the player has a row in forgotten (#772)."""
    return FollowTheSwitch(
        switches=build_general_switches(session, runtime=runtime),
        rows=build_ranking_rows(session),
        orders=orders,
    )


def build_blocks_either_way(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> BlocksEitherWay:
    """Everybody a block stands between the reader and, either way — **signed
    in ``rankings/infrastructure/``** over the blocks' one query, so the arrow
    runs ``rankings → blocks`` (#772)."""
    return QueriedBlocksEitherWay(build_block_query(session, runtime=runtime))


def build_readers_friends(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> ReadersFriends:
    """The reader's friends now, **signed in ``rankings/infrastructure/``**
    over Friends' own read, so the arrow runs ``rankings → friends`` (#771)."""
    return FriendsReadersFriends(build_read_relations(session, runtime=runtime))


def build_the_friends_table(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> TheFriendsTable:
    """A reader's Friends table: worked out on each read, from one pass over
    the reader and their friends (#771)."""
    return TheFriendsTable(
        rows=build_ranking_rows(session),
        friends=build_readers_friends(session, runtime=runtime),
    )


def build_the_general_order(
    session: AsyncSession, *, orders: GeneralOrders
) -> TheGeneralOrder:
    """A sport's General order as a read finds it: the kept one while fresh,
    or worked out in one pass and kept (#770)."""
    return TheGeneralOrder(rows=build_ranking_rows(session), orders=orders)


def build_read_ranking(
    session: AsyncSession,
    *,
    settings: Settings,
    clock: Clock,
    orders: GeneralOrders,
    runtime: EventRuntime | None = None,
) -> ReadRanking:
    """``GET /rankings/{sport}``: the card, the podium and General's first
    page, or the whole Friends table."""
    return ReadRanking(
        general=build_the_general_order(session, orders=orders),
        friends=build_the_friends_table(session, runtime=runtime),
        faces=build_ranked_faces(session, settings=settings, runtime=runtime),
        levels=build_sport_levels(session, runtime=runtime),
        blocks=build_blocks_either_way(session, runtime=runtime),
        clock=clock,
    )


def build_read_general_page(
    session: AsyncSession,
    *,
    settings: Settings,
    clock: Clock,
    orders: GeneralOrders,
    runtime: EventRuntime | None = None,
) -> ReadGeneralPage:
    """``GET /rankings/{sport}/general/rows``: a page of General (#770)."""
    return ReadGeneralPage(
        general=build_the_general_order(session, orders=orders),
        faces=build_ranked_faces(session, settings=settings, runtime=runtime),
        blocks=build_blocks_either_way(session, runtime=runtime),
        clock=clock,
    )


def build_read_home_ranking(
    session: AsyncSession, *, clock: Clock, orders: GeneralOrders
) -> ReadHomeRanking:
    """Home's trophy: the sport of the latest result, and the General and
    Friends places there."""
    return ReadHomeRanking(
        rows=build_ranking_rows(session),
        general=build_the_general_order(session, orders=orders),
        friends=build_the_friends_table(session),
        clock=clock,
    )


def build_ranking_on_home(
    session: AsyncSession, *, clock: Clock, orders: GeneralOrders
) -> RankingOnHome:
    """Home's trophy — Rankings' read, signed in ``proposals/infrastructure/``
    (``docs/adr/0203`` §5)."""
    return RankingsOnHome(build_read_home_ranking(session, clock=clock, orders=orders))


def build_member_relations(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> MemberRelations:
    """Members' pills, **signed in ``groups/infrastructure/``** over Friends' read."""
    return FriendsMemberRelations(build_read_relations(session, runtime=runtime))


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
    the index has an event to read, while the write path — the rating tail and
    ``PUT /api/v1/play-intents/{sport}`` — is ADR-0094's own build. This line is
    what that build wires to rather than re-deciding, and it is one line so that
    the re-decision never happens somewhere else.
    """
    return EventSourcedPlayIntentDeclarationRepository(
        event_store=event_store, events=events
    )


# --------------------------------------------------------------------------
# Matchmaking — the three outward ports
# --------------------------------------------------------------------------
#
# ``docs/adr/0098``'s consumer-driven contracts, one line per port so the choice
# of implementation is made here rather than re-made wherever a reader is
# assembled: the two account gates the player record asks, and the at-stake read
# a booked game's pairing prints (``build_at_stake_query``, below with the
# games). Four more went with the searches (#579). The register in
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


def build_published_score_query(
    session: AsyncSession, *, event_store: DomainEventStore | None = None
) -> PublishedScoreQuery:
    """``player_score`` — Player reliability in points (#659) — over the two
    contexts that keep a record of anything: the games, and the bookings.

    It is built from the two providers' own published ports rather than from the
    session, so this line stays a choice of implementation and the folds behind
    it stay with the contexts that own them. ``event_store`` as ``_own_or``
    reads it.
    """
    return PointsFromTheRecord(
        games=build_game_history_query(session),
        bookings=build_booking_history(session, event_store=event_store),
    )


def build_booking_history(
    session: AsyncSession, *, event_store: DomainEventStore | None = None
) -> BookingHistoryQuery:
    """Who kept the booked games they held a seat on, and how the others were
    broken — folded off each booking's stream (#544, #659). ``event_store`` as
    ``_own_or`` reads it."""
    return EventSourcedBookingHistory(
        directory=build_booking_directory(session),
        bookings=build_booking_repository(
            session,
            event_store=_own_or(event_store, session, None),
            events=build_event_publisher(session),
        ),
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
    lookup by payload: *has this booking already opened a game*, which is what
    makes the opening idempotent inside the fill's own transaction.
    """
    return EventSourcedGameRepository(
        event_store=event_store, events=events, session=session
    )


def build_game_court_pairing(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> CourtPairing:
    """What the engine makes of a game's court, for the reader (``docs/adr/0161``).

    The one outward demand ``games`` makes of the matcher, **answered from the
    balance forecast directly** (#575): a booked game's court is read side
    against side from the people's Levels under the live ruleset — the reading
    a Games card makes of the same people (:func:`build_balance_forecasts`) —
    and from ``rating``'s published figures and result-update rule beside it.
    """

    return GamesCourtPairing(
        ratings=build_rated_player_query(session, runtime=runtime),
        ruleset=build_ruleset(),
        at_stake=build_at_stake_query(session, runtime=runtime),
    )


def build_game_clubs(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> GameClubs:
    """Where a booked game's club is, for an attendance tap to be measured
    against (#657; ``docs/adr/0195`` §3) — the Games context's demand, answered
    by Bookings off the booking's stream and the Club directory."""

    return BookedGameClubs(
        bookings=build_booking_repository(
            session,
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
        clubs=build_club_directory(session),
    )


def build_game_history_query(
    session: AsyncSession,
    *,
    runtime: EventRuntime | None = None,
) -> GameHistoryQuery:
    """What ``games`` owes the rest of the platform — over the log.

    Over the log rather than a projection: the standing is a fold of the record
    against a clock, and a stored one would be wrong for the whole gap between a
    deadline passing and anything noticing — with nothing to notice it, because
    this context has no sweep.
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

    One class answers both ports so a screen wanting the aggregates and a reader
    wanting the counts do not run the same substring match twice. They stay two
    ports: a caller that wants counts has no business holding the aggregates.
    """
    return EventSourcedGameHistory(session, (runtime or get_event_runtime()).codec)


def build_rated_player_query(
    session: AsyncSession,
    *,
    runtime: EventRuntime | None = None,
    event_store: DomainEventStore | None = None,
) -> RatedPlayerQuery:
    """Levels read and never held, over the rating streams.

    Narrower than ``build_skill_rating_repository`` on purpose: that one
    remembers stream versions so a rating it found can be saved, and a reader
    that only wants two floats has no business with the path that could move
    them. ``event_store`` is the deck read's shared one (#704); every other
    caller gets a store of its own.
    """
    return EventSourcedRatedPlayers(event_store=_own_or(event_store, session, runtime))


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
    life of one request and a longer-lived one would be a cache of numbers that
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
    of a port it already carries could call it inside a walk over hundreds of
    people. Typed narrowly here, it reaches only the surface that opens one
    person at a time.
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


def build_scored_games(session: AsyncSession) -> ScoredGames:
    """Which of some games had a score put on their table lately — ids over
    the stream index, nothing folded (#613): where Home looks, among games older
    than the hour it reads from, for a score a correction re-dated."""
    return EventSourcedScoredGames(session)


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
    narrow type is what stops it being reachable from a caller that walks a
    list of people.
    """

    return GamesSubjectVariety(
        build_opponent_variety_query(session, runtime=runtime)
    )


def build_subject_reliability(session: AsyncSession) -> SubjectReliability:
    """A record's subject's Player reliability — points, band, *New*, counts.

    Built over ``player_score``'s **published** read and never over the two folds
    underneath it, which is the same fence every other row here takes: the
    points a player is shown are that context's arithmetic, and a second caller
    reaching past it to ``games`` and ``bookings`` would be a second author of
    what the number means.
    """

    return ScoreSubjectReliability(build_published_score_query(session))


def build_reliability_filters(session: AsyncSession) -> ReliabilityFilters:
    """The reader's own reliability filter in their groups, and the figure that
    brings them back (#661) — over ``groups``' directory, each member's Player
    profile and ``player_score``'s **published** read, the same three facts the
    pair rule's clause is asked over."""

    return FiltersInTheGroups(
        groups=build_group_directory(session),
        profiles=build_player_profile_repository(
            event_store=build_domain_event_store(session),
            events=build_event_publisher(session),
        ),
        scores=build_published_score_query(session),
    )


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
    clock: Clock | None = None,
) -> SettleRatingsOnResults:
    """The catch-up, wired the way a request is.

    The clock is built here unless one is handed in, because *has this result
    settled* is a fact about the instant the run happens and a caller holding
    one could hold a stale one — the same argument the composed match-history
    read makes. The one caller that hands one in is the dev console's *Run it
    now* (#593), with its request's clock: read the moment the press runs, as
    every other press's job is, and the clock a test moves.
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
        clock=clock or build_clock(),
    )


def build_ruleset() -> Ruleset:
    """Which numbers the forecast and the level window run on. **Chosen here
    and nowhere else.**

    ``docs/adr/0093`` ships a ruleset with the code and defers the runtime store
    — *its arrival changes only where the file is read from, never what the
    stamp guarantees*, and this is the line it changes.

    **Nothing here reads the environment.** A tolerance is not a setting: who
    may share a court is behaviour a domain test can observe, and `local`,
    `development`, `staging` and `production` run the same numbers.
    """
    return LIVE_RULESET


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


def build_game_disclosure(session: AsyncSession) -> PriorDisclosure:
    """*We were on a court together* — over ``games``' directory."""

    return GamesTheyPlayed(build_game_directory(session))


def build_group_disclosure(session: AsyncSession) -> PriorDisclosure:
    """*We are both in a group* — over ``groups``' directory.

    The strand a group's Members needed: it lists every member rated in the
    sport and opens their record on a press and hold, and the group alone is
    what showed them to each other.
    """

    return GroupsTheyShare(build_group_directory(session))


def build_runner_disclosure(session: AsyncSession) -> PriorDisclosure:
    """*I run a group they are in* — over ``groups``' directory and who runs each
    official group now, the same reading the group's Members makes (#566).

    The strand an official group's Administrator needed: Members lists every
    member rated in the sport and opens their record on a press and hold, and
    running a group is not being in it.
    """

    return GroupsTheReaderRuns(
        build_group_directory(session), build_group_administrators(session)
    )


def build_account_gates(
    *, holds: AccountHoldQuery, account_status: AccountStatusQuery
) -> AccountGates:
    """The two gates about accounts — a hold, an account that may not be shown —
    over the two reads a request already holds, so there is one spelling of
    each. **No block** (``docs/adr/0193`` §2)."""

    return AccountGates(holds=holds, account_status=account_status)


def build_record_gates(
    *, accounts: AccountGates, holds: AccountHoldQuery
) -> RecordGates:
    """The two about accounts, plus the reader's own hold — no preference
    (#575) and no block (``docs/adr/0193`` §2).

    The two are **not built here**: they are ``matchmaking``'s collaborator,
    already assembled per request, and this line composes rather than copies. A
    second spelling of a safety gate is the defect the whole rule exists to
    prevent.
    """

    return LiveRecordGates(accounts=accounts, holds=holds)


def build_blocks_by_the_reader(blocks: BlockQuery) -> BlocksByTheReader:
    """The record's *you blocked them* — the reader's own block, over the one
    directed read ``BlockQuery`` has (``docs/adr/0193`` §3)."""

    return OwnBlocksOfTheReader(blocks)


def build_relations_of_the_reader(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> RelationsOfTheReader:
    """The record's left button — the reader's own relation to the person on it,
    over Friends' read (``docs/adr/0202`` §1)."""

    return FriendsRelationsOfTheReader(build_read_relations(session, runtime=runtime))


# --------------------------------------------------------------------------
# Background runs
# --------------------------------------------------------------------------


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
        ),
        build_game_directory(session, runtime=runtime),
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
    played: PlayedCourt | None = None,
    runtime: EventRuntime | None = None,
) -> Membership:
    """*The people on this room's game's court right now* — read off ``games``.

    ``played`` is takeable because the list read asks the same port a second
    question — *which games is this player on* — and two courts over one
    session would be two aggregate repositories each remembering its own stream
    versions. One per request, handed in.
    """
    return Membership(played=played or build_played_court(session, runtime=runtime))


def build_a_room_of_yours(
    *,
    conversations: ConversationRepository,
    membership: Membership,
    clock: Clock,
) -> ARoomOfYours:
    """*This room, if you are in it* — the seam every act on one room shares.

    Built from the collaborators rather than from a session, because both are
    already request-scoped and a second copy of either would be a second answer
    to *who is in this*.

    **The clock is what makes the lifetime a read.** A room past its end answers
    ``conversation_not_found`` whether or not the sweep has run
    (``docs/adr/0153`` §5). *Over* is folded off the room's own stream — the
    same fold the list and the sweep decide it through — and this is the one
    seam every act on **one** room passes through, so the refusal has a single
    place.
    """
    return ARoomOfYours(
        conversations=conversations,
        membership=membership,
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
    return TellTheRoom(
        conversations=conversations,
        directory=build_conversation_directory(
            session=session, conversations=conversations
        ),
        nudges=nudges,
    )


def build_nudge_publisher(client: Redis) -> NudgePublisher:
    """*Tell whoever is listening that a room moved* — **wrapped, always.**

    The composition root never hands out an unwrapped publisher: the entry is
    already durable in Postgres when this is called, so a bus that is down costs
    a room its liveness and may never cost anybody their message. An unwrapped one would
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


# --------------------------------------------------------------------------
# Notifications (#549; docs/adr/0189 §5)
# --------------------------------------------------------------------------
#
# Told through the outbox by contexts that do not know it exists, as a room is
# (docs/adr/0146 §5): the teller and the pusher are built per delivery run over
# its session, and the push service is a per-run seam beside the payment
# provider — Expo's for the API, a recording one for a seed run.


def build_notification_preferences_repository(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> NotificationPreferencesRepository:
    """One stream per player — the three choices and the phones — and the
    choices' and phones' projections written beside it."""
    return EventSourcedNotificationPreferencesRepository(
        session=session,
        event_store=build_domain_event_store(session, runtime=runtime),
        events=build_event_publisher(session, runtime=runtime),
    )


def build_notice_day_repository(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> NoticeDayRepository:
    """One stream per player per day in Kraków — what they were told — and the
    recent list written beside it."""
    return EventSourcedNoticeDayRepository(
        session=session,
        event_store=build_domain_event_store(session, runtime=runtime),
        events=build_event_publisher(session, runtime=runtime),
    )


def build_bell_repository(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> BellRepository:
    """One stream per player — when they last opened their recent notices —
    and the last visit written beside it."""
    return EventSourcedBellRepository(
        session=session,
        event_store=build_domain_event_store(session, runtime=runtime),
        events=build_event_publisher(session, runtime=runtime),
    )


def build_notice_directory(session: AsyncSession) -> NoticeDirectory:
    return SqlAlchemyNoticeDirectory(session)


def build_push_notifications(settings: Settings) -> PushNotifications:
    """The push service this process pushes through: Expo's, or — where
    ``PUSH_PROVIDER`` says so, which a deployed environment refuses — one that
    records and pushes nothing."""

    if settings.PUSH_PROVIDER is PushProvider.RECORDING:
        return RecordingPush()
    return ExpoPush(
        endpoint_url=settings.EXPO_PUSH_URL,
        access_token=settings.EXPO_ACCESS_TOKEN,
        timeout_seconds=settings.EXPO_PUSH_TIMEOUT_SECONDS,
    )


def build_recording_push() -> RecordingPush:
    """A push service that pushes nothing — a seed run's, whose players have no
    phones."""
    return RecordingPush()


def build_game_briefs(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> GameBriefs:
    """A game as a notice tells it: its proposal's stream and its booking's."""
    store = build_domain_event_store(session, runtime=runtime)
    events = build_event_publisher(session, runtime=runtime)
    return BookedAndProposedGames(
        proposals=build_proposal_repository(session, event_store=store, events=events),
        bookings=build_booking_repository(session, event_store=store, events=events),
    )


def build_game_courts(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> GameCourts:
    """A booked game's court as a notice tells it — the Game's own stream
    (#663)."""
    return GameStreamCourts(
        games=build_game_repository(
            session=session,
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        )
    )


def build_ended_hours(session: AsyncSession) -> EndedHours:
    """The booked games whose hour has just ended — the bookings' own
    projection (#663)."""
    return BookedHours(build_booking_directory(session))


def build_group_joiners(session: AsyncSession) -> GroupJoiners:
    """When each account first joined a group it is in now — the groups' own
    published directory (#727)."""
    return DirectoryGroupJoiners(build_group_directory(session))


def build_rated_accounts(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> RatedAccounts:
    """Who holds a Skill rating in any sport — rating's published read, which
    holds nothing (#727)."""
    return RatingsRatedAccounts(build_rated_player_query(session, runtime=runtime))


def build_decks(
    session: AsyncSession, *, settings: Settings, runtime: EventRuntime | None = None
) -> Decks:
    """Whose deck shows a card — asked of the deck itself, so an alert never
    points at a card the reader cannot find."""
    return ProposalsDecks(
        proposals=build_proposal_repository(
            session,
            event_store=build_domain_event_store(session, runtime=runtime),
            events=build_event_publisher(session, runtime=runtime),
        ),
        deck=build_read_group_deck(
            session, settings=settings, clock=build_clock(), runtime=runtime
        ),
    )


def build_paid_shares(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> PaidShares:
    """What a refund gives back, off the share's own Seat charge."""
    return SeatChargeShares(_seat_charge_repository(session, runtime))


def build_seat_offers(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> SeatOffers:
    """Who an open seat is offered to — the Fill in board's own offer."""
    return RescueSeatOffers(
        pools=build_pools(session),
        bookings=build_player_bookings(session, runtime=runtime),
        offers=build_rescue_offers(session, runtime=runtime),
    )


def build_notice_names(session: AsyncSession) -> Names:
    """A person's nickname and a club's name, for what a notice says."""
    return PlatformNames(
        users=build_user_repository(session),
        clubs=build_proposal_club_names(session),
        groups=build_group_directory(session),
    )


def build_notice_words(session: AsyncSession) -> NoticeWords:
    return NoticeWords(names=build_notice_names(session))


def build_notice_friendships(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> Friendships:
    """What Notifications reads of Friends: the requests and the asks for a
    level on a reader's Home (#745, #764), and whether two are friends."""
    return FriendsOfTheReader(
        requests=ReadRequestsWaiting(
            directory=build_friendship_directory(session),
            blocks=build_readers_blocks(session, runtime=runtime),
        ),
        asks=build_read_level_asks_waiting(session, runtime=runtime),
        relations=build_read_relations(session, runtime=runtime),
    )


def build_read_recent_notices(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> ReadRecentNotices:
    """The list behind the bell — a friend request and a *level asked* each
    listed only while its card is on Home (#745, #764)."""
    return ReadRecentNotices(
        notices=build_notice_directory(session),
        words=build_notice_words(session),
        friendships=build_notice_friendships(session, runtime=runtime),
    )


def build_notice_pushes(session: AsyncSession) -> NoticePushes:
    """What a notice is pushed as — to every phone, and in the dev console's
    *Sent* pane."""
    return NoticePushes(words=build_notice_words(session))


def build_give_notice(
    session: AsyncSession, *, runtime: EventRuntime | None = None
) -> GiveNotice:
    """One player told one notice, as their choices and their day allow."""
    return GiveNotice(
        preferences=build_notification_preferences_repository(session, runtime=runtime),
        days=build_notice_day_repository(session, runtime=runtime),
    )


def build_tell_the_players(
    session: AsyncSession, *, settings: Settings, runtime: EventRuntime | None = None
) -> TellThePlayers:
    """What a player is told about a game and its money — built per delivery
    run, over the session the delivery commits in."""
    preferences = build_notification_preferences_repository(session, runtime=runtime)
    return TellThePlayers(
        give=build_give_notice(session, runtime=runtime),
        games=build_game_briefs(session, runtime=runtime),
        courts=build_game_courts(session, runtime=runtime),
        decks=build_decks(session, settings=settings, runtime=runtime),
        shares=build_paid_shares(session, runtime=runtime),
        offers=build_seat_offers(session, runtime=runtime),
        preferences=preferences,
        friendships=build_notice_friendships(session, runtime=runtime),
    )


def build_ask_how_did_it_go(
    session: AsyncSession, *, clock: Clock, runtime: EventRuntime | None = None
) -> AskHowDidItGo:
    """One run of *How did it go?* over this session — the job's, the
    console's press and a test's (#663)."""
    return AskHowDidItGo(
        hours=build_ended_hours(session),
        courts=build_game_courts(session, runtime=runtime),
        games=build_game_briefs(session, runtime=runtime),
        give=build_give_notice(session, runtime=runtime),
        uow=build_unit_of_work(session),
        clock=clock,
    )


def build_tell_get_your_level(
    session: AsyncSession, *, clock: Clock, runtime: EventRuntime | None = None
) -> TellGetYourLevel:
    """One run of *Get your level* over this session — the job's and a
    test's (#727)."""
    return TellGetYourLevel(
        joiners=build_group_joiners(session),
        ratings=build_rated_accounts(session, runtime=runtime),
        notices=build_notice_directory(session),
        give=build_give_notice(session, runtime=runtime),
        uow=build_unit_of_work(session),
        clock=clock,
    )


def build_push_the_notice(
    session: AsyncSession,
    *,
    push: PushNotifications,
    clock: Clock,
    runtime: EventRuntime | None = None,
) -> PushTheNotice:
    """A notice given, pushed to its player's phones over the run's push
    service."""
    return PushTheNotice(
        preferences=build_notification_preferences_repository(session, runtime=runtime),
        pushes=build_notice_pushes(session),
        push=push,
        clock=clock,
    )
