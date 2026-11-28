# ADR-0156 — The live channel carries presence, and a heartbeat is the only honest shape

- **Status:** Accepted
- **Date:** 2026-09-10
- **Answers [#399](https://github.com/Rakieta02/Rakieta/issues/399)**, part of
  [#397](https://github.com/Rakieta02/Rakieta/issues/397).
- **Supersedes one sentence of
  [ADR-0147](0147-the-live-channel-carries-a-nudge-and-the-sequence-is-what-cannot-be-swapped.md)** —
  §3's *the channel carries a nudge and nothing else* — and **nothing else in it**. The envelope,
  the cursor rule, the gapless sequence, the token deadline, the fail-soft publisher and the
  fail-loud subscriber all stand exactly as written.
- **Reverses `cards.py`'s *"this product does not have one"***, which was true about a presence
  indicator on the day it was written and is now false. It is corrected rather than left to be
  found; what it refuses — *activity recency, at any granularity* on a **card**, about a stranger —
  is untouched and is a different question.
- **Does not reopen the SSE-versus-WebSocket decision.** ADR-0147 chose the cheapest transport and
  `presentation/routes.py` argues it: *"the only thing it adds is a capability we would then write
  a rule forbidding."* Presence is the feature whose obvious home is that capability, and it lands
  here as an ordinary authenticated `POST` precisely so the argument survives contact with it.
- **Adds no table, no migration and no event.** Nothing here is durable anywhere.

## Context

**This product had no presence of any kind, by decision, and two records said so.** ADR-0147 shaped
the live channel as a nudge and nothing else — `Nudge`'s own docstring calls it *"the whole live
contract"* — and `matchmaking/domain/cards.py` states outright that *"last seen 2 hours ago"* is a
presence indicator *"and this product does not have one."*

The author has decided to build one for real rather than stub it. That decision is upstream of this
record; what this record decides is the shape, and the shape is the part that goes wrong.

**The obvious shape is a state machine, and it is the wrong one.** `POST /typing {started: true}`
and `{started: false}` is what everybody writes first, and it has exactly one failure mode, which
is the one that matters: a *stopped* that never arrives. The app is killed, the phone loses signal,
the request is dropped, the process is redeployed mid-request — and every one of those leaves a
room with a typing indicator that **nothing in the system will ever clear**, about a person who
stopped typing an hour ago. There is no reconciliation to write, because the fact was never
recorded anywhere; there is no sweep to write, because a sweep would need to know when the last
keystroke was, which is the thing the missing message was carrying.

**The second force is that presence is the first thing on this wire that is not news.** ADR-0147's
whole argument is that a frame carries *news* and never *content*: a nudge says the room moved and
the client fetches from its own cursor through the authoritative read path, so a dropped frame is
repaired by the next one for free and *may the UI render what it did not read from the read path*
stops being a rule anybody keeps. Presence has no authoritative read path to defer to. There is no
record of it, there never will be one, and inventing a read route to serve a fact that expires in
five seconds — polled by every phone in the room, once a second — is not a smaller decision than
putting the fact on the frame.

**The third is that the stream already carries one shape, and a second one must not arrive as a
guess.** A discriminator inside the JSON is a branch somebody writes, and a branch somebody writes
is a branch a shipped build does not have.

## Decision

### 1. Presence ships, and it stops at *is somebody typing right now*

`POST /api/v1/conversations/{conversation_id}/typing` → `204`, and the stream gains a second named
event carrying who is typing. Nothing else. §7 lists what stays refused.

### 2. A heartbeat, not a state machine

**The client posts while somebody is typing and stops posting when they stop.** There is no
*started*, no *stopped*, no flag on the body and no body at all. `TYPING_CADENCE` is three seconds
and is published in the route's own description.

**The TTL is the correctness mechanism, and it is the only one.** A heartbeat is a key with
`TYPING_TTL` — five seconds — on it, and the roster for a room is whatever has not expired. Nothing
deletes a key and nothing may.

This is the whole argument for the shape: **the failure mode is the indicator vanishing rather than
sticking.** Every way a client can disappear is a way a *stopped* fails to arrive, and each of them
would leave an indicator standing for ever; the same events, under a heartbeat, are indistinguishable
from *they stopped typing*, which is what they almost always mean. A design whose worst case is
*the indicator went away a second early* is available; a design whose worst case is *this room says
Ola is typing, permanently* is not.

**The TTL must exceed the cadence**, or a heartbeat expires before its successor lands and the
indicator flickers on somebody who never stopped. Five against three is most of a cadence of slack
for a slow request. The two are one decision and live beside each other in
`conversations/domain/live.py`, with the ordering asserted at import rather than remembered.

**No rate limit, and none is planned.** Writing the same key with the same TTL is the cheapest
thing this store does, and the TTL is what bounds repetition. A limiter here would be a second
mechanism guarding a cost nobody has measured.

### 3. The store is ephemeral, and it is not the bus

Two keys per room in Redis, beside the existing pub/sub and touching none of it:
`typing:{conversation}:{player}` with the TTL, and `typing:{conversation}` — a set naming who has
typed here lately, carrying the same TTL.

**The index exists because a read may not scan.** *Who is typing in this room* has to be answerable
without knowing who is **in** the room: membership is derived from whichever record is arranging
(ADR-0146 §7), and the stream has closed its database session before its first frame (ADR-0147 §6).
The alternative to an index is `SCAN` over the whole key space, once a second, per open conversation
screen.

**The index is a hint and never the answer.** A member is reported only if their own key is alive,
so a name the set has not dropped costs one slot in an `MGET` and can never produce a false
indicator — which is what lets the read be a pure read that repairs nothing and races nobody.

**Presence never reaches Postgres.** It is ephemeral by definition, and a durable row for it would
be the one fact in this context that outlives the room it is about.

### 4. The typing frame moves no sequence, and that is the invariant

**A typing frame is not an entry.** It appends nothing, locks nothing, commits nothing, and the
gapless per-conversation allocator ADR-0147 §2 built is never asked for a number. The heartbeat's
use case loads the room **to read** and not to append, so the row's `FOR UPDATE` — the thing that
makes `last_seq + 1` gapless under two people typing at once — is not taken by the very act of
typing.

The frame carries `{v, conversation_id, player_ids}` and no `last_seq`, because there is nothing it
could honestly put there. **The room's `last_seq` is unchanged after any number of heartbeats**, and
that is asserted at the use case and again over HTTP.

**It carries the people and not a name**, exactly as every system line does: the client fills
handles from the membership it already holds, so a corrected nickname fixes the indicator for free.
**A list**, because a group chat has more than one possible typist and the client draws one
indicator either way. **The order is fixed by the sender** — a set iterated by whatever the store
returned would put ADR-0105's problem on a wire.

**The reader is filtered out of their own room's frame**, on the way out, in the stream that knows
whose it is. Without it the composer draws an indicator for the person using it.

### 5. The kind is the SSE `event:` name, and `LIVE_CHANNEL_VERSION` does not bump

`event: nudge` and `event: typing`. **A client subscribes per name, so a frame it has never heard
of is ignored by construction rather than by a branch** — which is what makes a third event, one
day, additive for every phone already in the world. A discriminator inside the JSON would hand that
back to whoever remembers to write the `else`.

**The version does not move**, and saying so is part of the decision. An installed client listens
for `nudge`, never hears the new name, and parses exactly the shape it shipped with. Bumping `v`
would tell every phone in the world that the envelope it reads had changed when it had not.

**Naming an event costs the declaration back, and it is bought back.** Setting `event:` means
yielding a `ServerSentEvent`, and the framework reads any of those as *this route builds its own
frames* and documents an opaque `data: string`. Left alone, adding this feature would have **deleted
`LiveNudgeSchema` from `components.schemas`** — a contract change nobody asked for, arriving at a
shipped client as a deletion. So `app/api/streaming.py` reads a `ServerSentEvent` **subclass** for
its narrowed `data` annotation and declares that, and both envelopes are generated as before
(ADR-0006 still gets no exception). The check on the way out moves rather than disappearing: a frame
is validated by pydantic where it is constructed, and `LiveFrame.event` is a **closed set**, so a
third kind is added in one place rather than spelled correctly at a call site — and the API suite
reads the `event:` lines off the wire and asserts both names arrive. **What no check covers is the
document**: the SSE item schema's `event` is a bare string the framework writes, so the names reach
a client through the route's description and through nothing generated. That hole is named here
rather than closed.

### 6. Two ports, and they do **not** fail in opposite directions

The heartbeat write fails **soft**, like `NudgePublisher` and for a stronger version of its reason:
a lost nudge costs a room its liveness, and a lost heartbeat costs one second of a courtesy.

The roster read fails **soft too**, and this is a deliberate departure from the pattern beside it
rather than an oversight. ADR-0147 §8 makes a subscription fail loud because *a subscription is the
room's liveness* — a connection held open delivering nothing is the failure that looks like a quiet
room. A roster is not that. It is a courtesy read, issued from inside a live stream **on the command
client**, which is the one with a two-second deadline; a store that is merely slow would therefore
close every healthy stream on the platform, once a second, to report that nobody is typing. A stream
whose nudges are flowing **is** live, and closing it says something false about the half that works.

An unreadable roster reports nobody typing — the same answer a quiet room gives, which is the
collapse `fail_soft_ledgers.py` argues for and the reason it is safe here rather than indefensible
as it would be for a gate.

**One departure from the wrappers beside it, too:** the roster's wrapper complains on the
**transition** into failure rather than on every read. Everything else that fails soft in this
repository is asked at human pace; this is asked once a second for the life of a stream, and a line
per read would turn one outage into a log entry per second per screen. The wrapper is built per
stream, so *first failure, then quiet until it works again* is one line per stream per outage.

### 7. What stays refused

- **Read receipts and `seen_at`.** Who has read what is durable by nature — the point of it is that
  it survives — which is the opposite of everything above.
- **Online, and last-seen.** Both are presence that outlives the moment, both are a fact about a
  person rather than about a room they are already in, and `cards.py`'s refusal is about exactly
  that: a stranger's activity recency, at any granularity, on a card. It stands.
- **A second stream for the Chats list.** `routes.py` says there is not one and there will not be
  one, and a typing indicator on a list of rooms is what would ask for it.
- **A bidirectional socket.** See the header.

Each of these is refused on the same property: nothing in this record is stored, so there is nothing
here for one of them to be built out of.

## Consequences

**A typing indicator works, and its worst failure is that it disappears.** A killed app clears
within five seconds, having sent nothing and told nobody. That case is asserted for its own sake in
`tests/api/test_conversation_stream.py`, because it is the entire reason the shape is a heartbeat.

**The stream asks the store once a second, per open conversation screen, whether or not anybody is
typing.** This is the price of a clear that has no event behind it, and it is stated rather than
hidden: `TYPING_CHECK` is the first number to revisit if the ephemeral store shows pressure, and it
is why the roster read is one keyed lookup rather than a scan. A push design would buy latency on
the *arrival* and would still need this timer for the *clear* — plus a second frame kind on the bus,
a widened subscriber port, and a cached set whose staleness is a second bug. One mechanism where
that is three.

**An indicator can be up to `TYPING_CHECK` late in both directions**, appearing and going away. A
second is the number chosen; a second is also what a person notices, and it is the honest cost of
not putting presence on the bus.

**The follow loop grew a second clock, and the subscription had to stop being cancelled.**
`asyncio.timeout` around `anext` cancels it, and a cancelled `anext` finishes the subscriber's
generator — harmless when the only deadline was the last one the loop would ever wait, and fatal
once there is a shorter one firing every second. The pull is now awaited as a task that outlives a
timed-out wait, and cancelled and awaited before the subscription is closed. That is a real
increase in the delicacy of the one piece of async in this context, and it is the change most
likely to be got wrong by the next person editing it.

**Nothing was added to `absent_providers.py`, and that is a deliberate divergence from #399.**
`NobodyIsFollowing` exists because a seed run and a command-line outbox drain genuinely **append to
rooms** with no phone attached, and both call the publisher explicitly. Nothing outside a request
writes or reads a typing heartbeat — there is no seed, no job and no drain that types — so a null
object here would be a class with no caller, which is a claim nothing keeps. The acceptance the
ticket wanted from it is asserted directly instead: with the ephemeral store unreachable, the app
runs, the heartbeat answers `204`, the stream stays open and nobody is ever reported typing.

**The client has to regenerate.** `openapi.player.json` gained a path and a schema and changed the
stream's item to an `anyOf`; `LiveNudgeSchema` is untouched and still generated under its own name,
so what a shipped build parses is unchanged. `make gen-api` and the drift check are the client
ticket's, per #399's own handoff.

**`the-loop-screens.md` §3.6 gains a third live-surface state and `the-words.md` §24 gains the
sentence a pulsing dot cannot say.** The indicator is announced **politely**: it is a courtesy about
somebody else's fingers, and interrupting a listener mid-message to deliver it would be the loudest
possible way to say the least important thing on the screen.
