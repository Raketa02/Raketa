# The Enrolled Match Engine Architecture

*An analysis of the proposed three-engine design, and the architecture I would build instead — with the reasoning for every difference.*

---
---

# PART 0 — YOUR PROPOSAL, ASSESSED

## 0.1 What you proposed

| # | Engine | Responsibility |
|---|---|---|
| **1** | Time tracker | Tracks time since enrolment · applies the hold-ladder and commitment rules · emits events when a rule stops holding |
| **2** | State machine | Receives those events · re-evaluates the match · rebuilds the player's enrolled-match list · publishes it reactively |
| **3** | Player-event tracker | Catches player actions — leave, invite, accept — applies them to the match · informs engine 2 |

## 0.2 What is right about it, and it is most of it

**The separation of *what happened* from *what it means* is correct.** Engine 3's job — turning a tap into a domain change — is genuinely different from engine 2's job — turning a domain change into something a screen can render. Products that merge these end up with business rules inside view code.

**Making the list a published artefact rather than a query is correct**, and it is the decision that makes the feature feel the way it should. A client that has to ask *"has anything changed?"* is a client that is either wrong or wasteful, and on the most-used screen in the app that is not a trade worth making.

**Recognising that the clock is a first-class source of change is correct**, and it is the thing most teams get wrong. Six of this feature's transitions fire with nobody doing anything, and four of those six are bad news. An architecture that only reacts to user actions cannot deliver this product.

**Separating the card-building responsibility is correct.** The thirty-three states each have a tag, a tone, a context line, two facets and up to five lines. That is a real amount of work and it deserves its own component.

## 0.3 Three problems, in order of severity

### Problem 1 — Two engines write to the same match

Engine 1 *"generates events that would change the enrolled match state."* Engine 3 *"makes the corresponding changes in the enrolled match."* **Both write.**

Consider Saturday 14:29:58. The rescue window opens at 14:30. A player taps Leave.

```
        t=14:29:58   Engine 3 reads the match   (committedAt set, no vacancy)
        t=14:29:59   Engine 1 reads the match   (committedAt set, no vacancy)
        t=14:30:00   Engine 1 writes            → "rescue window opened"
        t=14:30:00   Engine 3 writes            → vacated = 'ola'
```

Depending on interleaving you get: a rescue notification for a match with no vacancy, a vacancy that never triggers the cascade, or a lost write. **And this race is not rare** — it is concentrated at exactly the four moments the product is about, because those are the moments people act.

**Two writers on one aggregate is the single most expensive mistake available in this design**, because the failures are intermittent, they cluster at the deadline, and they corrupt the one fact that must never be wrong.

### Problem 2 — "Tracking time" is the wrong verb

*"One engine in charge to track the time since the player joined"* implies the engine **holds state about where the match is in its life.**

Every earlier document in this system argues the opposite:

> *"There are no timers, no intervals, and no scheduled jobs — the app recomputes on every render, so moving the clock backwards is as valid as moving it forwards."*

> *"The absence of caching is a design property, not an oversight."*

**A tracker introduces a second source of truth.** Now the match record says one thing and the tracker says another, and they can disagree — after a restart, after a deploy, after a message is dropped, after a clock adjustment. Reconciling two sources of truth about money and commitment is not a bug class you want.

**But the intuition behind it is right and important.** Nobody is looking at the match at T−12h. Something has to notice. The fix is not to remove that something — it is to give it a much smaller job:

> **A scheduler that decides *when to look* is safe. A tracker that decides *what is true* is not.**

The timekeeper should hold no state that could not be thrown away and rebuilt from the match records in one query.

### Problem 3 — Rebuilding the whole list

*"Builds the updated list of enrolled matches that will be automatically published."*

One match changes. The player has three. Rebuilding and shipping all three means:

- three cards re-render when one changed
- the horizontal strip may lose its scroll position
- the entrance animation replays on cards that did not change
- bandwidth scales with matches-per-player, not with what happened

**And a subtler one:** if two matches change within a second, two full-list pushes race, and the second may carry a staler view of the first match.

The list is **sorted by start time, which never changes.** A state change therefore never reorders the strip. That property makes per-card patching safe and trivially correct, and it should be used.

## 0.4 The correction that simplifies everything

**Your engines 1 and 3 are the same engine.**

Both of them do the same thing: they produce a *reason to re-evaluate this match*, and they cause a change to be written. One's reason is a clock threshold; the other's is a person tapping. Neither needs its own writer, its own locking, or its own concurrency story.

```
   BEFORE                                AFTER

   Engine 1 ──writes──┐                  Timekeeper ──command──┐
                      ├──▶ Match                               ├──▶ ONE writer ──▶ Match
   Engine 3 ──writes──┘                  Player action ─command┘
```

