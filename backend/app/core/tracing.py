"""The per-request trace id — the thread between a client failure and a log line.

An error body that says only *what* went wrong cannot be taken to support: the
conversation needs a handle on the **one request** that failed. Every request
therefore carries an id, which is returned on the response header, embedded in
every error envelope, and attached to the log line the failure writes. Nothing
else is needed to tie a phone's crash report to a server log — and, deliberately,
no payload has to be logged to get there.

An inbound id is honoured so a client (or an edge proxy) can correlate from its
own side, but only after it is checked against a conservative pattern: the value
reaches a log file, and a header is attacker-controlled input.
"""

from __future__ import annotations

import re
from uuid import uuid4

from starlette.requests import Request

#: Returned on every response and accepted on the way in.
TRACE_ID_HEADER = "X-Request-ID"

#: Where the id lives for the duration of the request.
TRACE_ID_STATE_ATTR = "trace_id"

# Deliberately narrow: an id is an opaque handle, so anything that could break a
# log line or a header is simply replaced with one we generate.
_SAFE_TRACE_ID = re.compile(r"\A[A-Za-z0-9._-]{1,64}\Z")


def new_trace_id() -> str:
    return uuid4().hex


def assign_trace_id(request: Request) -> str:
    """Attach this request's id to its state, honouring a safe inbound one."""

    supplied = request.headers.get(TRACE_ID_HEADER)
    usable = bool(supplied and _SAFE_TRACE_ID.match(supplied))
    trace_id = supplied if usable and supplied else new_trace_id()
    setattr(request.state, TRACE_ID_STATE_ATTR, trace_id)
    return trace_id


def trace_id_for(request: Request) -> str:
    """This request's id, minting one if the middleware never ran.

    An error response without a trace id would be an error nobody can look up,
    so the fallback generates rather than omits.
    """

    existing = getattr(request.state, TRACE_ID_STATE_ATTR, None)
    return existing if isinstance(existing, str) else new_trace_id()
