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
probed through, and ``game_not_found`` is ``challenge_not_found``'s argument
verbatim — one code for two cases, because separating them would answer *is
this id real* about four strangers' evening.
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
    whole that will not play lets its window lapse into *Never played*, as it
    always has (#411 rule 4); a game that has already ended by its clock stays
    the end it is, because a call-off that reached a ghost would flip a standing
    the platform has already drawn and un-charge a strand after the fact.

    The challenge guarantees the open seat by construction — *Call it off* is
    admitted in ``LINE_UP_INCOMPLETE`` and nowhere else — and the use case steps
    over a game already ended by its clock rather than raising this, so on the
    withdrawal route neither half is a code a client meets. The aggregate keeps
    the refusal all the same: the button is UX, and the server is the
    correctness mechanism.
    """

    code = "not_a_game_to_call_off"

    def __init__(self) -> None:
        super().__init__(
            "Only a game awaiting its entry with a seat open can be called off."
        )


class TheGameWasCalledOff(ConflictError):
    """*We played* said about a game somebody called off.

    Its own code rather than the ghost's ``the_entry_window_has_closed`` or the
    umbrella ``the_result_is_settled``, for the ghost's own reason: the entry is
    the one act a player composes by hand, and it is told which end it met. The
    acceptance meets the umbrella, as it does on a ghost — a tap on a score that
    is already on the table needs no such precision.
    """

    code = "the_game_was_called_off"

    def __init__(self) -> None:
        super().__init__(
            "This game was called off, so it cannot be recorded as played."
        )


class GameIsNotCalledOff(ConflictError):
    """A dismissal asked of a game on any standing but ``CALLED_OFF``.

    Its own code (``docs/adr/0172`` §5), because the other endings' cards are
    the record for the day they stay — *Never played*, *Counted* and
    *Uncounted* carry a score or a strand's verdict — and a live game's card is
    the game. Widening the trash is a design of its own and is out of scope by
    name, so the refusal says which standing the act wants rather than an
    umbrella.
    """

    code = "game_is_not_called_off"

    def __init__(self) -> None:
        super().__init__("Only a called-off game's card can be dismissed.")


class TheGameIsNotOpenToSeating(ConflictError):
    """A seat asked to change on a game that is not awaiting its entry.

    After *we played* — or after the entry window closed on silence — the
    line-up is the record of an evening and nothing on it moves. ``challenges``
    asks the moment guard before it gets here and refuses with its own
    ``game_is_history``, so this is the aggregate's backstop rather than the
    code a client meets — and it has its own code because a code is unique
    across the platform, and this one names what *this* record refuses.
    """

    code = "the_line_up_is_settled"

    def __init__(self) -> None:
        super().__init__(
            "This game has happened, or never will, so its line-up is settled."
        )


class TheEntryWindowHasClosed(ConflictError):
    """*We played* said too late, about a game that is now a ghost.

    A refusal rather than a late acceptance: the game already reads as never
    played to everybody who has looked at it, and an entry that resurrected it
    would contradict a card the platform has already drawn.
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


class TheOtherSideHasAnswered(ConflictError):
    """A correction arriving after the other side responded.

    Correcting is free **until the other side responds** and not afterwards: past
    that point the score has been read and answered, and revising it would be a
    second proposal wearing a correction's name.
    """

    code = "the_other_side_has_answered"

    def __init__(self) -> None:
        super().__init__(
            "The other side has answered, so this score can no longer be corrected."
        )


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


class TheResultIsAlreadyAccepted(ConflictError):
    """An acceptance of a score the accepter's side has already agreed to."""

    code = "the_result_is_already_accepted"

    def __init__(self) -> None:
        super().__init__("Your side has already accepted this result.")


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
# Somebody did not come (#547; the mechanics §15.3)
# --------------------------------------------------------------------------- #


class NoShowsAreForBookedGames(ConflictError):
    """*Kuba didn't come*, said of a game a completed line-up opened. Only a
    **booked** game has an hour somebody could fail to turn up to: a Classic
    play game is the arrangement's, and its people say whether they played."""

    code = "no_shows_are_for_booked_games"

    def __init__(self) -> None:
        super().__init__("Only a booked game can report somebody who did not come.")


class TheGameHasNotStarted(ConflictError):
    """A no-show reported before the game's hour: nobody can have failed to
    turn up to a game that has not begun."""

    code = "the_game_has_not_started"

    def __init__(self) -> None:
        super().__init__("This game has not started yet.")


class AResultIsAlreadyEntered(ConflictError):
    """A no-show reported on a game somebody already said they played, with a
    score: a score is four people on a court, and a report that one of them
    was not there contradicts it. The score's own answers are the way to
    disagree with it."""

    code = "a_result_is_entered"

    def __init__(self) -> None:
        super().__init__("A result is already entered for this game.")


class ANoShowIsReported(ConflictError):
    """A score entered while a player's report of not turning up waits out its
    day. The game does not count whatever the report comes to — it stands, or
    it is disputed and nobody arbitrates — so there is no score to enter."""

    code = "a_no_show_is_reported"

    def __init__(self) -> None:
        super().__init__("Somebody was reported as not coming to this game.")


class NotOnThisCourt(BadRequestError):
    """A no-show reported of somebody who was not on the game. The court is the
    whole of who could have come."""

    code = "not_on_this_court"

    def __init__(self) -> None:
        super().__init__("That player was not on this game.")


class YouCannotReportYourself(BadRequestError):
    """A player reporting themselves as not turning up — the one person whose
    presence the act proves."""

    code = "you_cannot_report_yourself"

    def __init__(self) -> None:
        super().__init__("You cannot report yourself as not coming.")


class CheckedInAtTheClub(ConflictError):
    """A no-show reported of a player the club's desk checked in (the mechanics
    §15.1, §16.10): the scan is evidence they were there, so they can never be
    reported."""

    code = "checked_in_at_the_club"

    def __init__(self) -> None:
        super().__init__("The club checked this player in.")


class YouWereReportedAsANoShow(ConflictError):
    """A player reported as not turning up reporting somebody else. Their answer
    is the dispute, inside their day; two reports pointing at each other would
    be the arbitration this platform refuses to make."""

    code = "you_were_reported_as_a_no_show"

    def __init__(self) -> None:
        super().__init__("You were reported as not coming; dispute it instead.")


class NobodyReportedYou(ConflictError):
    """A dispute from a player nobody reported as not turning up."""

    code = "nobody_reported_you"

    def __init__(self) -> None:
        super().__init__("Nobody reported you as not coming to this game.")


class TheDisputeWindowHasClosed(ConflictError):
    """A dispute after the reported player's day: the report stands, and the
    record already shows it."""

    code = "the_dispute_window_has_closed"

    def __init__(self) -> None:
        super().__init__("The day to dispute this report has passed.")
