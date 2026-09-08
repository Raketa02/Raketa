"""What this context refuses, and why each refusal is a refusal and not a no-op.

Three families, and the third is the one with an argument behind it.

**Who may write, and whether there is still anything to write on.** Two codes,
and they are *the port's one question* asked in two halves (``docs/adr/0148``
§8) — *is this player on this game's court, and is that game still open to
planning*. ``plan_not_found`` is a 404 for a non-member on
``challenge_not_found``'s argument verbatim: one code for two cases, because a
403 would answer *is this id real* about a stranger's evening.

**The shape of a value.** A *where* that says nothing or says too much, and an
hour nobody offered. All three arrive from a person composing a value by hand or
tapping a chip, so they are refusals with codes rather than ``invariant``s — the
split ``CONTEXT.md``'s *Invariant vs Unavailability* names.

**A moment that has already gone.** One refusal, raised from either of the two
slots that can produce it, because the day and the hour are filled in either
order and either one can be the second. It names both remedies and no value:
``the-words.md`` §22.2's *"That moment has already passed — change the day or the
hour"*, and the platform has no opinion about which of the two is the wrong one.

**Nothing here empties a slot, unmakes a plan or cancels a game**, because there
is no act that does any of those (``docs/adr/0144``). A refusal exists for
something somebody can ask for; these are not asks with answers, they are asks
with no route.
"""

from __future__ import annotations

from app.shared.domain.errors import (
    BadRequestError,
    ConflictError,
    NotFoundError,
)


class PlanNotFound(NotFoundError):
    """No plannable game of **yours** has that id.

    **One code for two cases** — there is no game with that id, or there is one
    and you were not on its court. They are not told apart on purpose: separating
    them would answer *is this id real* about four strangers' evening, which is
    ``challenges``' and ``games``' rule holding one context over.

    It is also what a **read** never raises. Every plan read is scoped to the
    games the reader is on the court of, so there is no id to be refused about.
    """

    code = "plan_not_found"

    def __init__(self) -> None:
        super().__init__("There is no plan of yours with that id.")


class PlanIsHistory(ConflictError):
    """The game left its entry window, so the slots are frozen.

    **The only thing that freezes them** (``docs/adr/0144``), and it is not a
    lock: once the game can no longer be said to have happened, the plan is
    history. A write that went through would edit a note about an evening that is
    over, in a room where nobody is arranging anything any more.
    """

    code = "plan_is_history"

    def __init__(self) -> None:
        super().__init__("This game is over, so its plan can no longer change.")


class ThePlaceIsEmpty(BadRequestError):
    """A *where* with nothing in it.

    **A slot may be changed but never emptied** (``docs/adr/0144``), so a blank
    value is not a way of clearing one — it is a value that says nothing, and it
    is refused rather than stored.
    """

    code = "the_place_is_empty"

    def __init__(self) -> None:
        super().__init__("Say where you are meeting.")


class ThePlaceIsTooLong(BadRequestError):
    """Past the cap. **Refused, never truncated.**

    A shortened *where* is one the person who typed it believes they wrote whole,
    in front of the other people on the court.
    """

    code = "the_place_is_too_long"

    def __init__(self) -> None:
        super().__init__("That is longer than a one-line note about where to meet.")


class TheDayIsPastTheHorizon(BadRequestError):
    """A day past ``planned_at + PLAN_HORIZON``.

    The clamp, refused server-side (``docs/adr/0144``). A plan naming a day on
    which *we played* is no longer sayable would walk the card from *Game on* to
    *Never played* while the plan still read *next Saturday*.
    """

    code = "the_day_is_past_the_horizon"

    def __init__(self) -> None:
        super().__init__("That day is past this game's planning window.")


class TheHourIsNotOffered(BadRequestError):
    """An hour outside the grid, or between two steps of it.

    **Bounded chips the platform offered, never a free instant** (``docs/adr/0145``
    §9). The client drawing the grid is a convention; this is what makes it true.
    """

    code = "the_hour_is_not_offered"

    def __init__(self) -> None:
        super().__init__("That is not one of the times this app offers.")


class ThatMomentHasAlreadyPassed(ConflictError):
    """The day and the hour together name a moment that has gone.

    **Raised when the second of the two is filled, in either order**, and it
    names neither of them: the sentence is true whichever pair produced it and
    the platform has no opinion about which one is wrong.
    """

    code = "that_moment_has_already_passed"

    def __init__(self) -> None:
        super().__init__("That moment has already passed.")
