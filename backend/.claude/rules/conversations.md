---
paths:
  - "app/modules/conversations/**"
  - "app/api/streaming.py"
---

# Conversations and the live channel

Moved verbatim from `backend/CLAUDE.md` (2026-09-30); decisions that are load-bearing and not obvious from the code.

- **A room is opened by the first acceptance, and it is told by contexts that do not know
  it exists** ([ADR-0146](../../../docs/adr/0146-the-chat-is-two-contexts-and-a-system-line-is-a-code.md),
  [ADR-0147](../../../docs/adr/0147-the-live-channel-carries-a-nudge-and-the-sequence-is-what-cannot-be-swapped.md),
  [ADR-0148](../../../docs/adr/0148-the-last-line-is-the-pill-and-the-plan-is-read-beside-the-game.md)).
  `app/modules/conversations/` is the eighth context, the platform's first messaging of any
  kind, and it is deliberately narrow: purpose-bound, never between strangers, never
  permanent. Five things about it are load-bearing and none is obvious from the code alone.
  **It is the outbox's first *writing* subscriber**, and that is ADR-0110's second
  guarantee: the candidate index went to the log because an outbox subscriber *"could never
  name the `sequence_no`"*, and a room names no event's sequence — only its own. Two
  consequences fell out of being first. `EventBatch` now takes a unit of work and **rolls
  back a failed delivery before recording the attempt**, because `mark_failed` commits the
  session the handlers ran in; and the teller is subscribed **per batch, over that batch's
  session** (`EventRuntime._dispatcher_over`), so a system line commits with the outbox row
  that caused it. Delivery is still at-least-once, so **every write here is idempotent** —
  a room per challenge on a unique index, a line per **outbox row** on `source_event_id`,
  a message per `client_message_id`. **The sequence is gapless and it is the aggregate's
  own fact**: `last_seq + 1`, minted under the conversation row's lock inside the appending
  transaction — not a Postgres sequence object, which is documented not to be gapless, and
  not a timestamp, which ADR-0097 disqualified. It is **not** the stream version, and the
  two part company at row one because the opening event writes no entry. The lock is the
  one thing this suite cannot exercise: SQLite renders no `FOR UPDATE` and runs one
  connection, so that path meets Postgres or nothing. **Membership is derived, never
  stored** — the challenge's accepted seats until the line-up completes, the game's
  **current** line-up after (ADR-0162: a seat can be left and re-seated, and the roster reads
  the game live either way), one rule read against two records, and a stored roster would be
  the copy that decides who may read the messages. **Two shapes ride one stream and no sentence is
  ever stored**: a Message is content, a system line is a code and its values, and `values`
  never repeats what membership already says, so a corrected name fixes the whole backlog —
  and **the read resolves a face for everybody the page names, not only for the roster**
  (ADR-0148 §4 as amended, #408): the person a `SEAT_LEFT` line is about was never a member
  — a *no* is not an accepted seat — so each of the three reads carries `people`: the roster
  and the entries' actors and authors on the room and the row, the page's own on a page,
  one `MemberFaces` read each. `members` stays the roster and the gate.
  **What is refused is a table rather than prose** — `application/telling.py` names every
  event either half of the loop publishes and what this room does about it, including the
  ones that write nothing and why, because a builder reading only the event list would write
  a line for each. There is no *Game on* line. And **a refused line is not a refused
  telling**: `GamePlanned` reaches the room, draws nothing, and is where the room learns its
  game — as does `ChallengeWithdrawn`, whose whole effect is that the room stops existing.
  **One row carries a code *and a condition*, and it is the only one**: a mutual is the
  opening, and on a doubles court it is also half a game — both people on one side, a side
  still to fill — so that room is born with `SIDE_FORMED` at `seq` 1, the first code that
  names no actor, while a singles mutual's room gets no line (ADR-0169 §8). `Telling.only_when`
  carries that condition as a **predicate and its sentence together**, and `line_drawn_by` is
  how the handler asks — so the table stays the whole truth about what ships, and a row reworded
  cannot ship the old line green. It is not a *Game on* line by the other door: it announces no
  standing and is re-derived from nothing, an introduction written once at birth. The
  doubles/singles fact is `challenges`' own `seats_per_side`, read off the event's sport in the
  table and never respelled.
  **A room is for the episode, and its end is derived**
  ([ADR-0153](../../../docs/adr/0153-a-conversation-is-for-the-episode-and-its-end-was-already-on-the-wire.md),
  [ADR-0164](../../../docs/adr/0164-a-plan-is-the-challenges-and-a-room-without-a-game-lives-as-long-as-its-challenge.md)
  §6). A room **with a game** ends on the earliest of `entry_closes_at(planned_at)` and
  `GamePlayed` plus `CONVERSATION_GRACE` — both facts the room is **already told**, so it
  costs no new event, no new field and no new telling, and the anchor is `Game.planned_at`
  and never the plan's agreed point, which two people could walk forward by tapping a chip.
  A room **without a game has ended exactly when its challenge is over** — `DECLINED`,
  `LAPSED`, `WITHDRAWN` — read on every read through `ArrangingCourt.over_among`, the port
  its membership already comes from: the adapter folds the standing with `challenges`' own
  `ENDED` and a set of ids crosses the port, so the application layer never learns what a
  standing is; a withdrawal destroys it in the same act. **There is no departure shelf.** ADR-0153 §3's *48 h after the last
  membership line when it was a departure* read the order the answers arrived in — `B yes →
  D yes → C no` closed a room under the three people still in it, `B yes → C no → D yes`
  never did — and a fill after it opened a fresh room with no history; a fill now continues
  the **same** room. There is no `ends_at` column: the instant moves as the room is told
  things, so **past its end every route answers `conversation_not_found` whether or not the
  sweep has run** — the sweep makes the destruction real, not the answer right — and
  `application/lifetime.py` is the one seam that decides *over*, for the list, the sweep and
  `ARoomOfYours` alike, asking the port about the rooms without a game and nothing about the
  rest. `CONVERSATION_GRACE` is **48 h and belongs here, not to `games`**: there is no
  interlock with `ENTRY_GRACE`, and its falsifier is written down with it.
  Three things about the lifetime are worth holding separately from the rule.
  **`conversations` imports `games`, and that arrow is the second one to run this way** —
  `domain/lifetime.py` takes `entry_closes_at`, exactly as `plans` takes `PLAN_HORIZON`
  (ADR-0148 §8); the reverse stays shut by `.importlinter`'s *No context knows the
  Conversation exists*, and the import is why the derivation is a module rather than a method
  on the aggregate, which is folded by a repository that knows nothing about entry windows.
  **The destruction appends no event and that is not the ledgers' exemption** — it is the end
  of an event-sourced aggregate rather than one that skips event sourcing, and a
  `ConversationDestroyed` on the stream it deletes would be a record of the destruction
  inside the thing destroyed. **And the coupling `domain/lifetime.py` used to state between
  `ANSWER_WINDOW` and `CONVERSATION_GRACE` went with the shelf it existed for** — it kept a
  departure from destroying a court somebody was still entitled to accept into, and a room
  that lives as long as its challenge cannot be destroyed under an open seat by any number.
  `lifetime.py` says so where the coupling was written down.

- **The live channel carries a nudge and a typing frame, and nothing else is on the wire**
  ([ADR-0147](../../../docs/adr/0147-the-live-channel-carries-a-nudge-and-the-sequence-is-what-cannot-be-swapped.md),
  [ADR-0156](../../../docs/adr/0156-the-live-channel-carries-presence-and-a-heartbeat-is-the-only-honest-shape.md)).
  `GET /conversations/{id}/stream` is the platform's **first real-time surface**, and it is
  Server-Sent Events on FastAPI's own `EventSourceResponse` — **zero new dependencies**,
  against a WebSocket path that starts with one and whose absence fails *silently*, since
  `uvicorn` is pinned without `[standard]` and would refuse the upgrade rather than erroring.
  Six things about it are load-bearing. **The frame is
  `{v, conversation_id, last_seq}` and never content**: the client fetches from **its own**
  high-water mark through the ordinary read path, so a lost frame is repaired by the next
  one for free, and *whether the UI may render what it did not read from the authoritative
  path* stops being a rule anybody keeps and becomes a thing the wire cannot express. **One
  mechanism carries messages and system lines alike** — a send publishes after its commit,
  and the room teller publishes after each line it writes, so there is no separate live-plan
  feature to build and none to defer. **Fan-out is Redis pub/sub keyed on the
  conversation**, on the subscriber's **own** client — the process's second, from
  `create_redis_subscriber_client`, whose read has no deadline because on a subscription
  waiting *is* the operation (#342). **Publisher soft, subscriber loud**: a publish happens
  after the entry is durable so an outage costs a room its liveness and never a message,
  while a dead subscriber **closes the stream**, because a chat that is not live has to look
  not-live. `/health` stays about the **process** for the same reason — a probe that pinged
  Redis would take sign-in down with the chat. **The stream closes at the access token's
  `exp`**, which keeps revocation prompt and makes reconnect run every fifteen minutes in
  production rather than only on deploys, so the hardest-to-test path cannot rot unnoticed;
  the gate and the first frame run in a **dependency**, before the response starts, which is
  also where the request's database session is closed so a fifteen-minute stream holds no
  connection. And **the envelope is declared on the route and generated** — ADR-0006 gets no
  exception — which needed `app/api/streaming.py`, a dated shim for a framework bug that
  drops a stream's item type on every `include_router`. The hole that remains is named: the
  checks cover the *declaration*, and nothing proves the emission.
  **The second frame is presence, and a heartbeat is the only honest shape for it**
  ([ADR-0156](../../../docs/adr/0156-the-live-channel-carries-presence-and-a-heartbeat-is-the-only-honest-shape.md)).
  `POST /conversations/{id}/typing` is a `204` gated exactly like the send — membership, then the
  hold, because an indicator is drawn on other people's screens — and there is deliberately no
  *stopped*: every way a client can vanish is a way a *stopped* fails to arrive, and each of them
  would leave a room saying somebody is typing for ever. **The TTL is the correctness mechanism and
  the only one**: `TYPING_TTL` sits above `TYPING_CADENCE` in `conversations/domain/live.py` with
  the ordering asserted at import, and the roster for a room is whatever has not expired. The store
  is Redis and **never Postgres** — a durable row would be the one fact here that outlives the room
  — with an index set beside the per-typist keys so a read is one keyed lookup and never a scan;
  that index is a **hint**, since a member is reported only if their own key is alive. **The frame
  moves no sequence**, which is the invariant: the heartbeat loads the room `to_read`, so the
  `FOR UPDATE` that mints a gapless `seq` is not taken by the act of typing, and it carries
  `player_ids` sorted by the sender with **the reader filtered out on the way out**. **The kind is
  the SSE `event:` name** — `nudge` and `typing` — so an unknown frame is dropped by the transport
  rather than by a branch, and `LIVE_CHANNEL_VERSION` **does not bump**. Naming an event costs the
  declaration back and it is bought back: the framework reads any `ServerSentEvent` as *this route
  builds its own frames*, so `app/api/streaming.py` reads the narrowed `data` off `LiveFrame`
  instead — without it, adding this would have deleted `LiveNudgeSchema` from `components.schemas`.
  And **this pair does *not* fail in opposite directions**: the roster read fails soft like the
  heartbeat, because it is a courtesy read on the **command** client — the one with a two-second
  deadline, asked once a second by every open stream — and failing it loud would let a merely slow
  store close every healthy stream on the platform.
