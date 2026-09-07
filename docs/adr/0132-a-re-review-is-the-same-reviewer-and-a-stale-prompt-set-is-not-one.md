# ADR-0132 — A re-review is the same reviewer, and a stale prompt set is not one

- **Status:** Accepted
- **Date:** 2026-08-29

## Context

[ADR-0129](0129-the-photo-check-is-a-sidecar-the-backend-asks.md) built the on-court check
and put it on the upload path. It did not — could not — look at anything already in the
bucket. **Every photo uploaded before it landed carries `review: allowed`, written by
`PassThroughPhotoReview`, which allowed everything by construction.** Nothing looked at
those images. The metadata says otherwise, and says it in exactly the words a real verdict
uses.

That was harmless while nothing could see another player's photo. It stops being harmless
at the same commit ADR-0129 was measured against: **the first route that returns
`player_card.photo_id` to a client that renders it**
([ADR-0107](0107-the-player-card-is-assembled-outside-the-engine.md)). On that day the
corpus is part reviewed and part not, and the deadline is the one
[#181](https://github.com/Raketa02/Raketa/issues/181) already carried, for the same
reason. Filed as [#197](https://github.com/Raketa02/Raketa/issues/197).

**The one thing that makes this tractable is that ADR-0129 shipped the distinction on
purpose.** An unreviewed photo is already distinguishable from a reviewed one, by its note
and by nothing else:

| what the object carries | what happened |
| --- | --- |
| `clip;m=<model>;p=<fingerprint>;c=<confidence>;s=<raw vector>` | an image was really scored |
| `clip;p=<fingerprint>;unavailable=<timeout\|transport\|status\|malformed>` | the reviewer could not be asked |
| **no `review-note` key at all** | the pass-through era |

So *which photos need re-reviewing* is a query over object metadata rather than a guess.
It is also **three** populations, not one, and they are not the same job:

1. **The pass-through era.** No note. Fixed, and only shrinks — the 24-hour sweep
   ([ADR-0091](0091-photo-storage-behind-a-port.md),
   [ADR-0092](0092-periodic-jobs-as-embedded-loops.md)) already removes the ones no
   profile ever committed.
2. **`unavailable=…`.** The sidecar was down, slow or wrong when the photo arrived. This
   population **keeps growing**, which is what makes a one-shot script the wrong shape.
3. **A superseded prompt-set fingerprint.** Reviewed honestly, against captions that are
   no longer the ones being asked.

The forces that actually shape the answer:

- **A metadata write is not free.** An S3 metadata update is a copy of the object onto
  itself, billed and server-side. A re-runnable job that re-stamped what it had already
  fixed would pay for the whole corpus on every tick, for ever.
- **A second reviewer is worse than no backfill.** The verdict is
  `verdict_from_similarities` in `player_profile/domain/photos.py`, the function the
  upload path calls. A batch holding its own threshold could disagree with the upload path
  about one image, and nothing downstream could say which of them was right.
- **Rate.** This is CPU inference per photo against one sidecar container that runs a
  single worker by design, with a live upload path queueing behind it.
- **`unavailable` is a failure mode of the fix, too.** A run while the sidecar is
  unhealthy must not stamp a fresh *could not be asked* over an old one, which is work
  that looks like progress.

## Decision

We will re-review the unreviewed corpus with **a periodic job under ADR-0092**, and the
rules it runs under are these.

- **The note is the query, and reading it is the domain's job.** `review_standing` in
  `player_profile/domain/photos.py` answers *never asked / unavailable / reviewed* from
  one string, and the encoder that writes that string (`review_metadata`) sits beside it.
  The two metadata keys move out of `application/upload_photo.py` into the domain for that
  reason: an encoder in one module and a decoder in another is the pair that drifts, and
  drift here is a backfill that silently finds no population at all.
- **A note that cannot be read is *nobody looked*.** This is the deliberate inverse of the
  sweep's rule, which refuses to act on a key it cannot parse. The sweep's action is a
  delete and a wrong answer destroys something a player cannot get back; this job's action
  is a re-read, and a wrong answer costs one inference and leaves behind a note that does
  parse.
- **Populations 1 and 2 are the work. Population 3 is counted and left alone.** Whether a
  corpus judged against older captions is worth re-running is a judgement about how far
  the set moved, and nobody has made it. What the fingerprint buys is that the question is
  *answerable*: the count is in the job's log line, so the decision is taken against a
  number rather than a guess. **Deciding to re-run population 3 is a new record, not a
  configuration change** — and `PROMPT_SET_FINGERPRINT` is derived from the prompts
  themselves, so the population appears the moment somebody edits a caption.
- **It re-reviews through the `PhotoReview` port and stores what it is handed.** No
  threshold, no confidence and no prompt set appear in the use case. This is the seam
  ADR-0091 defined and ADR-0129 proved: the backfill is a second *caller* of the checker
  and never a second checker.
- **It never rewrites a note that is already right**, which the reviewed shape makes a
  string test rather than a lookup.
- **A run against a reviewer that cannot be *reached* stops; a refusal about one image
  does not.** The old note is left exactly as it was either way — stamping the result
  would erase the evidence of when the photo actually arrived — but what happens next
  turns on which of the four `PhotoReviewUnavailability` reasons came back. A timeout or a
  transport error mean the container is not answering, so the next photo gets the same
  answer and the run ends rather than spending its budget one full timeout at a time. A
  status or a malformed body mean it *answered*, possibly about that one image: those are
  counted and stepped over. **This is the difference between a job that pauses and a job
  that stalls** — one photo the sidecar always refuses would otherwise end every run at
  the same object, for ever, and nothing behind it in the listing would be looked at
  again. It is the same trap an undecodable object is caught to avoid, and the split lives
  on the enum (`is_about_the_reviewer`) so a fifth reason cannot be added without deciding
  which kind it is.
- **Rate is configuration and selects nothing, and the two halves of it protect different
  things.** The budget and the pause between asks
  (`PHOTO_REVIEW_BACKFILL_BATCH_LIMIT`, `PHOTO_REVIEW_BACKFILL_PAUSE_SECONDS`) protect the
  **sidecar**: one container, one worker, a live upload path queueing behind it. The
  cadence (`PHOTO_REVIEW_BACKFILL_INTERVAL_SECONDS`) protects the **object store**, and it
  is in hours for the same reason the sweep's is — a tick walks the whole prefix whether
  or not there is anything left to do. None of them can change *which* photos are chosen
  or *what* is concluded, which is the line
  [ADR-0028](0028-four-environment-model-and-typed-configuration.md) draws and the same
  one that keeps the sweep's retention window in the domain while its cadence is a
  setting.
- **The port grows three methods, and one of them is a write.** `with_review_notes` (list
  with metadata), `read` (the bytes back) and `replace_metadata` (a copy of the object
  onto itself). `PhotoStorage` was previously write-once-read-never for a stored object's
  content; this is the first thing on the platform that reads a photo's bytes back out.
- **It is idempotent and safe beside itself, with no lock** — ADR-0092's condition for
  being registered at all. Two runs handed the same photo both ask and both write the
  same-shaped metadata, and the loser overwrites a verdict with a verdict. The bytes are
  never touched by either. What *N* processes cost here is duplicated inference, which is
  why the budget is small and the interval is not.

**No moderation queue, no second opinion, no appeal.** Nothing a human looks at is in
scope, and the threshold and the prompt set stay exactly as provisional as ADR-0129 left
them.

## Consequences

**Easier**

- The corpus becomes uniform before the player card can show any of it, and *has this
  photo been looked at* stops being a question about when it was uploaded.
- The threshold work ADR-0129 deferred gets the whole corpus rather than the recent half:
  every re-reviewed photo records the similarity vector it was scored from, so a real
  threshold is still derivable by reading stored objects instead of paying for inference
  twice.
- Population 2 stops being a leak. It grows on every sidecar outage and now drains on a
  clock instead of accumulating for the life of the platform.

**Harder**

- **A listing does not carry user metadata in any S3-compatible store, so a run is one
  `HEAD` per object.** In the steady state — every photo reviewed — a run is that many
  HEADs and no inference at all, per API process, for ever. That is the price of keeping
  the verdict *on the object* rather than in a table beside it, which is a trade ADR-0091
  already made for a different reason; the point at which to revisit it is when the corpus
  makes the walk itself expensive, and the fix then is the same one ADR-0092 names for the
  sweep — not a second table.
- **Two periodic jobs now walk the same bucket with no lock between them.** The sweep can
  delete a photo between this job's listing and its read, or its read and its write. Both
  outcomes are handled — `read` answers `None`, `replace_metadata` treats absent as
  success — and neither can produce a wrong verdict, because a photo id is never reused.
  It is still a second job over one prefix, and it is the first time this repository has
  had two.
- **A corrupt object, and a photo the sidecar always refuses, are re-read on every tick,
  for ever.** Neither can be reviewed; both are counted and left carrying whatever they
  carry, because stamping a verdict nobody took would be worse. They stay visible in the
  report rather than being hidden by a note, and nothing removes them. That is the price
  of not stalling on them, and it is the right way round: a bounded cost that shows up in
  a log line beats an unbounded one that shows up as photos nobody ever re-reviewed.
- **The re-review scores a re-encode, not the stored bytes.** The reviewer takes a
  `TranscodedImage` and the store cannot say how big a stored photo is, so the bytes go
  back through `ImageTranscoder` on the way in. The stored object is already JPEG inside
  the cap, so this is a second encode at quality 85 of an image nothing writes back —
  invisible to a cosine similarity, and the alternative was a dimension field on the port
  that only this caller wants.
- **A backfilled photo's verdict is not the verdict its upload would have produced.** It
  is today's model and today's prompt set against an image from months ago, and the note
  records that honestly. This is correct and still worth stating: the corpus after a
  backfill is uniform in *having been looked at*, not in *when*.

**Neutral**

- Population 3 is now a number in a log line and nothing else. If it is never acted on,
  the cost of having measured it is one field.
- This does not wake ADR-0010's dormant deployment path, and it adds no container: the
  sidecar it asks is the one `make up` already starts.
