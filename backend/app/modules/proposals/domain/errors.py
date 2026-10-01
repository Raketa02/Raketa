"""The Proposals context's refusals.

**A player meets four of them from a card** — the game is over, the answer was
already given, every seat is In, or the people In now include somebody they do
not fit — and three from what their own account is missing: a payment method,
a live yes to spare. None of them names another person: *somebody you do not
fit* is said without saying who, as a withheld row is (``docs/adr/0130``).

The next four are **the dealer's**, met by whoever makes and deals proposals —
the engine (#540), a seed, a test — and by no player, since no route makes one.

The last two are **Games & money**'s: a value its form does not offer, each
naming what it does, so the screen can say both.
"""

from __future__ import annotations

from app.shared.domain import BadRequestError, ConflictError, NotFoundError


class ProposalNotFound(NotFoundError):
    """No such proposal **for this player**: it does not exist, it was never
    dealt to them, or they are not in its pool. One code for all three, so a
    proposal id is not a way to learn what somebody else was dealt."""

    code = "proposal_not_found"

    def __init__(self) -> None:
        super().__init__("no such proposal")


class BookingNotFound(NotFoundError):
    """No such booked game **for this player**: it does not exist, or they have
    no seat on it. One code for both, so a booking id is not a way to learn
    whose evening it is (#542). **For a club**, no such booking at that club —
    another club's is not one (#543)."""

    code = "booking_not_found"

    def __init__(self) -> None:
        super().__init__("no such booking")


class ProposalIsOver(ConflictError):
    """The game is no longer filling — its book-by passed, its poster withdrew
    it, or the last court at its club and hour went — named by
    ``details.standing``. The card leaves; nothing was recorded."""

    code = "proposal_is_over"

    def __init__(self, *, standing: str) -> None:
        super().__init__(
            "this game is no longer filling", details={"standing": standing}
        )


class ProposalAlreadyAnswered(ConflictError):
    """This player already said no, and a card swiped left never comes back
    (the mechanics §5.3) — or, asked of a no, they are In: somebody In leaves
    by withdrawing their yes, never by a no."""

    code = "proposal_already_answered"

    def __init__(self) -> None:
        super().__init__("this card was already answered")


class ProposalIsFull(ConflictError):
    """Every seat is already In. Nothing was recorded."""

    code = "proposal_is_full"

    def __init__(self) -> None:
        super().__init__("every seat on this game is already in")


class NoLongerFits(ConflictError):
    """Somebody who said yes since this card was dealt is somebody this player
    does not fit, and a replacement must fit everybody already In — every pair
    (the mechanics §6.1). The card has gone; **who** is not said."""

    code = "no_longer_fits"

    def __init__(self) -> None:
        super().__init__("the people in on this game no longer fit this player")


class LiveYesesExhausted(ConflictError):
    """``details.cap`` live yeses in ``details.sport`` already — yeses on games
    that have not filled (the mechanics §6.6). The card springs back; one of
    them has to fill, expire or be withdrawn first."""

    code = "live_yeses_exhausted"

    def __init__(self, *, cap: int, sport: str) -> None:
        super().__init__(
            f"{cap} live yeses in this sport already",
            details={"cap": cap, "sport": sport},
        )


class PaymentMethodRequired(ConflictError):
    """A yes is *charge my share if it fills*, and there is nothing to charge:
    the player has no saved payment method. Save one, then say yes (the
    mechanics §6.1, §12.5)."""

    code = "payment_method_required"

    def __init__(self) -> None:
        super().__init__("a payment method must be saved before a yes")


# --------------------------------------------------------------------------- #
# The dealer's
# --------------------------------------------------------------------------- #


class PoolNotFound(NotFoundError):
    """No such pool: not one that exists, and not a group a pool could be
    opened for."""

    code = "pool_not_found"

    def __init__(self) -> None:
        super().__init__("no such pool")


class NotInThePool(ConflictError):
    """Somebody named on a version, or posting, is not a player of the pool —
    nobody is dealt a game from a pool they are not in."""

    code = "not_in_the_pool"

    def __init__(self) -> None:
        super().__init__("somebody named is not a player of this pool")


class VersionDoesNotFit(ConflictError):
    """A version names somebody who does not fit everybody else on it — the
    people already In and the rest of its own names, every pair (the mechanics
    §6.1, §7). Nothing was dealt."""

    code = "version_does_not_fit"

    def __init__(self) -> None:
        super().__init__("somebody on this version does not fit everybody else on it")


class CourtHourNotForSale(ConflictError):
    """The club sells no court of this sport at this hour through Raketa — it
    is not live, it is paused, the hour is not in its pattern or is closed, or
    the hour's book-by has passed. Nothing was proposed."""

    code = "court_hour_not_for_sale"

    def __init__(self) -> None:
        super().__init__("no court of this sport is for sale at this club and hour")


# --------------------------------------------------------------------------- #
# Games & money
# --------------------------------------------------------------------------- #


class GamesPerWeekOutOfRange(BadRequestError):
    """Games per week outside the one to seven the stepper offers.
    ``details`` carries the range."""

    code = "games_per_week_out_of_range"

    def __init__(self, *, least: int, most: int) -> None:
        super().__init__(
            f"games per week is between {least} and {most}",
            details={"least": least, "most": most},
        )


class MostIllPayNotOffered(BadRequestError):
    """A ceiling that is not one of the chips — *off* is ``null``, never a
    nought. ``details.choices`` carries the ones offered, in grosze."""

    code = "most_ill_pay_not_offered"

    def __init__(self, *, choices: tuple[int, ...]) -> None:
        super().__init__(
            "most I'll pay is off or one of the offered ceilings",
            details={"choices": list(choices)},
        )


class CourtJustTaken(ConflictError):
    """Another full game at the same club and hour booked the court this one
    read as free, a moment before it. The yes is tried once more, on the courts
    left; only a second race in a row reaches a client, which retries. Nothing
    was recorded and nobody paid."""

    code = "court_just_taken"

    def __init__(self) -> None:
        super().__init__("the court was booked a moment ago; try again")


class PaymentToConfirm(ConflictError):
    """This player's seat reopened because their payment could not be held,
    and **confirming that payment is their yes again** (the mechanics §12.2) —
    ``details.seat_charge_id`` names it. A plain yes would ask the bank the same
    question and be refused the same way. Nothing was recorded."""

    code = "payment_to_confirm"

    def __init__(self, *, seat_charge_id: str) -> None:
        super().__init__(
            "confirm the payment to keep this seat",
            details={"seat_charge_id": seat_charge_id},
        )


# --------------------------------------------------------------------------- #
# A club answering a request (#543)
# --------------------------------------------------------------------------- #


class RequestNotWaiting(ConflictError):
    """The game is not waiting for this club's answer any more: the club
    already answered it, the request was withdrawn because a seat opened — and
    the game is filling again — or its deadline passed and it was recorded as
    unanswered. Nothing was recorded."""

    code = "request_not_waiting"

    def __init__(self) -> None:
        super().__init__("this game is not waiting for your answer")


class RequestTimedOut(ConflictError):
    """The club's time to confirm ran out before this answer arrived: the
    request is called off as unanswered, whether or not that is recorded yet.
    Nothing was recorded and nobody paid."""

    code = "request_timed_out"

    def __init__(self) -> None:
        super().__init__("the time to answer this request has run out")
