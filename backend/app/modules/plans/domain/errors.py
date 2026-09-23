"""What this context refuses, and why each refusal is a refusal and not a no-op.

Three families, and the third is the one with an argument behind it.

**Who may write, and whether there is still anything to write on.** Two codes,
and they are *the port's one question* asked in two halves (``docs/adr/0148``
§8, ``docs/adr/0164`` §3) — *is this player on this court, and is that court
still open to planning*. ``plan_not_found`` is a 404 for a non-member on
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

**A plan that is not complete yet, and a court that is not whole yet.** Two
refusals, and they are the shape the *act* takes where the three above are about
a value. Both are **conflicts** rather than bad requests: the body carried
nothing at all, and what is wrong is the state of the plan (``docs/adr/0155``)
or of the court it is for (``docs/adr/0164`` §5). They are two codes because the
card draws a different thing for each — a greyed button, and the count line
where the button will be.

**Nothing here empties a slot, unmakes a plan, unlocks one or cancels a game**,
because there is no act that does any of those (``docs/adr/0144``,
``docs/adr/0155``). A refusal exists for something somebody can ask for; these
are not asks with answers, they are asks with no route.
"""

from __future__ import annotations

from app.shared.domain.errors import (
    BadRequestError,
    ConflictError,
    NotFoundError,
)


class PlanNotFound(NotFoundError):
    """No plannable court of **yours** has that id.

    **One code for three cases** — there is no challenge with that id, there is
    one and you were never on its court, or you were asked and have not said
    yes. They are not told apart on purpose: separating them would answer *is
    this id real* about four strangers' evening, which is ``challenges``' and
    ``games``' rule holding one context over — and telling an invitee still
    deciding that there *is* a plan would be the read-only card
    ``docs/adr/0164`` §3 deliberately withholds.

    It is also what a **read** never raises. Every plan read is scoped to the
    courts the reader holds an accepted seat on, so there is no id to be refused
    about.
    """

    code = "plan_not_found"

    def __init__(self) -> None:
        super().__init__("There is no plan of yours with that id.")


class PlanIsHistory(ConflictError):
    """The court is over, so the slots are frozen.

    **The only thing that freezes them** (``docs/adr/0144``), and **the lock is
    not it** (``docs/adr/0155``): a locked plan stays editable by every member,
    and this is the one state that does not. A court is history once its game
    has left its entry window — once it can no longer be said to have happened
    — or, before any game, once the challenge itself has ended
    (``docs/adr/0164`` §3). A write that went through would edit a note about
    an evening that is over, in a room where nobody is arranging anything any
    more.

    It refuses the lock as it refuses a slot write: past that point there is
    nothing left to agree.
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
    """A day past the anchor plus ``PLAN_HORIZON``.

    The clamp, refused server-side (``docs/adr/0144``). A plan naming a day on
    which *we played* is no longer sayable would walk the card from *Game on* to
    *Never played* while the plan still read *next Saturday*. The anchor is the
    challenge's send until the game exists and ``planned_at`` after, and it only
    ever moves later (``docs/adr/0164`` §4) — so a day admitted under the first
    is still admitted under the second.
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


class ThePlanIsNotComplete(ConflictError):
    """A lock asked for on a plan with a slot still empty.

    **A refusal and not a silent no-op**, which is deliberately the opposite
    shape from locking a plan that is already locked (``docs/adr/0155``). A
    second lock lands exactly the state its caller asked for and so records
    nothing; an incomplete plan does not, and answering `200` would leave a
    client believing it had agreed one.

    **A conflict rather than a bad request.** Nothing was sent — the body carried
    nothing at all — so there is no field to be wrong; what is wrong is the state
    of the plan the act was aimed at.
    """

    code = "the_plan_is_not_complete"

    def __init__(self) -> None:
        super().__init__("Set all three before locking the plan.")


class TheCourtIsNotWhole(ConflictError):
    """A lock asked for while a seat on the court is still open or unanswered.

    **The lock waits for the court** (``docs/adr/0164`` §5). Where, day and hour
    are proposals anybody on the court may make and move; *we are agreed* is
    said only once everybody who will have to keep it is in. So a plan two of
    four have filled to the brim is refused here, on the court, and the card
    draws the count line where the button will be — never a greyed button, which
    is ``the_plan_is_not_complete``'s shape and the reason the two are two codes.

    **A conflict rather than a bad request**, on ``ThePlanIsNotComplete``'s
    argument: the request carried nothing at all, and what is wrong is the state
    of the court the act was aimed at. It is asked **before** the count, because
    the count is a fact about a button and there is no button until the court is
    whole.

    **It does not unmake a lock.** A departure after the lock opens a seat and
    the plan stays locked; the refusal is only for a lock not yet taken.
    """

    code = "the_court_is_not_whole"

    def __init__(self) -> None:
        super().__init__("Lock the plan once everyone is in.")
