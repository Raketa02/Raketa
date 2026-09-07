"""What this context refuses, and the one failure it will not paper over."""

from __future__ import annotations

from http import HTTPStatus

from app.shared.domain.errors import AppError, BadRequestError


class CannotBlockYourself(BadRequestError):
    """A player named themselves as the other party.

    A domain error rather than a no-op, deliberately (``docs/adr/0095`` §3).
    Silently accepting it would open a stream whose two sides are one person and
    whose effect — *this player disappears from their own view everywhere* — is
    nothing the caller can have meant. A refusal is also the only answer that
    tells a client its own bug.
    """

    code = "cannot_block_yourself"

    def __init__(self) -> None:
        super().__init__("A player cannot block themselves.")


class BlockStateUnavailable(AppError):
    """The live block state could not be read, so nothing may be shown.

    **This is the fail-closed rule as a class** (``docs/adr/0095`` §5). A term
    that cannot be evaluated stands down; a *gate* that cannot be evaluated
    excludes — and at the search level that means the search refuses rather than
    returning rows nobody verified.

    It exists so that the alternative is unavailable: a query that returned an
    empty exclusion set when the database was unreachable would report *nobody is
    blocked*, which is a safety control switching itself off under exactly the
    conditions nobody is watching. Raising is what makes that impossible to do by
    accident.

    A 503 and not a 500 because the failure is transient and about the platform,
    never about the caller: the code tells a client to retry the same request
    rather than to change it.

    **Its own code, and deliberately not the matcher's.** A search that cannot
    evaluate a gate refuses with ``gate_data_unavailable``
    (``matchmaking/domain/errors.py``) — that is the code on the wire contract,
    and the one a client branches on. This one is raised one layer in, by the
    context that owns the fact, and it names *which* gate could not be
    evaluated: a consumer catches it and re-raises its own refusal, which is why
    the Blocks context does not import the matcher's error class. Every surface
    that shows one player to another consults this port, and the matcher is only
    the first of them.
    """

    status_code = HTTPStatus.SERVICE_UNAVAILABLE
    code = "block_state_unavailable"

    def __init__(
        self, message: str = "Block state could not be read; nothing was shown."
    ) -> None:
        super().__init__(message)
