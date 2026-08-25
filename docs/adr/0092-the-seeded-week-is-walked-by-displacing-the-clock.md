# ADR-0092 — The seeded week is walked by displacing the clock, and only a laptop may displace it

- **Status:** Accepted
- **Date:** 2026-08-24
- **Discharges:** [`Raketa02/Raketa#134`](https://github.com/Raketa02/Raketa/issues/134)

## Context

`backend/app/seeds/courts.py` anchors every seeded window to `SEED_MONDAY` — Monday 7
September 2026, written out rather than computed, and deliberately:

> **The window is a fixed absolute instant, not an offset from now.** A seed run is
> idempotent, and *"next Tuesday at 18:00"* computed at run time is a different Tuesday
> tomorrow — so a second run would claim a second court and the run that creates nothing
> could never happen.

That reasoning is right and this decision does not argue with it. What it argues with is
the consequence: **the week is walkable only from a clock inside it, and the product had
no such clock.** `build_clock()` answered `SystemClock` and there was no override
anywhere — not a setting, not a header, not a dependency the API exposed.

Two things followed, and they are different sizes.

**The post-play conversation was unreachable over HTTP on any day.** `needsResult` and
`confirmResult` are true only between Tuesday 21:00 and Wednesday 21:00 on the seeded
week. Before the week both read `full`; after it they read `playedNoScore` and
`completed`. So the two screens
[ADR-0048](0048-silence-confirms-a-result-and-disagreement-carries-a-score.md) and
[ADR-0060](0060-a-result-is-entered-on-a-route-and-the-card-names-the-act.md) specify
could not be met by signing in, on any date, ever.

**The week expires.** Once the wall clock walks past 13 September 2026, every seeded
address's Now is at most one shelf of new clubs: every match is in the past, so no match
is a candidate, no offer is live and the strip has let go of them. The seed's own name
checks pass throughout, because each asks `kernel.situation` at its own scenario's
instant — *the data is right and there is no day on which somebody can see it.*

What is **not** a problem, and is not addressed here: the week is **staged**. Each
scenario names the instant its claim is asserted at, and no single instant shows all
thirteen matches in the states they are named for — a match played on Tuesday evening is
not still forming on Friday. That is the catalog's design.

[`Raketa02/Raketa#96`](https://github.com/Raketa02/Raketa/issues/96) had already gone as
far as a test can: `backend/tests/api/test_demo_week.py` signs in over HTTP and then
composes at the week's own instants **through the composition root**, with the reason
written down. It proves the data. It cannot prove a developer's experience, and a
developer's experience was the thing that was missing.

Three shapes were considered and they are not equivalent.

**An anchor computed once per seed run and stored**, so the week is *the week after the
database was made*. Idempotence survives — the anchor is read back rather than
recomputed — and every fixed instant in the four catalogs becomes an offset. It loses
*the same run twice is the same state twice* across two databases, and it does not reach
the post-play conversation at all: the two states are still a one-day window inside a
week that a wall clock passes through once.

**Re-seeding, with the anchor moved by hand when it goes stale.** Cheapest, and it makes
the demo week something a person has to maintain. Reaches neither problem.

**A clock the process can be moved off.** The largest, and the only one that reaches the
first problem. The surface is genuinely one function, because
[ADR-0015](0015-engines-as-a-pure-versioned-layer.md)'s first purity rule already did the
work: no module reads ambient time, every engine takes `now` as an input, and every use
case takes a `Clock`. The cost is stated in the issue and is real — *a clock a request
can move is a clock a test can forget to put back*.

The constraint this had to be designed against is
[`docs/environments.md`](../environments.md)'s first rule: **the environment may select
configuration defaults; it may never select behaviour a domain test could observe.**

## Decision

**We will add a second `Clock` adapter that displaces the host's clock, select it by
configuration rather than by environment, and refuse that configuration anywhere but
`local`.**

**The environment does not select it; it only refuses it.** `CLOCK_SCRUBBABLE` is
`False` in all four environments, including `local`. What an environment decides is
whether somebody may turn it on — a boot refusal, which is rule 2 of the environments
document and not rule 1. The permission is a table written out per environment,
`CLOCK_MAY_BE_SCRUBBED`, whose completeness is checked at import exactly as
`app/seeds/guard.py`'s `SEEDABLE` is: the day a fifth environment is named is the day
this file stops covering `Environment` and refuses to import. `development` and
`staging` are `False` and not *not yet* — a clock somebody can move is a clock a second
person is reading, and on a shared environment a demo would be an outage on somebody
else's screen with no error anywhere.

**It displaces time; it does not stop it.** `ScrubbableClock.now()` is the base clock
plus a signed whole number of seconds. Scrub to Tuesday 21:30 and it is Tuesday 21:30,
and a minute later it is 21:31. Every deadline in the system stays a deadline: a seat
claim's five minutes lapse while somebody watches, `next_wake_at` comes due, the
timekeeper takes the wake. A clock frozen at an instant would show the seeded week and
animate none of it — and the states worth looking at are exactly the ones a boundary is
about to end.

**One clock per process, and the delivery worker is on it too.** `build_clock(settings)`
is the single answer to *what time does this deployment think it is*: `SystemClock` when
the setting is off, and the process's one `ScrubbableClock` when it is on. The lifespan
hands the same object to the event-delivery worker. A tick on the wall while the requests
it feeds are on a scrubbed week is a week in which no deadline ever arrives.

**A scrub is absolute and outlives the request that made it.** `POST /_clock {"at": …}`
puts the clock at an instant measured from the host's, never from where the last scrub
left it; `GET` reports where it is standing and where the host is; `DELETE` gives the
host's clock back. The route is mounted on the application beside `/health`, by
`create_app`, and **only when the setting is on** — never on either surface router, so
neither client generates a type for it and `make gen-api` has nothing to say. The path is
`/_clock` rather than `/api/v1/clock`, because the `/api/v1` prefix rule is about the
product's routes and this is not one.

**`CLOCK_SCRUB_TO` names where the clock starts**, so a stack brought up against a seeded
database lands inside the seeded week rather than three weeks past it. It is refused
without `CLOCK_SCRUBBABLE`, and refused if it carries no UTC offset.

**Nothing above the composition root can tell the two adapters apart**, and no route
imports either. The router is handed something satisfying a `MovableClock` protocol
declared where it is used, so `tests/unit/test_system_clock.py`'s walk — *only a
composition root may import the wall clock* — stays true as written.

**The reset is a named function, not a convention.** `forget_the_movable_clock()` drops
the process's clock, and `backend/tests/conftest.py` calls it after **every** test,
autouse. The issue's warning is answered structurally rather than by asking each test to
remember.

We will **not**: give a request its own clock or accept a per-request `X-Raketa-Now`
header (it would need the player app taught to send one, and the two clients are separate
deployables); freeze rather than displace; or move `SEED_MONDAY`.

## Consequences

**The two post-play screens are reachable by signing in**, which is the whole of what was
asked for. `backend/tests/api/test_scrub.py` asserts it the way the issue described the
gap: sign in over HTTP, scrub over HTTP, read the result route over HTTP, and find
`needsResult` and `confirmResult` — with a control case asserting the same two matches say
something else on the wall clock, so the test cannot pass by the week having been quietly
re-anchored.

**The week no longer expires for a developer.** It still expires for the wall clock, and
that is unchanged and deliberate: `SEED_MONDAY` stays fixed, seed runs stay idempotent,
and the way to stand on the week in 2027 is the way to stand on it today.

**A clock a request can move is a clock a test can forget to put back.** The autouse
reset is the mitigation and it is not free of assumption: it protects tests that go
through the fixture and would not protect a process that constructed one some other way.
Nothing does today, and the settings default means CI never builds one at all.

**The new-arrivals cache is on the same clock, and a backwards scrub outlives its TTL.**
Entries are stamped when written, so after a scrub into the past an entry stamped in the
future never expires until the clock returns. It is a cache of *who is new*, it expires
and never invalidates, and the wrong answer it can give is a slightly stale shelf on a
laptop. Named here rather than fixed.

**Two reads inside one command can now disagree in a way they could not before** — if a
scrub lands between them. ADR-0015's *one read per command, captured once* already
forbids the shape that would notice, and reaching it takes an HTTP request timed into a
microsecond gap on a laptop. It is a real widening of a guarantee, stated rather than
denied.

**A seed run driven from a scrubbed process registers its timeless aggregates at that
process's instant.** An account is registered whenever it is registered and no catalog
claim reads a registration instant, so nothing checks differently — but *the day the seed
ran* is now a configurable day.

**`build_clock` takes the settings**, which is one more argument at four call sites and
brings it into line with every other factory in the composition root: an adapter is a
function of a session and configuration.

**The seeded week is still staged**, and one instant still does not show all thirteen
matches in the states they are named for. Walking it is now possible; it is still
walking, and `tests/api/test_demo_week.py` continues to compose at each scenario's own
instant because that is what asserting thirteen different claims requires.

**A protocol is declared twice.** `MovableClock` in `app/api/scrub.py` restates what
`ScrubbableClock` offers, so that a presentation module never imports an adapter. Two
declarations can drift; the drift is a `mypy` failure at the one call site that connects
them, which is the trade taken.
