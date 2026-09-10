"""The plan wire shapes — **a note between people, and never a booking.**

Five rules decide everything below.

**A slot carries its value and nothing else** (``docs/adr/0148`` §8). No
``set_by``, no ``set_at``. Every change writes a system line naming who and what,
and *those lines are this context's history* — so attribution on a slot would be
the second place one fact is true, in a record whose own decision is that it
stores nothing it can derive. The game screen draws the plan read-only and never
needed it.

**``locked_at`` is not a violation of that rule**, because it is not on a slot.
The lock is an **act** rather than a value (``docs/adr/0155``), and its moment is
the only thing a client draws it by — there is no locked *state* to send, since a
locked plan is not a frozen one and nothing else about it changes. Who locked it
is still on the line in the room, exactly like every other attribution here.

**The agreed point is derived and sent.** It is a timezone conversion the client
must not redo, and it is present the moment a *day* is recorded — the agreed
instant when the hour is there, the start of the following local day when it is
not (``docs/adr/0145`` §3).

**The list carries no ``read_at``.** A plan folds nothing against the clock, so
there is no instant for it to have been folded against, and the card is folded
against ``games``' own — which is what gives Now one clock by construction rather
than by convention (``docs/adr/0148`` §10).

**There is no slot count and no card name.** Both are folds over what is here,
and the ladder that reads them is the client's ``domain/``: a card name on the
wire would be this context deciding what a screen says, and a count would be the
one derived value that could disagree with the three fields beside it.
"""

from __future__ import annotations

from datetime import date, datetime, time
from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.plans.domain.slots import (
    EARLIEST_HOUR,
    HOUR_STEP_MINUTES,
    LATEST_HOUR,
    PLACE_LENGTH_CAP,
    PLATFORM_ZONE,
    as_wall_time,
)

#: The two ends of the offered grid, spelled for a human reading the contract.
#: Rendered through the domain's own inverse rather than formatted here, so the
#: documentation cannot drift from the rule it describes.
_FIRST_HOUR = as_wall_time(EARLIEST_HOUR).isoformat("minutes")
_LAST_HOUR = as_wall_time(LATEST_HOUR).isoformat("minutes")


class PlanSchema(BaseModel):
    """One game's plan: three slots and the moment they name.

    **Keyed on the game and on nothing else.** A plan has no id of its own —
    ``game_id`` identifies it, for ever, and a second identity beside that would
    be a second name for one thing.

    Each slot is nullable and an empty one is spelled ``null``. **A slot is never
    emptied**, so a ``null`` here is a slot that has never been filled and never a
    slot somebody cleared; the client draws the slot's name in its place.
    """

    game_id: UUID = Field(
        ...,
        description=(
            "The game this plan is for. **A plan is one game's, for ever** — "
            "join it against `GET /games` by this."
        ),
    )
    place: str | None = Field(
        None,
        description=(
            "Where these people are meeting, as somebody typed it. **Short free "
            "text, one line** — never an id, a lookup, an autocomplete, a reuse "
            "or a geocode, and **nothing anywhere reads it**. It is a note "
            "between the people on the court and never a place the platform "
            "knows."
        ),
    )
    day: date | None = Field(
        None,
        description=(
            f"The local day, in the platform's one zone (`{PLATFORM_ZONE}`). "
            "**A wall-clock fact, drawn literally and never counted down** — "
            "nothing expires at the end of it."
        ),
    )
    hour: time | None = Field(
        None,
        description=(
            "The local clock time. **The agreement itself, not a guess at a "
            "booking**: nothing on this platform will ever hold a court, so "
            "nothing can contradict it."
        ),
    )
    agreed_point: datetime | None = Field(
        None,
        description=(
            "The moment this plan names, **derived and never stored**. The "
            "agreed instant when the day and the hour are both recorded; the "
            "**start of the following local day** when only the day is; `null` "
            "when no day is.\n\n"
            "Coarsened **later, never earlier**, so nobody is asked for a result "
            "before they could have played. It is sent because it is a timezone "
            "conversion the client must not redo."
        ),
    )
    locked_at: datetime | None = Field(
        None,
        description=(
            "The moment somebody agreed this plan, or `null` while nobody "
            "has.\n\n"
            "**A locked plan is not a frozen one.** Any member may still move "
            "any slot afterwards, and each move writes its own system line — "
            "there is no un-agreeing to fear, only re-agreeing. The plan stays "
            "locked and the line trail is the friction, as it already is for "
            "every change.\n\n"
            "**There is no unlock**, and this never returns to `null`. The lock "
            "is a thing that happened.\n\n"
            "**It is not the slot count under another name**: a plan with all "
            "three slots filled is one everybody *could* agree, and this says "
            "somebody did."
        ),
    )


class PlanListResponse(BaseModel):
    """Every plan for the games you are on the court of.

    **No `read_at`, and that is deliberate.** A plan folds nothing against the
    clock, so there is no instant for it to have been folded against — the card
    is folded against `GET /games`' own `read_at`, which is what keeps Now on one
    clock by construction (``docs/adr/0148`` §10).

    **A game with nothing agreed is absent**, not present with three nulls. *No
    plan* is what such a game draws, and one spelling for it is what stops an
    empty plan being told apart from a missing one.
    """

    plans: list[PlanSchema]


class SetPlaceRequest(BaseModel):
    """*We are meeting here.*"""

    place: str = Field(
        ...,
        description=(
            "Where you are meeting. Runs of whitespace collapse to one space, so "
            "the value is one line; empty after that is `the_place_is_empty`, "
            f"and past {PLACE_LENGTH_CAP} characters is `the_place_is_too_long`. "
            "**Neither is silently fixed** — a shortened note is one the person "
            "who typed it believes they wrote whole, in front of the other "
            "people on the court.\n\n"
            "**The cap is not declared here on purpose.** A `maxLength` would "
            "make an over-long note a `422` about a field, where it is a "
            "refusal this context owns and names — the same shape "
            "`POST /conversations/{id}/messages` already takes."
        ),
    )


class SetDayRequest(BaseModel):
    """*We are playing on this day.*"""

    day: date = Field(
        ...,
        description=(
            "A local day in the platform zone, **clamped to the game's own "
            "planning horizon** — so a plan can never name a day past the entry "
            "window, and the row of days a client offers shrinks as the week "
            "runs out."
        ),
    )


class SetHourRequest(BaseModel):
    """*We are playing at this time.*"""

    hour: time = Field(
        ...,
        description=(
            f"A local clock time in **{HOUR_STEP_MINUTES}-minute steps between "
            f"{_FIRST_HOUR} and {_LAST_HOUR}**, validated "
            "server-side. Bounded chips the platform offered, never a free "
            "instant: the grid a client draws is a convention, and this is what "
            "makes it true."
        ),
    )
