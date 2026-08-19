# Spec delta — live delivery, and the projection consumer under it

**Governs over** `3-enrolled_match_engine_architecture.md` §2.4 (the partitioning requirement),
§2.5 (Delivery), §3.5 (Cold start), §5.1 (the failure table's push rows), and over
`5-now_screen_architecture_review.md`'s build-order row 7. Everything else in both documents
stands unchanged.

**The decisions:** [ADR-0038](../../../adr/0038-now-is-polled-the-push-is-specified-and-deferred.md)
— Now is polled; the push is specified and deferred. And
[ADR-0039](../../../adr/0039-the-card-projection-rebuilds-from-the-record.md) — the projection
rebuilds from the record, so its consumer needs no partition.
**The reasoning:** [`Raketa02/Raketa#12`](https://github.com/Raketa02/Raketa/issues/12).

The source documents are **not edited**. 27 bare-filename cross-references resolve against their
bytes.

---

## 1. What is built in v1

| §2.5 / doc 5 row 7 as written | What governs |
|---|---|
| A WebSocket carrying `sync` / `patch` / `drop` / `ping` | **Not built.** `GET /now` is the only delivery mechanism |
| Delivery is the seventh of seven deliverables | Delivery is **not a deliverable of the Now effort**. §2 below is its specification, held for the trigger in §5 |
| §3.5's cold start: `GET /now`, render, **then open a socket** | `GET /now`, render. The client polls at **30 s while foregrounded**, never while backgrounded — `focusManager` / `onlineManager` (ADR-0013) gate it |
| §2.4 *"the push needs a diff"* as a reason to materialize | Reasons **1** (the card is expensive relative to the state) and **3** (cold start must be one indexed read) carry the projection on their own. Reason 2 was contingent |

**Rule IV is unchanged and now literal.** *The read is the truth; the push is an optimisation* —
so the optimisation is not built. The residual staleness is bounded at thirty seconds while
foregrounded rather than assumed away, and **no card admits staleness on screen**: no marker, no
banner. That is a UI addition neither UI authority draws.

## 2. The frame protocol, specified and held

Written down so that building it later is reading rather than rediscovery. None of this ships in
v1.

- **Transport: WebSocket.** Not for §2.5's reason. React Native ships `WebSocket` and does
  **not** ship `EventSource`, so SSE would need a third-party polyfill that ADR-0013 refuses
  absent a stated requirement — the usual web reasoning inverts here. §3.5's handshake also
  sends the client's held `listVersion` upstream, which SSE carries only as a query parameter
  and cannot repeat.
- **Authentication: at handshake, bounded by the access token.** `ACCESS_TOKEN_EXPIRE_SECONDS`
  is 900, so the **server** closes the connection at token expiry with a close code the client
  can distinguish from a network drop, and the client reconnects immediately rather than backing
  off. A client-enforced ceiling is one a client can decline to enforce, and revocation is the
  reason for the ceiling. The socket asks `shared/lib/auth` for a token **at connect time only**
  and never re-implements rotation, so ADR-0008's single-owner property survives.
  A same-version reconnect costs a handshake, not a full list — §3.5's *equal → nothing, behind
  → sync* is what makes the 15-minute cycle cheap, so that handshake is **not optional**.
- **Registry: `playerId → connections`, behind a port**, with an in-process adapter. Redis is
  declared in `pyproject.toml` and imported by nothing; it becomes the adapter when a second
  instance exists. **Deployment invariant while the adapter is in-process: the API cannot run
  more than one instance.** Its failure mode reads as "the push is a bit unreliable", which is
  why it is written here and not discovered.
- **Placement:** the projection is a read model **of Matches** and lives with it; the connection
  registry and frame protocol are cross-cutting infrastructure under
  `app/infrastructure/delivery/`, the shape `EventWorker` and the outbox already have. The
  socket route mounts on the **player** surface only ([ADR-0016](../../../adr/0016-modular-monolith-two-api-surfaces.md)).
- **Heartbeat: 20 s**, as §2.5 states.

### What [ADR-0032](../../../adr/0032-order-is-a-property-of-the-composed-screen.md) changes about the frames

§2.5 justified patching with *"cards are sorted by match start, which never changes."*
ADR-0034 makes `start` explicitly mutable — *a moved match is the same match* — and ADR-0032
forbids reordering on a live frame. So:

- **A `sync` carries content and order; a mid-view `sync` applies content only** and keeps the
  held order. The twenty-second self-heal keeps working, and the strip still never moves under a
  thumb. The deferred order lands at the next composition — open, foreground, or pull.
- **A live frame never inserts.** A new card has no legal position mid-view. The one exception
  costs nothing: **the player's own mutation composes** — joining a match is a TanStack mutation
  with a declared cache effect (ADR-0013), so your own join lands instantly and only other
  people's news waits.
- **`drop` stays live**, because both of its triggers are non-interactive: *you left* composes
  anyway, and *settled past 24 h* is a retention expiry nobody is watching. Attached rule:
  **no bad-news transition may ever be expressed as a `drop`.** A cancelled match renders a
  cancelled card and keeps its position; it never disappears. Without that written down, "drop
  is live" is one refactor away from being how a cancellation reaches the screen.

## 3. §2.4 — the partitioning requirement does not carry

| §2.4 as written | What governs |
|---|---|
| **"Partition the projection consumer by `playerId`, not by `matchId`"** — *"the one non-obvious choice"* | **No partitioning.** One more handler on the existing `EventWorker` — doc 5's *"wiring, not infrastructure"* is literally true |
| Partitioning is what keeps `listVersion` monotonic when two matches change at once | The **rebuild** keeps it correct; an **atomic** `UPDATE … SET version = version + 1` keeps the counter safe. Ordering was never the defect |

The consumer **rebuilds each affected player's card from the current match record** — it never
applies a delta and never reads a previous card to compute a new one. Two events for one match
in either order read the same current record and produce the same card. That is a **rule**: a
handler that starts diffing has silently reintroduced the ordering requirement, and the
reviewer's question is *"does this handler read the previous card?"*

## 4. §5.1 — the failure table

C2's row was already narrowed by [ADR-0034](../../../adr/0034-matches-is-a-record-and-keeps-no-history.md):
`formCancelled` and `checkpointCancelled` are receipts on derivable conclusions, so a stale read
derives `cancelledIncomplete` correctly without the writer. Of doc 5's four bad-news
transitions, **two remain undeliverable by derivation** — `clubCancelled` (a Declaration) and
`inventoryLost` (an Allocation) — plus `releasedAt`, unless ClubPolicy's `maxHoldAge` rides in
the card's record slice, in which case a lapsed hold is a threshold the client's own kernel
crosses.

| §5.1 row | What governs |
|---|---|
| *Push frame lost* → ≤ 20 s stale, client requests sync | **No push.** ≤ 30 s stale while foregrounded |
| *Socket down* → client derives locally, sync on reconnect | **No socket.** The client derives locally at every clock threshold — this is now the primary freshness mechanism, not a fallback — and polls for the writer-driven residual |
| *Notification dropped* → player finds out on next open | Unchanged, and now the standing answer for a backgrounded app. What makes it safe is the rest of that row: **the card carries the whole story** |

## 5. The trigger for building §2

**A feature whose value depends on another player's action reaching a viewer in under one
second** — live scoring, in-match chat, a spectator view. Now is not that feature; those would
justify the channel on their own terms rather than inheriting it.

Not triggers: polling cost (one indexed single-row read per foregrounded player per 30 s), or
the fact that §2.5 specifies a socket.

## 6. What ships on `GET /now` with no reader

`listVersion`, `cardVersion`, `serverTime`, `nextTransition`. Adding them later is a breaking
change against phones that cannot be forced to update (ADR-0008), which is the whole reason they
ship now. **`serverTime` is the one most likely to be deleted as dead weight** — it is what keeps
a countdown from trusting a wrong device clock (§5.1's client-clock row).
