"""A game still filling, opened by anybody it was dealt to — the rules that need
no I/O (#542; the mechanics §14.2; the screens A4.2).

The details are the deck's card turned into a screen, for three more readers: a
card's *i*, a You're In row, and a game the reader already answered. Three rules
shape them.

**Who is drawn follows who is reading.** A reader still deciding sees **their own
card** — everybody In, them, the rest of their version — exactly as the deck
deals it (``domain/deck.py``), and is shown nothing when somebody In is somebody
they may not share a court with, as the deck withholds that card. A reader **In**
sees everybody In and the open seats, as their You're In row draws it: whose
names are still deciding is no business of somebody already In. And nobody is
deciding on a game that is over.

**Waiting for one payment is a full game still filling** (#625): a share was
refused, and its player's time to pay runs — their seat theirs alone. No club
confirms a game (``docs/adr/0196`` §1), so nothing else leaves a full game
filling (#669).

**What the details say about the game follows its kind** (``docs/adr/0207``
§5, §6, #833): a competitive game its full forecast and what is at stake for
the reader — only while the game is still theirs to play, and once every seat is
named — and a For-fun game its Social vibe and the reader's rows, and never a
forecast.

**The actions are what the routes would take.** *I'm in* and *Not this time*
while the reader may answer and a seat is open; *Withdraw* when they are In;
*Leave the game* in its place while a payment is awaited (the mechanics §13); a
refused payment is **confirmed**, never said again, since the bank would be
asked the same question — within the payer's time to pay too, when a share
refused for terms or a missing method is said yes to again once fixed; and
nothing once the game is over or the answer is final — a no, a seat reopened
because they no longer fit, a yes paused by a full week, which comes back by
itself.
"""

from __future__ import annotations

from collections.abc import Callable, Collection, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import final
from uuid import UUID

from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, exhaustive
from app.modules.proposals.domain.deck import ReadersView, Sides, anybody, view_of
from app.modules.proposals.domain.proposal import Proposal, ReopenReason, Standing


class ProposalStatus(StrEnum):
    """Where a proposal stands for its details (the mechanics §14.2)."""

    #: Seats are open — *Filling · 2 of 4 in*.
    FILLING = "FILLING"
    #: Every seat is In and one player's refused share is awaited: their time
    #: to pay runs (#625).
    WAITING_FOR_A_PAYMENT = "WAITING_FOR_A_PAYMENT"
    #: The last yes booked it: the booking has the proposal's id.
    FILLED = "FILLED"
    EXPIRED = "EXPIRED"
    WITHDRAWN = "WITHDRAWN"
    COURT_HOUR_LOST = "COURT_HOUR_LOST"


class ReaderAction(StrEnum):
    """What the reader may do from the details."""

    #: *I'm in* — ``POST /proposals/{id}/yes``.
    YES = "YES"
    #: *Not this time* — ``POST /proposals/{id}/no``.
    NO = "NO"
    #: *Withdraw* — ``DELETE /proposals/{id}/yes``.
    WITHDRAW = "WITHDRAW"
    #: *Leave the game* while a payment is awaited: leaving withdraws the yes —
    #: ``DELETE /proposals/{id}/yes`` — with its sheet (the mechanics §13).
    LEAVE = "LEAVE"
    #: *Confirm your payment to keep your seat*.
    CONFIRM_PAYMENT = "CONFIRM_PAYMENT"


@final
@dataclass(frozen=True, slots=True)
class DetailsView:
    """Who the details draw: everybody In, the reader, and — for a reader still
    deciding — the rest of their version."""

    reader: UUID
    #: Everybody In, in the order they said yes — the reader among them when
    #: they are In.
    in_: tuple[UUID, ...]
    #: The rest of the reader's version, shown beside them while they decide.
    others: tuple[UUID, ...]

    @property
    def people(self) -> tuple[UUID, ...]:
        """Everybody drawn, in the card's order."""

        if self.reader in self.in_:
            return (*self.in_, *self.others)
        return (*self.in_, self.reader, *self.others)

    @property
    def beside_the_reader(self) -> tuple[UUID, ...]:
        """Everybody drawn but the reader — who the sides are arranged from."""

        return tuple(player for player in self.people if player != self.reader)