That single change removes Problem 1 entirely, and it makes the timekeeper's job small enough that Problem 2 dissolves with it.

---
---

# PART 1 — THE ARCHITECTURE

## 1.1 The five components

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   ┌────────────────┐                    ┌──────────────────────┐             │
│   │  PLAYER ACTION │                    │     TIMEKEEPER       │             │
│   │  leave·invite  │                    │  "which matches are  │             │
│   │  accept·pay    │                    │   due a look?"       │             │
│   └───────┬────────┘                    └──────────┬───────────┘             │
│           │                                        │                         │
│           │   Command                    Command   │                         │
│           └────────────────┬───────────────────────┘                         │
│                            ▼                                                 │
│              ╔═════════════════════════════╗                                 │
│              ║   ② MATCH COMMAND HANDLER   ║   ◀── THE ONLY WRITER           │
│              ║   load · evaluate · apply   ║       optimistic concurrency     │
│              ╚══════════════╤══════════════╝                                 │
│                             │                                                │
│                    ┌────────▼────────┐                                       │
│                    │ ① DERIVATION    │  pure · shared with the client        │
│                    │    KERNEL       │  the §1.4 ladder · the 12+7 rules     │
│                    └────────┬────────┘                                       │
│                             │                                                │
│                    Match + DomainEvents                                      │
│                             │                                                │
│                       ┌─────▼──────┐                                         │
│                       │  OUTBOX    │  same transaction as the write          │
│                       └─────┬──────┘                                         │
│                             │                                                │
│         ┌───────────────────┼───────────────────┬────────────────┐           │
│         ▼                   ▼                   ▼                ▼           │
│  ┌─────────────┐   ┌────────────────┐   ┌────────────┐   ┌────────────┐     │
│  │④ PROJECTION │   │ NOTIFICATIONS  │   │ RESCUE     │   │ ANALYTICS  │     │
│  │  card list  │   │  push · email  │   │ SAGA       │   │            │     │
│  │  per player │   └────────────────┘   └────────────┘   └────────────┘     │
│  └──────┬──────┘                                                             │
│         │                                                                    │
│  ┌──────▼──────┐                                                             │
│  │⑤ DELIVERY   │  WebSocket · per-card patch · monotonic version             │
│  └──────┬──────┘                                                             │
└─────────┼────────────────────────────────────────────────────────────────────┘
          ▼
      ┌────────────────────────────────────────────┐
      │  CLIENT — renders the card, derives between │
      │  pushes using the SAME kernel               │
      └────────────────────────────────────────────┘
```

## 1.2 How your three map onto these five

| Your engine | Becomes |
|---|---|
| **1** Time tracker | **Timekeeper** (when to look) + **Derivation Kernel** (what is true) + **Command Handler** (writing the crossing) |
| **2** State machine | **Derivation Kernel** (the state) + **Projection** (the card) + **Delivery** (the push) |
| **3** Player events | **Command Handler** — the same one the timekeeper uses |

**Nothing you identified is dropped.** The responsibilities are redistributed so that exactly one component writes and exactly one component decides.

## 1.3 The governing rules

| # | Rule | Consequence |
|---|---|---|
| **I** | **One writer.** Every change goes through the Match Command Handler | No races, one lock, one concurrency story |
| **II** | **Derive, never track.** No component stores the current state | Nothing can go stale; nothing needs reconciling |
| **III** | **Decide purely, act at the edge.** `evaluate` is pure; `apply` writes | Client, server and tests call the same function |
| **IV** | **The push is an optimization; the read is the truth.** A lost push must never produce a wrong screen | Every failure mode degrades to *slightly late*, never *wrong* |
| **V** | **Idempotent by identity.** Every command carries a stable id | At-least-once delivery is enough |
| **VI** | **Patch cards, never lists.** Sorted by start, which never changes | One card changes, one card re-renders |

**Rule IV is the trust property.** Everything else is engineering; this one is the product promise. It means that when the WebSocket dies on a train, the notification is dropped by the OS, and the projection is six seconds behind — a player who opens the app still sees the truth, because opening the app derives it.

---
---

# PART 2 — THE COMPONENTS

## 2.1 ① The Derivation Kernel

**Pure. No I/O. No clock. Shipped to the server and both clients as one package.**

```ts
evaluate(match: Match, now: Instant, policy: ClubPolicy): Evaluation

