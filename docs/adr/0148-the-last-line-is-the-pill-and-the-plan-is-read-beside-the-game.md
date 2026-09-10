# ADR-0148 — The last line is the pill, and the plan is read beside the game rather than inside it

- **Status:** Accepted
- **Date:** 2026-09-07
- **Extends [ADR-0146](0146-the-chat-is-two-contexts-and-a-system-line-is-a-code.md)** into the
  contract: that record made a system line *a code and its values, never a Message with a `kind`*,
  and said the two *"share one ordered stream and one sequence number"*. This decides how two
  shapes ride one JSON list, and what each one carries.
- **Extends [ADR-0144](0144-a-plan-is-the-games-and-the-third-slot-is-the-lock.md)** into the
  contract: three slots, three events, no lock — and therefore three routes and no lock route.
  *(Its **no lock** half is amended by
  [ADR-0155](0155-the-plan-gains-a-lock-and-locking-is-an-act-rather-than-a-count.md): there is a
  fourth event and a fourth write route, and the lock is an **act** rather than a slot. Everything
  this record decides about the three slots — §8's shape, `agreed_point`, and *a slot carries its
  value and nothing else* — is untouched; `locked_at` is not on a slot.)*
- **Cites [ADR-0145](0145-the-hour-is-the-agreement-and-no-booking-will-contradict-it.md)**, whose
  scoping of ADR-0137 is **checkable** — *"`games` importing the Plan is what breaks it"* — which
  is the constraint §7 is built around rather than a nicety it observes.
- **Cites [ADR-0143](0143-the-challenge-is-the-gate-and-the-card-is-recomputed-for-the-reader.md)**
  for `read_at` at the envelope, for *nothing is re-evaluated against the reader*, and for the
  handle rule it inherited from
  [ADR-0141](0141-a-game-names-its-court-and-the-court-is-the-gate.md).
- **Cites [ADR-0147](0147-the-live-channel-carries-a-nudge-and-the-sequence-is-what-cannot-be-swapped.md)**,
  which already answered *what the live channel sends versus what a route answers*: the channel
  asserts no fact, so the two cannot disagree about one.
- **Cites [ADR-0022](0022-kernel-negative-space-and-constant-homes.md)** for constant homes, and
  **[ADR-0095](0095-block-directed-record-symmetric-effect-gates-fail-closed.md)** for the *no
  trace anywhere in any response* posture the refusals take.
