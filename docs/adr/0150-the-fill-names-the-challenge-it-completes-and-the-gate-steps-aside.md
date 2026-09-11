# ADR-0150 — The fill names the challenge it completes, and the gate steps aside for that one court

- **Status:** Accepted
- **Date:** 2026-09-07
- **Extends [ADR-0142](0142-a-withdrawn-challenge-is-the-one-conclusion-the-seats-cannot-reach.md)**,
  which fixed the pair rule's predicate as *a pair is held while the challenge is
  `AWAITING_ANSWERS` or `LINE_UP_INCOMPLETE`*. That predicate is what makes this decision
  necessary: it is precisely the standing this ADR has to search inside.
- **Amends [`the-play-screens.md`](../specs/matchmaking/the-play-screens.md) §9**, whose
  *"opening the builder from an accepted challenge is out of scope"* was true of the destination
  #217 drew and is not true of [#321](https://github.com/Raketa02/Raketa/issues/321)'s.
- Settles [#337](https://github.com/Raketa02/Raketa/issues/337) on the map
  [#321](https://github.com/Raketa02/Raketa/issues/321).

## Context

**Half the mechanism has been built and unreachable since it was written.**
`Challenge.invite()` fills open seats, keeps everybody already in on the side the new
arrangement gives them, refuses to remove an accepted player, refuses a send with nobody new,
dates each newly-seated player from the moment of the invite, and publishes
`challenges.seats_invited`. It has **no caller anywhere in `app/`** — no command, no use case,
no route. On the client, `BuildSeat.accepted` and `CourtSeat`'s seat type both carry a flag
documented for exactly this ticket — *"They have already said yes to a challenge this builder is
completing… they can change sides, never seats"* — and `forecast.ts` sets it `false`
unconditionally while **nothing reads it**, not even the clear badge.

**The half that was called live is not.** §9 split the feature and said *"the mechanism is
decided and live on day one; only the entry point waits"*, naming `locked_seats`, the
`FILL_SEATS` surface and `optimised_for: GROUP` as already exercised. They are — from a builder
reached through *Find a game*, where the hand-seated player is a stranger. Reached from a
challenge they cannot be, and the reason is a gate:

- `run_lineup_search._locked` resolves every locked seat **out of this search's own pool or not
  at all**, on the argument that *"the only people they could have chosen are people this
  backend showed them"*;
- `gate_of` excludes every candidate in `context.gates.open_challenge_ids`, built in
  `search_workbench` from `MatchHistoryQuery.open_challenges` — *"one row per counterpart, and a
  counterpart is everybody occupying a seat other than your own"*;
- and ADR-0142 holds that pair for the whole of `LINE_UP_INCOMPLETE`.

So everybody who accepted your half-built challenge is, by construction, absent from the pool of
the search meant to complete it. ⚡ with them locked is `locked_seat_not_available`, **every
time**. The same fact points at the send: `open_pairs_among` over the whole court would return
the court's own pairs and refuse with `AnOpenChallengeStandsWithThisPair`.

**A second asymmetry runs the other way.** `open_challenges` releases a declined or lapsed
counterpart *"immediately: their seat is open again, so they return to the deck rather than
losing a candidate they never turned down."* So somebody who said no to this challenge is back
in the pool that fills it, seatable by ⚡ or by hand — and then refused by
`NobodyIsAskedTwice` at the send, after the player chose them.

**And the commonest half-built court has no organiser.**
`ChallengeOpenedFromMutualInterest` seats its pair in the court's first two positions, which in
a doubles sport is both on side A — `LINE_UP_INCOMPLETE` **from birth**, with a whole side open,
`mode: null` and `window: null`. Its "organiser" is whoever's yes arrived second, and the
aggregate says so in writing: *"they are the organiser in the sense the aggregate means it — the
seat the court is built out from — and in no other: neither of them proposed anything to the
other."*

## Decision

### 1. Any live member may complete the line-up; only the organiser may end it

`LINE_UP_INCOMPLETE` *"is not a waiting room"* — the people who are in are in, and a
conversation between them is already open. Growing a court and ending one are different acts
and get different permissions: **the fill is every live member's, ADR-0142's withdraw stays the
organiser's.** A mutual-born pair decides that on its own, since making an arbitrary tiebreak
the only person who can finish a padel four would leave the other looking at a court they can
neither complete nor leave.

The aggregate needs no change for this: `invite` never asked who was inviting, only that the
organiser still holds a seat. What moves is the **searcher** — the seat origins cite the search
of whoever pressed it. `OriginSearchQuery.court_origin`'s `organiser_id` parameter has always
meant *the searcher*, and this is the path that makes the two visibly different; renaming it is
a build-ticket row, not a change of behaviour.

### 2. The fill names the challenge it completes, and says nothing else about the court

`POST /lineups` grows one optional field, `completing_challenge_id`. When it is present the
**sport, the mode and the locked seats are all read off that challenge**, and sending any of the
three is refused at the request's own boundary rather than made optional — a caller supplying
one is offering a second place for a fact the challenge already holds, which is the failure
`_is_a_court_that_could_exist` is written against.

This keeps `lineup_routes.py`'s *"a line-up and filling seats are one route, and they differ by
a property of the request"* exactly as it stands: this is a second such property, not a second
route. `availability_override` stays sendable — it is *this search's* week and says nothing
about the challenge — and `offered_by_search_id` / `rung` are untouched.

The alternative, letting the client send `locked_seats` alongside the challenge id, was refused
for what it makes possible: locking somebody who is not in the challenge, or forgetting somebody
who is.

### 3. The gate steps aside for that one challenge, and for nothing else

`OpenChallenge` grows `challenge_id`. `search_workbench` builds `open_challenge_ids` from every
open challenge **except the one being completed**; `OpenChallengeQuery.open_pairs_among` grows
an `except_challenge_id` so the send does not refuse a court for the pairs it is made of.

Stated as narrowly as it is meant: the gate is not weakened and its meaning does not move. It
still excludes everybody the searcher is arranging with — **except the people already sitting on
the court this search exists to finish**, which is not an exception to *one thing at a time* but
the same rule read correctly. Candidates are gated normally, and the four fail-closed gates
(block, hold, account state, mutual gender) are untouched, so somebody who has become
unreachable since they accepted still falls out.

The alternative — letting locked seats bypass the pool entirely — was refused because a seated
player with no scored row is a player the group objective cannot optimise around, and
`optimised_for: GROUP` *is* that optimisation. Redefining the gate as *open challenges with
people not on this court* was refused because it changes what the gate says on every other
surface to fix one.

### 4. Nobody who has answered this challenge is a candidate for its own fill

The same read that exempts the court excludes the challenge's `answered` set from the fill's
pool. `NobodyIsAskedTwice` stays exactly where it is, as the aggregate's backstop, and stops
being a screen anybody reaches.

The consequence is ADR-0142's argument arriving from a second direction and is recorded rather
than softened: **a lapsed invitee is unreachable in every sport until this challenge ends**, and
the withdraw is the only thing that ends it.

> **That last sentence is retracted** — see the amendment below
> ([#393](https://github.com/Raketa02/Raketa/issues/393)). This section's heading and the pool
> exclusion it describes are sound; *every sport* is not. It is left in place because three specs
> and three route descriptions quoted it, so readers have met it.

### 5. The mode is inherited or resolved; the window is never re-stamped

A challenge born with a mode keeps it — a competitive court must not have its last seat filled
by a for-fun search. A challenge with **no** mode (deck-born, mutual-born) resolves one
backend-side from the filler's declared Play intent, which is the deck's own rule
(`NO_PREFERENCE → fun`, `search.intent_read` recording the declaration as it stood). **No mode
picker appears anywhere**, and ADR-0100 keeps its silence.

The **window is stamped by `ChallengeSent` and by nothing else.** `SeatsInvited` carries none
and will not: re-stamping would move a fact other people have already answered against. A
mutual-born challenge therefore stays window-less for its whole life. What this costs is that a
newly-invited player answers against a label derived from somebody else's grid, possibly weeks
ago — and it costs little, because ADR-0145 made the **plan** the authority on when people
actually play and a `Window` is *"a label on the search, never a proposed time"*.

### 6. `POST /challenges/{challenge_id}/seats` grows a challenge

The send's shape minus the mint — `{search_id, court}` — on `POST /games/{id}/result`'s
precedent. It re-verifies the send's five facts with one changed by §3, resolves origins for the
**newly seated only** (`_still_in` already raises if a plan carries an origin for somebody
already in), and calls `Challenge.invite`.

**Each newly-seated player starts their own 24 hours**, which is not a decision this record
takes but one it affirms: `_seat_from` dates from `occurred_at` and `SeatSchema` already says
*"a seat filled later starts its own day and cannot inherit a deadline from a send it was not
part of."*

The act **fails when offline and is never sent later**, inheriting #327's feature-wide rule
without a new argument: its meaning is fixed by the moment it is tapped, because that moment is
what dates the new seats.

### 7. The entry point is ⚡ itself, and the builder is pushed on the Chats stack

On the **challenge screen**, never a Chats row — ADR-0143's surface, and #324's *"every row is a
door; every act is on the surface behind it."* The control is **⚡ Fill the seats**, the
builder's own label for the identical act, and pressing it runs the fill and pushes a builder
holding a full court and a fresh search. That is *Find a game*'s shape exactly — press, the
search runs, the builder arrives with a court on it — and it is what makes *Pick players myself*
work on the first screen rather than after a mandatory ⚡. Nothing outbound happens:
*"searching, browsing, seating, swapping and replacing produce nothing outbound"*, and the send
is still a separate press.

The route is under `/chats/…`, which lights the Chats column for free because `/chats` is a tab
root — `games` needed an `INSIDE_A_TAB` entry only because Now's root is `/`. **Nothing in this
flow calls `resetShellStack`**, which dismisses the stack and ends the Play session; the builder
is a plain push, and **the send pops back to the challenge screen**. `landOnNow`'s argument does
not transfer — *"there is nothing left to be behind: the court is gone"* is false here, where
the thing behind is the challenge you were completing and is the surface that draws the result.

The builder borrows `playSession` rather than keeping a route-local line-up, so there is one
store and one definition of a line-up. Its **working week is undefined**, already the legal
value meaning *fill against the profile's grid* and the right one, since there was no *Find a
game* on which to improvise a week. One sentence moves and the important half does not:
`playSession` now begins when the shell lays the Play stack down **or when a challenge is
re-entered from Chats**, and still ends in exactly one place.

### 8. An accepted seat is not a control

No clear badge, no press, no pool. Swapping still works, and it is the only thing that works on
them — which draws *an acceptance is to the game, not to the side* rather than writing it.
`BuildSeat.accepted` is set for the first time, and *Start over* is **absent** on a court
somebody has agreed to, on the same argument: the two acts it sits beside — discard the four,
re-arrange the four — both operate on a court nobody has committed to.

The source documentation asks for a named refusal, *"{Name} already accepted — they keep their
place."* **That sentence is never written**, because the state it refuses is unreachable, and
#324's *"no copy, no pill, no disabled control"* is the rule it loses to.

### 9. `LINE_UP_INCOMPLETE` counts open seats, because it can never count answers

`standingLine` renders *"{n} in, {m} still to answer"* from an `awaiting` count. `standing_of`
returns `AWAITING_ANSWERS` if **any** seat is awaiting, so at the rung that yields
`LINE_UP_INCOMPLETE` nothing is: `{m}` is structurally zero and the line reads *"2 in, 0 still
to answer."* `StandingFacts` takes `open` instead of `awaiting`, and both sentences count seats:
*"{n} in, {m} seats open — the chat is already open"* / *"You're in. {m} seats open, and the chat
is already open."* #221's constraint is untouched — the phrasing that would be false is still
*waiting for the rest* — and a field that could only ever be zero is what let the sentence be
wrong.

## Consequences

- **The gate now has a documented exemption, and the exemption is an input.** A reader asking
  *why does this search skip the open-challenge gate* finds `completing_challenge_id` in the
  request and this record behind it, rather than a condition somebody has to reconstruct.
  `GATE_ROSTER` is unchanged, the histogram still counts ten codes, and the exemption is a
  smaller `open_challenge_ids`, never a gate that fired and was ignored.
- **A published port grows a field.** `OpenChallenge` gains `challenge_id`, under
  ADR-0098's demand register, which is the honest price of §3 and the only place *which
  challenge* could come from — the row carries a counterpart, an origin and an instant and
  nothing that identifies the aggregate.
- **The locked players come back as ordinary rows**, which is why the builder can draw them —
  handle, level, photograph — with no second read. Bypassing the pool would have cost a
  parallel path for four seats out of four.
- **A lapsed invitee is out of that challenge's own pool until it ends** — not out of every
  sport, which is what §4 claimed and the amendment below retracts. The pair rule released them
  when their seat reopened; what still excludes them is `already_asked_at`, per aggregate.
  ADR-0142's withdraw remains far from optional furniture, and the reason is the people who
  **accepted**: they cannot leave, and it is their only exit.
- **A newly-invited player may answer against a window nobody re-derived**, and a mutual-born
  challenge has none at all. Accepted in §5 on ADR-0145's ground.
- **Three seams that were written and unreachable are reached**: `Challenge.invite`,
  `BuildSeat.accepted` / `CourtSeat`'s locked seat, and `standingLine` — the third of which was
  wrong, and could stay wrong because nothing called it.
- **`locked_seat_not_available` stops being unreachable on this path and starts meaning
  something.** With the court exempted, the only way it can now fire is that somebody in your
  line-up has been blocked, held or deactivated since they accepted — a true thing to say, and
  followed by §11 item 9's re-read rather than a payload.
- **Two members can fill concurrently.** The aggregate's optimistic concurrency decides it and
  the loser gets `NobodyNewToInvite` or a version conflict; neither writes a half-grown court,
  because `SeatsInvited` carries the whole arrangement.
- **`the-play-screens.md` §9 is amended rather than contradicted silently**, and its split
  survives with the halves relabelled: the mechanism is live, the entry point is now decided,
  and the sentence claiming the mechanism worked from a challenge was never tested because
  nothing could reach it.

## Amendment — 2026-09-10: §4's consequence held for a seat that accepted, never for one that left

**What §4 claimed.** *"A lapsed invitee is unreachable in every sport until this challenge ends"*,
credited to ADR-0142's pair rule arriving from a second direction.

**It is false, and the pair rule is the half that does not hold.** ADR-0142 §1 holds a pair while
these two are **still arranging a game**, and `players_in_it_at` — which
`EventSourcedOpenChallengeQuery.open_pairs_among` folds to answer it — keeps only seats that are
`is_live_at`. `Seat.is_open_at` is *declined, or lapsed against the clock*. So a departed invitee is
dropped from the fold and **no pair containing them is returned**, whether or not their court is
still standing and whether or not any sweep has been past.

Established on the one arrangement no test covered — a court that is **still standing** with a
departed seat on it. A padel four, one invitee accepted so the court goes on standing as
`LINE_UP_INCOMPLETE`, another's day run out unswept:

```
standing at OUTSIDE: Standing.LINE_UP_INCOMPLETE
BOB's seat live? False
pairs held: [('ALICE', 'ORGANISER')]
lapsed BOB held by the pair rule? False
```

That transcript is a probe and is regenerated by nothing.
**`test_a_half_built_court_releases_the_pair_of_a_seat_that_left` is where it lives now**, asserting
the same facts on every run, and a sibling does the decline path.

The existing tests did not catch it because they sat either side of that case: the two release tests
use **singles** courts, which have *ended* by the time they assert, so they prove the release via the
challenge ending rather than via the seat leaving; and
`test_a_half_built_court_still_stands_between_its_pair` covers a standing court but asserts the
invitee who **accepted**. #393 adds the one in between.

**What is true, and it is a different rule with a different scope.** A departed invitee is excluded
from **this challenge's own fill pool**, by `Challenge.already_asked_at` feeding
`NobodyIsAskedTwice` — *per aggregate*, and not the pair rule at all. Every other search of theirs,
and everybody else's, reaches them immediately, in any sport. So:

> A departed invitee cannot be re-asked into **this** challenge until it ends. They are reachable
> everywhere else at once.

**Why the mistake was easy, and what it does not touch.** §3's reasoning is about the players who
**accepted** your half-built court, and for them the claim is exactly right — they *are* pair-held
for the whole of `LINE_UP_INCOMPLETE`, which is the whole reason ⚡ could not finish a challenge and
the reason this ADR exists. §4 carried that consequence one seat too far. **No decision in §1–§3 or
§5–§9 depends on the retracted sentence**, and the fill's behaviour is unchanged: it was always
`already_asked_at` doing the work. What did depend on it was this record's own **Consequences**
bullet, which restated it and is corrected above.

**Cost of the error, and it is the reason this is an amendment rather than an edit.** The sentence
propagated to **fourteen** sites: two screen specs, both apps' `CLAUDE.md`, four client source
files, three route descriptions and therefore the published contract, this record's own
Consequences, and — most tellingly — `ChallengeDirectory.open_challenges_with`'s docstring, which
stated the premise correctly and then drew §4's conclusion from it anyway. #393 corrects all
fourteen in one commit, because a false claim half-corrected across two apps is the state
[#390](https://github.com/Raketa02/Raketa/issues/390) was filed to clean up.

**Two of the fourteen were found by review rather than by the sweep**, and the reason is worth
keeping: a literal search for *unreachable in every sport* misses `unreachable in **every sport**`
and *unreachable until the challenge ends, in every sport*. Emphasis and word order defeat a grep,
so the sweep that finds a claim like this has to be looser than the claim.

## Amendment — 2026-09-11: the pool over a fill had nobody to offer, and the line-up's answer now carries the pool it seated from

**What §7 promised.** Pressing ⚡ on the challenge screen *"is what makes *Pick players myself*
work on the first screen rather than after a mandatory ⚡."* It did not, and the reason is not in
this record: the builder reached from a challenge arrives on the fill's **own** record, and
`POST /lineups` returned exactly the rows it seated — *"the seated, as the rows the record and the
card were built from"*. So `pickable(candidates, members)` over that record was `{seated} − {seated}`,
and the pool over a fill court — which this record calls one of *"the remedies on this court — ⚡
and another seat"* — offered the one person just taken off a seat, or nobody
([#407](https://github.com/Raketa02/Raketa/issues/407)).

**Nothing on the client could supply a list, and that is this record's own doing.** The line-up is
bound to one `search_id`; `POST /forecasts` and the send both refuse anybody the cited search never
returned ([ADR-0108](0108-a-forecast-is-a-route-not-a-search.md) §3, `search_court_origin.py`);
and a plain `POST /searches` is gated by the very challenge being completed — the people sitting on
the court are exactly the ones it excludes, which is §3's argument read from the pool's side. On
the *Find a game* route the same defect was fixed on the client by opening the pool on the
shortlist the court was searched under; from a challenge there is no such shortlist.

**Decision: `POST /lineups` returns the pool it seated from.** The returned band is `pool_for`'s
top `K` by Fit, in Fit order, with the seated among them; `lineup.seats[].player_id` is looked up
there, which is what `LineupSeatSchema` always said. The read-back therefore *is* a list, the pool
over a fill opens on the fill's own record, and a forecast or a send citing that search may name
anybody on it. Four costs, each paid on purpose:

- **`attach` builds `K` cards rather than the seated few** — the same bound a shortlist pays for
  twenty, over a pool already truncated at `K` for the enumeration's sake.
- **Exposure counts the seated only.** The court is what was shown; the rest of the pool is shown
  only if the player opens the list, and a ⚡ that counted two dozen appearances would sink the top
  of every ranking a few fills later under the ±6 exposure adjustment
  ([`the-engine.md`](../specs/matchmaking/the-engine.md) §8). A list opened off the record is
  shown and **under**-counted — the opposite error from a shortlist, which counts every row it
  returned whether or not the player scrolled to it. Neither is a gate, and the two do not cancel.
- **`position` on a line-up's recorded row is a place in the pool and no longer a seat** — the Fit
  rank, unless a row above it was dropped because its card could not be assembled, exactly as a
  shortlist's is — and `n_returned` counts the pool while staying the redaction detector it was.
  Who sat down was a
  fact the returned band held and layer 4's winner holds only for a **complete** four — a partial
  line-up and a singles court record no winner — so **layer 4 gains `seated`**, in the order they
  were seated, beside the deepest rank it already implied. `null` on a row written before is *not
  recorded* and never *nobody*, exactly as the area code's absence is; no migration, because layer
  4 is one JSON column.
- **`the-two-contracts.md` §1 and §5 move**, and are amended in the same commit.

**The other shape was refused.** `POST /searches` taking `completing_challenge_id` — this record's
own §2 one route over — would mint a challenge-completing shortlist for the pool to open on. It was
refused for a hole rather than for its size: a shortlist is twenty rows by **rank key**, so an
accepted seat is not guaranteed a row on it, and a pick that moved the court onto such a list would
drop a seat §8 says is not a control. The fill already has the right posture for that case —
`_locked` resolves a seat out of this search's own pool *or refuses* — and a list the seated are on
by construction is the one the fill already holds.

**What does not move.** §1–§9 stand. The seats route still resolves origins for the newly seated
only, against `RETURNED` rows by id; the gate's exemption is still an input; and nothing here
touches the ruleset corpus, whose line-up records name *who sat down* as the thing a ruleset diff
compares, which is still the right comparison.
