"""What this context refuses, and why each refusal is a refusal and not a no-op.

Two families, and they map onto the two halves of the flow.

The first is about **who may act**: only the people who were on the court, and
only about a game that is still open to being acted on. Everything here is a
caller's bug or a race, and a no-op would hide it behind a plausible answer.

The second is about **the shape of the argument** — one proposal per side, a
correction only while nobody has answered, an acceptance only from across the
net, and never a rejection with nothing in it. These are the rules that bound a
disagreement to two rounds, and they are the reason silence is safe to treat as
agreement.

**No refusal here names anybody and none of them carries a payload**, on this
repository's standing rule: a refusal states the class of problem and the client
re-reads the sources it already owns. There is nothing to disclose in a game a
player was on the court for, but the rule is kept so it stays a rule.

**The pairing read has two refusals of its own** (``docs/adr/0161``), and the
first is a ``404`` where the acts above say ``403``. An act on a game is made by
somebody holding a game id the list already gave them, so *you were not on this
court* is a caller's bug; a **read** keyed on an id is the shape a directory is
probed through, and ``game_not_found`` is one code for two cases, because
separating them would answer *is this id real* about four strangers' evening.
"""

from __future__ import annotations

from app.shared.domain.errors import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
)


class YouWereNotOnThisCourt(ForbiddenError):
    """Somebody who is not on the court, acting on the game.

    **The people who may act are the people on the court now** — never somebody
    who left, never somebody who declined, never a spectator. The line-up is on
    the record, so this is answerable from it alone and needs no other context to
    be asked.
    """

    code = "you_were_not_on_this_court"

    def __init__(self) -> None:
        super().__init__(
            "Only the players of this game may enter or answer its result."
        )


class TheCourtHasAnOpenSeat(ConflictError):
    """*We played* said about a court with a seat open.

    #411 rule 5 withholds the entry on the client while a seat is open, and this
    is what makes that a rule rather than a promise (``docs/adr/0162`` §3): a
    score on a three-person doubles game is a score with a side the engine
    cannot price and a seat with no outcome to give anyone. The seat stays open
    until it is filled, the game is called off, or the entry window closes.
    """

    code = "the_court_has_an_open_seat"

    def __init__(self) -> None:
        super().__init__(
            "This game has a seat open, so it cannot be recorded as played."
        )


class TheGameStartedShort(ConflictError):
    """*We played* said about a booked game whose hour came with a seat open
    (#544; the mechanics §14.1). Somebody left after the club's cut-off and
    nobody took the seat, so the game went ahead short — and it ends
    **uncounted, a seat was empty**: nothing about it can be recorded."""

    code = "the_game_started_short"

    def __init__(self) -> None:
        super().__init__(
            "This game started with a seat empty, so it cannot be recorded as played."
        )


class NotAGameToCallOff(ConflictError):
    """A call-off asked of a game that is not awaiting its entry with a seat open.

    **One code for both halves** (``docs/adr/0163`` §2), because they are one
    sentence — *this is not a game that can be called off*. A court standing
    whole that nobody records lets its window lapse into *Played · no score*
    (#655); a game that has already ended by its clock stays the end it is,
    because a call-off that reached one would flip a standing the platform has
    already drawn and move a record after the fact.

    The booking guarantees the open seat by construction — its cut-off calls
    off only a game short of a player — and the use case steps over a game that
    already started short rather than raising this, so neither half is a code a
    client meets. The aggregate keeps the refusal all the same: the caller is
    one context over, and the server is the correctness mechanism.
    """

    code = "not_a_game_to_call_off"

    def __init__(self) -> None:
        super().__init__(
            "Only a game awaiting its entry with a seat open can be called off."
        )


class TheGameWasCalledOff(ConflictError):
    """*We played* said about a game somebody called off.

    Its own code rather than the window's ``the_entry_window_has_closed`` or the
    umbrella ``the_result_is_settled``, for the window's own reason: the entry
    is the one act a player composes by hand, and it is told which end it met.
    The acceptance meets the umbrella — a tap on a score that is already on the
    table needs no such precision.
    """

    code = "the_game_was_called_off"

    def __init__(self) -> None:
        super().__init__(
            "This game was called off, so it cannot be recorded as played."
        )


class TheGameIsNotOpenToSeating(ConflictError):
    """A seat asked to change on a game that is not awaiting its entry.

    After *we played* — or after the entry window closed on silence — the
    line-up is the record of an evening and nothing on it moves. ``bookings``
    asks whether a seat may still move before it gets here and refuses with its
    own codes, so this is the aggregate's backstop rather than the code a client
    meets — and it has its own code because a code is unique across the
    platform, and this one names what *this* record refuses.
    """

    code = "the_line_up_is_settled"

    def __init__(self) -> None:
        super().__init__(
            "This game has happened, or never will, so its line-up is settled."
        )


class TheEntryWindowHasClosed(ConflictError):
    """*We played* said too late, about a game whose entry window has closed.

    A refusal rather than a late acceptance: a full court nobody recorded
    already reads *Played · no score* to everybody who has looked at it (#655),
    and a score arriving now would contradict a card the platform has already
    drawn.
    """

    code = "the_entry_window_has_closed"

    def __init__(self) -> None:
        super().__init__("This game can no longer be recorded as played.")


