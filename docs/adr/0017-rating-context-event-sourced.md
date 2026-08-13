# ADR-0017 — Assessment and SkillRating are event-sourced

- **Status:** Accepted
- **Date:** 2026-08-13

## Context

[`CONTEXT.md`](../../CONTEXT.md) requires this decision to be made deliberately and written
down before a new context is coded: whether it is **event-sourced** like `User` or
**persisted-with-events** like `RefreshToken`. The rating context is the first racket-sport
context to be built, so it also sets the example the rest will read.

Two things about the rating domain make the choice unusually clear.

**The specification already describes an event-sourced design without using the words.**
The rating model's data section asks for `question_response` (question id, version, option,
ordinal, asked order, timestamp), `routing_event` (step, current μ and σ, candidates,
selection, selection reason, projected gain) and `rating_event` (event type — onboarding,
match, inactivity, recalibration, status change — with before and after μ, σ and
volatility, and the engine version). Those are events. `rating_snapshot` and
`assessment_features` are projections over them.

Built as CRUD tables *plus* those logs, every write becomes a dual write, and the day the
rating row and the replayed log disagree there is nothing to say which one lied.

**The engine is a pure function of the transcript** ([ADR-0015](0015-engines-as-a-pure-versioned-layer.md)).
The adaptive router branches on the live estimate, which is recomputed from every answer
given so far; the flags the prototype held as mutable session state are all derivable,
provided the transcript records *why* each question was asked as well as what was answered.
The specification independently demands exactly that record, for a different reason:
*"missing answers are not random — a future model has to know why a question was never
asked, or it will learn from the gaps instead of the answers."*

So the purity requirement and the machine-learning requirement turn out to be the same
requirement, and an event stream satisfies both at once. Recording the routing decision is
described as *"easy to skip and expensive to omit"*; making it the stream is what stops it
being skippable.

The alternatives considered:

- **A JSON transcript column** on an `assessments` row, appended per answer, with the
  rating event-sourced. Less machinery on a short-lived object, but the routing log becomes
  a second write to remember, and the answer path loses optimistic concurrency.
- **Plain tables with separate audit and ML logs.** Familiar, and the dual-write shape.

## Decision

We will model both aggregates as **event-sourced**, on the existing `DomainEventStore`.

- **`Assessment`** — stream `assessment-{id}`. One adaptive questionnaire run, for one
  player and one sport. Events: `AssessmentStarted` (sport, engine version, questionnaire
  version), `QuestionAsked` (question id and version, selection reason, projected gain, the
  μ and σ that existed at that moment), `QuestionAnswered` (option id, ordinal value,
  answered at), and `AssessmentCompleted` or `AssessmentAbandoned`. **Replaying the stream
  produces the transcript the engine consumes** — there is no second representation.
- **`SkillRating`** — stream `rating-{player_id}-{sport}`. Events: `RatingInitialised`
  today; `RatingUpdatedFromMatch`, `RatingWidenedByInactivity`, `RatingStatusChanged` when
  matches exist. Every event carries the engine version that produced it.
- **The key is `(player_id, sport)`.** There is no format dimension; see
  [`CONTEXT.md`](../../CONTEXT.md).
- **Projections, not parallel writes.** `player_ratings` is the read model matchmaking
  queries for many players at once; `assessment_features` is the training projection. Both
  are built from the streams and never written independently.
- **Answers are append-only.** No retraction event and no replay branching. An answer is
  accepted only for the question currently outstanding, which makes re-submission idempotent
  by domain rule; `expected_version` on the event store makes a concurrent double-submit
  fail loudly rather than corrupt the transcript. A mis-tap is prevented on the client with
  an explicit confirm before the answer is sent.
- **Completing an assessment is one transaction.** `AssessmentCompleted` and
  `RatingInitialised` are appended together and the result is returned inline, because the
  player sees their rating on the next screen. **The outbox carries side effects only** —
  projections, analytics, later notifications — never a state transition a response
  depends on.

## Consequences

**Easier**

- The audit trail the specification asks for is not something anyone has to remember to
  write. *Why did this rating move?* is answerable by construction, for every rating, for
  the life of the product.
- A historical assessment can be replayed against a newer engine version to measure what
  the change would have done — which is how a constant gets falsified rather than merely
  re-guessed.
- The double-submit race has two independent guards, one in the domain and one in the
  store, without an idempotency-key mechanism.
- The pattern matches `User`, so the rating context reads like the code already in the tree.

**Harder**

- **Every answer is a stream append with a version check**, which is heavier than an
  `UPDATE`. Volumes are trivial here — under ten events per assessment — but the pattern is
  being set for contexts where they will not be.
- **Read models can lag.** Anything that must be read immediately after a write has to come
  from the transaction that wrote it, not from a projection. The completion path is written
  that way on purpose; future paths must be too.
- Events are a published contract. Changing a payload means a new version in the event
  catalog, not an edit — including for events nobody outside the module reads yet.
- Answers being irreversible is a real product constraint, not only a storage one. It is
  what keeps contradiction detection from becoming opt-out, and it costs the player the
  ability to change their mind two questions later.

**Neutral**

- Question definitions need no table. A shipped engine version is never deleted, so the
  question bank that asked a historical assessment is still readable as code.
- `volatility`, `counted_matches`, `informative_matches` and the diversity counters are
  present on the rating and inert until the match-update engine exists. They are scalar
  attributes with specified future behaviour, not key dimensions, so carrying them costs a
  column rather than a migration.
