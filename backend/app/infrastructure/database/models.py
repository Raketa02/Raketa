"""Import all ORM models so SQLAlchemy registers them on Base.metadata."""

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
from app.modules.users.infrastructure.sqlalchemy_user_model import UserORM

__all__ = [
    "ClubCardOffsetORM",
    "ClubCourtCatalogueORM",
    "ClubCourtCategoryORM",
    "ClubORM",
    "ClubPayoutDestinationORM",
    "ClubPolicyORM",
    "EventOutboxORM",
    "EventStoreORM",
    "RefreshTokenORM",
    "UserORM",
]
