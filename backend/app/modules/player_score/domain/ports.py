"""What this context publishes outward, and the three reads it lives on.

**One port out, and no port in.** ``player_score`` writes nothing and stores
nothing, so there is no repository here and never will be one. What it owns is an
*arithmetic over other people's records*, and the three facts it folds are read
through their own contexts' published ports — ``games``' ``GameHistoryQuery``,
twice, and ``challenges``' ``ChallengeHistoryQuery`` — rather than through a
query written here. A ``select`` over ``event_store`` on this side would make
this context a second reader of two other schemas and a second author of what *a
ghost* means.

**Why it is not called ``PlayerScoreQuery``.** The matcher already declares a port
of that name — its *demand*, in its own vocabulary, answered by an adapter on its
side of the arrow. This is the *publication*, in this context's vocabulary, and
the two are different shapes. A shared word over two different shapes is what
renamed ``Standing`` on the contract when ``games`` arrived (``docs/adr/0137``);
the rule that came out of it is that **the cost of a shared word is paid by
whoever arrives second**, and here that is this context.
"""

from __future__ import annotations

from typing import Collection, Mapping, Protocol, runtime_checkable
from uuid import UUID

from app.kernel import Instant
from app.modules.player_score.domain.strands import PlayerScore


@runtime_checkable
class PublishedScoreQuery(Protocol):
    """Each of these players' Player Score, **for those that have one.**

    **A player with no record is absent from the answer** — not a zero and not a
    neutral half. That is the one rule this port exists to keep: nobody has
    failed to turn up who was never due to, and the day this read starts
    answering ``0`` about a stranger is the day *no record* becomes *a bad
    record* everywhere downstream at once.

    **One call for the whole set, never one per player.** The matcher asks it
    once per search over every candidate still standing, which is five hundred
    people on a busy one; a per-row read behind this port would be fifteen
    hundred walks of two event logs inside one request. The player record asks about
    **one** person and is served by the same method with a collection of one —
    the narrowing lives in that context's adapter, because the shape a port takes
    belongs to the caller that could not afford another one.

    **It takes the clock rather than reading one.** Every part of the answer is a
    fact about an instant — a plan is a ghost only once its entry window has
    closed, a seat has lapsed only once its day has run out, a score is ignored
    only once its window has — so a caller asking about attendance and about
    answering in one request must get one instant's answer to all of it. The
    instant is also what the one **window** here is measured back from
    (``docs/adr/0156``), so two clocks would be two horizons.
    """

    async def scores_for(
        self, player_ids: Collection[UUID], *, now: Instant
    ) -> Mapping[UUID, PlayerScore]:
        """The Player Score of each of these people who has one.

        Answers only about ids it was asked about, and volunteers nobody.
        """
        ...


__all__ = ["PublishedScoreQuery"]