type Evaluation = {
  state:    StateKey;                  // one of the 33, per the §1.4 ladder
  hold:     { kind: 'hard'|'soft'|'none'; why: string };
  committed:boolean;
  deadlines:Deadlines;
  facts:    FactDelta;                 // what SHOULD be true but is not yet written
  nextWakeAt: Instant | null;          // the next moment this could change
}
```

**`facts` is the piece that makes the whole design work.** `evaluate` does not write, but it reports what a writer would have to write:

```ts
type FactDelta = {
  setCommittedAt?:   Instant;
  assignCourt?:      CourtId;
  releaseCourt?:     true;
  setHoldKind?:      'hard' | 'soft';
  markInventoryLost?:true;
  markFormCancelled?:true;
  markCheckpointCancelled?: true;
}
```

Three callers, three uses of the same function:

| Caller | Uses |
|---|---|
| **Command handler** | `facts` → writes them · `nextWakeAt` → stores it |
| **Projection** | `state` → builds the card |
| **Client** | `state` → renders between pushes · `nextWakeAt` → schedules a local re-derive |

**`nextWakeAt` is a pure function of the record**, and it is the timekeeper's entire input. It returns the earliest future instant at which the derived state could differ:

```ts
function nextWakeAt(m: Match, now: Instant): Instant | null {
  if (isTerminal(m)) return null;
  const d = deadlines(m);
  const candidates: Instant[] = [];

  if (m.committedAt == null)                candidates.push(d.commit);
  if (filled(m) === 2 && n > 2)             candidates.push(m.start - 12*HOUR);   // Rule 8
  if (filled(m) === n - 1 && n > 2)         candidates.push(m.start -  4*HOUR);   // Rule 6
  if (m.vacated && m.committedAt != null)   candidates.push(d.rescue);
  candidates.push(d.check, d.joinCut, m.start - 15*MIN, m.start,
                  matchEnd(m), resultWindow(m), keepUntil(m));

  return min(candidates.filter(t => t > now));
}
```

**Note that the candidate set depends on the seat count.** A match on two paid seats wakes at T−12h; the same match after a third payment wakes at T−4h instead. **So every write recomputes the wake time.** That is not an inconvenience — it is what keeps the schedule honest with no reconciliation.

## 2.2 ② The Match Command Handler — the only writer

```ts
async function handle(cmd: MatchCommand): Promise<Result<DomainEvent[]>> {
  const now = clock.now();                            // ONE read, per command
  const m   = await matches.load(cmd.matchId);        // carries m.version

  if (await commands.alreadyApplied(cmd.id)) return commands.resultOf(cmd.id);

  const decision = decide(m, cmd, now, m.policySnapshot);   // PURE
  if (!decision.ok) return decision;

  return matches.append(
    m.id, m.version,                                   // optimistic concurrency
    decision.value.events,
    { nextWakeAt: decision.value.nextWakeAt,
      commandId:  cmd.id },
  );                                                   // ONE transaction, includes the outbox
}
```

### The commands

| Command | Source | Idempotency key |
|---|---|---|
| `JoinMatch` | player | client-generated uuid |
| `LeaveMatch` | player | client-generated uuid |
| `InviteToSeat` / `AcceptInvite` | player | client-generated uuid |
| `PayForSeat` | payment webhook | payment intent id |
| **`EvaluateAt`** | **timekeeper** | **`{matchId}:{threshold}:{scheduledFor}`** |
| `ClubCancel` / `LockCourt` | club console | club action id |
| `ConsentResponse` | player | consent id + player id |

**`EvaluateAt`'s idempotency key is the thing to look at closely.** It is *deterministic* — derived from the match, the threshold name, and the instant it was scheduled for. Fire it twice and the second is a no-op. Fire it from two workers and one loses. **This is what makes at-least-once scheduling safe**, and it is why the timekeeper needs no exactly-once guarantee, no leader election, and no distributed lock.

### Why optimistic concurrency and not a lock

Writes to one match are **rare** — a handful over its whole life. Reads are constant. A pessimistic lock held across a derive-heavy path is a lock held for a long time, protecting almost nothing.

A version conflict retries once with a fresh load. On the second failure the command reports honestly — *"This match is full"* — which is the message the player should see anyway.

### The one clock read

```
const now = clock.now();          ← captured ONCE, passed to everything
```

Two reads inside one command can disagree, and the money engine already depends on them not doing so: it captures the protection state *before* evaluating so it can tell whether *this* payment is the one that reserved the court.

## 2.3 ③ The Timekeeper — a poller over an index, not a service with memory

**The simplest correct implementation, and I would ship it:**

```sql
-- next_wake_at is a column on the match, written by the command handler
CREATE INDEX idx_wake ON matches (next_wake_at)
  WHERE next_wake_at IS NOT NULL AND terminal = false;
