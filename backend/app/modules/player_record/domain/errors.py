"""The one refusal this context has, and the whole of what it says.

**Three refusals, one answer, byte for byte.** *Never disclosed to you*,
*held*, and *no such player* return the same status and the same body — not three
codes a client branches on, not three messages, and no ``details``. The
indistinguishability **is** the feature: a payload naming the gate would say
which (``docs/adr/0130``), and a payload separating *never disclosed* from *no
such player* answers *is this id real* about a stranger. **A block is not one of
them** since ``docs/adr/0193`` §2: it refuses no record, either way round.

**It is a 404 rather than a 403**, and that follows from the same rule rather
than from taste. A 403 says *there is somebody here you may not see*; a 404 says
nothing at all, which is exactly the amount this refusal is allowed to say. The
client draws one line — *This record isn't available.* — and there is nothing on
the wire it could draw a second one from.

There is deliberately no second error class in this context. A route that wanted
to explain a refusal would have to add one, and adding one is the argument.
"""

from __future__ import annotations

from app.shared.domain.errors import NotFoundError


class RecordUnavailable(NotFoundError):
    """This record cannot be opened, and the reason is not disclosed.

    The message is **fixed at the raise sites** rather than passed in, which is
    what makes *byte-identical* a property of the code instead of a promise
    every caller has to keep. ``tests/api/test_player_record.py`` drives all
    three causes and compares the responses.
    """

    code = "record_unavailable"


#: The one sentence this refusal ever carries. A diagnostic, like every
#: ``message`` on this platform — the copy a player reads is the client's, chosen
#: from the code — and it names no gate, no person and no id.
RECORD_UNAVAILABLE = "this record is not available"


__all__ = [
    "RECORD_UNAVAILABLE",
    "RecordUnavailable",
]
