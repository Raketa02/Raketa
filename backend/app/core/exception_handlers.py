"""The error envelope — one JSON shape for every failure, keyed by a stable code.

    {"code": "question_not_outstanding", "message": "...", "trace_id": "..."}

Two properties make this contract usable from a client, and both are load-bearing:

**Clients branch on ``code``, never on ``message``** (``docs/adr/0006``, and the
player app's own error model). The message is a diagnostic that improves as the
copy does and disappears the moment the app is localized; the code is the stable
half. So every error carries its **own** code rather than its base class's:
``QuestionNotOutstanding`` and ``AssessmentAlreadyFinished`` are both 409s, but
one means *refetch the current step* and the other *jump to the result*, and a
client that cannot tell them apart cannot do either.

**Every failure is the same shape.** A validation failure and an unhandled 404
are as much a part of the contract as a domain error, so the handlers below
normalize FastAPI's and Starlette's own bodies into this envelope too — a client
that has to special-case ``detail`` for two statuses has no error model at all.

``ErrorResponse`` is the schema both OpenAPI documents publish *and* the model the
handlers build their bodies from, so the type a client generates and the body it
receives cannot drift apart.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Mapping, Optional

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.application.events.store import EventStreamVersionConflict
from app.core.tracing import trace_id_for

logger = logging.getLogger(__name__)


class ErrorResponse(BaseModel):
    """The body of every error response, on both API surfaces."""

    code: str = Field(
        description=(
            "Stable, machine-readable identifier for this exact failure. The only "
            "half of the envelope a client may branch on."
        ),
        examples=["question_not_outstanding"],
    )
    message: str = Field(
        description=(
            "Human-readable diagnostic. Never the copy shown to a user — that is "
            "the client's, chosen from the code."
        ),
    )
    trace_id: str = Field(
        description=(
            "This request's identifier, also returned on the X-Request-ID header. "
            "Ties a client-side failure to a server log without logging a payload."
        ),
    )
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Structured context for this code, when the code defines any.",
    )


class AppError(Exception):
    """Base for every domain / application error rendered as JSON over HTTP.

    Subclasses override ``status_code`` and ``code``; FastAPI never sees these
    classes — the registered handler maps them to the envelope above.

    **A subclass that does not set its own ``code`` inherits an ambiguous one**,
    which is how two errors demanding opposite client recoveries end up
    indistinguishable on the wire. ``tests/unit/test_error_envelope.py`` fails
    the build when that happens.
    """

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    code: str = "internal_error"

    def __init__(
        self, message: str, *, details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class BadRequestError(AppError):
    status_code = status.HTTP_400_BAD_REQUEST
    code = "bad_request"


class UnauthorizedError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "unauthorized"


class ForbiddenError(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    code = "forbidden"


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "not_found"


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "conflict"


#: The codes carried by responses no domain error authored: request validation,
#: and whatever Starlette raises on its own behalf (an unrouted path, a wrong
#: method). Statuses are unchanged — only the body is now the envelope.
VALIDATION_ERROR_CODE = "validation_error"

#: Two writes reached the same aggregate stream and the store rejected the
#: second. Not a domain error — no context authored it, and every event-sourced
#: context can raise it — so it is mapped here rather than being re-declared as
#: an ``AppError`` per module, which would also make an application-layer store
#: error know about HTTP.
#:
#: **Until this existed it was a 500**, because nothing mapped it: a genuine
#: concurrent double-submit told the client the server had broken, when what had
#: actually happened was that its own retry lost a race it can safely re-read.
#: The recovery is to refetch the current step, which is the same recovery
#: ``question_not_outstanding`` asks for and the reason both are 409s.
CONCURRENT_MODIFICATION_CODE = "concurrent_modification"

_STATUS_CODES: dict[int, str] = {
    status.HTTP_400_BAD_REQUEST: BadRequestError.code,
    status.HTTP_401_UNAUTHORIZED: UnauthorizedError.code,
    status.HTTP_403_FORBIDDEN: ForbiddenError.code,
    status.HTTP_404_NOT_FOUND: NotFoundError.code,
    status.HTTP_405_METHOD_NOT_ALLOWED: "method_not_allowed",
    status.HTTP_409_CONFLICT: ConflictError.code,
    status.HTTP_422_UNPROCESSABLE_ENTITY: VALIDATION_ERROR_CODE,
    status.HTTP_429_TOO_MANY_REQUESTS: "rate_limited",
}


def code_for_status(status_code: int) -> str:
    """The code a response carries when no domain error named one."""

    if status_code in _STATUS_CODES:
        return _STATUS_CODES[status_code]
    return "internal_error" if status_code >= 500 else "request_failed"


def _validation_message(exc: RequestValidationError) -> str:
    """A diagnostic naming the first offending field — and nothing it contained.

    Pydantic's error dicts carry the rejected ``input`` alongside the location,
    and a rejected signup body contains a password. Only the location and
    Pydantic's own explanation are read out.
    """

    errors = exc.errors()
    if not errors:
        return "Request validation failed."
    first = errors[0]
    location = ".".join(str(part) for part in first.get("loc", ())) or "body"
    return f"Request validation failed: {location}: {first.get('msg', 'invalid')}"


def _error_response(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    headers: Optional[Mapping[str, str]] = None,
) -> JSONResponse:
    body = ErrorResponse(
        code=code,
        message=message,
        trace_id=trace_id_for(request),
        details=details or None,
    )
    merged = dict(headers or {})
    if status_code == status.HTTP_401_UNAUTHORIZED:
        merged.setdefault("WWW-Authenticate", "Bearer")

    # The log line is what makes the trace id worth returning. Codes and our own
    # diagnostics only: no token, no header, no request body ever reaches it.
    logger.log(
        logging.ERROR if status_code >= 500 else logging.INFO,
        "request failed",
        extra={
            "extra_fields": {
                "trace_id": body.trace_id,
                "code": code,
                "status": status_code,
                "path": request.url.path,
                "detail": message,
            }
        },
    )
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(exclude_none=True),
        headers=merged or None,
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return _error_response(
            request,
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            details=exc.details,
        )

    @app.exception_handler(EventStreamVersionConflict)
    async def _stream_conflict_handler(
        request: Request, exc: EventStreamVersionConflict
    ) -> JSONResponse:
        # The exception's own text names the aggregate type, the stream id and
        # the two versions. That is a diagnostic about our storage, not about
        # the caller's request, so it is logged here and the envelope carries a
        # generic message — the trace id is what ties the two together.
        logger.warning(
            "event stream version conflict",
            extra={"extra_fields": {"detail": str(exc), "path": request.url.path}},
        )
        return _error_response(
            request,
            status_code=status.HTTP_409_CONFLICT,
            code=CONCURRENT_MODIFICATION_CODE,
            message="This resource was modified concurrently; re-read and retry.",
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return _error_response(
            request,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code=VALIDATION_ERROR_CODE,
            message=_validation_message(exc),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return _error_response(
            request,
            status_code=exc.status_code,
            code=code_for_status(exc.status_code),
            message=str(exc.detail),
            headers=exc.headers,
        )