```

```ts
setInterval(async () => {
  const due = await db.query(`
    SELECT id, next_wake_at, wake_reason FROM matches
    WHERE terminal = false AND next_wake_at <= $1
    ORDER BY next_wake_at LIMIT 500
    FOR UPDATE SKIP LOCKED`, [clock.now()]);

  for (const m of due) {
    await bus.send(EvaluateAt(m.id, m.wake_reason, m.next_wake_at));
  }
}, 2000);
```

**Why this beats a queue, a scheduler service, or a timer per match:**

| Property | This design |
|---|---|
| **Nothing to rebuild** | The schedule *is* a column. There is no second store to reconcile |
| **Crash-safe by construction** | A restart loses nothing. The next poll picks up everything overdue |
| **Self-healing** | A missed wake is simply late, then caught. `next_wake_at <= now` is still true |
| **No leader election** | `FOR UPDATE SKIP LOCKED` lets N workers poll safely |
| **No drift** | Recomputed on every write, from the record |
| **Trivially inspectable** | *"What is due in the next hour?"* is a `SELECT` |

**Precision is the poll interval.** At 2 seconds, a state flips within two seconds of its threshold. Nothing in this product needs better: the door code at T−15min, the commitment at T−12h, the checkpoint at T−2h — all of them are human-scale.

**The sweep is the safety net.** A separate, slower pass catches anything with a null or stale wake time:

```sql
-- every 5 minutes: matches that should have woken and did not
SELECT id FROM matches
WHERE terminal = false
  AND (next_wake_at IS NULL OR next_wake_at < now() - interval '1 minute')
```

**If the sweep ever finds anything, that is a bug and should page somebody** — but it means the bug produces a late card, not a wrong one.

**Scale.** A city with 500 live matches has roughly 5,000 scheduled wakes across a week. A poll over an indexed column returning zero rows costs microseconds. This design holds to six figures of live matches before anything needs to change, and the first change is partitioning the poll by shard.

## 2.4 ④ The Projection — the per-player card list

**One materialized row per player, containing their ordered card list.**

```ts
type PlayerCardList = {
  playerId: PlayerId;
  version:  number;                       // monotonic, per player
  cards:    EnrolledCard[];               // sorted by match start, ascending
  builtAt:  Instant;
}
```

```ts
type EnrolledCard = {
  matchId:  MatchId;
  cardVersion: number;                    // monotonic, per match
  state:    StateKey;
  tag: string; tone: Tone; context: string;
  court: string; group: string;
  alert: string | null;
  lines: { settled: boolean; text: string }[];
  cta:   { label: string; target: string };
  showAccess: boolean;
  glyph: { seats: SeatSymbol[]; filled: number; capacity: 2|4 };
  money: { share: Grosze; cardOff: Grosze; payable: Grosze };

  nextTransition: { at: Instant; becomes: StateKey } | null;   // ← for the client
  record: MatchRecordSlice;                                    // ← for local derivation
}
```

### The build, on every domain event

```
DomainEvent(matchId)
   → who is enrolled in this match?        (up to 4 players, +waitlisters)
   → for each: rebuild THAT ONE CARD       (evaluate + render)
   → bump the player's list version
   → emit CardPatch(playerId, listVersion, card)
```

**One card, not the list.** The strip is sorted by start time and a state change never reorders it, so a patch is always safe.

**The card is built once per player, not once per device.** Fan-out to devices happens in delivery.

### Why a materialized projection at all

The alternative is deriving on every read. Three reasons not to:

1. **The card is expensive relative to the state.** Thirty-three states × up to five lines each, with interpolated names, prices and times. The state is integer comparisons; the card is string building.
2. **The push needs a diff.** Materialization gives you a previous version to compare against, which is how you avoid pushing a card that did not change.
3. **Cold start must be one read.** Opening the app is the most common operation in the product and it should be a single indexed lookup.

**But it is a cache, and it is treated as one.** It can be rebuilt from the match records at any time, and the rebuild is the disaster-recovery story.

### The two-writer problem, again — and why it does not exist here

The projection is written by exactly one consumer of the outbox, keyed by player. Two events for the same player are processed in order because they are in the same partition. **Partition the projection consumer by `playerId`, not by `matchId`** — that is the one non-obvious choice, and it is what keeps a player's list version monotonic when two of their matches change at once.

## 2.5 ⑤ Delivery — reactive, and safe to lose

```
CardPatch(playerId, listVersion, card)
        │
        ▼
   ┌─────────────────────────────────────────┐
   │  Connection registry: playerId → sockets │
   └────────────────┬────────────────────────┘
                    ▼
        one frame per connected device
```

### The wire protocol

```jsonc
// on connect
{ "t": "sync",  "listVersion": 412, "cards": [ … ] }

// on change — one card
{ "t": "patch", "listVersion": 413, "card": { … } }

// card gone (settled past 24h, or you left)
{ "t": "drop",  "listVersion": 414, "matchId": "m_1180" }

