# ADR-0146 — The chat is two contexts, and a system line is a code rather than a message

- **Status:** Accepted — **§7 narrowed 2026-09-14 by
  [ADR-0168](0168-a-member-may-leave-the-chat-once-the-game-is-behind-them.md)**: the roster is
  still derived from the court, and the room now stores **one subtraction from it** — its members'
  own exits, admissible only once the line-up can no longer move, and effective only while it
  stays so, which is read against `games` on every read rather than kept here.
- **Date:** 2026-09-07
- **Completes [ADR-0144](0144-a-plan-is-the-games-and-the-third-slot-is-the-lock.md)**, which made
  a Plan *"its own bounded context"* and then deferred: *"the context's name, its events' spelling
  and what it refuses in the glossary's own voice are owed to
  [#332](https://github.com/Raketa02/Raketa/issues/332)."*
- **Cites [ADR-0110](0110-the-index-tails-the-log-the-outbox-delivers-side-effects.md)** — *two
  subscriptions, two guarantees*. That record sent the candidate index to the **log**; this one
  sends a conversation to the **outbox**, and the reason the objection does not transfer is
  stated below.
- **Cites [ADR-0022](0022-kernel-negative-space-and-constant-homes.md)**, which is what decides
  the shape of a system line rather than taste.
- **Cites [ADR-0003](0003-transactional-outbox-for-event-delivery.md)** for the delivery
  mechanism, unchanged.
- **Amends the preamble to `CONTEXT.md` Part 1**, on that preamble's own written instruction.
- Settles [#332](https://github.com/Raketa02/Raketa/issues/332) on the map
  [#321](https://github.com/Raketa02/Raketa/issues/321).

## Context

**The root `CONTEXT.md` names no chat, no conversation, no message, no plan.**
`backend/app/modules/` has no module for any of it. The diagnosis this map starts from puts the
problem in one sentence: **the chat is three contexts wearing one word** — a conversation, a plan,
and ownership — and shipping them under that one word is how four slices become twelve. Decision 3
deleted ownership, so two are left to name.

Four accepted records already decided what these things *are* without deciding what they are
**called**: ADR-0142 gave the conversation a lifetime, ADR-0143 the challenge screen it opens
from, ADR-0144 the Plan's three slots and its status as a context of its own, and ADR-0145 the
meaning of the hour in it. Each of the last three explicitly declined to write the glossary and
named this ticket as its owner.

### The word is already double-booked

`games` uses *conversation* for the **result argument** — eight states, a client file called
`domain/conversation.ts` folding the standing and the scores on the table into what to draw — and
the same context's glossary section uses it for **the chat**: *"nothing about where, money, or the
conversation belongs here."* One word, two things, inside one paragraph.

### And `CONTEXT.md`'s preamble already answered a question three records deferred

ADR-0142, ADR-0144 and ADR-0145 each held off writing the glossary on the ground that *Part 1
documents implemented bounded contexts*. The preamble says close to the opposite:

> A context that does not appear below has no vocabulary yet — **resolve its terms into this file
> before writing it**, which is what every section from **Player profile** down was: settled in an
> accepted ADR and written here first, then built.

It also anticipates precisely this case, in a block warning written after the top of the file went
stale twice: *"a term settled and unbuilt is stated in its own section, where the reason for it
is."*

## Decision

### 1. Two contexts, two modules: `conversations/` and `plans/`

**We will ship a Conversation and a Plan as separate bounded contexts**, one module each, in the
shape every other context here takes.

ADR-0144 settled half of it. What makes them genuinely two rather than one with a seam is a
lifecycle fact neither shares: **a conversation exists without a plan.** It opens on the first
acceptance, and a challenge whose line-up never completes has an open conversation and **no plan
at all** — ADR-0144's *born by being used*. A single module would carry a nullable half its own
lifecycle contradicts, and a nullable that is *usually* absent is how a slice becomes three.

### 2. The chat takes `Conversation`; the result argument gives it up

**`Chat` is refused on `challenges`' own test.** That context is *"deliberately not called
`matches` — that word promises results, history and a played game, none of which is in scope."*
*Chat* promises messaging — free-form, between anybody, searchable, permanent — and this context
refuses all four. It is also the **tab's** name, and the tab holds challenges *and* conversations,
so a context called `chat` would name the container rather than the thing in it.

**The result side never held the word as a term.** `games` owns **Proposal**, **Correction**,
**Counter** and **Acceptance**; *conversation* appears there in prose and in one client filename.
The chat's Conversation is an aggregate with members, a lifetime and an ordered stream. **The
glossary word goes to the thing that needs it**, and `games/domain/conversation.ts` is renamed for
what it actually folds — a build-ticket row, not a second decision.

### 3. `Plan`, and the second arrival pays

Around's *plans* are a second, unrelated kind, already named in the sources beside *game chats*.
**We will take `Plan` anyway**, on a rule this glossary has already written and paid once:
`games` took `Standing` and spells `GameStanding` on the wire because *"the contract is one
namespace, and **the cost of a shared word is paid by whoever arrives second**."* Around is the
second arrival.

`GamePlan` was rejected twice over: it is an English idiom meaning *strategy*, and it is redundant
inside a context ADR-0144 defines as *the plan of one game, identified by that game's id*.
Renaming would also make an accepted record wrong — ADR-0144 says **Plan** throughout.

### 4. A system line is a code and its values, never a Message with a `kind`

The prototype puts two `kind` values on one shape. **We will not**, and ADR-0022 decides it rather
than taste: **the backend sends numbers and machine codes and never display text.**

- **A Message is content.** A player typed it; it crosses as-is; it has an author in the ordinary
  sense.
- **A system line is derived from an event.** It must cross as a **code plus its values** for the
  client to render, exactly as every standing sentence in this product already does. Nobody typed
  *Tomek set the day*.

One shape with a `kind` forces one of two failures: storing a rendered sentence, which breaks
ADR-0022 and freezes copy into history; or a text field that is real for one kind and meaningless
for the other, which every reader must then remember.

**They share one ordered stream and one sequence number.** They are two shapes in it, not one
shape with a discriminator.

### 5. A conversation is **told**, through the outbox, by contexts that do not know it exists

Its system lines are written from events published by three contexts — `challenges`, `games` and
the Plan. **We will subscribe through the transactional outbox** (ADR-0003), and the publishers
gain no knowledge of the subscriber. That ignorance is the whole of the diagnosis's argument: the
moment `challenges` knows a conversation exists, the two ship as one thing.

**ADR-0110's objection does not transfer, and it is worth saying why.** That record sent the
candidate index to the **log** rather than the outbox because *"the outbox orders by
`(created_at, id)` and mints a row id unrelated to the event's, so an outbox subscriber could
never name the `sequence_no`"* — and closed with **two subscriptions, two guarantees.** A
conversation names no event's `sequence_no`: its cursor is a **conversation-scoped sequence
number minted on append**, decided by the transport research, and ordering is therefore this
context's own fact rather than something inherited. **This is the second guarantee.**

The two alternatives are refused for named reasons. **An inline port** — the shape `challenges`
uses to open a game — would put the conversation inside the acceptance's transaction and make
`challenges` know it exists. **A read at open** would put three contexts' event vocabularies in a
read path and interleave messages with lines by timestamp, which is an ordering nobody owns.

### 6. No system line for a derived standing

`challenges` and `games` both state that **nothing announces a conclusion the record already
implies**. A system line for a derived standing is a sentence with no event behind it, so
**there is no *Game on* line** — the prototype writes that phrase four different ways and every
one of them is folded from the seats. Derived standings are drawn on the row and on the
state-detail surface, where they have exactly one place to be true.

### 7. Membership is derived, from whichever record is currently arranging

**Never stored.** The challenge's accepted seats until the line-up completes; the game's frozen
line-up after. That is one rule rather than two — **the people who have agreed to be on this court
right now** — which is what grows one acceptance at a time (#221) and then stops growing when a
line-up is *frozen at the plan*.

> **Two words superseded 2026-09-12 by [ADR-0162](0162-a-games-line-up-is-frozen-until-somebody-leaves-it.md)**: the game's **current** line-up after, and it
> no longer *stops growing* — a seat can be left and re-seated, and the roster reads the game's
> line-up live either way. The rule itself, *the people who have agreed to be on this court right
> now*, is exactly what made that a two-word change: nothing is stored, so nothing had to move.

Storing it would make *who is in this* true in a second place, and the first copy to go wrong is
the one deciding who may read the messages.

### 8. Both sections go into `CONTEXT.md` now, and the preamble loses a sentence

The preamble's rule is **ADR → glossary → code**, and its condition — *a decision* — is met four
times over. So both contexts are written now, each **saying in its own section that it is settled
and unbuilt**, which is where the preamble's own warning puts a verdict that narrow.

And the preamble stops claiming *"every section describes code that exists in `backend/app/`
today"*, because that is a per-context verdict at the top of the file — the exact thing the
paragraph beneath it says went stale twice.

## Consequences

**A conversation can be wrong about the world for as long as the outbox takes.** Somebody accepts,
the game opens, and the line saying so lands a poll later. That is the price of the publishers not
knowing, and it is the right price here — nothing in a conversation is a gate, and no act is
refused on the strength of a system line.

**Two shapes in one stream is more work for every reader of it.** The wire carries a union, the
client renders two components, and the ordering is the sequence number rather than a type. What it
buys is that no copy is ever frozen into stored history — a sentence rewritten in six months
rewrites the whole backlog, which a stored string could not.

**The result argument loses a filename it has had since #314.** The rename is mechanical and
touches a shipped, tested surface that is otherwise out of this map's scope. It is worth it: two
things called *conversation* in one codebase is how somebody eventually subscribes the wrong one.

**`Plan` will collide the day Around ships**, and this record chooses to pay then rather than now.
The glossary's precedent says the second arrival disambiguates; if Around arrives and the cost
turns out to be larger than `GameStanding`'s was, this is the record that was wrong.

**The glossary now describes two things that do not exist.** That is a first for this file, and the
mitigation is that each section says so where the reason for it is. The failure mode to watch is a
reader treating a settled-and-unbuilt section as a description of code — which is exactly what the
preamble's deleted sentence used to prevent, and what the per-section verdict now has to.

**Three accepted records deferred to a ticket rather than to the code**, and this record shows they
were right about the sequence and wrong about the principle. ADR-0142's *"Part 1 documents
implemented bounded contexts"* is not what the preamble says, and repeating it twice made it look
settled. **A precedent cited three times is not thereby true.**
