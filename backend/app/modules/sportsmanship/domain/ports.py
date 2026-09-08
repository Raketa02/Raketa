"""What this context stores behind, what it reads elsewhere, and what it publishes.

**Three ports, and the interesting one is still what none of them can express.**

``SportsmanshipLedger`` is this module's own store, and it has no method that
answers *what did somebody say about me*, or *what did I say about them*. It
answers only *which of these cards are closed*, which is a fact about an act and
not about an opinion — the list read joins on it and the write path gates on it,
and neither can learn a star from it. That is
the same shape ``InterestLedger`` takes and for a stronger reason: an inbox there
was merely a query nobody wanted, and here an individual rating reaching anybody
is the failure the whole design is built to prevent. *No individual rating is
returned to anybody, on any route, in any shape* is a rule about routes only
while a route could get one — so the port does not offer one, and a route that
wanted to leak one would have to grow a read first.

``PublishedSportsmanshipQuery`` is the third and the only one pointed outward,
and it is where that rule is paid for rather than repeated. It answers **two
questions off one window** — the figure and its count for a reader, and a coarse
band for the subject — and the split is structural for the reason the ledger's
silence is: a published average plus a published count in front of the person it
is about is a *subtraction*, so the method the subject's sheet calls is a method
that cannot say the figure. Neither answer is an individual rating, which is what
lets this port exist at all beside the paragraph above.

``SettledCourts`` is somebody else's, and it asks ``games`` one question at two
arities — *which of my games are over, and who else was on each* — answering with
courts, or with a court, or with nothing at all. The two are not two questions:
the plural draws the list a player is offered and the singular is the gate on the
act, and both are *is this a settled court of mine*. What it does **not** borrow
is a card, a Level or a handle: a card is what a searcher reads to decide about a
game that might happen (``docs/adr/0141``), and this is a question about an
evening that already did. The names on the card are the client's to draw from the
games list it drew the card from.

**Absence has one spelling, at both arities.** A game that does not exist, a game
somebody else played and a game whose result has not settled are all ``None`` from
the singular and simply not in the plural's tuple — one answer, because they have
one remedy and because separating them would let a caller answer *is this id real*
about four strangers' evening.
"""

from __future__ import annotations

from typing import Collection, Protocol, runtime_checkable
from uuid import UUID

from app.kernel import Instant
from app.modules.sportsmanship.domain.card import SettledCourt, SportsmanshipCard
from app.modules.sportsmanship.domain.published import (
    PublishedSportsmanship,
    SportsmanshipBand,
)


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

    async def courts_of(
        self, player_id: UUID, *, now: Instant
    ) -> tuple[SettledCourt, ...]:
        """Every settled court this player was on, in no promised order.

        **The window is not applied here**, and that is the layering rather than
        an omission: *has this evening finished* is ``games``' fact and *may I be
        asked about it yet* is this context's rule, so the port answers the first
        and ``window.py`` answers the second. A port that filtered on the card's
        week would put this context's clock inside somebody else's answer, and the
        day the week changed there would be two places to look.

        **Order is the caller's to impose.** What comes back is a fold over
        streams, and a promise about its order here would be a promise the
        directory underneath does not make.
        """
        ...

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

    async def answered_among(
        self, *, rater_id: UUID, game_ids: Collection[UUID]
    ) -> frozenset[UUID]:
        """Which of these games this player has already answered the card for.

        **The whole of what closes a card.** A game is in the answer for the
        all-blank card too, which is the point of storing the card apart from the
        stars on it: an explicit *I am not rating anyone* is an answer, and an
        answer that left no trace would be an invitation to come back and fill
        somebody in later.

        **One method and not two.** The list read asks about a whole page of
        courts and the write path asks about the one it is about to close, and
        they are the same question — a singular spelling beside this one would be
        a second read of the same table, and the first of the two to be changed
        would win for whichever caller went through it.

        **A set and not a mapping**, because there is nothing else about a closed
        card a caller may have: not when it was answered, not how many people were
        on it, and least of all what was said.
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


@runtime_checkable
class PublishedSportsmanshipQuery(Protocol):
    """What other players said about somebody. **The one thing this context
    publishes outward, and it publishes two different answers.**

    **Why it is not a method on ``SportsmanshipLedger``.** That port is this
    module's own store and it answers *which of these cards are closed* — a fact
    about an act. This is the publication, in the vocabulary a reader is shown,
    and it is separate for the reason ``player_score`` separates its own
    (``docs/adr/0140``): a consumer holding the store could write through it, and
    a fold that a sheet reads has no business being reachable from a port a use
    case commits.

    **Two methods, and the second is not the first with a rounding on top.** A
    reader may be told the figure and the count; the subject may be told a coarse
    band and **nothing else**. Both come off one window, and the reason they are
    two methods rather than one answer a caller narrows is that a caller which
    received the figure has already been handed the thing the rule forbids —
    ``docs/adr/0154``'s subtraction is available to anybody holding an average
    and a count, whatever they choose to render. So the sheet about *you* calls
    a method that cannot say your figure.

    **Nothing here takes a clock.** The window is fifty **people** and not fifty
    days: nothing decays, and an opinion falls out of the record when fifty other
    people have since had one rather than when a calendar passes. A `now` on this
    port would be a second horizon nobody could keep in step with the first.
    """

    async def published_for(self, subject_id: UUID) -> PublishedSportsmanship | None:
        """The figure and the count of people behind it, **for another reader.**

        ``None`` for somebody nobody has rated — the record omits the zone rather
        than drawing a nought, on the rule this platform applies to every fact
        nobody has measured.

        **Published from the very first rating**, because the count crosses
        beside it: ``3,0 / 5 · 1 player`` is visibly one person's opinion. A
        minimum here would be the platform withholding the honest answer until it
        looked more authoritative than it is.
        """
        ...

    async def band_for(self, subject_id: UUID) -> SportsmanshipBand | None:
        """The coarse band, **for the person it is about.** No count, no figure.

        ``None`` for somebody nobody has rated, which is the same absence
        ``published_for`` spells and reaches the sheet the same way.

        It is folded from the same window and coarsened from the same rounded
        figure, so a subject's band can never disagree at an edge with what a
        reader is shown — one record, read at two resolutions.
        """
        ...


__all__ = [
    "PublishedSportsmanshipQuery",
    "SettledCourts",
    "SportsmanshipLedger",
]
