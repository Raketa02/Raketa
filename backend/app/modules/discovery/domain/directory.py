"""The player directory: one entry per account, as the people rows read it
(``docs/adr/0204`` §10).

**A copy, never the record.** Every field is what an owner holds now — the
nickname ``users``', the rest the Player profile's — and an entry is written
whole each time either owner's event is delivered, by asking the owners again,
so a redelivery or an out-of-order delivery writes what the owners hold, and
the rebuild writes what live delivery did.

**An account plays once it holds a Player profile.** Club staff — an
administrator-only account, which an invitation opened — never commit one, so
they are in the directory and in no row. What only a player has rides on
:class:`PlayerFacts`, so an entry that plays and an entry with a profile are one
fact, not two that could disagree.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.kernel import Instant


@final
@dataclass(frozen=True, slots=True)
class Area:
    """The Location area's cell, as coarse as the profile holds it. **Never
    served**: a row may one day say how far, and never where."""

    latitude: float
    longitude: float


@final
@dataclass(frozen=True, slots=True)
class PlayerFacts:
    """What a player's profile says that a people row reads."""

    #: *Joined*: when sign-up finished — the profile commit that ends
    #: onboarding, the moment a **Newcomer**'s 14 days also run from (call 1).
    #: A player who committed before the directory existed keeps that date.
    joined_at: Instant
    #: The first photograph, the one every face draws; ``None`` draws the
    #: court poster.
    photo_id: UUID | None
    area: Area | None
    #: Every social tag the player holds, by its permanent id.
    tags: frozenset[str]
    #: *Show me to new people* (``docs/adr/0204`` §2): off takes the player out
    #: of every people row on everybody else's Home.
    open_to_new_people: bool


@final
@dataclass(frozen=True, slots=True)
class DirectoryEntry:
    """One account. ``player`` is ``None`` for an account that doesn't play."""

    player_id: UUID
    #: ``None`` before the naming, and for an account an invitation opened.
    nickname: str | None
    player: PlayerFacts | None

    @property
    def plays(self) -> bool:
        return self.player is not None
