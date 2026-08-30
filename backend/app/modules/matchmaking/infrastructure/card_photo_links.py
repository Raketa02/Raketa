"""The one thing on a response that is not in the record: the photo's address.

**It reads the provider's own port and never their bucket.** The rule its
neighbour ``player_card_source`` states holds here for the same reason: a key
template written in this module would make the matcher a second implementation of
where a photograph lives, and the two would disagree the day the layout changes.
``PhotoStorage`` takes a whole ``PhotoRef``, so ownership is part of the contract
rather than a check this caller has to remember.

**Signing is arithmetic, not a request.** Presigning is a signature over a
request that is never sent, so a whole shortlist costs **no round trips** — which
is what makes minting per response affordable at all, and it is the reason the
record can go on storing an id rather than a link that dies within the hour
(``docs/adr/0107``).

What it does cost is the store adapter's own shape: every ``PhotoStorage`` method
builds a client per call, so twenty links are twenty client constructions and no
network. That is the same price its neighbour ``player_card_source`` pays per row
and prices the same way — it is bounded by the shortlist rather than by the city,
it is the smaller half of what assembling a card already costs, and if it ever
stops being affordable the fix is a **batched signing method on the provider's
port**, not a client cached in this module over somebody else's session.

**And it never asks whether the object is still there.** ``GET /photos/{id}``
checks, because there the photograph *is* the response and a 404 is an answer the
client asked for. Here it would be twenty round trips before the response, to
turn a photo removed since into a poster — and the link expires in minutes in any
case, so a client that cannot survive an image failing to load is already broken
on the photograph it can see.
"""

from __future__ import annotations

from typing import Collection, Mapping
from uuid import UUID

from app.modules.matchmaking.domain.searches import SearchCandidateRecord
from app.modules.player_profile.domain.photos import PhotoRef
from app.modules.player_profile.domain.ports import PhotoStorage


class PresignedCardPhotos:
    """``CardPhotoLinks`` over the Player profile's photo store."""

    def __init__(self, *, storage: PhotoStorage, valid_for_minutes: int) -> None:
        self._storage = storage
        self._valid_for_minutes = valid_for_minutes

    async def links_for(
        self, rows: Collection[SearchCandidateRecord]
    ) -> Mapping[UUID, str]:
        """A link per row that recorded a photo, **signed as its own owner**.

        The owner is the person on the card and never the person looking: the
        store keys the whole ``PhotoRef``, so a link signed under the searcher's
        id would reach an object that does not exist.

        The window is the platform's one photo window, so a card and
        ``GET /photos/{id}`` cannot come to two answers about how long a link
        may live.
        """

        links: dict[UUID, str] = {}
        for row in rows:
            # A near miss records no card at all — it was shown to nobody — and
            # that is not the same state as a card whose player has no photo.
            # Neither has an address, so neither is in the answer.
            photo_id = None if row.card is None else row.card.photo_id
            if photo_id is None:
                continue
            links[row.player_id] = await self._storage.presigned_read_url(
                PhotoRef(owner_id=row.player_id, photo_id=photo_id),
                valid_for_seconds=self._valid_for_minutes * 60,
            )
        return links
