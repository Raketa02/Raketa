"""Import all ORM models so SQLAlchemy registers them on Base.metadata."""

from app.infrastructure.events.event_delivery_model import EventOutboxORM
from app.infrastructure.events.event_store_model import EventStoreORM
from app.infrastructure.mail.mail_queue_model import MailQueueORM
from app.modules.auth.infrastructure.one_time_credential_model import (
    OneTimeCredentialORM,
)
from app.modules.auth.infrastructure.sqlalchemy_refresh_token_model import (
    RefreshTokenORM,
)
from app.modules.clubs.infrastructure.club_model import ClubAccountORM, ClubORM
from app.modules.conversations.infrastructure.conversation_model import (
    ConversationORM,
)
from app.modules.groups.infrastructure.group_model import GroupMemberORM, GroupORM
from app.modules.matchmaking.infrastructure.candidate_index_model import (
    CandidateIndexCursorORM,
    CandidatePlayerFactsORM,
    CandidateRowORM,
)
from app.modules.matchmaking.infrastructure.deck_reset_model import DeckResetORM
from app.modules.matchmaking.infrastructure.interest_model import InterestORM
from app.modules.matchmaking.infrastructure.search_model import (
    SearchCandidateORM,
    SearchORM,
)
from app.modules.sportsmanship.infrastructure.card_model import (
    SportsmanshipCardORM,
    SportsmanshipRatingORM,
)
from app.modules.users.infrastructure.sqlalchemy_user_model import UserORM

__all__ = [
    "CandidateIndexCursorORM",
    "CandidatePlayerFactsORM",
    "CandidateRowORM",
    "ClubAccountORM",
    "ClubORM",
    "ConversationORM",
    "DeckResetORM",
    "EventOutboxORM",
    "EventStoreORM",
    "GroupMemberORM",
    "GroupORM",
    "InterestORM",
    "MailQueueORM",
    "OneTimeCredentialORM",
    "RefreshTokenORM",
    "SearchCandidateORM",
    "SearchORM",
    "SportsmanshipCardORM",
    "SportsmanshipRatingORM",
    "UserORM",
]
