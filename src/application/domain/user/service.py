from sqlalchemy.ext.asyncio import AsyncSession

from application.core.exceptions import ConflictError, UnauthorizedError
from application.core.security import PasswordHasher
from application.domain.user.entities import User
from application.domain.user.repository import UserRepository
from application.domain.user.schemas import LoginRequest, UserCreateRequest


class UserService:
    def __init__(self, session: AsyncSession, password_hasher: PasswordHasher) -> None:
        self._session = session
        self._users = UserRepository(session)
        self._hasher = password_hasher

    async def create_user(self, payload: UserCreateRequest) -> User:
        if await self._users.get_by_email(payload.email):
            raise ConflictError("email already registered", details={"field": "email"})
        if await self._users.get_by_nickname(payload.nickname):
            raise ConflictError("nickname already taken", details={"field": "nickname"})

        user = User(
            email=payload.email,
            nickname=payload.nickname,
            password_hash=self._hasher.hash(payload.password1),
            authority="USER",
            is_admin=False,
            is_active=True,
        )
        user = await self._users.add(user)
        await self._session.commit()
        return user

    async def authenticate(self, payload: LoginRequest) -> User:
        user = await self._users.get_by_email(payload.email)
        if not user or not self._hasher.verify(payload.password, user.password_hash):
            # Identical error on both branches — no user enumeration.
            raise UnauthorizedError("invalid email or password")
        if not user.is_active:
            raise UnauthorizedError("account disabled")
        return user
