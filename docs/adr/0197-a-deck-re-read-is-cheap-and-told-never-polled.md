# ADR-0197 — A deck re-read is cheap and told, never polled

- **Status:** Proposed
  - §1 is built in the player app, on `feat/RKTA-06_games_fill_in` (a91b71bb).
  - §2's three optimisations are built in the backend on the same branch, 2026-10-12: [#702](https://github.com/Raketa02/Raketa/issues/702) (432c315b), [#703](https://github.com/Raketa02/Raketa/issues/703) (e51fc77f) and [#704](https://github.com/Raketa02/Raketa/issues/704) (f588b29a). The figures as built are under §2.
  - §3 waits on the product owner's choice of transport.
  - (0196 is taken on `feature/club_no_confirms`.)
- **Date:** 2026-10-12
- **Relations:**
  - **Builds** the mechanics' §6.4, *B is looking at that card → A's tile flips to In*, and §8.2's order (*cards with more people In rise*). Neither was reachable while a player was answering.
  - **Keeps** [ADR-0189](0189-a-yes-books-a-court-and-the-club-is-the-seller.md)'s 2026-09-30 amendment, under which the deck is *a projection, recomputed at every read and stored nowhere*. §2's request-scoped reuse stores nothing past the request.
  - **Would narrow** [ADR-0147](0147-the-live-channel-carries-a-nudge-and-the-sequence-is-what-cannot-be-swapped.md)'s *never build* list and reopen its capacity line, **if §3 is accepted**. That section says how.

## Context

**The complaint.** Player A is swiping *Picked for you*. Player B says yes to a card with A on it,
and that card gains momentum. A's deck learns of it slowly, or not until A stops.

**Why, on the phone.** The deck was re-read on focus once the read was 30 seconds old, and after each
of the player's own answers. It was never re-read on a timer, by the rule that *a read that reordered
the deck would put a different card under the thumb*.

The answers' re-read was TanStack's `invalidateQueries`, whose default throws away a read still in
flight and starts another (`cancelRefetch: true`). A player answering faster than the deck is read
therefore **never saw a read land**. Each answer cancelled the read the previous one asked for. B's
yes waited for A to stop swiping, and the server did every cancelled read's work all the same.

**Why, on the server.** A deck read rebuilds the whole deck on every request. It replays:
- every dealt proposal's event stream;
- every person's profile and rating streams, several times over, because each adapter loads its own;
- the rescue candidates.

It also signs each face's photo URL and computes the overlap grid for every card. Nothing is cached
and there is no rate limiter.

Measured in-process against the local Docker stack, as the CPU and SQL statements of one
`GET /pools/{id}/deck`, median of 15:

| The reader's deck | CPU per read | Statements | Photo signing | Event-store loads | Overlap grid |
| --- | --- | --- | --- | --- | --- |
| 47 dealt, 33 shown, 13 people | 171 ms | 256 | 74 ms | 57 ms | 40 ms |
| 12 dealt | 112 ms | 209 | 57 ms | 43 ms | 8 ms |
| 16 dealt | 90 ms | 107 | 48 ms | 25 ms | 5 ms |
| 6 cards, no photos | 28 ms | 55 | — | 11 ms | 4 ms |

A segment the reader's intent does not show costs the same as the one it does, because every shown
segment is computed for its count.

**Why that is a concurrency problem rather than a latency one.**
- Production runs **one gunicorn `UvicornWorker` per task** (`startup.prod.sh`, `GUNICORN_WORKERS`
  unset) at `cpu 512`.
- A CPU-bound handler holds the task's only event loop. **Every request on the task waits behind
  it** — chat, answers, payments.
- At the measured figures, one task serves roughly 6–11 deck reads a second at best, and fewer on
  half a vCPU, before anything else.
- Each read also holds one of the process's 5 + 10 pooled connections for its whole length. In a
  deployed network, every statement is a round trip.

Anything that makes more phones read the deck — a pull, a faster re-read, a live nudge — multiplies
this cost.

**Polling was weighed and refused.** Every open deck would pay for a full rebuild every few seconds
whether anything changed or not. At launch concurrency that is the dominant load on the task, spent
mostly on nothing.

