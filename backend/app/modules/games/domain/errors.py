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
"""

from __future__ import annotations

from app.shared.domain.errors import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
)


class YouWereNotOnThisCourt(ForbiddenError):
    """Somebody who did not play, acting on the result.

    **The people who may act are the people who were seated when the line-up
    completed** — never a leaver, never somebody who declined, never a spectator.
    A game's line-up is frozen at the plan, so this is answerable from the record
    alone and needs no other context to be asked.
    """

    code = "you_were_not_on_this_court"

    def __init__(self) -> None:
        super().__init__(
            "Only the players of this game may enter or answer its result."
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
    and reopening it a day later is the arbitration this platform refused.
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
