"""Import all ORM models so SQLAlchemy registers them on Base.metadata."""

from app.infrastructure.events.event_delivery_model import EventOutboxORM
from app.infrastructure.events.event_store_model import EventStoreORM
from app.modules.auth.infrastructure.sqlalchemy_refresh_token_model import (
    RefreshTokenORM,
)
from app.modules.matchmaking.infrastructure.candidate_index_model import (
    CandidateIndexCursorORM,
    CandidatePlayerFactsORM,
    CandidateRowORM,
)
from app.modules.users.infrastructure.sqlalchemy_user_model import UserORM

__all__ = [
    "CandidateIndexCursorORM",
    "CandidatePlayerFactsORM",
    "CandidateRowORM",
    "EventOutboxORM",
    "EventStoreORM",
    "RefreshTokenORM",
    "UserORM",
]
