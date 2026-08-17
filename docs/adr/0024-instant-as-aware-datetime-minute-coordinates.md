# ADR-0024 — An Instant is an aware datetime; engines compute in integer minute coordinates

- **Status:** Accepted
- **Date:** 2026-08-16

## Context

The source specification documents define `Instant` as branded epoch **milliseconds**, and
argue for it against JavaScript's `Date`: mutable, allocation-heavy, inconsistently
serialised. *"Do not store an `Instant` as a `Date`."*

None of that is true of Python's `datetime`, and this repository already has exactly one time
representation. `app/shared/clock.py` returns `datetime.now(timezone.utc)`; every domain event
carries `occurred_at: datetime`; Postgres stores `timestamptz`. Adopting epoch-milliseconds
would introduce a second representation and a conversion at four boundaries — the clock, the
event store, the database and the API.

Their genuinely portable insight is a different one, and it survives intact: **the engines
compute in (day offset, minute of day) because that makes interval arithmetic integer and
timezone-free.** That is why the most-called predicate in the system is a handful of integer
comparisons, and it has nothing to do with how the anchor instant is represented.

The other non-negotiable is that engines cannot read the clock. That is
[ADR-0015](0015-engines-as-a-pure-versioned-layer.md)'s first purity rule and the documents'
single hardest one, and everything rests on it: scrubbing the clock forwards and backwards,
determinism, and every test in the system.

One thing the documents get right and that is *cheaper* here than there: DST. Poland observes
it, a day in March has twenty-three hours and a day in October has twenty-five, and 02:00–03:00
occurs twice. Their worst case is a deadline computed by subtracting from a wall-clock hour —
`T − 12h` meaning twelve elapsed hours — which commits four people who have already paid an
hour early or late, twice a year. Python's `zoneinfo` and `fold` are stdlib; theirs was a rule
and a warning.

The alternatives considered:

- **Epoch milliseconds, as specified.** Faithful to the documents, and it invents a second time
  representation inside a codebase that already has one.
- **`datetime` everywhere, including booking arithmetic.** Loses the integer-minute property
  that makes availability cheap, and pulls DST traps into the hot path.
- **Aware `datetime` for instants, integers for in-day coordinates, one conversion between
  them.**

## Decision

- **An `Instant` is a timezone-aware `datetime` in UTC** — what the clock already returns, what
  events already carry, and what the database already stores.
- **`MinuteOfDay`, `DayOffset` and `Minutes` are integers,** and engines compute in them. The
  hot path never touches an `Instant`.
- **`slot_start(anchor, day, minute, tz)` is the single conversion** from in-day coordinates to
  an instant. There is exactly one, and it uses `zoneinfo`.
- **The `Clock` Protocol lives in the kernel; `SystemClock` moves to `app/infrastructure/`.**
  They currently share a module, so importing the abstraction drags the implementation into
  scope.
- **`now` is a parameter, never read.** One clock read per command, captured once and passed to
  every engine that command calls — two reads inside one command can disagree, and at least one
  documented rule depends on them not doing so.
- **DST is handled explicitly**, tested against `Europe/Warsaw`:
  - A **nonexistent** local time returns a typed `Unavailable`. Python does not raise here;
    detection is the round-trip idiom — construct it, convert to UTC and back, compare — and
    that must be written down or it will be omitted.
  - An **ambiguous** local time resolves to the earlier offset, always, via `fold=0`.
  - **Elapsed-hour rules are computed as elapsed time,** never as wall-clock subtraction.
    `T − 12h` means twelve elapsed hours.
- **`DayOffset` is never persisted and never crosses the wire.** It is anchor-relative, and an
  anchor-relative day in stored data is a landmine. In-memory coordinate only.

## Consequences

**Easier**

- One time representation across the clock, the event store, the database and the API. No
  conversion at four boundaries and no second notion of "when".
- DST is cheaper than the documents assume: `zoneinfo` and `fold` are stdlib, so the four
  boundary behaviours are library calls rather than hand-rolled arithmetic.
- Booking arithmetic stays integer, so availability keeps the cost the documents measured.
- The clock is injectable, so scrubbing forwards and backwards works and every determinism
  property is testable.

**Harder**

- **The specification documents say the opposite,** in several places and with worked
  reasoning. A reader who finds them needs this record to know why.
- **`datetime` allocates,** so any future path doing instant arithmetic in a loop needs
  watching. None does today, because the minute coordinates keep it off the hot path.
- **The nonexistent-local-time check is manual.** Python's silence is a footgun, and the
  failure it hides is a slot the grid offers that does not exist.
- **Moving the `Clock` Protocol touches roughly twenty call sites** across `auth`, `rating`,
  `users` and `bootstrap`. The Protocol is structural, so no behaviour moves — but it is a
  real diff in modules nobody is otherwise changing.

**Neutral**

- The four `Europe/Warsaw` boundary tests get written even though the demo week does not cross
  a boundary. They are four cases, and they are the difference between a kernel and a demo.
