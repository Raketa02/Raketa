# ADR-0076 — The schedule is a column, a wake is a look, and there is no list of boundaries

- **Status:** Accepted
- **Date:** 2026-08-21

## Context

Now has moments that must be noticed without anybody opening the app: a commitment deadline
passing, a court's soft hold lapsing, an offered seat's hour running out, a club's
reconciliation window closing. [#45](https://github.com/Raketa02/Raketa/issues/45) asked three
things — whether `next_wake_at` is a column, whether it rides the existing `EventWorker` or a
second one, and whether the acceptance grace belongs in a timekeeper at all.

**Nothing can be handed to a platform.** Research on
[#25](https://github.com/Raketa02/Raketa/issues/25) established that APNs, FCM and Expo offer no
server-side scheduling whatsoever, and Expo's `scheduleNotificationAsync` is on-device — it
cannot know about a vacancy the phone has not heard of. That makes the timer store load-bearing
rather than an implementation detail.

**What exists.** [ADR-0003](0003-transactional-outbox-for-event-delivery.md)'s transactional
outbox is polled by an embedded `EventWorker` — an asyncio task hosted by the API, a one-second
tick, `SELECT … FOR UPDATE SKIP LOCKED`. `3-enrolled_match_engine_architecture.md` §2.3 proposes
`next_wake_at` as a column over exactly that shape, and doc 5 finding 4 endorses it, adding that
*"it should probably be the same poller with a second query rather than a second process."*
[ADR-0038](0038-now-is-polled-the-push-is-specified-and-deferred.md) records Redis as **declared
in `pyproject.toml` and unused**; this is the first thing on the map that could have wanted it.
[ADR-0039](0039-the-card-projection-rebuilds-from-the-record.md) already set the precedent for
the shape of an answer here — one more handler on the existing worker, no new infrastructure.

**The ticket's own premise turned out to be the thing that was wrong.** Its boundary table is
introduced as *"fully enumerated — four tickets built it and nothing here needs discovering,
only deciding"*, and it is short by five: **T−12h** (Rule 8, the two-seat soft hold lapses),
**T−4h** (Rule 6, the three-seat hold lapses), **`joinCut`**, `start − 15 min` and `start`. The
first two **release a club's court**, which is the most consequential thing anything on this map
does to somebody outside it. They were not forgotten by a careless author: the candidate set is
a **function of the record** — `3` §2.1, *"a match on two paid seats wakes at T−12h; the same
match after a third payment wakes at T−4h instead"* — and `commit` is `min(club window, T−12h)`,
`rescue` is T−4h for doubles and T−6h for singles, and `joinCut` is `club.joinCut ?? 30`. A hand
-maintained table cannot track that, and a table that tries is a second ladder beside
[ADR-0040](0040-one-ladder-resolves-a-situation.md)'s one.

### Ruled out

- **Redis, or any second store.** It can disagree with the record, it must be rebuilt after a
  wipe, and it buys nothing here: the tightest window on the map is an hour, backstopped at
  twelve.
- **A second worker for the notification channel.** Considered for failure isolation, not for
  precision — no boundary on this map costs anybody anything if it fires a minute late.
- **A queue, a scheduler service, or a timer per match.** `3` §2.3's argument stands: the
  schedule *is* a column, so there is nothing to rebuild and no leader to elect.
- **Delaying the existing outbox with a `not_before` column.** One nullable column would buy the
  overnight hold for free, and it is wrong: [ADR-0052](0052-a-vacancy-is-offered-not-announced.md)'s
  rule is *"Finding is immediate; telling is scheduled"*, so holding the event back until 08:00
  would delay every consumer of it — the card projection included — in order to schedule one
  message. The outbox carries what happened; a delayed send is what we intend to say.

## Decision

**We will store each scheduled moment on the record whose moment it is, define the boundaries as
a function rather than a list, and make a wake mean *look at this*, never *do this*.**

### The schedule is a column

- **A match carries `next_wake_at` and `wake_reason`**, recomputed on **every** write, under a
  partial index over non-terminal rows. A restart loses nothing; a missed wake is simply late and
  then caught, because `next_wake_at <= now` is still true.
- **The notification channel carries its own scheduled sends**, in its own table with its own
  due-at column. Same shape, different record.
- **Redis stays unused.** This ticket is not the thing that turns it on.

### There is no list of boundaries

- **The timekeeper's input is the derivation kernel's `nextWakeAt(record, now)`** — the same
  function that decides what the card says. A boundary therefore cannot exist in one and be
  missing from the other, which is the defect that produced the five omissions.
- **#45's table is an illustration and is explicitly non-normative.** The ladder stays the only
  enumeration. Any future document that lists thresholds for the timekeeper is a second ladder
  and should be deleted rather than reconciled.
- **The comparison is strictly one-directional** — `>` on the remaining time, never `>=`.
  `3.1` warns that a match sitting exactly on T−12h with two paid seats otherwise flaps between
  `heldSoft` and `heldReleased` on every recomputation.

### A wake is a look, not an instruction

- **The handler re-derives from the record** and does whatever the kernel says now. It never acts
  on the stored reason: that reason was computed at a past write, and the match may have moved
  since — a seat paid, a club cancelled, a player left. A wake that executes a stale intention
  writes a lie into the record.
- **`wake_reason` is a label and half the idempotency key** — `{matchId}:{threshold}:{scheduledFor}`,
  which is what makes at-least-once scheduling safe with no exactly-once guarantee, no leader
  election and no distributed lock.
- **This is why lateness is affordable**: it changes *when you look*, never *what you find*.

### The offered seat splits at the seat, not at the channel

#45 filed all four of [ADR-0052](0052-a-vacancy-is-offered-not-announced.md)'s clocks as *"the
notification channel's, not a match's"*. They do not behave alike, and the line runs through them:

- **The match's** — the exclusive hold's **hour from delivery** and the **twelve-hour backstop**.
  Both change who may take a seat, and only whatever owns seats can promise *nobody else can take
  it*. Delivery-to-the-device is a fact the channel reports **in**, and that report is a write,
  so it re-arms the clock like any other write.
- **The channel's** — the **08:00 overnight hold** and the **ten-minute wave gaps**. Inside 24
  hours the offer is an open call that reserves nothing; these schedule *telling*.

Two consequences that are invisible if all four are filed together: **`joinCut` stops the
cascade**, so a match boundary must be able to silence the channel's pending sends; and **T−12h
is now three rules on one instant** — the commitment floor, Rule 8's hold lapse, and this ADR's
backstop — landing on two different records at once.

### One worker, three queries, one tick

The existing `EventWorker` gains two more indexed lookups on the tick it already runs: the
outbox, due match wakes, due sends. **No new interval and no second process.**

### What leaves the timekeeper

- **`proposal + 30 min`** — the acceptance grace is a **gate**, not a moment. Refusing a late
  counter is a rule applied to an action that turns up; the settlement of an unanswered
  acceptance changes only what the screen would say, and a read derives that. Nothing leaves the
  building at that instant — no money, no message, no seat, and under
  [ADR-0075](0075-the-second-table-is-unpaid-and-the-first-ships-in-english.md) no level movement
  to print.
- **`keepUntil`** — [#19](https://github.com/Raketa02/Raketa/issues/19) concluded that *"anything
  walking matches to retire them must read settlement"*. That obligation is **discharged, not
  inherited**: settling is itself a write, and every write recomputes the moment, so settlement
  sets the retire clock as a side effect of settling. `keepUntil` is not unschedulable — it is
  only unschedulable *in advance*. **No sweep and no second walker.**
- **The client's copy of the kernel** — already gone, and this ADR only records why the
  timekeeper does not bring it back. `3` §5 has the phone notice a passed threshold and re-derive
  locally; [ADR-0053](0053-the-phone-holds-no-rules-and-only-subtracts.md) refused it outright —
  *the phone holds no rules and no clock; its only power is subtracting* — and
  [ADR-0054](0054-now-refreshes-when-asked-never-on-a-timer.md) makes *a countdown reaching zero*
  a fetch rather than a flip. **The kernel stays server-side.**

  **The card's moment and the timekeeper's moment are different things, and must never be the
  same field.** ADR-0053 gives a card *the one moment it is about* — a confirm deadline, a start
  time, an offer expiry — and warns that pointing it at *"the next time this card changes"*
  drifts the number away from the words above it. `next_wake_at` is exactly that forbidden
  quantity: it is the earliest instant anything could differ, chosen by a `min()` over candidates
  the player is not being told about. It is **internal, and never serialised onto a card.**
  [ADR-0071](0071-two-fields-with-no-reader-are-not-forwards-compatibility.md) has already
  dropped `nextTransition` from the wire; this is the reason it must not come back wearing the
  timekeeper's name.

## Consequences

**Easier**

- A restart, a crash or a redeploy loses no schedule, and there is no second store to reconcile.
  *"What is due in the next hour, and why"* is a `SELECT`.
- The five omitted boundaries are already fixed, and were never really missing — they were
  missing from a list that should not have existed. The same is true of the next five.
- One implementation of the ladder, exercised by the ladder's own tests. A boundary added to the
  kernel is scheduled the day it is added, with no second edit anywhere.
- N workers can poll safely under `FOR UPDATE SKIP LOCKED` if this ever runs on more than one
  process, with no code change and no leader election.

**Harder**

- **A reviewer cannot check the timekeeper against a table**, because there deliberately is not
  one. The ladder's tests are the only place a missing boundary shows up, which raises what those
  tests owe.
- **The read path is now load-bearing for a property people will attribute to the timekeeper.**
  *A downed timekeeper delays the money and never the truth* is true **only because every read
  re-derives**. The day something serves a stored state without re-deriving, that property dies
  silently and nothing fails. This is the sentence to quote at whoever proposes caching a
  rendered card — and note that
  [ADR-0068](0068-now-is-one-request-and-the-caches-serve-the-screens-two-clocks.md) has already
  deleted the one cache that could have done it.
- **The honest cost of a downed timekeeper is a club's court.** T−12h and T−4h release a held
  court, and a court sitting held past its lapse is somebody else's Saturday. The failure is
  invisible to every player and visible only to the club — which is the one audience with no
  screen on this map. Monitoring is owed here, and it is owed on the query, not on the tick.
- **One worker means one queue of work.** A slow or stuck notification send delays a match wake
  behind it. That is the failure isolation given up by refusing a second process; it is
  affordable because a minute is free, and it stops being affordable the moment anything on this
  map needs a boundary honoured in seconds.
- **`next_wake_at` is a field that looks serialisable and is not.** It sits on the record beside
  things the card does carry, it is a plausible answer to *"when does this change?"*, and putting
  it on the wire would be a one-line change that quietly reverses ADR-0053. The rule has to be
  written on the column, not remembered.

**Neutral**

- Redis remains declared and unused. Whatever genuinely needs it first pays the whole setup cost,
  and this ADR is a reason it is not this.
- The notification channel gets a table before it gets a transport. That is the right order —
  [ADR-0052](0052-a-vacancy-is-offered-not-announced.md) specified the schedule long before
  anything could send.
