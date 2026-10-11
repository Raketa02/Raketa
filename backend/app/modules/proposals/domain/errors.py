"""The Proposals context's refusals.

**A player meets four of them from a card** — the game is over, the answer was
already given, every seat is In, or the people In now include somebody they do
not fit — and one from what their own account is missing: a payment method.
There is no cap on live yeses (removed 2026-10-05): games per week and one
game per hour already bound what a player can be charged for. None of them
names another person: *somebody you do not
fit* is said without saying who, as a withheld row is (``docs/adr/0130``).

The next four are **the dealer's**, met by whoever makes and deals proposals —
the engine (#540), a seed, a test — and by no player, since no route makes one.

The last two are **Games & money**'s: a value its form does not offer, each
naming what it does, so the screen can say both.

**Posting a game** (#546) adds the post's own: a Level range wider than the
engine's window or upside down, *Mixed pairs* in a singles sport, a poster
with no Level in the sport or left out by their own *Who*, and the button's
guards — two live posts, a week already booked, a game at that hour, and
nobody who fits free then.
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


# --------------------------------------------------------------------------- #
# Leaving a booked game (#544)
# --------------------------------------------------------------------------- #


class GameHasStarted(ConflictError):
    """*Leave the game* after its hour began (the mechanics §13: *after the
    start, no button*). Nothing was recorded."""

    code = "game_has_started"

    def __init__(self) -> None:
        super().__init__("this game has started; it can no longer be left")


class BookingIsCalledOff(ConflictError):
    """The game is off — refused, unanswered, or short at its cut-off — so
    there is nothing to leave; everybody still in is refunded, or nobody paid.
    Nothing was recorded."""

    code = "booking_is_called_off"

    def __init__(self) -> None:
        super().__init__("this game is called off")


class SeatJustTaken(ConflictError):
    """The open seat this player went for was taken a moment before — **the
    first join wins** (#545; the mechanics §10.1, §19) — or there is none left
    to take. Nothing was recorded, and nobody charged them."""

    code = "seat_just_taken"

    def __init__(self) -> None:
        super().__init__("somebody just took this seat")


class RescueNotOffered(ConflictError):
    """The open seat is not one this player is offered (#545): they do not fit
    somebody on the game, are not free for its hour, play then already, are at
    their Games & money, are on the game or left it. **Which is not said**, as a
    withheld card's reason is not (``docs/adr/0130``). Nothing was recorded."""

    code = "rescue_not_offered"

    def __init__(self) -> None:
        super().__init__("this seat is not offered to this player")


# --------------------------------------------------------------------------- #
# Posting a game (#546)
# --------------------------------------------------------------------------- #


class LevelRangeTooWide(BadRequestError):
    """A level bound outside the engine's window for the kind around the
    poster's Level — *you can narrow it, not widen it* (the mechanics §9.1
    step 4, Q78). ``details`` carries the window, ``low`` to ``high``.
    Nothing was read or posted."""

    code = "level_range_too_wide"

    def __init__(self, *, low: float, high: float) -> None:
        super().__init__(
            "a post's level range can be narrowed, never widened",
            details={"low": low, "high": high},
        )


class LevelRangeInverted(BadRequestError):
    """The lower level bound is above the upper one: nobody is between them."""

    code = "level_range_inverted"

    def __init__(self) -> None:
        super().__init__("the lower level bound is above the upper one")


class MixedPairsOnlyInDoubles(BadRequestError):
    """*Mixed pairs* is a doubles game — each side one man and one woman — and
    ``details.sport`` is played one a side."""

    code = "mixed_pairs_only_in_doubles"

    def __init__(self, *, sport: str) -> None:
        super().__init__("mixed pairs is only for doubles", details={"sport": sport})


class NotRatedInTheSport(ConflictError):
    """The poster holds no Level in ``details.sport``: there is no window to
    deal a game in, and nobody to fit (*Get rated in padel to post here*)."""

    code = "not_rated_in_the_sport"

    def __init__(self, *, sport: str) -> None:
        super().__init__(
            "rate yourself in this sport to post a game in it",
            details={"sport": sport},
        )


class WhoLeavesYouOut(ConflictError):
    """The game's *Who* is everybody's on it, the poster's too, and the
    poster's own gender or preference is not one it takes. Which is not said."""

    code = "who_leaves_you_out"

    def __init__(self) -> None:
        super().__init__("you would not be on a game for these players")


class LivePostsExhausted(ConflictError):
    """``details.cap`` posts of this player's are live already — until one
    fills, is withdrawn, or reaches its book-by (the mechanics §9.3)."""

    code = "live_posts_exhausted"

    def __init__(self, *, cap: int) -> None:
        super().__init__(f"{cap} live posts already", details={"cap": cap})


class GamesPerWeekBooked(ConflictError):
    """The poster's games per week are already booked for the week the hour is
    in (Monday ``details.week``) — the deck deals nothing in that week either
    (the mechanics §6.6, Q73)."""

    code = "games_per_week_booked"

    def __init__(self, *, games_per_week: int, week: str) -> None:
        super().__init__(
            "your games this week are booked",
            details={"games_per_week": games_per_week, "week": week},
        )


class YouPlayThen(ConflictError):
    """The poster already has a game at that hour (*one game per hour*, the
    mechanics §6.6)."""

    code = "you_play_then"

    def __init__(self) -> None:
        super().__init__("you already have a game at that hour")


class NobodyFitsThen(ConflictError):
    """None of the poster's best fits is free at that hour: a cell that cannot
    be picked (the mechanics §9.1 step 5). Nothing was posted."""

    code = "nobody_fits_then"

    def __init__(self) -> None:
        super().__init__("nobody who fits is free then")


class PostNotOpenToYou(ConflictError):
    """A member joining a post they were never dealt could not be dealt it
    now: not free for its hour, a game of theirs then, their week booked, its
    share above their *most I'll pay*, or a kind they do not want. **Which is
    not said**, as a rescue's is not (``docs/adr/0130``). Nothing was recorded."""

    code = "post_not_open_to_you"

    def __init__(self) -> None:
        super().__init__("this post is not one you could join")


# --------------------------------------------------------------------------- #
# The club runs its bookings (#547)
# --------------------------------------------------------------------------- #


class BookingNotBooked(ConflictError):
    """The game is still waiting for the club's answer: accept or refuse it.
    There is no court of the players' to move and nothing paid to cancel."""

    code = "booking_not_booked"

    def __init__(self) -> None:
        super().__init__("this game is waiting for your answer")


class CourtNotFree(ConflictError):
    """The court the club chose is not a free court of the game's sport at its
    hour — another game holds it, it is closed then, or it is another sport's.
    Nothing was recorded."""

    code = "court_not_free"

    def __init__(self) -> None:
        super().__init__("that court is not free for this game")
