"""Import all ORM models so SQLAlchemy registers them on Base.metadata."""

from app.infrastructure.events.event_delivery_model import EventOutboxORM
from app.infrastructure.events.event_store_model import EventStoreORM
from app.infrastructure.mail.mail_queue_model import MailQueueORM
from app.modules.administrators.infrastructure.administrator_model import (
    AdministratorORM,
)
from app.modules.bookings.infrastructure.booking_models import (
    BookingKeepORM,
    BookingORM,
    BookingSeatORM,
)
from app.modules.auth.infrastructure.one_time_credential_model import (
    OneTimeCredentialORM,
)
from app.modules.auth.infrastructure.sqlalchemy_refresh_token_model import (
    RefreshTokenORM,
)
from app.modules.clubs.infrastructure.club_model import (
    ClubAccountORM,
    ClubORM,
    ClubPaymentsAccountORM,
)
from app.modules.conversations.infrastructure.conversation_model import (
    ConversationORM,
)
from app.modules.friends.infrastructure.friend_link_model import FriendLinkCodeORM
from app.modules.friends.infrastructure.friendship_model import (
    FriendLevelAskORM,
    FriendRelationORM,
)
from app.modules.groups.infrastructure.group_model import GroupMemberORM, GroupORM
from app.modules.notifications.infrastructure.notification_models import (
    NoticeORM,
    NotificationPreferencesORM,
    PushDeviceORM,
)
from app.modules.payments.infrastructure.payment_models import (
    PaymentCustomerORM,
    PaymentNoticeORM,
    SeatChargeORM,
)
from app.modules.sportsmanship.infrastructure.card_model import (
    SportsmanshipCardORM,
    SportsmanshipRatingORM,
)
from app.modules.proposals.infrastructure.proposal_models import (
    PoolORM,
    ProposalORM,
    ProposalPersonORM,
)
from app.modules.users.infrastructure.sqlalchemy_user_model import UserORM

__all__ = [
    "AdministratorORM",
    "BookingKeepORM",
    "BookingORM",
    "BookingSeatORM",
    "ClubAccountORM",
    "ClubORM",
    "ClubPaymentsAccountORM",
    "ConversationORM",
    "EventOutboxORM",
    "EventStoreORM",
    "FriendLevelAskORM",
    "FriendLinkCodeORM",
    "FriendRelationORM",
    "GroupMemberORM",
    "GroupORM",
    "MailQueueORM",
    "NoticeORM",
    "NotificationPreferencesORM",
    "OneTimeCredentialORM",
    "PaymentCustomerORM",
    "PaymentNoticeORM",
    "PoolORM",
    "ProposalORM",
    "ProposalPersonORM",
    "PushDeviceORM",
    "RefreshTokenORM",
    "SeatChargeORM",
    "SportsmanshipCardORM",
    "SportsmanshipRatingORM",
    "UserORM",
]
