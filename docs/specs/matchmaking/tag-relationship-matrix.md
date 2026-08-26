# The tag relationship matrix

**Thirty-seven rows over the nineteen ids that shipped.** Product-owned ruleset data (§23 Q18),
feeding the two tag terms — playing style and social vibe. The rules that govern the rows are
[ADR-0115](../../adr/0115-a-tag-about-the-person-may-be-shown-never-scored.md); the rows
themselves are ruleset data and revisable without one. The scoring formula, the constants and
their falsifiers are [`ranking-weights.md`](ranking-weights.md) §5.

Settled by [The tag relationship matrix, over the nineteen ids that actually shipped](https://github.com/Raketa02/Raketa/issues/179).

## 1. The entry

```
{ a, b,
  kind:     MATCH | COMPLEMENT | CLASH,
  column:   STYLE | VIBE,
  modes:    [COMPETITIVE, FOR_FUN],
  seats:    [PARTNER, OPPONENT],
  strength | severity }
```

A `MATCH` row has `a == b`, carries `column` and nothing else: no `strength`, because §5's
`dr(matches)` is a count. `modes` and `seats` default to both.

**Firing.** Given searcher tags `S` and candidate tags `C`, an entry `{a,b}` fires iff
`(a∈S ∧ b∈C) ∨ (b∈S ∧ a∈C)` — **at most once per entry per pair**, whoever holds what. A shared
tag may pay both a match and a complement; they are two different claims (*you both want this*
versus *your two things fit together*), and refusing the second would delete
`HERE_TO_IMPROVE + WARMS_UP_PROPERLY` for exactly the pairs it describes best.

**Entries are symmetric — there is no direction field.** Fit is already asymmetric through
familiarity, which reads the searcher's tags and never the candidate's, so asymmetry was
available and is refused here: every relationship §9.3.6 states is a both-sides claim, and a
directed row would score the same two people differently depending on who searched.

**A pair may carry more than one row, and their `modes × seats` scopes must be disjoint.** Two
pairs below use this, and the ruleset validator enforces it.

**Where no seat is assigned, a pair reads the `OPPONENT` row; a `PARTNER`-only row does not fire
at all.** §9.3.6 rule 3 — being wrong about a clash buries a person — so the unseated shortlist
takes the more forgiving reading, and the harsher one applies only once somebody is being seated
as a partner, which is [`the-group-objective.md`](the-group-objective.md) §2.2's **seat delta** —
added for the searcher's partner pair, and exactly zero for the two opponent seats because
unseated already reads `OPPONENT`. Singles and unseated doubles therefore read identically, which
is one fewer rule.

**One matrix, all four sports, and no `sport` field — ever.** A tag relationship is a claim about
people; *levels never transfer between sports* is a claim about **proof**, not about temperament.
The only sport-shaped variation the entries need is already carried by `seats`: padel and
badminton seat four, tennis and squash seat two
([`kernel/sports.py`](../../../backend/app/kernel/sports.py)), so a `PARTNER` row is unreachable
in the two-player sports by arithmetic rather than by rule.

## 2. What "exhaustive" means here

**Exhaustive on the match arm by obligation; sparse on the complement and clash arms by design.**

Each of the nineteen ids either takes a `MATCH` row or is named in §3 with the reason it takes
none — a **nineteen-row obligation, not a 171-pair one**. Authoring 171 pairs to a standard
anyone would defend is not possible, and a pair with no entry is not silence: it scores **0.20**
under §5's normalisation, which is the legitimate answer *different, not incompatible*.

The complement and clash arms take **no coverage rule**, because a coverage rule there would
manufacture relationships to fill a table. They are governed by §6's coverage report instead.

## 3. The eighteen match rows

Column defaults to the id's group and is overridden only where the claim plainly sits elsewhere.

| Column | Ids |
|---|---|
| **STYLE** | `TALKS_THROUGH_THE_MATCH` †, `PLAYS_TO_WIN`, `LAUGHS_OFF_MISTAKES`, `ENCOURAGES_A_PARTNER`, `GENEROUS_ON_LINE_CALLS`, `QUIET_AND_FOCUSED`, `WARMS_UP_PROPERLY` |
| **VIBE** | `STAYS_FOR_A_DRINK`, `STRAIGHT_HOME_AFTER`, `SETTLES_UP_ON_THE_SPOT`, `BOOKS_THE_NEXT_ONE`, `SHARES_A_LIFT`, `HERE_TO_IMPROVE`, `HERE_TO_COMPETE`, `HERE_FOR_THE_EXERCISE`, `HERE_TO_MEET_PLAYERS`, `HERE_FOR_A_REGULAR_GAME`, `HERE_TO_GET_BACK_INTO_IT` |
| **no row** | `OPEN_TO_MEET_SOMEONE` |

† **The one override.** `TALKS_THROUGH_THE_MATCH` is filed under `AFTER_THE_MATCH`, and *"you both
talk through the match"* is felt during the hour. §1 of `ranking-weights.md` names this id as the
clearest case that the split is by claim and not by group.

**`OPEN_TO_MEET_SOMEONE` takes no row of any kind**, by
[ADR-0115](../../adr/0115-a-tag-about-the-person-may-be-shown-never-scored.md): a tag about the
person rather than the game may be shown; it may never score.

**The two closest calls, kept.** `HERE_TO_COMPETE` and `HERE_FOR_THE_EXERCISE` sit near **intent
alignment** — term 3, at 14/14, larger than either tag column in competitive — and §9.3.6's strike
rule never had intent in view, because intent is the eighth term the prototype lacked. They keep
their rows because play intent is **per sport and revisable**
([ADR-0094](../../adr/0094-play-intent-declared-per-sport-in-its-own-aggregate.md)) while a social
tag is per person and platform-wide: a player can be competitive at squash and here for the
exercise at padel, and the tag says which of those is *them*.

**The derived domains.** Adding the ids named in §4 and §5, `STYLE` holds **10 of 19** and `VIBE`
holds **12 of 19**; `OPEN_TO_MEET_SOMEONE` is in neither.

| Column | Domain |
|---|---|
| **STYLE** | the seven above, plus `HERE_TO_IMPROVE`, `HERE_TO_GET_BACK_INTO_IT`, `HERE_FOR_THE_EXERCISE` |
| **VIBE** | the eleven above, plus `TALKS_THROUGH_THE_MATCH` |

Two consequences of that, both live under §5's stand-down rule (*a column stands down when either
side holds no tag in that column's domain*):

- A player holding only `ON_THE_COURT` tags **stands VIBE down**, which in for fun is **24.2 of
  100** renormalising away. §5's worked case was the mirror of this one.
- A player who spends one of their minimum two tags on `OPEN_TO_MEET_SOMEONE` has spent half
  their budget on something the matcher never reads, and nothing tells them —
  [ADR-0115](../../adr/0115-a-tag-about-the-person-may-be-shown-never-scored.md) accepts that
  price rather than solving it.

## 4. The twelve complement rows

Six are §9.3.6's. Its seventh — `HERE_TO_IMPROVE` + *"a stronger, focused opponent"* — is struck
by ADR-0115 rule 3: it reads μ and is not a tag pair. Six are added, because six complements over
171 pairs leaves the arm decorative.

| a | b | column | modes | strength | Why |
|---|---|---|---|--:|---|
| `HERE_TO_IMPROVE` | `WARMS_UP_PROPERLY` | STYLE | both | 0.70 | §9.3.6 — one wants to get better; the other runs the half hour that does it |
| `HERE_TO_GET_BACK_INTO_IT` | `ENCOURAGES_A_PARTNER` | STYLE | both | **1.00** | §9.3.6 — the returning player and the person who makes returning bearable |
| `HERE_TO_GET_BACK_INTO_IT` | `GENEROUS_ON_LINE_CALLS` | STYLE | both | 0.70 | §9.3.6 — a first game back should not be litigated |
| `HERE_FOR_A_REGULAR_GAME` | `BOOKS_THE_NEXT_ONE` | VIBE | both | **1.00** | §9.3.6 — the standing four, and the person who actually makes it standing |
| `HERE_TO_MEET_PLAYERS` | `SHARES_A_LIFT` | VIBE | both | 0.70 | §9.3.6 — one needs a way in; the other is already going |
| `HERE_TO_MEET_PLAYERS` | `STAYS_FOR_A_DRINK` | VIBE | both | 0.70 | §9.3.6 — the same, an hour later |
| `HERE_TO_GET_BACK_INTO_IT` | `LAUGHS_OFF_MISTAKES` | STYLE | both | 0.70 | rust, unremarked on |
| `HERE_TO_GET_BACK_INTO_IT` | `WARMS_UP_PROPERLY` | STYLE | both | 0.70 | a body that has been off needs the half hour more, not less |
| `HERE_TO_MEET_PLAYERS` | `BOOKS_THE_NEXT_ONE` | VIBE | both | 0.70 | one wants a way in; the other turns one game into several |
| `HERE_TO_MEET_PLAYERS` | `TALKS_THROUGH_THE_MATCH` | VIBE | both | 0.70 | for one of them the conversation is the point |
| `HERE_TO_IMPROVE` | `PLAYS_TO_WIN` | STYLE | `COMPETITIVE` | 0.70 | the struck μ row's intent, in tag ids only — §9.3.6: *"that is precisely how you improve"* |
| `HERE_FOR_A_REGULAR_GAME` | `SHARES_A_LIFT` | VIBE | both | 0.70 | the standing game somebody drives to — **the weakest of the six added** |

**All twelve are unscoped on `seats`**, the two returning-player rows included: their value is
largest in exactly the unseated shortlist a `PARTNER` scope would exclude them from, and
`ENCOURAGES_A_PARTNER`'s wording is partner-shaped where its behaviour is not.

**Two rows at 1.00 and a ceiling there.** `TAG_COMPLEMENT_STRENGTH = 0.70` is the default and
1.00 is the maximum, which **narrows §9.3.6**'s claim that some complements are *"sometimes better
than a match"* — see [ADR-0115](../../adr/0115-a-tag-about-the-person-may-be-shown-never-scored.md)
rule 5. No row sits below the default: a complement product is not confident about should not be
a row.

## 5. The seven clash rows

§9.3.6 gives four in a table and a fifth in prose. `TALKS_THROUGH_THE_MATCH ↔ QUIET_AND_FOCUSED`
is *"far worse as partners than as opponents"*, which one `severity` field cannot say — so it
becomes **two rows with disjoint seat scope**, introducing no constant.

| a | b | severity | column | modes | seats | Why |
|---|---|---|---|---|---|---|
| `TALKS_THROUGH_THE_MATCH` | `QUIET_AND_FOCUSED` | **REAL** 0.15 | STYLE | both | `PARTNER` | §9.3.6 — *"ruins the hour for both"*, far worse as partners |
| `TALKS_THROUGH_THE_MATCH` | `QUIET_AND_FOCUSED` | MILD 0.06 | STYLE | both | `OPPONENT` | the same relationship, across the net |
| `STAYS_FOR_A_DRINK` | `STRAIGHT_HOME_AFTER` | MILD 0.06 | VIBE | `FOR_FUN` | both | §9.3.6 — *"in a competitive game nobody promised an evening"* |
| `PLAYS_TO_WIN` | `HERE_FOR_THE_EXERCISE` | MILD 0.06 | STYLE | `FOR_FUN` | both | §9.3.6 |
| `PLAYS_TO_WIN` | `LAUGHS_OFF_MISTAKES` | MILD 0.06 | STYLE | both | `PARTNER` | §9.3.6 — *"partner relationship only"* |
| `PLAYS_TO_WIN` | `HERE_TO_IMPROVE` | MILD 0.06 | STYLE | `FOR_FUN` | both | §9.3.6 prose — *"a mild one in a friendly"*; disjoint with §4's competitive complement |
| `STRAIGHT_HOME_AFTER` | `HERE_TO_MEET_PLAYERS` | MILD 0.06 | VIBE | `FOR_FUN` | both | added — the negation of two complements already in the table |

**One deliberate omission, stated rather than left silent.** `PLAYS_TO_WIN ↔ HERE_TO_GET_BACK_INTO_IT`
is a real mismatch and takes **no row**: level fit already separates them, and the returning
player is the population [The newcomer path](https://github.com/Raketa02/Raketa/issues/175)
decided to protect. A clash row against them costs more than it buys.

### Where the clash arm is audible

The rows above make `CLASH_CAP = 0.25` reachable in for fun and unreachable in competitive.
Against §5's *no relationship fired* baseline of 0.20:

| | worst reachable Σseverity | term value | cost of 100 |
|---|--:|--:|--:|
| Competitive, singles — tennis, squash | 0.06 | 0.152 | **0.5** |
| Competitive, doubles, partner seat | 0.21 | 0.032 | 1.7 |
| For fun, either | 0.25 — **capped** | 0.00 | up to 7.3 |

**This is the answer to *are the sparse regions sparse on purpose* for that region: yes, and here
is the number.** §9.3.6 scoped three of its four clashes to for-fun itself, and competitive
players are separated by level rather than by temperament — so the clash arm being worth half a
point in competitive singles is the document's own design, now measured instead of assumed.
`CLASH_CAP` stays at 0.25: a guard whose job is stopping a later ruleset burying somebody is
doing that job when it rarely binds. A ruleset that widens the clash arm is changing this table,
and should say so.

## 6. The falsifier

**`ranking-weights.md` §5's proposed falsifier is testing the formula, not the matrix, and is
replaced.** It reads: *if raw is bimodal at 0 and 0.55 rather than spread, the matrix is too
sparse.* But `dr(n) = 1 − 0.45ⁿ` takes seven values — 0, 0.55, 0.80, 0.91, 0.96, 0.98, 0.99 — so
raw is **discrete by construction** and lumpy at 0 and 0.55 whatever the matrix contains. It
would fire on day one against a perfect matrix.

**In its place: a coverage rate.**

| Threshold | Value | What it is |
|---|--:|---|
| `MATRIX_COVERAGE_FLOOR` | **0.20** | the fraction of scored pairs in which at least one **complement or clash** row fires, over a rolling month |

Below the floor, the matrix is decorative: the honest move is to add rows, or to collapse both
terms to a shared-tag count under a name that says so. It is a **reporting threshold, not a
ruleset constant** — nothing in scoring reads it, so it owes a §24 row and no falsifier of its
own. The raw-score distribution stays a *reported* statistic.

The `TAG_PHI`, `TAG_COMPLEMENT_STRENGTH`, `CLASH_SEVERITY_*` and `CLASH_CAP` falsifiers in
[`ranking-weights.md`](ranking-weights.md) §5 are unaffected and stand.
