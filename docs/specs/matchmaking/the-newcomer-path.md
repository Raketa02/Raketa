# The newcomer path, and the welcoming record

Resolves [#175](https://github.com/Raketa02/Raketa/issues/175) on the map
[The matchmaking engine: who sits down, and why](https://github.com/Raketa02/Raketa/issues/155).
Decisions here are carried by
[ADR-0113](../../adr/0113-newness-changes-the-gate-never-the-weights.md) and
[ADR-0114](../../adr/0114-a-newcomer-may-not-be-declined.md); this file holds the shape, the
day-one behaviour and the measurements.

---

## 0. Four facts that decide most of it

Checked against the code before anything was designed. Three of them change what the ticket
could ask.

1. **Nothing in this platform records that a game happened.** No `matches` context, no
   games-played counter. `counted_games` — read by §9.10's newcomer predicate *and* by its
   *"never the most competitive player"* cap — exists nowhere.
2. **The rating's status has exactly one value.** Every rating the questionnaire produces is
   stamped `"Initial Estimate"` (`backend/app/engines/racketskill/v3/engine.py:309`), and no
   transition can change it. So §9.10's predicate `counted_games == 0 ∧ rating_status ==
   INITIAL_ESTIMATE` is **true for every player who will ever exist**. As written, everybody is
   a newcomer, permanently.
3. **All three of the welcoming record's named tag inputs already ship, and are already
   scored.** `GENEROUS_ON_LINE_CALLS` and `ENCOURAGES_A_PARTNER` are `ON_THE_COURT` — the style
   term. `HERE_TO_IMPROVE` is `WHY_YOU_ARE_HERE` — the vibe term
   (`backend/app/modules/player_profile/domain/social_tags.py`). Sportsmanship is a reliability
   strand. Its inputs are not new evidence; they are evidence the engine has already paid for.
4. **Nothing about a newcomer's own newness stands a single Fit term down.** All eight terms are
   pairwise, and the ones that go quiet are about the *candidate*. So §9.10's re-weighting is a
   real product choice and not something graceful degradation supplies for free — checked
   expecting the opposite.

---

## 1. Who is new, and for how long

> **New until their first game, and never longer than 14 days.**

Two halves, one measurable today.

| Half | Reads | Status |
| --- | --- | --- |
| Until their first game | `matches` | **Inert.** Nothing to count until `matches` ships |
| Never longer than 14 days | `profile_created_at` | **Live from build one** |

**The clock starts at the profile commit** — the last step of onboarding and the moment a
player becomes searchable. Not registration and not the rating: a window that opens before a
player has an index row spends days they could not have used, which is the one failure a
bounded subsidy never recovers from. It is also the event the index row is already born from,
so it costs nothing new.

**Calendar days, not searches.** A player who signs up and searches nothing for three weeks
spends the window without using it — and that case already belongs to somebody else: §14.2's
exposure floor lifts anybody shown zero times this week, newcomer or not.

**The 14 days is a ceiling, not the definition.** The definition is *before your first game*;
the ceiling is what makes it terminate when the definition cannot be read.

### The index stores a date, never a flag

A stored `is_newcomer` boolean goes stale hourly — which is precisely why §14.5 grew an hourly
sweeper loop to *"open and close 14-day windows"*. A date never goes stale.

> **§14.5's newcomer-window loop is struck.** The window is `now − profile_created_at < 14 d`,
> computed where it is read. There is no newcomer ledger, and there is no loop.

The column passes [ADR-0111](../../adr/0111-the-index-holds-only-what-a-player-changes-about-themselves.md)'s
test in its most literal form: completing your own profile is *a fact a player changes about
themselves*, and it arrives as an event ([ADR-0110](../../adr/0110-the-index-tails-the-log-the-outbox-delivers-side-effects.md)),
namely `PlayerProfileCreated`.

---

## 2. Newness changes the gate, never the weights

§9.10 proposes a third weight vector — level 30 · balance 22 · reliability 20 · intent 14 ·
availability 8 · style 4 · vibe 2 · distance 0. **It is struck**
([ADR-0113](../../adr/0113-newness-changes-the-gate-never-the-weights.md)).

The cost is concrete. [`the-five-numbers.md`](the-five-numbers.md) set **one** `QUALITY_FLOOR`
for both modes and every sport precisely because *"each extra dimension is a place to lower it
quietly for whichever pool is thin"*, and [`ranking-weights.md`](ranking-weights.md) read the
integer **44** off six judged pairings scored on the two existing vectors. A third vector
re-derives every Fit value in that table, so it either moves the floor for newcomers — the
thing the map refused — or owes the six pairings before it can ship.

What replaces it:

> **While either side of a pairing is inside their window, the level gate is evaluated at
> `LEVEL_TOL_COMP`, in both modes.**

- **No new constant.** `LEVEL_TOL_COMP = 0.55` and `LEVEL_TOL_FUN = 0.90` both already exist and
  both already carry falsifiers. Nothing is introduced, so nothing is owed.
- **It binds the pairing, not the search.** Gating only the newcomer's *own* search would let
  the bad first game arrive through the veteran's list instead — a game the newcomer never
  searched for and cannot decline. This is the third instance of a shape this map keeps
  reaching: [ADR-0095](../../adr/0095-block-directed-record-symmetric-effect-gates-fail-closed.md)'s
  block and [ADR-0096](../../adr/0096-gender-preference-mutual-gate-invisible-to-the-scorer.md)'s
  preference are both about a pair, and both bind whoever is in it.
- **Distance needs no rule.** §9.10 sets its weight to 0 on the argument that *a first game is
  worth a longer journey*. It already is: [ADR-0099](../../adr/0099-relaxation-offers-the-searchers-own-asks.md)'s
  radius rungs let a newcomer travel further **if they ask**, which is the map's standing answer
  to every widening the engine would otherwise perform on somebody's behalf.

### *Never the most competitive player in the pool* is refused, not deferred

§9.10 caps the candidate's `counted_games` percentile. Four problems, and the fourth is the one
that settles it.

1. **It is a percentile over the pool.** The identical pairing is admissible in a large city and
   refused in a small one — the shape
   [ADR-0101](../../adr/0101-partition-derived-never-a-matching-criterion.md) struck for the
   partition, and unexplainable in one sentence naming evidence, which is the third refusal.
2. **Its input does not exist** (§0 fact 1).
3. **ADR-0103's level gate does not catch the case §9.10 gives.** A 3.40 against a 3.35 is
   Δμ = 0.05, nowhere near either tolerance. The worry is about **experience, not level**, and
   the engine holds no unit for experience.
4. **It refuses the pairing the calibration modifier pays +4 for.** §9.4 rewards *their band is
   wide and yours is narrow*; §9.10 forbids it. Same document, two sections apart.

If the concern survives, it returns in the units the engine has — Δμ and σ — and lands as a gate
under ADR-0103, where it will have to reconcile with calibration value rather than sit two
sections away from it.

---

## 3. The welcoming record, reduced to its one unpaid input

§9.4's modifier names four inputs. Audited against what already scores them:

| Input | Already scored by | Verdict |
| --- | --- | --- |
| Sportsmanship | The reliability term — it is a strand | **Struck** |
| `GENEROUS_ON_LINE_CALLS`, `ENCOURAGES_A_PARTNER` | The style term | **Struck** |
| `HERE_TO_IMPROVE` | The vibe term | **Struck** |
| Opponent variety | Its only other consumer — familiarity's sign — was struck by [#164](https://github.com/Raketa02/Raketa/issues/164) | **Struck; and see below** |
| A history of wide-band opponents | Nothing | **Kept** |

Paying the tags again inside a ±10 modifier budget is the same double-charge that struck the σ
clause from familiarity, and it would pre-empt
[The tag relationship matrix](https://github.com/Raketa02/Raketa/issues/179), which owns what
those tags mean.

> **Welcoming record** = *this candidate has played opponents whose rating was still settling*.
> One input, from the `rating` port. **Printed.** Range `0 … +4`, unchanged.

It is also the only one of the four that means what the modifier claims. Sportsmanship says you
are pleasant; variety says you get around; neither says you are **willing to play somebody who
might be bad**.

### Opponent variety is withdrawn from the contract

[ADR-0098](../../adr/0098-matcher-demands-as-executable-contracts.md) demanded opponent variety
as a **seventh published statistic that is explicitly not a strand**, on behalf of two consumers.
[#164](https://github.com/Raketa02/Raketa/issues/164) struck one; this ticket strikes the other.

**A consumer-driven contract with no consumer is withdrawn, not carried.** Its whole discipline
is that a demand is executable against a provider — a demand nobody reads is a demand nobody will
notice going wrong. ADR-0098 is amended to say so. If a later term wants it, it returns as that
term's demand.

---

## 4. The asymmetry: printed, never declinable, capped

Being matched to a newcomer is a cost somebody bears.
[ADR-0114](../../adr/0114-a-newcomer-may-not-be-declined.md) settles all three parts.

### Printed, always

§9.10 already commits to it — *"They're new — this game does most of its work for them"* — and
the third refusal demands it: the engine never produces a number it cannot explain in one
sentence with the evidence named. Two codes, two directions, both rendered by the client
([ADR-0022](../../adr/0022-kernel-negative-space-and-constant-homes.md),
[ADR-0106](../../adr/0106-evidence-vocabulary-is-contract-weights-are-configuration.md)):

| Direction | Code | Field |
| --- | --- | --- |
| The veteran is told the candidate is new | `newcomer_window` | `liveness_reasons[]` |
| The newcomer is told the candidate plays unsettled ratings | `welcoming_record` | `modifiers[]` |

**One collision, real but not yet live.**
[#171](https://github.com/Raketa02/Raketa/issues/171) settled that *a reason line never restates
a value the card already renders*, and the player card carries `counted_games`. Newness here is
a **date**, not a game count — a player twenty days in with no games is not in the window — so
they are different claims. Today it is moot in the simplest way: `counted_games` reads `matches`
and renders absent, so there is nothing to restate. **The constraint for the day it lands is
that the two stay distinct facts**, not that either one goes.

### Never declinable

A *no beginners* switch is a preference over people, and unlike
[ADR-0096](../../adr/0096-gender-preference-mutual-gate-invisible-to-the-scorer.md)'s gender
preference it protects nobody. ADR-0096's mutuality argument was about a person's safety in
their own inbox; this is not that. It would let the strongest half of a thin pool opt out of the
single mechanism that gets a newcomer a first game — the cold-start trap, entered through the
door built to escape it. It also cannot be mutual, and a one-directional preference over people
is the exact thing ADR-0096 refused.

### Capped

The pressure is real, and §14.4 already names where it ends: a player given nothing but
newcomers stops answering, their answer rate falls, and **the matcher punishes them for having
helped**. So the valve is a bound on the ask, not a switch.

| | |
| --- | --- |
| **Counts** | Appearances in a **newcomer's** shortlist, per week, per sport |
| **Where** | The exposure ledger — same shape, same cadence, no second ledger |
| **When it binds** | The welcoming modifier and the newcomer-driven reorder are **dropped**; the player still ranks on their merits |
| **Never** | Withheld from generation |
| **Who is told** | **Nobody** |

**Never withheld**, because withholding makes a thin pool thinner for the one person who can
least afford it. This section once let §14.4's withholding stand as the *measured* exception —
a remedy for a full inbox somebody had counted, where this cap has only a suspicion of load.
**[#189](https://github.com/Raketa02/Raketa/issues/189) found the distinction is about the wrong
party and removed the exception**: the measurement is of the *candidate's* inbox while the cost
is paid by everyone searching, and no relaxation rung reaches a gate. §14.4's withholding is
**deleted**, its third rung becoming the bottom step of the sink at `−12`
([ADR-0125](../../adr/0125-a-full-inbox-sinks-a-player-never-withholds-them.md)). So this
section's rule is now the *only* rule and not the strict half of two: **the engine bounds how
hard it pushes somebody, and never removes them from the pool.**

**Nobody is told, because nothing has happened to them.** Their list is unchanged and their inbox
is unchanged; the only thing that moved is how often the engine volunteers them. §14.4's rule —
*the person whose inbox is full is told, the searcher is not* — survives the deletion above and is
about a fact the player can already see: it is `count(open challenges)`, owed by the app when they
next open it, and the engine emits nothing for it. This one has no symptom at all.

The magnitude belongs with the weights. That the cap exists, and what it counts, is settled here.

---

## 5. The window's one power, and the signal it splits

### It exempts from minimum evidence, and from nothing else

[`the-five-numbers.md`](the-five-numbers.md) added a gate beside the floor: **a fraction of live
terms must have fired for that person**, reading person-specific gaps only, *"excluding nobody
today on purpose"* — true, because on day one the same terms are down for everybody.

**The moment `player_score` and `matches` land, the person with a person-specific gap is exactly
the newcomer.** The minimum-evidence gate becomes a newcomer exclusion on the day it starts
working, and §14.3's window exists to prevent that precise outcome.

> **While the window is open, minimum evidence does not apply.** Nothing else bends: not the
> quality floor, not any of the ten gates, not a block.

The alternative — count the fraction only over terms that *could* have fired for that pairing —
was rejected. It silently deletes the gate for everybody, because a term that did not fire can
almost always be argued not to have applied.

### `NEWCOMER_WINDOW` and `ZERO_EXPOSURE` are one signal with two printabilities

[`ranking-weights.md`](ranking-weights.md) parked this here by name: *"#175 may argue exposure
into printability and take its +8 back; until it does, the invariant binds it."* The invariant is
**`|silent movement| < MOVE_NOTICE`**, and it cut §14.2's `+8` to `+6` because the signal could
not be shown.

They are one row in the weights table and two codes on the wire, and their printability
arguments point in opposite directions:

- ***They're new — this game does most of its work for them*** is a sentence the product wants
  said out loud.
- ***You are seeing this person because nobody has been shown them all week*** is a fact about a
  third party's unpopularity that damages them to reveal, and the searcher is owed no version
  of it.

> **Split the signal.**
>
> | Signal | Bound | Printable |
> | --- | --: | --- |
> | **Newcomer lift** | **+8** | **✓** |
> | **Exposure adjustment** | **−6 … +6** | ✗ |

The newcomer lift may exceed `MOVE_NOTICE` **honestly**, because the invariant binds *silent*
movement and this one speaks. The exposure adjustment stays where the invariant holds it. Two
signals, two bounds, two printabilities — and the invariant is satisfied by construction rather
than by a cap that flattened both.

### `inclusion_reason` narrows to the one code that includes

Since [ADR-0099](../../adr/0099-relaxation-offers-the-searchers-own-asks.md), only
`INTEREST_LIFT` admits anybody; the other two reorder. The field's name describes one of its
three values.

| Code | Was | Now |
| --- | --- | --- |
| `INTEREST_LIFT` | `inclusion_reason` | `inclusion_reason` — unchanged |
| `NEWCOMER_WINDOW` | `inclusion_reason` | **`liveness_reasons[]`** — a printable reorder |
| `ZERO_EXPOSURE` | `inclusion_reason` | **Telemetry only. Never crosses the wire** |

`inclusion_reason` stays a union of one, so the next reason that genuinely admits somebody has
somewhere to go. `search_candidate.inclusion_reason` keeps all three values — the store is open
where the wire is closed
([ADR-0106](../../adr/0106-evidence-vocabulary-is-contract-weights-are-configuration.md)) — and
`ZERO_EXPOSURE` is the first code that lives only there.

---

## 6. Which surfaces it reaches

| Surface | Gate | Lift | Welcoming modifier |
| --- | --- | --- | --- |
| The ranked list | ✓ | ✓ | ✓ |
| The deck | ✓ | ✓ | ✓ |
| Doubles seats | ✓ | ✓ | ✓ |
| The doubles **group objective** | — | — | — |

Gates bind every seat, and §2's tightened tolerance inherits that. **The reading of *every
seat* has since been corrected** — ADR-0096's ninth gate was applied before §9.9 enumerates and
bound every seat *against the searcher*, leaving the three pairs a searcher is not in gated
against nobody. [ADR-0116](../../adr/0116-in-a-four-every-gate-binds-all-six-pairs.md) makes all
six bind, and carries §2's tolerance with it: **every pair containing a newcomer takes
`LEVEL_TOL_COMP`, whoever ran the search** — because gating only the newcomer's own pairs with
the searcher recreates exactly the hole §2 was written to close. The price is named there: in a
for-fun four, three of six pairs narrow from 0.90 to 0.55, and at launch density a newcomer's
first doubles game may frequently be a partial line-up. The welcoming record is a Fit modifier,
so it rides wherever Fit is computed.

**What a newcomer does to a four-player objective is settled by**
[The doubles group objective](https://github.com/Raketa02/Raketa/issues/180), which took this
constraint unchanged rather than re-deriving it:

> **A newcomer is never seated below the quality floor to complete a four.**

That is [ADR-0099](../../adr/0099-relaxation-offers-the-searchers-own-asks.md)'s partial-line-up
rule — *doubles returns a partial line-up rather than filling a seat below the floor* — applied
to the person it protects most.

---

## 7. Day one: everything wired, nothing waiting, nothing standing in

| Piece | Reads | Day one |
| --- | --- | --- |
| Tightened level gate | μ, `profile_created_at` | **Live** |
| Newcomer window and its `+8` lift | `profile_created_at` | **Live** |
| Minimum-evidence exemption | The gate | **Live but inert** — the gate excludes nobody yet |
| Welcoming record | `matches` + a result-update rule | **`NoEvidence`** |
| The cap | The welcoming modifier | **Wired, never binds** |

**Everything ships wired.** The map has settled this shape three times —
[ADR-0095](../../adr/0095-block-directed-record-symmetric-effect-gates-fail-closed.md)'s hold
gate ships *wired and true-over-empty*, and ADR-0098's ports ship as `NoPlayerScoresExist` and
`NoMatchHistoryExists`. Welcoming ships as a null-object read returning `NoEvidence`; the cap
ships as code that never binds.

**Nothing stands in for the welcoming record**, and the reason is already written: *a gate may be
honestly empty; a term may never be honestly neutral*. Every proxy available is one of the inputs
§3 struck for being paid already — so standing one in would not merely invent a number, it would
invent one the engine has **already counted**.

---

## 8. When the window closes on somebody who never played

Nothing happens. The lift stops.

This is §14.3's own stated fear arriving anyway — *"never accumulate the evidence that would lift
them"* — and the answer is that a bounded subsidy is bounded.

**What catches them is not newcomer-specific and never expires:** §14.2's exposure floor lifts
anybody shown zero times this week. They do not fall off a cliff; they fall back onto the general
fairness mechanism, which is correct, because after 14 days they are not new — they are a player
nobody has played, and that is a different problem with an existing remedy.

**A window that extends while unused was rejected.** It is not a window; it is a permanent
subsidy for the players the engine knows least about, and it would become the largest standing
distortion in the market.

---

## 9. The measurements

| What | Falsifies | Owner |
| --- | --- | --- |
| **Fraction of newcomers who play a game before the window closes** | The window itself. If it is low, the window is not working — and its **duration is the wrong lever**, because the honest response is recruiting, not a longer subsidy | This spec |
| **Return rate of first games, split by whether the tightened gate bound** | §2's gate. If games at Δμ between `LEVEL_TOL_COMP` and `LEVEL_TOL_FUN` return as well for newcomers as for anybody, the tightening is unearned | ADR-0113 |
| **Answer rate of players who absorb the most newcomer appearances** | §4's cap. If it does not fall as absorption rises, the cap is guarding nothing | ADR-0114 |
| **Fraction of shortlists where the newcomer lift moved somebody more than `MOVE_NOTICE`** | The `+8`. If it never does, the reclaim bought nothing and `+6` was right | `ranking-weights.md` |

Search-side, the telemetry must record **whether each side of a pairing was inside their window**
— reconstructible from `profile_created_at` and the search timestamp, so no new column, but the
join must be possible. The first three need the outcome half of the chain, which needs `matches`,
which is out of scope. They ship as argued judgements with their falsifiers attached, like the
other five numbers.

---

## 10. What this strikes

| Struck | Where | Why |
| --- | --- | --- |
| The newcomer weight vector | §9.10 row 1 | Re-derives a floor defined by six judged pairings ([ADR-0113](../../adr/0113-newness-changes-the-gate-never-the-weights.md)) |
| *A first game is worth a longer journey* | §9.10 row 2 | The radius rungs already do it, on the searcher's own ask |
| *Never the most competitive player in the pool* | §9.10 row 4 | A percentile over the pool; and it refuses what calibration pays for |
| Sportsmanship, the three tags, opponent variety | §9.4 welcoming row | All already scored elsewhere |
| Opponent variety as a contracted statistic | ADR-0098 | No consumer left |
| The newcomer-window sweeper loop | §14.5 row 3 | A date needs no loop |
| `NEWCOMER_WINDOW` / `ZERO_EXPOSURE` as inclusion reasons | ADR-0099, the two contracts | Neither admits anybody |

§9.10's two surviving rows — *be honest about the band* and *do not zero their Player Score* —
were already settled elsewhere and are kept: `provisional` travels inside the forecast
([#170](https://github.com/Raketa02/Raketa/issues/170)), and *no record is not a bad record* is
`NoEvidence` (ADR-0098), which is **not** a neutral prior. The document's phrase *"neutral prior"*
is loose for renormalisation and must not be read literally — a neutral prior is exactly the
invented zero the invariant forbids.
