"""The matchmaking context's one refusal left: a gate that could not be read.

Fourteen codes went with the searches, the deck and the radar (#579) — every
refusal a shortlist, a line-up, a deal, a reading, a *Let's play*, a pass or a
prompt's *not now* could answer with. What is left is the code the player
record's account gates raise when one of them cannot be evaluated.
"""

from __future__ import annotations

from http import HTTPStatus

from app.shared.domain.errors import AppError


class GateDataUnavailable(AppError):
    """A gate could not be evaluated, so the read refuses rather than guesses.

    **A gate that cannot be evaluated excludes** (``docs/adr/0095``). Blocks,
    holds and account state are safety controls, and *nobody is held* and *we
    could not find out* are different sentences: showing somebody on the second
    while printing the first is the one failure mode a gate may not have.

    It is its **own code** rather than the generic transient one, because a
    client must be able to tell an outage that will pass from a refusal about
    *you* — ``account_held`` is a 403 about the reader, and this is a 503 about
    the platform.
    """

    status_code = HTTPStatus.SERVICE_UNAVAILABLE
    code = "gate_data_unavailable"
