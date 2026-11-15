"""``DirectorySources`` — the nickname from ``users``, the rest from the Player
profile, each over its own port: what the two owners hold about one account
**now**, which is what every directory entry is written from.

**An account is gone when ``users`` has no active row for it** — none was ever
opened, or it was disabled, the one way an account stops today (nothing
deletes a User). **It plays once it holds a profile**, and the profile's
``created_at`` is *joined*: the commit that ends onboarding.

**Every account is every User stream**, oldest first — the rebuild's walk, read
off the event store as Rankings' rebuild walks the rating streams.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import final
from uuid import UUID

from app.application.ports import DomainEventStore
from app.modules.discovery.domain.directory import Area, DirectoryEntry, PlayerFacts
from app.modules.player_profile.domain.ports import PlayerProfileRepository
from app.modules.users.application.user_stream import USER_AGGREGATE
from app.modules.users.domain.ports import UserRepository


@final
class AccountDirectorySources:
    def __init__(
        self,
        *,
        users: UserRepository,
        profiles: PlayerProfileRepository,
        event_store: DomainEventStore,
    ) -> None:
        self._users = users
        self._profiles = profiles
        self._event_store = event_store

    async def entry_of(self, player_id: UUID) -> DirectoryEntry | None:
        user = await self._users.get_by_id(player_id)
        if user is None or not user.is_active:
            return None
        nickname = None if user.nickname is None else user.nickname.value
        profile = await self._profiles.load(player_id)
        if profile is None:
            return DirectoryEntry(player_id=player_id, nickname=nickname, player=None)
        return DirectoryEntry(
            player_id=player_id,
            nickname=nickname,
            player=PlayerFacts(
                joined_at=profile.created_at,
                photo_id=profile.photo_ids[0] if profile.photo_ids else None,
                area=Area(
                    latitude=profile.location.latitude,
                    longitude=profile.location.longitude,
                ),
                tags=frozenset(profile.social_tags.ids),
                open_to_new_people=profile.show_me_to_new_people,
            ),
        )

    async def every_account(self) -> Sequence[UUID]:
        return tuple(
            await self._event_store.find_aggregate_ids_by_first_event(
                aggregate_type=USER_AGGREGATE, payload_equals={}
            )
        )
