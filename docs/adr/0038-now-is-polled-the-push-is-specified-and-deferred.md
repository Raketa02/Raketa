# ADR-0038 — Now is polled; the push is specified and deferred

- **Status:** Accepted
- **Date:** 2026-08-19
- **Superseded in part by:** [ADR-0054](0054-now-refreshes-when-asked-never-on-a-timer.md) — the
  30-second polling cadence below is withdrawn. Now refreshes only when it is asked: on arrival,
  on pull, on an action, and when a countdown reaches zero. Everything else here — the deferred
  frame protocol and the four forwards-compatibility fields — stands as written.
- **Scope note:** [ADR-0053](0053-the-phone-holds-no-rules-and-only-subtracts.md) leaves
  `nextTransition` and `serverTime` with **no reader and no prospect of one**. They survive on
  this ADR's forwards-compatibility argument alone; read that before deleting them as dead weight.

## Context

Now is a status surface, and `3-enrolled_match_engine_architecture.md` §2.5 specifies a
delivery channel for it: a WebSocket carrying `sync` / `patch` / `drop` / `ping` frames, with
monotonic acceptance and a version-carrying heartbeat so a dropped frame self-heals within
twenty seconds. Doc 5 affirms that design in full and calls the transport *"genuinely absent —
that is new build,"* placing it seventh of seven in the build order because
[Rule IV](../specs/now/3-enrolled_match_engine_architecture.md) — *the read is the truth; the
push is an optimisation* — means everything above it works without it.

Nothing in `backend/app/` speaks WebSocket or SSE. Redis is declared in `pyproject.toml` and
runs in `docker-compose-local.yml`, and no line of `backend/app/` imports it. On the client,
[ADR-0013](0013-player-app-runtime-architecture.md) has TanStack Query owning **all** server
state, with `focusManager` and `onlineManager` already wired to native `AppState`, and refuses
new dependencies "without a stated requirement."

The question this decision answers is not *which* transport. It is whether Now needs one.

### What actually changes on this screen, and what carries it

Classifying all 33 contexts by what drives the transition *into* them — using the predicates
verified in [`research/state-table.md`](../specs/now/research/state-table.md) — splits them
cleanly:

**Clock-driven.** `forming → formingLate` at `d.commit`. `heldSoft → heldStale` at
`maxHoldAge`. `full → ready` at `start − 15 min`. `replacement → rescue → rescueLate` at
`d.rescue` and `d.check`. Everything crossing into the played and needs-result group at
`matchEnd` and `matchEnd + 30 min`. And, since
[ADR-0034](0034-matches-is-a-record-and-keeps-no-history.md) classified them as receipts on
derivable conclusions, `cancelledIncomplete` and `cancelledCheckpoint`.

**Writer-driven.** Occupancy — somebody joins or leaves. Declarations — `clubCancelled`,
`courtLocked`, `clubExtended`, `weather`, `score`, `noShow`. Allocations — `inventoryLost`,
`releasedAt`.

§4.2 names the moments this screen exists for: *"the fifteen minutes before play, the minute
around a deadline."* **Every one of them is in the first list.** The kernel ships to the client
and §4.2's layer 2 re-derives locally, so the transitions that make the screen feel alive are
already free. A socket contributes nothing to them.

What a socket carries is the second list, and the honest statement of its value is: another
player's seat change, or a club's action, arrives in under a second instead of under thirty —
and only while the player happens to be looking. Matches fill over days; a session on this
screen lasts seconds.

### The moment that would justify it, and why it isn't there

The nearest candidate is two players racing for the last seat before a commit deadline: you tap
Join on a seat that filled twenty-five seconds ago. That is a mutation conflict, and its fix is
a clean taken-seat error on the server — needed whether or not a socket exists. A socket
narrows the race; it never closes it. `rescue` is urgent over hours, not seconds, and the
transition into it is clock-driven anyway.

### The costs, stated

A transport on both sides. A **deployment invariant** that the API cannot run more than one
instance until the connection registry is shared, whose failure mode reads as "the push is a
bit unreliable" — the worst possible symptom. A second source of server state living outside
TanStack Query, contradicting ADR-0013's single-owner rule. And §5.3's *drop every third push,
assert convergence* suite. Battery is a wash: a 20 s ping and a 30 s poll cost comparable radio
wake-ups.

## Decision

**We will deliver Now by polling. The push channel is specified and not built.**

