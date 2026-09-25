# ADR-0022 — What the kernel is not, and where a constant lives

- **Status:** Accepted
- **Date:** 2026-08-16
- **Its *No tenant data* narrowed by [ADR-0182](0182-a-club-is-a-place-players-search-and-its-account-signs-in-only-on-the-club-surface.md)** (2026-09-25): the Club context now exists and owns clubs, and the kernel still holds none. Its *no presentation* rule is **distinguished, not amended**, twice: a group's monogram letters are content cut from content ([ADR-0183](0183-a-group-is-a-crowd-at-a-home-club-and-its-link-never-changes.md) §5), and an email has no client to render it ([ADR-0186](0186-email-goes-through-a-port-and-a-purged-queue.md) §4).

> **Note — the 2026-08-25 reset.** It cites **ADR-0011** (the club design system), **ADR-0023** (money in integer grosze) and **ADR-0026** (the matchmaking snapshot contract), all removed in the 2026-08-25 reset. The kernel's money module went with ADR-0023; the two questions this ADR asks of a candidate constant are unchanged, and are what the surviving kernel is held to. See the [ADR index](README.md#the-2026-08-25-reset--why-the-sequence-has-gaps). This ADR's body is left as written: an accepted ADR is immutable, and the reason a past decision looked right is itself information.

## Context

[ADR-0015](0015-engines-as-a-pure-versioned-layer.md) established a pure engines layer and a
dependency-free shared kernel, enforced by `import-linter`. The kernel specification document
([ADR-0021](0021-kernel-in-backend-clients-derive-by-comparison.md) describes where it comes
from) proposes filling that kernel with fifteen modules. Read against this repository, five of
them carry decisions that belong somewhere else, and the constants section contradicts both
itself and ADR-0015.

**`records` — the `Match` shape.** The documents call this *"the one genuinely contested
boundary"* and decide in favour, guarded by a lint rule forbidding functions in that
directory. Their argument is the hub problem: put `Match` in one engine and the other nine
import it. Here the cost is higher. It would put an aggregate shape in the ring ADR-0015
defines as *the thing every context reads verbatim and none may redefine*, so the Matches
context would not own its own aggregate. It would silently answer the questions
[`CONTEXT.md`](../../CONTEXT.md) deliberately leaves open — *"Is a Booking owned by the Court,
the Club, or standing alone? Is availability a projection over bookings, or its own stored
concept? What is the tenancy spine?"* And their `Match` is a flat twenty-five-field snapshot,
which is a read model rather than an aggregate; this repo already separates those
([ADR-0018](0018-aggregate-repositories-over-the-event-store.md)).

Python offers a third option the documents could not have. **Structural `Protocol`s** let each
engine declare the narrow set of fields *it* reads — protection needs seats, start,
`committed_at`; pricing needs club, sport, share. No hub, no kernel-owned aggregate, and a
half-built draft object satisfies the same Protocol a saved match does, which is the Null
Object the overlap engine needs, for free.

**`catalogue` — clubs, courts and rates as data.** `Sport`/`SportSpec` is already in the
kernel and correctly so: a closed enum, extended by a release rather than a row. Clubs, courts
and rate cards are the opposite in every respect — tenant data, per club, effective-dated,
edited by club staff, destined for contexts `CONTEXT.md` already names. The documents' own
`< 12 kB` data budget with *"a second city doubles it"* is the tell.

**`level` — the scale.** It collides head-on with `backend/app/engines/racketskill/core.py`,
which already owns `SCALE_MIN`, `SCALE_MAX`, `SkillEstimate`, `combine_sigma`,
`confidence_percent` and the bands — and which ADR-0015 explicitly made that home, *"so
onboarding and the later match-update engine cannot develop two ideas of what σ means."*

**`random` — a PRNG.** Three consumers, none of which survives. Occupancy generation is a
fixture. The rescue tie-break is one engine's concern. And the ledger reference should not be
hashed at all: it already contains a unique match id, while a 32-bit FNV-1a reaches 50%
collision probability at roughly 77,000 references — against a documented unique constraint on
`ref`, which turns a collision into a failed payment write.

