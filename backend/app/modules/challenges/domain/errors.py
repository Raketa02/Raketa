"""What this context refuses, and why each refusal is a refusal and not a no-op.

Two families. The first is about the **shape** of a send — a court that is not
the sport's, a challenge with nobody in it, a player in two seats — and every one
of them is a caller's bug that a no-op would hide behind a plausible answer.

The second is about **answering**, and it is where the rules that look
inconvenient live: a seat is answered once, by the person holding it, inside
their own window.

**No refusal here names anybody.** ``AppError.details`` is untyped, invisible to
the central response fence and ungeneratable against the API contract, so a
refusal states the class of problem and the client re-reads the sources it
already owns to find out who. That is one exemption not bought, and the
open-challenge refusal is the one where it matters: a payload naming the pair
would be a disclosure route through an error message.
"""

from __future__ import annotations

from app.shared.domain.errors import BadRequestError, ConflictError, ForbiddenError


class CannotChallengeYourself(BadRequestError):
    """The organiser appears among their own invitees.

    A refusal rather than a dropped seat: the only possible meaning is a caller's
    bug, and silently seating them once would hand back an arrangement nobody
    built.
    """

    code = "cannot_challenge_yourself"

    def __init__(self) -> None:
        super().__init__("A player cannot challenge themselves.")


class AChallengeNeedsAnInvitee(BadRequestError):
    """A send with nobody to ask.

    The organiser alone on a court is indistinguishable from never having sent,
    so there is nothing for this to record and nobody for it to reach.
    """

    code = "challenge_with_no_invitee"

    def __init__(self) -> None:
        super().__init__("A challenge must ask somebody.")


class TheCourtIsNotThisSports(BadRequestError):
    """The seats are not ``2 x seats_per_side(sport)``, evenly split.

    The court's shape is the sport's, and it is checked rather than trusted
    because *which side is short* is a fact this aggregate promises to hold — a
    three-seat padel court could not answer it.
    """

    code = "court_is_not_the_sports"

    def __init__(self, message: str) -> None:
        super().__init__(message)


class OnePersonToASeat(BadRequestError):
    """One player appears in two seats of the same court."""

    code = "one_person_to_a_seat"

    def __init__(self) -> None:
        super().__init__("A player may hold only one seat in a challenge.")


class TheOrganiserHoldsASeat(BadRequestError):
    """The organiser is not in the arrangement they built.

    They hold a seat like anybody else, and it is accepted from birth — that is
    what makes *every seat accepted* the whole of the completion rule, with no
    special case for singles.
    """

    code = "organiser_holds_a_seat"

    def __init__(self) -> None:
        super().__init__("The organiser holds a seat in their own challenge.")


class NotYourSeat(ForbiddenError):
    """Somebody answered for a seat they do not hold.

    Forbidden rather than not-found: the challenge exists and the caller can see
    it, and an answer on somebody else's behalf is the thing being refused.
    """

    code = "not_your_seat"

    def __init__(self) -> None:
        super().__init__("That seat is not yours to answer.")


class TheSeatIsAlreadyAnswered(ConflictError):
    """A second answer on a seat that already has one.

    Not idempotent, deliberately. *Yes* after *no* is a different answer and not
    a repeat of one, and a no-op would let the second quietly win or quietly
    lose depending on which way round it went.
    """

    code = "seat_already_answered"

    def __init__(self) -> None:
        super().__init__("That seat has already been answered.")


class TheAnswerWindowHasPassed(ConflictError):
    """An answer arriving after this seat's own deadline.

    Refused rather than accepted late: past the window the seat already reads as
    lapsed and the organiser may have offered it to somebody else, so an accept
    that resurrected it would contradict a card the platform already drew.
    """

    code = "answer_window_has_passed"

    def __init__(self) -> None:
        super().__init__("That seat's answer window has passed.")


class NobodyNewToInvite(ConflictError):
    """A send that would ask nobody who was not already asked.

    A rearrangement on its own is not a thing this context can record: once the
    court is full the sides are frozen, and the only door back into an
    arrangement is an open seat.
    """

    code = "nobody_new_to_invite"

    def __init__(self) -> None:
        super().__init__("There is nobody new to invite.")


class AnAcceptedPlayerMayNotBeRemoved(ConflictError):
    """A send that would drop or replace somebody who is already in the game.

    They may be moved across the net — an acceptance is to the game, not to the
    side — and they may never be taken out of it.

    **Somebody still deciding is covered too**, and the name says *accepted*
    because that is the settled vocabulary for the rule. Dropping a seat whose
    window is still open is a silent uninvite: the platform asked, the person is
    about to answer, and nothing would tell either of them it had stopped
    caring — which is the same damage to the answer record as asking twice.
    """

    code = "accepted_player_may_not_be_removed"

    def __init__(self) -> None:
        super().__init__("A player who accepted cannot be removed or replaced.")


class NobodyIsAskedTwice(ConflictError):
    """A send that would ask somebody who has already answered this challenge.

    Their seat is open again and somebody else may have it — but *they* have
    answered, and asking them a second time reads as the platform having lost
    track of them. It also damages the very record the matcher reads as
    reliability: a second lapse from one person on one challenge would count
    twice in a denominator that is supposed to be *challenges answered inside
    their window*.

    Re-offering that seat to a **different** person is the ordinary path and is
    not this. Re-proposing to the person who left is a proposal to somebody who
    has already decided, which is a **new** challenge if it is anything.
    """

    code = "nobody_is_asked_twice"

    def __init__(self) -> None:
        super().__init__("Somebody in this line-up has already answered.")


class TheChallengeIsOver(ConflictError):
    """Something was asked of a challenge nobody is left in.

    Its seats are open and its standing is settled; filling one would be a
    proposal to a different set of people, which is a **new** challenge.
    """

    code = "challenge_is_over"

    def __init__(self) -> None:
        super().__init__("That challenge is over.")


class AnOpenChallengeStandsWithThisPair(ConflictError):
    """Two people on this court already have a game between them, in any sport.

    **Names nobody**, on purpose: the organiser's own challenges were always
    theirs to read, so the client finds out who by reading them rather than by
    being told in an error payload.
    """

    code = "open_challenge_stands"

    def __init__(self) -> None:
        super().__init__(
            "Somebody on this court already has an open challenge with "
            "somebody else on it."
        )
