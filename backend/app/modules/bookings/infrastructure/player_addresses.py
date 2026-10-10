"""Whom an email to a player is addressed to — the ``users`` context's fact,
signed here, so the arrow runs ``bookings → users`` (#623): the club's no and
its silence are emailed to each player on the request (the mechanics Q105)."""

from __future__ import annotations

from collections.abc import Collection, Mapping
from typing import final
from uuid import UUID

from app.modules.bookings.domain.ports import PlayerAddress
from app.modules.users.domain.ports import UserRepository


@final
class UserPlayerAddresses:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    async def of(self, player_ids: Collection[UUID]) -> Mapping[UUID, PlayerAddress]:
        addresses: dict[UUID, PlayerAddress] = {}
        for player_id in dict.fromkeys(player_ids):
            user = await self._users.get_by_id(player_id)
            if user is None:
                continue
            addresses[player_id] = PlayerAddress(email=user.email.value)
        return addresses