- **`GET /now` is the only delivery mechanism in v1.** The client composes on open and on
  pull-to-refresh ([ADR-0032](0032-order-is-a-property-of-the-composed-screen.md)), and polls
  at **30 s while foregrounded and never while backgrounded** — `focusManager` and
  `onlineManager` already gate this, so it is configuration, not machinery.
- **The screen never admits staleness.** Rule IV holds as written, with the residual bounded at
  thirty seconds rather than assumed away. No card carries a stale marker; no banner appears.
- **`GET /now` carries `listVersion`, `cardVersion`, `serverTime` and `nextTransition` from day
  one**, though nothing reads them yet. Adding them later is a breaking change against phones
  that cannot be forced to update (ADR-0008's own consequence), which is the entire reason they
  ship now.
- **The projection is still built** — see
  [ADR-0039](0039-the-card-projection-rebuilds-from-the-record.md). §2.4's reasons 1 and 3 (the
  card is expensive relative to the state; cold start must be one indexed read) hold with no
  push at all. Only reason 2, *the push needs a diff*, was contingent on delivery.
- **The frame protocol is written down and deferred**, in
  [`docs/specs/now/deltas/live-delivery.md`](../specs/now/deltas/live-delivery.md): WebSocket
  (React Native ships `WebSocket` and does not ship `EventSource`, so SSE's usual advantage
  inverts here), authenticated at handshake and closed by the server at access-token expiry, a
  connection registry behind a port with an in-process adapter, `sync` applying content-only
  mid-view, and no live insert.
- **The trigger for building it is named:** a feature whose value depends on another player's
  action reaching a viewer in **under one second** — live scoring, in-match chat, a spectator
  view. Now is not that feature. Those would justify the channel on their own terms rather than
  inheriting it.

**A flag defaulting off is refused.** It pays the full build cost and the single-instance
invariant, and ships a path that rots untested.

## Consequences

**Easier**

- The largest category of state change — every clock threshold — is already instantaneous, with
  no transport, no reconnect, and no frame to lose. The screen is at its most alive exactly
  where §4.2 said it needed to be.
- No deployment invariant. The API scales horizontally from the first instance, because nothing
  holds per-player connection state in a process.
- ADR-0013's "TanStack Query owns all server state" survives without an exception. There is one
  source of server state and one cache.
- The whole of §5.3's push-convergence suite is not written, and the failure modes it covers do
  not exist.
- Rule IV stops being a claim and becomes the architecture. Doc 5 put delivery last to de-risk
  the feature; not building it de-risks it further, for the same reason.

**Harder**

- **Another player's action takes up to thirty seconds to appear.** A friend joining your match
  does not light the seat dot as it happens. This is real product value forgone, and the
  argument is that it is not worth a transport — not that it is worthless.
- **A club cancellation is wrong on screen for up to thirty seconds** while foregrounded, and
  until next open otherwise. `clubCancelled` and `inventoryLost` are the two facts no client can
  derive ([ADR-0034](0034-matches-is-a-record-and-keeps-no-history.md)), so this is the floor,
  not an implementation gap.
- **A backgrounded app learns nothing.** Push notifications are out of scope for the Now effort,
  so a cancellation at 22:00 for an 08:00 match is discovered on open. What makes this safe is
  §5.1's own row — *the card carries the whole story* — not a promise that it is fast.
- **Four fields ship with no reader.** `listVersion`, `cardVersion`, `serverTime` and
  `nextTransition` will look like dead weight to anyone reading the contract without this ADR,
  and `serverTime` in particular invites deletion. It is what keeps a countdown from trusting a
  wrong device clock (§5.1).
- **Polling cost scales with foregrounded players, not with events.** It is one indexed
  single-row read per player per 30 s, which is nothing at this size and is not free forever.
  The socket's cost scales the other way, which is the shape that eventually wins.

**Neutral**

- `3-enrolled_match_engine_architecture.md` §2.5 and doc 5's build-order row 7 are **amended by
  spec delta, never edited** — the rule
  [ADR-0036](0036-a-ui-document-is-final-on-the-screen-not-on-the-arithmetic.md) established.
  §2.5 is not wrong; it is a design for a channel we are not building yet, and it is kept intact
  so that building it later is reading rather than rediscovery.
- This revises the scope line settled while charting the Now map on 2026-08-18 (*"live WebSocket
  delivery in scope"*). The transport question is still **answered**, which is what the
  destination asked for; it is answered *no* for v1.
