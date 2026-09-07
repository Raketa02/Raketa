"""The sidecar client, against a real server on a loopback socket.

**A stand-in for the sidecar, not a stand-in for HTTP.** The adapter's whole job
is what happens on the wire and what happens when the wire does not answer, so a
mocked `ClientSession` would test the mock. `aiohttp` ships a test server; the
requests below are real requests, and the timeout below really elapses.

What is *not* here is CLIP. The model is the sidecar's, and the thing it hands
back is a list of floats — so the numbers are written out, and the rule they are
fed into is asserted in `test_photo_review_policy.py` with no adapter at all.
"""

from __future__ import annotations

import asyncio
from base64 import b64decode

import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer

from app.modules.player_profile.domain.photos import (
    PHOTO_REVIEW_PROMPTS,
    PROMPT_SET_FINGERPRINT,
    PhotoReviewDecision,
    TranscodedImage,
)
from app.modules.player_profile.infrastructure.clip_photo_review import (
    SIMILARITIES_PATH,
    ClipSidecarPhotoReview,
    SidecarAnswerRejected,
    similarities_in,
)

MODEL = "openai/clip-vit-base-patch32"
IMAGE = TranscodedImage(
    data=b"\xff\xd8\xff pretend this is a jpeg",
    media_type="image/jpeg",
    width=800,
    height=600,
)

ON_COURT = [0.34] * 5 + [0.18] * (len(PHOTO_REVIEW_PROMPTS) - 5)
OFF_COURT = [0.18] * 5 + [0.34] * (len(PHOTO_REVIEW_PROMPTS) - 5)


class Sidecar:
    """One scripted answer, plus whatever request produced it."""

    def __init__(self, handler) -> None:
        self._handler = handler
        self.requests: list[dict] = []

    async def _route(self, request: web.Request) -> web.StreamResponse:
        self.requests.append(await request.json())
        return await self._handler(request)

    def application(self) -> web.Application:
        app = web.Application()
        app.router.add_post(SIMILARITIES_PATH, self._route)
        return app


def answering(payload: dict, *, status: int = 200):
    async def handler(request: web.Request) -> web.StreamResponse:
        return web.json_response(payload, status=status)

    return handler


async def reviewer_for(sidecar: Sidecar, *, timeout_seconds: float = 5.0):
    """A started server, and an adapter pointed at it."""

    server = TestServer(sidecar.application())
    await server.start_server()
    reviewer = ClipSidecarPhotoReview(
        endpoint_url=str(server.make_url("")).rstrip("/"),
        timeout_seconds=timeout_seconds,
    )
    return server, reviewer


# ---------------------------------------------------------------------------
# What goes over the wire
# ---------------------------------------------------------------------------


async def test_the_sidecar_is_asked_the_domain_s_prompts_and_given_the_image() -> None:
    """The rule stays in the backend: the service is told what to ask.

    That is what lets the threshold and the captions be re-tuned without
    touching the sidecar, and the model be swapped without a backend release.
    """

    sidecar = Sidecar(answering({"model": MODEL, "similarities": ON_COURT}))
    server, reviewer = await reviewer_for(sidecar)
    try:
        await reviewer.review(IMAGE)
    finally:
        await server.close()

    sent = sidecar.requests[0]
    assert sent["prompts"] == list(PHOTO_REVIEW_PROMPTS)
    assert b64decode(sent["image_base64"]) == IMAGE.data
    assert sent["media_type"] == IMAGE.media_type


async def test_a_court_photo_comes_back_allowed_with_its_evidence() -> None:
    sidecar = Sidecar(answering({"model": MODEL, "similarities": ON_COURT}))
    server, reviewer = await reviewer_for(sidecar)
    try:
        verdict = await reviewer.review(IMAGE)
    finally:
        await server.close()

    assert verdict.decision is PhotoReviewDecision.ALLOWED
    assert verdict.note is not None
    assert f"m={MODEL}" in verdict.note
    assert "0.3400" in verdict.note


async def test_a_photo_of_something_else_comes_back_flagged() -> None:
    sidecar = Sidecar(answering({"model": MODEL, "similarities": OFF_COURT}))
    server, reviewer = await reviewer_for(sidecar)
    try:
        verdict = await reviewer.review(IMAGE)
    finally:
        await server.close()

    assert verdict.is_flagged


# ---------------------------------------------------------------------------
# When the sidecar does not answer usably
# ---------------------------------------------------------------------------


