"""The two card fields the candidate index deliberately does not hold.

**A nickname belongs to ``users``**, which the index does not tail at all, and a
photo list belongs to the **Player profile**, which the index deliberately does
not project — ``candidate_projection`` refuses ``player_profile.photos_changed``
by name, because the card is assembled outside the engine (``docs/adr/0107``).

**It reads each provider's own port and never their tables.** The rule its
neighbour ``users_account_status`` states applies here twice over: a ``select``
over ``UserORM``, or a walk over the profile streams in ``event_store``, would
make the matcher a second reader of somebody else's schema — and the second is
worse than the first, because it would also be a second implementation of how a
profile is folded.

**It runs after the floor**, so it is at most twenty players even when the pool
is five hundred: one set read for the nicknames, and one profile per surviving
row. The per-row read is the price of not owning somebody else's storage, and it
is bounded by the shortlist rather than by the city. If it ever stops being
affordable, the fix is a read model **on the provider's side** with a port over
it, not a query written here.

**No URL is minted here.** Photos are served through short-lived presigned links
and a search record is kept for ever, so what this source hands over — and what
the record stores — is the id. The link is signed one layer out, per response,
by ``CardPhotoLinks``: it is not a fact about the player, and a card assembled
before the record is written must not carry one.
"""

from __future__ import annotations

from typing import Collection, Mapping
from uuid import UUID

from app.modules.matchmaking.domain.cards import CardIdentity
from app.modules.player_profile.domain.ports import PlayerProfileRepository
from app.modules.users.domain.ports import UserRepository


class PlayerCardIdentities:
    """``PlayerCardSource`` over the ``users`` and Player profile ports."""

    def __init__(
        self, *, users: UserRepository, profiles: PlayerProfileRepository
    ) -> None:
        self._users = users
        self._profiles = profiles

    async def identities_for(
        self, player_ids: Collection[UUID]
    ) -> Mapping[UUID, CardIdentity]:
        """Each of these players' nickname and first photo.

        **The nickname is what decides whether there is a card at all.** A player
        ``users`` has never heard of is absent from the answer rather than
        present with a blank name, and the caller drops the row before the record
        is written so that ``n_returned`` and the rows stored still agree.

        A missing *photo*, by contrast, is an ordinary state: the card is drawn
        and the client draws the generated court poster.
        """

        if not player_ids:
            return {}
        nicknames = await self._users.find_nicknames_of(player_ids)
        return {
            player_id: CardIdentity(
                nickname=nickname, photo_id=await self._first_photo(player_id)
            )
            for player_id, nickname in nicknames.items()
        }

    async def _first_photo(self, player_id: UUID) -> UUID | None:
        """The photo a card shows — **the first**, because order is meaning in a
        player's photo list.

        ``None`` when they have none, which is not an absence to report: the
        glossary calls a player with no photo *"not an absence but a generated
        court poster"*, so the field is simply omitted and the client draws one.
        """

        profile = await self._profiles.load(player_id)
        if profile is None or not profile.photo_ids:
            return None
        return profile.photo_ids[0]
