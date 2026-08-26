# ADR-0115 — A tag about the person may be shown; it may never score

- **Status:** Accepted
- **Date:** 2026-08-26

## Context

The tag relationship matrix is product-owned ruleset data (§23 Q18) and it feeds two of the
eight Fit terms — playing style and social vibe, together 14.9 of 100 in competitive and
**36.3 of 100 in for fun**, where social vibe is the largest term in the match.
[ADR-0106](0106-evidence-vocabulary-is-contract-weights-are-configuration.md) settled that a
ruleset may move every number for free, so the matrix is the one part of those two terms that
product edits without an API release. [The ranking weights](https://github.com/Raketa02/Raketa/issues/168)
settled its **shape** and left its **content** unauthored — and an unwritten matrix is not a gap
in a table, it is two of the eight terms not working.

**The shape contradicted itself, in a way that decided a product question by accident.**
`ranking-weights.md` §1 gives the entry as `{a, b, kind: MATCH | COMPLEMENT | CLASH, column, …}`
— an explicit row per relationship. Two paragraphs later it rules that *"a **matched** single tag
falls to its own group's column"*, which only means anything if a match is **implicit**: every
shared tag scores, and its column comes from the group the vocabulary filed it in. Both cannot
be true, and nothing in the spec chose.

The choice is not cosmetic, because of what shipped on the day before this was written.
`social_tags.py` gained a nineteenth id, `OPEN_TO_MEET_SOMEONE`, and recorded in the same commit
that it *"sits at the edge of this module's own rule"* — a tag is about the game, never about the
person — and that it is deliberately not `HERE_TO_MEET_PLAYERS`, which is about finding people to
play with. Under **implicit** matching, two people who have both ticked *open to meet someone*
are scored higher for each other on that basis, in the term that carries a quarter of a for-fun
match. Nobody would decide that. It would simply follow, unremarked, from a rule written to
answer a different question — and the first person to notice would be a player.

The same silence covers the rest of the vocabulary. §9.3.6 offers eleven relationships over
nineteen ids — 171 unordered pairs — and states one strike rule, *"wherever a tag restates
something the matcher already measures, the measurement wins"*, illustrated by two examples that
turn out to have been struck for two different reasons. `HERE_TO_IMPROVE` + *"a stronger, focused
opponent"* is not a tag pair at all: it reads μ, and belongs to level fit. `SETTLES_UP_ON_THE_SPOT`
names a reliability strand — but the strand scores **one person's record** while a match scores
**a shared norm**, and reliability cannot express a pair fact under any weighting. Read as one
rule, the strike deletes real pair evidence; read as two, it deletes nothing that exists today
and forbids the row that would actually be wrong.

[ADR-0096](0096-gender-preference-mutual-gate-invisible-to-the-scorer.md) answered the adjacent
question for a protected characteristic — *may gate, may never score* — and enforced it as a type
boundary rather than a review checklist. A social tag cannot gate: §9.3.6 rule 1 is that
**tags never exclude anybody**, they move position. So the strongest available restriction for a
tag is one step weaker than 0096's, and it needs saying, because the mechanism that would
otherwise enforce it — a field simply not being in the scorer's input type — is unavailable here.
The tag *is* in the input. What it must not have is a row.

## Decision

**We will make `MATCH` an explicit row, and rule that a tag about the person rather than the
game may be shown but may never score.**

1. **A match is a row, not a rule.** The matrix holds one `MATCH` row per id that may match and
   **none** for an id that may not, so a strike is *data* rather than a second mechanism, and
   §1's claim that *"a column's tag domain is derived from the matrix"* stays literally true. A
   match row carries `column` and nothing else — no `strength`, because §5's `dr(matches)` is a
   count and a per-match weight would break it. The column may differ from the id's group, which
   is §1's whole thesis: `TALKS_THROUGH_THE_MATCH` is filed under `AFTER_THE_MATCH` and *"you both
   talk through the match"* is a claim about the hour on court.

2. **`OPEN_TO_MEET_SOMEONE` takes no row of any kind** — no match, no complement, no clash — and
   is therefore in neither column's derived domain. It stays in the picker, counts toward the
   2–6 selection, and reaches the player card under
   [ADR-0107](0107-the-player-card-is-assembled-outside-the-engine.md)'s `social_tags[]`, where a
   human reads it and decides for themselves. It already takes *neither* in the familiarity
   reading map, settled by [#164](https://github.com/Raketa02/Raketa/issues/164); this is the same
   call in the other map. The rule it stands for: **a tag about the person rather than the game
   may be shown; it may never score.**

3. **Both sides of an entry are tag ids.** This is what strikes `HERE_TO_IMPROVE` + *"a stronger,
   focused opponent"*, and it is checkable by the ruleset validator rather than by review.

4. **An entry scores agreement between two people, never a property of one.** `GENEROUS_ON_LINE_CALLS`
   and `SETTLES_UP_ON_THE_SPOT` therefore **keep their match rows** — a shared norm is not a record
   — and no strike is conditional on `player_score` landing, so no ruleset re-shapes when it does.
   What this rule forbids is the row nobody has written yet: *`PLAYS_TO_WIN` is good.*

5. **Complement `strength` has a ceiling of 1.00 and no override below the 0.70 default.** This
   **narrows §9.3.6**, whose complement preamble claims some pairs are *"sometimes better than a
   match"*. §5's own argument for the discount forbids it: a match is two people independently
   choosing the same string, a complement is product's editorial claim about two different ones.
   Parity is the most that claim can be worth. No downward override either — a complement product
   is not confident about should not be a row.

The 37 rows this authorises are in
[`docs/specs/matchmaking/tag-relationship-matrix.md`](../specs/matchmaking/tag-relationship-matrix.md).
They are ruleset data and revisable; the five rules above are not.

## Consequences

**A player can spend half their tag budget on something the matcher never reads, and nothing
tells them.** The floor is two tags; one of them may be `OPEN_TO_MEET_SOMEONE`. The picker
cannot warn without either publishing the matrix or implying the other eighteen are guaranteed
to score, and both are worse than the silence. This is the honest price of keeping the id in a
vocabulary a player chose it from, and it is accepted rather than solved.

**Eighteen near-identical rows exist so that one absence can be data.** A reviewer will propose
collapsing them back to a group map; the reason not to is `TALKS_THROUGH_THE_MATCH`, and the
reason not to special-case *that* is that the next override will not be predicted either.

**§9.3.6's rule 5 — *corroborated tags count more* — survives rule 4 and is worth saying so.**
Corroboration weights an entry by whether each side's claim is true against a record; it does not
introduce an entry that scores one person. When `matches` and `player_score` land, that upgrade
is still available.

**The clash arm is nearly silent in competitive singles, by consequence rather than by choice.**
With the authorised rows, the worst reachable clash in tennis or squash competitive costs **half
a point of 100**; `CLASH_CAP` binds only in for fun. That follows from §9.3.6 scoping three of
its four clashes to for-fun itself, and it is now a measured fact rather than an assumption —
recorded in the spec so that a later ruleset widening the clash arm knows what it is changing.

**Somebody will ask for a `sport` field on an entry.** There is none, and the refusal is
[`kernel/sports.py`](../../backend/app/kernel/sports.py)'s on `Format`: a tag relationship is a
claim about people, and the only sport-shaped variation the entries need is already carried by
`seats`, which is unreachable as `PARTNER` in the two-player sports by arithmetic rather than by
rule.

**This is one step weaker than [ADR-0096](0096-gender-preference-mutual-gate-invisible-to-the-scorer.md)
and cannot be strengthened.** 0096 keeps gender out of the scorer's *input type*, so a term
cannot read it because the value is not in the process. A social tag is in the input by
construction — the terms exist to read tags — so this rule is enforced by the ruleset validator
refusing a row naming `OPEN_TO_MEET_SOMEONE`, and by the matrix's coverage report, not by a type.
A future id at the same edge inherits the rule and the same weaker enforcement.
