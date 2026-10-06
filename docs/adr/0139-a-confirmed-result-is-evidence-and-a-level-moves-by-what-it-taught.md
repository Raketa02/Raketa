# ADR-0139 — A confirmed result is evidence, and a Level moves by what it taught us

- **Status:** Accepted
- **Date:** 2026-09-04
- **Extends [ADR-0017](0017-rating-context-event-sourced.md)**: the SkillRating aggregate gains
  its second transition, and the one the σ core was extracted to serve.
- **Pays a cost [ADR-0137](0137-a-result-is-the-record-that-a-game-happened.md) recorded by
  name** — *the rating context has nothing to subscribe to, so #304 must read games forward from
  a cursor rather than handle an event* — and answers it with a different cursor from the one
  that sentence imagined.
- **Second instance of [ADR-0015](0015-engines-as-a-pure-versioned-layer.md)'s versioned
  engines** inside RacketSkill: a second stamp beside the questionnaire's, retuned separately.
- Settles [#304](https://github.com/Raketa02/Raketa/issues/304) on the spec
  [#302](https://github.com/Raketa02/Raketa/issues/302).

> **Note — the Classic play removal (2026-10-06, [#569](https://github.com/Raketa02/Raketa/issues/569)).** The search card that priced *you against this person* is gone (#579), and so are the matcher's skill term and the `games_match_history.py` beside which §6 put the adapter. *At stake* is read only on a booked game's pairing now, side against side, by the same `stakes()` that moves the Level (ADR-0161). The update rule, its constants, the statuses, a four's share and the hourly catch-up stand as written.

## Context

**Nobody's Level has ever moved.** `NoResultUpdateRuleExists` says so in its own name, and it
has been the honest answer since onboarding shipped: `rating` produces a hypothesis from a
questionnaire and nothing on this platform has ever tested one. `AtStake` is a type with an
invariant written, `AtStakeSchema` is on the wire, and the block is omitted from every
competitive card because the number behind it does not exist.

Two things changed. [ADR-0137](0137-a-result-is-the-record-that-a-game-happened.md) built
`games`, so the platform now knows that a game was played and what the score was. And the same
ADR struck *confirms results* from the Player Score, on the grounds that **an unconfirmed result
is a fact about a pair and a strand is a verdict about a person**. What is left to price a
confirmed result with is the thing it was always about: the Level.

**This is the arithmetic the whole marketplace's honesty rests on.** Everything else in
`matchmaking` is a weighting that can be retuned on evidence; this is the number a player
watches, argues about, and decides whether to trust. `CONTEXT.md` already reserves the ground —
*it reads the rating engine's own update rule, so nobody else may compute it* — and the four
questions it leaves open are what this record answers.

### What bounds the answer

- **σ is a floor, not a posterior.** *Onboarding cannot produce confidence above 30%, enforced
  as a floor on σ rather than as a display cap.* That floor is humility about self-report; it is
  **not** a belief anybody derived that a fresh player's Level could be a third of a band out.
  Treating it as a full Bayesian prior over-weights the first results, and the arithmetic below
  does exactly that unless something stops it.
- **Silence confirms** (ADR-0137, carrying ADR-0048). A result nobody answered is a result, and
  an evening the loser never opened the app about will move their Level. That is deliberate —
  it is what removes the profit in staying quiet — and it is also the reason a single evening
  must not be worth very much.
- **Skill and certainty are separate variables**, and *absence widens, it never lowers*. A rule
  that moved μ without saying what happened to σ would be half a rule.
- **A rating explains itself, and the explanation is computed, never authored.** Which is why
  *at stake* has to be the update rule read forward and not a second expression of it.
- **[ADR-0105](0105-determinism-is-a-set-iteration-problem-in-python.md).** Two players' Levels
  after the same history must not depend on which order a `for` walked a set.

## Decision

### 1. A result is evidence, weighed by inverse variance — with one relative twist

**The questionnaire fuses answers by inverse variance and lets σ fall out of the fusion; a
result is folded the same way.** That is what stops onboarding and the update rule developing
two definitions of uncertainty, which is the reason `racketskill/core.py` was extracted before
either existed.

What differs is *what kind* of evidence a result is. **An answer is a statement about you; a
result is a statement about the gap between two people.** So the observation is relative, and
the shape is Elo's — an expected score over a Level difference — with the Bayesian weight
wrapped around it. In one sentence:

> Your Level moves by **how surprising the result was**, times **how unsure we are about you**,
> divided by **how unsure we are about them**.

**The relative form is forced, not preferred.** The absolute form — *a win says you play about a
third of a Level above them; fuse that in* — was written and tested first, and it breaks
`AtStake`'s invariant on its second pairing: losing to somebody a Level above you **raises** your
Level, because having been on court with them at all is evidence you are better than we thought.
That sentence is genuinely defensible and the card cannot print it. `win_delta > 0 > loss_delta`
is what rules out the whole family.

The rule is `backend/app/engines/racketskill/update_v1/`, pure, and it is **a version directory
rather than a module beside `core.py`** — ADR-0015's *a version is a directory*, applied for its
own reason: every constant in it is an admitted hypothesis, and retuning one in place would
change what `racketskill-result-update-v1` means on rows already in the store. `core.py` is for
what outlives a version, and this is emphatically not that. It carries its own stamp beside the
questionnaire's, because a Level that has been tested by results was last written by this and
attributing it to the questionnaire would make the one thing a retune has to be traceable
through a lie.

### 2. Five constants, each with a falsifier

| Constant | Value | What it says |
| --- | --- | --- |
| `ODDS_DECADE_LEVELS` | 1,70 | the Level gap at which the stronger player is a **ten-to-one** favourite |
| `RESULT_MOVE_CEILING` | 0,15 | the most one **whole observation** may move a Level |
| `SHARED_COURT_SHARE` | 0,5 | how much of a four is evidence about any one of the four |
| `STABLE_SIGMA` | 0,30 | the uncertainty at which a rating is called **Stable** — 75% confidence |
| `SETTLED_SIGMA_FLOOR` | 0,10 | the uncertainty the platform will never claim to be inside |

**`ODDS_DECADE_LEVELS` does two jobs and cannot be split.** It decides both how decisive a gap
is and how much a result at that gap teaches — because a result between mismatched people is
exactly as uninformative as it was predictable. At 1,70: half a Level is two to one, one Level
is four to one, two Levels is fifteen to one.

**The move ceiling is a brake, not the rule**, and it is where §"σ is a floor" is paid. Left to
itself the arithmetic moves a rating fresh out of onboarding by ±0,36 on an even game and ±0,62
on an upset — which is what Glicko does with a provisional player and is right when σ is a
measured posterior. It binds for roughly the first ten counted games and never again.

Two properties of the brake are load-bearing:

- **It scales both sides by one factor**, so a braked pairing keeps its shape. Capping each
  delta on its own would make losing to somebody far above you cost exactly what losing to an
  equal costs, which is the opposite of what the pairing said. A fresh player against somebody a
  Level above reads `+0,150 / −0,039`.
- **It holds back the certainty too, by the same factor.** Braking the Level while letting σ
  tighten at full speed would leave the platform sure of a number it had just refused to move.

### 3. Confidence tightens because the maths says so

There is **no second rule and no schedule**. The information a result carries is the Fisher
information of the outcome — largest for an even game, near nothing for a foregone one — times
the share, times the brake, and σ is the inverse-variance posterior of that. Two consequences
worth stating because they are what the decision buys:

- **A result against somebody nobody has watched teaches less**, and the same expression says so
  in both places: the opponent's own σ flattens the expected score *and* shrinks the move.
- **A foregone result tightens nothing.** Two players three Levels apart learn nothing about each
  other by confirming what everybody knew.

Confidence after *n* counted singles games against opponents the platform knows, starting from
onboarding's 30%:

| n | 1 | 5 | 10 | 20 | 25 | 50 |
| --- | --- | --- | --- | --- | --- | --- |
| confidence | 34% | 48% | 60% | 72% | **75%** | 82% |

Every figure in this record is **derived from the shipped rule**, not estimated beside it — the
table above, the braked pair in §2 and the two doubles figures in §5 are each asserted by a test.

**A club season makes you known.** Twenty-five counted games is what *Stable* costs against
people we know, and longer against strangers — which is the point of putting the bar on σ.
A doubles-only player reaches 68% over the same twenty-five — 55% at ten, 77% at fifty — by §5.

`SETTLED_SIGMA_FLOOR` is the σ analogue of *confidence is never 100*: people change, take
winters off and find a coach, so even a player watched for years is not known to better than
±0,10. Without it a heavy user's σ walks toward zero and the likely range printed on their
profile becomes a claim nobody could defend.

### 4. A count opens the door and certainty closes it

**Initial Estimate → Calibrating** on the **first** confirmed counted result. **Calibrating →
Stable** when σ reaches `STABLE_SIGMA`.

This is what `CONTEXT.md` already says word for word — *Initial Estimate (onboarding output, no
counted matches) → Calibrating (real matches started, still moving) → Stable* — and each
boundary is the honest test for that boundary: *has anything real happened yet*, and *are we sure
yet*.

*Initial Estimate* wins over σ whatever σ says. Onboarding cannot reach the Stable bar today, and
if a retune ever let it, the word would still be a lie about a player nobody has watched.

The two rejected alternatives fail in opposite directions. **A pure count** (0 → 1–19 → 20+) is
trivially explainable and lets somebody whose twenty games were all against unrated strangers
reach *Stable* while the platform is still unsure of them — and the label then lies to whoever
they match next. **Pure certainty** loses the distinction the glossary cares about, and because
onboarding leaves everybody at exactly the σ floor, a first game that barely tightens anything
flips the status by a rounding margin.

**There is no status-change event.** A status is authored by whichever rule moved the rating, so
a transition arriving on its own would be a second author of a word only one thing decides.

### 5. A four is two players, and it counts for half

**Each pair is one player at the average of its two Levels**, with the uncertainty of that
average — independent σ combining as `√(σ₁² + σ₂²) / 2`, so a pair is a better-known quantity
than either person in it. **Both sides go through that averaging**, and the Level move is priced
side against side, so all four move by the same amount in the direction their side went.

**A partner is not somebody you are rated against**, and that is what the sentence above is
guarding. Pricing each player on their own μ against the opposing average reads reasonable and is
the *rejected* option wearing a different hat: two people on the same side of the same scoreline
come out moved by different amounts — 4,0 by `+0,012` and 2,0 by `+0,047` on the same game — which
the card would have to explain, and which pays a strong player to pick a weak partner.

**The Level move is the side's and the certainty is the player's own**, and they separate here for
the same reason the glossary keeps them apart. What the evening taught is a property of the game,
so everybody on the side gains the same information — and folds it into the uncertainty they
actually had. A newcomer and a player watched for years do not come off one court equally sure of
themselves.

That averaging is doing real work rather than being a simplification: **carrying a weaker partner
to a win still moves you up**, with nothing written to make it happen, because the average is
what made the result the upset it was — `+0,0175` beside a 2,6 against `+0,0125` beside an equal.

**And a four is half the evidence about you**, because you were half of what happened. Applied as
a weight on the whole observation — the Level move and the certainty it buys together — and
**the ceiling is share-scaled with it**, so a four's ceiling is 0,075. That last clause is not a
detail: with an absolute ceiling both a padel evening and a squash evening would cap at the same
figure for exactly the players the share was decided for, and *a four is half the evidence about
you* would have been true of everybody except the provisional padel players it was written about.

**Split by partner strength was rejected.** Moving the weaker partner more on a win reads as fair
and pays you to pick partners weaker than you, which is the opposite of what a matchmaking
marketplace wants — and it gives two players on the same side of the same scoreline different
answers that the card would then have to explain.

Which sport is a four is read from the closed `SPORT_SPECS` registry — padel and badminton — on
the precedent `challenges/domain/seats.py` set. A second table of *how many people play this*
would be a second place for padel to stop being doubles.

### 6. *At stake* is not a preview of the rule; it **is** the rule

`stakes()` always computes **the pair**, and `rating_after()` applies the branch that happened.
A card promising `+0,07` and an update delivering something else is not a state the code can
reach, because the ceiling has to see both sides to scale them together anyway.

`AtStakeQuery`'s registered implementation is `RatingResultUpdateRule`, which reads two Levels
through a new narrow port and calls that same function. `NoResultUpdateRuleExists` is **deleted**
— the second of the three null objects to retire by its own stated fact becoming false, and the
swap was one row in the register, exactly as [ADR-0095](0095-block-directed-record-symmetric-effect-gates-fail-closed.md)
promised.

**The card prices the pairing it is showing you**: you against this person, with that sport's own
share applied. In a doubles sport the game will be a four and the other two seats are unknown
when the card is drawn; averaging against an imaginary partner would be inventing the one thing
the read has no basis for.

**A `None` here is measured and means one thing** — either party unrated in this sport — and the
block is omitted, never drawn as a pair of zeros.

**The adapter lives on the matcher's side, and that is forced rather than chosen.** `CONTEXT.md`
says *not the matcher, which reads what a player is shown and never re-derives it*, which reads
like an argument for putting it in `rating` — but `AtStake` is the **matcher's** type, and a
provider that imported it would be a provider that knows a matcher exists. `games` is fenced from
exactly that, in `.importlinter`, by name. So the adapter sits at
`matchmaking/infrastructure/rating_at_stake.py` beside `games_match_history.py` and
`users_account_status.py`, and the rule it is forbidden to re-derive it does not: it **calls**
`update_v1.stakes`, the same function that moves the Level when the game is played. *Never
re-derives it* is satisfied by there being one implementation, not by which directory the call
sits in.

**One rounding rule is worth recording because it looks like a bug.** Deltas are published at
four decimals and **never rounded to zero**: a foregone pairing prices the expected side at a few
hundred-thousandths, and `round` answers `-0.0`, which is not a small number — it is the claim
the invariant exists to refuse. Under the resolution, the sign is kept and the smallest thing the
resolution can hold is published.

A Level itself is carried to **two** decimals, as it always has been, and the rounding lands on
the **new Level** rather than on the move — so a run of results each too small to show still
climbs: 3,00 → 3,0067 → 3,01 and on from there.

### 7. The rating streams are the cursor

ADR-0137 predicted this ticket would *read games forward from a cursor*. It reads games forward;
the cursor is not the one that sentence imagined, and the difference is the decision.

**Every move records the game that caused it**, so *have I applied this result* is answered by
replaying the aggregate that would be changed. There is **no cursor row, no table and no
migration** — which means one fewer record of progress to be stale, and the first one to be wrong
would have been the one nothing could check. A catch-up that dies half way costs a repeated read
and never a repeated move.

**`games` publishes `ConfirmedResultLedger`**, which answers *every counted game confirmed by
this instant, oldest first*. Oldest first is the contract and not a convenience: a Level is moved
against the Levels as they stood, so applying Tuesday's result after Thursday's produces a
different rating for the same history and nothing would ever say so. The order is
`(confirmed_at, game_id)` — the moment the result became final, **derived** from the record and
the clock like every other fact in that context, so it is the same instant on every reader's
clock and there is no column anybody has to keep current.

**A `SettleRatingsOnResults` job runs it hourly**, on ADR-0092's embedded-loop mechanism and the
challenge lapse loop's shape: one transaction per game, a version conflict counted and stepped
over, no lock. **It is the only job on that list that correctness depends on** — every other one
buys a record or a table's size — and that is stated in its own docstring so nobody switches it
off thinking it is a sweep.

**A four moves four ratings against one snapshot**, read before anything moves, so nobody's
number depends on where they came in the loop.

**Nothing moves a Level that should not.** An unscored game and a friendly are both absent from
the ledger, so *an evening is not evidence* and *a friendly is a thing people choose* are
enforced by the read rather than by a branch anybody could forget.

## Considered options

**A chess-style K-factor with a written σ schedule.** Familiar, and every constant defensible on
its own. Rejected on two counts. It is **two rules tuned independently**, and two rules about one
player are two places to disagree — the exact failure `racketskill/core.py` was extracted to
prevent. And a schedule counts games, so it cannot tell a win over a stranger from a win over
somebody we know cold; the Bayesian form gets that for free, from the same expression that
produces the expected score.

**Faster settling — about ten counted games.** Places people quickly, and ±0,30 is most of a
band: two lucky nights move a player across a band boundary and matchmaking believes it. Under
*silence confirms*, a wrong score nobody bothered to counter would be worth ±0,30, which is a lot
to hang on inattention.

**Slower settling — about fifty.** Nobody's Level swings on an evening, and *at stake* reads
`+0,09 / −0,07` on the card — a block that small stops being a reason to tap anything. A newcomer
stays provisional for months and the matcher stays wary of them the whole time.

**Damping the mean update by a constant instead of a ceiling.** It hits the same headline number
for a fresh player and keeps shrinking the move for everybody: a settled player's even game drops
to ±0,02, which is invisible on a card. The ceiling leaves the settled regime untouched and tames
only the provisional explosion, which is the only place the problem was.

**A `ResultConfirmed` event, or a sweep that appends one.** Considered and rejected by ADR-0137 on
its own ground — a durable name for a *standing* is the second place for it to be true — and the
argument has not moved. What has changed is that the cost turns out to be smaller than that
record feared: the streams that would be changed already know what they have folded.

**A cursor row for the catch-up**, as the candidate-index tail has. Rejected because the index's
cursor is over an append-only sequence with nothing else recording its position, where this one
would sit beside a per-rating record of the same fact. Two records of progress, and the cheaper
one to read is the one that would be believed.

## Consequences

**Easier**

- **The competitive card's last empty block fills.** `at_stake` is populated in competitive, its
  description stops saying *omitted today*, and the number is the same one the game will deliver.
- **A rating stops being a hypothesis nothing can test.** *Initial Estimate*, *Calibrating* and
  *Stable* have been three words in a glossary with nothing driving them since the reset.
- **The matcher's skill term gets sharper without being touched.** Every σ that tightens narrows
  a forecast that reads it.
- **Two null objects left, and both still say something true.** `NoPlayerScoresExist` and
  `NoHoldsExist` remain because nobody has ever been due to turn up and nothing can open a case.

**Harder**

- **The catch-up walks every game the platform has recorded, every hour.** The same cost profile
  as every other read in `games` and stated in the same words — the pagination that fixes it
  belongs with the first run that measures it, and it will want `confirmed_at` somewhere a
  `WHERE` can reach, which today is derived and nowhere.
- **A Level now moves without anybody doing anything.** Silence confirms, and an hour later a
  rating has changed. That is the design, and it is the first thing on this platform that is
  true of.
- **Five constants are hypotheses and none of them is a measurement.** Their falsifiers: how many
  counted games players actually reach before their σ stops moving; whether the ceiling binds
  past the tenth game once real pairings replace even ones; and whether the doubles share
  produces padel Levels that visibly lag tennis ones for the same population.
- **The ceiling flattens the provisional period, on purpose.** For roughly the first ten games
  the card reads ±0,15 on most pairings, and the shape only reappears once a rating settles. A
  player watching closely will notice.
- **`at_stake` is priced head-to-head in a doubles sport.** It carries padel's share, so the
  magnitude is right; what it cannot know is who the partners will be, so the *pairing* it prices
  is not quite the game that gets played.
- **Two decimals is the Level's resolution, and a pairing lopsided enough can round back to
  nothing.** It takes a gap the matcher would never draw, and the alternative was a second μ at a
  second precision, which is the two-sources-of-truth defect this repository refuses everywhere
  else.

**Neutral**

- **`SkillRating` gains its second transition and no table.** The streams are already in
  `event_store`; there is no migration in this change.
- **The three status words move to `racketskill/core.py`**, where the scale and the confidence
  transform already live. `v3` reads *Initial Estimate* from there instead of spelling it, and
  the stored value is unchanged.
- **`RatedPlayerQuery` is the first thing `rating` publishes that is not an aggregate**, and it
  brings the third demands register with it. A reader that only wants two floats has no business
  with the repository that remembers stream versions so a rating can be saved — and a port with
  one consumer that fails soft is exactly the kind whose quiet breakage nothing would report, so
  it is contracted in `tests/demands/` like the other two registers' rows.
- **Inactivity still moves nothing.** *Absence widens, it never lowers* is unimplemented and stays
  so; it is a fact about time passing rather than about a result, and it needs the same treatment
  this record gave the update — argued, not assumed.
