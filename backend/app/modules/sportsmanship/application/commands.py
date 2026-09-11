"""What a caller asks this context to do. **One command, and it is the only one.**

There is no command to amend a card, none to withdraw one and none to read one
back, because none of those acts exists: submitting closes the card, a blank
stays blank for ever, and no individual rating reaches anybody.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.modules.sportsmanship.domain.card import StarsGiven


@final
@dataclass(frozen=True, slots=True)
class AnswerTheCardCommand:
    """*Here is what I thought of the people I played.*

    ``given`` carries **only the people who were given stars**. A blank is spelled
    by not being in it, which is the one spelling for *nothing to say* everywhere
    in this context, and an empty ``given`` is the whole-card blank — an answer,
    and the thing that closes the card.
    """

    game_id: UUID
    rater_id: UUID
    given: tuple[StarsGiven, ...]