def status_of_proposal(proposal: Proposal, *, now: Instant) -> ProposalStatus:
    standing = proposal.standing_at(now)
    match standing:
        case Standing.FILLING:
            if proposal.waiting_for_a_payment:
                return ProposalStatus.WAITING_FOR_A_PAYMENT
            return ProposalStatus.FILLING
        case Standing.FILLED:
            return ProposalStatus.FILLED
        case Standing.EXPIRED:
            return ProposalStatus.EXPIRED
        case Standing.WITHDRAWN:
            return ProposalStatus.WITHDRAWN
        case Standing.COURT_HOUR_LOST:
            return ProposalStatus.COURT_HOUR_LOST
        case _:
            exhaustive(standing)


def details_view(
    proposal: Proposal,
    reader: UUID,
    *,
    unfit: Collection[frozenset[UUID]],
    in_the_pool: Collection[UUID],
    now: Instant,
    may_stand: Callable[[Sequence[UUID]], bool] = anybody,
    wants: Mapping[UUID, Collection[SearchMode]] | None = None,
) -> DetailsView | None:
    """Who the reader's details draw — ``None`` for a proposal that is nothing
    to them, and for one with somebody In they may not share a court with, or
    not stand with on a *Mixed pairs* post, while they are not In themselves.
    ``unfit`` is every pair that may not; ``wants`` the names' Play intents, as
    the deck reads them (Q127)."""

    if not proposal.is_on_it(reader):
        return None
    if reader in proposal.yeses:
        return DetailsView(reader=reader, in_=proposal.yeses, others=())
    if any(frozenset((reader, player)) in unfit for player in proposal.yeses):
        return None
    if not may_stand((*proposal.yeses, reader)):
        return None
    dealt: ReadersView | None = view_of(
        proposal,
        reader,
        unfit=unfit,
        in_the_pool=in_the_pool,
        now=now,
        may_stand=may_stand,
        wants=wants,
    )
    # Nothing beside the reader's tile but the people In: a game that is over,
    # full, answered with a no, or with nobody else left on the reader's version.
    others = () if dealt is None else dealt.others
    return DetailsView(reader=reader, in_=proposal.yeses, others=others)


def stakes_are_priced(
    sides: Sides, *, seats_per_side: int, actions: Collection[ReaderAction]
) -> bool:
    """Whether what a counted result would do to the reader is priced on these
    sides (``docs/adr/0207`` §6): **only on a game still theirs to play** —
    still filling, and the reader In or free to answer or to confirm a
    payment (``actions``) — **and only with every seat named**.

    Nothing is at stake for a reader who said no, no longer fits, or waits on
    a paused yes, nor on a game that is over: the court that plays, if any, is
    not one they are on. A filled game's stakes are its booking's pairing's,
    whose court can change after the fill. And a seat open is a court that is
    not yet the one that will play, so nothing is priced on it, as on a booked
    game (``docs/adr/0162`` §3)."""

    return bool(actions) and len(sides.yours) == len(sides.theirs) == seats_per_side


def actions_for(
    proposal: Proposal, reader: UUID, *, now: Instant
) -> tuple[ReaderAction, ...]:
    """What the reader may do from the details, in the order the screen draws
    them."""

    if proposal.standing_at(now) is not Standing.FILLING:
        return ()
    if reader in proposal.yeses:
        way_out = (
            ReaderAction.LEAVE if proposal.open_seats == 0 else ReaderAction.WITHDRAW
        )
        paying = proposal.paying.get(reader)
        if paying is not None:
            # Their time to pay: the payment confirmed — or, refused for terms
            # or a missing method, said yes to again once fixed.
            pay = (
                ReaderAction.CONFIRM_PAYMENT
                if paying.payment_to_confirm is not None
                else ReaderAction.YES
            )
            return (pay, way_out)
        return (way_out,)
    if reader in proposal.declined or reader in proposal.paused:
        return ()
    reopened = proposal.reopened.get(reader)
    if reopened is not None:
        if reopened.payment_to_confirm is not None:
            return (ReaderAction.CONFIRM_PAYMENT,)
        if reopened.reason is ReopenReason.NO_LONGER_FITS:
            return ()
    if proposal.open_seats == 0:
        return ()
    return (ReaderAction.YES, ReaderAction.NO)
