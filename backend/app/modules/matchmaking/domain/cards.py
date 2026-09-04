"""The player card — assembled **outside** the engine, from a closed list.

``docs/adr/0107``. A ``ScorableCandidate`` has no name, no photo, no gender, no
birthdate and no precise location, so the response can name a player and say
nothing whatever about who they are. The card is the second author on a returned
row — the same seam ``at_stake`` rides — attached by the backend after
``matchfit`` returns, over the twenty rows that survived rather than over the
pool.

**The list is closed, and two of its absences are permanent refusals rather than
gaps.**

*No bio, and no free-text field of any kind.* It would be the platform's first
player-authored text shown to strangers, which is a moderation surface, and the
full moderation story is out of scope beyond the block.

*No activity recency, at any granularity* — not a timestamp, not *active today*,
not a green dot. That is row three of the Liveness table, and Liveness reaches a
screen the one way it is sanctioned to: as a reason **code**. *"Last seen 2 hours
ago"* is a presence indicator, and this product does not have one.

**A photo id in the record, and a URL on the response.** Photos are served
through short-lived presigned links and a search record is kept forever, so a URL
written into one is a dead link within the hour. The record stores the id; the
response carries ``photo_url`` beside it, minted per response by
:class:`CardPhotoLinks` and written down nowhere.

**And the on-court verdict beside the id, recorded rather than minted**
(``docs/adr/0138``). It goes the other way from the URL and for the mirror
reason: a link is dead within the hour so it cannot be stored, and a verdict is
one store round trip per row so it must not be re-read on every read-back. Both
are facts about the *photograph* rather than about the player, and neither may be
derived by a client — a shield says *checked and passed*, and only a decision the
stored note proves earns one.

**A nickname, and nothing may shorten it.** ``users`` holds no real name and no
given name. Every sentence naming somebody uses the whole handle or names
nobody — the prototype's ``split(' ')[0]`` has nothing behind it here, and
inventing a first name is the product addressing a person by a name they never
gave it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Collection, Mapping, Protocol, final, runtime_checkable
from uuid import UUID

from app.modules.matchmaking.domain.searches import SearchCandidateRecord
from app.modules.player_profile.domain.photos import PhotoReviewDecision


@final
@dataclass(frozen=True, slots=True)
class CardIdentity:
    """The three card fields the candidate index deliberately does not hold.

    Everything else on a card — the area, the tags, the Level and its band — is
    already on the index row, because those are facts a player changes about
    themselves. These three are absent for two reasons, both deliberate: a
    nickname belongs to ``users``, which the index does not tail at all, and
    **no photo fact reaches the index** by ``docs/adr/0107``'s rule that the card
    is assembled outside the engine — which covers the id and the verdict alike.
    """

    nickname: str
    #: The **first** photo, which is the one a card shows: order is meaning in a
    #: player's photo list. ``None`` when they have none, and the client draws
    #: the generated court poster rather than a placeholder for a missing image.
    photo_id: UUID | None
    #: What the on-court check concluded about **that** photograph, or ``None``
    #: for *nobody looked* (``docs/adr/0138``).
    #:
    #: **The third state is the point of the field.** A shield drawn on ``None``
    #: would claim a check happened on every photo the platform holds from
    #: before ADR-0129, and on every one that arrived while the sidecar was
    #: down. Only a decision the stored note proves crosses; the note itself
    #: never does, on any route, in any shape.
    #:
    #: It travels with `photo_id` and is meaningless without it: this is a fact
    #: about *that* photograph, not about the player.
    review: PhotoReviewDecision | None


@runtime_checkable
class PlayerCardSource(Protocol):
    """Where the three non-index card fields come from.

    **One call for the whole shortlist, never one call per row** — the shape
    every set read in this module has. What that call costs *behind* the port is
    the adapter's business and is not promised here: the one this repository has
    pays a set read for the nicknames, a profile per surviving row and, for a row
    with a photograph, an object-store ``HEAD`` for its verdict
    (``docs/adr/0138``). It is read *after* the floor, so all of that is bounded
    by twenty players even when the pool is five hundred — which is what makes a
    per-row price affordable rather than merely tolerated.
    """

    async def identities_for(
        self, player_ids: Collection[UUID]
    ) -> Mapping[UUID, CardIdentity]:
        """Each of these players' nickname, first photo and that photo's verdict.

        A player absent from the answer is one ``users`` has never heard of. A
        row whose card cannot be assembled is **dropped from the response**
        rather than shown with a blank name: a card with no nickname is not a
        card, and the search is still a `200` with one fewer row.

        **A missing verdict is never a missing card.** It is the ordinary state
        of every photograph nothing has looked at, and of every player who has no
        photograph at all — the row is answered, and the shield is what goes
        absent (``docs/adr/0138``).
        """
        ...


@runtime_checkable
class CardPhotoLinks(Protocol):
    """Where a card's photograph gets an address. **Per response, never stored.**

    The record keeps the id and this mints the link over it — the one difference
    the round trip allows itself, on the ``POST`` and again on every ``GET``
    (``docs/adr/0107``, ``docs/adr/0109``).

    **The client cannot mint one itself, and that is why this exists.**
    ``GET /photos/{id}`` signs only the asking player's own photos and refuses a
    stranger's id deliberately — the alternative is an endpoint that confirms
    whether a stranger's id is real. A card's photo is by definition another
    player's, so the server that disclosed the person hands over their
    photograph with them rather than leaving the client an id it can do nothing
    with.
    """

    async def links_for(
        self, rows: Collection[SearchCandidateRecord]
    ) -> Mapping[UUID, str]:
        """A short-lived URL for each of these rows that recorded a photo.

        **Keyed by player**, because a row is what the renderer holds and a
        photo id is what the record holds. A row whose card has no photo is
        **absent from the answer** rather than present as ``None``: the field is
        omitted on the wire and the client draws the generated court poster.

        One call for the whole list, never one per row — the shape every set
        read in this module has.
        """
        ...
