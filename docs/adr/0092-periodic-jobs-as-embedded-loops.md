# ADR-0092 — Periodic jobs are embedded loops, and a job must be safe to run twice at once

- **Status:** Accepted
- **Date:** 2026-08-25

## Context

[ADR-0091](0091-photo-storage-behind-a-port.md) decided that photos uploaded during
onboarding's second part and never committed to a profile are swept after 24 hours, and
recorded in the same breath what that costs: **the platform has no periodic-job
machinery.** There is an embedded `EventWorker` polling the transactional outbox
([ADR-0003](0003-transactional-outbox-for-event-delivery.md)) and nothing else. A
scheduled sweep is new machinery, and #142 was split out of the storage ticket precisely
so the shape of it could be decided rather than assumed.

So the question is not *how do I delete old objects* — that is a listing and a delete. It
is **what runs it, how often, and what happens when two of them run at once.** The
platform's deployment path is dormant ([ADR-0010](0010-local-first-development-aws-deferred.md)):
everything runs locally, there is one API container, and there is no orchestrator to hang
a schedule on. But the answer has to survive the day that path wakes and there are several
API processes, because that is the day a naïve answer breaks.

The options:

- **An OS cron entry, or an ECS scheduled task.** The conventional answer, and it puts the
  schedule where operators expect to find it. It also puts the schedule *outside the
  repository* — in a crontab or a task definition — so a job's code and the fact that it
  runs are versioned separately, and the second one is the one that silently stops being
  true. It needs an entrypoint that boots the application without serving it, and on ECS
  it is a second task definition with its own image tag to keep in step. All of that is
  real work in service of a deployment target that does not exist yet.
- **A queue with a scheduler — Celery beat, APScheduler, arq.** A dependency, a broker, a
  second process, and a whole vocabulary (beat, workers, queues, results) for one job that
  runs four times a day. It is the right answer at the scale where jobs have priorities,
  retries with backoff, and a dashboard. This platform has one job.
- **A leader-elected loop.** An advisory lock in Postgres, or a lease row, so that exactly
  one process runs the job per interval. It is the answer that lets a job be *unsafe* to
  run concurrently — and it is a distributed-systems component with its own failure modes
  (a held lock behind a dead process, a lease that expires mid-run) written to protect
  work that does not need protecting.
- **An `asyncio` loop in the API process.** What the outbox worker already is.

The fourth option only works if concurrent runs are harmless. That turned out not to be a
compromise for the sweep but a property of it: listing is a read, checking whether a
profile references a photo is a read, and `DeleteObject` is idempotent in every
S3-compatible store — an absent key is a 204, not a 404. Two sweeps handed the same orphan
both succeed, and the loser deletes nothing.

## Decision

We will run periodic jobs as **`asyncio` loops hosted by the API process**, and we will
require every job to be **idempotent and safe to run beside itself**.

- **`PeriodicJob`** (`backend/app/infrastructure/jobs/`) is the whole mechanism: start a
  task, run the work, wait the interval, stop cleanly on shutdown, and **log a failed run
  without ending the loop**. A job that could not reach its dependency this morning runs
  again this evening; a loop that died on it stops doing its work and looks identical from
  outside.
- **`app/bootstrap/jobs.py` is the register**, and where the next job is added. One
  function per job, built from the same `app/bootstrap/composition.py` adapters a request
  is served from, so a job reaches the same bucket and the same event store rather than a
  second opinion about where either lives.
- **The `EventWorker` is rewritten on top of `PeriodicJob`** and keeps only what makes it
  that job: a session per tick, the batch, and the worker id its batches lease outbox rows
  under. The two are not the same *kind* of work — one drains a queue as fast as it fills,
  the other runs because a period elapsed — but they are the same *loop*, and a shutdown
  path written twice is one that is correct in one copy and not the other.
- **The concurrency rule is the price of the choice, and it is stated as a rule rather
  than defended as a coincidence.** With N API processes a job runs N times per interval,
  at unrelated moments, with no lock anywhere. A job that cannot tolerate that may not be
  registered here; it needs a different mechanism, and that mechanism needs its own ADR.
