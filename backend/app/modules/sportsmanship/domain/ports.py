"""What this context stores behind, and the one thing it reads elsewhere.

**Two ports, and the interesting one is what neither of them can express.**

``SportsmanshipLedger`` is this module's own store, and it has no method that
answers *what did somebody say about me*, or *what did I say about them*. That is
the same shape ``InterestLedger`` takes and for a stronger reason: an inbox there
was merely a query nobody wanted, and here an individual rating reaching anybody
is the failure the whole design is built to prevent. *No individual rating is
returned to anybody, on any route, in any shape* is a rule about routes only
while a route could get one — so the port does not offer one, and a route that
wanted to leak one would have to grow a read first.

``SettledCourts`` is somebody else's, and it is one method wide. It asks
``games`` a single question — *is this a game of mine that is over, and who else
was on it* — and answers with the court or with nothing at all. What it does
**not** borrow is a card, a Level or a handle: a card is what a searcher reads to
decide about a game that might happen (``docs/adr/0141``), and this is a question
about an evening that already did. The names on the card are the client's to
draw from the games list it drew the card from.

**Absence has one spelling.** A game that does not exist, a game somebody else
played and a game whose result has not settled are all ``None`` — one answer,
because they have one remedy and because separating them would let a caller
answer *is this id real* about four strangers' evening.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable
from uuid import UUID

from app.kernel import Instant
from app.modules.sportsmanship.domain.card import SettledCourt, SportsmanshipCard


@runtime_checkable
class SettledCourts(Protocol):
    """The courts a player may be asked about. **``games``' answer, narrowed.**

    *Settled* is ``games``' word and it is narrowed here rather than borrowed
    whole: that context calls a plan nobody ever claimed settled too, and there
    is nobody to rate for an evening that did not happen. What this port means is
    **played and over** — the score is agreed, or the two sides disagreed and
    both windows closed. An unscored game is in: two people who cannot agree what
    the score was were still on a court together for two hours, and how that went
    is exactly what this context is for.
    """

    async def court_of(
        self, game_id: UUID, *, player_id: UUID, now: Instant
    ) -> SettledCourt | None:
        """This player's settled court for that game, or ``None``.

        ``now`` is passed rather than read, because *has it settled* is folded
        from the record and a clock (``docs/adr/0137``) and a port that read its
        own would be a second opinion about when a result became final.
        """
        ...


@runtime_checkable
class SportsmanshipLedger(Protocol):
    """The cards that have been answered, and the stars on them.

    **Two methods, and the second one commits nothing.** The transaction boundary
    is the use case's decision, exactly as it is for every durable ledger in the
    matcher: a card is written in the request that answered it, and a store that
    committed for itself would take that decision away from the one place that
    has to make it.
    """

    async def has_been_answered(self, *, game_id: UUID, rater_id: UUID) -> bool:
        """Whether this player has already answered this game's card.

        **The whole of what closes a card.** It is true of the all-blank card
        too, which is the point of storing the card apart from the stars on it:
        an explicit *I am not rating anyone* is an answer, and an answer that
        left no trace would be an invitation to come back and fill somebody in
        later.
        """
        ...

    async def record(self, card: SportsmanshipCard) -> None:
        """Write the card and its answers. **The caller commits.**

        **Each answer replaces this rater's previous one about that person**, so
        the collapse *only a rater's most recent rating counts* is the store's
        shape rather than a rule every future reader has to remember
        (``docs/adr/0154``). Two friends who partner every week give each other
        one opinion between them however many evenings they play, and the count
        beside the published figure keeps meaning *how many different people have
        an opinion*.
        """
        ...


__all__ = [
    "SettledCourts",
    "SportsmanshipLedger",
]
