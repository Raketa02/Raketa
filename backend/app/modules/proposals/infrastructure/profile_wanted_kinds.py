"""``WantedKinds`` over the Player profile's own Play intent declarations.

A deck's segments follow the player's intent for the sport (the mechanics §3,
§4.1): *competitive* shows the Competitive segment, *for fun* the For fun one,
and **no preference** — the app's *Either* — both. This is the deck's reading of
a declaration and neither of the two already written: the matcher's
``mode_for_intent`` picks one weight vector for a search and lets *no
preference* inherit the fun ruler, and ``challenges``' friendly choice honours a
stated wish for one game. A group deck shows kinds, and *either* is both.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.engines.matchfit.core import SearchMode
from app.kernel import Sport, exhaustive
from app.modules.player_profile.domain.play_intent import PlayIntent
from app.modules.player_profile.domain.ports import PlayIntentDeclarationRepository


@final
class ProfileWantedKinds:
    def __init__(self, declarations: PlayIntentDeclarationRepository) -> None:
        self._declarations = declarations

    async def of(
        self, player_id: UUID, *, sport: Sport
    ) -> frozenset[SearchMode] | None:
        declaration = await self._declarations.load(player_id=player_id, sport=sport)
        if declaration is None:
            return None
        match declaration.intent:
            case PlayIntent.COMPETITIVE:
                return frozenset({SearchMode.COMPETITIVE})
            case PlayIntent.FOR_FUN:
                return frozenset({SearchMode.FOR_FUN})
            case PlayIntent.NO_PREFERENCE:
                return frozenset(SearchMode)
            case _:
                exhaustive(declaration.intent)