// every 20s
{ "t": "ping",  "listVersion": 414 }
```

### Three rules that make lost frames harmless

**Monotonic acceptance.** The client ignores any frame whose `listVersion` is not greater than what it holds. Duplicates and out-of-order frames are free.

**Gap detection on the heartbeat.** The `ping` carries the current version. If the client's version is behind, it requests a full `sync`. **This is the mechanism that makes a dropped patch self-heal within twenty seconds**, with no server-side tracking of what each client has seen.

**Reconnect is a sync, never a replay.** No event log is replayed to a client. It gets the current list and its version. Simple, bounded, and correct regardless of how long it was away.

### Fan-out numbers

One match event touches at most four enrolled players plus waitlisters. Each has one to three devices. **So a single domain event produces on the order of ten frames.** Even at a thousand events a minute city-wide, that is trivial — and it partitions perfectly by player.

---
---

# PART 3 — THE FLOWS

## 3.1 A clock threshold — nobody did anything

The two-seat soft hold lapses at T−12h.

```
 t         Component            Action
──────────────────────────────────────────────────────────────────────────────
 06:30:01  Timekeeper           poll finds match m1180, next_wake_at = 06:30:00
 06:30:01  Timekeeper           send EvaluateAt(m1180, 'HOLD_FAR_LAPSE', 06:30:00)
                                idempotency key = "m1180:HOLD_FAR_LAPSE:1754887800"
 06:30:01  Command handler      load m1180 (version 7)
 06:30:01  Derivation Kernel    evaluate(m, now)
                                  → hold: none · farLapsed
                                  → facts: { releaseCourt: true }
                                  → state: heldReleased
                                  → nextWakeAt: T−2h (the checkpoint)
 06:30:01  Command handler      append v7 → v8
                                  events: [CourtReleased]
                                  set next_wake_at = 16:30:00
                                  outbox row, SAME transaction
 06:30:01  Outbox → Projection  4 enrolled players
                                  rebuild 1 card each
                                  bump each player's listVersion
 06:30:01  Delivery             4 players × ~2 devices = ~8 frames
 06:30:01  Notifications        "The court went back" — amber, to everyone in the match
 06:30:02  Client               patch applied, card animates in place, strip does not reorder
──────────────────────────────────────────────────────────────────────────────
                                total: ~1 second from threshold to pixel
```

**If the timekeeper had been down**, the poll picks it up when it recovers, and any player who opened the app in the meantime would have seen the correct state anyway — because opening the app derives it.

## 3.2 A player leaves after commitment

```
 t         Component            Action
──────────────────────────────────────────────────────────────────────────────
 14:00:00  Client               POST /commands { type:'LeaveMatch', id:<uuid> }
 14:00:00  Command handler      dedupe check on <uuid> → not seen
 14:00:00                       load m1180 (version 11)
 14:00:00  Derivation Kernel    leaveOutcome(m, now) → kind:'rescue', 50%
                                  committed ⟹ seat STAYS PAID
                                  facts: { vacated:'ola', vacatedAt:now }
                                  hold stays HARD (Rule 3)
                                  state: replacement
                                  nextWakeAt: 14:30 (rescue opens)
 14:00:00  Command handler      append v11 → v12
                                  events: [SeatVacated]
 14:00:00  Outbox → Rescue saga PHASE A fires immediately — full-price nudge to standby
 14:00:00  Outbox → Projection  Ola's card → the leaver's view
                                  3 others' cards → replacement + ALERT strip
 14:00:00  Delivery             ~8 frames
 14:00:01  Notifications        "Ola left. Your payment will not change." — coral
──────────────────────────────────────────────────────────────────────────────
 14:30:00  Timekeeper           EvaluateAt(m1180, 'RESCUE_OPEN', 14:30)
                                  → state: rescue · amber · Stages 1–5 begin
```

**The leaver and the three who stayed get different cards from the same event**, because the projection builds per player and the money line is player-relative.

## 3.3 The race — a leave at the same instant as a threshold

```
 14:29:59.8  Player command       load m1180 v11
 14:30:00.1  Timekeeper command   load m1180 v11
 14:30:00.2  Player command       append v11 → v12  ✓
 14:30:00.3  Timekeeper command   append v11 → ✗ CONFLICT (now v12)
 14:30:00.3  Timekeeper command   RETRY: reload v12, re-evaluate, append v12 → v13  ✓
```

**Both effects land, in a defined order, with no lost write.** The retry re-evaluates against the *new* record, so the rescue threshold is applied to a match that already has a vacancy — which is exactly right, and is why the retry re-runs `evaluate` rather than replaying a stale decision.

**In your original design this is where the corruption happens**, and it happens silently.

## 3.4 The push is lost

```
 06:30:01  Delivery       patch(listVersion 413) sent
 06:30:01  Network        frame dropped — train tunnel
 06:30:20  Delivery       ping(listVersion 413)
 06:30:20  Client         holds 412 < 413 → requests sync
 06:30:20  Delivery       sync(413, [cards])
 06:30:20  Client         correct, 19 seconds late