## Decision

### 1. The phone re-reads in turn, and never swaps the card under the thumb (built)

- **An answer's re-read lets a read already in flight land, and sends one more after it.** The read
  in flight may predate the answer. Every answer that settles meanwhile shares that one more
  (`readAgainInTurn`). Each query waits only for its own read, so a deck never waits for a Fill in
  that is retrying. This adds no request; it removes the cancelled ones.
- **The card on top stays on top while it is still dealt.**
  - A read redraws it in place, so a tile flips to **In** under the reader's eyes (§6.4).
  - The cards behind take the server's order, so the game that gained momentum is the next card up
    (§8.2) and is never swapped in under the thumb.
  - A notice's card still goes first, and a card *Undo* takes back goes back on top. A card no longer
    dealt still leaves.
  - **A pull keeps the top card too.** That is a product call, open below.
- **A card whose answer is still on its way is hidden.** A read that set out before the answer reached
  the server still deals it, and since the first bullet, such reads land. The deck reads pending
  answers off the mutation cache, so this covers the deck's own answers, the details screen's, and
  the fill's booked yes. A refusal that puts the card back keeps it drawn.

With the card under the thumb held, the old reason for never re-reading an open deck is gone. What
stops a poll now is only its price.

### 2. The deck read is made cheap before anything multiplies it (built)

Three optimisations, each **pure** — every response byte-identical, photo-URL signatures aside,
since those carry the signing instant and differ on every signing anyway. Each is measured in place
against the real code and local data:

