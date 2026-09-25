from __future__ import annotations

from app.modules.auth.application.token_rotation import TokenPair, TokenRotator
from app.modules.auth.domain.audience import Audience
from app.modules.auth.domain.errors import InvalidCredentials
from app.modules.auth.domain.ports import PasswordHasher
from app.modules.clubs.application.commands import SignInClubCommand
from app.modules.clubs.domain.ports import ClubAccountRepository
from app.modules.users.domain.value_objects import Email


class SignInClub:
    """The desk signs in, and gets a pair **for the club audience**.

    Reads Club accounts only, so a player's credentials are refused here exactly
    as a stranger's are — even for an email a club account also uses, because
    the two are different identities with different passwords (``docs/adr/0182``
    §3). The refusal is ``invalid_credentials``, identical for an unknown email,
    a malformed one and a wrong password, as the player's sign-in is.
    """

    def __init__(
        self,
        *,
        accounts: ClubAccountRepository,
        hasher: PasswordHasher,
        rotator: TokenRotator,
    ) -> None:
        self._accounts = accounts
        self._hasher = hasher
        self._rotator = rotator

    async def execute(self, command: SignInClubCommand) -> TokenPair:
        try:
            email = Email(command.email)
        except ValueError:
            raise InvalidCredentials() from None
        account = await self._accounts.get_by_email(email)
        if account is None or not self._hasher.verify(
            command.password, account.password_hash.value
        ):
            raise InvalidCredentials()
        return await self._rotator.issue_pair(account.id, audience=Audience.CLUB)
