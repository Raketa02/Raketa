"""What crosses the wire. **One request shape, and one that carries no answer.**

There is no schema here for an *answered* card, because there is no route that
returns one. That absence is the context's central rule expressed as the thing a
client generates its types from: *no individual rating is returned to anybody, on
any route, in any shape*, and the shape does not exist to be returned.

What does come back is the list of cards still **waiting** — a game id and the
people on that court, which is a fact about an evening and not about anybody's
opinion of it. There is nowhere on it for a star to arrive later: an open card is
by definition one nobody has answered.

**A blank has one spelling and it is absence.** Somebody left blank is not in
``ratings``; there is no ``stars: null``, because two spellings of *nothing to
say* is two things for a client to get right and one for a reader to
misinterpret. An empty ``ratings`` is therefore the whole-card blank, and it is a
legal request rather than a no-op.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class StarsGivenSchema(BaseModel):
    """One player on the card, and the stars they were given.

    ``stars`` is declared as a plain integer **on purpose**. The range is one to
    five whole stars and it lives in the domain, where a seed, a test and a
    request all meet the same refusal; a Pydantic bound restating it here would
    be a second copy of the rule, and the first of the two to be edited would win
    silently for whichever callers went through it. A number off the scale comes
    back as `stars_are_one_to_five`.
    """

    player_id: UUID = Field(
        ...,
        description="One of the other players on that court — in doubles an "
        "opponent or your partner, in singles the one opponent.",
    )
    stars: int = Field(
        ...,
        description="One to five whole stars. There is no zero and there are no "
        "halves.",
    )


class AnswerTheCardRequest(BaseModel):
    """A whole card, answered once.

    Everybody from one game is answered together, which is what keeps a busy
    month from becoming a chore list.
    """

    ratings: list[StarsGivenSchema] = Field(
        default_factory=list,
        description="The players you are rating. **Leave somebody out to leave "
        "them blank**, and send an empty list to answer the card without rating "
        "anybody — both are answers, and both close the card for ever.",
    )


class OpenCardSchema(BaseModel):
    """One court still waiting for this player's stars.

    **Ids and nothing else.** What the people are called, which sport it was and
    when it happened all come from the games list this card is drawn beside —
    joined on ``game_id``, which is the same join the client already makes to
    draw the game. Repeating them here would be a second copy of an evening's
    description, and the day the two disagreed the card would name somebody the
    game did not.
    """

    game_id: UUID = Field(
        ...,
        description="The game this card is about. Post the answer to "
        "`/api/v1/sportsmanship/{game_id}`, and join it against `/api/v1/games` "
        "for the handles, the sport and the date.",
    )
    players: list[UUID] = Field(
        ...,
        description="Everybody else who was on that court, in the line-up's own "
        "order — in doubles both opponents **and** your partner, in singles the "
        "one opponent. Any of them may be left blank when you answer.",
    )


class OpenCardsResponse(BaseModel):
    """Every card waiting for you, **soonest to expire first**.

    An empty list is the ordinary answer and means nothing is waiting. It does
    not distinguish *no games*, *not yet a day* and *already answered*: all three
    are simply not on the list, and none of them is something a client would draw
    differently.

    ``cards`` is **required and never absent**, empty though it usually is: a
    default would emit it as optional and hand every client a list it has to
    check for existence before checking for length.
    """

    cards: list[OpenCardSchema] = Field(
        ...,
        description="The courts still waiting for your stars. A card appears the "
        "day after the game and stays for seven days; ignoring one costs "
        "nothing.",
    )
