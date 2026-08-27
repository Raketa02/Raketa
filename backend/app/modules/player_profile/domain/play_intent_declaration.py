"""The PlayIntentDeclaration aggregate — event-sourced, keyed by (player, sport).

**The second aggregate in the Player profile context, and it is per sport where
the profile deliberately is not.** ``docs/adr/0094`` settles that split and it is
worth restating here, because *put it on the profile* is the obvious thing and it
was rejected on an argument that is not obvious.

``PlayerProfile`` is the first aggregate in the racket-sport domain without a
sport dimension (ADR-0089), and a ``Mapping[Sport, PlayIntent]`` field would have
been the first per-sport fact on it — a precedent set to save one aggregate. What
decides it, though, is ordering. Onboarding's second part is **one** client-held
draft committed at the end (ADR-0090), so a profile does not exist until every
rating already does; put intent on the profile and it can only be asked in part
two, which welds *the sports I have an intent for* to *the sports I had rated the
day I finished onboarding*. A sport rated afterwards could never acquire one.
Here the coverage rule is exactly **you have an intent for every sport you have a
level in**, and it has a floor and a lid.

**One stream per pair, and never one stream per player folding to a mapping.**
That alternative was rejected too: it would put two sports' declarations on one
stream, contending on one version, and give *something* in the system a reason to
hold two sports at once. *Levels never transfer between sports, and intent does
not either* is then structural — no object holds two sports' intent, so there is
nothing to transfer.

**It is not in the rating context**, whose founding rule is *a level is proved,
never declared*. Putting the platform's one declared per-sport fact inside it
invites exactly the conflation that rule exists to prevent.

**A declaration that changes nothing records nothing.** Intent is a preference,
not a consent: there is no wording to evidence it against, which is precisely
what makes ``ProposalsOptInAnswered`` the profile's exception and this not one.
Re-declaring ``COMPETITIVE`` over ``COMPETITIVE`` from a different surface is
still the same answer, and a stream that grew an event for it would be recording
that a player did not do anything.

**Nothing writes one yet.** ADR-0094 puts the write path at
``PUT /api/v1/play-intents/{sport}``, unkeyed — the resource is one player's
intent in one sport, the same request twice lands the same state, and the no-op
rule means the second appends nothing — with the rating tail as the required
first surface and the search screen as the edit surface. That endpoint, the tail
prompt and the drift detector are ADR-0094's build and are not here; what is here
is the aggregate and its durable contract, so that when they arrive they append
to a stream whose shape was decided once.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable
from uuid import UUID

from app.kernel import Instant, Sport, instant
from app.modules.player_profile.domain.events import PlayIntentDeclared
from app.modules.player_profile.domain.ids import play_intent_declaration_id
from app.modules.player_profile.domain.play_intent import PlayIntent, PlayIntentSurface
from app.shared.domain import DomainEvent
from app.shared.domain.events import EventRecorder


@dataclass
class PlayIntentDeclaration:
    """One player's declared intent, in one sport, rebuilt by folding its stream."""

    player_id: UUID
    sport: Sport
    intent: PlayIntent
    #: Where the *standing* declaration was made. The history of surfaces is the
    #: stream; nothing accumulates a list here, for the reason the profile's
    #: consent answer does not.
    surface: PlayIntentSurface
    declared_at: Instant
    updated_at: Instant
    version: int = 0
    _events: EventRecorder = field(
        default_factory=EventRecorder, init=False, repr=False, compare=False
    )

    @property
    def id(self) -> UUID:
        """The stream id, derived from the pair rather than carried on the event.

        ``(player, sport)`` **is** the identity, so the id is a function of it
        (``ids.py``) and there is nothing to store. An id on the event would be a
        second copy of one fact and a second place for it to disagree — and it is
        the copy that would be believed, because it is the one the row holds.
        """

        return play_intent_declaration_id(self.player_id, self.sport)

    def pull_events(self) -> list[DomainEvent]:
        return self._events.pull()

    @classmethod
    def from_history(cls, events: Iterable[DomainEvent]) -> "PlayIntentDeclaration":
        declaration = cls._empty()
        for event in events:
            declaration._apply(event)
        return declaration

    @classmethod
    def _empty(cls) -> "PlayIntentDeclaration":
        declaration = cls.__new__(cls)
        declaration.version = 0
        declaration._events = EventRecorder()
        return declaration

    @classmethod
    def first_declared(
        cls,
        *,
        player_id: UUID,
        sport: Sport,
        intent: PlayIntent,
        surface: PlayIntentSurface,
        occurred_at: Instant,
    ) -> "PlayIntentDeclaration":
        """Open the stream for a pair that has never declared.

        Two of these racing compute the same stream id and collide on version 1,
        and the store rejects the loser (``ids.py``) — which is the same trade
        the assessment's deterministic id makes, and the reason the id is derived
        rather than minted.
        """

        declaration = cls._empty()
        declaration._record_that(
            PlayIntentDeclared(
                player_id=player_id,
                sport=sport.value,
                intent=intent.value,
                surface=surface.value,
                occurred_at=occurred_at,
            )
        )
        return declaration

    def declare(
        self,
        intent: PlayIntent,
        *,
        surface: PlayIntentSurface,
        occurred_at: Instant,
    ) -> None:
        """Record a change of mind. **A no-op when the value has not moved.**

        The surface is deliberately not part of that comparison. *The same
        answer, given again, from a different screen* is not a new fact about
        what kind of game this player wants — it is only a fact about where they
        were standing, and nothing branches on that.
        """

        if intent == self.intent:
            return
        self._record_that(
            PlayIntentDeclared(
                player_id=self.player_id,
                sport=self.sport.value,
                intent=intent.value,
                surface=surface.value,
                occurred_at=occurred_at,
            )
        )

    def _record_that(self, event: DomainEvent) -> None:
        self._apply(event)
        self._events.record(event)

    def _apply(self, event: DomainEvent) -> None:
        if isinstance(event, PlayIntentDeclared):
            self.player_id = event.player_id
            self.sport = Sport(event.sport)
            self.intent = PlayIntent(event.intent)
            self.surface = PlayIntentSurface(event.surface)
            if self.version == 0:
                self.declared_at = instant(event.occurred_at)
            self._touch(event.occurred_at)
            return
        raise TypeError(f"Unsupported play intent event {event!r}")

    def _touch(self, occurred_at: datetime) -> None:
        self.updated_at = instant(occurred_at)
        self.version += 1
