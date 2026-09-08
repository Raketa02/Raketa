"""What crosses the wire. **One request shape, and no response shape at all.**

There is no schema here for an answered card, because there is no route that
returns one. That absence is the context's central rule expressed as the thing a
client generates its types from: *no individual rating is returned to anybody, on
any route, in any shape*, and the shape does not exist to be returned.

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
