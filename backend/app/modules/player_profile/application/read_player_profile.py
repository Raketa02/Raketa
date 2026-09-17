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

**The third read is the store's, and it is the one that costs a round trip per
photograph.** The You tab draws each photo with the verdict its uploader is owed
(``docs/adr/0179`` §8) — the three-valued reading ``docs/adr/0138`` unfolded:
passed, flagged, *nobody looked* — and that verdict is user metadata on the
object, which no listing carries and no presign reads, so it is one ``HEAD`` per
photograph. ``GET /photos/{id}`` refuses to pay it on every tile restored
(``docs/adr/0133``); this read pays it once, for at most the three photographs a
profile may hold, on the one screen whose whole question is *what did the check
say about mine*. A profile holding none asks the store nothing. Unlike the four
declaration reads these **are** gathered, on the port's own promise that one
``review_decision`` shares nothing with the next — which is how the card source
pays for the same answer over twenty rows.
"""

from __future__ import annotations

from asyncio import gather
from dataclasses import dataclass
from typing import Mapping
from uuid import UUID

from app.kernel import Sport
from app.modules.player_profile.domain.errors import PlayerProfileNotFound
from app.modules.player_profile.domain.photos import PhotoRef, PhotoReviewDecision
from app.modules.player_profile.domain.play_intent import PlayIntent
from app.modules.player_profile.domain.ports import (
    PhotoStorage,
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
    that pre-trimmed the profile would make *what the tab sees* a fact about a
    use case rather than about a contract — which is what let the deferred
    fields land on the same route when *You* was built (``docs/adr/0179`` §8)
    with one addition here, the store's answer about the photographs, and what
    keeps the location area off the wire today.
    """

    profile: PlayerProfile
    #: Only the sports this player has declared in. Absence is *undeclared*, and
    #: there is deliberately no key with a null behind it.
    play_intents: Mapping[Sport, PlayIntent]
    #: What the on-court check concluded about each of the profile's
    #: photographs, keyed by photo id — and **only the photographs something
    #: concluded about**. Absence is *nobody looked*, the same spelling as an
    #: undeclared sport above and for the same reason: ``PhotoReviewDecision``
    #: deliberately has no third value (``docs/adr/0138``), so a key with a null
    #: behind it would be inventing one. The order is the profile's own
    #: ``photo_ids``; this is the store's answer beside it, never a second list.
    photo_verdicts: Mapping[UUID, PhotoReviewDecision]


class ReadPlayerProfile:
    def __init__(
        self,
        *,
        profiles: PlayerProfileRepository,
        declarations: PlayIntentDeclarationRepository,
        photos: PhotoStorage,
    ) -> None:
        self._profiles = profiles
        self._declarations = declarations
        self._photos = photos

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

        # One `HEAD` per photograph the profile holds, and none for a profile
        # holding none. The owner is in the ref, so the store cannot be asked
        # about anybody else's photo here.
        refs = [
            PhotoRef(owner_id=player_id, photo_id=photo_id)
            for photo_id in profile.photo_ids
        ]
        decisions = await gather(*(self._photos.review_decision(ref) for ref in refs))
        verdicts = {
            ref.photo_id: decision
            for ref, decision in zip(refs, decisions, strict=True)
            if decision is not None
        }

        return PlayerProfileSurface(
            profile=profile, play_intents=declared, photo_verdicts=verdicts
        )
