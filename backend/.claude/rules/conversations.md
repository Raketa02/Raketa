---
paths:
  - "app/modules/conversations/**"
  - "app/api/streaming.py"
---

# Conversations and the live channel

Moved verbatim from `backend/CLAUDE.md` (2026-09-30); decisions that are load-bearing and not obvious from the code.

- **A room is opened by a booked game, and it is told by a context that does not know it
  exists** ([ADR-0146](../../../docs/adr/0146-the-chat-is-two-contexts-and-a-system-line-is-a-code.md),
  [ADR-0147](../../../docs/adr/0147-the-live-channel-carries-a-nudge-and-the-sequence-is-what-cannot-be-swapped.md),
  [ADR-0148](../../../docs/adr/0148-the-last-line-is-the-pill-and-the-plan-is-read-beside-the-game.md),
  #541, #575). `app/modules/conversations/` is the eighth context, the platform's first
  messaging of any kind, and it is deliberately narrow: purpose-bound, never between strangers,
  never permanent. **A booked game's `GamePlanned` — one with an hour on it — is the only thing
  that opens a room** (`TellTheRoom._open`): filed under the booking's id (`booking_id`, on the
  wire and in the table — it was `challenge_id` until #575 and migration `0046`), born already
  about the game, its members the game's line-up, its end measured from the booked hour. A
  challenge's acceptance, a mutual yes and a plan open and write nothing; a game with no hour
  opens no room. **Its lifetime and its telling read booking and game events only.**
  `conversations.opened` is on **v2** (`booking_id`); v1 (`challenge_id`) is kept as
  `ConversationOpenedUnderAChallengeId` and still folds, because stored history outlives code.
  Five things about it are load-bearing and none is obvious from the code alone.
  **It is the outbox's first *writing* subscriber**, and that is ADR-0110's second
  guarantee: the candidate index went to the log because an outbox subscriber *"could never
  name the `sequence_no`"*, and a room names no event's sequence — only its own. Two
  consequences fell out of being first. `EventBatch` now takes a unit of work and **rolls
  back a failed delivery before recording the attempt**, because `mark_failed` commits the
  session the handlers ran in; and the teller is subscribed **per batch, over that batch's
  session** (`EventRuntime._dispatcher_over`), so a system line commits with the outbox row
  that caused it. Delivery is still at-least-once, so **every write here is idempotent** —
  a room per booking on a unique index, a line per **outbox row** on `source_event_id`,
  a message per `client_message_id`. **The sequence is gapless and it is the aggregate's
  own fact**: `last_seq + 1`, minted under the conversation row's lock inside the appending
  transaction — not a Postgres sequence object, which is documented not to be gapless, and
  not a timestamp, which ADR-0097 disqualified. It is **not** the stream version, and the
  two part company at row one because the opening event writes no entry. The lock is the
  one thing this suite cannot exercise: SQLite renders no `FOR UPDATE` and runs one
  connection, so that path meets Postgres or nothing. **Membership is derived, never
  stored** — the game's **current** line-up (ADR-0162: a seat can be left and re-seated, and
  the roster reads the game live), and a stored roster would be the copy that decides who may
  read the messages. **Two shapes ride one stream and no sentence is ever stored**: a Message
  is content, a system line is a code and its values, and `values` never repeats what
  membership already says, so a corrected name fixes the whole backlog — and **the read
  resolves a face for everybody the page names, not only for the roster** (ADR-0148 §4 as
  amended, #408): somebody who spoke and has since left the court is not a member, so each of
  the three reads carries `people`, one `MemberFaces` read each. `members` stays the roster
  and the gate.
  **What is refused is a table rather than prose** — `application/telling.py` names every
  event a booked game's court publishes and what this room does about it, including the ones
  that write nothing and why. One line is written today: `GAME_PLAYED`. `SystemLineCode` keeps
  the eight codes rooms opened by challenges carried, so a stored line still folds and the
  sweep can destroy those rooms. The challenges and plans that wrote them are gone (#578);
  the codes are still on the player document and the player app still renders them, so they
  leave with a player ticket rather than under it. There
  is no *Game on* line. And **a refused line is not a refused telling**: `GamePlanned` reaches
  the room, draws nothing, and is what opens it; `GameCalledOff` draws nothing and is what
  destroys it.
  **A room is for the episode, and its end is derived**
  ([ADR-0153](../../../docs/adr/0153-a-conversation-is-for-the-episode-and-its-end-was-already-on-the-wire.md)).
  A room ends on the earliest of `entry_closes_at(planned_at, starts_at=…)` — measured from the
  booked hour — and `GamePlayed` plus `CONVERSATION_GRACE`: both facts the room is **already
  told**, so it costs no new event, no new field and no new telling. **A room with no game has
  ended**: nothing opens one any more (only a challenge's first acceptance did), so it is over,
  every route refuses it and the sweep destroys it. There is no `ends_at` column: the instant
  moves as the room is told things, so **past its end every route answers
  `conversation_not_found` whether or not the sweep has run** — the sweep makes the destruction
  real, not the answer right — and `domain/lifetime.py` (`has_ended`, `ended_among`) is the one
  fold that decides *over*, for the list, the sweep and `ARoomOfYours` alike, off each room's
  own stream and no port. `CONVERSATION_GRACE` is **48 h and belongs here, not to `games`**:
  there is no interlock with `ENTRY_GRACE`, and its falsifier is written down with it.
  Two things about the lifetime are worth holding separately from the rule.
  **`conversations` imports `games`, and that arrow is deliberate** — `domain/lifetime.py`
  takes `entry_closes_at`; the reverse stays shut by `.importlinter`'s *No context knows the
  Conversation exists*, and the import is why the derivation is a module rather than a method
  on the aggregate, which is folded by a repository that knows nothing about entry windows.
  **The destruction appends no event and that is not the ledgers' exemption** — it is the end
  of an event-sourced aggregate rather than one that skips event sourcing, and a
  `ConversationDestroyed` on the stream it deletes would be a record of the destruction
  inside the thing destroyed.

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

- **The list finds a room through the reader's games** (`PlayedCourt.bookings_played_by`,
  #542): a room is filed under its game's booking, and the games a player is on name their
  bookings. Candidates only — membership is still the game's current line-up. A game's
  details find its chat by ADR-0149 §3's join over this list by `game_id`; the client finds it
  by `booking_id` (#577).
