from __future__ import annotations

from datetime import datetime, timezone

import jwt
import pytest

from app.core.exception_handlers import UnauthorizedError
from app.modules.auth.domain.ports import IssuedToken
from app.modules.users.application.resolve_current_user import (
    ResolveCurrentUserFromAccessToken,
)
from app.modules.users.domain.errors import UserNotEligible
from app.modules.users.domain.user import User
from app.modules.users.domain.value_objects import Email, HashedPassword, Nickname
from app.shared.ids import new_uuid


class StubTokenService:
    def __init__(self, payload=None, error: Exception | None = None) -> None:
        self._payload = payload or {}
        self._error = error

    def issue_access(self, subject: str) -> IssuedToken:
        raise NotImplementedError

    def issue_refresh(self, subject: str) -> IssuedToken:
        raise NotImplementedError

    def decode_access(self, token: str) -> dict:
        if self._error is not None:
            raise self._error
        return self._payload

    def decode_refresh(self, token: str) -> dict:
        raise NotImplementedError

    @property
    def access_ttl_seconds(self) -> int:
        return 900

    @property
    def refresh_ttl_seconds(self) -> int:
        return 86400


class StubGetCurrentUser:
    def __init__(
        self,
        user: User | None = None,
        error: Exception | None = None,
    ) -> None:
        self._user = user
        self._error = error
        self.seen_user_id = None

    async def execute(self, user_id):
        self.seen_user_id = user_id
        if self._error is not None:
            raise self._error
        return self._user


def _user() -> User:
    return User(
        id=new_uuid(),
        email=Email("alice@example.com"),
        nickname=Nickname("alice"),
        password_hash=HashedPassword("hash"),
        created_at=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_resolve_current_user_from_access_token_success():
    user = _user()
    getter = StubGetCurrentUser(user=user)
    service = StubTokenService(payload={"sub": str(user.id)})

    resolved = await ResolveCurrentUserFromAccessToken(service, getter).execute("token")

    assert resolved is user
    assert getter.seen_user_id == user.id


@pytest.mark.asyncio
async def test_resolve_current_user_rejects_missing_access_token():
    service = StubTokenService(payload={"sub": str(new_uuid())})
    getter = StubGetCurrentUser(user=_user())

    with pytest.raises(UnauthorizedError, match="missing bearer token"):
        await ResolveCurrentUserFromAccessToken(service, getter).execute(None)


@pytest.mark.asyncio
async def test_resolve_current_user_rejects_invalid_access_token():
    service = StubTokenService(error=jwt.InvalidTokenError("bad token"))
    getter = StubGetCurrentUser(user=_user())

    with pytest.raises(UnauthorizedError, match="invalid access token"):
        await ResolveCurrentUserFromAccessToken(service, getter).execute("token")


@pytest.mark.asyncio
async def test_resolve_current_user_rejects_malformed_subject():
    service = StubTokenService(payload={"sub": "not-a-uuid"})
    getter = StubGetCurrentUser(user=_user())

    with pytest.raises(UnauthorizedError, match="malformed token subject"):
        await ResolveCurrentUserFromAccessToken(service, getter).execute("token")


@pytest.mark.asyncio
async def test_resolve_current_user_preserves_user_eligibility_errors():
    service = StubTokenService(payload={"sub": str(new_uuid())})
    getter = StubGetCurrentUser(error=UserNotEligible())

    with pytest.raises(UserNotEligible):
        await ResolveCurrentUserFromAccessToken(service, getter).execute("token")
