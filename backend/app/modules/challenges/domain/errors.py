"""What this context refuses, and why each refusal is a refusal and not a no-op.

Two families. The first is about the **shape** of a send — a court that is not
the sport's, a challenge with nobody in it, a player in two seats — and every one
of them is a caller's bug that a no-op would hide behind a plausible answer.

The second is about **answering**, and it is where the rules that look
inconvenient live: a seat is answered once, by the person holding it, inside
their own window.

The third family arrived with the send, and it is about **other people's live
state**: the four fail-closed gates, re-verified in the send's own transaction
over a court that may have been built an hour ago.

**No refusal here names anybody, and none of them carries a payload.**
``AppError.details`` is untyped, invisible to the central response fence and
ungeneratable against the API contract, so a refusal states the class of problem
and the client re-reads the sources it already owns to find out who
(``docs/adr/0130`` admits exactly one field against *nobody may ask who was
withheld*, and says in its own words that the single exemption is what keeps it a
rule). That is one exemption not bought, and it matters twice over: a payload
naming the pair on the open-challenge refusal would be a disclosure route through
an error message, and a payload naming the withheld seat on the gate refusal
would be a **block detector** handed to the person the block is invisible to.

**The hold refuses with ``account_held``, which is declared in
``app/shared/domain/errors.py``** rather than a second time here. It is one fact
with one remedy and it must cross as one code; the class is shared for the same
reason the *port* is not.
"""

from __future__ import annotations

from app.shared.domain.errors import (
    AppError,
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
)
from http import HTTPStatus


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


class TheWithdrawIsTheOrganisers(ForbiddenError):
    """Somebody on the court asked to end the whole challenge, and the act is
    not theirs.

    Forbidden rather than not-found, for ``NotYourSeat``'s reason: the challenge
    exists and the caller can see it, and what is being refused is an act on
    everybody else's arrangement.

    **One code for three cases, and the code keeps its name** (``docs/adr/0163``
    §1). On a court that was never a game the withdraw is the organiser's alone;
    on a court that has been a game it falls back, once the organiser's own seat
    is open, to any remaining player — so a non-organiser on a court whose
    organiser is still in, somebody whose own seat is no longer live on a court
    whose organiser has left, and the organiser who left it themselves, are all
    told the same thing: *the act is not yours*. The sentence gained its second
    clause; the code did not move, because a shipped client already switches on
    it.

    **The invitee is not offered a smaller version of it either.** Leaving a
    seat you have already answered is refused by ``TheSeatIsAlreadyAnswered``
    while the court is being arranged — once it has become a game, leaving is
    its own act (``docs/adr/0162``) and still not a withdraw; a withdraw is
    whole-challenge, and a per-seat one would be the organiser removing an
    accepted player, which ``AnAcceptedPlayerMayNotBeRemoved`` exists to say no
    to.
    """

    code = "withdraw_is_the_organisers"

    def __init__(self) -> None:
        super().__init__(
            "Only the organiser may withdraw a challenge — or, once the organiser "
            "has left the game it became, anybody still on its court."
        )


class TheFillIsTheLiveMembers(ForbiddenError):
    """Somebody holding a seat they have left tried to grow the court.

    **The mirror of the withdraw's refusal, one act over** (``docs/adr/0150``
    §1). Growing a court and ending one are different acts with different
    permissions: the withdraw is the organiser's, and the fill is every **live**
    member's — accepted, or still deciding.

    A declined or lapsed invitee still holds their seat and still sees the
    challenge on their own list, which is why this is a `403` and not a `404`:
    pretending it is not there while their own seat is drawn on it would be the
    wrong lie. They have left the game, and filling somebody else's court is not
    a thing leaving entitles you to.
    """

    code = "fill_is_the_live_members"

    def __init__(self) -> None:
        super().__init__(
            "Only somebody still on this court may fill its open seats."
        )


class OnlyAHalfBuiltLineUpIsWithdrawn(ConflictError):
    """A withdraw asked of a challenge that has some other end already.

    **The exit exists exactly where nothing else ends it** (``docs/adr/0142``
    §2). ``AWAITING_ANSWERS`` ends itself when the clocks run out; ``ON`` has
    become a game, and ending the challenge would not touch it; the three endings
    have ended. ``LINE_UP_INCOMPLETE`` is the one standing that never ends on its
    own and where nobody else holds an exit, so it is the one that gets the act.

    **One code for five standings, deliberately.** They are one sentence — *this
    is not a half-built line-up* — and splitting them would be five ways of
    saying that the caller is looking at a standing it has already been told.

    **A court that has been a game and had a seat reopened is not among them.**
    It is ``LINE_UP_INCOMPLETE`` too, and it *is* withdrawn here
    (``docs/adr/0163``): the game it became is called off in the same
    transaction, so the withdraw no longer ends a challenge while its game goes
    on standing — which was the one reason ``docs/adr/0162`` §2 refused it with
    this code for a day.
    """

    code = "not_a_half_built_line_up"

    def __init__(self) -> None:
        super().__init__("Only a half-built line-up can be withdrawn.")


class NotAGameYet(ConflictError):
    """A departure asked of a court that has not become a game.

    Leaving a half-built court is a **decline**, and it is already given: an
    invitee who has not answered says no, and one who has is in a court that is
    still being arranged rather than in a game. The departure is the act for the
    one standing where nothing else lets a person out — ``ON`` — and it is asked
    of no other (``docs/adr/0162`` §1).

    **One code for two standings**: ``AWAITING_ANSWERS`` and
    ``LINE_UP_INCOMPLETE`` are one sentence here — *this is not a game yet*.
    """

    code = "not_a_game_yet"

    def __init__(self) -> None:
        super().__init__("This challenge has not become a game yet.")


