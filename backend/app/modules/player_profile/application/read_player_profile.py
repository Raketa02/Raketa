"""The profile surface the Play screens read: a week, a radius and a declaration.

**One read across two aggregates**, which is the cheaper half of a precedent
already accepted: ADR-0090 put ``has_player_profile`` on ``GET /users/me`` across
a **context** boundary, because *"onboarding's entry gate reads it on every cold
launch and two round trips is two things that can fail on a bad connection."*
Two aggregates inside one context is strictly less than that.

**A screen-shaped read was refused.** A ``GET /play-screen`` would make the second
surface that wants a radius add a second endpoint, and the radius already has
three readers on the Play screens alone.

**The fourth fact a screen needs is not here.** *Which sports am I rated in* is
``GET /api/v1/ratings``, already served, and re-serving it would be this context
answering the rating context's question.

**The declaration is a map of what was declared.** ADR-0094 forbids a nullable
intent, and a row saying ``{sport, intent: null}`` would walk that back in
through the encoding rather than through the value — so an undeclared sport is
**absent** and the client's *rated but undeclared* is a set difference against
the ratings it is already fetching, which is a comparison ADR-0021 permits.

**Four sports, four direct stream reads, and no scan.** The declaration's stream
id is a pure function of ``(player, sport)``, so *has this player declared in this
sport* is a primary-key read rather than a query over their sports — which is
what the deterministic id buys and why asking it four times is affordable. It is
sequential rather than gathered because the four reads share one session, and a
session is not something two coroutines may use at once.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping
from uuid import UUID

from app.kernel import Sport
from app.modules.player_profile.domain.errors import PlayerProfileNotFound
from app.modules.player_profile.domain.play_intent import PlayIntent
from app.modules.player_profile.domain.ports import (
    PlayerProfileRepository,
    PlayIntentDeclarationRepository,
)
from app.modules.player_profile.domain.profile import PlayerProfile


@dataclass(frozen=True, slots=True)
class PlayerProfileSurface:
    """What one player's screens read: the profile, and what they declared.

    Two objects rather than a flattened bag, because they are two aggregates and
    the boundary is what decides which of each one's fields cross. The
    **withholding is the response's job**, not this one's: an application layer
    that pre-trimmed the profile would make *what Play sees* a fact about a use
    case rather than about a contract, and the deferred fields land on the same
    route when *You* is built.
    """

    profile: PlayerProfile
    #: Only the sports this player has declared in. Absence is *undeclared*, and
    #: there is deliberately no key with a null behind it.
    play_intents: Mapping[Sport, PlayIntent]


class ReadPlayerProfile:
    def __init__(
        self,
        *,
        profiles: PlayerProfileRepository,
        declarations: PlayIntentDeclarationRepository,
    ) -> None:
        self._profiles = profiles
        self._declarations = declarations

    async def execute(self, player_id: UUID) -> PlayerProfileSurface:
        profile = await self._profiles.load(player_id)
        if profile is None:
            raise PlayerProfileNotFound()

        declared: dict[Sport, PlayIntent] = {}
        for sport in Sport:
            declaration = await self._declarations.load(
                player_id=player_id, sport=sport
            )
            if declaration is not None:
                declared[sport] = declaration.intent

        return PlayerProfileSurface(profile=profile, play_intents=declared)
