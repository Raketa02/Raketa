from uuid import UUID

from app.modules.users.domain.errors import UserNotEligible
from app.modules.users.domain.ports import UserRepository
from app.modules.users.domain.user import User


class GetCurrentUser:
    """Resolve a user_id (already decoded from an access token) into a domain
    User and enforce that the account is still active."""

    def __init__(self, users: UserRepository) -> None:
        self._users = users

    async def execute(self, user_id: UUID) -> User:
        user = await self._users.get_by_id(user_id)
        if user is None or not user.is_active:
            raise UserNotEligible()
        return user
