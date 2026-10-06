# ADR-0140 — A Player Score is what the platform watched, and two strands is what it can see

- **Status:** Accepted
- **Date:** 2026-09-04
- **Carries out [ADR-0137](0137-a-result-is-the-record-that-a-game-happened.md)'s Decision 5** —
  *confirms results* leaves the vocabulary, the ruleset and the wire here.
- **Decides a clause ADR-0137 opened and did not close**: whether *shows up* survives the same
  argument that struck *confirms results*. It does, and the reason is written down.
- **Extends [ADR-0098](0098-matcher-demands-as-executable-contracts.md)**: `PlayerScoreQuery`'s
  null object retires and a real provider signs, which makes reliability the last term to stop
  being absent platform-wide.
- **Applies ADR-0111**:
  the published number may not go on the candidate index, and reaches a card at assembly time.
- Settles [#305](https://github.com/Raketa02/Raketa/issues/305) on the spec
  [#302](https://github.com/Raketa02/Raketa/issues/302).

> **Note — the Classic play removal (2026-10-06, [#569](https://github.com/Raketa02/Raketa/issues/569)).** The matcher's half of this record is gone — `PlayerScoreQuery`, the reliability term and its evidence gate, the ruleset's strand weights and `horizon_days`, and the candidate index §6 kept the score off (#579, #580). *Answers challenges* stood down at #544, when *keeps plans* came up on booked games, and has no source now that challenges are gone, so `player_score` folds `games` and `bookings` instead. §1, §2, §4 and §5 stand: no record of its own, a ghost charged to the whole court, no decay beyond the ratio, and the published weights.

## Context

**The card's first record block prints *Player Score — reliability out of 100*, and there is no
`player_score` context.** The root [`CONTEXT.md`](../../CONTEXT.md) says so in as many words:
*"Nothing about this context is decided and nothing is built"*. The six strand names are in the
glossary because the matcher contracted them and because a player reads them on their own
screen — they are the product's language before they are the engine's — and nothing on this
platform has ever published one.

That was defensible while nothing had happened to anybody. It stopped being defensible when
[ADR-0137](0137-a-result-is-the-record-that-a-game-happened.md) shipped `games`: a plan now
produces a game or it does not, and `challenges` has recorded who answered inside their day
since the send shipped. Two of the six strands have a real source, and a demand with a
satisfiable provider that nobody satisfies is a demand quietly rotting in a contract suite.

**Five names, not six.** ADR-0137 struck *confirms results* rather than deferring it: an
unconfirmed result is a fact about a **pair**, a strand is a verdict about a **person**, and
every denominator tried on it docked somebody
ADR-0049 protects — both sides of an
honest disagreement included. It named this ticket as the one that removes the enum member, its
two ruleset weights and its member on `openapi.player.json`, *"because that change is a wire
change and has to ship with its client."*

**Three of the five survivors have no source and will not get one here.** *Keeps plans* needs a
plan with a moment to be late for, and `games` publishes `late_change_threshold() -> None`
because there is no such thing on this platform. *Settles up* needs court money, which the
context map rules out of scope. *Sportsmanship* needs players rating each other afterwards, and
no surface exists on which anybody could.

## Decision

### 1. `player_score` is a context that keeps no record, and that is its shape

We will add `app/modules/player_score/` with **no aggregate, no table and no migration.** Every
fact it publishes is folded out of `games`' and `challenges`' streams at the moment somebody
asks, through those contexts' own published ports.

This is not an economy. A stored Player Score would be a second place for *did that game
happen* to be true, and the first one to be wrong would be the copy every screen believed —
which is the argument `games`' `standing.py` and `challenges`' `standing.py` already make about
a single game, applied to the fold over all of them. A score is derived from two records; it is
not a third record.

The consequence is a context with one outward port and none inward. `PublishedScoreQuery`
answers *what does the record say about these people*, in this context's own vocabulary, once
per set and never once per player.

**It is called `PublishedScoreQuery` and not `PlayerScoreQuery`** because the matcher's port of
that name already exists and is a different shape — the *demand*, where this is the
*publication*. ADR-0137's third finding is the rule: the contract is one namespace, and **the
cost of a shared word is paid by whoever arrives second**.

### 2. *Shows up* ships, and a ghost is charged to the whole court

**This is the clause ADR-0137 opened without closing, and it is the hardest call in this
record.**

The only evidence this platform has about turning up is a **ghost** — a planned game whose
entry window closed with nobody ever saying *we played*. And the act that produces a ghost is
**nobody entering a result**, which is the exact act ADR-0049 protects in the sentence *"no
player is penalised for not entering or not agreeing a result."* Read literally, *shows up*
dies on the same argument as *confirms results* and the Player Score ships one strand.

We will ship it anyway, on a distinction we are prepared to be wrong about:

**ADR-0137's objection was that a denominator would have to decide who was wrong.** Its table is
explicit — every candidate denominator *"docks both sides of every disagreement, including the
one who was right"*, or *"the side whose honest counter the other side then ignored"*. A
disagreement has a right side and a wrong side and the platform cannot tell them apart, so
pricing it means guessing.

**A ghost has no sides.** Nobody proposed anything, nobody countered anything, and every person
on that court did the same thing: nothing. Charging all of them equally is not a guess about who
was at fault; it is the arrangement itself failing, recorded against everybody who was in it.
What *shows up* prices is **an arrangement that dissolved**, not a tap that never happened — and
over a career the person common to a run of dissolved arrangements is the one the strand is
about, which is exactly what a ratio is for.

Three things bound the damage, and they are the reason this is affordable:

- **`min_observations` is 3** and is the matcher's own ruleset data. One ghost out of one
  arrangement stands the strand down rather than publishing a nought.
- **The charge is symmetric.** Nobody is singled out, so nothing here can be read as the
  platform taking a side in a dispute — which was ADR-0049's actual fear.
- **A game still inside its entry window is in neither half.** It is not a ghost until the clock
  says so, and filing it either way would publish a conclusion nothing has reached.

**What would falsify this.** If ghost rates turn out to be flat across players — that is, if a
ghost predicts nothing about who you are and everything about the week it happened in — then
*shows up* is measuring weather rather than people and it should be withdrawn the way *confirms
results* was. That is a measurement, and it is the measurement this decision is a bet on.

### 3. The strands, and what each counts

| Strand | Opportunity — the denominator | Good outcome — the numerator |
| --- | --- | --- |
| **Shows up** | plans that settled: a game that was played, or a ghost | the ones that were played |
| **Answers challenges** | invitations whose day is over: answered, or lapsed | the ones answered inside the day |

Four narrowings, each of which would be a defect if it were not written down:

- **An invitation is a seat with a deadline.** Three seats in `challenges` carry an answer
  nobody was asked to give — the organiser's, accepted from birth because they are the one
  proposing, and both seats of a challenge born from a mutual yes. `answer_by is None` is what
  says so, and a strand that counted the organiser's own seat would publish a hundred per cent
  for anybody who only ever organises.
- **A decline is a good outcome.** *Answers challenges* is the only strand on this platform
  where a no scores. It prices silence, not judgement — which is why `SeatAnswer.LAPSED` and
  `SeatAnswer.DECLINED` are different values on the seat, and why the ADR that separated them
  said the strand would be unmeasurable if they were filed alike.
- **Friendlies count towards turning up.** The choice that makes a game a friendly is a choice
  about ratings; it says nothing about whether the people who arranged it came.
- **The moment is when the opportunity closed**, not when it opened. A ghost is observed when
  its entry window shuts, and dating it from the plan would age a record faster than the record
  aged — which the matcher's `horizon_days` reads directly.

### 4. There is no decay beyond the ratio itself

`CONTEXT.md` says *"the score is a memory, and it fades with new evidence — decay belongs here,
on the side that owns the record."* We will implement that as **the arithmetic of a ratio and
nothing more**: every opportunity counts for ever, and one no-show among forty games weighs
almost nothing because there are thirty-nine others. That *is* fading with new evidence.

We rejected a rolling window this context would own. It would be a second number that must not
disagree with the matcher's `horizon_days`, and it would make the denominator a fact about a
window rather than about a career — so *out of what* would stop meaning what a reader assumes.
The matcher stands the whole term down past its horizon, which is the only forgetting anybody
has argued for.

### 5. The published number, its weights, and where they live

`PlayerScore.published` is the figure out of a hundred on a player's own profile: the strands
present, weighted at **35 / 20 / 12 / 10 / 8** and renormalised over whatever is there.

- **They are this context's constants and not ruleset data.** The ruleset is the matcher's
  release, versioned and stamped on every recorded search. This is what a player is told about
  themselves. A number the matcher could re-release would let a weight release change what
  somebody's own profile says about them.
- **They are the six-strand vector's own numbers with the struck name's 15 removed, not
  redistributed.** Nothing was retuned because nothing was learned; a weight that moved would be
  a hypothesis about a player's own screen with no evidence behind the move.
- **The vector sums to 85 and that is deliberate.** A ruleset weight vector must sum to a
  hundred so each number reads as a share of a term's budget. This is not a budget: its basis is
  the strands a player actually has, which is two today, so a hundred would be a coincidence
  dressed as a meaning.
- **One rounding *rule*, half up — and deliberately two applications of it.** Python's `round`
  goes to even, which would show two players either side of a half the same number one week and
  different numbers the next, so `out_of_a_hundred` is spelled once and used by both a strand and
  the blend. It is used **twice on the way to the published number**: each strand is rounded to
  the figure the player is shown, and the blend is then taken over *those* figures rather than
  over the ratios behind them. That is the point rather than an oversight — the number on the
  profile is the weighted mean of the numbers printed beside it, where a blend over the unrounded
  ratios would occasionally differ from its own strands by a point.

**The published score has two readers now and computes itself for neither.** The reliability
floor prices it through `published_score_bar`, and — with [#306](https://github.com/Raketa02/Raketa/issues/306) —
the player card prints it. `PlayerScoreReading.published_score` already documented itself as
*"the one deliberate exception"* to the never-blend rule; this record notes that the exception
now has a second reader and that the reason is the same one: **a card explaining a match with a
figure the player's own profile disagrees with is worse than a card that says nothing.**

### 6. The number may not go on the candidate index

ADR-0111 rules that the
index holds only what a player changes about themselves. **A Player Score is the platform's
observation of them**, so it may not go on the index — not as a column, not as a tailed
projection, not as a denormalised strand.

It reaches a card the way the other three non-index card fields do: **through a port at assembly
time**, over the twenty rows that survived the floor rather than over the pool, on the seam
`CardIdentity` already rides ([ADR-0107](0107-the-player-card-is-assembled-outside-the-engine.md)).
The engine reads it through `PlayerScoreQuery` for scoring, which is a separate read for a
separate purpose and is bounded by the box rather than by the shortlist.

### 7. The ruleset loses two weights in place, and the survivors are restated

`ReliabilityStrand.CONFIRMS_RESULTS` leaves the enum, both `strand_weights` maps,
`openapi.player.json` and the client's generated types.

**Five of the six spec files that name six strands are edited, and the sixth is not touched on
purpose.** `matchmaking-engine.md` is one of the two **verbatim input documents**: its own
README lands it byte-identical and rules that *"corrections go in an ADR, or in the conflict
table here — never in the source."* So it keeps saying six, and
[`docs/specs/matchmaking/README.md`](../specs/matchmaking/README.md) gains a conflict row
naming §7.1, §9.3.4 and §23 Q11. A spec that has been tidied is no longer the thing the
decisions were argued against.

**`r2026_08_26_a.py` is edited rather than superseded.** The file says it is frozen, and the
freeze is about *numbers moving*: a hypothesis changing needs a new dataset with a new name and
an offline diff. Nothing was learned here — a word left the language. No recorded search read
either weight, because reliability stood down platform-wide for every search this version has
ever run. The precedent is [ADR-0139](0139-a-confirmed-result-is-evidence-and-a-level-moves-by-what-it-taught.md)'s:
`AtStakeQuery` became real under this same version, because **a provider arriving is not a
weight release**.

**The survivors had to be restated, and that is worth being precise about.** A weight vector
here is validated as summing to a hundred, so dropping a key forced the rest to be re-expressed
over the smaller vocabulary. They were rescaled by largest remainder and by nothing else:
competitive 25/22/14/10/5 of 76 became **33/29/18/13/7**, for fun 32/22/14/12/16 of 96 became
**33/23/15/12/17**. The reliability term already renormalises over the strands that arrive, so
scaling the whole vector by a constant would change nothing at all — **and the residue is the
rounding, not the scaling**. The three walkthrough golden files move by it and by nothing else:
one reliability reading goes `0.375 → 0.37375` and another `0.350 → 0.349`, worth **0.016 and
0.009 Fit points**. No order changes, nobody crosses the floor, and no candidate is admitted or
refused who was not before. That is the whole price of expressing five ratios as five integers,
and it is stated rather than rounded away.

### 8. Reliability stops being absent platform-wide

`NoPlayerScoresExist` retires — the third null object to go by its own stated fact becoming
false, after `NoMatchHistoryExists` and `NoResultUpdateRuleExists`. `build_absent_terms` now
answers with an empty set and loses its argument, because there is nothing left to read it off.

Three things move with it, and none of them is cosmetic:

- **A stood-down reliability is now `NOTHING_FROM_THEM`, not `NOT_YET_ON_THIS_PLATFORM`.** The
  fact exists; this person has no record of it. That is the line `floor.py` draws twice and it
  now falls on the other side.
- **The evidence gate counts eight live terms rather than seven.** It **excludes nobody**: the
  gate wants half, and every candidate the index can produce reads level, balance and distance
  plus at least one of intent, availability and the two tag columns — four of eight clears a bar
  of `0.5` exactly as four of seven did. The margin is now zero rather than one term, which is
  the honest way to say it.
- **The one null object left is a gate**, and that is ADR-0098's rule showing through rather
  than a coincidence: *a gate may be honestly empty; a term may never be honestly neutral.*
  Every term now has a provider; what survives is the one fact a zero can honestly state.

## Consequences

**Two strands is a thin score, and the card will say so by saying little.** Most players will
have one strand, many will have none, and the number will move a lot on early evidence.
`min_observations` covers the second problem and nothing covers the first: the honest reading of
*Player Score 67* today is *of the two things we can watch, here is one of them*. The product
copy is the client's and this record does not write it, but a client that renders this as a
confident verdict is rendering more than the number contains.

**The decomposition's justification narrowed and is now watched rather than asserted.**
`ReliabilityStrand`'s docstring says the per-mode split is justified *"for exactly as long as"*
a pair of strands exists that the two modes order oppositely. That pair was *confirms results*
against *sportsmanship*, at 24/4 versus 5/16 — a wide inversion, and it is gone. What is left is
*keeps plans* against *sportsmanship*, at 18/7 versus 15/17, which still flips and is asserted
in `tests/unit/test_matchfit_terms.py`. **The day no pair inverts, the argument for reading
strands separately is due again**, and the test is what will say so.

**A ghost charged to four people will occasionally be unfair to one of them**, and this record
accepts that rather than solving it. The person who drove to the court and waited carries the
same mark as the three who forgot. There is no act on this platform by which they could say so —
inventing one is a product decision several tickets larger than this, and inventing a *denial*
would be arbitration, which ADR-0048 refused about the score for reasons that apply here word
for word.

**Two reads got more expensive and neither is indexed.** Both new folds walk the event log with
a substring match, like every other read in `games` and `challenges`, and both are called once
per search over every surviving candidate. The index that fixes them is PostgreSQL's, over
tables with no rows on a platform with no deployed environment, and it belongs with the first
query that measures the problem.

**`answer_rate` stays `None` and the Liveness signal stays unreachable.**
`LivenessSignal.ANSWER_RATE_AND_SPEED` wants a rate **and a speed**, and this context publishes
a rate. Feeding a ramp half its definition would be a second definition of the signal, written
where nobody would look for it. It is left absent, named here so the next reader does not take
it for an oversight.

**The seeded cohort still cannot draw that signal, and now for a different reason.**
`app/seeds/screens.py` lists it under `CANNOT_BE_DRAWN` because *`player_score` does not exist*;
the context exists and the sentence is rewritten rather than the entry removed. Nothing else in
the cohort moves: no seeded member has ever been invited or planned a game, so no seeded member
has a Player Score, and the reliability term stands down for all of them as their own gap.

**Three strands are still unpublishable and the vocabulary keeps carrying them.** That is
deliberate and is the difference from a withdrawal: *keeps plans*, *settles up* and
*sportsmanship* each have a provider that could exist and a shape already agreed, where
*confirms results* had an argument that it could never be published honestly. A name in the
vocabulary with no provider is a promise; a name nobody could ever fill is a lie, and ADR-0137
removed the one that was.

## Alternatives considered

**Ship one strand and stand *shows up* down.** The strictly consistent reading of ADR-0049, set
out in Decision 2. Rejected because the objection ADR-0137 actually recorded was about
denominators that must decide who was wrong, and a ghost gives nothing to decide. If the
falsifier in Decision 2 fires, this is what we do.

**Restate the published weights as a fresh five-name vector summing to a hundred.** Rejected:
it would be a second set of numbers to defend with no evidence behind the move, and the blend
renormalises over the strands present in any case, so it buys nothing that keeping the original
numbers does not already do.

**Cut a new ruleset version for the two removed weights.** Rejected in Decision 7. A dataset
whose only difference is a vocabulary change is a release the ruleset-diff gate would have to
report as moving nothing, and it would leave two near-identical seven-hundred-line files whose
difference a reader would have to diff to find.

**Let `player_score` sign `PlayerScoreQuery` directly.** Rejected: it would make a provider
import the consumer it exists to serve, put the matcher's rounding inside the number on a
player's own profile, and break the arrow every other provider keeps. A fourteenth
`.importlinter` contract now fences it, on the same argument as the twelfth and thirteenth.