- Settles [#334](https://github.com/Raketa02/Raketa/issues/334) on the map
  [#321](https://github.com/Raketa02/Raketa/issues/321).

## Context

Naming settled what these contexts *are* (ADR-0146) and the transport settled how a change
*travels* (ADR-0147). What a client asks for and what it gets was still open, and two of the
ticket's own items had gone stale in the interval:

- It asks **what a refused lock says**. ADR-0144 answered that there is no lock — *filling the
  third slot is the lock* — and that §5.3's guard *"is not implemented because it cannot be
  reached"*. There is no refusal to word. *(ADR-0155 gave the lock a destination and therefore a
  refusal after all: `the_plan_is_not_complete`, a 409. §5.3's own guard stays unreachable —
  there is still no plan before the line-up completes.)*
- It asks where a conversation row's **state pill** reads its standing from, correctly insisting it
  is *"a derived standing, never a stored status"*. Reading one at all turns out to be the
  problem — see §6.

And one constraint arrived from outside the ticket entirely. ADR-0145 scoped ADR-0137's *"no
booking, no calendar and no date field anywhere"* to `games`' record and made the scoping
**checkable**, in that record's own words: *"`games` importing the Plan is what breaks it."*
Meanwhile [#324](https://github.com/Raketa02/Raketa/issues/324) keys four of the twelve card states
— *Game on*, *Planning*, *Today*, *Needs result* — on `AWAITING_ENTRY` read against **the plan's
filled slots and the clock**. So every card in Now needs its game's plan, and the plan may not be
on `GameSchema`. That is an N+1 unless the wire is shaped for it, and a wire shaped badly here
would force ADR-0145 open within one build ticket.

## Decision

### 1. Two reads for the Chats tab, and no combined endpoint

*Challenges for you* is `GET /challenges`, already shipped and unchanged; *Conversations* is a new
`GET /conversations`. **We will not merge them.** ADR-0146's entire argument is that `challenges`
must not know a conversation exists, and a response carrying both would need a third thing to own
it — which would be the coupling that record refused, arriving through the presentation layer
instead of the domain. Two sections, two contexts, two queries, two caches.

The challenges half needs nothing from this record: ADR-0143 §7 already gave it `read_at` at the
envelope and `nickname` on the seat.

### 2. A conversation has its own id, and membership is the gate

**Its own `conversation_id`.** ADR-0144's Plan takes the game's id and that precedent pulls the
other way, but the map requires this design to *anticipate a second kind of conversation without
building one* — Around's plan chats — and keying on a challenge id forecloses exactly that. A UUID
costs one column and keeps the door open. `challenge_id` and a nullable `game_id` ride as fields,
because a row has to know which door it opens.

**The gate is membership, and nothing is re-gated.** ADR-0143 §2 applies unchanged: the four
safety gates ran over every pair of the court in the send's own transaction, and re-running them on
a read would tell a reader that something changed about somebody else — the one thing a safety gate
may never say. Membership is derived from accepted seats
([#221](https://github.com/Raketa02/Raketa/issues/221)) and only ever grows.

### 3. One read for the header and the newest page; one for paging back

- **`GET /conversations/{id}`** returns the header **and** the newest page, so members and entries
  can never disagree: they came from one fold, against one `read_at`.
- **`GET /conversations/{id}/entries?before_seq=&limit=`** pages backward and carries no header.

A client that has been away and finds a hole below the newest page pages backward through that
*same* route until it reaches its cursor. **One code path serves history and catch-up**, which is
the property ADR-0147 bought by making the cursor a sequence rather than an offset.

**No `has_more`, anywhere.** ADR-0147's sequence is **gapless**, so `seq` 1 *is* the beginning of
the conversation. A flag beside that would be the same fact twice.

`limit` defaults to **50**, capped at **100**, enforced as `Query(le=100)` so an over-large request
is a 422 by construction. **Not a silent clamp:** a route that quietly returns something other than
what was asked for cannot be told apart from a route that ran out, and that is a habit worth not
starting.

### 4. Two shapes in one union, and values never repeat membership

The entries list is a **discriminated union** — `oneOf` with an explicit `type`, generating a
TypeScript union through `openapi-typescript`.

**This is not the *one shape with a `kind`* ADR-0146 refused.** That refusal was about a single
object carrying a text field real for one arm and meaningless for the other. Two genuinely
different objects behind a discriminator is the shape that record was arguing *for*.

- **A message** carries `seq`, `author_id`, `sent_at`, `text` and §5's client id. **No separate
  message id**: `(conversation_id, seq)` already identifies it, and a UUID beside a unique key is a
  second identity for one row.
- **A system line** carries `seq`, `code`, `occurred_at`, a nullable `actor_id` and `values` — and
  one rule that keeps it honest: **`values` never repeats what membership already says.** The line
  carries `actor_id`; the client renders the handle from the members it already holds, exactly as
  `standingLine` fills `{name}` today. The handle stays true in one place, and ADR-0022's promise
  survives — the backend sends codes and values, and nobody typed *Tomek set the day*.

### 5. The client's id does two jobs, and that is why it is not a header

`POST /conversations/{id}/messages` carries a client-generated **`client_message_id` in the body**,
and returns the created message.

`challengesApi.ts` refused an `Idempotency-Key` for the challenge send because *"one open challenge
per pair"* is a rule that does not expire and a key does. A message has no such rule behind it, so
that argument gives nothing away here — but **the header precedent is not overturned either**. It
is for a key that is *only* a key. Here the same value does two jobs: it is the idempotency key
**and** the reconciliation key for an optimistic send, so the client renders immediately and
replaces its own message when the real one arrives. **One mechanism for one fact**, which is the
thing this repo consistently refuses to have two of.

It also matters for [#327](https://github.com/Raketa02/Raketa/issues/327): *a paused act is not a
failed one*, so a send that pauses offline and resumes must not become two messages. A stable
client id is what makes that retry safe.

A repeat answers **200 with the same message and the same `seq`, recording nothing** — the repo's
existing idempotency language. And returning the message is `architecture.md` Part 7's rule
(*"don't immediately refetch what you were just handed"*), with a second benefit under ADR-0147:
**the sender's own message never waits for a nudge round trip.**

### 6. The conversation row carries no state pill, because the last line is what a pill would say

The design draws one. Reading it would make the conversation ask `challenges` and `games` what they
are — the one thing ADR-0146 says it never does: *a conversation is told, and tells nothing.*

And it does not need to ask, because **it has already been told.** ADR-0146 §5 writes those
contexts' events into the conversation as system lines, so **the last entry is what a pill would
have said**, and a pill beside it would be the second place one fact is true. It also lands exactly
where #324 put the boundary: *every row is a door, every act is on the surface behind it* — and the
state-keyed surfaces are the challenge screen and the game screen, not this row.

A row therefore carries `members` (handles and photos), the sport, `last_entry` as §4's union —
**never a rendered preview string**, ADR-0022 again — and its two ids.

**Photos are affordable here where ADR-0143 refused them.** That record priced a photo per person
as the most expensive shape and refused it on a challenges list that keeps ended challenges *for
ever*. A conversation is **destroyed** 24 h after the moment it was arranging, so this list is
bounded and small. The difference is not a change of mind; it is a difference between a record and
a room.

**And read state resolves by scope rather than by decision.** The tab badge counts challenges only
([#326](https://github.com/Raketa02/Raketa/issues/326)), and the unread mark inside a conversation
is out of scope, so **nothing marks a conversation read and no field carries it.**

### 7. The plan is read beside the game, never inside it

**`GET /plans` — every plan for the games you are on the court of — and it is the only plan read.**
Now issues two reads and joins by game id; the chat screen draws the same cached list.

This is the shape ADR-0145's checkable scoping forces. The plan cannot be on `GameSchema` without
`games` importing the Plan, and a per-game plan read would be an N+1 across the whole of Now. One
list beside the other keeps the check green **and** the read cheap, and gives one plan shape to two
surfaces rather than two shapes for one fact.

The list is ordered and lifetimed like its owner, and it carries **no `read_at`** — see §10.

### 8. Three writes, one per slot; two refusals

> **Amended by [ADR-0155](0155-the-plan-gains-a-lock-and-locking-is-an-act-rather-than-a-count.md).**
> This heading read *no lock*. There is a fourth write route, `PUT /plans/{game_id}/lock`, and it
> is not a slot: it takes no body, answers the same `PlanSchema`, and adds one refusal —
> `the_plan_is_not_complete`, a 409 — to the two below. **Nothing else here moves.** *A slot
> carries its value and nothing else* is a rule about slots, and `locked_at` is on the plan
> rather than on one of them.

`PUT /plans/{game_id}/place`, `/day`, `/hour`, because ADR-0144 has exactly three events and
*setting a slot and moving one are the same event told with two sentences*.

**Writing the value already there records nothing and answers 200.** Without that the chat fills
with *Tomek set the day to Saturday* three times over, and it is the repo's own idempotency
language — *"the same value twice lands the same state and records nothing the second time."*

**Two refusals, and they are the port's one question** — *is this player on this game's court, and
is that game still open to planning*: **404 `plan_not_found`** and **409 `plan_is_history`**.

**A slot carries its value and nothing else.** No `set_by`, no `set_at`. ADR-0144 says every change
writes a system line *naming who and what*, and that those lines **are** this context's history —
so attribution on the slot would be the second place one fact is true, in a record whose own
decision is that it *"stores nothing it can derive."* The game screen draws the plan read-only and
never needed it.

The three values: **`place`**, free text capped at 120 characters, refusing an id, a lookup, an
autocomplete, a reuse and a geocode; **`day`**, a `date`, clamped to `planned_at + PLAN_HORIZON`;
**`hour`**, a `time` validated **server-side** to 30-minute steps between 06:00 and 23:00. That
validation is the point: the client offering seven chips and a grid is a convention, and **the
server enforcing it is what makes ADR-0145's *bounded chips the platform offered, never a free
instant* true** rather than something the next client could quietly break. **`agreed_point`** is a
nullable instant, derived and sent, present the moment a *day* is recorded (ADR-0145 §3), because
it is a timezone conversion the client must not redo.

**`PLAN_HORIZON` stays in `games/domain/windows.py` and `plans` imports it.** ADR-0022 governs
constant homes and the obvious move is to promote it to the kernel; the reason not to is ADR-0145's
interlock — *the clamp and `ENTRY_GRACE` interlock so that every plannable day leaves at least
twenty-four hours to say* we played. Two numbers whose **relationship is the argument**, and
promoting one across a boundary would separate them so the next person to change either cannot see
the other. The direction is the permitted one: ADR-0145's check is that `games` must not import the
Plan, and this is the reverse.

### 9. A hold stops you writing, and never stops you reading

`account_held` refuses **the send and all three slot writes**, and refuses **no read**.

The hold's own argument is that *"a hold that stops you searching but lets you send invitations is
the same hole with the blast radius pointed at other people"*, and a message is reach. But a hold
must not erase an arrangement other people are already inside; they still need to read what was
said and reach each other. **So the rule generalises: a hold stops you writing anywhere another
player sees it, and never stops you reading.** It sits beside ADR-0143 §7's forward-looking block
without contradicting it — that one is about a pair, this one is about a person.

**404 for a non-member, not 403**, on `challenge_not_found`'s argument verbatim: one code for two
cases, because separating them would answer *is this id real* about a stranger's evening.

### 10. The plan folds nothing against the clock, so Now has one clock

ADR-0143 §7 put `read_at` at the envelope *"so a client's countdowns and the standings beside them
cannot come from two different readings of the clock."* Now joins two reads, so the obvious move is
a `read_at` on each — and that is precisely what would create the two clocks the rule exists to
prevent.

**`GET /plans` carries no `read_at`.** A plan folds nothing against the clock: `slot_start`
converts recorded values through one platform zone and never consults *now*, and ADR-0145 already
holds that a plan's day and hour are *"wall-clock facts, drawn literally, never counted down."*
There is no instant for a plan to have been folded against, so the card is folded against **`games`'
`read_at`** — one clock by construction rather than by convention.

**Both conversation envelopes carry one**, and the list earns it for a reason worth writing down:
**its very membership is a fold.** A conversation is destroyed, not delisted, 24 h after the moment
it was arranging, so whether a row appears at all was decided against an instant. The detail
response carries **its own**, per ADR-0143 §7.

**And no separate `last_seq` field anywhere** — the newest entry's `seq` is it, on the detail and
on the row alike.

### 11. The list is live-only, ordered by its last entry

**Ordered by the last entry, newest first.** A chat list rises on activity, which ADR-0147 already
cleared: *nothing in Play background-refetches* is written about ranked lists and the harm of a
pool reordering under a finger, and this is neither. It rests on every conversation having at least
one entry, which holds because **the opening event is itself a system line**.

**Only live conversations are in it, because there are only live conversations.** Destruction is
the mechanism, so the list needs no filter. This is **deliberately the opposite of
`ChallengeListResponse`**, which keeps ended challenges and says so — a reader who knows one will
expect the other, and the asymmetry is the difference between a record and a room.

## Consequences

**Easier**

- **One clock in Now**, without a rule anyone has to remember, because the only response that could
  have carried a second one does not.
- **ADR-0145's check stays green under a surface that wanted to break it.** The N+1 that would have
  argued for putting the plan on `GameSchema` is answered by a second list rather than by reopening
  a record.
- **One plan shape for two surfaces**, and one entry shape for the chat and the row.
- **The optimistic send and the offline retry are the same mechanism**, so #327's *a paused act is
  not a failed one* needs nothing new at this layer.
- **The row cannot drift from the state**, because it does not hold one.

**Harder**

- **The wire was settled before the screen.** [The Chats tab](https://github.com/Raketa02/Raketa/issues/335)
  is unblocked and may find it needs a field this record did not anticipate. That is an additive
  change rather than a re-decision, but it is a real inversion of the normal order and it was
  accepted knowingly.
- **A conversation row shows no state at a glance**, which is a visible subtraction from the design.
  The last system line has to carry that weight, and a conversation whose last line is a message
  says nothing about the arrangement behind it.
- **Now costs two reads and a client-side join** by game id, in a client whose features are
  otherwise self-contained. `architecture.md` will want a word about where that join lives.
- **`plans` imports `games`**, which is a real cross-module dependency chosen over a kernel
  promotion. It is the permitted direction, and it is still a dependency somebody will question.
- **A held account can watch a conversation it may not write to**, which is a state with no copy
  written for it yet. §9 decides the rule; what the screen says about it is the tab's and the
  screen specs'.
- **Three routes for three slots** is more surface than one route with a slot name in the body,
  and the justification is entirely that ADR-0144 has three events. If a fourth slot ever existed
  this shape would grow rather than absorb it.

**Neutral**

- **No `CONTEXT.md` change.** ADR-0146 wrote both sections and this record adds no domain term —
  it decides shapes, statuses and routes, which the glossary deliberately does not hold.
- **The union's discriminator is the first `oneOf` in this contract**, so it is also the first test
  of what `openapi-typescript` makes of one. If the generated type is unpleasant, that is a
  mapper's problem and not a reason to collapse two shapes into one.
