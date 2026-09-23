# ADR-0164 — A plan is the challenge's, and a room without a game lives as long as its challenge

- **Status:** Accepted
- **Date:** 2026-09-13
- **Supersedes, by named sentence:**
  [ADR-0144](0144-a-plan-is-the-games-and-the-third-slot-is-the-lock.md) §*A plan is the game's*'s
  *"We will make a Plan the plan of one game, identified by that game's id"* — it is the plan of
  one **challenge**, identified by that challenge's id, and the game the challenge becomes inherits
  it; and the same section's *"A challenge that has not completed its line-up therefore has an open
  conversation and no plan. Two of four may not write down Saturday at 18:00 while two seats are
  unanswered"* — they may write it down; what they may not do is **lock** it (§5). ADR-0155's note
  under ADR-0144's *There is no lock* — *"there is still no plan before the line-up completes, so
  a four still cannot be locked by two"* — is answered the other way round: there is a plan, so
  the guard the source documentation's §5.3 asked for (*a four cannot be locked by two*) is
  **implemented**, for the first time reachable; ADR-0144's consequence *"not implemented,
  because it cannot be reached"* is superseded with it.
  [ADR-0153](0153-a-conversation-is-for-the-episode-and-its-end-was-already-on-the-wire.md) §3's
  *"the room that never becomes a game gets the same number, and stops living for ever"* — it gets
  **no number**: a room without a game has ended exactly when its challenge is over, and not a
  grace after a departure (§6).
