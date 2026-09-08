"""What this context refuses. **Two codes, and one of them covers three cases.**

**``conversation_not_found`` is one code for *it does not exist*, *it is not
yours* and — once the sweep lands — *it is over*.** That is
``challenge_not_found``'s argument verbatim (``docs/adr/0148`` §9): separating
them would answer *is this id real* about a stranger's evening, and a 403 on a
room you are not in tells you there is a room.

**The hold refuses with ``account_held``**, declared in
``app/shared/domain/errors.py`` rather than a third time here. It is one fact
with one remedy and must cross as one code; the class is shared for the same
reason the *port* is not.

**No refusal here names anybody**, and none carries a payload.
"""

from __future__ import annotations

from app.shared.domain.errors import BadRequestError, NotFoundError


class ConversationNotFound(NotFoundError):
    """No room of that id that you are in.

    **One code for three cases**, and the client's recovery is the same for all
    three: leave the screen. A member who is told *not yours* and a stranger who
    is told *no such thing* would between them turn this route into a way of
    asking whether two people are arranging a game.
    """

    code = "conversation_not_found"

    def __init__(self) -> None:
        super().__init__("No such conversation.")


class AMessageMustSaySomething(BadRequestError):
    """A send with nothing in it, or nothing but whitespace.

    A refusal rather than a dropped send: an empty bubble is indistinguishable
    from a bug at the composer, and recording one would put a blank line in front
    of three other people.
    """

    code = "message_is_empty"

    def __init__(self) -> None:
        super().__init__("A message must say something.")


class TheMessageIsTooLong(BadRequestError):
    """Past ``MESSAGE_LENGTH_CAP``. **Refused, never truncated.**

    A silently shortened message is one the sender believes they sent whole, in
    front of people who read a different sentence.
    """

    code = "message_is_too_long"

    def __init__(self) -> None:
        super().__init__("That message is too long.")
