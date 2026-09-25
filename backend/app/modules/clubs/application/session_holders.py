from __future__ import annotations

from uuid import UUID

from app.modules.clubs.domain.club_account import ClubAccount
from app.modules.clubs.domain.errors import ClubAccountNotEligible
from app.modules.clubs.domain.ports import ClubAccountRepository


async def eligible_club_account(
    accounts: ClubAccountRepository, account_id: UUID
) -> ClubAccount:
    """The Club account a token names, or ``club_account_not_eligible``.

    One rule for using a club session and renewing one, as ``GetCurrentUser`` is
    for a player's. Nothing disables a Club account yet, so *eligible* is
    *still exists*.
    """

    account = await accounts.get_by_id(account_id)
    if account is None:
        raise ClubAccountNotEligible()
    return account


class ClubAccountSessionHolders:
    """``SessionHolders`` for the club website: a session is a Club account's."""

    def __init__(self, accounts: ClubAccountRepository) -> None:
        self._accounts = accounts

    async def refuse_unless_eligible(self, account_id: UUID) -> None:
        await eligible_club_account(self._accounts, account_id)
