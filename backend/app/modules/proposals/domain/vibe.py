"""A For-fun table's **Social vibe**, as Proposals asks it (``docs/adr/0207``
§2, #830): the people at the table, and the tags each holds now.

**One rule, borrowed twice and kept nowhere.** The tags that don't count are
the Player profile's, beside its vocabulary (``counted``), and the arithmetic
is the Match Fit engine's (``social_vibe``); this is only where Proposals hands
one to the other, so the deck, the details, the Friends card and Post a game's
fits all ask the same question in the same words. Nothing is stored: it is
worked out from the current tags on every read.

**The table is whoever the caller names** — on a card, everybody on the
reader's version: the people In, the reader and the names dealt. An empty seat
is nobody, so it is not at the table. Somebody whose tags aren't known carries
none: they share nothing, and they are still one of the others a tag could be
carried by.
"""

from __future__ import annotations

from collections.abc import Collection, Iterable, Mapping
from fractions import Fraction
from uuid import UUID

from app.engines.matchfit.v1 import social_vibe, social_vibe_share
from app.modules.player_profile.domain.social_tags import SocialTag, counted


def social_vibe_of(
    table: Iterable[UUID], tags: Mapping[UUID, Collection[SocialTag]]
) -> int | None:
    """The whole percent a card shows for these people at one table — ``None``
    with fewer than two of them, when nothing is drawn."""

    return social_vibe([counted(tags.get(player, ())) for player in table])


def social_vibe_share_of(
    table: Iterable[UUID], tags: Mapping[UUID, Collection[SocialTag]]
) -> Fraction | None:
    """The same table's vibe **exact, before it is rounded** — what For fun
    ranks tables by when it builds them (``docs/adr/0207`` §1, #831), so two
    tables a card would print alike are still told apart."""

    return social_vibe_share([counted(tags.get(player, ())) for player in table])
