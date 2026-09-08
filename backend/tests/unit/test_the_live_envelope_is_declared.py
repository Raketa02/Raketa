"""The live envelope is declared on the route and generated. ADR-0006, no exception.

A live event is a backend response, so the client never hand-writes a DTO
mirroring it (`docs/adr/0147` §7). These read the **emitted document** rather than
the source, because what a client generates from is the document.

**Separate from `test_live_channel.py` on purpose.** That file is adapter and
use-case logic — what `backend/CLAUDE.md` scopes `tests/unit/` to — and these are
assertions about a generated artifact. They live beside
`test_dev_console_surface.py`, which reads the same documents for the same reason.
"""

from __future__ import annotations

from app.api.contract import SURFACES, build_surface_spec

STREAM = "/api/v1/conversations/{conversation_id}/stream"


def _the_stream_operation() -> tuple[dict, dict]:
    spec = build_surface_spec("Raketa Player API", SURFACES["player"])
    return spec, spec["paths"][STREAM]["get"]


def test_the_live_envelope_is_declared_on_the_route_and_generated():
    """The assertion the framework shim in `app/api/streaming.py` exists for.

    Without it a stream documents an opaque `data: string`, the client generates
    no type for the envelope, and neither the drift nor the freshness check has
    anything to diff. This goes red if the repair stops matching, rather than the
    contract quietly losing a schema.

    **What it does not cover is the emission.** Nothing here proves the bytes on
    the stream match this declaration — a stream body is not a response model —
    and that residual hole is `docs/adr/0147` §7's, named rather than closed.
    """

    spec, stream = _the_stream_operation()

    frame = stream["responses"]["200"]["content"]["text/event-stream"]["itemSchema"]
    assert frame["properties"]["data"]["contentSchema"] == {
        "$ref": "#/components/schemas/LiveNudgeSchema"
    }
    assert set(spec["components"]["schemas"]["LiveNudgeSchema"]["properties"]) == {
        "v",
        "conversation_id",
        "last_seq",
    }


def test_the_frame_is_three_fields_and_the_document_says_so():
    """**The whole live contract**, read back off the artifact a client reads.

    A fourth field here would be a widening of the one shape no check watches
    behaviourally, which is exactly what `docs/adr/0147` §3 chose this envelope to
    make unaffordable.
    """

    spec, _ = _the_stream_operation()

    envelope = spec["components"]["schemas"]["LiveNudgeSchema"]
    assert envelope["required"] == ["v", "conversation_id", "last_seq"]


def test_the_refusal_on_the_stream_is_json_and_not_an_event_stream():
    """A non-member is refused before the stream begins, so it is an ordinary error."""

    _, stream = _the_stream_operation()

    assert set(stream["responses"]["404"]["content"]) == {"application/json"}