class TheGameIsHistory(ConflictError):
    """A seat asked to change on a court whose game has happened, or never will.

    The departure, the fill and the acceptance all meet it, on a court that had
    become a game: after *we played*, and after the entry window closed on
    silence, the line-up is the record of an evening and nothing on it moves.
    **Not ``challenge_is_over``**, deliberately: the challenge is still ``ON``
    and the person is looking at a game, so the refusal names the game.
    """

    code = "game_is_history"

    def __init__(self) -> None:
        super().__init__("This game has happened, or never will.")


class TheGameMomentHasPassed(ConflictError):
    """A seat asked to change after the moment the plan agreed.

    Once the agreed moment has passed the game is *Needs result* and leaving
    means nothing — so it is refused, and a no-show cannot vacate a seat to
    block the result. The same instant closes the court to a fill and to an
    acceptance: a newcomer accepting into *Sunday* on Monday joins a game whose
    moment is gone (``docs/adr/0162`` §4).

    The moment is the **plan's**, read through ``games`` at the guard and
    stored nowhere on this side.
    """

    code = "game_moment_has_passed"

    def __init__(self) -> None:
        super().__init__("The moment this game was agreed for has passed.")


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


class TheLineUpIsNoLongerSendable(ConflictError):
    """One of the four fail-closed gates now refuses somebody on this court.

    A block either way, a hold, an account ``users`` may not show, or the mutual
    gender preference — **indistinguishably**, and about a seat this refusal does
    not name. Four gates behind one code is the same posture ``read_back_search``
    takes one screen earlier and for the same reason: a block is invisible to the
    person it was taken against, a hold and an account state are moderation facts
    about somebody else, and a gender preference is a safety setting whose owner
    is the only person entitled to read it.

    **Whole-send, never per-seat.** A send that quietly dropped the refused
    invitee would hand the organiser an arrangement they did not choose, which is
    the harm recording the arrangement exists to prevent arriving through the
    safety check. So nothing is written and there is no half-sent challenge to
    reconcile.

    **The remedy is to read the origin search back**, which re-evaluates the same
    four gates and marks the rows it withholds. Nothing new is disclosed, no
    second exemption is bought, and the line-up keeps the ``search_id`` it was
    built on — re-running the pool would mint a new id the whole line-up must
    adopt, and its untouched seats are only *probably* in the new answer.
    """

    code = "line_up_no_longer_sendable"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(
            message
            or "Somebody on this court can no longer be invited to it."
        )


class TheCourtDidNotComeFromThatSearch(ConflictError):
    """The cited search cannot place this court.

    **Four cases and one code**, exactly as the *Let's play* origin refuses: the
    search does not exist, it is somebody else's, it was run for another sport,
    or it never returned one of these people. Telling them apart would answer
    *does this search_id exist* about a stranger's id, one probe at a time.

    A send is bound to **one** search, because that is what the arrangement was
    built and forecast against. It is not an authorization check standing in for
    the gates — those run afterwards, live — it is what makes every seat's origin
    true by construction rather than by a client being honest about it.
    """

    code = "court_origin_not_found"

    def __init__(self) -> None:
        super().__init__(
            "No search of yours showed all of those players for that sport."
        )


class TheGatesCouldNotBeEvaluated(AppError):
    """A safety gate could not be read, so nothing is minted.

    **The fail-closed rule as a class** (``docs/adr/0095`` §5). A term that
    cannot be evaluated stands down; a *gate* that cannot be evaluated excludes,
    and at the send that means the whole send refuses rather than writing a
    challenge nobody verified.

    A 503 and not a 500 because the failure is transient and about the platform,
    never about the caller: the code tells a client to retry the same request
    rather than to change it. **Its own code and deliberately not the matcher's**
    ``gate_data_unavailable``, for the reason ``BlockStateUnavailable`` is not
    that code either — a consumer catches somebody else's outage and re-raises
    its own refusal, which is what stops this context importing the matcher's
    error class.

    **It does not reach ``POST /api/v1/interest``.** A mutual yes mints a
    challenge inline, in the same transaction, so a raise there would roll back
    somebody\'s *Let\'s play* — and losing a tap to a hiccup in a hold query is a
    strictly worse outcome than the pair having a mutual with no game opened. So
    that path catches this and mints nothing, which is the same fail-closed rule
    reaching the only remedy it has: on a send there is an organiser at a screen
    who can retry, and on a deck there is nobody to refuse to.
    """

    status_code = HTTPStatus.SERVICE_UNAVAILABLE
    code = "challenge_gates_unavailable"


class NoChallengeOfYoursHasThatId(NotFoundError):
    """A challenge id that names nothing this reader holds a seat in.

    **Two cases and one code, deliberately.** The challenge does not exist, or it
    exists and this player is not on its court — and the two answer identically,
    because an answer that separated them would tell a caller whether a stranger's
    challenge id is real. That is a directory of other people's evenings, read one
    probe at a time, and it is the same refusal ``search_not_found`` already makes
    about the same class of question.

    ``NotYourSeat`` is **not** this and is not reachable from the routes: it is the
    aggregate's own invariant, refusing an answer given on somebody else's behalf
    by a caller that has already been handed the challenge.
    """

    code = "challenge_not_found"

    def __init__(self) -> None:
        super().__init__("No challenge of yours has that id.")
