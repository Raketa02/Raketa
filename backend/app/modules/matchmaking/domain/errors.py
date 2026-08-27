"""The matchmaking context's refusals.

One today, and it is the one a fail-closed read owes the client. The rest of the
context's error vocabulary — a searcher with no rating for the sport, an
undeclared Play intent, a held searcher, a search that could not be recorded —
arrives with the routes that can raise them, because an error nothing can produce
is a code a client would be branching on for nothing.
"""

from __future__ import annotations

from http import HTTPStatus

from app.shared.domain.errors import AppError


class GateDataUnavailable(AppError):
    """A gate could not be evaluated, so the search refuses rather than guesses.

    **A gate that cannot be evaluated excludes** (``docs/adr/0095``). Blocks,
    holds and account state are safety controls, and *nobody is held* and *we
    could not find out* are different sentences: serving a shortlist on the
    second while printing the first is the one failure mode a matcher may not
    have.

    It is its **own code** rather than the generic transient one, because a
    client must be able to tell an outage that will pass from a refusal about
    *you* — ``account_held`` is a 403 about the searcher, and this is a 503 about
    the platform.
    """

    status_code = HTTPStatus.SERVICE_UNAVAILABLE
    code = "gate_data_unavailable"
