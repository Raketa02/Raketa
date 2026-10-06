"""Declare what kind of game a player wants, in one sport.

**ADR-0094's write path, finally built.** The aggregate and its durable contract
have shipped since that record was accepted and nothing wrote one: the rating
tail, the search screen's inline offer and the drift prompt all end at this use
case, and each says which of them it was through ``surface``.

**Open or append, decided by one question.** A pair that has never declared has
no stream, so ``load`` answering ``None`` is what separates ``first_declared``
from ``declare`` — the same shape ``BlockPlayer`` has, and for the same reason:
the stream id is a pure function of the pair, so two concurrent first
declarations collide on version 1 and the store rejects the loser rather than
quietly opening a second stream (``domain/ids.py``).

**A declaration that changes nothing records nothing**, including one made from a
different screen. Intent is a preference: re-declaring the same value says
nothing the previous answer did not. The aggregate holds that rule; this use
case saves either way and the repository is a no-op with nothing pending.

**It does not require a profile, and that is not an oversight.** Intent is asked
for at a rating run's tail, which happens in onboarding's *first* part — a
profile does not exist until every rating already does (``docs/adr/0090``), so a
declaration with no profile behind it is the ordinary first case. Nor is a rating
re-checked here: *you have an intent for every sport you have a level in* is a
coverage rule the tail satisfies by construction, and the search is where an
undeclared searcher is gated, with ``play_intent_not_declared``.
"""

from __future__ import annotations

from app.application.ports import UnitOfWork
from app.kernel import Clock, instant
from app.modules.player_profile.application.commands import (
    DeclarePlayIntentCommand,
)
from app.modules.player_profile.domain.play_intent_declaration import (
    PlayIntentDeclaration,
)
from app.modules.player_profile.domain.ports import (
    PlayIntentDeclarationRepository,
)


class DeclarePlayIntent:
    def __init__(
        self,
        *,
        declarations: PlayIntentDeclarationRepository,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._declarations = declarations
        self._uow = uow
        self._clock = clock

    async def execute(self, command: DeclarePlayIntentCommand) -> PlayIntentDeclaration:
        at = instant(self._clock.now())
        declaration = await self._declarations.load(
            player_id=command.player_id, sport=command.sport
        )
        if declaration is None:
            declaration = PlayIntentDeclaration.first_declared(
                player_id=command.player_id,
                sport=command.sport,
                intent=command.intent,
                surface=command.surface,
                occurred_at=at,
            )
        else:
            declaration.declare(command.intent, surface=command.surface, occurred_at=at)

        await self._declarations.save(declaration)
        await self._uow.commit()
        return declaration
