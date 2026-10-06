# ADR-0114 — A newcomer may not be declined: printed, never optional, capped

- **Status:** Accepted
- **Date:** 2026-08-26

> **Note — the Classic play removal (2026-10-06, [#569](https://github.com/Raketa02/Raketa/issues/569)).** The search, its liveness reasons and modifiers, the exposure ledger and the welcoming modifier are gone (#579, #580), so decisions 1, 3 and 4 and the 2026-08-28 amendment describe nothing that runs: nothing prints newness and nothing volunteers anybody, so there is nothing for a cap to bound. Decision 2 stands and is tested (`tests/unit/test_level_window.py`): no profile, commit or ruleset field lets a player decline newcomers, for the reason the Consequences give against ADR-0096. A newcomer's protection is now ADR-0113's tightened level window on every pair the Games deck would seat.

## Context

§9.10 of `matchmaking-engine.md` ends on the
asymmetry:

> **And make it worth the veteran's while.** Playing a newcomer should not feel like community
> service. […] the card says what is happening: *"They're new — this game does most of its work
> for them."* Most people are glad to be asked; nobody likes finding out afterwards.

It says the cost should be printed. It never says whether it may be **refused**.

Resolving [#175](https://github.com/Raketa02/Raketa/issues/175) on the map
[The matchmaking engine: who sits down, and why](https://github.com/Raketa02/Raketa/issues/155)
put the question directly, because this platform has already answered a question of exactly this
shape and answered it the other way.
[ADR-0096](0096-gender-preference-mutual-gate-invisible-to-the-scorer.md) overruled the design
document's §23 Q8 and gave players a **Gender preference** — *a player may say who they want to
play with, out of the box* — made mutual so it protects an inbox and not only a search.

*May a player say who they will be matched with* now has two answers in this repository, and a
reader finding them side by side without the argument will assume one is a mistake.

§14.4 supplies the other half of the context. A player sitting on unanswered challenges is
lowered in liveness and eventually withheld, because the alternative is the death spiral the whole
of §14 exists to describe: they are flooded, they stop answering, their answer rate falls, and
**the matcher punishes them for having been popular**. Any mechanism that systematically points
newcomers at the same helpful players walks into that spiral deliberately.

## Decision

**Printed always. Never declinable. Capped.**

1. **Printed, both directions**, as codes the client renders
   ([ADR-0022](0022-kernel-negative-space-and-constant-homes.md),
   [ADR-0106](0106-evidence-vocabulary-is-contract-weights-are-configuration.md)):
   `newcomer_window` in `liveness_reasons[]` tells the veteran the candidate is new;
   `welcoming_record` in `modifiers[]` tells the newcomer this candidate plays opponents whose
   rating is still settling.

2. **There is no setting that declines newcomers.** Not a toggle, not a search-scoped narrowing,
   not a preference with a default.

3. **The ask is bounded instead.** Appearances in a **newcomer's** shortlist are counted per week
   per sport on the existing exposure ledger. Past the cap, the **welcoming modifier** is
   **dropped** — the player still ranks on their merits — and they are **never withheld from
   generation**. *(Amended 2026-08-28 — see the amendment below. As accepted, this clause dropped
   the newcomer-driven reorder as well.)*

4. **Nobody is told the cap bound.**

## Consequences

**This reaches the opposite conclusion to ADR-0096 on purpose, and the distinction is not
seniority.** ADR-0096's case rested on **mutuality protecting an inbox**: a one-directional gender
filter would leave a woman open to every man who searched `ANY`, so the preference had to govern
both what a player sees *and* whether they can be seen. A *no beginners* switch has no such
structure. It cannot be mutual — a newcomer declining veterans is incoherent — so it could only
ever exist as the one-directional preference over people that ADR-0096 refused by name. And it
protects nobody: the cost of a newcomer is a worse evening, not a risk.

**The consequence of allowing it is specific, not vague.** Newcomers are matched by the strongest,
most reliable half of the pool, because those are the players `welcoming_record` and the tightened
gate select. Handing that half a switch lets the pool's most useful players opt out of the single
mechanism that gets a newcomer a first game. That is the cold-start trap of §14.3, entered through
the door built to escape it — and in a market this thin, a handful of opt-outs is the difference
between a newcomer path and a slogan.

**The pressure the refusal creates is real and is not waved away.** §14.4 describes exactly where
it ends. So the valve is a **bound on the ask** rather than a switch: a player may be volunteered
to newcomers only so often, after which the engine stops preferring them for it. Bounding the ask
keeps the player's own agency intact where it matters — they still decline any individual
challenge, for any reason, and a player they want gone entirely is a
**[Block](0095-block-directed-record-symmetric-effect-gates-fail-closed.md)**. What they cannot do
is pre-refuse a *class* of people.

**Never withheld, and this is where it departs from §14.4.** §14.4 withholds at
`open_challenges ≥ 8` — a remedy for a **measured** full inbox, a fact about that player right
now. This cap measures only how often the engine has *volunteered* somebody, which is a fact about
the engine. Withholding on it would make a thin pool thinner for the person who can least afford
it, on a suspicion of load rather than evidence of it. Dropping the lift is the proportionate
move: it removes the engine's thumb, not the player.

**Nobody is told, because nothing has happened to them.** §14.4's rule — *the person whose inbox
is full is told, and the searcher is not* — is about a fact the player can already see for
themselves; telling them names something they are living. This cap has no symptom: their own list
is unchanged, their inbox is unchanged, and the only thing that moved is how often the engine puts
them forward. A notification here would manufacture a grievance out of an internal fairness
adjustment, and it would also be the first time this platform told somebody how the engine ranks
*them*, which is a much larger door than this decision needs.

**One collision, real but not yet live.**
[#171](https://github.com/Raketa02/Raketa/issues/171) settled that *a reason line never restates a
value the card already renders*, and the player card carries `counted_games`. Newness here is a
**date**, not a game count — a player twenty days in with no games is not in the window — so the
two are different claims. Today it is moot: `counted_games` reads `matches` and renders absent.
The constraint for the day it lands is that the two stay **distinct facts**, not that either goes.

**The falsifier:** answer rate of the players who absorb the most newcomer appearances, regressed
on absorption. If it does not fall as absorption rises, the cap is guarding against something that
does not happen and its number is too tight — or it should not exist. If it falls anyway, the cap
is too loose. Either way the measurement, not the argument, moves it. It needs the outcome half of
the telemetry chain, so it ships as an argued judgement with its falsifier attached.

**What would reverse it.** Evidence that helpful players leave rather than absorb — that the cap
is not the valve, and that the only thing that keeps them is a real refusal. That is a claim about
people, and it would be settled by watching them, not by arguing about it here.

## Amendment — 2026-08-28: the cap bounds veterans, and the lift is left alone

Building the cap ([#214](https://github.com/Raketa02/Raketa/issues/214)) found that decision 3's
two clauses reach **opposite populations**, which is invisible in prose and unmissable in code.

`welcoming_record` fires for a player who has *played opponents whose rating was still settling* —
an experienced player, and exactly the half of the pool this record says the newcomer path leans
on. `NEWCOMER_LIFT` fires only when the **candidate is themselves inside the window**. So capping
both meant that on the day the integer shipped, the cap's reachable effect would have been to take
the `+8` from newcomers appearing in other newcomers' lists — cutting the subsidy from the very
people the cap exists to keep from being leaned on, and doing it hardest in a thin pool where
newcomers see mostly each other.

**The cap now binds the welcoming modifier and nothing else.** It reads the candidate's absorption
tally at stage 4; stage 6 does not read it and carries no field that could. Everything else in
this record stands unchanged — printed always, never declinable, never withheld, nobody told — and
this narrowing strengthens rather than weakens the sentence the Consequences argue throughout:
*newcomers are matched by the strongest, most reliable half of the pool, because those are the
players `welcoming_record` and the tightened gate select*, and the cap is the bound on how often
the engine volunteers one of them.

**The cost is that the cap has no reachable effect until `matches` lands**, because the welcoming
record is `NoEvidence` until then. That is the correct cost: it ships **wired and never binding**
either way (the integer is still refused), the tally is counted from today so the integer can be
chosen against real weeks, and a mechanism with no effect is better than one whose only effect is
backwards.

**What would reverse the amendment.** Evidence that newcomers absorb newcomer load at a rate that
matters — that a newcomer volunteered into every other newcomer's list is a real cost to somebody.
That is a measurement over the durable search rows, not an argument, and it would return as its
own bound rather than by re-broadening this one.
