"""The on-court check, asked over HTTP of a sidecar that holds the model.

**The model does not run in this process, and that is the decision this file
implements** (``docs/adr/0129``). ADR-0091 asked that the real checker drop in
behind the ``PhotoReview`` port with no call-site change; a thin HTTP client
satisfies that as literally as an in-process adapter would, and it keeps
``poetry install``, every CI run and the API image exactly as they are. The
alternative — ``torch`` and a CLIP implementation in ``pyproject.toml`` — puts
the sidecar image's measured 3.2 GB on every install and image, several hundred
megabytes of resident memory in a process that mostly serves JSON, and the
inference itself inline on the upload request.

**The rule stays here; only the arithmetic goes over the wire.** The sidecar is
asked *how close is this image to each of these captions* and answers with one
cosine similarity per caption. Which captions, how those numbers become a
confidence and where the line sits are all in
``player_profile/domain/photos.py``, where a domain test can see them — the
service holds a model and no policy, so a threshold can be re-tuned without
touching it and the model can be swapped without a backend release.

**It fails open, deliberately.** A reviewer that turned its own timeout into a
failed upload would refuse a real player's first photo for a reason that has
nothing to do with the photo — strictly worse than the false reject the
soft-warn rule already declines to pay. An unreachable sidecar produces an
``ALLOWED`` verdict whose note says it was never really looked at, which is a
row a re-review pass can find rather than a signup that did not happen.
"""

from __future__ import annotations

import logging
from base64 import b64encode
from typing import Any, Sequence

import aiohttp

from app.modules.player_profile.domain.photos import (
    PHOTO_REVIEW_PROMPTS,
    PhotoReviewUnavailability,
    PhotoReviewVerdict,
    TranscodedImage,
    verdict_from_similarities,
    verdict_when_unreviewable,
)

logger = logging.getLogger(__name__)

#: The path on the sidecar that scores one image against a list of captions.
SIMILARITIES_PATH = "/similarities"


class SidecarAnswerRejected(Exception):
    """The sidecar answered, and the answer was not one this can use.

    Local to this adapter and never crosses it: every caller of `review` gets a
    verdict. It exists so that the three ways a malformed answer is noticed —
    a non-JSON body, a missing field, a vector of the wrong length — arrive at
    one place instead of three.
    """


def similarities_in(payload: Any) -> tuple[str, list[float]]:
    """The model name and the similarity vector out of one decoded response.

    Pure, and separate from the request, because *what a well-formed answer is*
    is the part worth a test and the part that will change if the sidecar's
    contract ever does. Raises `SidecarAnswerRejected` for anything else —
    including a vector of the wrong length, which is checked here rather than
    left to the domain so that the reason recorded is *the sidecar answered
    wrongly* and not *this image scored strangely*.
    """

    if not isinstance(payload, dict):
        raise SidecarAnswerRejected("response body is not an object")

    model = payload.get("model")
    scores = payload.get("similarities")
    if not isinstance(model, str) or not model:
        raise SidecarAnswerRejected("response names no model")
    if not isinstance(scores, list) or not all(
        isinstance(value, (int, float)) and not isinstance(value, bool)
        for value in scores
    ):
        raise SidecarAnswerRejected("similarities is not a list of numbers")
    if len(scores) != len(PHOTO_REVIEW_PROMPTS):
        raise SidecarAnswerRejected(
            f"asked {len(PHOTO_REVIEW_PROMPTS)} prompts, got {len(scores)} scores"
        )
    return model, [float(value) for value in scores]


class ClipSidecarPhotoReview:
    """`PhotoReview` over a sidecar holding a CLIP model.

    A session is created per call rather than held, for the reason the S3
    adapter creates a client per call: an ``aiohttp.ClientSession`` binds to the
    event loop it was made on, so a long-lived one on an application object is
    the shape that fails under a second loop — a worker, a management command, a
    test — with a symptom a long way from its cause. One review is a
    multi-hundred-millisecond inference call, so a connection setup beside it is
    not a cost worth designing around.
    """

    def __init__(self, *, endpoint_url: str, timeout_seconds: float) -> None:
        self._endpoint_url = endpoint_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    async def review(self, image: TranscodedImage) -> PhotoReviewVerdict:
        try:
            model, similarities = await self._score(image)
        except TimeoutError:
            return verdict_when_unreviewable(PhotoReviewUnavailability.TIMEOUT)
        except aiohttp.ClientResponseError as exc:
            # The sidecar answered, and refused. Its own body is not read: a
            # 4xx or 5xx from an inference service says nothing about the image.
            logger.warning(
                "photo review sidecar returned %s", exc.status, exc_info=False
            )
            return verdict_when_unreviewable(PhotoReviewUnavailability.STATUS)
        except aiohttp.ClientError as exc:
            # Unreachable, DNS, connection reset, TLS. The container is not up,
            # which on a laptop is the ordinary state of a stack that has just
            # started, and is why this is a warning rather than an error.
            logger.warning("photo review sidecar unreachable: %s", exc)
            return verdict_when_unreviewable(PhotoReviewUnavailability.TRANSPORT)
        except SidecarAnswerRejected as exc:
            logger.error("photo review sidecar answered unusably: %s", exc)
            return verdict_when_unreviewable(PhotoReviewUnavailability.MALFORMED)

        return verdict_from_similarities(model=model, similarities=similarities)

    async def _score(self, image: TranscodedImage) -> tuple[str, Sequence[float]]:
        # Base64 rather than a multipart body: the image is already capped at
        # 1600px and re-encoded as JPEG by the time it gets here, so the third
        # this encoding adds is tens of kilobytes on a loopback hop, and one
        # JSON object keeps the request and its answer the same shape.
        request = {
            "image_base64": b64encode(image.data).decode("ascii"),
            "media_type": image.media_type,
            "prompts": list(PHOTO_REVIEW_PROMPTS),
        }
        timeout = aiohttp.ClientTimeout(total=self._timeout_seconds)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                f"{self._endpoint_url}{SIMILARITIES_PATH}", json=request
            ) as response:
                response.raise_for_status()
                try:
                    payload = await response.json()
                except (aiohttp.ContentTypeError, ValueError) as exc:
                    raise SidecarAnswerRejected("response body is not JSON") from exc
        return similarities_in(payload)
