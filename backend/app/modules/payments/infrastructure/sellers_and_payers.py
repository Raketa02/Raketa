"""This context's two demands for a seat charge (#541), answered over the
contexts that hold the facts: **the seller** — a club's name and its account at
the provider, read off the Club courts stream (``clubs``, so the arrow runs
``payments → clubs`` as the account link's does) — and **the payer**, a player's
address and Name (``users``).
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from typing import final
from uuid import UUID

from app.modules.clubs.domain.ports import ClubCourtsRepository, ClubDirectory
from app.modules.payments.domain.ports import Payer, Seller
from app.modules.users.domain.ports import UserRepository


@final
class ClubSellers:
    def __init__(
        self, *, directory: ClubDirectory, courts: ClubCourtsRepository
    ) -> None:
        self._directory = directory
        self._courts = courts

    async def of(self, club_ids: Collection[UUID]) -> Mapping[UUID, Seller]:
        listed = await self._directory.listed(club_ids)
        sellers: dict[UUID, Seller] = {}
        for club_id, listing in listed.items():
            payments = (await self._courts.load(club_id)).payments
            sellers[club_id] = Seller(
                name=listing.name,
                account_id=None if payments is None else payments.account_id,
            )
        return sellers


@final
class UserPayers:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    async def of(self, player_ids: Collection[UUID]) -> Mapping[UUID, Payer]:
        payers: dict[UUID, Payer] = {}
        for player_id in dict.fromkeys(player_ids):
            user = await self._users.get_by_id(player_id)
            if user is None:
                continue
            payers[player_id] = Payer(
                email=user.email.value,
                name=None if user.name is None else user.name.value,
            )
        return payers