**`format` — Polish money strings and English sentences.** Its consumers here are two
TypeScript clients with separate design systems (**ADR-0011** *(removed)*,
[ADR-0012](0012-player-app-design-system.md)). A preformatted string can only be one rendering,
and one price needs three: struck-through beside its discounted twin, bare inside a tile whose
header carries the unit, and plain on a row.

**The constants.** The two source documents contradict each other outright: one puts
`RESCUE_LAW` in the rescue engine with its price fraction as a literal `0.5`, the other puts it
in the kernel registry with the fraction derived from the refund table. ADR-0015 gives a third
position — *"Constants travel with the version as a frozen dataclass."* The framing *"ninety
constants, one declaration each"* conceals that they are not one kind of thing.

The alternatives considered:

- **Port the fifteen modules as specified.** Fastest, and it buries four unmade domain
  decisions in the innermost ring of the system.
- **Put everything shared anywhere in the kernel.** What "ninety constants" amounts to in
  practice, and it makes retuning one engine a kernel change.
- **Decide each module and each constant by one question:** is this *vocabulary*, or is it an
  *answer*?

## Decision

We will keep the kernel to **vocabulary**, and settle every borderline case with the two
questions the source documents themselves supply: *does it answer a question about the
domain?* — then it is not the kernel. *Would a second implementation of it be a defect?* —
then it is.

The kernel holds identity types, invariants and exhaustiveness, money, time, intervals,
results, ordering, the decision envelope, the `Sport` registry, and a small registry of
calendar facts. Nine modules, roughly nine hundred lines.

- **No aggregate shapes.** Engines declare narrow input `Protocol`s naming only the fields
  they read; the owning context publishes a snapshot that satisfies them. Adding a field to a
  match is invisible to every engine that does not read it.
- **No tenant data.** `Sport`/`SportSpec` stays. Clubs, courts, rates and categories are owned
  by their contexts and reach an engine through a port that engine declares, per ADR-0015's
  one-`Protocol`-per-engine rule. The seeded nine-club world is a fixture adapter. The
  invariant that a club/sport/category has exactly one effective multiplier becomes a
  **validation at club configuration**, where it can stop a real club from breaking it.
- **No presentation.** The kernel emits values and stable machine codes, never display text.
  `Unavailable` crosses the wire as `{kind, …payload}`, and each client owns its own copy in
  its own language — which is also the only way *"show nothing"* stays a client decision.
- **No engine hypotheses.** See the four homes below.
- **No PRNG.** `kernel/random` is not built. Ledger references derive structurally —
  `PAY-{match_id}-{seat_index}` — unique by construction, needing no collision test and
  readable in a support ticket.
- **The scale stays where ADR-0015 put it.** `racketskill/core.py` owns the level scale, σ,
  the bands and the confidence transform. If a second engine needs `Level` and `Sigma` as
  vocabulary, only the scalar types and the scale bounds are promoted to the kernel and
  `racketskill/core` imports them — a relocation, behaviour-identical, no number touched.

**A constant has one of four homes,** decided by whether it is a hypothesis:

| Kind | Home | Examples |
| --- | --- | --- |
| Calendar and marketplace facts, several readers, not tunable | the kernel registry | `SLOT_MINUTES`, `WEEK_START`, `OPEN`, `LEAD_TIME_MIN` |
| Admitted hypotheses owned by one engine version | that version's frozen constants, hashed into its output | gap and spread coefficients, term weights, clamps, confidence bands |
| Marketplace law — frozen, unreachable from policy resolution | with its engine | `RESCUE_LAW`, whose price fraction is **derived** from the refund table, never typed |
| A quantity two engines share | with the engine that *defines* it; the other imports it | the K-factor, in `racketskill/core` |

**Errors and unavailability use different mechanisms,** split on the fence `import-linter`
already draws:

- Inside the kernel and engines: no exceptions for domain conditions. `Result[T]` is returned;
  `invariant()` is raised only for a broken precondition, which means a bug shipped.
- Outside: modules and adapters raise as they do today, and translate an `Unavailable` into a
  response.
- Exhaustiveness by `typing.assert_never`, so a new `Unavailable` kind or lifecycle state
  fails typechecking at every branch that does not handle it.

**Purity is enforced, not assumed.** Five checks, three of which close a hole that exists
today:

- **`app.shared` joins both `.importlinter` forbidden lists.** It was on neither, so a kernel
  or engine module could import `SystemClock` or `new_uuid` with CI green — the exact hole
  ADR-0015 rejected an alternative for leaving open.
- **The `Clock` Protocol moves into the kernel; `SystemClock` moves to
  `app/infrastructure/`.** They currently share a module, so importing the abstraction drags
  the implementation into scope.
- A test asserts every kernel and engine top-level import is in `sys.stdlib_module_names`.
- An AST test rejects `datetime.now`, `date.today`, `time.time`, `random.*` and `uuid4` —
  needed because `import-linter` works at module granularity, and `datetime` is legal here
  while `datetime.now()` is not.
- **Fixed-arity collections are tuple types, never lists.** mypy has no
  `noUncheckedIndexedAccess`, so the structural fix the documents offer as defence in depth is
  here the only defence against the `NaN` hazard they describe.

`verify_kernel()` runs at the FastAPI lifespan and in every test session.

## Consequences

**Easier**

- Four domain decisions stay open until the context that owns them is designed, instead of
  being answered by a type in the innermost ring.
- An engine's input `Protocol` names exactly what it reads, which is the clearest available
  documentation of coupling — and it makes a draft object satisfy it for free.
- Retuning an engine is an engine change, not a kernel change, and it shows in that engine's
  version hash rather than rippling through a shared registry.
- The kernel is small enough to read in one sitting.

**Harder**

- **More `Protocol`s to write and keep aligned.** Every engine declares its own input shape,
  so renaming a snapshot field touches each Protocol that names it. The compiler finds them,
  but they are files.
- **No single place to read "all ninety constants."** Four homes means four places, and the
  registry that made a duplicate-literal lint cheap now guards a dozen values instead of
  ninety.
- **The two clients duplicate formatting,** deliberately, and it can drift. Mitigated by
  pinning the rules in a shared design doc and by ADR-0021's contract suite — not eliminated.
- **Forbidding `app.shared` moves the `Clock` import in roughly twenty call sites** across
  `auth`, `rating`, `users` and `bootstrap`.
- **Two of the source specification documents are now wrong in places.** A reader who finds
  them needs this record to know which way each disagreement resolved.

**Neutral**

- The documents' Wave 0–5 build order no longer applies as written; it assumed a kernel
  answering questions this record moves out of it.

## Applications

Cases settled by the two questions above, recorded here so the next borderline one has
precedent rather than a fresh argument. **The record stays `Accepted`** — these are the
decision being applied, not revised.

**Half away from zero, 2026-08-17** ([#88](https://github.com/RobertConstantin02/rakieta/issues/88)).
The rounding rule had reached three implementations in two packages: private in
`kernel/money.py` over a `Fraction`, in `engines/pairing/core.py` over a `float`, and in
`engines/matchfit/core.py` over a `Ratio`. Both questions pointed the same way — it answers
nothing about the domain, and a second implementation of it is a defect — so it was made
public in the kernel and both engines now delegate. **A relocation, behaviour-identical, no
number touched**, which is the same move this record reserves for `Level` and `Sigma`.

The argument against was real enough to be worth writing down: **ADR-0026** *(removed)*
fences the two engines from each other so that neither's arithmetic moves when the other's
version moves, and a shared rule is shared. It does not apply here. That fence is
engine↔engine, and both engines already stand on the kernel, which is what a kernel is for.
The thing it protects against is a *retune* propagating across lineages — and this rule
carries no version and no tuning knob. It is arithmetic, not a hypothesis. The test that
separates the two cases is the one this record already states: **would a second
implementation be a defect?** For a rounding rule, yes; for a gap coefficient, no, which is
exactly why those stay in their engine version's frozen constants.

What each engine kept is its own *crossing* into the rule's domain — `pairing/core` converts
a float, `matchfit/core` scales a ratio by a hundred and guards its range — because those
are engine vocabulary and the rounding underneath is not.
- Nothing here decides how the kernel's money or time types are *shaped* — see
  **ADR-0023** *(removed)* and
  [ADR-0024](0024-instant-as-aware-datetime-minute-coordinates.md).