| | What changes | 47 dealt | 16 dealt | Elsewhere |
| --- | --- | --- | --- | --- |
| **a** · [#702](https://github.com/Raketa02/Raketa/issues/702) | Photo URLs are signed by **one client per process** instead of a new S3 client per signature. Presigning sends no request; building the client is the whole cost. | −54 ms CPU | −48 ms | Group page 70 → 32 ms (−52%). The same applies on every surface that draws faces. |
| **b** · [#703](https://github.com/Raketa02/Raketa/issues/703) | **A week's hours answer *is this hour ticked?* by lookup**, not by scanning every ticked hour. | Grid 40 → 8 ms | Grid 5 → 1 ms | Post a game's grid −14%; the proposer's *free for the hour*. |
| **c** · [#704](https://github.com/Raketa02/Raketa/issues/704) | **Each event stream is read once per deck read.** Today each adapter replays the same profile and rating streams again. | 256 → 137 statements, −32 ms CPU | 107 → 61 | Every removed statement is a network round trip once deployed. |
| **all three** | | **171 → 59 ms CPU (−65%)** | **90 → 29 ms (−68%)** | 6 cards, no photos: 28 → 17 ms |

**As built** (2026-10-12, the same method on the same seed decks, the container's log at
WARNING for every run so that a DEBUG line per signature counts in neither; the busy deck
is 47 dealt, 33 shown, 13 people, 59 faces; each cell the median of 15 reads, and the busy
deck's CPU read twice because run-to-run noise is about ±10 ms):

| The reader's deck | Before | after #702 | after #703 | after #704 (all three) |
| --- | --- | --- | --- | --- |
| 47 dealt | 160 ms, 257 statements | 118–137 ms | 98 ms | **56 ms, 138 statements** |
| 16 dealt, 9 faces | 72 ms, 108 | 41 ms | 42 ms | **26 ms, 62** |
| 12 dealt, 14 faces | 101 ms, 210 | 72 ms | 73 ms | **38 ms, 101** |
| 6 cards, no photos | 25 ms, 56 | 27 ms | 24 ms | **20 ms, 38** |
| A group's page | 49–52 ms, 67 | **20–22 ms** | 22 ms | 20 ms |
| Post a game's grid | 104–107 ms, 211 | 114 ms (noise) | 101–104 ms | 87 ms, 211 (not wired to §2c) |

Under cProfile, the overlap grid's share of the busy deck fell from 123 to 24 ms per read
(§2b). The deck's response is byte-identical before and after apart from each photo URL's
signature and its date, which change on every signing; Post a game's grid is byte-identical.
§2c's wrapper is `ReadOnceEventStore`, built in `build_read_group_deck` alone, and every
builder it reaches takes it as an optional `event_store`.

**The bar a deck optimisation ticket clears.** It must:
- keep every response identical, shown by tests;
- show its gain with the method below on the same decks, recorded on the ticket;
- touch no contract.

**The method.**
1. Call the route in-process with an ASGI client, the reader stubbed through the `current_user`
   override.
2. Initialise only the engine, so no scheduled job runs.
3. Count statements with an engine `before_cursor_execute` listener.
4. Take CPU from `process_time` across the call, with nothing else running in the process.
5. Report the median of 15 reads after one warm read.

**Weighed and not ticketed:**
- **Reading the dealt proposals' streams in one query.** Its gain is round trips alone, which the
  local stack cannot show because its database is on the same machine. Measure it on a deployed
  environment first.
- **Snapshots or read models for profile and rating streams.** Today's longest is 11 events and the
  average under 4. They are not significant yet, and they change what is stored. Revisit when a
  measured stream length says so.

### 3. Not decided: telling a reader who answers nothing

§1 reaches a player on their next answer, pull or return to the app. It does not reach a player who
is looking at a card and doing nothing.

**The proposed shape.** When the server records something that changes a dealt game — a yes said or
withdrawn, the game filling or ending, a new deal — an outbox subscriber sends a **content-free
nudge** to each player **dealt that game**, except the one who acted. The nudge says *your deck in
this group changed*; the phone answers it with §1's read.
- **The fan-out is the card's people, not the group's.** A yes in a group of 200 reaches the handful
  dealt the game.
- **Over ADR-0147's mechanism**: SSE, Redis pub/sub, Postgres the only truth, the stream open only
  while Games is on screen in the foreground.
- **But one Redis subscriber per process, routing to that process's streams**, instead of one
  subscriber connection per open stream. That is what lets one task hold thousands of open decks.
  ADR-0147 §5 already allows one channel filtered in process.
- **Latency** is the outbox's poll (at most 1 s) plus one §2 read.

**The choice it waits on.** ADR-0147 sized live connections at *low tens* and said to reopen a
managed service such as Ably at *hundreds*. An open-deck stream at launch concurrency is past that
line. **Self-hosted, as above, or managed** is the product owner's decision, on cost and operations.

Accepting §3 adds a scope note to ADR-0147. Its *never build* list gains the exception *a nudge to
the players dealt a game, while their deck is open*.

**Order:** §2 before §3. A nudge turns into reads, so the reads must be cheap first.

## Consequences

**Easier.**
- A fast swiper sees another player's yes on their next card.
- The card being read never changes under them, and its tiles flip in place.
- The server stops paying for reads nobody receives.
- After §2, a deck read costs a third of today's CPU and roughly half its statements. That is about
  three times the deck reads a task can serve, and a third of the time every other request on the
  task waits behind one.
- §2a speeds every screen that shows faces, not just the deck.

**Harder, or worse.**
- **The game that gained momentum comes up second, not first.** A player who wanted it on top now
  waits one swipe, and so does a pull — the call left open for the product owner.
- **An answer stays pending longer.** It settles after the read in flight *and* one more. Nothing on
  the deck waits on that, but anything new that does will.
- **A read that predates an answer can show counts off by one** — the segment count and the Games
  badge — until the next read lands. The card itself never shows, because §1 hides it.
- **§2c adds a request-scoped cache: a new seam that must never reach a write path.** A use case that
  appends and then reloads in one session must see its own events, so the cache belongs to read-only
  composition alone.
- **§2a holds signing credentials for the life of the process.** They rotate only with a restart, as
  the settings that carry them already do.
- **The figures are the local stack's**, on a development machine. A deployed half vCPU is slower,
  and its database round trips are not measured here.
- **Until §3 is decided and built, a reader who answers nothing still waits** for a pull, an answer
  or a return to the app. Nothing here reaches a closed app; push does that, and today it is inert on
  phones.