class TheResultIsSettled(ConflictError):
    """An act on a game that is over.

    **A settled result is final** — there is no support correction path and no
    reversal — and *over* includes the game that produced no result at all: two
    people who were both on court and cannot agree what happened is not a result,
    and reopening it a day later is the arbitration this platform refused. It
    includes a game that was **called off**, too, on the acceptance — the entry
    names that end with its own code (``TheGameWasCalledOff``).
    """

    code = "the_result_is_settled"

    def __init__(self) -> None:
        super().__init__("This game's result is settled and cannot be changed.")


class AResultMustCarryAScore(BadRequestError):
    """An objection with nothing in it.

    **There is no bare rejection.** A rejection carrying no score is free and
    always optimal for the loser: the result is suspended, their Level never
    moves, and they have said nothing in front of the three people who were
    there. Requiring the score makes the objection specific, falsifiable, and —
    because a counter is itself a proposal — answerable by the other side's
    silence in turn.

    It is refused **here** rather than by a type signature on purpose. The
    aggregate is where this rule is true, and a rule that only a type checker
    enforces is a rule an untyped caller does not meet.
    """

    code = "a_result_must_carry_a_score"

    def __init__(self) -> None:
        super().__init__("A result must carry a score.")


class AScoreMustNameAWinner(BadRequestError):
    """A level set, or a match level in sets.

    **A result names a winner**, and that is the contract rather than a sanity
    check: *Last 5* is win or loss, none of the four sports produces a draw, and
    a set that is level has not finished. A score nobody won would be a row on
    that card the client could not draw and a game the rating context could not
    read.
    """

    code = "a_score_must_name_a_winner"

    def __init__(self) -> None:
        super().__init__("A result must name a winner.")


class AScoreIsNotThisShape(BadRequestError):
    """More sets than any of these sports has, or a number no set reaches.

    A typo guard rather than a rule about any sport: the platform holds no
    opinion about what a tiebreak is worth, and it does hold one about a set
    somebody won 300–2.
    """

    code = "a_score_is_not_this_shape"

    def __init__(self) -> None:
        super().__init__("That is not the shape of a score.")


class YourSideHasAlreadyAnswered(ConflictError):
    """A third score from a court that has already had two.

    **Each side proposes once.** The cap is what bounds an argument to two
    rounds, and it is what makes silence safe to read as agreement: with a third
    turn available, going quiet stops being the last word and starts being a
    tactic.
    """

    code = "your_side_has_already_answered"

    def __init__(self) -> None:
        super().__init__("Your side has already put a score on the table.")


class CorrectionsHaveClosed(ConflictError):
    """A correction arriving after the game's entry window closed (#654;
    ``docs/adr/0195`` §5).

    **Corrections end with the entry window**: a correction re-dates its side's
    score, so a side that kept correcting could keep a game waiting for ever.
    The score it would have corrected still stands and its answer window still
    runs — only the side that put it up can no longer change it.
    """

    code = "corrections_have_closed"

    def __init__(self) -> None:
        super().__init__("The time to correct this score has passed.")


class NobodyHasProposedAResult(ConflictError):
    """An acceptance with nothing to accept."""

    code = "nobody_has_proposed_a_result"

    def __init__(self) -> None:
        super().__init__("There is no result from the other side to accept.")


class AcceptingYourOwnSidesResult(ConflictError):
    """An acceptance from the side that proposed.

    **Acceptance comes only from the opposing side, because a teammate agreeing
    with a teammate proves nothing.** One opponent suffices; the person across
    the net is the whole of the evidence a result was real.
    """

    code = "accepting_your_own_sides_result"

    def __init__(self) -> None:
        super().__init__("Only the other side can accept a result.")


class NoGameOfYoursHasThatId(NotFoundError):
    """A game id that names nothing this reader was on the court of.

    **Two cases and one code, deliberately.** The game does not exist, or it
    exists and this player did not play in it — and the two answer identically,
    because an answer that separated them would tell a caller whether a
    stranger's game id is real. ``YouWereNotOnThisCourt`` is the same fact
    refused to an **act**, and stays a ``403`` there.
    """

    code = "game_not_found"

    def __init__(self) -> None:
        super().__init__("No game of yours has that id.")


class PairingIsHistory(ConflictError):
    """A pairing asked for about a game that has happened, or never will.

    The pairing means what a card means *because this game has not happened*
    (``docs/adr/0143``): after it has, the values are a claim about people made
    from a record that has moved on. So the read answers only while the game is
    awaiting an entry — never after *we played*, never after the entry window
    closed on silence, and never after it was called off.
    """

    code = "pairing_is_history"

    def __init__(self) -> None:
        super().__init__(
            "This game has happened, or never will, so there is no pairing to read."
        )


