# ADR-0018 — Aggregate repositories over the event store

- **Status:** Accepted
- **Date:** 2026-08-14

## Context

The rating context ([ADR-0017](0017-rating-context-event-sourced.md)) is the first to
accumulate several use cases that write an event-sourced aggregate, and it made visible
something a single use case hides.

Four of them — `CreateAssessment`, `SubmitAnswer`, `AbandonAssessment`, `GetAssessment` —
each walk the same eight steps: `load_stream` with a literal aggregate-type string,
`from_history`, an ownership check, capture `base_version` *before* mutating, mutate,
`pull_events`, `append(expected_version=…)`, `publish_many`, `commit`. The literal
`ASSESSMENT_AGGREGATE = "assessment"` is declared in five modules and `RATING_AGGREGATE`
in two. The rule that a mismatched player is *indistinguishable from does not exist* is
written three times.

The `base_version` capture in particular is not defensive style. `Assessment._record_that`
records and applies in one step, so `version` is already the post-mutation value by the
time a use case is ready to persist. Every caller has to know that, and the knowledge is
carried only by convention.

**The cost is measurable in the test suite.** None of those four use cases has a unit
test. Exercising one means standing up a `DomainEventStore`, a `UnitOfWork` and a
`DomainEventPublisher` together — a miniature event-sourcing runtime — so all coverage
runs through `tests/api/test_assessments.py`, 1206 lines of HTTP over SQLite.
`tests/unit/test_load_all_in_progress.py` reaches past the use case to a module-level
function instead, and the `SkillRating` aggregate is named by no unit test at all.

There is a second, quieter coupling. The in-progress and ratings lookups find streams by
matching the **stored JSON payload** of a stream's opening event
(`payload_equals={"player_id": …, "sport": …}`), so those dict keys must agree with the
serialized field names of `AssessmentStarted` and `RatingInitialised`. A rename does not
raise: the query returns `[]`, which is indistinguishable from *no run in progress* — the
ordinary answer for almost every player. `.claude/rules/domain-events.md` protects an
event's durable *name*; nothing protects the field names these queries read.

**`UserRepository` looks like a precedent and is not.** It is a *read-model* repository
over the `users` projection table — `get_by_email`, `get_by_nickname`,
`project_registered` — and exists so uniqueness surfaces as a domain conflict rather than
a constraint violation. `RegisterUser` still talks to the event store directly, aggregate
string and all. So no pattern existed to follow, and the shape chosen here is the one the
planned contexts will read.

The alternatives considered:

- **Leave it.** Correct while a context has one writing use case. The rating context has
  four, and the four planned contexts in [`CONTEXT.md`](../../CONTEXT.md) Part 2 will each
  have several.
- **Module-level helper functions** over the store. Removes the repetition without moving
  the seam: a use case still takes `DomainEventStore`, so it still cannot be tested
  without one, which is the problem worth solving.
- **A generic `EventSourcedRepository[A]`**, parameterised by aggregate type and a
  `from_history` callable, shared across contexts.

## Decision

We will give each event-sourced aggregate **its own repository port**, declared in the
module's `domain/ports.py` and implemented in its `infrastructure/`.

```python
class AssessmentRepository(Protocol):
    async def load(self, assessment_id: UUID, *, for_player: UUID) -> Assessment: ...
    async def save(self, assessment: Assessment) -> None: ...
    async def find_open(self, *, player_id: UUID, sport: Sport) -> Assessment | None: ...
    async def find_all_open(self, *, player_id: UUID) -> list[Assessment]: ...

class SkillRatingRepository(Protocol):
    async def save(self, rating: SkillRating) -> None: ...
    async def find_all_for(self, *, player_id: UUID) -> list[SkillRating]: ...
```

- **`save` appends and publishes. It never commits.** The transaction boundary stays with
  the use case, because completing an assessment spans two aggregates in one transaction
  and ADR-0017 states that as a domain rule, not a persistence detail. Completion reads
  `save(assessment)` · `save(rating)` · `uow.commit()`, and the rule stays where a reader
  can see it.
- **The adapter holds a per-request identity map of loaded versions,** so `save` recovers
  the expected version itself rather than taking it. An aggregate the repository never
  loaded has no entry and is therefore appended at `expected_version=0` — so *this stream
  does not exist yet* is a consequence of never having read it, not a literal someone
  types.
