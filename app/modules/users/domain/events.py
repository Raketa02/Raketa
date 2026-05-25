from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class UserRegistered:
    user_id: UUID
    email: str
    nickname: str
    occurred_at: datetime
