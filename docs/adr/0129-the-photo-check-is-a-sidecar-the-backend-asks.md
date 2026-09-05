# ADR-0129 — The photo check is a sidecar the backend asks; the rule stays in the backend

- **Status:** Accepted
- **Date:** 2026-08-27

> **The threshold's *"it costs nothing today because nothing reads the decision"* expired
> twice.** [ADR-0133](0133-the-verdict-crosses-on-the-upload-and-the-warning-may-be-wrong.md)
> made it a sentence shown to the photograph's owner, and
> [ADR-0138](0138-the-verdict-crosses-on-a-card-and-never-checked-is-its-own-answer.md) made
> it a shield shown to twenty people who are not. The value is still `0.5` and still
> provisional; what this record left as a note about a corpus that did not exist is now
> [#316](https://github.com/Raketa02/Raketa/issues/316). The mechanism that makes it fixable
> is the one this record built: every verdict stores the similarities it was taken from.
>
> **Two Consequences below have been overtaken and neither is wrong about its own day.** *Fail-open
> means an outage is silent to the player* names the trade *"correct while nothing reads the
> decision"* and asks for it to be re-examined *"on the day something does"* — **that day came
> twice, and the re-examination is on the record**: ADR-0133 kept fail-open in substance, and
> ADR-0138 changed its spelling, because an unreachable reviewer now records **no decision**
> rather than `ALLOWED` — the word that meant *nothing to warn about* would mean *checked and
> passed* on somebody else's card. And *the API contract does not change* was true of **this**
> change and of no later one: the verdict crosses on the upload (ADR-0133) and on
> `player_card.review` (ADR-0138), and a card marks **only the pass**.

## Context

[ADR-0091](0091-photo-storage-behind-a-port.md) defined a `PhotoReview` port with a
pass-through adapter and deferred the real check on an argument it wrote down: *nobody can
see another player's photo yet. There is no matchmaking, no player card and no discovery, so
a check today protects nothing.*
[ADR-0107](0107-the-player-card-is-assembled-outside-the-engine.md) creates the player card,
which attaches `photo_id` to a candidate after the engine returns — so every profile photo is
*destined* to be seen by strangers, and the premise the deferral rested on has an expiry date.
It is a **deadline and not a blocker**: what ends the deferral is the first route that returns
`player_card.photo_id` to a client that renders it, and this work shares no file with the
matchmaking build ([#181](https://github.com/Raketa02/Raketa/issues/181)).

Three things were already settled and are not re-opened here. The check runs **server-side**,
because a client-side one is trivially bypassed. It **soft-warns rather than hard-blocks** —
`PhotoReviewDecision` has no `REJECTED`, and a flagged photo is stored with its verdict as
object metadata. And the model is **CLIP, MIT-licensed, used zero-shot**: ADR-0091 records
that Ultralytics YOLO is AGPL-3.0, which running inside a network service obliges publication
of this backend's source, and that COCO offers `tennis racket` and no `court` class at all
while a padel racket is solid, short and stringless — so the highest-volume sport would draw
the highest false-reject rate.

What was left is **where the model runs**, and it turned out to decide **when** as well.

- **In the API process — `torch` plus a CLIP implementation in `pyproject.toml`.** The
  obvious answer, and the one ADR-0091's *drops in behind the port* wording suggests. It puts
  gigabytes on every `poetry install`, every CI run and every API image — the built sidecar
  measures **3.2 GB**, of which 605 MB is the weights and the rest is `torch` and its CPU BLAS
  stack; several hundred megabytes of resident memory in a process that otherwise serves JSON;
  and CPU inference inline on the upload request, which reviews before `storage.put` and
  answers in the same response.
- **A managed vision API.** No local weights and no container. It sends a player's face to a
  third party on every upload, needs a credential this repository does not have, and makes an
  onboarding step depend on somebody else's availability and pricing — for a check whose whole
  design is that it may be wrong.
- **A sidecar container, reached over HTTP.**

The cost of the deferral was almost entirely the first option's dependency weight, and the
third deletes it — which changes the timing answer too. The threshold and the prompt set need
a flag-rate distribution over real photos, and an empty corpus has none; building now is what
*produces* the input that tuning needs, while there is still slack to react to it. The tree is
already **measure-only by construction**: `UploadPhoto` records the verdict as object metadata,
no route returns it, and no client copy shows a warning.

## Decision

We will run the on-court check in a **sidecar container reached over HTTP**, and keep the rule
that interprets its answer **in the backend's domain layer**.

- **`ClipSidecarPhotoReview` is the `PhotoReview` adapter**, a thin `aiohttp` client in
  `player_profile/infrastructure/`. This honours ADR-0091's *no call-site change* as literally
  as an in-process adapter would — the composition root's one line changed and nothing else on
  the upload path did — while `poetry install`, CI and the API image stay exactly as they were.
- **The sidecar holds a model and no policy.** It is asked *how close is this image to each of
  these captions* and answers one **raw cosine similarity per caption**, in the order asked. It
  does not know which captions are the on-court ones, does not softmax, does not threshold and
  has no concept of a verdict. So the prompt set can be re-tuned and the threshold moved with no
  change to the service, and the model can be swapped with no backend release.
- **The prompt set, the temperature and the threshold live in
  `player_profile/domain/photos.py`**, beside the size caps and the retention window, and
  **never in `app/core/config.py`**. They are behaviour a domain test can observe, and a photo
  flagged on a laptop and allowed in production is exactly what the four-environment rule
  forbids ([ADR-0028](0028-four-environment-model-and-typed-configuration.md)). What *is*
  configuration is where the sidecar is and how long it may take; neither can change a verdict.
- **The prompt set is fingerprinted, not versioned.** A short digest of the captions as asked is
  derived at import and written into every note, because a declared version number is a thing
  somebody forgets to bump.
- **Every verdict records its evidence**, allowed ones included: the model, the prompt-set
  fingerprint, the confidence and the raw similarity vector, in `review-note` on the object. The
  threshold shipping today is an explicit placeholder — *the on-court captions won* — and this
  is what makes that safe. A better one is chosen later by reading stored objects, without
  paying for inference over the corpus a second time.
- **The adapter fails open.** An unreachable, slow, refusing or unusably-answering sidecar
  produces `ALLOWED` with a note that names which of those it was, from a closed set. A reviewer
  that turned its own outage into a failed upload would refuse a real player's first photo for a
  reason that is not about the photo — strictly worse than the false reject the soft-warn rule
  already declines to pay. There is deliberately **no third decision value** for it:
  `PhotoReviewDecision` says what the reviewer *concluded* about an image, and an outage is not
  a conclusion about an image.
- **The API does not wait for the sidecar**, in compose or anywhere else. Failing open is what
  makes that safe, and it keeps the slowest container in the stack off the front of `make up`.

This ships in **measure-only posture**, which is not a mode and needs no flag — it is what the
tree already is. Nothing a player experiences changes; what changes is what the recorded verdict
*is*.

## Consequences

**Easier**

- The threshold becomes an empirical question with data behind it instead of a guess, from the
  first upload onwards, and re-deriving it costs a query rather than a GPU afternoon.
- The card can ship against an already-reviewed corpus. The backfill named in #181 shrinks to
  the photos uploaded before this landed, rather than all of them.
- Swapping the model, or replacing CLIP entirely, is a container rebuild. Nothing in `app/`
  names a model, and the port never did.

**Harder**

- **Local development gains a second required container, and it is the heavy one.** ADR-0091
  named this tax when MinIO added the first; this one is **3.2 GB built** and slow the first
  time. A stack that is half-up now records `unavailable=transport` notes instead of verdicts.
  The weight did not go away — it moved somewhere only a laptop's compose stack pulls it, and
  out of the three places that paid for it on every change.
- **The check is now a network hop inside a request.** The upload path acquired a dependency
  that can be slow, and the timeout that bounds it is a number somebody will eventually have to
  defend.
- **Fail-open means an outage is silent to the player and visible only in metadata.** That is
  the correct trade while nothing reads the decision; it is a trade that has to be re-examined
  on the day something does, and the closed set of reasons exists so that day is a query.
- **The prompt set is a rule written in English, and it will be wrong in ways a test cannot
  anticipate.** Four sports whose courts look nothing alike are asked about with five captions.
  What catches that is the flag-rate distribution this ADR exists to start collecting, not
  review.

**Measured, on seven photos, which is a smoke test and not a corpus**

The built sidecar was driven through the real adapter on seven hand-picked images. A padel
court, a tennis player and an empty squash court scored 0.9999, 0.9998 and 1.0000; a selfie
0.207, a dog 0.0009 and a cat 0.0002. A street photograph with a fenced tennis court in the
background and a car in the foreground scored 0.363 and was flagged — arguably correctly, since
it is a photograph of a street.

Two things follow, and neither is a tuned threshold. The confidences **cluster at the ends**
rather than spreading, so the placeholder 0.5 sits in a wide empty gap and almost any value
between 0.4 and 0.95 would have decided all seven identically — which is why moving it later is
cheap. And the one ambiguous case was ambiguous in the *photograph*, not in the model. Seven
images cannot establish a flag rate; that is what the recorded corpus is for.

**Neutral**

- The API contract does not change. No route returns a verdict, no schema gained a field, and
  `openapi.player.json` is byte-identical — so no client work is implied and none is unblocked.
- `PassThroughPhotoReview` stays. It is no longer what the composition root builds, and it is
  the standing proof that ADR-0091's seam did its job: the checker arrived and no use case,
  route or test of the upload path changed shape.
- This does not wake ADR-0010's dormant deployment path. The sidecar is a compose service on a
  laptop; no credential is created and no workflow trigger changes.
