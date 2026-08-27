# The photo-review sidecar

One HTTP service, one job: given an image and a list of captions, say how close the image
is to each caption. It holds a CLIP model and **no policy** — not the captions, not the
threshold, not what *flagged* means. Those are the backend's, in
`app/modules/player_profile/domain/photos.py`, where a domain test can see them
(`../../../docs/adr/0129-the-photo-check-is-a-sidecar-the-backend-asks.md`).

That split is the point. The backend can re-tune the prompt set or move the threshold with
no change here, and this image can be rebuilt on a different model with no backend release.

## Why it is not in the API process

This image is **3.2 GB** built: 605 MB of weights and the rest `torch` and its CPU BLAS
stack. In `pyproject.toml` that weight would be on every `poetry install`, every CI run and
every API image, plus several hundred megabytes resident in a process that otherwise serves
JSON and CPU inference inline on the upload request. Here it is in one image that only a
laptop's compose stack pulls. The cost is a second required local container — a tax ADR-0091
already named when MinIO added the first.

## The contract

`POST /similarities`

```json
{ "image_base64": "…", "media_type": "image/jpeg", "prompts": ["a photo of …", "…"] }
```

```json
{ "model": "openai/clip-vit-base-patch32", "similarities": [0.2713, 0.1904, …] }
```

One cosine similarity per prompt, **in the order the prompts were given** — raw, not
softmaxed and not thresholded. Raw is what makes the recorded verdict re-derivable: the
backend stores these numbers beside the photo, so a better threshold can be chosen later
by reading stored objects instead of paying for inference over the corpus twice.

`GET /health` → `{"status": "ok", "model": …}` once the weights are loaded. It is the
compose healthcheck, and it is *not* something the API waits for: the client fails open,
so a sidecar still loading costs a photo its verdict and never costs a player their
signup.

## Licence

CLIP is MIT (OpenAI), and so is `open_clip`. This is deliberate and it is written down in
ADR-0091: the obvious alternative, Ultralytics YOLO, is AGPL-3.0 — which running inside a
network service obliges publication of this backend's source — and is fitted to the wrong
question anyway.

## The weights are baked into the image

Downloaded at build time and copied in, so a container start needs no network and a laptop
with no internet still brings the stack up. It is why the image is large and why the build
is slow the first time.