```

**And if the socket is down entirely**, the client's own copy of the kernel notices that `nextTransition.at` has passed and re-derives locally from `card.record`. **The card is right before any network round-trip happens.**

## 3.5 Cold start

```
 App opens
   → GET /now             one indexed read of the player's projection row
   → render               < 100 ms
   → open WebSocket, send held listVersion
   → server: equal → nothing. behind → sync.
```

**One read. No fan-out, no derivation, no join.** This is why the projection is materialized.

---
---

# PART 4 — THE CLIENT CONTRACT

## 4.1 The client has the kernel

The kernel package ships to the server and both applications. That is already established, and it pays for itself here.

```
The client MAY derive.       The client may NEVER decide.
```

| Client may | Client may not |
|---|---|
| Re-derive the state from `card.record` when a push is late | Write a derived value anywhere |
| Tick a countdown | Send a conclusion to the server |
| Flip optimistically at a predicted threshold | Treat its own derivation as authoritative over a later push |
| Render correctly offline | Skip reconciliation on reconnect |

**Commands carry intent — `join this match` — never conclusions — `this match is committed`.**

## 4.2 The three-layer render

```
 1.  A push arrived              → render the server's card. Authoritative.
 2.  nextTransition passed,
     no push within 3 s          → re-derive locally, render, mark provisional
 3.  A push arrives later        → replace. Server always wins.
```

**Layer 2 is what makes the screen feel instant** at exactly the moments a player is watching it — the fifteen minutes before play, the minute around a deadline. It is also what makes the app correct in a basement.

**Layer 2 is never allowed to persist anything**, and a provisional card that disagrees with a later push is simply replaced. No merge, no conflict resolution, no diff.

## 4.3 The strip does not reorder

Cards are sorted by match start, which never changes. A card can change every field it has and stay exactly where it is.

**This is what makes patching safe**, and it is worth protecting with a test: apply every possible state transition to every card and assert the order is unchanged.

---
---

# PART 5 — CORRECTNESS

## 5.1 Every failure mode, and what it degrades to

**The design goal: every failure produces *late*, never *wrong*.**

| Failure | Detected by | Degrades to | Recovery |
|---|---|---|---|
| Timekeeper down | Sweep · monitoring | Cards stale until it returns. **Any read is still correct** | Poll catches everything overdue |
| Timekeeper fires twice | Idempotency key | Nothing | Second command is a no-op |
| Two workers grab one match | `FOR UPDATE SKIP LOCKED` | Nothing | One wins |
| Command handler conflict | Version check | One retry | Re-evaluate against the new record |
| Duplicate player command | Command id dedupe | Nothing | Original result returned |
| Outbox consumer lags | Consumer lag metric | Push is late. **Reads are correct** | Catches up |
| Projection corrupted | Checksum · rebuild drill | Wrong cards | **Rebuild from match records** |
| Push frame lost | Heartbeat version gap | ≤ 20 s stale | Client requests sync |
| Socket down | Connection state | Client derives locally | Sync on reconnect |
| Server restart | — | Nothing in memory was authoritative | — |
| Client clock wrong | Server `serverTime` on every frame | Countdown drifts | Offset, never absolute device time |
| Notification dropped | — | Player finds out on next open | The card carries the whole story |

**Two rows are the load-bearing ones.** *Any read is still correct* appears twice, and it is the reason this architecture is trustworthy: the push path can fail completely and the product still works, just less magically.

## 5.2 Invariants — assert these, do not assume them

```
 1  exactly one component writes to a match
 2  committedAt, once written, is NEVER unwritten
 3  committedNow ⟹ holdKind = 'hard'                        (Rule 3)
 4  committed AND no court                                   UNREACHABLE
 5  committed AND soft hold                                  UNREACHABLE
 6  next_wake_at is recomputed on EVERY write
 7  next_wake_at is null ⟺ the match is terminal
 8  a listVersion never decreases
 9  a cardVersion never decreases
