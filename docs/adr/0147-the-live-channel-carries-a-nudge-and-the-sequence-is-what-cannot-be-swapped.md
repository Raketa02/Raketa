# ADR-0147 — The live channel carries a nudge, and the sequence is what cannot be swapped

- **Status:** Accepted
- **Date:** 2026-09-07
- **Completes [ADR-0146](0146-the-chat-is-two-contexts-and-a-system-line-is-a-code.md)**, which
  gave a conversation *"a **conversation-scoped sequence number minted on append**, decided by the
  transport research"* and left its shape, its promise and its transport to this record.
- **Cites ADR-0110** — *two
  subscriptions, two guarantees*. ADR-0146 claimed the second guarantee; this record is the
  mechanism that makes the claim true.
- **Cites [ADR-0097](0097-event-store-append-order-is-a-sequence-column.md)**, whose finding —
  `func.now()` is transaction-start time, identical across a transaction and not unique — is why
  no timestamp may ever serve as this stream's order.
- **Cites [ADR-0003](0003-transactional-outbox-for-event-delivery.md)** for delivery, and
  **[ADR-0002](0002-event-sourced-user-aggregate.md)** for the write model this record refuses to
  move.
- **Cites [ADR-0004](0004-jwt-access-with-rotating-refresh-tokens.md)** — the stream is ended by
  the access token's expiry rather than permitted to outlive it.
- **Extends [ADR-0006](0006-backend-owns-api-contract.md)**: a live event **is** a backend
  response, and it is generated from the contract like every other one. This is not an exception
  to that record, and no exception is granted.
