"""``FriendlyChoiceQuery`` over the declaration repository ``player_profile``
already publishes.

**It reads the provider's own port and never the provider's table.** A
``select`` over the event store filtered on the declaration's stream written
here would make ``challenges`` a second reader of somebody else's stream shape,
and ``player_profile`` owns both what a declaration is and how it is stored.
``PlayIntentDeclarationRepository.load`` is keyed on the pair ``(player, sport)``
exactly as the stream is, which is the one shape this question has.

**It translates three declarations and an absence into one word, and that is
the whole of it.** ``FOR_FUN`` is *chose a friendly*; ``COMPETITIVE``,
``NO_PREFERENCE`` and *never declared* are not, and the caller cannot tell
those three apart because nothing crosses but the subset. In particular
``NO_PREFERENCE`` is **not** read the way the matcher reads it
(``mode_for_intent``, where it inherits the fun ruler): that mapping picks a
weight vector for a search, this one honours a wish about somebody's evening,
and indifference is not a wish for a friendly.

**The port is bulk; this implementation of it is a walk, and the difference is
deliberate** — ``games_settled_game.py``'s shape exactly. The repository offers
one load and it is per pair, so the loop is here rather than in the caller: the
cost is one adapter's to pay and one adapter's to fix, and what it walks is a
mutual's two people.

**A read that cannot answer raises.** Nothing here catches, for the reason the
port gives: an empty answer would mint a counted game on a fact this call does
not have.
"""

from __future__ import annotations

from typing import Collection, final
from uuid import UUID

from app.kernel import Sport
from app.modules.player_profile.domain.play_intent import PlayIntent
from app.modules.player_profile.domain.ports import PlayIntentDeclarationRepository


@final
class ProfileFriendlyChoice:
    """*Which of these people declared* for fun *in this sport?*"""

    def __init__(self, declarations: PlayIntentDeclarationRepository) -> None:
        self._declarations = declarations

    async def chose_a_friendly_among(
        self, player_ids: Collection[UUID], *, sport: Sport
    ) -> frozenset[UUID]:
        chose: set[UUID] = set()
        # Sorted, so the reads happen in the same order on every process and
        # under every ``PYTHONHASHSEED`` (``docs/adr/0105``).
        for player_id in sorted(set(player_ids)):
            declaration = await self._declarations.load(
                player_id=player_id, sport=sport
            )
            if declaration is not None and declaration.intent is PlayIntent.FOR_FUN:
                chose.add(player_id)
        return frozenset(chose)
