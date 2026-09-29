# ADR-0151 — A window whose default costs you the game must outlast the gap between app opens

- **Status:** Accepted
- **Date:** 2026-09-07
- **Narrowed 2026-09-29 by [ADR-0189](0189-a-yes-books-a-court-and-the-club-is-the-seller.md) to the Classic play loop**: a game made in a group has no answer window; a card lives until its court's book-by.
- **Amends `challenges.domain.answer_window.ANSWER_WINDOW`**, which was
  [#217](https://github.com/Raketa02/Raketa/issues/217)'s adopted number and is the first
  clock in this repository to be argued for rather than inherited.
- **Does not touch [ADR-0145](0145-the-hour-is-the-agreement-and-no-booking-will-contradict-it.md)'s
  interlock**: `ENTRY_GRACE` stays at twenty-four hours, and stops citing the number that moved.
- Settles [#344](https://github.com/Raketa02/Raketa/issues/344) on the map
  [#321](https://github.com/Raketa02/Raketa/issues/321).

## Context

**The number has never had an argument behind it.** `answer_window.py` says so in its own
words — *"Twenty-four hours, and it is a product decision rather than a tuned number… AC-140's
number, and the only place it is written."* AC-140 is the source documentation's *"Challenges
hold an answer for 24 hours"*, adopted whole while the aggregate was being built. So what
follows is not the overturning of a reasoned decision; it is the reasoning that was never
supplied.

**What forced the question.** [How an invitee finds out](https://github.com/Raketa02/Raketa/issues/326)
ruled push out of scope — there is no `expo-notifications`, no device-token context, and nothing
in this repository reaches a phone its owner is not holding — and affirmed `CHALLENGE_SENT`'s
*"they'll see it the next time they open Raketa"* as literally true. It then proved a cost it
could not pay: **a seat invited at 19:00 Monday and read at 20:00 Tuesday is already lapsed.**
The invitee never had a turn, and [ADR-0142](0142-a-withdrawn-challenge-is-the-one-conclusion-the-seats-cannot-reach.md)
established that `answering_for` prices them for the silence regardless. A player who opens the
app once a day is not an edge case; it is the modal player of a sports app, and the loop breaks
at its first step for them.

**Three facts in this repository bear on it directly, and all three point the same way.**

- **`ACCEPTANCE_GRACE` has already made this move, and it changed a number by twelve.** Thirty
  minutes became six hours because *"a grace that binds only when both opponents are on their
  phones at once does not do the job it exists for — somebody is always slower to their phone."*
- **`PROPOSAL_WINDOW` already records that a window and a notification channel are coupled** —
  *"the prompt reaches nobody who has not opened the app, and shortening it without a
  notification channel reintroduces the discarded-game problem."* `challenges`' window was set
  without that coupling being examined.
- **`interest.ttl_days` is 21.** A deck yes — the *lower*-commitment signal, into a pile that may
  never be reciprocated — gets three weeks. A direct invitation, from somebody who chose you and
  arranged a court around you, gets a day.

## Decision

### 1. The window is forty-eight hours, and the rule that picks it is stated

> **A window must exceed the gap between app opens, not equal it.**

Twenty-four hours **equals** the modal period, which is what makes this a boundary condition
rather than a design flaw: a window set to the length of the thing it must outlast fails about
half the time by construction, and every fix that keeps it is working around a number chosen
badly. Forty-eight hours clears the gap by a full day, covers everybody who opens at least every
other day, and still means no court sits half-answered for more than two days. Seventy-two buys
nothing the second day did not and costs a third day of the pair block.

**Falsifier, named rather than implied** — the discipline `ACCEPTANCE_GRACE` wrote for itself as
*"an admitted hypothesis, with its falsifiers named"*: **answer rate against time since
invitation.** If answers cluster inside the first day and the second adds nothing, the second day
is not being used and the number comes back down. The second reading is the **share of seats that
lapse**, which is what the change is meant to move.

### 2. Dating the clock from first sight is refused, on four counts

[#326](https://github.com/Raketa02/Raketa/issues/326) backed this shape and explicitly did not
decide it. It is refused, and each count is already written down somewhere:

- **The recordable fact is delivery, not sight.** #326 mounts `GET /challenges` on the shell at
  `staleTime: 0` with `refetchOnWindowFocus`, so what a server can observe is *their client asked
  and this seat was in the answer* — on every foreground, whether or not the player ever looked
  at the badge, let alone opened the tab. Calling that *sight* is the naming failure this
  repository keeps refusing.
- **`answer_by` would be null until seen, and there is a written argument against that exact
  shape.** `ChallengeOpenedFromMutualInterest` is a **distinct event** rather than a nullable
  deadline *"because a nullable `answer_by` is how a later reader invents a deadline that never
  existed."*
- **The deadline is the invitation's identity.** `answering_for` keys an invitation on
  `(player_id, answer_by)` — *"that pair is what one invitation is"* — in the one read that
  prices a person. A moving deadline is a moving key.
- **The organiser's promise becomes unbounded.** A player who never opens the app would block the
  seat for ever, so a backstop is needed anyway, and the product ends with **two clocks where it
  had one**.

And it buys the modal player nothing a longer window does not.

### 3. `ENTRY_GRACE` does not move, and stops citing the number that did

`ENTRY_GRACE` is twenty-four hours and its docstring borrows this window's authority — *"A day is
what this platform already asks of a person it needs an answer from — the challenge's own answer
window."* It stays at twenty-four hours for a reason of its own: ADR-0145 made it load-bearing
through the plan clamp's interlock, which leaves *"twenty-four hours after any plannable day, the
number the grace was chosen to be."*

**So the citation is rewritten rather than left standing.** An argument that points at a fact
which has changed is worse than no argument, because it reads as agreement between two numbers
that have stopped agreeing.

### 4. `PROPOSAL_WINDOW` does not move, and the reason is the default

Silence on a proposed score **confirms**; silence on an invitation **costs you the game**. A
window whose default is benign can be short; a window whose default takes the game away has to be
long enough to actually reach somebody. That is why the two twenty-four-hour numbers stop being
the same number, and it is stated here because otherwise the next reader re-aligns them.

### 5. `CHALLENGE_LOAD`'s rungs are stated, not tuned

They count *seats awaiting your answer* at 3 / 5 / 8, so doubling the window roughly doubles the
steady-state count and the rungs bite at half the invitation rate. **They do not move in this
change.** They are a released ruleset row with their own falsifier — *answer rate by
open-challenge bucket* — that nobody has measured, and moving two numbers at once makes neither
falsifiable.

### 6. The strand keeps charging the lapse

A fourth shape was available: keep the day and exempt an unseen invitation from `answering_for`,
as ADR-0142 already exempts a withdrawn one — *"neither answered nor lapsed and absent from the
denominator."* It is refused. **Once the window exceeds the gap between app opens, silence is the
fact the strand exists to measure**: somebody who opens the app less often than every other day
genuinely is slow to answer, and the matcher sinking them is the ranking working rather than
failing. The exemption would also need *did they see it*, which §2 refused, and it breaks the
strand from the far side — [#327](https://github.com/Raketa02/Raketa/issues/327)'s *"unmeasurable
if silence is filed as judgement"* has a mirror: **unmeasurable if judgement is filed as
absence.** `answering_for` is untouched.

### 7. Two things in the tree are wrong and are corrected with the number

- **`answer_window.py`'s own warning is false in this codebase.** It says moving the number
  *"moves what every outstanding challenge already said"*. It does not: `answer_by` is stamped on
  the seat when the seat is invited and folded back off the stream, so **nothing already sent
  moves** and there is no migration. What changes is the promise made by invitations sent after
  it.
- **The sweep's narrowing survives lengthening and would not have survived shortening.**
  `may_have_lapsed` filters on `occurred_at <= now - ANSWER_WINDOW`, applying the *current*
  constant to *historical* events. Widening the window widens the filter, so seats in flight
  under the old day are recorded **up to a day later** rather than lost — and nothing observable
  changes, because a standing is derived and *"the sweep exists for the record, not for
  correctness."* That claim is tested here for the first time and pays. Shortening the window
  would have dropped lapses silently, and that belongs beside the constant.

## Consequences

- **No copy changes anywhere**, which is `the-words.md` §14's *"24 h is not a string"* paying off:
  the pre-send sheet names no duration (#241), the per-seat line renders whatever `answer_by`
  says through the duration formatter, and the mutual-yes line has no deadline clause. The number
  is spelled in exactly one file.
- **The pair rule blocks two people for up to two days instead of one**, across every sport,
  because ADR-0142 holds a pair while the challenge is `AWAITING_ANSWERS`. That is the price, and
  it is the one a reader should weigh against the loop closing at all.
- **A modal player gets a turn.** That is the whole point, and it is the first step of the loop
  this map exists to close.
- **The lapse sweep does more work per run** — it walks challenges opened up to forty-eight hours
  ago rather than twenty-four. Bounded by the same narrowing, ordered the same way, and idempotent
  as before.
- **The seeded fixtures move with it**: `app/seeds/pairs.py` builds awaiting and lapsed seats
  against this constant, so the seed's declared states are re-derived rather than re-typed —
  which is what ADR-0029's *seed through aggregates* buys.
- **`ANSWER_WINDOW` is still not configuration.** `config.py` says so by name and that is
  unchanged: it is what a player is promised, which is behaviour a domain test can observe.
- **One row for the source ledger** ([#331](https://github.com/Raketa02/Raketa/issues/331)):
  the documentation's *"Challenges hold an answer for 24 hours"* is **repo wins**, and the row
  records that the source's number was adopted without an argument and has been replaced with one.
