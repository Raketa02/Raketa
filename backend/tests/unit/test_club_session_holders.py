"""A club session whose account can no longer be found ends.

Unreachable over HTTP today — nothing deletes or disables a Club account — so
the rule is asserted at the two places it is applied: resolving a request's
token, and renewing a session. Both refuse with ``club_account_not_eligible``,
the club surface's ``user_not_eligible``. Ports are stubbed by hand, as this
suite does everywhere a use case takes one.
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from app.bootstrap.composition import build_clock, build_token_service
from app.core.config import get_settings
from app.modules.auth.domain.audience import Audience
from app.modules.auth.domain.errors import AccessTokenInvalid
from app.modules.clubs.application.resolve_club_account import (
    ResolveClubAccountFromAccessToken,
)
from app.modules.clubs.application.session_holders import ClubAccountSessionHolders
from app.modules.clubs.domain.club_account import ClubAccount
from app.modules.clubs.domain.errors import ClubAccountNotEligible
from app.modules.users.domain.value_objects import Email, HashedPassword


class StubAccounts:
    def __init__(self, *accounts: ClubAccount) -> None:
        self._by_id = {account.id: account for account in accounts}

    async def get_by_id(self, account_id: UUID) -> ClubAccount | None:
        return self._by_id.get(account_id)

    async def get_by_email(self, email: Email) -> ClubAccount | None:
        raise NotImplementedError

    async def save(self, account: ClubAccount) -> None:
        raise NotImplementedError


DESK = ClubAccount(
    id=uuid4(),
    club_id=uuid4(),
    email=Email("desk@ogrody33.pl"),
    password_hash=HashedPassword("$2b$04$notarealhash"),
)


def token_for(account_id: UUID, audience: Audience) -> str:
    return (
        build_token_service(get_settings(), clock=build_clock())
        .issue_access(str(account_id), audience=audience)
        .token
    )


async def test_a_club_token_resolves_to_its_account():
    resolve = ResolveClubAccountFromAccessToken(
        token_service=build_token_service(get_settings(), clock=build_clock()),
        accounts=StubAccounts(DESK),
    )

    assert await resolve.execute(token_for(DESK.id, Audience.CLUB)) == DESK


async def test_a_club_token_whose_account_is_gone_is_refused():
    resolve = ResolveClubAccountFromAccessToken(
        token_service=build_token_service(get_settings(), clock=build_clock()),
        accounts=StubAccounts(),
    )

    with pytest.raises(ClubAccountNotEligible):
        await resolve.execute(token_for(DESK.id, Audience.CLUB))


async def test_a_player_token_naming_a_club_account_s_id_is_still_refused():
    resolve = ResolveClubAccountFromAccessToken(
        token_service=build_token_service(get_settings(), clock=build_clock()),
        accounts=StubAccounts(DESK),
    )

    with pytest.raises(AccessTokenInvalid):
        await resolve.execute(token_for(DESK.id, Audience.PLAYER_APP))


async def test_only_an_account_that_still_exists_may_renew_a_club_session():
    holders = ClubAccountSessionHolders(StubAccounts(DESK))

    await holders.refuse_unless_eligible(DESK.id)
    with pytest.raises(ClubAccountNotEligible):
        await holders.refuse_unless_eligible(uuid4())
