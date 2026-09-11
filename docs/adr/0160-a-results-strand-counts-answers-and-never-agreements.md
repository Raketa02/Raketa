# ADR-0160 — A results strand counts answers, and never agreements

- **Status:** Accepted
- **Date:** 2026-09-08
- **Overturns nothing in [ADR-0137](0137-a-result-is-the-record-that-a-game-happened.md)
  §5, and that is the whole of Decision 1.** *Confirms results* stays struck; what ships
  here is a different measurement over the same events.
- **Amends [ADR-0140](0140-a-player-score-is-what-the-platform-watched-and-two-strands-is-what-it-can-see.md)**
  — its §4 (*there is no decay beyond the ratio itself*) gains one named exception, and its
  §5 weights take back the 15 they set aside.
- **Is a ruleset release under [ADR-0119](0119-a-ruleset-ships-on-an-offline-diff-and-a-deploy.md)**:
  `2026.09.08-a`, with the offline diff committed beside it.
- Settles [#383](https://github.com/Raketa02/Raketa/issues/383) on the spec
  [#373](https://github.com/Raketa02/Raketa/issues/373), whose
  `docs/specs/player-record/the-decisions.md` §4 and §6 are the product decisions this
  record carries out.

## Context

**The player record sheet prints metered rows, and there are two of them.** *Shows up* and
*answers challenges* are what the platform can watch a person do
([ADR-0140](0140-a-player-score-is-what-the-platform-watched-and-two-strands-is-what-it-can-see.md)),
and the sheet's own promise — *counted by the system, not written by people* — is the
strongest thing on it. Two rows is a thin promise. The obvious third row is about results,
and it is the one this repository has already refused in writing.

**ADR-0137 §5 struck *confirms results* and gave a reason that has not aged.** An
unconfirmed result is a fact about a **pair**; a strand is a verdict about a **person**;
and every denominator tried on it docked somebody
[ADR-0049](0049-an-unscored-match-is-an-evening-not-evidence.md) protects. Its table is
explicit — *counted games played* docks both sides of every disagreement including the one
who was right, and *games where a score was put in front of you* docks the side whose
honest counter the other side then ignored.

**What makes that argument bite is that silence confirms.** ADR-0137's own three endings
say so: a lone score is agreed when its window closes, so **ignoring a result and agreeing
with it produce the same outcome**, and the *only* games that end unconfirmed are the ones
where two people put different scores up and neither gave way. A row counting confirmations
would therefore be a row counting **disagreements**, printed under a word that sounds like
diligence.

The product owner asked for the row anyway, was shown the conflict, and reaffirmed it
(`the-decisions.md` §4). What follows is not that refusal being overridden. It is the
observation that **the refusal was about a denominator, and there is another one.**

## Decision

### 1. The strand counts answers, and it is not the strand that was struck

We will add `ReliabilityStrand.ANSWERS_RESULTS`, published as **Answers about results**.

| | |
| --- | --- |
| **Opportunity** | a score put in front of that player, whose window has closed |
| **Good outcome** | they answered inside the window — **accepting counts, countering counts** |
| **Miss** | silence until the window closed |

**Why this is not a reinstatement**, stated against ADR-0137's own table rather than around
it:

- ADR-0137's objection is that a denominator would have to **decide who was wrong**. This
  one decides nothing of the kind. A counter is a good outcome, so the player who believes
  the score is wrong and says so is credited for saying it — and the other side, whose
  honest score was countered, is credited for having opened. **Neither of the two people in
  a disagreement is docked by this strand for the disagreement.**
- The strand it replaces would have found *ignoring* and *agreeing* indistinguishable,
  because silence confirms. This one is precisely the measurement that tells them apart:
  the numerator is the tap, the denominator is the question, and the confirmation is not
  read at all.
- ADR-0049's sentence is *"no player is penalised for not entering or not agreeing a
  result."* Not agreeing costs nothing here. **Not answering costs something, and that is
  the change** — argued rather than smuggled: what is priced is not opening the app when a
  question was put to you, which is the same act *answers challenges* has priced since it
  shipped, on a surface where the platform can see the question was delivered.

The name is load-bearing and is not a synonym. Keeping the word *confirms* over a number
counting answers would mean a player who counters a score they believe is wrong watches
their *confirms* figure **rise** — and that player is exactly the one who would notice.
The word `ANSWERS_RESULTS` reaches the wire; nothing in this repository spells it
*confirms* again.

### 2. The opportunity is a score put to a side that has not put one up

`games/domain/answering.py` folds one question out of a game, and **at most one**:

- The entry that records *we played* records a score in the same act, so one side always
  **opens**. The opener is asked nothing: their score is the question.
- The other side is **asked once**. Countering is an answer, accepting is an answer, and
  the window is `PROPOSAL_WINDOW` measured from the standing proposal — a correction
  re-dates it, because a score they have not seen has not started their day.
- **Once both sides have put a score up, nobody is asked anything further.** The argument is
  capped at two rounds by
  [ADR-0137](0137-a-result-is-the-record-that-a-game-happened.md) §4, so the opener facing a
  counter may only **give way**. Filing their silence as a miss would price surrender, which
  is docking somebody for disagreeing by another route — the exact failure Decision 1 claims
  to avoid, arriving one act later.
- A score still inside its window is in **neither half**, the rule every strand here keeps.

The fold lives in the domain beside `standing.py` rather than inside the query, because
*whether a counter is an answer* is a judgement about what a result is. `games` publishes it
as `ResultAnswering` on `GameHistoryQuery` — a sixth fact, the same shape and the same
absence rule as `attendance_for`: **a player nobody ever put a score to is absent from the
answer**, never `0/0`.

**Friendlies count.** A score is a question whether or not the evening was evidence about
anybody's Level — the same reasoning ADR-0140 §3 applied to turning up.

### 3. It forgets after twelve months, and it is the only strand that does

ADR-0140 §4 rejected a rolling window for the two strands it shipped, on the grounds that a
window would be a second number that must not disagree with the matcher's `horizon_days`,
and would make *out of what* stop meaning a career. **That reasoning stands for those two
strands and this record does not disturb it.** `ANSWERED_RESULTS_WINDOW` is a named
exception, and the reason is what this strand prices.

Turning up to a game and answering an invitation are **commitments somebody made to another
person**. Answering a score is a **habit of opening an app**, and ADR-0049 has already said
in as many words that a flat battery and simple inattention are the same event to us. A mark
for something that cheap to fail by accident, carried for a career, is a mark a player cannot
work off — and the whole reason the reliability floor reads the *published* number is that a
player who repairs their record must be able to watch the penalty lift.

**Twelve months, chosen to equal `horizon_days`.** The cost ADR-0140 named is real and is
paid rather than avoided: they are two spellings of one judgement, in two contexts, and
`player_score` may not read the matcher's ruleset — a provider importing the consumer it
serves is the arrow every port here keeps. So the agreement is asserted by a test
(`tests/unit/test_player_score_strands.py`) rather than by construction, and the day somebody
moves the horizon, that test is what says the window has to move with it.

**The window is the caller's and never `games`'.** It crosses the port as an instant. A
game's three clocks are what a player is promised; *how far back a strand remembers* is a
judgement about what a record is worth, and it belongs to the context that publishes the
strand.

### 4. Per-strand minimums replace the single number

`ReliabilityRules.min_observations` becomes a `Mapping[ReliabilityStrand, int]`, exhaustive
over the vocabulary and refused if a key is missing.

*Answers about results* asks **five**; the other five keep **three**. Raising the single
number to five instead would take a brand-new player who has played three games and turned
up to all three from a full score to **no score at all** — a decision about how this product
treats newcomers, arriving as a side effect of tuning one strand. A shape that cannot express
*this strand needs more evidence than that one* is a shape that forces that trade.

A missing key is an invariant violation rather than a default, because a strand whose bar was
never set would enter a reading on its first observation and nothing downstream would notice.

**The bar is the matcher's, the published figure has never had one, and that is a choice
this record makes rather than inherits.** `the-decisions.md` §4 says the strand *"enters the
reliability number and the matcher … with a minimum of 5 results put to that player before it
counts"*, and #373's story 65 asks that a short results record *"stay out of my number"*. Read
strictly, that wants a bar on the published blend too. We are not putting one there, for two
reasons and with the cost stated rather than absorbed:

- **Three is the matcher's number and nowhere else's.** #383's own wording is *the other
  strands keep three* — and three exists only as ruleset data. Giving the published blend a bar
  would not leave the other two strands as they are; it would give them a bar they have never
  had, so a player with one game played and nothing else would have **no published score at
  all**. That is a change to what a newcomer's own profile says about them, arriving as a side
  effect of tuning one strand — which is the same objection this decision makes to raising the
  single number, one layer out.
- **The two surfaces have different honesty mechanisms.** On the sheet, every metered row
  **prints its raw fraction** (#373, story 24), so *nought of two* is visibly a claim about two
  things; inside a ranking nobody can see the fraction, so there the mechanism has to be the
  bar.

**The cost, named:** the reliability *floor* reads the published number, so a thin results
record can move somebody's distance from `published_score_bar` while the strand stands down
inside the term. That asymmetry is not new — ADR-0140 shipped it for *shows up*, where one
ghost out of one arrangement publishes a nought — but this strand makes it reachable more
often, and if it bites, the fix is a bar on the published blend for **every** strand, decided
on its own terms and not as a footnote to this one.

**The bar for `SPORTSMANSHIP` stays at three and is inert**, and that is not the same number
as `the-decisions.md` §6's *1*. That one is about the **published figure**, which
[ADR-0158](0158-a-rating-is-one-per-person-and-the-collapse-is-the-key.md) publishes from the
first rating with the rater count printed beside it. The matcher may not read sportsmanship
at all, so its ruleset bar governs a strand no provider crosses; setting it to one here would
read as the matcher expecting to score somebody on a single opinion.

### 5. A ruleset release, and the weights are restored rather than retuned

`2026.09.08-a` is cut. It moves exactly two things — the two `strand_weights` vectors and the
shape of `min_observations` — and copies the rest of `2026.08.26-a` unchanged.

| | competitive | for fun |
| --- | --- | --- |
| shows up | 25 | 32 |
| answers challenges | 22 | 22 |
| **answers about results** | **24** | **4** |
| keeps plans | 14 | 14 |
| settles up | 10 | 12 |
| sportsmanship | 5 | 16 |

These are the six numbers the vector carried **before** *confirms results* was struck.
ADR-0140 §7 rescaled the five survivors by largest remainder over the smaller vocabulary
precisely because a weight vector must sum to a hundred; restoring the sixth share restores
the five beside it exactly. **Nothing was learned about the other five**, and inventing new
numbers for them would be a hypothesis with no evidence behind it dressed up as tidiness.
The published Player Score blend takes its 15 back for the same reason and is
**35 / 20 / 15 / 12 / 10 / 8** again.

**What the two offline gates print, which is what this release is argued on:**

- **The judged pairings do not move at all.** `reliability` is `None` for every one of the
  six cases, so no term value changes, and `QUALITY_FLOOR` still holds at 44 with the same
  0.50-point margin under the lowest case it must show.
- **The synthetic ruleset diff moves nothing but its own version stamp**, and *that is not
  evidence that the release moves nothing.* 416 of 416 searches unchanged, zero reordered, zero
  compositions changed, zero floor crossings, zero emptiness flips, top-1 unchanged, adversarial
  tail unchanged — and the reliability digest in that artifact is the **empty-input hash**,
  because nobody in the synthetic population has a Player Score. The gate is measuring a
  population this release cannot touch. It is printed by the report rather than assumed, and it
  is why the *claim* below is the part of this release that has to be argued rather than the
  rates.
- **Two of the three walkthrough goldens move, by 0.016 and 0.009 Fit points, on one
  candidate**, and those are the *same two numbers* ADR-0140 §7 recorded when the vector was
  rescaled — this release rounds them back. `0.37375 → 0.375` and `0.349 → 0.35`. The third
  walkthrough has no Player Score in it at all and does not move. No order changes and nobody
  crosses the floor.

The measurable diff is therefore small, and the **claim** is not: on deploy, every player
who has a record is re-mixed, because a third strand enters the published blend and both
mode vectors. Some players' matcher penalty will appear or lift through no action of their
own. That is a one-off and it is the thing to say to players if a channel for it ever exists.

### 6. The frozen dataset had to say something about a word it never knew

`2026.08.26-a` is edited in place a second time, for the same kind of reason as the first and
not a different one. A strand vector is validated as **exhaustive**, so a released dataset has
to name every member of the vocabulary — and the vocabulary widened.

The exhaustiveness is itself a choice, and the alternative was a **default** — an unset bar
reading as one — which would have left the released dataset untouched. Decision 4 refuses it:
a strand nobody set a bar for would enter a reading on its first observation, and a default is
how that arrives silently. Paying for it in the frozen file is the smaller of the two costs.

What it says is **nought in both modes**, which is not a weight anybody chose but the fact
restated: no search that version ever ran could read a strand the platform could not publish.
The five real weights are untouched, both vectors still sum to a hundred, and
`min_observations` is the same three it always was, now spelled once per strand because the
field's shape moved under it. **A number moving is still a new dataset; a vocabulary widening
is not one** — the precedent is ADR-0140 §7 removing a key from the same file.

## Consequences

**Three strands is still a thin score, and the honest reading has not changed.** *Player
Score 67* means *of the three things we can watch, here is the blend*. What has changed is
that the third of them is the one a player most directly controls from inside the app.

**`TwoStrandsFromTheRecord` is renamed `ThreeStrandsFromTheRecord`**, which its own docstring
promised: it is named for the fact it asserts, so the day the claim moved the name moved with
it.

**The wire gains an enum member and no field.** `ANSWERS_RESULTS` appears on
`openapi.player.json` wherever `ReliabilityStrand` does — the Fit breakdown's strand rows and
the player record's metered rows — and the client regenerates. It is additive: no shipped app
loses a field, and an old client meeting an unknown code is the same problem it already has
for every other code on that contract.

**A doubles pair share one miss and are not asked separately.** Two people were asked one
question and either of them could have answered it, so the pair carries the same figure. That
is the same shape *shows up* takes and a different reason: there, everybody on the court was in
the arrangement; here, one side was asked and the other was not. The person whose partner
answered for them is credited, which is correct — their side answered.

**The strand can be gamed by never entering a score.** Somebody who is never the *asked* side
has no opportunities and no strand, and is absent rather than penalised. Racing to enter the
score first is therefore a way to avoid ever being measured on this row — and it costs a tap,
puts your own score up for the other side to counter, and is indistinguishable from ordinary
diligence. We are not solving it: the behaviour it incentivises is *enter the result*, which
is the behaviour the product wants anyway.

**The matcher's answer to *how much evidence is enough* is now six numbers rather than one.**
That is more configuration surface, and the mitigation is that it is exhaustive and validated
rather than defaulted — a strand added to the vocabulary cannot slip in with an implicit bar.

**The seeded cohort exercises it for free, and only on its good half.**
`app/seeds/games.py` already writes both endings — a score accepted from across the net, and
a score countered — and both are *answers*, so every seeded member on a receiving side gains
this strand at a hundred per cent. Nothing in `app/seeds/screens.py` moves: no member gains a
Player Score they did not already have, because a member who was put a score to was on that
court and therefore already had *shows up*. **What the workbench cannot draw is a miss**, and
the first person who wants a poor *answers about results* row on a screen has to seed a game
whose score nobody answered.

## Alternatives considered

**Ship nothing, and leave the sheet with two metered rows.** The strictly conservative
reading of ADR-0137, and the one this record has to beat rather than ignore. Rejected because
the objection ADR-0137 recorded is specifically about denominators that must decide who was
wrong, and this denominator decides nothing — the argument is answered rather than outvoted.

**Count confirmations and exclude disagreements from the denominator.** *Results confirmed,
out of results awaiting an answer where nobody countered.* Rejected: it is the struck strand
with a hole in it, the hole is *the games where somebody disagreed*, and a ratio whose
denominator quietly drops the interesting cases is a ratio that reads as more than it is.

**Count the opener's silence after a counter as a miss.** The strictly symmetric reading of
*a score put in front of you*. Rejected in Decision 2: the platform gives that side no act
but surrender, so the row would price giving way.

**Raise the single `min_observations` to five.** Rejected in Decision 4 — it changes how the
product treats every newcomer as a side effect of tuning one strand.

**A window this context owns for every strand.** Rejected: ADR-0140 §4's argument against a
window for *shows up* is untouched by anything here, and widening the exception to strands
that did not need it would make *out of what* stop meaning a career on rows where it still
does.

**Edit `2026.08.26-a` in place with the new weights rather than cutting a release.** Rejected
by the rule the file states about itself: a hypothesis moved, so this is a new dataset with a
new name and an offline diff. ADR-0140's edit was licensed by *a word left the language and
no number moved*; both halves of that are false here.
