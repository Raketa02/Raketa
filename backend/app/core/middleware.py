from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import Settings
from app.core.tracing import TRACE_ID_HEADER, assign_trace_id


class RequestTraceMiddleware(BaseHTTPMiddleware):
    """Give every request an id, on its state and on the response header.

    Sits outside the exception handlers, so an error envelope built further in
    reports the same id the caller sees on the header.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        trace_id = assign_trace_id(request)
        response = await call_next(request)
        response.headers[TRACE_ID_HEADER] = trace_id
        return response


def register_middleware(app: FastAPI, settings: Settings) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOW_ORIGINS,
        allow_credentials=settings.ALLOW_CREDENTIALS,
        allow_methods=settings.ALLOW_METHODS,
        allow_headers=settings.ALLOW_HEADERS,
        # Without this a browser client cannot read the header at all, which
        # would leave the trace id useful to the mobile app and dead weight to
        # the club console.
        expose_headers=[TRACE_ID_HEADER],
    )
    app.add_middleware(RequestTraceMiddleware)