- **`save` on an aggregate with no pending events is a no-op.** It is the same statement
  as saving one already saved — *the store already agrees with this aggregate* — and it is
  what makes abandoning an already-abandoned run idempotent without the use case
  remembering to check.
- **`for_player` is required and keyword-only on `load`,** which raises
  `AssessmentNotFound` for a stream that is absent *or* another player's. An id alone does
  not name an Assessment in this system; `(id, player)` does, which is already how the
  repository finds streams at all. Forgetting the argument is a `TypeError` rather than
  one player reading another's transcript. A future path that legitimately reads across
  players gets a second, explicitly-named method.
- **The finders live on the repository,** so the aggregate-type string and the
  payload-key coupling each have exactly one home, and the newest-first scan and the
  one-open-run-per-sport rule become one implementation that cannot disagree with itself.
- **No generic base until a third aggregate earns it.** The shared mechanics are about
  fifteen lines, and two aggregates in one module is thin evidence. More importantly,
  `CONTEXT.md` Part 2 keeps **event-sourced vs persisted-with-events** an open per-context
  decision — `RefreshToken` is already the latter — and shipping `EventSourcedRepository[A]`
  now would quietly answer that question for four contexts nobody has asked it of.

**Tests fake the event store, not the repository.** A repository fake would leave the
identity map, the version arithmetic, the encoded payload keys and the newest-first scan
— everything this decision introduces — exercised by nothing. The in-memory store is bound
by three rules that are what make it faithful rather than merely convenient: it enforces
`expected_version` as equality against stream length, which is exactly the real semantics;
it runs the real `JsonEventCodec`, because the finders match stored JSON (`player_id` as
`str(uuid)`, `sport` as `sport.value`) and not Python attributes; and it preserves
insertion order, because the newest-wins rule reads the scan in reverse.

## Consequences

**Easier**

- The four use cases become testable with a stub, which is the point. Idempotent replay,
  the ownership guard, one-transaction completion and abandonment-as-a-no-op are behaviour
  that wants dozens of cheap tests and currently gets HTTP over SQLite.
- **`EventStreamVersionConflict` becomes reproducible in a unit test for the first time** —
  and that immediately surfaces that it has no HTTP mapping, so a genuine concurrent
  double-submit is a 500 today. The decision does not fix that; it makes it visible.
- The payload-key coupling has one home, so the silent-empty failure mode has one place
  to be guarded rather than being latent in every query written from now on.
- Version bookkeeping stops being a fact any caller knows, which removes a mistake that
  cannot be caught by review — `base_version` captured one line too late still compiles,
  still passes, and corrupts a transcript only under concurrency.

**Harder**

- **The dependency count barely moves**, and claiming otherwise would oversell this.
  `GetAssessment` 2 → 2, `AbandonAssessment` 4 → 3, `CreateAssessment` 5 → 4,
  `SubmitAnswer` 5 → 5. What changes is the body and what each dependency requires a
  caller to know, not the length of a constructor.
- **The adapter holds mutable per-request state.** It must be built per request from the
  session, exactly as `DomainEventStoreDep` is. An adapter accidentally made
  application-scoped would carry one request's versions into another and fail as spurious
  version conflicts under load — a failure that will not appear in development.
- `find_all_open` replays every assessment stream the player ever opened. That cost was
  always there, but it is now behind a method name, which makes it easier to call without
  thinking about. A projection is the answer when it stops being tens of streams.
- **The seam introduced is not the seam the tests cross.** Use-case tests exercise use
  case + repository + codec together. That is the right trade while the repository is new
  code carrying subtle rules, but it is a deliberate departure from testing at the
  interface.
- Two adapters share roughly fifteen near-identical lines, on purpose, until a third
  aggregate shows what actually varies.

**Neutral**

- `UserRepository` is untouched and keeps its name. `backend/CONTEXT.md` gains an
  **Aggregate repository** entry distinguishing it from the read-model kind, because after
  this change the codebase has two things called "repository" doing unrelated jobs and the
  one an agent finds first is the wrong template.
- Read-model repositories are a different thing and this record does not govern them.
  Whether the rating context eventually grows one — `player_ratings` is named as a
  projection in ADR-0017 — is a separate decision.
