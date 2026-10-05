"""``ClubDesks`` over what the Club context publishes — so the arrow runs
``bookings → clubs`` only, as the court finder's does.

**The desk is the club's one sign-in** (the mechanics §16.14: one login per
club), read from its account's row, which is whom every email to a club is
addressed to; **the name is the club's listing**, as a player reads it.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.modules.bookings.domain.ports import ClubDesk
from app.modules.clubs.domain.ports import ClubAccountRepository, ClubDirectory


@final
class AccountClubDesks:
    def __init__(
        self, *, accounts: ClubAccountRepository, directory: ClubDirectory
    ) -> None:
        self._accounts = accounts
        self._directory = directory

    async def of(self, club_id: UUID) -> ClubDesk | None:
        account = await self._accounts.get_by_club(club_id)
        listing = (await self._directory.listed([club_id])).get(club_id)
        if account is None or listing is None:
            return None
        return ClubDesk(email=account.email.value, club_name=listing.name)