- **Amends** [ADR-0148](0148-the-last-line-is-the-pill-and-the-plan-is-read-beside-the-game.md)
  §7: `GET /plans` is still the only plan read and is still read *beside* the game, never inside
  it — but it lists **every court the reader may plan**, written or not, and the join is by
  **challenge id**, which `GameSchema` and the conversation both already carry; and §8: the four
  writes are addressed by `challenge_id`, the horizon is `PLAN_HORIZON` past the row's **anchor**
  rather than past `planned_at`, and the lock gains a refusal. **Adds one arrow**: `plans` reads
  `challenges` through a port, as it reads `games` (ADR-0148 §8's permitted direction);
  [ADR-0145](0145-the-hour-is-the-agreement-and-no-booking-will-contradict-it.md) §4's check —
  `games` must not import the Plan — is untouched.
- **Leaves standing** [ADR-0155](0155-the-plan-gains-a-lock-and-locking-is-an-act-rather-than-a-count.md)
  whole — the lock is an act, it freezes nothing, there is no unlock — and
  [ADR-0146](0146-the-chat-is-two-contexts-and-a-system-line-is-a-code.md) §7 whole: membership
  is still the challenge's accepted seats until the line-up completes and the game's line-up
  after, and nothing here stores it. [ADR-0157](0157-the-conversation-header-names-its-people-by-their-stems-and-says-which-rung-the-game-is-on.md)
  stands too: the header's state word and the *Details* door are the game's, and a room without a
  game still draws the sport alone.
- Settles the first half of [#420](https://github.com/Raketa02/Raketa/issues/420); built by
  [#422](https://github.com/Raketa02/Raketa/issues/422),
  [#423](https://github.com/Raketa02/Raketa/issues/423) and
  [#425](https://github.com/Raketa02/Raketa/issues/425). Grilled 2026-09-13.

## Context

**The author found it testing a padel four.** The organiser sends to three; one accepts; the room
opens; and the two people who have now agreed to play have **nothing to plan on**. The Plan card is
absent until the last of the four says yes — and when one of the three says no, it is absent for as
long as it takes to find a fourth. From inside the room it reads as broken: two people agreed, the
chat is open, there is no card.

It is not broken. It is ADR-0144 doing exactly what it decided: *a plan is the game's*, the room's
`game_id` is `null` until `Standing.ON`, `ON` is *every seat accepted*, and `GET /plans` answers
*which games is this player on the court of*. Every link in that chain is deliberate, and the
argument at the top of it is a good one: *"the people who would have to keep that promise have not
agreed to be anywhere."*

### The argument is about the promise, and the promise moved

When ADR-0144 was written, filling the third slot **was** the agreement — *"There is no lock.
Filling the third slot is the lock."* A slot recorded by two of four would then have been two
people agreeing for four. [ADR-0155](0155-the-plan-gains-a-lock-and-locking-is-an-act-rather-than-a-count.md)
changed that: **the count and the lock are two facts**. A filled slot is a value somebody wrote,
movable by anybody, *last write wins*, with the room's line as its only friction; the lock is the
one act that says *we are agreed*, with an actor and a moment. So the promise ADR-0144 was
protecting now lives in one place, and it is not the slots. Two of four writing *Saturday 18:00*
is a proposal in the exact sense ADR-0144 §*Three facts already decided* uses — *the card records
an agreement; it does not negotiate one* — except that until the lock, nobody has agreed anything.

### What the old shape costs, beyond the missing card

- **The room can vanish under the people in it.** ADR-0153 §3 gave a room without a game an end:
  48 h after the last departure line, unless an acceptance or a fill follows it. That reads the
  **order** the answers arrived in — `B yes → D yes → C no` closes the room two days later while
  A, B and D are still talking in it; `B yes → C no → D yes` never closes it — and it fires only on
  rooms that still have accepted players in them, because a room exists only once somebody
  accepted and nobody on a court that was never a game could leave it. A garbage collector for
  abandoned courts that only ever collects occupied ones, keyed on a coincidence of two numbers the
  module itself asks the reader not to tidy away.
- **A fill after that opens a fresh room with no history.** The record forgets the conversation
  that chose Saturday; with a plan in the picture, a newcomer would meet the slots without the
  talk.
- **Now is right and the chat is wrong.** Now draws games only — *"Challenges have one home and it
  is Chats"* — and a game exists only once the court is whole. That half stays. The half that
  fails is the chat, which is where the planning was supposed to happen.

### The author's rule

*Simplicity over rules that surprise players when the app is released.* A chat is for the people
in it; it exists while it has them; nothing about who answered in which order should decide
whether they keep it. The plan is what the chat is for, from the first yes.

## Decision

### 1. A plan is the challenge's

**We will identify a Plan by the id of the challenge it is arranging.** One challenge has at most
one room and at most one game, and both already carry `challenge_id`; it is the one id every
reader shares, so the room draws the plan by its own `challenge_id` and a game finds its plan by
the `challenge_id` it was opened from. The Plan's three recordings and its lock carry
`challenge_id`. Nothing else about the Plan moves: it is still born by being used, still has no
opening event, still stores nothing it can derive, still writes the room's lines.

**Contradicts `backend/.claude/skills/api-contract-change`'s *add → migrate → remove, not all
three at once* — but worth reopening because the rule's reason is absent.** The sequence exists
for a released mobile build that stays installed on real phones and cannot be forced to update;
there is none — only `local` runs ([`docs/environments.md`](../environments.md)) — and the drift
check is what keeps the two apps honest on the branch. So this is **a straight rename on the
wire**, one contract change. The skill's rule is not amended: it is right the day a build ships,
and from that day this sentence stops being available and every later rename is two steps.

### 2. The room draws it from its opening

**The pinned Plan card is drawn for every room**, with whoever is in it — two of four, three of
four — and not only for a room with a game. Membership does not change: the room's members are
the challenge's accepted seats (ADR-0146 §7), and only they read and write the plan. The header's
second line and the *Details* door still need a game (ADR-0157): the rung ladder is the game's,
and a room without a game still draws the sport alone above a card it now has.

### 3. Which courts a player may plan

**The Plan's one port keeps asking one question about a player — *which courts is this player
arranging, and which are history?* — and it answers about courts, not games.** A court is
plannable by a player who holds an **accepted, live** seat on it; it is *open to planning* while
the challenge is arranging (`AWAITING_ANSWERS`, `LINE_UP_INCOMPLETE`) or `ON` with its game
`AWAITING_ENTRY`, and *history* otherwise. Somebody who left a court is not on it; somebody whose
seat is awaiting an answer is not on it either.

**An invitee who has not answered does not read the plan.** The challenge is an ask to play with
these people, and it carries no moment by design; showing two people's proposed Saturday to a
third before they have said yes would turn the challenge screen into a fixed-time invite, and
the moment is negotiated by whoever is in, once they are. This is an **admitted hypothesis** —
that a yes to the people, followed by a proposal met in the room, loses fewer games than a
proposal met on the challenge screen — and its falsifier is named: *the share of late accepters
who leave within 48 h of accepting, against the decline rate*. If it is high, a read-only card on
the challenge screen is the follow-up, and the port already knows which seats are asked.

The port is answered by an adapter that folds the challenge and, for a court that has become a
game, the game — provider-publishes, in the shape every cross-context read here takes. `plans`
therefore reads `challenges` as it already reads `games`; `challenges` and `games` still import
neither the Plan nor each other's aggregates, and the import-linter contracts say so.

### 4. The horizon anchor is the send, then the court filling

A plan may name a day up to `PLAN_HORIZON` past its anchor. ADR-0144 anchored it at
`planned_at`, and ADR-0148 §8 kept `PLAN_HORIZON` in `games` so that the clamp and the entry grace
interlock (ADR-0145 §5: every plannable day leaves a day to say *we played*) — which holds once a
game exists and is undefined before one. **Before the game exists the anchor is the instant the
challenge was sent; once it exists it is the game's `planned_at`.** The anchor only ever moves **later**, so a day chosen under the first is still
valid under the second, and the day chips widen when the court fills rather than shrinking.

**The anchor rides on the plan row, and `GET /plans` lists one row for every court the reader may
plan, written or not.** The client needed the game for two things — the anchor, and the fact that
there was a plan to draw — and it now needs it for neither.

### 5. The lock waits for the court

**`lock` is refused while the court is not whole**, with a code of its own beside
`the_plan_is_not_complete`: **`the_court_is_not_whole`**, a 409, the plan's third refusal after
`plan_is_history`. This is the whole of ADR-0144's promise argument, kept in the one act
that is a promise: where, day and hour are proposals anybody on the court may make and move; *we
are agreed* is said only once everybody who will have to keep it is in. The source documentation's §5.3
guard — *a four cannot be locked by two* — which ADR-0144 declared unreachable and ADR-0155 left
unreachable, is implemented, because it is reachable now.

On the card, the lock button is **absent** while the room has no game — not disabled, on #324's
rule — and in its place one line: **`2 of 4 in — you can plan now, lock when everyone's here`**,
the count being the room's members over the court's seats. When the last seat accepts, the line
becomes the button. A lock already taken survives a later departure, as #411's rule 2 has it — *the plan, the room
and the record survive*.

### 6. A room without a game lives as long as its challenge

**A room without a game has ended exactly when its challenge is over** — `DECLINED`, `LAPSED`,
`WITHDRAWN` — derived on every read from the challenge's own standing, through the port the room
already reads its membership from, never stored. A withdrawal destroys it in the act, as today.
The departure shelf goes: no grace, no anchor on the last membership line, no dependence on the
order the answers came in. A fill continues the **same** room with its history. The lifetime
module's stated coupling between `ANSWER_WINDOW` and `CONVERSATION_GRACE` goes with the shelf it
existed for.

**A room with a game keeps ADR-0153 §2's clock** — the entry window closing, or 48 h after *we
played* — untouched, with §4's hypothesis and falsifier as they stand.

What ends a challenge that never becomes a game is [ADR-0165](0165-the-exits-a-yes-can-be-taken-back-and-a-court-is-over-when-one-is-left.md)'s;
without it, a half-built court whose organiser never withdraws keeps its room — which is exactly
what today's second answer order already does, now for both orders.

### 7. Now is unchanged

Games only. A game card appears when the court fills, and the rung ladder reads the slots that
already exist on its first read — a court whose four people filled every slot in the chat lands on
Now as *Game on*, never as *Planning*. Recorded so that nobody adds a card for a half-built court
in the name of consistency: the inconsistency was the chat's, and it is the chat that moved.

### 8. Records and copies

ADR-0144's status line and ADR-0153's name what moved. The root `CONTEXT.md`'s Plan entry says
*one challenge's*. [`the-loop-screens.md`](../specs/the-loop/the-loop-screens.md) §3.1, §3.2 and
§3.4 say the card is drawn from the room's opening, the count line where the lock will be, and
that what a player sees when the court completes is the **lock button** appearing rather than the
card. `the-words.md`'s new sentences — the count line, the new refusal — are the client ticket's.
`backend/CLAUDE.md` still says *a plan is the game's* and states the grace coupling; it documents
what is **built**, so it moves with the code in #422 and #423 rather than here.

## Consequences

- **One contract change**: `GET /plans`' row is keyed by `challenge_id`, carries the anchor, and
  exists for unwritten plans; the four `PUT` routes are re-addressed; `lock` gains a refusal.
  `openapi.player.json` regenerates in the backend ticket and the client regenerates in its own,
  so **the drift check is red between the two commits** on the branch — the author's rule is green
  at the end, not per ticket.
- **A plan can be shaped by two of four before the others are in**, and the newcomer arrives to a
  proposed Saturday they had no part in. Accepted: the lock is the mitigation, the room's lines say
  who proposed what, and any member may move any slot. The hypothesis in §3 is how we find out if
  that was wrong.
- **A newcomer after a departure meets slots without the talk that chose them.** The room survives
  a fill (§6), so the lines are there when the room is; when a room ended with its challenge and
  the court was re-sent, that is a new challenge with a new plan, as ADR-0142 §2 already has it.
- **`plans` gains an arrow.** It reads `challenges` as well as `games` — one more context the Plan
  depends on, one more import-linter contract, and a fold that walks challenge streams on every
  plan read. Bounded by the courts a player has ever been on, which is every read in this context.
- **A half-built room has no clock of its own.** It lives as long as its challenge, and until
  ADR-0165 a challenge in `LINE_UP_INCOMPLETE` lives until withdrawn. That is today's behaviour in
  one of the two answer orders, made the behaviour in both; ADR-0165 gives it an end that does not
  need the organiser.
- **The horizon before the game is shorter than after it.** A challenge that takes five days to
  fill leaves two days of choosable days until it fills, then widens. Bounded by the 48 h answer
  window and the jump; the alternative — anchoring on nothing, or on the first yes, which nothing
  records — was worse.
- **Tests that pinned the old rule move**, and they are named rather than discovered:
  `planCard`'s *is not drawn at all where the room has no game*, the conversation lifetime's
  *ends a grace later*, and every plan test addressed by a game id.
- **ADR-0144's filename stays wrong-er**: *a plan is the game's* is now false in its first word,
  and the file is linked from a dozen others, so — on its own precedent — the title is left and
  the status line says so.
