"""One line of framework repair, so a streamed frame is declared and checked.

**A streaming route loses its item type the moment its router is included, and
this puts it back.**

FastAPI detects what a generator endpoint yields exactly once, in
``APIRoute.__init__``, and only *while* ``response_model`` is still the
placeholder that means *nobody said*. For a stream it then sets
``response_model = None``, because the item type and a response model are two
different things. ``APIRouter.include_router`` re-creates every route it
inherits, and it passes ``response_model=route.response_model`` — which is now a
real ``None`` rather than the placeholder. The copy therefore never looks at the
annotation, and ``stream_item_type`` is silently absent on every route that has
been included even once. This application includes three deep: a module's router
into the player surface, the surface into the API router, that into the app.

**Two things are lost with it, and both matter here** (``docs/adr/0147`` §7).

- **The declaration.** ``openapi.player.json`` documents the stream as an SSE
  frame carrying an opaque ``data: string``, instead of one whose ``data`` is the
  declared envelope — so ``check-contract-drift.sh`` has nothing to diff and the
  client generates no type for it. ADR-0006 gets no exception for a live event,
  and this is the line that makes that true rather than aspirational.
- **The check on the way out.** With the field set, the framework validates and
  serialises every yielded item **through the declared model** before it reaches
  the wire. That does not close the hole ADR-0147 names — nothing proves the
  route keeps yielding that type, because a stream body is not a response model —
  but it is the difference between *the emission is checked at runtime* and *the
  emission is whatever the route happened to build*.

**Two alternatives, both refused, and it is worth saying which.** Declaring the
envelope as ``responses={200: {"model": LiveNudgeSchema}}`` does register the
schema without touching the framework — but it lands *beside* the opaque
``itemSchema`` rather than inside it, leaving the document saying two things
about one response, and it buys no check on the way out. Writing the
``contentSchema`` by hand into ``openapi_extra`` is worse: a hand-maintained
mirror of a backend response is the thing ADR-0006 exists to forbid, and it would
rot the first time the envelope gained a field.

**A route that names its own frames still declares its payload, and that is
the second half of this file** (``docs/adr/0156`` §5). A stream carrying two
kinds has to name them, and the SSE ``event:`` field is where a name goes — which
means yielding ``ServerSentEvent`` rather than a bare model, and the framework
treats **any** ``ServerSentEvent`` as *this route is building its own frames* and
declares nothing about them. So a subclass that narrows ``data`` is read for its
``data`` annotation instead, and the document carries that as the frame's
``contentSchema`` exactly as it carries a plain item's. Without this, adding the
second event would have quietly deleted the **first** one's schema from
``components`` — a contract change nobody asked for, arriving as a deletion.

**What is not restored on that path is the check on the way out.** The framework
skips ``stream_item_field`` for a ``ServerSentEvent``, so the field set here is
the declaration only; the validation moves to where the frame is **constructed**,
since a narrowed ``data`` is a pydantic field like any other. Same guarantee,
one step earlier, and neither of them proves which event names are emitted.

**Applied to the finished application, once**, rather than by pushing a custom
route class down three routers: the routes an app serves and the routes its
document is generated from are the same objects, so one pass over
``app.routes`` fixes both. ``app/api/contract.py`` builds its own throwaway app
per surface and calls this for the same reason.

**It is a shim and it is dated.** ``tests/api/test_conversation_stream.py``
asserts the emitted contract carries the envelope, so the day the framework does
this itself the tests stay green and this file can be deleted; the day the
framework changes shape underneath it, they go red rather than the document
quietly losing a schema.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi._compat import lenient_issubclass
from fastapi.dependencies.utils import (
    get_stream_item_type,
    get_typed_return_annotation,
)
from fastapi.routing import APIRoute, request_response
from fastapi.sse import ServerSentEvent
from fastapi.utils import create_model_field


def restore_stream_item_types(app: FastAPI) -> tuple[str, ...]:
    """Re-derive each streaming route's item type. **The paths it repaired.**

    Returned rather than logged so a test can assert the shim still finds
    something: a repair that quietly stops matching is worse than none, because
    the contract would lose a schema and nothing would say so.
    """

    repaired: list[str] = []
    for route in app.routes:
        if not isinstance(route, APIRoute) or not route.is_sse_stream:
            continue
        if route.stream_item_field is not None:
            # Either the framework found it — a route that has never been
            # included — or this has already run.
            continue
        item = _declared_payload(
            get_stream_item_type(get_typed_return_annotation(route.endpoint))
        )
        if item is None:
            continue
        route.stream_item_type = item
        route.stream_item_field = create_model_field(
            name="StreamItem_" + route.unique_id,
            type_=item,
            mode="serialization",
        )
        # The handler closed over the field at construction, so it is rebuilt
        # here. Without this the document would be right and the wire would not,
        # which is the worse half of the two to leave broken.
        route.app = request_response(route.get_route_handler())
        repaired.append(route.path)
    return tuple(repaired)


def _declared_payload(item: Any | None) -> Any | None:
    """What this stream's ``data`` is, or ``None`` if it declares nothing.

    Two shapes reach here and the second is why this function exists.

    A route yielding a **plain model** yields that model *as* the payload, so the
    item is the payload.

    A route yielding a **``ServerSentEvent``** is naming its own frames, which is
    the only way to set the SSE ``event:`` field. The base class carries
    ``data: Any`` and declares nothing — but a **subclass that narrows ``data``**
    is a declaration, and it is the one the client generates from. Reading it
    here rather than in the route is what keeps *the envelope is declared and
    generated* (ADR-0006) true of a stream that has more than one kind of frame
    on it.
    """

    if item is None:
        return None
    if not lenient_issubclass(item, ServerSentEvent):
        return item
    if item is ServerSentEvent:
        # The base class. `data: Any` is not a declaration, and documenting it
        # as one would put `{}` in the contract where a schema belongs.
        return None
    payload = item.model_fields["data"].annotation
    return None if payload is Any else payload
