"""The error taxonomy — pure, so a domain layer can refuse without learning HTTP.

Every failure this application renders as JSON is one of these. A class carries the
two things that describe the failure itself: the stable ``code`` a client branches on
(``docs/adr/0006``), and the status the envelope will be sent with. The envelope, the
handlers and the OpenAPI schema live on the other side of the boundary, in
``app/core/exception_handlers.py``.

**Why this is not in ``app/core/`` with them.** It was, and it made every module's
``domain/errors.py`` import ``fastapi``, ``starlette`` and ``pydantic`` transitively —
the one thing ``backend/CLAUDE.md`` forbids a domain layer by name (#101). The file
had grown two jobs: a taxonomy that needs only integers, and a transport that needs a
web framework. Splitting them costs nothing on the wire — the codes and statuses here
are the ones that were there — and the fence in ``.importlinter`` now holds the
separation open.

**Why ``status_code`` stays on the class**, rather than being mapped at the
presentation boundary as the purer reading of ``docs/adr/0001`` would have it: the
alternative separates a class from its status, so the two are maintained in two files
and a subclass added without a registry entry becomes a 500 found in production
instead of a red test. Keeping them together is what lets
``tests/unit/test_error_envelope.py`` walk every subclass and assert both properties
in one pass. The cost is one integer attribute on a domain class. It is a number, not
a dependency — nothing here imports a framework to obtain it, and no behaviour in this
module varies by transport.

``http.HTTPStatus`` is stdlib and spells out the same integers ``fastapi.status``
does.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import Any, Dict, Optional


class AppError(Exception):
    """Base for every domain / application error rendered as JSON over HTTP.

    Subclasses override ``status_code`` and ``code``; the web framework never sees
    these classes — the handler registered in ``app/core/exception_handlers.py`` maps
    them to the error envelope.

    **A subclass that does not set its own ``code`` inherits an ambiguous one**,
    which is how two errors demanding opposite client recoveries end up
    indistinguishable on the wire. ``tests/unit/test_error_envelope.py`` fails
    the build when that happens.
    """

    status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR
    code: str = "internal_error"

    def __init__(
        self, message: str, *, details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class BadRequestError(AppError):
    status_code = HTTPStatus.BAD_REQUEST
    code = "bad_request"


class UnauthorizedError(AppError):
    status_code = HTTPStatus.UNAUTHORIZED
    code = "unauthorized"


class ForbiddenError(AppError):
    status_code = HTTPStatus.FORBIDDEN
    code = "forbidden"


class NotFoundError(AppError):
    status_code = HTTPStatus.NOT_FOUND
    code = "not_found"


class ConflictError(AppError):
    status_code = HTTPStatus.CONFLICT
    code = "conflict"
