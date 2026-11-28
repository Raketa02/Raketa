# ADR-0136 — The split is evidence for the forecast, and never a second score

- **Status:** Accepted
- **Date:** 2026-09-02

> **Note — the Classic play removal (2026-10-06, [#569](https://github.com/Rakieta02/Rakieta/issues/569)).** The line-up and forecast routes are gone (#579, #580), and with them `ArrangementSchema`, `is_current`/`is_best`, *Even it out* and the group objective `G` this record kept off the wire. The split survives on one route: `GET /games/{id}/pairing` serves `your_side`, `their_side` and a signed `gap` beside the forecast, in the reader's direction, from the engine's `Split`. The input-versus-second-score boundary and rules 2 and 3 stand as written.

## Context

ADR-0117 settled what a line-up may say
about itself, and one sentence of it is a refusal: **`G` is recorded and never returned.**
A second score the player must trust is worse than none — it competes with Fit, and nobody
can act on it — so the evidence half is paid by one closed reason code naming the term with
the largest margin over the runner-up, and `ArrangementSchema.is_best`'s own description
carries that refusal in the contract.

The builder's forecast card, meanwhile, prints one number: *90% · Very even*. The design it
is built against prints **two side strengths, the gap between them and a two-segment bar**
(`design-system.md` 7.11, `BalanceBar.advantage`). Every one of those is a number only the
engine has. `SidesSchema` carries seats and no strengths; `ArrangementSchema` carried none
either. A side's strength is not the mean of the two people on it — the weaker partner sets
more of it (`the-group-objective.md` §3.1's `TEAM_STRENGTH_SHARE`, 0.55 to the weaker half)
— so a client drawing the bar would have averaged the seated players' levels and printed a
pair of numbers the engine never computed. That is `the-play-screens.md` §11.3's *"no
forecast arithmetic on the client"*, and it is the one rule in that document whose check is
**looking for arithmetic rather than reading intent**. The card was therefore stuck at a
percentage a player either believes or does not.

So there is a real question, and it is not *may we return more*. It is: **what may cross
beside a forecast, given that one number next to it is already written down as refused?**
The two candidates look alike from a distance — both are figures the engine holds, both
would make the card more convincing — and the distinction has to be recorded rather than
re-derived by whoever asks next, because the cost of getting it wrong is asymmetric. Old
builds live on real phones for months: a field withdrawn later is a card that silently
loses a third of itself, and `openapi.player.json` is a contract this repository is not
free to shrink.

Two shapes were available and both were rejected.

**Leave the client to subtract.** Serve the two strengths and let the bar take the
difference. It re-opens §11.3 by exactly the amount it saves — and worse, the client would
be subtracting two *rounded* figures where the engine subtracts two unrounded ones, so the
two disagree at the boundary on a card that prints all three numbers.

**Serve it on `ForecastSchema`.** It is *one type, everywhere it appears*, and it rides on
every shortlist row's `would_be_forecast`. A response carries at most three arrangements and
tens of candidate rows, so that placement pays for the field twenty times over to say
something that is not true of a forecast in the first place: a split is a fact about **an
arrangement** — who is on which side — and a `would_be_forecast` has no arrangement.

## Decision

**We will return the split as evidence for the forecast, and we will not return the group
objective.** The line between them is: *an **input** to a figure the response already
serves may cross; a **second figure the player would have to trust** may not.*

`ArrangementSchema` gains a required `split` — `your_side`, `their_side`, and a **signed**
`gap` — beside `sides` and `forecast`, on both routes that return arrangements.

Four rules make the field mean one thing:

1. **On the arrangement, not on the forecast.** A split is *which side is which*, which a
   `Forecast` does not know.
2. **The four numbers are one computation.** `pct`, `your_side`, `their_side` and `gap` come
   off one reading of the two sides. In the engine that is structural rather than
   remembered: `_predicted` returns a `Split`, `Split.gap` is a **property** — so no
   constructor can take a difference its own two strengths do not make — and
   `Arranged.side_gap`, the number *Even it out* selects on, is `abs(split.gap)` rather than
   a second subtraction. A card reading `gap 0,00` beside `74% · fairly even` is the failure
   this is written against.
3. **`gap` is signed**, `your_side − their_side`. The bar takes an advantage; an unsigned
   gap would leave the client deciding which half is bigger, which is the same arithmetic
   in a smaller disguise. The sign is not a constant of a four either — it is a fact about
   the way round, and for a four at 3.0 / 3.2 / 3.5 / 3.8 the three arrangements read
   −0.545, −0.245 and +0.025.
4. **A provisional arrangement carries a split like any other**, under the same assumption
   `pct` is carried under: the empty seat is read as if the missing player matched the one
   already there, so `provisional` caveats all four numbers at once and none of them moves
   when the twin sits down.

**We will also make `is_current` on a line-up the evenest arrangement**, in both modes.
Which way round the four sit is the question balance answers, and *Even it out* is the tap
that answers it; a builder that opened on `is_best` showed a court whose first tap undoes
it. Who is on the court does not change — the objective still chose the four, `group_reason`
still says why, `is_best` keeps its meaning and keeps crossing — and `lineup.seats` follows
`is_current`. **`ForecastResponse.is_current` is untouched**: there it means *the seat order
you sent*, and a client that sends an arrangement must get that one back marked current or a
swap cannot be drawn.

`G` stays exactly where ADR-0117 put it. It is not a field, it is a property of the terms
that produced it, `GroupScore.arranged` is the projection a screen may see, and nothing in
this decision gives it a path onto the wire.

## Consequences

**The card can be argued with.** A player sees *what against what*, on the scale they
already read levels on — `matchmaking-engine.md`
§12 rule 1, *name the evidence, not a category*, which is the same rule that put `sigma_group`
beside `pct`.

**§11.3 stays checkable.** Its check greps for arithmetic; every number the card needs is
now served, so there is nothing left for a client to be tempted by — which is a stronger
position than the one before this change, where the design demanded numbers the contract
did not supply and the pressure was all in one direction.

**The boundary is written down, so the next ask is decided rather than argued.** *Is this
an input to a figure we already serve, or a second score?* `G` fails that test; so would a
per-seat contribution, and so would any figure whose only use is to be trusted.

**It is expensive to un-ship, and that is accepted rather than unnoticed.** Three floats on
the hottest payload in the product, on old builds for months. The bound on the cost is that
the fields are **derived from a computation that already runs** — no new term, no new
constant, no new ruleset row — so nothing here can move a number the engine produces, and
`make gen-judged-pairings` and `make gen-ruleset-diff` regenerate byte-identical.

**A line-up opening on the evenest is a behaviour change with no data behind it yet.** It
is the arrangement the player would have reached in one tap, so the change is small by
construction; what it costs is that the first thing a builder shows is no longer the one the
objective ranked first, and `is_best` is now a fact the screen has to draw rather than the
frame it draws in. If that turns out to read as the engine hedging, the fix is a screen
change and not a contract one — both booleans cross either way.

**Payload.** Three floats per arrangement, at most three arrangements per line-up. It is not
on candidate rows, which is the placement that would have mattered.
