"""The *Let's play* wire shapes — **three shapes around three numbers.**

``docs/adr/0127`` §6 draws the line: ``INTEREST_TTL``,
``OUTSTANDING_INTEREST_CAP`` and ``PASS_SUPPRESS`` are **ruleset configuration**,
and what is *contract* is the shapes around them — ``expires_at`` on an outgoing
row, the ``outstanding`` / ``cap`` / ``ttl_days`` triple plus the refusal code,
and, for ``PASS_SUPPRESS``, nothing at all.

So: **the client never hardcodes any of the three and never computes an expiry.**
It renders a number the backend sent and a moment the backend computed, because a
phone in somebody's hand can be months behind the backend — which is the whole
reason that line was drawn where it was. ``ttl_days`` is that rule applied to
the one sentence that needs the number itself (``docs/adr/0169`` §5): the deck's
ending says *your yeses stay live for N days*, and N crosses rather than being
held.

**There is no incoming list here, and there is no shape one could arrive in.**
``docs/adr/0109`` refuses an inbox: a one-sided yes was banked under a promise of
silence, and the only way somebody else's yes reaches its recipient is as a
mutual — which they can only see because they said yes first. The one thing
that promise was narrowed by is a **count**, and it crosses on the deal's pool
and not here (``docs/adr/0169`` §4, ``PoolSchema.want_to_play_you``): how many
are waiting, never who.

**Nothing here says how full anybody's inbox is.** Challenge load prints as a
coarse code on a candidate row and nowhere else; a number about somebody else's
popularity is not a fact this product hands out.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.kernel import Sport


class ExpressInterestRequest(BaseModel):
    """One tap. **Three fields, and the third is not optional.**

    ``search_id`` is the **origin key**: it says which search surfaced this
    person, and an interest citing a search that is unknown, that belongs to
    somebody else or that never showed them is **refused, never linked as null**.
    A silently dropped link is a denominator that lies, and *interests per search*
    is how this engine is judged.

    **The position is not sent.** The backend reads it off the cited search's own
    returned rows, so the origin key is true by construction rather than by a
    client being honest about where it was scrolled to.
    """

    sport: Sport = Field(..., description="Which sport this yes is for")
    player_id: UUID = Field(..., description="Who you would like to play")
    search_id: UUID = Field(
        ...,
        description=(
            "The search this person was shown to you in. **Required** — a yes "
            "with no origin is refused rather than recorded with a null link."
        ),
    )


class OutgoingInterestSchema(BaseModel):
    """One yes you sent, and when it lapses.

    ``expires_at`` is on the row from the moment it was created, and the client
    **renders** it rather than computing it: the TTL behind it is ruleset
    configuration and never crosses as a number.
    """

    player_id: UUID = Field(..., description="Who you said *Let's play* to")
    sport: Sport
    at: datetime = Field(..., description="When you said it")
    expires_at: datetime = Field(
        ...,
        description=(
            "When this yes lapses. **Dated when it was created** and never "
            "extended by tapping again — a second tap changes nothing. On "
            "expiry the row is simply gone: there is no *expired* state and no "
            "archive."
        ),
    )


class OutstandingSchema(BaseModel):
    """How many yeses you have in flight for one sport, and the cap in force.

    **Outstanding means sent, unexpired and not yet mutual** — a mutual has been
    answered and is no longer in flight. The pair travels together on every read,
    because a cap you cannot see is a refusal you cannot predict.
    """

    sport: Sport
    outstanding: int = Field(..., ge=0)
    cap: int = Field(
        ...,
        ge=1,
        description=(
            "The most you may have in flight for this sport at once. **Read it "
            "from here, never hardcode it** — it is ruleset configuration and "
            "may move between releases."
        ),
    )
    ttl_days: int = Field(
        ...,
        ge=1,
        description=(
            "How many days a yes you send in this sport stays live before it "
            "lapses. **Read it from here, never hardcode it** — it is the same "
            "ruleset number that dates every `expires_at`, sent so a screen can "
            "say *your yeses stay live for N days* without holding N. Every "
            "yes still carries its own `expires_at`; render that for a row, and "
            "this for the sentence."
        ),
    )


class ExpressedInterestResponse(BaseModel):
    """What one tap answers with.

    ``mutual`` is the one thing this tells you about the other person, and you
    have earned it by them having said yes to you first. Nobody is notified of a
    one-sided yes, in either direction.
    """

    interest: OutgoingInterestSchema
    mutual: bool = Field(
        ...,
        description=(
            "`true` when they had already said *Let's play* to you for this "
            "sport. **A mutual is told to both sides.** A one-sided yes is told "
            "to nobody, ever."
        ),
    )
    challenge_id: UUID | None = Field(
        ...,
        description=(
            "**The game the two of you have**, when there is one — the "
            "challenge this tap opened, or the one an earlier mutual between "
            "you opened that is not finished with.\n\n"
            "**`null` is one answer covering two causes, and it does not say "
            "which.** You may already have a game *being arranged* together, or "
            "the platform may have declined to open one. That distinction does "
            "not cross this wire and will not — so a client that reported the "
            "absence as a state of its own would be reporting the second, which "
            "is a fact about the other person no refusal here is allowed to "
            "disclose.\n\n"
            "`mutual` is unaffected either way: it is what the two yeses say."
        ),
    )
    outstanding: OutstandingSchema = Field(
        ...,
        description=(
            "Where this sport now stands against its cap, after this tap."
        ),
    )


class InterestListResponse(BaseModel):
    """Your own *Let's play* screen. **Outgoing and mutuals only.**

    There is no incoming list and there will not be one: a yes nobody has
    answered stays silent, which is what makes saying yes low-stakes. The two
    lists are disjoint — a yes that came back is in `mutual` and not in
    `outgoing` — so a client renders both without deriving either.
    """

    outgoing: list[OutgoingInterestSchema] = Field(
        ...,
        description=(
            "Yeses you sent that are still in flight, newest first. Every one "
            "carries its own `expires_at`."
        ),
    )
    mutual: list[OutgoingInterestSchema] = Field(
        ...,
        description=(
            "Yeses you sent that came back. **Both of you said it**, which is "
            "the only way somebody else's yes reaches you at all."
        ),
    )
    outstanding: list[OutstandingSchema] = Field(
        ...,
        description=(
            "One entry per sport, always — the count and the cap in force. Sent "
            "before you are near the limit, on purpose."
        ),
    )