async def test_an_unreachable_sidecar_fails_open() -> None:
    """The one that matters most: a container that is not up must cost a
    verdict, never a signup. A reviewer that turned its own outage into a failed
    upload would refuse a real photo for a reason that is not about the photo.

    **Failing open is now an absence rather than ``ALLOWED``** (``docs/adr/0138``):
    the photo is not flagged, and it is not claimed to have passed either — the
    same word would read *checked and passed* on a card a stranger sees.
    """

    # A port nothing is listening on — the ordinary state of a laptop stack that
    # has just started, since the API does not wait for the model to load.
    reviewer = ClipSidecarPhotoReview(
        endpoint_url="http://127.0.0.1:1", timeout_seconds=5.0
    )

    verdict = await reviewer.review(IMAGE)

    assert verdict.decision is None
    assert not verdict.is_flagged
    assert verdict.note == f"clip;p={PROMPT_SET_FINGERPRINT};unavailable=transport"


async def test_a_sidecar_that_is_too_slow_fails_open_as_a_timeout() -> None:
    async def slow(request: web.Request) -> web.StreamResponse:
        await asyncio.sleep(1.0)
        return web.json_response({"model": MODEL, "similarities": ON_COURT})

    sidecar = Sidecar(slow)
    server, reviewer = await reviewer_for(sidecar, timeout_seconds=0.05)
    try:
        verdict = await reviewer.review(IMAGE)
    finally:
        await server.close()

    assert verdict.decision is None
    assert not verdict.is_flagged
    assert verdict.note == f"clip;p={PROMPT_SET_FINGERPRINT};unavailable=timeout"


@pytest.mark.parametrize("status", [400, 500, 503])
async def test_a_refusal_from_the_sidecar_fails_open_as_a_status(status: int) -> None:
    # Its body is not read. A 4xx or 5xx from an inference service says something
    # about the service, never about the image.
    sidecar = Sidecar(answering({"detail": "no"}, status=status))
    server, reviewer = await reviewer_for(sidecar)
    try:
        verdict = await reviewer.review(IMAGE)
    finally:
        await server.close()

    assert verdict.note == f"clip;p={PROMPT_SET_FINGERPRINT};unavailable=status"


async def test_a_vector_of_the_wrong_length_is_never_scored() -> None:
    """Recorded as *the sidecar answered wrongly*, not as a verdict.

    Scoring a misaligned vector would attribute this image's similarity to the
    padel caption to whatever caption happened to shift into its place — and it
    would look like an ordinary confident verdict.
    """

    sidecar = Sidecar(answering({"model": MODEL, "similarities": ON_COURT[:-1]}))
    server, reviewer = await reviewer_for(sidecar)
    try:
        verdict = await reviewer.review(IMAGE)
    finally:
        await server.close()

    assert verdict.note == f"clip;p={PROMPT_SET_FINGERPRINT};unavailable=malformed"


async def test_a_body_that_is_not_json_fails_open_as_malformed() -> None:
    async def html(request: web.Request) -> web.StreamResponse:
        return web.Response(text="<h1>502 Bad Gateway</h1>", content_type="text/html")

    sidecar = Sidecar(html)
    server, reviewer = await reviewer_for(sidecar)
    try:
        verdict = await reviewer.review(IMAGE)
    finally:
        await server.close()

    assert verdict.note == f"clip;p={PROMPT_SET_FINGERPRINT};unavailable=malformed"


# ---------------------------------------------------------------------------
# What a well-formed answer is
# ---------------------------------------------------------------------------


def test_a_well_formed_answer_yields_the_model_and_the_vector() -> None:
    model, scores = similarities_in({"model": MODEL, "similarities": ON_COURT})

    assert model == MODEL
    assert scores == pytest.approx(ON_COURT)


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param([1, 2, 3], id="not-an-object"),
        pytest.param({"similarities": ON_COURT}, id="no-model"),
        pytest.param({"model": "", "similarities": ON_COURT}, id="empty-model"),
        pytest.param({"model": MODEL}, id="no-similarities"),
        pytest.param({"model": MODEL, "similarities": "0.3"}, id="not-a-list"),
        pytest.param(
            {"model": MODEL, "similarities": ["0.3"] * len(PHOTO_REVIEW_PROMPTS)},
            id="strings",
        ),
        pytest.param(
            {"model": MODEL, "similarities": [True] * len(PHOTO_REVIEW_PROMPTS)},
            id="booleans-are-not-numbers",
        ),
        pytest.param({"model": MODEL, "similarities": ON_COURT + [0.2]}, id="too-many"),
    ],
)
def test_anything_else_is_rejected_rather_than_interpreted(payload) -> None:
    with pytest.raises(SidecarAnswerRejected):
        similarities_in(payload)