- **The first run is immediate**, before the first interval elapses. On a job measured in
  hours that is the only thing that makes it observable on a laptop, where nobody leaves
  the API up that long — and a job that is safe beside itself is by construction safe to run again at
  every restart.
- **The retention window is domain; the cadence is configuration.** How old a photo must
  be before it is an orphan is a rule a domain test can observe, and it lives in
  `player_profile/domain/photos.py` with the size caps and for the same reason
  ([ADR-0028](0028-four-environment-model-and-typed-configuration.md): the environment may
  select configuration, never behaviour). How often the job runs is operational and lives
  in `Settings`. The sweep is registered at six hours against a 24-hour window, so the
  window is a promise about how long an orphan lives rather than a lower bound a daily
  cadence would double.

The first job under this decision is the **uncommitted photo sweep** (#142): every photo
the store took more than 24 hours ago that no committed profile currently names is
deleted. *Currently* is deliberate — a photo dropped from a profile is as unreachable as
one never committed, and gets the same answer. References are read from the profile
stream, one replay per owner rather than one per photo, which the store's own
lexicographic key order makes possible.

This does **not** wake ADR-0010's dormant deployment path. No scheduler is provisioned, no
task definition is added, and nothing here runs against AWS.

## Consequences

**Easier**

- A job is a use case and one line in a register. There is no second deployable, no
  broker, no image to keep in step, and the fact that a job runs is versioned in the same
  commit as what it does.
- Shutdown is written once. Every job inherits the grace period, the cancellation and the
  swallowed-failure behaviour, rather than each one getting a hand-written version of a
  path nobody exercises until a container is slow to die.
- The sweep needs no lock, so there is no lock to hold, expire, or leak behind a dead
  process — and no leader election to reason about the day there is more than one API.

**Harder**

- **A job runs once per API process, not once per platform.** Today that is one process.
  With four, the sweep lists the photo prefix four times a day times four, and the
  duplicated listings are wasted work even though the deletes are harmless. This is the
  real cost of the choice, and the point at which to revisit it is when a job's *work*
  rather than its result becomes expensive to duplicate.
- **The concurrency rule is enforced by reading, not by a test.** Nothing prevents somebody
  registering a job that must run exactly once. It is written at the top of the register
  and in the mechanism's own docstring, which is the best available given that the property
  is about a job's semantics rather than its shape.
- **The sweep holds one database session for the length of its walk.** It takes a session
  per *run* — never one held between ticks — but within a run the profile replays share it,
  so a read transaction stays open while the object store is paged. That is invisible at
  today's corpus and is the first thing to change when it is not: the replacement is a
  narrower port than `PlayerProfileRepository` — one that answers *which photos does this
  player's profile name* and opens a session per question — which the sweep would be better
  off depending on anyway, since it has no business being able to save an aggregate. It is
  not built now because a port with one implementation and one caller, added for a load
  nobody has, is the speculative generality this repo refuses elsewhere.
- **Job work competes with request serving.** It is the same event loop. The sweep is I/O
  bound against an object store and a database, so it yields constantly and the cost is
  small — but a future job that computed rather than waited would block requests, and
  nothing here would say so.
- **A job's schedule is invisible to operators.** There is no crontab to read and no
  dashboard: the evidence a job ran is a log line, which is why the sweep logs its report
  at info even when it deleted nothing. *Ran and found nothing* and *did not run* are the
  two states that have to be distinguishable from outside.
- **Sweeping is unrecoverable.** Deleting a photo destroys a thing a player cannot get
  back, and the sweep decides with what the object key says and what the profile stream
  says. That is why the key parser refuses anything that is not exactly the layout this
  application writes, rather than guessing: an object nobody can identify is left alone.

**Neutral**

- There is one race the sweep does not close, and it is recorded rather than papered over:
  a commit that names a photo *between* the reference check and the delete loses that
  photo. The window is microseconds, reachable only by a client that uploaded, waited a
  full day, and then committed inside them; closing it would mean a lock spanning the
  object store and the event stream. The recovery, if it ever happens, is an empty tile
  and a re-picked photo.
- Photos remain the only thing on the platform that is expensive per unit and cannot be
  regenerated ([ADR-0091](0091-photo-storage-behind-a-port.md)). This gives the corpus a
  floor; retention, export and deletion of *committed* photos are still unanswered.
