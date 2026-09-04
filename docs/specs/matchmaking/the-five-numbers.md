# The numbers that decide whether the product says nothing at all

Settles [#167](https://github.com/Raketa02/Raketa/issues/167) and, for two of its numbers,
[#194](https://github.com/Raketa02/Raketa/issues/194) on the map
[The matchmaking engine: who sits down, and why](https://github.com/Raketa02/Raketa/issues/155).

Most of the matcher's constants are a starting vector in a config file. These are **product
decisions wearing a config file's clothes**, because each one decides whether a player is shown
somebody or shown an apology. They are set here, with an argument, a falsifying measurement, and
a named owner — never a provenance.

> **There are seven, and the file was called *the five numbers* until
> [#194](https://github.com/Raketa02/Raketa/issues/194) added `INTEREST_TTL` and
> `PASS_SUPPRESS` (§8, §9).** The title stops being a count rather than the count being wrong:
> the discipline below is the document's content, and splitting it across two files so that
> *five* stayed true would mean the next person reading it finds one half. Expect a further one.
>
> **The section numbers are chronological, not ranked**, and the two newest sit at the end rather
> than at §6 — several accepted ADRs cite §7 as *the telemetry demands* and §6 as *the deleted
> penalty*, and a record already accepted should not have its pointers silently re-aimed.

## The test, so the eighth number does not need a debate

A number belongs in this file when **both** are true:

1. **Moving it changes what somebody is shown** — not how they are ranked, not what they may do:
   whether a person appears at all, or whether the answer is empty.
2. **Nothing on any screen would say so.**

Applied to the three constants [#194](https://github.com/Raketa02/Raketa/issues/194) settled,
they split on the *second* clause, which is the one that does the work. `INTEREST_TTL` moves
what is admitted below the quality floor, invisibly — in. `PASS_SUPPRESS` can empty a deck in a
thin pool, and no route returns a pass, so nobody can see it happen — in. The
`OUTSTANDING_INTEREST_CAP` decides whether a player may **act**, hides nobody, and
[ADR-0127](../../adr/0127-a-signal-expires-or-is-refused-never-quietly-decays.md) §4 made its
bite visible the instant it happens — out. It is an ordinary ruleset row with a falsifier, in
[`ranking-weights.md`](ranking-weights.md) §13.

**Owner of all seven: `RobertConstantin02`.** With one developer the name confers no authority;
that is not its job. It is so that the next person to hold one of these inherits a named
handover rather than a config file with no history. Any change to any of them **lands as
an ADR that names who moved it** ([ADR-0099](../../adr/0099-relaxation-offers-the-searchers-own-asks.md)),
and for the quality floor the ADR must additionally name **which of the six judged cases below
it now decides differently**.

**Almost none of these is measurable before the outcome half of the telemetry chain exists**,
which needs `matches`, which is out of scope. §8 and §9 are the exceptions and only partly:
each carries one falsifier that runs on day one, which is why §7's table grew. They are decided by argued judgement, shipped
with their falsifier attached, and revisited when the evidence exists. The falsifiers are
therefore also **demands on the search-side telemetry** (§6) — a search-time fact that is not
recorded from the first search cannot be reconstructed later, and a number whose falsifier can
never be run is a starting position that has quietly become permanent.

---

## 1. The quality floor — set by six judged cases, not by an integer

`QUALITY_FLOOR` is the Fit below which a candidate is not shown at all. It cannot be
calibrated against a distribution: there are no players, and the weights are not fixed. It is
therefore **defined by the cases it must satisfy**, and its integer is read off those cases
once the weights land.

Each case is *a searcher, and one candidate*. The verdict is whether that candidate appears.

| # | The candidate | Verdict | What it constrains |
|---:|---|---|---|
| 1 | Same level, free the same three evenings, five minutes away — nothing in common socially, no history either way | **Shown** | If this is not shown, nothing is |
| 2 | Ideal level, even forecast, lives close — but the two grids share **no** slot at all | **Shown** | Availability overlap is evidence a game can be *arranged*, not a proposed time; the times rung exists for exactly this |
| 3 | Two levels above, forecast lopsided, everything else fine | **Not shown** | The evening §9.7 exists to prevent |
| 4 | Everything exceptional, but the searcher is in competitive and the candidate has declared friendly-only | **Shown, low, reason printed** | Intent is a weight and not a gate ([ADR-0094](../../adr/0094-play-intent-declared-per-sport-in-its-own-aggregate.md)) |
| 5 | Average on everything. Nothing bad, nothing good — the median stranger | **Shown** | This is where the bar sits |
| 6 | A strong match well inside the searcher's radius — but the searcher is outside **theirs** | **Shown, docked, card says so** | A candidate's own radius is a Liveness dock and never a gate ([ADR-0099](../../adr/0099-relaxation-offers-the-searchers-own-asks.md)) |

As a constraint on any candidate weight vector:

```
Fit(case 3)  <  QUALITY_FLOOR  ≤  min( Fit(1), Fit(2), Fit(4), Fit(5), Fit(6) )
```

**If no weight vector satisfies it, that is the useful failure** — either the weights are wrong
or one of the six is misjudged, and the argument happens against a named case rather than
against an integer somebody dislikes. This is the constraint handed to
[The ranking weights](https://github.com/Raketa02/Raketa/issues/168), which fixes the integer.

The document's starting position of **52** is not adopted and not rejected here; it is simply
not yet an answer to anything. It survives only if it satisfies the six.

> **Resolved in [`ranking-weights.md`](ranking-weights.md) §10, and the failure this section
> anticipated is the one that happened.** No weight vector satisfies the six in for-fun, and the
> diagnosis was that neither instrument could do the job — the floor is now backed by a level
> gate ([ADR-0103](../../adr/0103-where-the-curve-saturates-the-gate-begins.md)). **Case 3 is
> excluded by that gate rather than by the floor**, so it no longer bounds the floor from below
> and is replaced by **case 3′**, the worst pairing still admitted to scoring. **52 is refuted by
> case 5** — the median stranger scores 46.0 in competitive, so 52 hides the case whose stated
> job is to sit at the bar. The floor is **44**.

> **And [#186](https://github.com/Raketa02/Raketa/issues/186) found that the term-value readings
> §10 claimed to carry did not exist.** They are reconstructed in
> [`the-judged-pairings.md`](the-judged-pairings.md) as a fixture of **inputs**
> ([ADR-0122](../../adr/0122-a-judged-pairing-is-two-people-never-a-profile-of-scores.md)); the
> recorded totals do not reproduce and are struck. **44 survives on `24.5 < FLOOR ≤ 44.5`** — half
> a point. Two of the six were not one pairing each: **case 3′ is two**, because `ADR-0103`'s gate
> is mode-relative, and **case 5 was re-judged**, because level fit and predicted balance read the
> same input and no pairing is average on both. **Case 4's verdict is narrowed**: *"shown,
> **low**"* is unachievable at 80.3 — it read low only while §6's deleted `intent_opposed`
> existed — so the fixture asserts shown, above the floor, intent exactly `0.00`, reason printed.

- **Falsified by:** return rate of games arising from candidates just above the floor versus
  just below it. Requires the outcome half.
- **Never relaxed, and the empty-result rate is never on its own sufficient grounds to move
  it** ([ADR-0099](../../adr/0099-relaxation-offers-the-searchers-own-asks.md)).
- **One floor, both modes, every sport.** Each extra dimension is another place the bar can be
  lowered quietly for whichever pool is thin — *"tennis is sparse, so tennis's bar is lower"*
  is the Wikimedia move with a per-sport label on it. A mode that genuinely needs its own bar
  earns one later, with evidence, as an ADR.

### The evidence rule that sits beside it

The floor is a fixed bar over a score whose ingredients vary **per comparison**: §10
renormalises for that candidate, so a candidate missing a term they would have scored badly on
is *lifted* by its absence. Ranking survives this — absence is not evidence of badness. A
**cut** does not: at the bar, giving nothing becomes a small advantage over giving something
mediocre.

**The bar stays absolute, and a separate rule carries the honesty:** below a minimum of
evidence *about that specific person*, they are not shown — **a gate, not a score adjustment**,
in keeping with [ADR-0098](../../adr/0098-matcher-demands-as-executable-contracts.md)'s *a gate
may be honestly empty; a term may never be honestly neutral*.

- Expressed as a **fraction of the terms live for the platform**, never a count, so it keeps
  meaning the same thing when a term turns on and the denominator changes. **At least half.**
- It counts **gaps specific to that person**, never platform-wide absence. On day one nobody
  has a reliability record; that must not gate the market.
- **Today it excludes nobody**, and that is the point. With the availability grid required
  ([ADR-0102](../../adr/0102-silence-is-never-scored.md)) every new profile produces evidence on
  every day-one term. It is standing insurance, in place before it is needed, so that the day a
  new term arrives *we know nothing about this person* cannot quietly become a passing score.

---

## 2. `MIN_SHORTLIST` — 5

**What it now does.** It no longer triggers anything. [ADR-0099](../../adr/0099-relaxation-offers-the-searchers-own-asks.md)
removed automatic widening: the engine never widens on its own, it carries the offers with
their real counts and the player takes one. `MIN_SHORTLIST` is what decides **whether the
offers are computed at all**.

Computing them means genuinely re-running generation and scoring per rung — the counts must be
real, because a count on a screen that was estimated breaks the third refusal. That is roughly
3 ms per rung ([#161](https://github.com/Raketa02/Raketa/issues/161)), cheap but not free, and
on most searches it is a lever nobody needs.

**The value: 5, not the document's 3.** Three results is already a thin screen; the offers cost
about 6 ms; and the number's real question is *how short is short enough that the player would
want another option*. At launch density this means offers are computed on roughly two thirds of
searches rather than one half ([#161](https://github.com/Raketa02/Raketa/issues/161): with 20
players scattered over a metro, 49% of searches return fewer than three candidates and 63%
fewer than five).

- **Falsified by:** rung take-up rate by shortlist length. If nobody holding four or five
  results ever takes an offer, 5 is too high.
- **The density hypothesis it now owes** rises with it: players per sport per district needed
  to clear **five** with no rung taken. It cannot be borrowed — nobody publishes a measured
  density threshold for a local matching product.

---

## 3. The widening ceiling — twice, clamped to the profile's own maximum

The ladder is **times → radius ×1.5 → radius ×2.0**
([ADR-0099](../../adr/0099-relaxation-offers-the-searchers-own-asks.md)). There is no third
radius rung.

- **Why it stops at double.** [#161](https://github.com/Raketa02/Raketa/issues/161) measured
  that at launch density, tripling the radius still leaves 15% of searches under five
  candidates. Widening does not rescue a thin market; past double it mostly spends the player's
  travel budget on failing. Recruiting a city club by club is worth more at that size than
  every term in §9.3 combined.

- **The cap already exists and is not this ticket's to invent.** The search radius is a Player
  profile field — `backend/app/modules/player_profile/domain/search_radius.py`, **1–50 km,
  whole kilometres, default 10**, set at profile commit and edited afterwards through
  `SearchRadiusChanged`. The glossary already gives it both halves of its job: *a filter when
  the player searches, and a weight when the engine proposes*.

  **Every rung clamps to `SEARCH_RADIUS_BOUNDS.maximum_km`.** A relaxation may never offer a
  radius the player could not have set for themselves — that is the same principle as *a rung
  may only relax what the searcher themselves asked for*, applied to the range the product
  allows them to ask within.

  Two consequences, both intended:
  - A searcher already at 50 km gets **no radius rung at all** — only the times rung. The
    honest empty state arrives sooner for them, correctly: there is nothing left to offer.
  - A searcher at 40 km has both multipliers clamp to 50, so **one radius rung is offered, not
    two**. A rung that would duplicate another rung's radius is not offered twice.

- **There is no per-search radius input.** The searcher's ask *is* their profile radius. A
  player who wants 40 km sets 40 km — that is their ask, not a relaxation.

- **Taking a wider search repeatedly offers to become the default.** *"Keep 15 km?"*, inline,
  bounded by the profile's own slider, and **never a silent write**. This is the third instance
  of one pattern — the intent drift prompt ([ADR-0094](../../adr/0094-play-intent-declared-per-sport-in-its-own-aggregate.md))
  and *"Keep these times?"* are the other two — and consistency is the argument. The engine
  notices drift and asks; it never acts on it.

- **Falsified by:** acceptance rate per rung. A rung whose matches never convert should be
  removed, not tuned.

---

## 4. The reliability bar — 70, on the number the player can see

**Which number.** The **published Player Score** — the one on the player's own profile — and
not the matcher's private per-mode blend of the five strands. The two are different numbers: the
screen blends at 35/20/12/10/8, and the ruleset weighs per mode at 33/33, 29/23 and so on
([`ranking-weights.md`](ranking-weights.md) §6).

> **Amended by [ADR-0140](../../adr/0140-a-player-score-is-what-the-platform-watched-and-two-strands-is-what-it-can-see.md).**
> There were six strands and *confirms results* was struck
> ([ADR-0137](../../adr/0137-a-result-is-the-record-that-a-game-happened.md)), taking its `15`
> out of the published blend and its two ruleset weights with it. The published vector **sums to
> 85 and is not renormalised to a hundred**, because its basis is the strands a player actually
> has rather than a budget — the blend renormalises over what is present, which is what lets a
> player the platform can see two things about be compared with one it can see five about. The
> per-mode vectors *were* rescaled, because a ruleset weight map is validated as totalling a
> hundred. **The bar itself did not move.**

[ADR-0098](../../adr/0098-matcher-demands-as-executable-contracts.md) already rules that the
matcher reads what the player is shown and never re-derives it. A penalty justified by a figure
that exists nowhere a human can look is unexplainable, and a player who works their visible
score back up must be able to see the penalty lift.

**This is the one deliberate place the matcher reads the blend instead of the strands**,
recorded as an exception so it does not later read as an oversight.

**The value: 70.** Roughly *you have missed something like a fifth of what you committed to*.

**The demand this raises on `player_score`.** Does a published score exist after one game, and
does it mean anything that early? The contract, in the shape the other demands take
([ADR-0098](../../adr/0098-matcher-demands-as-executable-contracts.md)): **the score is not
published until there is enough behind it to be fair, and until it is published the bar does
not fire.** A bar that can brand somebody on one observation is worse than no bar.

- **Falsified by:** ghost and no-show rate of games arising from candidates just above the bar
  versus just below it.
- **Never relaxed, at any rung.**

## 5. The reliability penalty — `MODIFIER_BUDGET + 1`, which is 11 today

Derived, not picked. The property that has to hold is the document's own sentence: **a stack of
small positives must never lift somebody over a recent no-show.** The modifier stack is clamped
to ±10, so the smallest penalty that keeps the promise is **11** — and defining it as
`MODIFIER_BUDGET + 1` means it moves by itself if the budget ever does. The document's 12 has
no separate argument behind it.

**And the promise is smaller than the sentence sounds, which is stated rather than fixed.** The
penalty guarantees the *modifier stack* cannot erase a no-show. It does nothing against the
main score: a candidate who is otherwise a superb match still lands well clear of the floor
after taking it, and appears — low, with the reason printed.

That is the right outcome, and it is why the bar is a dock rather than an exclusion:

- Excluding outright would be the platform refusing to show a genuinely good match over one
  missed game. *The weights persuade, the player decides* — and where a player wants somebody
  gone entirely, the block exists ([ADR-0095](../../adr/0095-block-directed-record-symmetric-effect-gates-fail-closed.md)).
- The sentence in §9.3.4 overstates what the number delivers. **The number is not changed to
  match the sentence; the sentence is corrected.**

---

## 6. What was deleted: the opposite-intent penalty

`intent_opposed` (−6) is **removed**. §6.4 scores a directly opposite declaration **0.00**
*and* levies a further flat modifier — the same single fact moving the score in two places,
which §6.5 and §9.3.6 forbid everywhere else in the same document.

The zero is the whole answer, and the gap that matters is already the right shape:

- A candidate who has **not declared** has the term dropped and renormalised away — they are
  scored as though intent did not exist.
- A candidate who has declared **the opposite** loses the term's entire weight.

So declaring against the searcher already costs strictly more than saying nothing, without a
second charge. The extra modifier existed to *bury* the candidate, which is a gate wearing a
modifier's clothes, and [ADR-0094](../../adr/0094-play-intent-declared-per-sport-in-its-own-aggregate.md)
settled that intent is a weight and not a gate.

The six cells of the alignment table are unchanged and were settled in
[ADR-0094](../../adr/0094-play-intent-declared-per-sport-in-its-own-aggregate.md).

---

## 7. What the search-side telemetry must record, from the first search

Handed to [The search-side telemetry](https://github.com/Raketa02/Raketa/issues/169) as a
demand, in the shape [ADR-0098](../../adr/0098-matcher-demands-as-executable-contracts.md) used
for the contexts that do not exist. **Every fact here is search-time and cannot be
reconstructed afterwards** — and [ADR-0118](../../adr/0118-a-past-search-is-not-reproducible.md)
makes that final: a past search is explainable forever and is not reproducible, so a fact not
written down at scoring time is gone. Without them, the falsifiers above are unrunnable even on
the day outcomes arrive.

| For | Record, per search | Why it cannot wait |
|---|---|---|
| **Quality floor** | How many candidates were scored, how many cleared the floor, and **the Fit of the best candidate that did not** | *The best match you refused to show* is the entire falsifier, and it exists only at scoring time |
| **Quality floor** | Which terms produced evidence per scored candidate | The renormalisation basis. Without it a Fit is uninterpretable a year later |
| **Evidence rule** | Whether a candidate was withheld for insufficient evidence, and which terms were missing | Distinguishes *nobody was good enough* from *nobody was known enough* |
| **`MIN_SHORTLIST`** | Shortlist length, and whether the rung offers were computed | Take-up by length is the falsifier |
| **Widening ceiling** | Which rungs were offered, each one's real count, which was taken, and the radius clamp if it bit | Acceptance rate per rung; and the clamp tells you how many searchers are already at the ceiling |
| **Reliability bar** | Whether the penalty fired for each scored candidate, and whether it was what put them below the floor | Separates *docked* from *docked out* |
| **`INTEREST_TTL`** | Per lifted candidate, the **age in days** of the yes that lifted them, and **whether the lift admitted them below the floor** | The age lives in Redis behind a TTL, so a year later it is unrecoverable — and it is the entire x-axis of *acceptance by age of yes*. The admission flag is what the TTL actually costs: how many below-floor rows it bought |
| **`INTEREST_TTL`** | **Yeses that expired having never lifted anybody** — the other person never ran a search | The one falsifier here that runs on **day one**, without `matches`. If most yeses expire unfired, 21 days is answering the wrong question and the pool is too quiet |
| **`PASS_SUPPRESS`** | Per deal, **how many cards a live suppression excluded**; and per card, whether that pairing had a **lapsed** suppression | The first distinguishes *your own passes emptied your deck* from *the pool is empty* — the failure mode that puts this constant in this file. Without the second, only plain pass rate is computable, never *re-shown* pass rate, which is the falsifier §24 names |
| **`OUTSTANDING_INTEREST_CAP`** | On the interest **write**, not on a search: refusals at the cap, and the **distribution** of outstanding counts per player | A raw refusal count cannot tell *20 is too low* from *somebody is saying yes to everybody* — only the shape of the distribution can, and the second is the behaviour the cap exists to catch. The cap is not five-numbers-shaped; its falsifier is recorded here because it is the same store |

Nothing here is a display string, and nothing here crosses the wire outward — this is the
engine's own record ([ADR-0022](../../adr/0022-kernel-negative-space-and-constant-homes.md)).

---

## 8. `INTEREST_TTL` — 21 days, flat, then absent

Settled by [ADR-0127](../../adr/0127-a-signal-expires-or-is-refused-never-quietly-decays.md),
which also refuses §9.5.1's linear decay over the final 7 days.

**It is here because an interest lift is the only guaranteed inclusion left.** ADR-0099 as
amended lets a human's own *Let's play* **admit** a candidate below `QUALITY_FLOOR`, where
nothing the engine computes may. So the TTL is the second number in this file that decides
whether somebody is shown at all — and unlike the floor, its expiry arrives on an ordinary
morning with no event attached.

**Why 21 and not 7.** The TTL looks like a claim about people — *do you still mean it* — and at
this pool size that is the wrong axis. A yes is **silent**: nobody is told, and it fires only
when the other person happens to run a search. A player who searches once a fortnight will never
see most of a 7-day yes. The failure that costs the product is *the yes never fired*, not *the
yes was stale*, and 21 days is chosen against that one.

**Why flat.** `days_ago` already crosses as evidence, so the card can say *"said yes 18 days
ago"*. A decay would charge for the same fact a second time, invisibly, and print the same
sentence at day 2 and day 20 while the row sat somewhere else — *Why 78?* failing on the screen
whose whole promise is showing its working.

**What expiry does, exactly.** The lift stops. *Already asked* is a deck exclusion, so the person
**re-enters the deck** and may be dealt again — read as a fresh chance rather than a loop, which
is part of why 21 rather than 30. Every outgoing row carried `expires_at` from the day it was
created, so nothing about this arrives as a surprise (ADR-0127 §5).

**Falsified by:** acceptance rate of interest-lifted candidates **by age of the yes** — needs
`matches`. And, on day one, by **yeses that expired having never lifted anybody**: if most yeses
expire unfired, 21 days is answering the wrong question and the real problem is that nobody is
searching. Owner `RobertConstantin02`.

**The cost, named.** A candidate admitted below the floor on a 20-day-old yes, with the reason
printed, is not there the next morning. In a thin pool that is a visibly shorter list, and the
decay §9.5.1 asked for would have faded them instead. The cliff is taken because a fade is
unexplainable and a cliff is at least dated.

---

## 9. `PASS_SUPPRESS` — 30 days, deck only, never escalating

Settled by [ADR-0128](../../adr/0128-a-pass-is-about-my-deck-a-block-is-about-a-person.md).

**It is here for the second clause, not the first.** Plenty of constants hide somebody. This one
hides them **and nobody can see it happening** — a pass is write-only, no route returns one in
any shape, and *Show them again* was struck for making the suppression a suggestion. In a thin
pool it is one of the few things that turns a non-empty pool into an **empty deck**, and the
player whose taps caused it has no surface that would say so.

**30 days, and a second pass means nothing more.** §9.5.1's *"repeated passes on the same person
are a soft signal respected quietly"* is struck: it cannot print, it cannot enter ADR-0123's
closed silent roster, and where it leads is a **Block** — which exists, is symmetric, is
reversible, and requires somebody to mean it.

**Deck only, and one-directional.** It never reaches the shortlist, the line-up or a forecast,
and it never touches the other person's deck. Both boundaries are argued in ADR-0128; the short
form is that a search is a question about the city and a swipe may not edit the answer.

**Falsified by:** pass rate on **re-shown** profiles — already paid for by the **Origin key** on
`POST /passes`, which makes this the one number in this file whose falsifier runs without
`matches`. Owner `RobertConstantin02`.

**The cost, named.** You can pass on somebody tonight and find them third in your shortlist
tomorrow. If that reads as the product ignoring you, the fix is a sentence on the deck about what
a pass does — never a wider suppression.
