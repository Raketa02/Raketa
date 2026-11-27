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
    spec = build_surface_spec("Rakieta Player API", SURFACES["player"])
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
    assert frame["properties"]["data"]["contentSchema"]["anyOf"] == [
        {"$ref": "#/components/schemas/LiveNudgeSchema"},
        {"$ref": "#/components/schemas/LiveTypingSchema"},
    ]
    assert set(spec["components"]["schemas"]["LiveNudgeSchema"]["properties"]) == {
        "v",
        "conversation_id",
        "last_seq",
    }
    assert set(spec["components"]["schemas"]["LiveTypingSchema"]["properties"]) == {
        "v",
        "conversation_id",
        "player_ids",
    }


def test_both_envelopes_survive_the_route_naming_its_own_events():
    """The half of the shim `docs/adr/0156` §5 needed, asserted for its own sake.

    Naming an event means yielding a `ServerSentEvent`, and the framework reads
    any of those as *this route builds its own frames* and declares nothing about
    them. Without `_declared_payload`, adding the typing event would have deleted
    **`LiveNudgeSchema`** from `components.schemas` — a contract change nobody
    asked for, arriving at a shipped client as a deletion.
    """

    spec, _ = _the_stream_operation()

    assert "LiveNudgeSchema" in spec["components"]["schemas"]
    assert "LiveTypingSchema" in spec["components"]["schemas"]


def test_each_frame_is_three_fields_and_the_document_says_so():
    """**Two frames, three fields each**, read back off the artifact a client reads.

    A fourth field on either would be a widening of the one shape no check
    watches behaviourally, which is exactly what `docs/adr/0147` §3 chose this
    envelope to make unaffordable — and `docs/adr/0156` kept, by giving the
    second frame its own shape rather than a field on this one.

    **The typing frame's missing fourth field is `last_seq`, and its absence is
    the ticket's own invariant** (`docs/adr/0156` §4): a typing frame is not an
    entry and may not carry, or move, a sequence.
    """

    spec, _ = _the_stream_operation()

    schemas = spec["components"]["schemas"]
    assert schemas["LiveNudgeSchema"]["required"] == [
        "v",
        "conversation_id",
        "last_seq",
    ]
    assert schemas["LiveTypingSchema"]["required"] == [
        "v",
        "conversation_id",
        "player_ids",
    ]


def test_the_typing_route_answers_no_content_and_takes_no_body():
    """A heartbeat records nothing and says nothing back (`docs/adr/0156`).

    **And it takes no body at all** — what is being typed is nobody's business
    until it is sent, and a request shape here is the field that would one day
    carry it.
    """

    spec, _ = _the_stream_operation()

    typing = spec["paths"][STREAM.replace("/stream", "/typing")]["post"]
    assert set(typing["responses"]) == {"204", "403", "404", "422"}
    assert "requestBody" not in typing


def test_the_refusal_on_the_stream_is_json_and_not_an_event_stream():
    """A non-member is refused before the stream begins, so it is an ordinary error."""

    _, stream = _the_stream_operation()

    assert set(stream["responses"]["404"]["content"]) == {"application/json"}
