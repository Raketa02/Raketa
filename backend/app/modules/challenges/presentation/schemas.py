"""The challenge wire shapes — **a court, and never a verdict about a person.**

Three rules decide everything below.

**A refusal names nobody, so neither does a response about one.** There is no
shape here in which a withheld seat, a gate or a reason could arrive: a refused
send answers with a code and an empty body, and the client re-reads the two
sources it already owns.

**The standing is derived and travels as a code.** ``Standing`` is five values and
the words for them are the client's (``docs/adr/0022``). It is on the response
because it is a fold of the seats against the moment the list was read — and it is
**not** on the aggregate, in the store, or anywhere a second copy could go stale.

**A seat carries its own deadline and no standing of its own.** Whether it is
waiting, lapsed or open is read off ``answer`` and ``answer_by`` against the
clock, so a client renders *how long you have* from a moment the backend computed
rather than one a phone derived.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.engines.matchfit.core import SearchMode
from app.kernel import Sport
from app.modules.challenges.domain.seats import SeatAnswer, Side
from app.modules.challenges.domain.standing import Standing
from app.modules.player_profile.domain.availability import Window


class SeatChoiceSchema(BaseModel):
    """One position on the court as the organiser left it.

    **An empty seat is a seat**, so ``player_id`` is genuinely optional: an A-side
    full with a B-side short is a different court from the reverse, and the next
    invitee's side is not a free choice.

    There is no origin field and no position. Where each invitation came from is
    resolved server-side against the cited search, because a position a client
    sent would be true only while the client was honest about where it had
    scrolled to.
    """

    side: Side = Field(..., description="Which side of the net this seat is on")
    player_id: UUID | None = Field(
        default=None,
        description=(
            "Who is to sit here, or omitted for a seat nobody was put in. The "
            "organiser holds one of these like anybody else."
        ),
    )


class SendChallengeRequest(BaseModel):
    """One press. **The court, and the search it was built on.**

    ``search_id`` is the origin, and it is one search for the whole court: the
    arrangement was built and forecast against a single answer, and a court
    assembled out of two searches is a court no forecast was ever computed for.

    **The sport, the kind of evening and the week are not sent.** All three are
    read off that search's own record — there is no window picker anywhere
    (``docs/adr/0100``), and a player changes their window by changing their grid.
    """

    search_id: UUID = Field(
        ...,
        description=(
            "The search this court was built from. **Required** — every invitee "
            "must have appeared in it, and each seat cites where they sat."
        ),
    )
    court: list[SeatChoiceSchema] = Field(
        ...,
        description=(
            "The sides as you arranged them, in the court's own order: every "
            "**A** seat, then every **B**. It must be the sport's shape and you "
            "must be in it."
        ),
    )


class SentChallengeResponse(BaseModel):
    """What a send answers with. **An id, and deliberately nothing else.**

    Not the challenge: nobody has answered it yet, so every seat says exactly
    what the organiser just sent, and a body repeating their own arrangement back
    at them is a round trip that says nothing. The id is what the client keeps.
    """

    challenge_id: UUID = Field(..., description="The challenge that now stands")


class SeatSchema(BaseModel):
    """One seat: a side, its occupant, their answer and their own deadline.

    ``answer_by`` is **this seat's own**, dated when this seat was invited — a
    seat filled later starts its own day and cannot inherit a deadline from a send
    it was not part of. It is absent exactly when nobody was asked: an empty seat,
    the organiser's, and both seats of a challenge born from a mutual yes.
    """

    side: Side
    player_id: UUID | None = Field(
        default=None, description="Who holds this seat, or absent if nobody does"
    )
    answer: SeatAnswer | None = Field(
        default=None,
        description=(
            "What they did about being asked, or absent while they have not "
            "answered. **A lapse is not a refusal** — they are different facts "
            "and the platform counts them apart."
        ),
    )
    answer_by: datetime | None = Field(
        default=None,
        description=(
            "When this seat's answer stops being wanted. Past it the seat reads "
            "as lapsed whether or not anything has swept it, and a late answer "
            "is refused rather than accepted late."
        ),
    )


class ChallengeSchema(BaseModel):
    """One challenge, with its whole court and what it is right now."""

    challenge_id: UUID
    sport: Sport
    mode: SearchMode | None = Field(
        default=None,
        description=(
            "The kind of evening it was sent for. Absent when the surface it came "
            "from has none — the deck asks nobody to pick one — and on every "
            "challenge born of a mutual yes."
        ),
    )
    window: Window | None = Field(
        default=None,
        description=(
            "How soon the week this was proposed for comes round. **Derived at "
            "send from the grid the search ran on** and never asked for. Absent "
            "on a mutual-born challenge: no grid was proposed from."
        ),
    )
    organiser_id: UUID = Field(
        ...,
        description=(
            "Whose proposal this is. Their seat is **accepted from birth** — they "
            "are the one asking."
        ),
    )
    standing: Standing = Field(
        ...,
        description=(
            "What this challenge is at the instant it was read. **Derived from "
            "the seats and the clock, never stored**, so it is right for the "
            "whole gap between a deadline and anything noticing."
        ),
    )
    opened_at: datetime
    seats: list[SeatSchema] = Field(
        ...,
        description=(
            "The court in its fixed order — every **A** seat, then every **B**. "
            "Empty seats are in the list, because which side is short is part of "
            "what a court is."
        ),
    )


class ChallengeListResponse(BaseModel):
    """Your challenges, newest first.

    **One list and not two.** *Challenge sent* and *Challenge for you* are one
    standing read from two sides, so nothing here splits them: the client tells
    them apart by whether ``organiser_id`` is yours.

    **Ended challenges are in it, and their standing says so.** A list that
    quietly dropped this morning's lapse would be the same class of lie as a
    read-back that got shorter.
    """

    challenges: list[ChallengeSchema]
