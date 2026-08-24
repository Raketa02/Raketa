"""Taking a seat: the act the offers region exists to make possible.

ADR-0061's open call arrives on a phone as one button on one card, and what it
opens is ADR-0081's five minutes — *"a seat is never taken until it is paid, and
what a player takes while she pays is a seat claim."*

**A refusal is not a second shape** (ADR-0070). Somebody else took it, the match
filled, joining closed, it started, it was cancelled, she is already in it: every
one comes back as **what a success returns**, the same three-part answer saying
what is true now. The player *sees* that the seat has gone rather than being told
by a dialog, and the client has one code path instead of two.

**Two refusals answer differently, and both are about her rather than the seat.**
She is already buying a seat somewhere else, and she let *this* seat go less than
thirty seconds ago. Neither can be said by recomposing this card — the first is a
sentence about a different match and the second is about a moment — so a card
that went on saying *first to take it* would be a button she taps for ever. They
are ADR-0081's own two structural limits on a serial claimant, and each carries
the one sentence that says what to do.

**Two regions come back whole, and exactly when the tap applied.** ADR-0070: *"an
accepted offer changes three things at once — the offer is gone, the match belongs
in the strip, and the shelf copy of that match now says you are in. The first is
expressed by a fresh offers region."* This is the first act in the product that
moves a card **between** regions, so it is the first that needs them; a refusal
moved nothing and sends neither, which is what leaves the corrected card on screen
long enough for the client to write its own fading line over it. The shelves are
never in an update, so the shelf copy waits for the next compose — corrected in
the meantime by the one card, which is identified by the match rather than by its
position.

**No idempotency key.** ADR-0030's log is for *destructive* commands, and this
one is not: a second tap by the player who already holds the claim is refused by
her own claim, and the state she gets is the state she asked for. What a key would
buy — *did my first tap land* — is answered by the card that comes back carrying
her claim.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.application.ports import UnitOfWork
from app.kernel import Clock, Instant, instant

from app.modules.matches.domain.errors import (
    JoiningClosed,
    MatchAlreadySettled,
    MatchAlreadyStarted,
    MatchIsFull,
    PlayerAlreadyHoldsASeat,
    SeatAlreadyClaimed,
)
from app.modules.now.application.commands import SportFilter
from app.modules.now.application.compose_enrolled import ComposeEnrolled, card_of
from app.modules.now.application.compose_now import stamp_at
from app.modules.now.application.compose_offers import (
    ComposeOffers,
    offer_card_of,
    offered_matches,
)
from app.modules.now.domain.ports import Claims, EnrolledMatches, OfferedSeats
from app.modules.now.domain.screen import (
    CardChanged,
    CardGone,
    EnrolledRegion,
    NowUpdate,
    OffersRegion,
    Stamp,
)

#: Every way the aggregate says *the seat is not yours to take*, and all of them
#: answer with the screen. Each is a state ADR-0070's rule was written for — the
#: act no longer applies, and what she needs is what is true now:
#:
#: - somebody else is alone with the last free seat, or has taken it;
#: - the match filled between the telling and the tap;
#: - joining closed, which is the one clock an offer dies to;
#: - it started, or it was cancelled;
#: - she is already in it, which is the answer a second phone would get.
_REFUSALS = (
    SeatAlreadyClaimed,
    MatchIsFull,
    JoiningClosed,
    MatchAlreadyStarted,
    MatchAlreadySettled,
    PlayerAlreadyHoldsASeat,
)


@dataclass(frozen=True)
class TakeSeatCommand:
    """*Give me the five minutes in front of a seat in this match.*

    Two fields about the act and one about the screen. No quote, because a seat's
    price is not a label the aggregate refuses on — the rescue tier moves for
    reasons that have nothing to do with her, and the card she is corrected onto
    states the new one. No vacancy either: **which seat is the match's answer and
    not the caller's**, which is ``open_claim``'s own rule and the reason a caller
    who could name one could name one somebody else is buying.
    """

    player_id: UUID
    match_id: UUID

    #: The chip on the sport bar when she tapped. It is a fact about the
    #: **screen** rather than about the match, and it is here for one reason: a
    #: tap that applies sends two regions back whole, and a region recomposed
    #: under a different filter from the one she is looking at would replace her
    #: filtered screen with somebody else's. It defaults to ``all``, which hides
    #: nothing, so a client that forgets it gets a superset rather than a hole.
    sport: SportFilter = SportFilter.ALL


@dataclass(frozen=True)
class SeatAnswer:
    """What taking a seat answers: what the tap did, and what her screen holds.

    ``claimed`` is the one thing here that is a fact about the **command** rather
    than about the match, and it is the departure route's ``applied`` in the shape
    a claim needs. It is what stops *was I refused* being a rule on the phone
    (ADR-0053): deriving it from a seat claim appearing on the card is a rule, and
    the acknowledgement ADR-0070 leaves to the client is a sentence it can only
    write if it knows.

    The two regions are present **exactly when ``claimed`` is true**, and that is
    one decision rather than two: a tap that applied moved a card from one region
    to the other, and a tap that did not moved nothing. A server deciding
    per-region whether *the contents changed* would be comparing against a screen
    it cannot see.
    """

    claimed: bool
    update: NowUpdate
    offers: OffersRegion | None = None
    your_matches: EnrolledRegion | None = None


class TakeTheSeat:
    """Open the claim, and hand back the screen it changed."""

    def __init__(
        self,
        *,
        claims: Claims,
        offered: OfferedSeats,
        enrolled: EnrolledMatches,
        offers: ComposeOffers,
        strip: ComposeEnrolled,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._claims = claims
        self._offered = offered
        self._enrolled = enrolled
        self._offers = offers
        self._strip = strip
        self._uow = uow
        self._clock = clock

    async def execute(self, command: TakeSeatCommand) -> SeatAnswer:
        """Take it if it is there, and say what is true either way.

        **Nothing is checked before the write but the address.** Anybody may buy
        a free seat in any match — ``open_claim`` is *"how **any** seat is taken
        from the marketplace: a seat offered to her and a seat she found herself
        are the same race when it is the last one, and offered seats behave
        differently is a second rule nobody would remember"* — so there is no
        membership here to be a stranger to. The only 404 is a match id that
        names nothing, which the port raises and which is about the address
        rather than about the act.
        """

        now = instant(self._clock.now())
        try:
            await self._claims.take(
                match_id=command.match_id, player_id=command.player_id, at=now
            )
        except _REFUSALS:
            return await self._answer(command, now=now, claimed=False)

        await self._uow.commit()
        return await self._answer(command, now=now, claimed=True)

    async def _answer(
        self, command: TakeSeatCommand, *, now: Instant, claimed: bool
    ) -> SeatAnswer:
        """The card, and the two regions when there are two to send.

        Read **after** the commit, on the departure route's rule: the answer has
        to describe the record as it stands rather than as the write left it in
        memory, and a card composed for a claim-holder carries facts — her claim's
        five minutes, the counting — that only the full read assembles.
        """

        stamp = stamp_at(now)
        if not claimed:
            return SeatAnswer(
                claimed=False,
                update=await self._card(command, now=now, stamp=stamp),
            )

        offers = await self._offers.compose(
            viewer=command.player_id,
            sport=command.sport.sport,
            now=now,
            stamp=stamp,
        )
        return SeatAnswer(
            claimed=True,
            update=await self._card(command, now=now, stamp=stamp),
            offers=offers,
            your_matches=await self._strip.compose(
                viewer=command.player_id,
                sport=command.sport.sport,
                now=now,
                stamp=stamp,
                offered=offered_matches(offers),
            ),
        )

    async def _card(
        self, command: TakeSeatCommand, *, now: Instant, stamp: Stamp
    ) -> NowUpdate:
        """The one card the tap was about, composed where the screen composes it.

        **Two composers and one order, and the order is what the situations are
        for.** A viewer who is something to the match — a seat, a departure, a
        queue place, and after a successful tap the claim she has just opened —
        gets the strip's card, because that is the region the match is in now. A
        viewer who is nothing to it but was told about it gets the offer card,
        which is what makes the refusal path work: ``offer_card_of`` hands the
        ladder an offer exactly while there is still a seat, so a card recomposed
        after somebody else took it resolves to the match's own situation and
        *says the seat is gone*.

        A viewer who is neither gets **``CardGone``**, and that is the honest
        answer rather than a fallback: there is no card about this match anywhere
        on her screen, so ADR-0070's *"this card is no longer on your screen"* is
        literally what is true. It is unreachable from the offer card today —
        nothing else names ``takeSeat`` — and it is what a shelf card naming it
        one day will need.
        """

        row = await self._enrolled.one(
            player_id=command.player_id, match_id=command.match_id, now=now
        )
        if row is not None:
            return CardChanged(card=card_of(row, now=now, stamp=stamp))
        offer = await self._offered.one(
            player_id=command.player_id, match_id=command.match_id, now=now
        )
        if offer is not None:
            return CardChanged(card=offer_card_of(offer, now=now, stamp=stamp))
        return CardGone(match_id=command.match_id)
