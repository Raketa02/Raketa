"""Matches errors.

No route mounts this context in v1 — `GET /api/v1/now` is
``Raketa02/Raketa#73`` and every act off it is a ticket of its own — so none of
these has been rendered as JSON yet. They carry a status and a code anyway, for
the reason ``app/shared/domain/errors.py`` gives: a status held in a separate
registry is one a new subclass can be added without, and the miss is a 500 in
production rather than a red test.

**``ConcurrentMatchModification`` is the one to read.** ADR-0034 answers the
event-sourcing question with *no* and takes its concurrency from a version on a
row instead — *"two concurrent writers cannot interleave: one wins, one
retries"*. This is the losing writer being told so. It is never a merge, and it
is never silent: a match that quietly took two writes at one version is a match
whose seat count and whose money disagree, and nothing downstream would look
wrong.
"""

from __future__ import annotations

from app.shared.domain import BadRequestError, ConflictError, NotFoundError


class MatchNotFound(NotFoundError):
    """No match with this id."""

    code = "match_not_found"

    def __init__(self) -> None:
        super().__init__("Match not found.")


class SeatNotFound(NotFoundError):
    """This match has no seat at that position."""

    code = "match_seat_not_found"

    def __init__(self) -> None:
        super().__init__("That seat does not exist on this match.")


class ConcurrentMatchModification(ConflictError):
    """The stored version moved while this match was in hand.

    The caller reloads and retries, or gives up. What it must not do is write
    anyway: the version guard is the whole of ADR-0034's concurrency story, and
    a writer that catches this and re-issues the same UPDATE without reloading
    has removed it.
    """

    code = "match_concurrently_modified"

    def __init__(self) -> None:
        super().__init__("This match was modified by someone else. Try again.")


class MatchAlreadySettled(ConflictError):
    """Nothing further can happen to this match.

    The four cancellations and the lost-inventory ending, which is what
    ``kernel.is_terminal`` means. A played match is **not** settled in this
    sense: a score can still be entered, and the card still moves.
    """

    code = "match_already_settled"

    def __init__(self) -> None:
        super().__init__("This match is over.")


class MatchAlreadyStarted(ConflictError):
    """The match has begun, and this write belongs before it."""

    code = "match_already_started"

    def __init__(self) -> None:
        super().__init__("This match has already started.")


class SeatAlreadyTaken(ConflictError):
    """Somebody is already on that seat."""

    code = "match_seat_taken"

    def __init__(self) -> None:
        super().__init__("That seat is taken.")


class SeatNotTaken(ConflictError):
    """Nobody is on that seat."""

    code = "match_seat_not_taken"

    def __init__(self) -> None:
        super().__init__("Nobody is on that seat.")


class SeatAlreadyPaid(ConflictError):
    """That seat's money has already landed.

    Refused rather than shrugged off, because the alternative is a second
    movement against a seat that owes nothing — and Money is the one context
    where a duplicate is not a no-op.
    """

    code = "match_seat_already_paid"

    def __init__(self) -> None:
        super().__init__("That seat is already paid for.")


class PlayerAlreadyHoldsASeat(ConflictError):
    """This player is already in this match.

    One player, one seat. Two would make *how full is this match* and *how many
    people are playing* different numbers, and every counting sentence on the
    card is written as though they are the same.
    """

    code = "match_player_already_seated"

    def __init__(self) -> None:
        super().__init__("You already hold a seat in this match.")


class MatchIsFull(ConflictError):
    """Every seat is taken."""

    code = "match_is_full"

    def __init__(self) -> None:
        super().__init__("This match is full.")


class VacancyAlreadyFilled(ConflictError):
    """That hole has already been closed."""

    code = "match_vacancy_already_filled"

    def __init__(self) -> None:
        super().__init__("That vacancy has already been filled.")


class CourtAlreadyHeld(ConflictError):
    """A court is already being held for this match."""

    code = "match_court_already_held"

    def __init__(self) -> None:
        super().__init__("A court is already held for this match.")


class NoCourtHeld(ConflictError):
    """No court is being held for this match, so none can be given back."""

    code = "match_no_court_held"

    def __init__(self) -> None:
        super().__init__("No court is held for this match.")


class MatchNotPrivate(ConflictError):
    """Only a private court has seats to open to the marketplace.

    An open match's seats are all on sale already, which is what makes it open.
    """

    code = "match_not_private"

    def __init__(self) -> None:
        super().__init__("Only a private court can open seats.")


class ResultAlreadyAgreed(ConflictError):
    """The score has settled and nothing more is asked of anybody."""

    code = "match_result_already_agreed"

    def __init__(self) -> None:
        super().__init__("This match's result is already settled.")


class NoScoreOnTheTable(ConflictError):
    """There is nothing to agree with."""

    code = "match_no_score_proposed"

    def __init__(self) -> None:
        super().__init__("No score has been proposed for this match.")


class MatchNotPlayed(ConflictError):
    """The match has not been played yet, so there is nothing to say about it."""

    code = "match_not_played"

    def __init__(self) -> None:
        super().__init__("This match has not been played yet.")


class ResultWindowClosed(ConflictError):
    """The twenty-four hours are up and a score can no longer be entered.

    The kernel's own boundary (``kernel.result_window``): past it the ladder
    answers ``playedNoScore``, so a score accepted here would be one the screen
    could never show. Not entering one carries no penalty — a match nobody
    agreed on is an evening, not evidence (ADR-0049).
    """

    code = "match_result_window_closed"

    def __init__(self) -> None:
        super().__init__("It is too late to enter a score for this match.")


class StartMustBeInTheFuture(BadRequestError):
    """A match cannot be moved to a moment that has already passed."""

    code = "match_start_in_the_past"

    def __init__(self) -> None:
        super().__init__("A match can only be moved to a future time.")
