"""The Player profile context's domain events — one stream, keyed on the player.

Events carry **primitive** fields, so their wire format survives any later
refactor of the Python types: a tag as its ``str`` id, a photo as its ``str``
uuid, an availability slot as its code, a location as two floats. Nothing here
holds a value object, and nothing here holds display text.

Seven events, and they fall into three kinds.

**One creation.** ``PlayerProfileCreated`` is the single commit that ends
onboarding's second part, carrying every preference at once (``docs/adr/0089``).
It also carries the **idempotency key** the commit was made under — which is what
lets the same request arriving twice be recognised as the same request without a
table beside the stream to keep in step with it. The key is evidence about a
*write*, not about the player, and it is on the creating event only.

**Five preference changes**, for the profile screen that edits the same values
later: tags, photos, availability, location and radius. Each carries the whole
new value rather than a delta, because a preference is small, replay stays a
fold, and *what was it before* is answered by the event before it.

**One consent answer.** ``ProposalsOptInAnswered`` carries the answer, the copy
version shown and the surface — and its own ``occurred_at`` is the moment. It is
appended by the creating commit **as well as** by every later change, so the
consent history is one sequence with no special first case: a reader that wants
every answer a player ever gave replays this one event type and needs to know
nothing about how the profile began.

**Adding a field to ``ProposalsOptInAnswered`` means a new catalog version.**
Events are a published contract, and this is the event most likely to be asked to
carry more later — a jurisdiction, a policy id, the surface's own version. The
existing rows must keep decoding, which is what the version is for.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class PlayerProfileCreated:
    """Every preference from onboarding's second part, in one event.

    The opt-in is **not** here: it arrives as its own
    ``ProposalsOptInAnswered`` appended immediately after, in the same
    transaction. That is deliberate and is what "one sequence with no special
    first case" means — the alternative puts the first consent answer in a
    different shape from every one that follows it, and every reader of the
    consent history then has two shapes to handle forever.
    """

    player_id: UUID
    social_tags: tuple[str, ...]
    photo_ids: tuple[str, ...]
    #: Availability slots as ``AvailabilitySlot.code`` writes them. Empty is a
    #: real answer — *no preference* — and never an absent one.
    availability: tuple[str, ...]
    latitude: float
    longitude: float
    search_radius_km: int
    #: What the client called this commit. Recorded so a retry of the same
    #: request is answerable from the stream itself.
    idempotency_key: str
    occurred_at: datetime

    def __post_init__(self) -> None:
        _retuple(self, "social_tags", "photo_ids", "availability")


@dataclass(frozen=True)
class SocialTagsChanged:
    player_id: UUID
    social_tags: tuple[str, ...]
    occurred_at: datetime

    def __post_init__(self) -> None:
        _retuple(self, "social_tags")


@dataclass(frozen=True)
class PhotosChanged:
    """The whole photo list, in its new order.

    Order is meaning here: the first photo is the one a player card shows, so
    re-ordering three photos is a change even though the set is the same.
    """

    player_id: UUID
    photo_ids: tuple[str, ...]
    occurred_at: datetime

    def __post_init__(self) -> None:
        _retuple(self, "photo_ids")


@dataclass(frozen=True)
class AvailabilityChanged:
    player_id: UUID
    availability: tuple[str, ...]
    occurred_at: datetime

    def __post_init__(self) -> None:
        _retuple(self, "availability")


@dataclass(frozen=True)
class LocationChanged:
    """The coarse area, and only ever the coarse area.

    The precise fix that produced it never reaches an event — it is discarded at
    the boundary by ``LocationArea.around``, so there is no version of this
    stream from which one could be recovered.
    """

    player_id: UUID
    latitude: float
    longitude: float
    occurred_at: datetime


@dataclass(frozen=True)
class SearchRadiusChanged:
    player_id: UUID
    search_radius_km: int
    occurred_at: datetime


@dataclass(frozen=True)
class ProposalsOptInAnswered:
    """One answer to the proposals question, with what makes it evidence.

    ``occurred_at`` is the moment, carried the way every event carries its
    moment rather than as a second field somebody has to keep in step with it.
    ``copy_version`` identifies the words shown — never the words themselves,
    because freezing copy in history is how a wording change becomes a
    migration.

    **Recorded every time it is answered, including when the answer has not
    changed.** That is the one place this stream departs from the preference
    events above, which are no-ops when nothing moved: *the player was asked
    again, against these words, and said yes again* is a fact about consent, and
    a consent log that drops re-affirmations cannot evidence one.
    """

    player_id: UUID
    accepted: bool
    copy_version: str
    surface: str
    occurred_at: datetime


def _retuple(event: object, *fields: str) -> None:
    """Force a collection field to a tuple, on the way in and out of storage.

    The codec encodes a tuple as a JSON array and decodes it back as a ``list``,
    so without this an event that has been through the store is unequal to the
    event that was appended — and a replay would fold lists where the first pass
    folded tuples. Frozen dataclasses are assigned through ``object`` for the
    same reason ``__post_init__`` normalisation always is.
    """

    for field in fields:
        object.__setattr__(event, field, tuple(getattr(event, field)))
