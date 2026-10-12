"""What this context publishes outward, and the two reads it lives on.

**One port out, and no port in.** ``player_score`` writes nothing and stores
nothing, so there is no repository here and never will be one. What it owns is an
*arithmetic over other people's records* (``domain/points.py``), and the lines it
folds are read through their own contexts' published ports — ``games``'
``GameHistoryQuery`` and ``bookings``' ``BookingHistoryQuery`` (#544, #659) —
rather than through a query written here. A ``select`` over ``event_store`` on
this side would make this context a second reader of two other schemas and a
second author of what *Didn't come* and *a broken booked game* mean.

**Why it is not called ``PlayerScoreQuery``.** The matcher declared a port of
that name — its *demand*, in its own vocabulary, answered by an adapter on its
side of the arrow — until the searches that read it went (#579). This is the
*publication*, in this context's vocabulary, and the two were different shapes.
A shared word over two different shapes is what renamed ``Standing`` on the
contract when ``games`` arrived (``docs/adr/0137``); the rule that came out of
it is that **the cost of a shared word is paid by whoever arrives second**, and
here that is this context.
"""

from __future__ import annotations

from typing import Collection, Mapping, Protocol, runtime_checkable
from uuid import UUID

from app.kernel import Instant
from app.modules.player_score.domain.points import PlayerScore


@runtime_checkable
class PublishedScoreQuery(Protocol):
    """Each of these players' reliability — the figure, *New* and the counts.

    **Everybody asked is answered** (``docs/adr/0195`` §1): everyone starts at a
    hundred, so a player nothing has happened to reads *100 · New* with every
    count at nought, and nobody is left out of the answer. It answers only about
    the ids it was asked about, and volunteers nobody.

    **One call for the whole set, never one per player.** A group's Members list
    asks about every member it draws, and the reliability filter will ask about
    every member of a deal (#661); a per-row read behind this port would be one
    walk of two event logs per person inside one request. The player record asks
    about **one** person and is served by the same method with a collection of
    one — the narrowing lives in that context's adapter, because the shape a
    port takes belongs to the caller that could not afford another one.

    **It takes the clock rather than reading one.** Every line is a fact about
    an instant — a game is played through only once somebody says so or its
    entry window has closed, a booked game is kept only once its hour has come,
    a line drops out six months after it happened — so one request must get one
    instant's answer to all of it.
    """

    async def scores_for(
        self, player_ids: Collection[UUID], *, now: Instant
    ) -> Mapping[UUID, PlayerScore]:
        """The reliability of each of these people, every one of them."""
        ...


__all__ = ["PublishedScoreQuery"]
