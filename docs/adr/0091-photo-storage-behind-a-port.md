# ADR-0091 — Photo bytes live behind a port; MinIO locally, S3 deployed

- **Status:** Accepted
- **Date:** 2026-08-25

> **Amended 2026-08-26 by [ADR-0107](0107-the-player-card-is-assembled-outside-the-engine.md):
> the condition this record deferred the photo check on has expired.** The argument below is
> *"nobody can see another player's photo yet. There is no matchmaking, **no player card** and
> no discovery, so a check today protects nothing, while a false reject blocks a real player on
> their first day."* ADR-0107 creates the player card, so every photo becomes visible to
> strangers. The `PhotoReview` port and its pass-through adapter stand as decided, and the
> soft-warn-never-hard-block ruling stands — what has gone is the asymmetry it rested on, since
> a passed photo is no longer seen by nobody. Filed as
> [#181](https://github.com/Raketa02/Raketa/issues/181); nothing else in this record changes,
> and the deferral is left as written because the reason it expired is the useful part.

## Context

The social steps of onboarding let a player attach up to three photos to their Player profile
([ADR-0089](0089-player-profile-context-event-sourced.md)). Photos are optional — a player
who adds none gets a generated court poster instead — but the step is real and functional,
and it makes the platform hold its first binary.

Nothing in the backend can hold one. `backend/app/infrastructure/` is `clock`, `database` and
`events`; there is no storage adapter, no upload path and no bucket.
[ADR-0010](0010-local-first-development-aws-deferred.md) keeps the entire AWS path **intact
but dormant**, and development is local Postgres and local Docker only. So the question is
not *which cloud* but *what do we write against today such that the deployed answer is not a
rewrite*, given the deployment target is AWS.

The options:

- **Postgres, as `bytea` or large objects.** No new infrastructure at all, transactional with
  the rest of the write, and by far the fastest thing to build. It is also the one that is
  painful to reverse: the database grows with every upload, every backup and restore carries
  the image corpus, and moving to object storage later is a migration of live user data
  rather than an adapter swap.
- **A local filesystem volume.** Cheap and obvious, and it diverges from production on the
  exact axes that bite — durability, concurrent access, and how a URL is handed to a client.
  The local code would be a shape production never uses.
- **MinIO.** S3-compatible, runs as one container in the existing compose file, and speaks
  the same API the deployed answer speaks.

There is a second seam in the same area. The product rule is that photos show a racket sport
on a court, and the source specification's copy claims that rule is *enforced by an automatic
check*. **That check is not in this slice**, and shipping the copy as written would have the
screen claim an enforcement that does not run — so the copy states the rule without claiming
the enforcement. The checker itself is deferred for a reason worth recording rather than
rediscovering: nobody can see another player's photo yet. There is no matchmaking, no player
card and no discovery, so a check today protects nothing, while a false reject blocks a real
player on their first day.

Recording one finding so it is not re-litigated later: **Ultralytics YOLO (v5, v8, v11) is
AGPL-3.0.** Running it inside a network service without a paid Enterprise licence obliges
publication of this backend's source. It is also fitted to the wrong question — the COCO
classes offer `tennis racket` and `sports ball` and **no `court` class at all**, so a COCO
detector asserts *a racket-shaped object is present*, not *this is a racket sport on a
court*. A padel racket is solid, short and stringless, so the highest-volume sport would draw
the highest false-reject rate. The better-fitted candidate when the check does land is
**CLIP (MIT), used zero-shot** against phrased prompts, which asks something much closer to
the actual rule and needs no training.

## Decision

We will put photo bytes behind a **`PhotoStorage` port**, with two adapters.

- **`MinioPhotoStorage`** for `local`, added as a container to
  `backend/docker-compose-local.yml`. **`S3PhotoStorage`** for the deployed environments,
  which satisfies the same port with no call-site change. This is the ordinary
  ports-and-adapters shape [ADR-0001](0001-clean-hexagonal-architecture.md) already applies
  everywhere else in this backend; the only thing worth deciding was which local adapter
  makes the deployed one a swap rather than a rewrite.
- **Upload is its own request, one photo at a time**, returning a photo id. The profile
  commit carries **ids only**. Three multi-megabyte images inside the commit would turn an
  idempotent JSON POST into a multipart upload whose failure takes the whole part's answers
  with it; separating them means a failed upload costs one photo.
- **Bytes are re-encoded server-side on receipt** — accepted as JPEG, PNG or HEIC, stored as
  JPEG at a capped long edge, with a request size cap. **Re-encoding is how EXIF is stripped
  reliably** rather than best-effort, and EXIF is not a detail here: it carries GPS, which is
  the same class of data the product's own privacy table puts in its *nobody, ever* row.
- **Photos are served through short-lived presigned URLs, never from a public bucket.** A
  photo has a scoped audience in this product; a public object URL is an unscoped one, and
  the difference is not recoverable once the URLs are in the wild.
- **Uploaded-but-uncommitted photos are swept after 24 hours.** The social part takes
  minutes, so anything older belongs to a commit that never happened, and those blobs are
  paid-for storage holding a stranger's face attached to no account state.
- **A `PhotoReview` port is defined now, with a pass-through adapter.** The call sites exist
  from day one and the real checker drops in behind it. When it lands it runs **server-side**
  — a client-side check is trivially bypassed — and **soft-warns rather than hard-blocks**,
  because in a product where a false reject stops a real player and a passed photo is seen by
  nobody, the two errors are not symmetric.

This does **not** wake the dormant deployment path of ADR-0010. Nothing here runs against
AWS, no credential is created and no workflow trigger changes. What it buys is that the day
that path does wake, storage is already portable.

## Consequences

**Easier**

- The deployed answer is an adapter, not a migration. No live user data has to move, and the
  code that runs locally is the shape production runs.
- EXIF stripping is structural rather than a call someone must remember, in the same way the
  logger's redaction is.
- The checker becomes a drop-in later, and the licence and model-fit questions are answered
  in writing before anyone reaches for the obvious library.

**Harder**

- **Local development gains a required container.** `docker-compose-local.yml` grows MinIO,
  and a developer whose stack is half-up now gets upload failures rather than a clean
  refusal. This is a real tax on the simplest workflow in the repo.
- **S3-compatible is not S3.** Presigned URL semantics, multipart edges and CORS behaviour
  differ enough that the adapter swap will not be literally free, and the first deployment
  will find at least one of them. It is a much smaller surprise than a data migration, which
  is the trade being made — but it is not zero, and claiming otherwise would be the
  comfortable lie in this ADR.
- **The 24-hour sweep needs a scheduler the platform does not have.** There is an embedded
  `EventWorker` polling the outbox and nothing else; a periodic job is new machinery, and
  until it exists orphaned blobs accumulate. **Answered by
  [ADR-0092](0092-periodic-jobs-as-embedded-loops.md)** (#142): the sweep runs today, as an
  `asyncio` loop in the API process, on the condition that a job be safe to run beside
  itself. The cost this bullet names was real and is now paid — recorded here rather than
  edited away, because what it cost is why 0092 exists.
- Photos are the first thing the platform stores that is expensive per unit and cannot be
  regenerated. Retention, export and deletion now have a binary corpus to account for, not
  only rows.

**Neutral**

- The generated court poster for a player with no photo touches none of this: it is derived
  from a hash of the player id and rendered on the client, so *no photo* costs no storage and
  still produces a stable identity across devices and reinstalls.
- Deferring the checker leaves the product rule stated and unenforced for a period. That is
  visible in the copy — which states the rule without claiming enforcement — rather than
  hidden, which is the only version of this that is honest.
