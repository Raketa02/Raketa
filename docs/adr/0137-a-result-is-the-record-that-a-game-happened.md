# ADR-0137 — A result is the record that a game happened, and the games context is event-sourced

- **Status:** Accepted
- **Date:** 2026-09-04
- **Revises [ADR-0034](0034-matches-is-a-record-and-keeps-no-history.md)** (deleted in the
  2026-08-25 reset, on `prototype/result-confirmation`): the shape is now **event-sourced**.
- **Carries forward [ADR-0048](0048-silence-confirms-a-result-and-disagreement-carries-a-score.md)**
  (same), with both clocks re-derived and one narrowing.
- **Carries forward [ADR-0049](0049-an-unscored-match-is-an-evening-not-evidence.md)** (same)
  **whole**, and strikes the clause of the root [`CONTEXT.md`](../../CONTEXT.md) that contradicts
  it.
- Settles [#303](https://github.com/Raketa02/Raketa/issues/303) on the spec
  [#302](https://github.com/Raketa02/Raketa/issues/302).

## Context

**Nothing on this platform knows that a game was played.** A `Challenge` carries a `Window` —
`TODAY`, `WEEKEND` — and never a date, a time or a court ([ADR-0100](0100-challenge-window-derived-never-chosen.md)),
so four acceptances leave no fact behind. Every empty block on the redrawn competitive card
traces back to that: `player_card.counted_games` is `OMITTED` because *the games ledger has no
provider in this build, and a zero would be an invented one*; *Last 5* has nothing to draw;
`AtStakeQuery` is wired to `NoResultUpdateRuleExists`; and `MatchHistoryQuery`'s registered
implementation is called `ChallengesButNobodyHasPlayed` **because that is literally true**.

Three **accepted** ADRs decided this ground and went in the reset with the contexts they
decided. Their substance is re-argued here rather than re-inherited, because the product they
were written about is gone: there are no courts, no reservations, no seats that cost money, no
departures and no four cancellation flags. What survives of a match is **a plan, a moment, a
score, and a two-sided disagreement about it** — which is the part ADR-0034 explicitly said it
had not built for.

**Three facts bound the redesign, and each of them has moved since ADR-0048 was written.**

- **There is still no way to reach anybody.** [ADR-0038](0038-now-is-polled-the-push-is-specified-and-deferred.md)
  deferred push, nothing in `backend/` sends anything to a phone, and the prompt exists only for
  a player who has already opened the app. ADR-0048's 24-hour deadlines were affordable
  *because* of that, and ADR-0049's refusal to fine anybody rested on it. Both premises hold
  unchanged.
- **A challenge has no end time**, so ADR-0048's *thirty minutes after the final point* and
  *24 hours after the match ends* have nothing to run from. The clocks have to be re-derived
  against a product whose only calendar is *an ordinary week*
  (`player_profile/domain/availability.py`).
- **`CONTEXT.md` grew a sixth Player Score strand while ADR-0049 was not in the tree.**
  *Confirms results — whether a counted game gets confirmed, so it counts* is contracted to
  the matcher by [ADR-0098](0098-matcher-demands-as-executable-contracts.md), weighed 24 in
  competitive and 4 for fun, and quoted in three documents as the whole argument for reading the
  strands separately. ADR-0049 rules that **no player is penalised for not entering or not
  agreeing a result**. Both cannot stand.

**The context has a name problem too.** ADR-0098, `ports.py` and four specs call the unwritten
provider `matches`; the card, the wire field and this batch call the thing it records a **game**.
One of the two spellings has to go before either is built into a durable event name.

## Decision

### 1. The context is `games`, and a game is opened by a completed line-up

`app/modules/games/`, and the placeholder `matches` is retired as vocabulary. The wire already
says `counted_games`, `the-newcomer-path.md` already says *new until their first game*, and a
context named for the noun the player reads is the one that stays honest.

**A `Game` is opened at the instant a challenge's line-up completes** — every seat accepted,
which is `challenges`' derived `Standing.ON`. That is the moment, and the only moment, at which
the arrangement is knowable: who is on which side, in which sport, for which window, for a game
that is **counted** or a **friendly**. Until then there is nothing to record; after then the
seats may still be rearranged but the membership is settled
(`CONTEXT.md`: *an acceptance is to the game, not to the side*).

**The opening is inline, in the transaction of the accept that completed the line-up**, through
a port `challenges` declares and `games` signs — the shape and the argument of
`MutualChallengeMinting`. The outbox is [ADR-0003](0003-transactional-outbox-for-event-delivery.md)'s
convention and is right nearly everywhere; it loses here twice. A subscriber would have to
**re-derive *did this accept complete the line-up*** by reading somebody else's aggregate, when
the use case that just folded it already holds the answer — a second reader of the challenge
log, and a second author of what *on* means. And the player who taps the last accept would be
told the game is on by a screen that cannot yet show it, for however long a poller takes.

**The trigger is the line-up completing and not the tapping, so it is checked at both places a
line-up can complete.** The second one is easy to miss and is the reason this is written down: a
challenge born of two *Let's play* yeses has both seats accepted from birth, so in a **singles**
sport the court is complete the instant it is minted and **no accept ever happens on it**. A
game opened only from the accept path would never record a tennis game arranged that way, and
the failure would read as *this pair has never played* — a sentence the matcher believes.

**A game nobody declared a kind for is counted.** A send carries the mode its search ran under;
the deck and a mutual yes carry none, because neither surface asks. The absence resolves to
**counted**, on ADR-0049's own reading of the word: *a friendly is a thing people choose*, so
nobody may end up with one by accident. The reverse default would leave `counted_games` at zero
for ever on the surface most games come from.

### 2. A result is the record that a game happened

**Whoever held a seat enters *we played, here is the score*, and that entry carries the moment.**
No booking, no calendar, no court reservation: the platform learns a game happened because
somebody says so and the other side does not disagree.

**The moment is the moment of the entry, and there is no date field anywhere.** A player who
says *we played* on Tuesday played on Tuesday as far as this platform is concerned. Asking for a
date would be a calendar — the thing `availability.py` refuses to hold and
[ADR-0100](0100-challenge-window-derived-never-chosen.md) refuses to propose — and it would be a
field with nothing to check it against.

So a game reaches exactly three ends, and **every one of them is folded from the record and the
clock, never stored**:

> **Superseded 2026-09-12 by [ADR-0163](0163-called-off-is-the-fourth-end-of-a-game.md): there
> are four.** *Called off* is the fourth, and it is the one an act reaches — a withdraw on a court
> that has been a game hands `GameCalledOff` to this context in the same transaction, and the
> standing reads it first, as `challenges` reads `withdrawn_at`. It is still folded and never
> stored; what moved is *never announced*, on ADR-0142 §3's exemption, because no arrangement of
> the record could reach it. The three below are untouched.

| End | What it means | What the record holds |
| --- | --- | --- |
| **Confirmed** | they played and a score is agreed | a played moment, and a proposal that was accepted or that nobody answered |
| **Unscored** | they played and no score is agreed | a played moment and two proposals, neither accepted, both windows closed |
| **Never played** | it was arranged and it did not happen | a plan, and no played moment, past the entry window |

**Nothing announces one of them.** There is no `ResultConfirmed`, no `GameUnscored` and no
`GameNeverPlayed`, for the reason `challenges` has no `GameOn`: *a standing that is derived has
exactly one place to be true, and an event saying otherwise would become the second* — the one a
subscriber would believe, and the one that would be wrong for the whole gap between a deadline
passing and a sweep noticing it. The events in the log are the six things **a person did**.

### 3. `games` is event-sourced

ADR-0034 argued *record*, and every reason it gave has been deleted:

| ADR-0034's reason | Today |
| --- | --- |
| twenty-three stored facts over a 33-situation state model | a plan, a moment, at most two proposals and an acceptance |
| *the busiest object in the product is the cheapest to read* — several matches per home-screen open | nothing reads a game on a hot path; the card reads two aggregates of counts |
| the disputable part is settled on court in thirty minutes | the disputable part is **the whole of what is left**, and it now runs for days |
| *if the score flow ever grows a genuine negotiation that must be reconstructable, the count will not be enough and the tracker will have to be load-bearing* | the negotiation is the context, and `playerEventsTracker` does not exist and is not being built |

ADR-0048 stored *four facts and no list* — the result on the table, which side proposed it,
whether it is agreed, how many proposals — and put the superseded proposals in the outbox trail,
*which is what keeps ADR-0034 intact*. That trail was to be consumed by a support tool nobody
has built, so on a record the first score somebody typed would be **unrecoverable by design**.
It is the one thing in this flow a human will ask about.

And the two reads this context owes are both **walks over what happened**, not folds of what is:
the pairwise `PLAYED` / `PLANNED_NEVER_PLAYED` tallies, and *the last five counted results*.
`challenges` already proved the shape — `EventSourcedChallengeHistory` walks the stream for
exactly the same reason, that *an answer is a thing that happened to the court as it stood then*.

[ADR-0018](0018-aggregate-repositories-over-the-event-store.md)'s deferred question — whether a
generic `EventSourcedRepository[A]` is owed — stays deferred, and this record is the asking it
asked for. Being event-sourced, **`games` adds no table and no migration**: the streams live in
`event_store` beside every other aggregate's.

### 4. ADR-0048's flow, carried forward, with the clocks re-derived

Unchanged in substance: **silence confirms**; **each side proposes once**; **correcting is free
until the other side responds and is not a second proposal**; **accepting comes only from the
opposing side and one opponent suffices**; **an acceptance does not settle until a grace has
passed**; **a counter must carry a score, and there is no bare rejection**; **two standing
proposals nobody accepts leave the game unscored**; **a settled result is final**. *We will not
arbitrate.*

**Three numbers, and none of them is ADR-0048's, because none of ADR-0048's has anything to run
from.**

- **The plan's horizon is one ordinary week from the line-up completing.** That is the only
  calendar this product has: the grid is *an ordinary week*, and every `Window` — `TODAY`,
  `TOMORROW`, `WEEKEND`, `THIS_WEEK`, `ANY` — is a statement about one. A per-window table was
  rejected: `ANY` has no horizon at all, and a window is *a label on the search*, never a
  proposed time.
- **Entry stays open for one day past the horizon.** A day is what this platform already asks of
  a person it needs an answer from (`ANSWER_WINDOW`), and it is asked here for the same reason
  and with the same excuse — we cannot ring them. Two constants rather than one number: gluing
  them into *eight days* would hide both arguments.
- **A proposal stands for 24 hours**, from the proposal or from the correction that re-dated it.
  A correction re-dates deliberately: the other side is answering a score, and a score they have
  not seen has not started their day.
- **The acceptance grace is six hours from the proposal**, not thirty minutes. Thirty minutes was
  chosen when the prompt appeared on court inside a thirty-minute result window and everybody was
  still at the club. Entry now happens at home, possibly days later, and a grace that only binds
  when both opponents are on their phones at once does not do the job it is for — *somebody is
  always slower to their phone*. Six hours is an **admitted hypothesis**, and its falsifier is
  recorded with it: counters arriving between the grace and the proposal's close are the objections
  the grace exists to protect, and the share of results settled by an explicit acceptance rather
  than by silence is what says whether accepting is still worth a tap.

**One narrowing, and it is a real change.** ADR-0048 let *anyone who played* counter, **including
a player on the proposing side**, while also capping proposals at **one per side**. Those two
sentences cannot both be executable: a counter from the proposing side is either that side's
second proposal or it is not a counter. The cap wins, because it is what bounds the argument to
two rounds and what makes *silence confirms* safe. The substance of the other sentence — *the
rule that makes a teammate's agreement worthless makes a teammate's objection credible* — is
carried by making **the correction the side's and not its author's**: any member of the proposing
side may revise their side's score while the other side has not answered. A player who disagrees
with their own partner has a way to say so, and neither side gets two turns.

### 5. ADR-0049 stands whole, and *confirms results* is struck from the six strands

**No player is penalised for not entering or not agreeing a result.** Not the silent loser, not
the four who all went home, not the side whose counter went unaccepted. **A game with no agreed
result is a counted game that produced no result** — never reclassified as a friendly — and it
**counts as an evening and never as evidence**: it is in history, it is in `counted_games`, it
establishes that these people have played together, and **it moves nobody's Level**.

`CONTEXT.md`'s *Confirms results — whether a counted game gets confirmed, so it counts* is
**withdrawn as a strand**. The argument is one sentence: **an unconfirmed result is a fact about
a pair, and a strand is a verdict about a person, and there is no way to turn one into the other
without deciding who was wrong** — which is exactly what ADR-0048 refused to do about the score
itself. Every denominator that was tried on it docks somebody ADR-0049 names as protected:

| Denominator | Who it docks that it must not |
| --- | --- |
| counted games played | both sides of every disagreement, including the one who was right |
| games where a score was put in front of you | the side whose honest counter the other side then ignored |
| games you countered | the same person, and nobody else in a position to tell them apart |

The alternative was revising ADR-0049 and pricing silence. It fails on ADR-0049's own arithmetic,
which has not moved: ADR-0048 removed the *profit* in staying silent — your Level moves whether
you tap or not — so what is left to price is not opening an app **that cannot ring you**, and a
dead battery and simple inattention are the same event to us. If players are later observed
confirming scores they believe are wrong to avoid a mark, that is a reason to add one, with
evidence.

**The strand is withdrawn the way opponent variety was, not deferred.** ADR-0098's rule — *a
consumer-driven contract with no consumer is withdrawn, not carried* — reads here as: a demand
whose provider has argued it cannot honestly be published is a demand nobody will notice going
wrong. The Player Score ships **five** strands, and ADR-0098's Decision 3 absorbs the loss by
construction: a strand nobody publishes stands down and the survivors renormalise *inside* the
reliability term. `ReliabilityStrand.CONFIRMS_RESULTS`, its two ruleset weights and its enum
member on `openapi.player.json` are removed by
[#305](https://github.com/Raketa02/Raketa/issues/305) — the ticket that builds the provider,
and the one whose change is a wire change that has to ship with its client.

### 6. What `games` publishes, and to whom

| Read | Who reads it | Shape |
| --- | --- | --- |
| `PLAYED` and `PLANNED_NEVER_PLAYED` pairwise | the matcher's familiarity term, **today** | the missing half of `MatchHistoryQuery` |
| counted games per player | `player_card.counted_games`, and §9.10's newcomer predicate | a count per player asked about, and **a zero is measured** |
| the last five counted results, oldest to newest, win or loss | *Last 5* on the card | fewer than five is a real answer; **it is never padded** |
| whether a game was counted or a friendly, and whether its result was confirmed | the rating and Player Score tickets | the two facts on the game, read per player through the directory |

`MatchHistoryQuery` **stays whole and gains a second composing adapter**, per ADR-0098's
amendment banner: `challenges` keeps answering `ACCEPTED` and `DECLINED`, `games` brings
`PLAYED` and `PLANNED_NEVER_PLAYED`, and one adapter merges the two into one bounded read of at
most `PAIRWISE_COUNTERPART_BOUND` counterparts. Splitting the port would cut that bound in half
and leave a caller merging two bounded reads, which is not a bounded read.

**Two ports are published and the repository is not**, and the line between them is who
reads it. `GameHistoryQuery` answers the three aggregate facts; `GameDirectory` answers per
player, in aggregates, because *counted or a friendly* and *confirmed or not* are folded
against the reader's clock and a projection of either would be a second place for it to be
true. Both are contracted in `tests/demands/` over every registered implementation; the
repository is how this module loads its own aggregate and nobody outside will hold one.

`late_change_threshold` **stays `None`**, and now for a reason that is this context's own rather
than borrowed: a *plan* here is a line-up with a window, and nothing about it can be changed
late — an accepted seat cannot be withdrawn, and the game has no time to move. *Late* has no
referent, so there is no number, and the *keeps plans* strand has no denominator. It is absent
rather than defaulted, on the same rule as everything else in that file.

## Considered options

**Open the game on the entry, not on the completed line-up.** The smaller build, and it is what
*a result is the record* sounds like it implies. It cannot produce `PLANNED_NEVER_PLAYED`, which
is half of what this context is being built for — familiarity must be able to tell a ghost from a
game — and the only way back is to derive the ghost inside the composing adapter, by subtracting
played pairs from accepted pairs. That puts the definition of *we arranged this and it never
happened* in an adapter, in the matcher's module, over somebody else's log.

**Announce a completed line-up from `challenges`.** Rejected by that context's own stated
invariant, and rightly: *nothing announces a conclusion the seats already imply*. `games`
concluding it is a different thing from `challenges` publishing it.

**A sweep that appends `ResultConfirmed` for the record**, the way the challenge lapse loop
appends `SeatLapsed`. Tempting, and it is the shape the rating context will want. It is not the
same case: a lapse is a fact about **one person's silence**, where a confirmation is the
**standing of the game**, and a durable name for a standing is the second place for it to be
true. The rating context reads confirmed results forward instead, and how it does that is
[#304](https://github.com/Raketa02/Raketa/issues/304)'s decision, recorded below as a cost.

**Keep `matches` as the context name**, matching ADR-0098 and four specs. Rejected: the wire, the
card and the newcomer path all say *game*, and a durable event name is the worst possible place
to discover that a context was named after a placeholder.

**A record with a version and an outbox**, as ADR-0034 decided. See §3 — every premise it rested
on was deleted with the product it described.

## Consequences

**Easier**

- **Four empty blocks on the competitive card acquire a producer**, and the batch above this
  ticket stops being blocked on a context that does not exist.
- **The three ends are unstoreable, so they cannot drift.** A reader asking *is this confirmed*
  between the deadline and any sweep gets the same answer as one asking after, because there is
  no sweep and nothing to be stale.
- **No table, no migration, no read model.** Event sourcing pays for itself the day the first
  person asks what the original score said.
- **`ChallengesButNobodyHasPlayed` retires by being composed, not replaced**, so the seam ADR-0098
  described in prose is the seam in the code, and the 500-counterpart bound is applied once, over
  the merged answer.

**Harder**

- **The newcomer predicate stops being inert.** `counted_games == 0` has been true for every
  player who will ever exist; from the first confirmed game it is not.
  `the-newcomer-path.md`'s *new until their first game, and never longer than 14 days* is live in
  both halves for the first time, and the seeded cohort now has to contain somebody who has
  played — which is [#308](https://github.com/Raketa02/Raketa/issues/308).
- **The rating context has nothing to subscribe to.** A confirmation is derived, so #304 must
  read games forward from a cursor rather than handle an event. That is a real cost of §2 and it
  is being taken deliberately; if it turns out to need an announcement, the argument to beat is
  the one in Considered options, not this record's silence.
- **Player Score ships five strands, and one of this batch's own decisions moves.** #302's second
  decision says *turning up, answering challenges, confirming results*; the third of those is
  struck here, and #305 is two strands and one published number rather than three.
- **The pairwise read now merges two providers at search time.** It is still one bounded answer,
  but the bound is applied after a merge rather than by the provider, so the order is this
  adapter's responsibility — and a counterpart cut off by the bound must stay indistinguishable
  from one fully decayed by time.
- **Six hours is a guess with a falsifier and not a measurement.** So is one ordinary week. Both
  are written in one place, in the domain, and neither is configuration: an environment that could
  select them could select behaviour a domain test can observe.

**Neutral**

- **`friendly` keeps its one meaning** — what you chose, never what you failed to record — which
  is the whole of ADR-0049's fourth rejected option and the reason the kind is stamped at the
  plan rather than derived at the end.
- **The score is a value object with an invariant: it names a winner.** Equal sets is refused,
  because *Last 5* is *win or loss* and a draw is not a result any of these four sports produces.
- Nothing changes for `User`, `Assessment`, `SkillRating`, `PlayerProfile`, `Challenge` or the
  matchmaking module's own aggregates. [ADR-0002](0002-event-sourced-user-aggregate.md)'s
  per-context rule is being followed rather than overturned — and this time it came out the way
  the tree already leans, which is what makes ADR-0034's opposite answer worth having had.