10  the card list is always sorted by match start
11  a state change never reorders the list
12  every command is idempotent under replay of its id
13  the projection is rebuildable from match records alone
14  a lost push is detected within one heartbeat
15  scrub the clock forward then back: every derived value returns — except committedAt
```

**Invariants 4 and 5 deserve the most testing**, because a violation is invisible on screen and catastrophic in effect: a committed match whose court quietly went back.

**Invariant 13 is the disaster-recovery story**, and it should be exercised on a schedule, not documented and forgotten.

## 5.3 The tests that matter

| Test | Why |
|---|---|
| **Threshold ± 1 second**, every threshold, every club type | Every branch point in the model lives at a threshold |
| **Concurrent leave + threshold**, deliberately interleaved | The race in §3.3 |
| **Duplicate `EvaluateAt`** | Idempotency |
| **Kill the timekeeper mid-week**, restart, assert convergence | Self-healing |
| **Drop every third push**, assert convergence within 20 s | Heartbeat recovery |
| **Rebuild the projection from scratch**, assert byte-identical | Invariant 13 |
| **Scrub the demo week forwards and backwards** | Derivation purity |
| **Atlantic Sports** (window 12h, so `commit` = T−12h exactly) | Two rules firing at one instant |
| **Singles** (n=2, no soft tier) | Rule 10 |
| **Both checkpoint policies**, including *nothing happens* | Three outcomes, not two |

---
---

# PART 6 — DESIGN PATTERNS

*Each one justified by a specific problem in this feature, not by being a pattern.*

## 6.1 Applied

| Pattern | Where | The problem it solves |
|---|---|---|
| **Aggregate + Command Handler** | The match | One consistency boundary, one writer, one version. Kills the §0.3 race |
| **Functional Core / Imperative Shell** | `evaluate` / `apply` | The same function is safe to call from a server, a client and a test |
| **Transactional Outbox** | Every write | No dual-write between the database and the bus. Events cannot be lost or ghosted |
| **Materialized read model (CQRS)** | The card list | Cold start is one read; the write model stays normalised |
| **Guard chain, ordered** | The §1.4 resolution ladder | The order *is* the specification. An ordered array of predicates says so; a class hierarchy hides it |
| **Table-driven state content** | The 33 states | Adding a state is a table row, not a subclass. The visual is identical across all of them by construction |
| **Idempotency key** | Every command | At-least-once delivery becomes safe, which removes the need for exactly-once anywhere |
| **Optimistic concurrency** | The match | Reads vastly outnumber writes; a lock would protect almost nothing at real cost |
| **Process Manager / Saga** | The rescue cascade | The one genuinely long-running thing. Durable, event-driven, resumable |
| **Version vector + monotonic accept** | Delivery | Duplicate and out-of-order frames become free |
| **Strategy** | `nextWakeAt` candidate rules | Each ladder rule contributes a candidate; adding Rule 11 (soft-hold max age) is one entry |

## 6.2 Deliberately refused

| Pattern | Where it is tempting | Why not |
|---|---|---|
| **Actor per match with a timer** | Natural encapsulation | The actor holds state that must also be persisted — two sources of truth. See §7.1 for the conditions under which I would reconsider |
| **State pattern (class per state)** | 33 states | They differ in *content*, not behaviour. Thirty-three classes with identical shape is a table with extra steps |
| **Full event sourcing on the match** | The events already exist | Most of the model is derived, so there is little to source. The **ledger** is event-sourced; the match is a record with an outbox |
| **Saga for anything but the cascade** | Multi-step flows | Everything else completes in one command. A saga for a synchronous operation is a distributed monolith |
| **A separate rules microservice** | "Engine" implies service | The rules are microseconds of integer comparison. A network hop per evaluation costs a thousand times the work it does |
| **Client-side state machine** | Instant UI | The client *derives* with the shared kernel. A second implementation is how two apps end up disagreeing about one booking |
| **Polling from the client** | Simplicity | 30-second polling on the most-used screen is both wrong-for-30-seconds and wasteful. The heartbeat already gives you the safety net |
| **Message queue for the timekeeper** | "Proper" scheduling | The schedule as a column is crash-safe with nothing to rebuild. A queue adds a store that can disagree with the record |

---
---

# PART 7 — ALTERNATIVES CONSIDERED

## 7.1 Actor per match — and when I would choose it

**The design:** each match is a virtual actor (Orleans, Dapr, Cloudflare Durable Objects). It owns its state, holds its own timer, and processes commands serially.

**What it gets right, genuinely:** the single-writer property comes free and is enforced by the runtime rather than by a version column. Serial processing means the §3.3 race cannot occur at all.

**What it costs:**

- The actor's in-memory state must also be persisted, so there are two representations and a rehydration path
- A timer inside an actor is lost on migration and must be re-armed from the record — which is the polling design, hidden
- Testing a threshold means manipulating actor time rather than calling a pure function
- Clock scrubbing, which the whole model depends on, becomes hard

**I would choose it if:** you are already on a virtual-actor platform, **and** the actor is written to *derive* rather than *track* — holding only the record, re-arming its timer from `nextWakeAt` on every activation.

Under those conditions it is a legitimate implementation of the same architecture, with the runtime providing the single-writer guarantee instead of the version column. **The architecture in this document does not change; only ② and ③ are implemented differently.**

## 7.2 Recompute everything on a tick

**The design:** every N seconds, evaluate every live match.

**Why it is tempting:** trivially correct, no scheduling, no missed wakes.

**Why not:** at 500 live matches and a 1-second tick that is 500 evaluations a second doing nothing 99.9% of the time — and it scales linearly with matches while the useful work scales with *transitions*, which is a far smaller number.

**But it is the right fallback**, and the sweep in §2.3 is a slow version of exactly this. Worth keeping precisely because it is dumb and cannot be subtly wrong.

## 7.3 Derive on read, no projection

**The design:** no materialized card list. `GET /now` evaluates and renders on the fly.

**Why it is tempting:** one fewer component, no rebuild story, no staleness.

**Why not, for this feature specifically:** the reactive push needs a *previous* version to diff against, and cold start needs one read rather than a fan-out. **Both requirements come from the feature being reactive**, not from performance.

**If the strip were not reactive, I would not build the projection.**

## 7.4 Store the state key

**The design:** a `state` column, written on transition.

**Why not, and this is the clearest no in the document:** the state is a pure function of the record and the clock. Storing it creates a value that can disagree with its own inputs, and every failure mode above becomes *wrong* instead of *late*.

**It also breaks the client's local derivation**, which is what makes the screen instant and offline-correct.

---
---

# PART 8 — SCALE

## 8.1 The numbers

| Quantity | One city | Ten cities |
|---|---|---|
| Live matches | ~500 | ~5,000 |
| Enrolled players per match | ≤ 4 | ≤ 4 |
| Scheduled wakes per match, whole life | ~10 | ~10 |
| Timekeeper polls | 30/min, mostly empty | 30/min, mostly empty |
| Domain events per minute, peak | ~60 | ~600 |
| Frames per domain event | ~10 | ~10 |
| Frames per minute, peak | ~600 | ~6,000 |
| Concurrent sockets | ~2,000 | ~20,000 |

**Nothing here is difficult.** The design's headroom is limited by socket count long before anything else, and sockets partition trivially by player.

## 8.2 What to partition, and when

| Component | Partition by | When |
|---|---|---|
| Command handler | `matchId` | Only if write contention appears — it will not soon |
| Timekeeper | shard of `matchId` | Above ~50k live matches |
| Projection consumer | **`playerId`** | From day one — see below |
| Delivery | `playerId` | With socket count |

**Partitioning the projection by `playerId` is the one non-obvious choice, and it is not optional.** If two of a player's matches change in the same second and the events are processed in different partitions, their list version can go backwards and a client will reject a valid card. Same key, same partition, ordered.

## 8.3 Budgets

| Operation | Budget |
|---|---|
| `evaluate` one match | < 50 µs |
| `nextWakeAt` | < 10 µs |
| Build one card | < 500 µs |
| Command end-to-end | < 50 ms |
| Threshold → pixel | **< 2 s** (dominated by the poll interval) |
| Cold start `GET /now` | < 100 ms |
| Reconnect sync | < 200 ms |

**Threshold-to-pixel is the number the feature is judged on.** Two seconds is the poll interval plus change, and it is imperceptible for every threshold in the model.

---
---

# PART 9 — BUILD ORDER

| # | Deliverable | Gate |
|---|---|---|
| **1** | Derivation kernel: the §1.4 ladder, the 12 + 7 rules, `nextWakeAt` | All 33 states from fixtures · scrub forward and back reproduces every value |
| **2** | Match aggregate + command handler, optimistic concurrency, dedupe | Concurrent leave + threshold: both land, no lost write |
| **3** | Outbox, in the same transaction as the write | Kill the process mid-write: no ghost event, no lost event |
| **4** | Timekeeper: `next_wake_at` column, poll, sweep | Kill it for an hour, restart, everything converges |
| **5** | Projection: per-player list, per-card build, versioning | Rebuild from records is byte-identical |
| **6** | Delivery: sync · patch · drop · ping, monotonic accept | Drop every third frame: converges within 20 s |
| **7** | Client: render pushes, derive between them, reconnect | Airplane mode across a threshold: correct card, no network |
| **8** | Rescue saga on the outbox | The six scenarios, with virtual time |
| **9** | Notifications on the outbox | Every red notification carries its money position |
| **10** | Chaos drills | Every row of §5.1, run deliberately |

## 9.1 The acceptance gate

- [ ] **Exactly one component writes to a match** — provable by inspection of the write path
- [ ] No component stores the current state key
- [ ] `next_wake_at` is recomputed on every write, and is null exactly when terminal
- [ ] `EvaluateAt` is idempotent under its deterministic key
- [ ] Concurrent player command + threshold: both effects land, defined order, no loss
- [ ] The projection rebuilds byte-identically from match records
- [ ] A dropped push self-heals within one heartbeat
- [ ] The client renders correctly with the socket closed, across a threshold
- [ ] All 15 invariants hold; 4 and 5 asserted unreachable
- [ ] Threshold to pixel under 2 seconds at p99
- [ ] Every §5.1 failure mode has been induced deliberately and degrades to *late*, never *wrong*

---

*Five components · one writer · one derivation · nothing tracked · the push is an optimization and the read is the truth.*
