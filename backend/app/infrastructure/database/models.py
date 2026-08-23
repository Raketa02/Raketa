"""Import all ORM models so SQLAlchemy registers them on Base.metadata."""

from app.infrastructure.database.command_log_model import CommandLogORM
from app.infrastructure.events.event_delivery_model import EventOutboxORM
from app.infrastructure.events.event_store_model import EventStoreORM
from app.modules.auth.infrastructure.sqlalchemy_refresh_token_model import (
    RefreshTokenORM,
)
from app.modules.clubs.infrastructure.sqlalchemy_club_models import (
    ClubCardOffsetORM,
    ClubCourtCatalogueORM,
    ClubCourtCategoryORM,
    ClubORM,
    ClubPayoutDestinationORM,
    ClubPolicyORM,
)
from app.modules.courts.infrastructure.sqlalchemy_court_models import (
    BookingORM,
    ReservationORM,
)
from app.modules.matches.infrastructure.sqlalchemy_match_models import (
    MatchORM,
    MatchSeatORM,
    MatchVacancyORM,
)
from app.modules.users.infrastructure.sqlalchemy_user_model import UserORM

__all__ = [
    "BookingORM",
    "ClubCardOffsetORM",
    "ClubCourtCatalogueORM",
    "ClubCourtCategoryORM",
    "ClubORM",
    "ClubPayoutDestinationORM",
    "ClubPolicyORM",
    "CommandLogORM",
    "EventOutboxORM",
    "EventStoreORM",
    "MatchORM",
    "MatchSeatORM",
    "MatchVacancyORM",
    "RefreshTokenORM",
    "ReservationORM",
    "UserORM",
]