# --------------------------------------------------------------------------- #
# Who turned up, caught at the court (#657; docs/adr/0195 §3)
#
# **Refusals in plain sentences**: each message is what the player is told, and
# a client may show it as it stands. None names a person; the one that names a
# place names the club, which everybody on the court already knows.
# --------------------------------------------------------------------------- #


class AttendanceIsForBookedGames(ConflictError):
    """An attendance tap on a game with no hour — a stream written before
    bookings. Only a **booked** game has an hour somebody could fail to turn up
    to."""

    code = "attendance_is_for_booked_games"

    def __init__(self) -> None:
        super().__init__("Only a game booked on a court has an hour to turn up to.")


class TheGameHasNotStarted(ConflictError):
    """A score stated, or somebody said not to be here, before a booked game's
    hour: nothing can have happened at a game that has not begun (#654, #657)."""

    code = "the_game_has_not_started"

    def __init__(self) -> None:
        super().__init__("This game hasn't started yet.")


class NotOnThisCourt(BadRequestError):
    """An attendance tap naming somebody who is not on the game. The court is
    the whole of who could have come."""

    code = "not_on_this_court"

    def __init__(self) -> None:
        super().__init__("That player isn't on this game.")


class NotAboutYourself(BadRequestError):
    """*Isn't here yet* or *yes, they were here* said of yourself: the tap is
    the proof that its maker is here, and a confirmation is somebody else's
    word."""

    code = "not_about_yourself"

    def __init__(self) -> None:
        super().__init__("You can't say that about yourself.")


class ALocationFixIsOffTheMap(BadRequestError):
    """A fix whose latitude is not within ±90, whose longitude is not within
    ±180, or whose stated accuracy is not a finite distance. A fix arrives from
    a phone, so it is refused rather than an invariant."""

    code = "a_location_fix_is_off_the_map"

    def __init__(self) -> None:
        super().__init__("That location isn't a place on the map.")


class NotAtTheClub(ConflictError):
    """A tap in the window from somewhere other than the club. **The verdict
    and nothing else** decided it: the fix it carried was measured against the
    club's map point and dropped."""

    code = "not_at_the_club"

    def __init__(self, club_name: str | None = None) -> None:
        super().__init__(f"You can say so only from {club_name or 'the club'}.")


class TheTapWindowHasClosed(ConflictError):
    """*Isn't here yet* or an arrival after the first thirty minutes of the
    game. An arrival that late is not one: a player still awaited then Didn't
    come, and has *I was there* for a day."""

    code = "the_tap_window_has_closed"

    def __init__(self) -> None:
        super().__init__("That can be said only in the first 30 minutes of the game.")


class TheTapWindowIsOpen(ConflictError):
    """*I was there* while the tap window still runs. A player who is at the
    club taps *I'm here*; the late claim is for after the window, for a phone
    that died."""

    code = "the_tap_window_is_open"

    def __init__(self) -> None:
        super().__init__(
            "Tap I'm here at the club. I was there opens once the first "
            "30 minutes of the game are over."
        )


class TheLateClaimHasClosed(ConflictError):
    """*I was there*, or its confirmation, more than a day after the tap window
    closed. *Didn't come* is final."""

    code = "the_late_claim_has_closed"

    def __init__(self) -> None:
        super().__init__("The 24 hours to say they were there have passed.")


class AlreadyArrived(ConflictError):
    """*Isn't here yet*, an arrival or *I was there* about a player whose
    arrival is already noted. The first arrival is the one that counts."""

    code = "already_arrived"

    def __init__(self) -> None:
        super().__init__("They're already here.")


class YouAreNotHereYourself(ConflictError):
    """A tap about somebody else, or a confirmation, from a player who is
    themselves awaited or Didn't come. Somebody not at the court cannot say who
    else is, and two absentees cannot vouch for each other."""

    code = "you_are_not_here_yourself"

    def __init__(self) -> None:
        super().__init__("You're marked as not here yourself.")


class NobodySaidTheyWereNotHere(ConflictError):
    """An arrival, or *I was there*, about a player nobody tapped. Everybody who
    arrives on time does nothing: there is nothing to record."""

    code = "nobody_said_they_were_not_here"

    def __init__(self) -> None:
        super().__init__("Nobody has said they aren't here.")


class NothingToConfirm(ConflictError):
    """*Yes, they were here* about a player who has not said *I was there*."""

    code = "nothing_to_confirm"

    def __init__(self) -> None:
        super().__init__("They haven't said they were there.")


class SomebodyIsNotHereYet(ConflictError):
    """A score while a player tapped *isn't here yet* is still awaited: if they
    never come the game takes no score, so it waits until they arrive or the
    first thirty minutes are over."""

    code = "somebody_is_not_here_yet"

    def __init__(self) -> None:
        super().__init__(
            "Somebody isn't here yet. The score waits until they arrive or the "
            "first 30 minutes are over."
        )


class SomebodyDidntCome(ConflictError):
    """A score on a game somebody Didn't come to: it takes no score and never
    counts — unless their *I was there* is confirmed, which makes them Came
    late and the game carries on."""

    code = "somebody_did_not_come"

    def __init__(self) -> None:
        super().__init__("Somebody didn't come, so this game takes no score.")
