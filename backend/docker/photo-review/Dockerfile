# The photo-review sidecar: a CLIP model behind one HTTP route.
#
# Two stages, and the split is about the weights rather than about the code. The
# builder downloads the model once and saves it to disk; the runtime copies that
# directory in, so a container start needs no network — a laptop offline still
# brings the stack up, and a Hugging Face outage is not a local dev outage.
#
# This image is large. That is the whole reason it is a separate image: the API
# image, every CI run and every `poetry install` stay exactly as they were.

FROM python:3.11-slim AS weights

ARG CLIP_MODEL_NAME=openai/clip-vit-base-patch32
# An ARG is not an environment variable. Exported here so the script below reads
# the value the build was given rather than silently falling back to its own
# default — the failure mode being an image whose weights are not the ones asked
# for, reporting the name that was.
ENV CLIP_MODEL_NAME=${CLIP_MODEL_NAME}

# Pillow is not optional here even though nothing in this stage opens an image:
# `CLIPProcessor` bundles `CLIPImageProcessor`, which refuses to be constructed
# without PIL — so `from_pretrained` fails at *save* time, not at use time.
RUN pip install --no-cache-dir \
      "transformers==4.46.3" "torch==2.5.1" "pillow==11.0.0" \
      --extra-index-url https://download.pytorch.org/whl/cpu

RUN python - <<'PY'
import os
from transformers import CLIPModel, CLIPProcessor

name = os.environ.get("CLIP_MODEL_NAME", "openai/clip-vit-base-patch32")
CLIPModel.from_pretrained(name).save_pretrained("/models/clip")
CLIPProcessor.from_pretrained(name).save_pretrained("/models/clip")
PY


FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1 \
    CLIP_MODEL_PATH=/models/clip \
    TORCH_NUM_THREADS=1

WORKDIR /srv

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY --from=weights /models/clip /models/clip
COPY app.py ./

# Unprivileged, like the API image. Nothing here writes anything.
#
# The `chmod` is load-bearing and its absence is a *silent* failure: `save_pretrained`
# writes `model.safetensors` as `0600` root, and `safetensors` reports a file it cannot
# open as `FileNotFoundError` — so an unreadable weights file looks exactly like an
# image that was never given one.
RUN useradd --create-home --uid 10001 review \
    && chown -R review /srv \
    && chmod -R a+rX /models/clip
USER review

EXPOSE 8000

# One worker. The model is several hundred megabytes resident and a second
# worker would be a second copy of it, for a service whose whole traffic is one
# request per uploaded photo.
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
