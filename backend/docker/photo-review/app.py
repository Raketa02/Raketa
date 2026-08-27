"""A CLIP model behind one HTTP route, and no opinion about photos.

**This service holds a model and no policy.** It is asked *how close is this
image to each of these captions* and answers with one number per caption. It
does not know what the captions mean, which of them are the ones the product
wants, where a line is drawn, or that anything called a verdict exists — all of
that is in the backend's domain layer, where a domain test can see it
(``../../../docs/adr/0129-the-photo-check-is-a-sidecar-the-backend-asks.md``).

The similarities go back **raw**: cosine, unscaled, un-softmaxed, in the order
the prompts arrived. Every transformation applied here is one the backend cannot
undo later over a stored corpus, and the whole reason the verdict records its
evidence is so a better threshold can be chosen without re-running inference.

Not part of the ``app`` package and not imported by it. It is a separate image
with a separate dependency set, which is the point.
"""

from __future__ import annotations

import base64
import binascii
import io
import logging
import os
from contextlib import asynccontextmanager
from typing import List

import torch
from fastapi import FastAPI, HTTPException, status
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, Field
from transformers import CLIPModel, CLIPProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("photo-review")

#: Where the weights were baked at build time. A local path rather than a hub
#: id, so a container start needs no network and a laptop offline still brings
#: the stack up.
MODEL_PATH = os.environ.get("CLIP_MODEL_PATH", "/models/clip")

#: What the backend records beside every photo this service scores. Reported
#: rather than assumed by the caller: a similarity vector means nothing without
#: the model that produced it, and the backend cannot see which one is loaded.
MODEL_NAME = os.environ.get("CLIP_MODEL_NAME", "openai/clip-vit-base-patch32")

#: The most captions one request may carry. Not a policy about the prompt set —
#: the backend owns that — but a bound on what one request can make this process
#: do, since text encoding is linear in the number of captions.
MAX_PROMPTS = 64

#: The largest image this will decode, in pixels. The backend caps its uploads
#: long before they get here; this is the independent bound, because a service
#: that trusts its caller's caps has no cap of its own.
MAX_DECODED_PIXELS = 40_000_000

_model: CLIPModel | None = None
_processor: CLIPProcessor | None = None


class SimilaritiesRequest(BaseModel):
    image_base64: str = Field(min_length=1)
    prompts: List[str] = Field(min_length=1, max_length=MAX_PROMPTS)
    # Accepted and ignored: Pillow reads the container from the bytes, and a
    # decoder that believed a header over the content would be one more thing a
    # caller could get wrong.
    media_type: str | None = None


class SimilaritiesResponse(BaseModel):
    model: str
    similarities: List[float]


def load_model() -> None:
    """Load the weights once, at startup rather than on the first request.

    A first upload that paid for a multi-second model load would look like a
    slow API, and the client's timeout would turn it into a photo with no
    verdict. The healthcheck goes green only after this returns.
    """

    global _model, _processor
    logger.info("loading %s from %s", MODEL_NAME, MODEL_PATH)
    # One thread, set before the weights are touched. Several containers' worth
    # of BLAS threads on a laptop is how a dev stack starves the database it is
    # sitting next to.
    torch.set_num_threads(int(os.environ.get("TORCH_NUM_THREADS", "1")))
    _processor = CLIPProcessor.from_pretrained(MODEL_PATH)
    _model = CLIPModel.from_pretrained(MODEL_PATH)
    _model.eval()
    logger.info("loaded")


@asynccontextmanager
async def lifespan(_: FastAPI):
    load_model()
    yield


app = FastAPI(
    title="Raketa photo review", docs_url=None, redoc_url=None, lifespan=lifespan
)


@app.get("/health")
def health() -> dict:
    if _model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="loading"
        )
    return {"status": "ok", "model": MODEL_NAME}


def decode_image(image_base64: str) -> Image.Image:
    """The image, or a 400. Never a traceback and never a decompression bomb."""

    try:
        raw = base64.b64decode(image_base64, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="image_base64 is not base64"
        ) from None

    try:
        image = Image.open(io.BytesIO(raw))
        # Declared dimensions, read before a pixel is decoded — the only check
        # that can see a small file that expands to gigabytes of raw pixels.
        if image.width * image.height > MAX_DECODED_PIXELS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="image too large"
            )
        return image.convert("RGB")
    except UnidentifiedImageError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="unreadable image"
        ) from None


@app.post("/similarities", response_model=SimilaritiesResponse)
def similarities(request: SimilaritiesRequest) -> SimilaritiesResponse:
    if _model is None or _processor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="loading"
        )

    image = decode_image(request.image_base64)
    inputs = _processor(
        text=request.prompts,
        images=image,
        return_tensors="pt",
        padding=True,
        truncation=True,
    )

    with torch.no_grad():
        image_features = _model.get_image_features(pixel_values=inputs["pixel_values"])
        text_features = _model.get_text_features(
            input_ids=inputs["input_ids"], attention_mask=inputs["attention_mask"]
        )

    # Cosine similarity, and nothing after it. `logits_per_image` would return
    # these already multiplied by the model's learned temperature; the backend
    # applies that itself, beside the threshold it belongs with, so that what is
    # recorded on the object is the rawest number there is.
    image_features = image_features / image_features.norm(dim=-1, keepdim=True)
    text_features = text_features / text_features.norm(dim=-1, keepdim=True)
    scores = (image_features @ text_features.T).squeeze(0)

    return SimilaritiesResponse(
        model=MODEL_NAME, similarities=[float(value) for value in scores]
    )
