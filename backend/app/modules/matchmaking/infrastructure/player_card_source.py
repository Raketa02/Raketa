"""The three card fields the candidate index deliberately does not hold.

**A name belongs to ``users``**, which the index does not tail at all, and a
photo list belongs to the **Player profile**, which the index deliberately does
not project — ``candidate_projection`` refuses ``player_profile.photos_changed``
by name, because the card is assembled outside the engine (``docs/adr/0107``).
**The third is what the on-court check concluded about that photograph**
(``docs/adr/0138``), and it is not on the index for the same reason the photo id
is not: it is a photo fact, and no photo fact reaches the index.

**It reads each provider's own port and never their tables.** The rule its
neighbour ``users_account_status`` states applies here twice over: a ``select``
over ``UserORM``, or a walk over the profile streams in ``event_store``, would
make the matcher a second reader of somebody else's schema — and the second is
worse than the first, because it would also be a second implementation of how a
profile is folded.

**It runs after the floor**, so it is at most twenty players even when the pool
is five hundred: one set read for the names, one profile per surviving row,
and — for a row that has a photograph — one object-store ``HEAD`` for the
verdict. The per-row reads are the price of not owning somebody else's storage,
and they are bounded by the shortlist rather than by the city. **The verdict's
is the first of them that is not a database read**, so it is the one that makes a
search's latency depend on the object store answering rather than only on it
signing; ``docs/adr/0138`` is where that was weighed. If any of them ever stops
being affordable, the fix is the same one: a batched method **on the provider's
side**, not a query or a cache written here.

**No URL is minted here.** Photos are served through short-lived presigned links
and a search record is kept for ever, so what this source hands over — and what
the record stores — is the id. The link is signed one layer out, per response,
by ``CardPhotoLinks``: it is not a fact about the player, and a card assembled
before the record is written must not carry one.
"""

from __future__ import annotations

from asyncio import gather
from typing import Collection, Mapping
from uuid import UUID

from app.modules.matchmaking.domain.cards import CardIdentity
from app.modules.player_profile.domain.photos import PhotoRef
from app.modules.player_profile.domain.ports import (
    PhotoStorage,
    PlayerProfileRepository,
)
from app.modules.users.domain.ports import UserRepository


class PlayerCardIdentities:
    """``PlayerCardSource`` over the ``users``, Player profile and photo ports."""

    def __init__(
        self,
        *,
        users: UserRepository,
        profiles: PlayerProfileRepository,
        photos: PhotoStorage,
    ) -> None:
        self._users = users
        self._profiles = profiles
        self._photos = photos

    async def identities_for(
        self, player_ids: Collection[UUID]
    ) -> Mapping[UUID, CardIdentity]:
        """Each of these players' name, first photo and that photo's verdict.

        **The name is what decides whether there is a card at all.** A player
        ``users`` has never heard of — or has not named, which the entry gate
        keeps off every surface a search reaches (``docs/adr/0171`` §4) — is
        absent from the answer rather than present with a blank name, and the
        caller drops the row before the record is written so that
        ``n_returned`` and the rows stored still agree. The nickname ``users``
        answers beside the name is left here: a handle is drawn on a record,
        never on a card.

        A missing *photo*, by contrast, is an ordinary state: the card is drawn
        and the client draws the generated court poster. So is a missing
        *verdict*, and for one more reason than a missing photo has — the photo
        may have arrived while the checker could not be reached, or before it
        existed at all (``docs/adr/0138``).
        """

        if not player_ids:
            return {}
        namings = await self._users.find_namings_of(player_ids)

        # **One after another, because they share the request's session.** An
        # `AsyncSession` is not safe to use concurrently, and a profile is folded
        # from a stream through it — so gathering these would be a race, not a
        # speed-up.
        photos = {
            player_id: await self._first_photo(player_id) for player_id in namings
        }

        # **All at once, because these share nothing.** Every `PhotoStorage`
        # method builds its own client and holds no session, so a shortlist's
        # verdicts are independent round trips — and serialising twenty of them
        # would put twenty store latencies end to end inside one search
        # (``docs/adr/0138``). The asymmetry with the line above is the whole
        # reason the two loops are written apart rather than as one.
        refs = [
            PhotoRef(owner_id=player_id, photo_id=photo_id)
            for player_id, photo_id in photos.items()
            if photo_id is not None
        ]
        verdicts = dict(
            zip(
                (ref.owner_id for ref in refs),
                await gather(*(self._photos.review_decision(ref) for ref in refs)),
                # `gather` answers in the order it was handed, one per awaitable,
                # so a length mismatch here would be the event loop having lost
                # an answer rather than a shape this code can produce.
                strict=True,
            )
        )

        return {
            player_id: CardIdentity(
                name=naming.name,
                photo_id=photos[player_id],
                review=verdicts.get(player_id),
            )
            for player_id, naming in namings.items()
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
