from __future__ import annotations

from datetime import datetime, timezone
from typing import cast
from uuid import UUID

import jwt
import pytest

from app.shared.domain import UnauthorizedError
from app.modules.auth.domain.audience import Audience
from app.modules.auth.domain.ports import IssuedToken
from app.modules.users.application.get_current_user import GetCurrentUser
from app.modules.users.application.resolve_current_user import (
    ResolveCurrentUserFromAccessToken,
)
from app.modules.users.domain.errors import UserNotEligible
from app.modules.users.domain.user import User
from app.modules.users.domain.value_objects import Email, HashedPassword
from app.shared.ids import new_uuid


#: What every decoded access token carries beside its subject.
#:
#: ``JwtTokenService`` requires ``exp`` on decode — an access token without one
#: never reaches this use case — and one caller reads it: the conversation stream
#: closes at that instant rather than outliving the credential that opened it
#: (`docs/adr/0147` §6). A stub that omitted it would be describing a token this
#: application cannot issue. ``iat`` likewise: it is required on decode, and it is
#: the issue instant a token without ``iat_us`` is compared with when its account
#: signs out everywhere (`docs/adr/0185` §7).
AN_HOUR_FROM_NOW = int(datetime.now(timezone.utc).timestamp()) + 3600
JUST_NOW = AN_HOUR_FROM_NOW - 3600


def _payload(**fields) -> dict:
    return {"exp": AN_HOUR_FROM_NOW, "iat": JUST_NOW, **fields}


class StubTokenService:
    def __init__(self, payload=None, error: Exception | None = None) -> None:
        self._payload = payload or {}
        self._error = error

    def issue_access(self, subject: str, *, audience: Audience) -> IssuedToken:
        raise NotImplementedError

    def issue_refresh(self, subject: str, *, audience: Audience) -> IssuedToken:
        raise NotImplementedError

    def decode_access(self, token: str, *, audience: Audience) -> dict:
        if self._error is not None:
            raise self._error
        return self._payload

    def decode_refresh(self, token: str, *, audience: Audience) -> dict:
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
        self.seen_user_id: UUID | None = None

    async def execute(self, user_id: UUID):
        self.seen_user_id = user_id
        if self._error is not None:
            raise self._error
        return self._user


def _user() -> User:
    return User(
        id=new_uuid(),
        email=Email("alice@example.com"),
        password_hash=HashedPassword("hash"),
        created_at=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_resolve_current_user_from_access_token_success():
    user = _user()
    getter = StubGetCurrentUser(user=user)
    typed_getter = cast(GetCurrentUser, getter)
    service = StubTokenService(payload=_payload(sub=str(user.id)))

    resolved = await ResolveCurrentUserFromAccessToken(
        service, typed_getter
    ).execute("token")

    assert resolved is user
    assert getter.seen_user_id == user.id


@pytest.mark.asyncio
async def test_resolve_current_user_rejects_missing_access_token():
    service = StubTokenService(payload=_payload(sub=str(new_uuid())))
    getter = StubGetCurrentUser(user=_user())
    typed_getter = cast(GetCurrentUser, getter)

    with pytest.raises(UnauthorizedError, match="missing bearer token"):
        await ResolveCurrentUserFromAccessToken(service, typed_getter).execute(None)


@pytest.mark.asyncio
async def test_resolve_current_user_rejects_invalid_access_token():
    service = StubTokenService(error=jwt.InvalidTokenError("bad token"))
    getter = StubGetCurrentUser(user=_user())
    typed_getter = cast(GetCurrentUser, getter)

    with pytest.raises(UnauthorizedError, match="invalid access token"):
        await ResolveCurrentUserFromAccessToken(service, typed_getter).execute("token")


@pytest.mark.asyncio
async def test_resolve_current_user_rejects_malformed_subject():
    service = StubTokenService(payload=_payload(sub="not-a-uuid"))
    getter = StubGetCurrentUser(user=_user())
    typed_getter = cast(GetCurrentUser, getter)

    with pytest.raises(UnauthorizedError, match="malformed token subject"):
        await ResolveCurrentUserFromAccessToken(service, typed_getter).execute("token")


@pytest.mark.asyncio
async def test_resolve_current_user_preserves_user_eligibility_errors():
    service = StubTokenService(payload=_payload(sub=str(new_uuid())))
    getter = StubGetCurrentUser(error=UserNotEligible())
    typed_getter = cast(GetCurrentUser, getter)

    with pytest.raises(UserNotEligible):
        await ResolveCurrentUserFromAccessToken(service, typed_getter).execute("token")


@pytest.mark.asyncio
async def test_an_access_token_carries_the_instant_it_stops_being_valid():
    """One caller needs it, and it is the live channel (`docs/adr/0147` §6).

    A stream is closed at the token's own `exp` rather than on a TTL recomputed
    beside it: the two agree today, and the honest deadline is the one written
    into the credential the caller actually presented.
    """

    user = _user()
    service = StubTokenService(payload=_payload(sub=str(user.id)))

    session = await ResolveCurrentUserFromAccessToken(
        service, cast(GetCurrentUser, StubGetCurrentUser(user=user))
    ).authenticated_session("token")

    assert session.user is user
    assert session.expires_at == datetime.fromtimestamp(
        AN_HOUR_FROM_NOW, tz=timezone.utc
    )


@pytest.mark.asyncio
async def test_a_token_with_no_readable_expiry_is_refused():
    """**Not defensive.** A credential that never runs out is what `docs/adr/0004`
    refuses, and a stream with no deadline is what §6 refuses — so *there is no
    expiry* has to be a refusal here rather than a stream nothing ever closes."""

    service = StubTokenService(payload={"sub": str(new_uuid())})

    with pytest.raises(UnauthorizedError):
        await ResolveCurrentUserFromAccessToken(
            service, cast(GetCurrentUser, StubGetCurrentUser(user=_user()))
        ).execute("token")
