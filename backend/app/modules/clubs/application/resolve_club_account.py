from __future__ import annotations

from app.modules.auth.application.access import read_access_token
from app.modules.auth.domain.audience import Audience
from app.modules.auth.domain.ports import TokenService
from app.modules.clubs.application.session_holders import eligible_club_account
from app.modules.clubs.domain.club_account import ClubAccount
from app.modules.clubs.domain.ports import ClubAccountRepository


class ResolveClubAccountFromAccessToken:
    """Translate a raw bearer token into the Club account it was issued to.

    The club surface's counterpart of ``ResolveCurrentUserFromAccessToken``, and
    it refuses a token in the same five ways, by the same function — plus a
    **player's** token, which is invalid here whatever account it names
    (``docs/adr/0185`` §6). The account is read from its row on every request,
    which is the read ``docs/adr/0185`` §7 prices in for this surface.
    """

    def __init__(
        self, *, token_service: TokenService, accounts: ClubAccountRepository
    ) -> None:
        self._token_service = token_service
        self._accounts = accounts

    async def execute(self, raw_token: str | None) -> ClubAccount:
        claims = read_access_token(
            self._token_service, raw_token, audience=Audience.CLUB
        )
        return await eligible_club_account(self._accounts, claims.account_id)