- **Cites [ADR-0010](0010-local-first-development-aws-deferred.md)**, whose predicted rot is
  [#341](https://github.com/Raketa02/Raketa/issues/341).
- Settles [#333](https://github.com/Raketa02/Raketa/issues/333) on the map
  [#321](https://github.com/Raketa02/Raketa/issues/321).

> **One sentence of Decision 3 superseded 2026-09-10 by
> [ADR-0156](0156-the-live-channel-carries-presence-and-a-heartbeat-is-the-only-honest-shape.md):
> the channel carries a nudge **and a typing frame**, and nothing else.** The second event is
> named on the SSE `event:` field, so a client that listens only for `nudge` is untouched and
> `LIVE_CHANNEL_VERSION` does not move. **Everything else in this record stands exactly as
> written** — the cursor rule, the gapless sequence, the token deadline, the fail-soft publisher
> and the fail-loud subscriber — and the new frame is emphatically outside the sequence: it is not
> an entry, takes no lock, and never asks the allocator for a number.

> **Amended 2026-09-08 by [#342](https://github.com/Raketa02/Raketa/issues/342): the subscriber's
> own client is the shared module's, and `REDIS_TIMEOUT_SECONDS` no longer exists.** Decision 5
> gives the subscriber its own Redis client because that constant was passed as both timeouts;
> it is now two — `REDIS_CONNECT_TIMEOUT_SECONDS` and `REDIS_READ_TIMEOUT_SECONDS` — beside a
> `create_redis_subscriber_client` whose connect is bounded and whose read has no deadline at all.
> **What Decision 5 asks for is unchanged**; one of the stated consequences retires. The amendment
> at the foot of this record says what moved and what did not.

> **Note — the Classic play removal (2026-10-06, [#569](https://github.com/Raketa02/Raketa/issues/569)).** The Plan and `challenges` are gone, so §3's plan and challenge lines, §12's live plan slots, lock and growing membership, and the plan half of the 2026-09-11 amendment — the plan list, the cancel before a plan write, the accept that wrote `SeatAccepted` with `GamePlanned` — describe nothing. Only `games` writes into a room now, and on a nudge the client re-reads the room and the games list. Membership (§5) is the booked game's current line-up. There is no Chats tab: the room list survives only as the read a booked game's chat door joins over. The transport, the nudge, the gapless sequence, the token deadline and the fail-soft/fail-loud split stand.

## Context

**This is the first live surface in either app.** `backend/app` has no websocket and no SSE;
`frontend_player/docs/architecture.md` has no posture for a live surface; and the client's standing
rule is that *nothing in Play background-refetches*. Everything below is new ground, and the ground
is load-bearing for four slices of the core loop.

The options were surveyed in
[`docs/research/the-chat-real-time-layer.md`](https://github.com/Raketa02/Raketa/blob/research/chat-real-time-layer/docs/research/the-chat-real-time-layer.md)
(branch `research/chat-real-time-layer`, 1414 lines). Its findings are treated here as facts to
argue **against**, not to re-derive. The ones that survived the argument:

- **SSE needs no new backend dependency; WebSockets need one before the first line of code.**
  `fastapi.sse.EventSourceResponse` landed in FastAPI **0.135.0** and this repo pins **^0.136.1**.
  Meanwhile `uvicorn` is pinned **^0.47.0 without `[standard]`**, so `websockets` is absent from
  `poetry.lock` entirely and the server as configured **silently refuses** an upgrade — the worst
  failure shape available, because it is indistinguishable from a client bug.
- **Every option must reconnect anyway.** The ALB's `client_keep_alive` defaults to 3600s and an
  ECS rolling deploy severs 100% of open connections about thirty seconds after the replacement is
  healthy. Reconnection is a property of the deployment, not a weakness of a protocol.
- **Fan-out is nearly free here.** Redis is already in the codebase; ElastiCache Valkey is
  $6–9/month. The managed options compete on engineering surface, not price.
- **Firebase puts the source of truth in two places with no transaction between them**, moves
  authorization into CEL, and hands the player a second session this platform cannot promptly
  revoke — against ADR-0004, whose whole point is detectable replay.
- **Polling cannot serve an open conversation.** Android's ~18-second radio tail per transfer means
  any usable interval costs roughly what an open connection costs, and adds a latency floor.

### The number that decides more than any argument

The research named **peak concurrent connections** as the first thing this ticket should ask for,
and it was asked. The answer is **single digits at launch, low tens at the ceiling being planned
for** — and it is a smaller number than it looks, because under Decision 9 a connection exists only
while a player has a **conversation screen open in the foreground**, not per logged-in user and not
per app-open.

That number is the licence for everything cheap below. It is also the number that would invalidate
this record: at **hundreds** concurrent, Ably's free tier (200 connections, 6M messages/month)
becomes the cheaper answer and Decision 4 should be reopened. **Stated so the reopening is a
measurement rather than an argument.**

### Where the research stopped, and why this record goes further

The research made the Redis bus a **nudge** — *"conversation X changed above seq N"* — and then, at
the hop from server to phone, quietly handed the client the entry itself. Taking the nudge the
whole way is Decision 3, and it is the decision the rest of this record hangs from.

## Decision

### 1. The source of truth does not move, and no future transport may move it

**We will keep the event-sourced Postgres write model as the only origin of anything a player
sees.** A live layer may cache, batch, fan out or notify; **nothing a player reads may originate
anywhere else.**

Stated as a standing clause rather than as a rejection of Firebase, because the clause is the part
that stays true after the transport is swapped. Firebase is refused as its first application, on
the argument above.

### 2. The conversation's sequence is **gapless**, and it is allocated on the aggregate

ADR-0146 §4 put messages and system lines in *"one ordered stream and one sequence number"* and
left the shape here. It is:

**`last_seq + 1`, read and written on the conversation row under that row's lock, inside the
appending transaction.** Not a Postgres sequence object, which is explicitly **not** gapless —
aborts and crashes leave holes — and not a timestamp, which ADR-0097 already disqualified.

Three reasons beyond cheapness, and the cheapness is real: contention at two-to-four members is
nil.

- It **serialises appends**, so the total order is the aggregate's own fact rather than a database
  object's side effect.
- It puts **`last_seq` on the conversation row**, which is exactly the value Decision 3's nudge
  publishes — no second read in the publish path.
- It leaves the unread mark buildable. The map holds *unread, inside a conversation* as
  unspecified, needing a **per-viewer position** over this sequence; a position is arithmetic only
  against a gapless count.

**And the client never infers loss from a gap anyway.** Belt and braces: the server promises
gapless, and no client is permitted to depend on the promise. Decision 3 is what makes that
affordable rather than pious.

### 3. The live channel carries a **nudge**, and nothing else

**The event a phone receives is `{v, conversation_id, last_seq}`.** Never a message body, never a
system line, never a plan slot. On receiving one, the client fetches from **its own** high-water
mark through the ordinary authenticated read path.

Three arguments, in the order they matter:

- **A lost frame self-heals.** If the event carried the entry, a dropped frame would be a hole the
  client must detect by sequence arithmetic and repair. Carrying a nudge, the **next** nudge
  repairs it for free — because the client asks from its own cursor and not from the nudge's
  number. At-most-once on Redis and at-most-once on SSE stop being two risks and become one
  harmless one.
- **The rule becomes structural.** *Whether the UI may render something it did not read from the
  authoritative path* is the most expensive of the research's four irreversibles. Under this
  decision it stops being a rule anyone has to keep and becomes **a thing the wire cannot
  express.**
- **The contract surface that no check watches collapses to two integers.** A live envelope has no
  request/response pair in `openapi.player.json` for `check-contract-drift.sh` to diff behaviourally
  (Decision 7 gets the declaration covered; the emission is not). If that unwatched shape is
  `{v, conversation_id, last_seq}`, the gap is a rounding error. If it carried entries, every
  future entry kind would widen a shape nothing is watching.

**This is what answers *"what actually goes live"*, and the answer is: everything, through one
mechanism.** ADR-0146 §5 already routes `challenges`', `games`' and the Plan's events into the
conversation as system lines through the outbox. They bump the same `last_seq` and ride the same
nudge as a message. **There is no separate live-plan feature to build, and none to defer.**

The cost is stated plainly: **one extra round trip per delivered message.** A message lands in
roughly twice the round-trip time. On a four-person thread that is latency, not throughput.

### 4. Server-Sent Events, on FastAPI's built-in `EventSourceResponse`

`GET /conversations/{id}/stream`, returning `fastapi.sse.EventSourceResponse`. Sends stay ordinary
authenticated `POST`s, on the existing auth, the existing error model and `architecture.md` Part
7's mutation posture. On the client, `react-native-sse` — pure JS over `XMLHttpRequest`, zero
dependencies, no native module, and therefore no new cost against the `expo ~52.0.0` /
`react-native 0.76.9` pins this app carries.

**And one of the research's arguments for SSE does not survive Decision 3, which is worth
recording.** Its headline was that `Last-Event-ID` is carried automatically by the client library,
so the reconnect cursor is maintained for you. Under a nudge that is no longer load-bearing: the
server **always emits a nudge on connect** carrying the current `last_seq`, so resume is correct
even if `Last-Event-ID` were absent, and the header is belt and braces rather than the mechanism.
SSE therefore wins on the two arguments that do survive:

- **Zero new backend dependencies**, against a WebSocket path that starts with one and whose
  absence fails silently.
- **The channel is unidirectional by construction.** A WebSocket's bidirectionality would buy a
  second write path this design has no use for — a second place to authorize, a second place to
  validate, and a second place for [#327](https://github.com/Raketa02/Raketa/issues/327)'s
  offline-pause rule to be re-litigated. The only thing it adds is a capability we would then have
  to write a rule forbidding.

**Socket.IO is refused** because connection-state recovery, its headline reliability feature, does
not exist on a Python server. **Ably is a respectable second** and is the option to revisit if the
concurrency number moves; it is second only because it adds a vendor and a second authorization
surface to a problem that costs six dollars a month inside a process already running.

### 5. Redis pub/sub, keyed on the **conversation**, on the subscriber's own client

One channel per conversation, `conversation:{id}`, subscribed and unsubscribed as streams open and
close. **The research's per-user channel is refused**: it forces the publisher to resolve *who is
in this conversation* before it can publish, and membership is derived from accepted seats
([#221](https://github.com/Raketa02/Raketa/issues/221)) — a read added to the append path to buy
nothing. Per-conversation, the publisher already holds the id: it just appended to it.

**The bus payload is the same nudge as Decision 3**, so at-most-once delivery is adequate and
Redis Streams are not needed. A subscriber that misses a notification loses **latency, not data**.

**The subscriber constructs its own Redis client with its own timeout policy.** `redis_client.py`'s
`REDIS_TIMEOUT_SECONDS = 2.0` is passed as **both** `socket_timeout` and `socket_connect_timeout`,
and a `socket_timeout` of 2.0 makes `pubsub.listen()` reconnect every two seconds. That is
[#342](https://github.com/Raketa02/Raketa/issues/342), and this decision does not wait on it: a
long-lived subscriber owns its own connection policy whichever way #342 lands. *(Amended 2026-09-08 —
see the amendment below. #342 has landed: that constant is now two, and the subscriber's own
client is the shared module's rather than hand-rolled. What this clause asks for is unchanged.)*

**Pre-authorised fallback:** if dynamic subscribe against `redis-py` 7.4's `PubSub` proves fiddly,
one channel for everything, filtered in-process, is acceptable at this concurrency. The swap is
server-side only — no client, no data, no contract — which is why it costs nothing to defer.

### 6. The stream closes when the access token does

`ACCESS_TOKEN_EXPIRE_SECONDS` is **900**; the ALB's idle timeout is **3600**. The token therefore
expires four times inside one connection's permitted life. **The server closes the stream at
`exp`**, and the client reconnects with a fresh token through its existing refresh interceptor.

The alternative — authenticate once at connect and let the stream live — hands a revoked player up
to an hour of live delivery, against the record whose entire point is prompt revocation.

**And there is a reliability dividend worth naming:** reconnect then runs **every fifteen minutes
in production**, rather than only on deploys. The hardest-to-test path in this design cannot rot
unnoticed, because it is the path that always runs.

**The token travels in the `Authorization` header.** `react-native-sse` is XHR-backed and can set
headers; a credential in a query string would be kept in the ALB access log.

### 7. The live envelope is **generated from the contract**, and versioned from the first message

The envelope is declared as a Pydantic model on the stream route's `responses` under
`text/event-stream`, so FastAPI emits it into `components.schemas`, `openapi-typescript` generates
it, and both `check-contract-drift.sh` and `check-contract-freshness.sh` cover the declaration.
**ADR-0006 gets no exception**: the client never hand-writes a DTO mirroring a backend response,
and a live event is a backend response.

**The hole this leaves is named rather than papered over.** The checks cover the *declaration*;
nothing type-checks that what the server writes into the stream body matches it, because a stream
body is not a response model FastAPI validates. The mitigation is that **the server serialises
through the same declared model**, and the smallness of Decision 3's envelope is what makes the
residual risk acceptable.

**And it carries a `v` from the first message.** A shipped client parses that envelope until that
build is gone from phones, which is the constraint `architecture.md` Part 17 is written about.

### 8. What the load balancer cannot see, and what Redis may not take down

`GET /health` proves the process serves HTTP. It cannot see a **dead Redis subscriber**: the task
keeps accepting streams and delivers nothing, silently, to everyone on it. Three parts:

- **The subscriber runs under a supervised reconnect loop**, so the ordinary failure repairs
  itself.
- **`/health` stays about the process.** A Redis outage must never fail every task at once and take
  sign-in, onboarding and challenges down with the chat. This is the edge that makes the obvious
  fix wrong.
- **A server that knows its subscriber is down closes the stream** rather than holding a connection
  that delivers nothing — so **a chat that is not live looks not-live, instead of looking
  up-to-date.** Decision 3 is what makes that affordable: the read path is authoritative and
  independent, so losing the stream costs latency only, and screen-open and pull-to-refresh are
  unaffected.

`stopTimeout` being unset and `deregistration_delay` sitting at 300 against a 30-second graceful
timeout are **defects, not decisions**, and are filed alongside #341 and #342 rather than settled
here.

### 9. The stream is foreground-only, and that is a platform fact

iOS severs a backgrounded app's connections. The client closes the stream on background through the
existing `appState` port and re-opens on foreground — **the same code path as any other reconnect**,
so there is no second story to write.

This is coherent with [#326](https://github.com/Raketa02/Raketa/issues/326) rather than a cost of
it: with push ruled out of scope there is no out-of-app reach, so a backgrounded app was never
going to be told anything, and it catches up on foreground.

### 10. The client holds one copy, and the Play rule is untouched

A **`LiveStreamPort`** in `shared/lib/platform/`, beside `appState`, `networkState` and `location`,
with a hand-written fake in `src/test-support/platform.ts`. It **composes with `networkState`** —
no connect attempt while offline, which is #327's rule rather than a new one. On a nudge it
invalidates the conversation's query; **the Query cache remains the single copy**, which is the
posture `architecture.md` Part 7 already takes for mutations.

**`nothing in Play background-refetches` is a scope clarification, not an exception.** That rule is
written about ranked lists and the harm of *a pool reordering under a finger*. A conversation is
append-ordered; there is no ordering to lose. The rule and the chat never touch.

`frontend_player/docs/architecture.md` gains its first live-surface section, carried by the first
client build ticket rather than by this record.

### 11. A conversation pages on a cursor over `seq`, never an offset

Nothing in `backend/app` pages today — `GET /challenges` returns every challenge a player holds a
seat in, unpaged — so a convention is invented here whether or not one is decided. It is decided:
**cursor over the sequence, never an offset**, which is what makes **one query serve the cold open,
the page-back and the catch-up.**

**The parameter names and the response envelope are
[#334](https://github.com/Raketa02/Raketa/issues/334)'s**, and this convention is **scoped to the
conversation**. A repo-wide pagination standard is a decision nobody has asked for, and inventing
one here would widen the map past its destination.

### 12. What defers, and what does not

**Defers, at no future cost:** typing and presence — the only things here with no event and no
record, needing a second non-durable channel whenever they are wanted; the **unread mark inside a
conversation**, which the map holds unspecified and which Decision 2 leaves buildable as a
per-viewer position; **Redis Streams**, a swap behind the same publisher interface; **multi-AZ
ElastiCache**, a single point of failure that costs a re-subscribe because the bus holds nothing;
**message edit and delete**, which nothing asks for.

**Does not defer, because Decision 3 makes it free:** live plan-slot changes, the lock, and
membership growing on each acceptance. They are system lines in the same stream.

**Never build:** a second stream for the Chats list. One stream per **open conversation** is the
entire surface; the list is a Query cache on ordinary defaults.

## Consequences

**Easier**

- **The transport is genuinely swappable, and this record says so.** With the envelope and the
  cursor fixed, replacing SSE with WebSockets is one port in `shared/lib/platform/` and one FastAPI
  route; replacing Redis with Ably is one publisher implementation. That asymmetry is the argument
  for choosing the cheapest transport that works now rather than the one that would still be right
  at a hundred times the size.
- **Degradation is coherent and needs no design.** A severed stream, a dead subscriber, a Redis
  outage and a backgrounded app all produce the same thing: a chat that is not live, whose ordinary
  read path still works.
- **One mechanism carries messages, system lines, plan slots, the lock and membership**, so there
  are not five live features to build, test and defer independently.
- **The reconnect path is exercised every fifteen minutes**, so the part of a live surface most
  likely to ship a duplicate or a hole is the part production runs constantly.

**Harder**

- **Every message costs two round trips.** Latency roughly doubles against a design that pushes the
  body. This is the price of the self-healing property and it is paid on every message, for ever.
- **Four stream establishments per hour per open conversation**, each an HTTP request, a Redis
  subscribe and a catch-up query. Trivial at the concurrency in Context; not free, and it scales
  with connections rather than with messages.
- **The gapless allocation serialises appends per conversation on a row lock.** At two-to-four
  members that is nil. It is a real ceiling if a conversation ever holds hundreds, and this record
  would need reopening before one does.
- **A second Redis connection policy to maintain**, which cannot simply reuse
  `REDIS_TIMEOUT_SECONDS`, and which will look like an inconsistency to anyone who has not read
  #342. *(Amended 2026-09-08 — see the amendment below: #342 landed and this
  consequence retires.)*
- **The stream body is outside the contract checks.** Decision 7 covers the declaration; nothing
  proves the emission matches it. Named, mitigated, not closed.
- **The pre-authorised fallback in Decision 5 is a small invitation to take a shortcut without
  measuring.** It is bounded — server-side only — but it is an invitation.
- **A player still learns of a message by opening the app.** #326 priced that; this record inherits
  it and does not improve it.
- **Typing and presence are now explicitly the exception**, and the uniformity of Decision 3 is
  bought by excluding exactly the things that have no record. Whoever builds them builds a second
  channel with different rules.

**Neutral**

- **The concurrency number is the reopening condition**, and it is the only one. At hundreds
  concurrent, Ably is cheaper than the ECS task count this implies, and Decision 4 should be
  reopened as a measurement rather than argued again.
- **`fastapi.sse` is a young API** — 0.135.0, and this repo pins 0.136.1. Being an early adopter of
  a first-party module in a dependency already pinned is a smaller risk than adding a dependency,
  but it is not zero.

## Amendment — 2026-09-08: #342 landed, and the subscriber's own client is the shared module's

Decision 5 said the subscriber constructs its own Redis client with its own timeout policy, and
named [#342](https://github.com/Raketa02/Raketa/issues/342) as the reason it could not reuse the
one the process holds. **#342 has landed, and `REDIS_TIMEOUT_SECONDS` no longer exists.**
`app/infrastructure/redis_client.py` now names the two halves separately —
`REDIS_CONNECT_TIMEOUT_SECONDS` and `REDIS_READ_TIMEOUT_SECONDS`, both still `2.0`, for two
unrelated reasons, which is the whole argument for two names — and hands out a subscriber-shaped
client from `create_redis_subscriber_client`: connecting still bounded at the shared constant, and
**no read deadline at all**.

**What Decision 5 asks for is unchanged.** The subscriber still gets its *own* client rather than
the process's pool, and the caller still owns both ends of it: a blocking read has no business in
the pool a player's critical path draws commands from. What is gone is the hand-rolling — the
policy is written once, in the module every other Redis caller already reads.

**One consequence retires.** *A second Redis connection policy to maintain, which cannot simply
reuse `REDIS_TIMEOUT_SECONDS`* is no longer a cost. It is one module naming both halves, with one
place a later edit could re-merge them and be caught: `tests/unit/test_redis_client.py` substitutes
one constant and asserts the other did not move, because both hold the same number and nothing else
can tell them apart.

**The mechanism is confirmed on the async client, which is a sibling of the one #342's triage
read rather than a layer under it.** The triage traced `redis/connection.py` — the **sync**
client, whose `read_response` genuinely takes no timeout argument — and this codebase imports
`redis.asyncio`. There, `PubSub.parse_response` does map `block=True` to `timeout=None`, and
`Connection.read_response` reads `None` as *use the socket's* rather than as *do not time out*
(`read_timeout = timeout if timeout is not None else self.socket_timeout`). Two routes, one
outcome, and **no dependency bump either way** — which is the part of the triage that mattered and
was right.

**This record's own sentence understates it, and the correction is recorded rather than made.**
Decision 5 says a 2-second `socket_timeout` makes `pubsub.listen()` *"reconnect every two
seconds"*. It does reconnect — `call_with_retry`'s failure callback disconnects, reconnects and
resubscribes — but a connection's default `Retry` allows **zero** retries, so `failures (1) >
retries (0)` and the `TimeoutError` is then **re-raised at the caller**. An idle `async for` over
`listen()` does not loop quietly; it dies. The defect is worse than the sentence describing it,
which strengthens this record's conclusion rather than weakening it, and the sentence stands as
written per this repo's rule that a record is not retro-edited.

**What dropping the read deadline costs, named here so the first subscriber inherits a choice
rather than a default.** A socket-wide read timeout is a crude liveness check as well as a
deadline: it is what noticed a connection that had died without saying so, and to a blocking read
with no deadline a TCP session severed by an idle NAT looks exactly like a quiet conversation. So
**liveness on a subscription becomes the subscriber's own to keep**, and there are three ways that
are not a socket-wide deadline — a per-read timeout the caller passes, `health_check_interval`, or
a keepalive. This record does not pick one. `create_redis_subscriber_client` deliberately does not
either, because a factory that chose would be making the decision for every subscriber that ever
uses it; what it refuses to do is leave a two-second deadline lying where it measures the wrong
thing.

**Nothing this record decides moves, and no subscriber is built.** #342 made the client usable by
one; the transport, the channel key and the envelope are still what Decisions 4 through 7 say.

## Amendment — 2026-09-11: the plan card follows the nudge, and §12's *free* needed one rule

**What was true and what was not.** Decision 3 says *there is no separate live-plan feature to
build, and none to defer*, and §12 lists *live plan-slot changes, the lock* under *does not defer,
because Decision 3 makes it free — they are system lines in the same stream.* Both sentences were
true of the **line** and were written before
[ADR-0148](0148-the-last-line-is-the-pill-and-the-plan-is-read-beside-the-game.md) §7 put the plan
on a second list, `GET /plans`, read beside the room and never inside it. Decision 10's client
half — *on a nudge it invalidates the conversation's query* — re-read the stream alone, so a phone
in the room drew *tomek.p set the place to Zabłocie* under a chip still reading `Where`, and
*tomek.p locked the plan* under a live `Lock the plan`, until the app was next foregrounded
([#405](https://github.com/Raketa02/Raketa/issues/405)).

**What changes, and it is one rule.** Decision 10 now reads: on a nudge the client invalidates
**the conversation's query, the plan list and the games list** — a nudge re-reads what the room
draws, and nothing it does not. The plan card is `(game, plan)`: the plan half is
[#405](https://github.com/Raketa02/Raketa/issues/405), and the game half is
[#406](https://github.com/Raketa02/Raketa/issues/406) — a doubles court that completed while the
room was open re-read a room that now carried a game and drew no card, because `GET /games` had
been read on the way in and held no game born a second ago; and a *we played* line moves a
standing the header reads off that list. The rule is chosen over the alternative — inspecting the
re-fetched stream for a plan line and re-reading only then — because Decision 3 is exactly why a
frame carries nothing to inspect: a trigger keyed on the line vocabulary would go stale on the
build too old to read a new code, which is the build that most needs the re-read. The stream's
opening frame is a nudge (Decision 4), so a reconnect re-reads both lists too, which is the
catch-up for free. **The cost is stated:** Decision 3's *one extra round trip per delivered
message* is three inside a room, all to short lists the room draws, and the games list is the one
folded against a clock — so the room's clock is now as old as the last nudge rather than the last
focus, the fresher of the two. The Chats list is still never re-read on a nudge; the room draws
nothing from it.

**One consequence on the writer's own phone.** `PUT /plans/…` answers the plan and the client
writes the reply in rather than refetching (ADR-0148 §8's idempotent write). A nudge-started read
can now be in flight when the next slot is recorded, land after the reply, and roll that slot back
for a second — so every plan write cancels the plan list's in-flight read first. That is not
optimism: nothing is drawn before the server answers, and what is cancelled is a read that can
only be older than the reply. The games list needs no such cancel, because a result write
invalidates rather than writes in, so a nudge's re-read and a result's re-read are the same read.

**A residual on the games half, stated rather than closed.** The accept that fills the last seat
writes `SeatAccepted` and `GamePlanned` in one transaction, and the conversation notes the game
*drawn, not announced* — no nudge, because that note moves no `seq` and Decision 3 refuses a frame
that does. Both rows land in one outbox batch in practice, so the line's nudge re-reads a room that
already carries its game; across a batch boundary the note can land after the frame, and the next
nudge or the next focus repairs it. `EVENT_DELIVERY_BATCH_SIZE` is 100, so the boundary is a
backlog rather than a Tuesday.

**Nothing else moves.** The envelope, the transport, the channel key, the gapless sequence, the
foreground rule and the *never build* list are what Decisions 2 through 12 say. The backend
already nudged on every plan line through one shared path; no route and no frame changed.
