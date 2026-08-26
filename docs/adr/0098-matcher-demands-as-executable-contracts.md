# ADR-0098 — What the matcher demands of the contexts that do not exist is an executable contract

- **Status:** Accepted
- **Date:** 2026-08-26

> **Amended 2026-08-26 by [ADR-0114](0114-a-newcomer-may-not-be-declined.md) and
> [`the-newcomer-path.md`](../specs/matchmaking/the-newcomer-path.md): opponent variety is
> withdrawn from the contract.** It was demanded on behalf of two consumers — familiarity's sign
> flip (§9.4) and the welcoming-record modifier.
> [#164](https://github.com/Raketa02/Raketa/issues/164) struck the first as a statistic that does
> not exist; [#175](https://github.com/Raketa02/Raketa/issues/175) struck the second as an input
> the style and vibe terms already pay for. **A consumer-driven contract with no consumer is
> withdrawn, not carried**: the whole discipline is that a demand is executable against a
> provider, and a demand nobody reads is a demand nobody notices going wrong. The six strands,
> the two standing-down powers and everything else below are untouched. If a later term wants
> variety, it returns as that term's demand and signs for it.

## Context

Of the eight Fit terms in
[`docs/specs/matchmaking/matchmaking-engine.md`](../specs/matchmaking/matchmaking-engine.md) §9.3,
five work against the backend as it stands. The rest read `player_score`, `matches` and `cases`,
**none of which exist**, and the map
[The matchmaking engine: who sits down, and why](https://github.com/Raketa02/Raketa/issues/155)
does not build them. It writes down what the matcher *demands* of them, and
[ADR-0093](0093-matcher-in-the-backend-with-a-pure-match-fit-engine.md)'s §10 degradation
property is what lets the engine ship in the meantime. This record settles
[#163](https://github.com/Raketa02/Raketa/issues/163).

**The specific failure this is written against.** §9.3.4 reads the Player Score's **six strands
separately**, because *confirms results* is close to worthless for a friendly and close to
essential for a counted game, and one blended number cannot express that. The Player Score is
**one number in the UI**. So the obvious thing for whoever builds `player_score` to ship is the
number the screen shows — at which point the entire strand-decomposition argument dies quietly,
and nobody finds out until somebody wires the term up and discovers there is nothing to
decompose. Every fact in this ADR has that shape: an unwritten demand is satisfiable by
accident, and a demand satisfied by accident is a demand that will not be.

**Prose is exactly as strong as whoever reads it.** The map's output is specs and ADRs, so the
cheap answer is a document under `docs/specs/matchmaking/` describing the required shape. That
document cannot fail a build, and the day it matters is months after the day it is written, in
a session that has never opened it.

**Three repository facts bear on the shape.**

- The candidate index is **one row per `(player, sport)`** (§7.2). Every `matches` fact the
  matcher wants except the open-challenge count — previous accept, previous decline, games
  played together, ghosted together, a challenge pending *between you* — is a fact about a
  **pair**. There is nowhere in that row to put a pair, and materialising a pair table across a
  city is absurd when a searcher has played, at most, tens of people.
- [ADR-0095](0095-block-directed-record-symmetric-effect-gates-fail-closed.md) already solved
  the identical problem for blocks: the searcher's own set travels with the search in the
  `SearchContext`, the index holds nothing, and the backend re-verifies live on the way out. It
  also already ships a gate against a context that does not exist —
  `AccountHoldQuery` with its one adapter `NoHoldsExist`, **named for the fact it asserts
  rather than for being empty**.
- The prototype computes *settles up* from a **live open case** (`social-prototype-v1.html:3376`
  — `0.15` when one exists), and its stored record holds counts for only three of the six
  strands (`:538` — `show`, `ans`, `res`, plus a sportsmanship mean and a variety figure).
  *Settles up* and *keeps plans* have no denominator anywhere.

The alternatives considered and rejected:

- **A prose contract only.** Rejected: see above. It is the thing this record exists to replace.
- **Demanding the six strands as bare `0–100` values**, as §7.2's index schema does
  (`strand_shows_up uint8 | null`). Rejected — see Decision 2. It cannot distinguish one
  no-show out of one game from thirty-five of thirty-eight, and it makes the absence rule a
  matter of trusting that somebody else sends `null` rather than `0`.
- **The matcher re-deriving strand values from raw counts.** Rejected: the player reads those
  strands on their own Player Score screen. A card that explains a match using a number the
  player's own profile disagrees with breaks the explainability refusal more thoroughly than
  saying nothing would.
- **Ports split by liveness** — one contract for what feeds the index, another for what is read
  live. Rejected: `player_score` would then have signed half of two contracts and all of
  neither, and the point of a consumer-driven contract is that one provider signs one thing.
- **A pair table in the candidate index.** Rejected on the same arithmetic that killed §9.2's
  geo-cell buckets in [#161](https://github.com/Raketa02/Raketa/issues/161): the pairs a search
  needs are the searcher's own, they number in the tens, and reading them once per search costs
  nothing against the measured 1.00 µs per surviving candidate.
- **Contract tests that skip until a provider exists.** Rejected — see Decision 4. A skipped
  test is a test nobody is watching, which is the guardrail failure `CLAUDE.md` already names:
  *a guardrail that silently stops matching is worse than none.*

## Decision

**1. Three ports, one per provider context, and one provider signs one contract.**
`PlayerScoreQuery`, `MatchHistoryQuery` and `AccountHoldQuery` (the last already standing from
ADR-0095). `MatchHistoryQuery` carries the searcher's pairwise read, the per-player
open-challenge count, and the origin-key demand of Decision 7. The split is by **who supplies
the fact**, never by how fresh it has to be.

**2. Every demanded fact crosses as a value, its evidence, and when it was last observed.**
For each of the six strands: the published value, the **numerator and denominator** behind it,
and the moment of the most recent observation. Sportsmanship crosses as its mean and the number
of ratings. ~~**Opponent variety is demanded as a seventh published statistic that is explicitly
not a strand** and never blended into the printed score.~~ **Withdrawn** — see the amendment
above. The unit of observation is named for
each strand in the contract spec; two people reading it compute the same denominator.

**3. The matcher reads what the player is shown, and never re-derives it.** Its entire policy
is the power to **stand a strand down**: below `RELIABILITY_MIN_OBSERVATIONS = 3` a strand is
`NoEvidence` on its own and the survivors renormalise *inside* the reliability term, exactly as
§10 renormalises terms inside Fit; past `RELIABILITY_HORIZON_DAYS = 365` since the most recent
observation across all strands, the whole term stands down. Both are **ruleset configuration**,
under ADR-0093's frozen ruleset version, and both are admitted hypotheses with a falsifier
recorded beside them. Decay is the provider's job and the matcher does not apply a second one.

**4. Pairwise facts travel with the search, bounded, and never enter the index.** The
searcher's most recent **500** pairwise counterparts — accepted, declined, played, ghosted,
each distinguishable from the others — plus **every** currently-open challenge, unbounded, read
once and carried in the `SearchContext`. The index keeps only the per-player open-challenge
*count*, advisory, for ranking on load. **The history read fails soft**: familiarity and the
previous-decline signal stand down and the search proceeds, because §7.5's *the matcher
proposes, the backend disposes* is a second net under a duplicate proposal. The block read is a
separate read and **keeps failing closed** under ADR-0095.

**5. The contract suite is parameterised over every registered implementation of each port,
including the null one.** `NoPlayerScoresExist` and `NoMatchHistoryExists` prove the degradation
behaviour green today, named for the facts they assert in ADR-0095's style. The moment a real
adapter is registered it is enrolled automatically, and either satisfies the suite or the build
is red. There is no skipped test to go stale, and no version of *shipped as one blended number*
that passes.

**6. A gate may be honestly empty; a term may never be honestly neutral.** The test for what a
missing context yields is whether a zero would be **measured** or **invented**. No challenge has
ever been sent by anyone, so the open-challenge count is a real zero and the pending-pair set is
really empty: **true-over-empty**, wired and live, like the hold gate. Nobody has failed to turn
up, because nobody has ever been due to — so every `player_score` fact is **`NoEvidence`**, and
so is familiarity with no history, on the grounds that a modifier firing identically on every
candidate changes no ranking while printing a sentence on every card.

**7. A challenge names its origin, and the field is not optional.** Every challenge carries
either the `(search_id, position)` it was sent from or an explicit value saying it came from
somewhere else. Never a nullable field left absent by a caller in a hurry: §19.2 is right that a
search not joined to its outcome is evidence that no longer exists, there is no backfill, and
the loss is permanent and silent.

**8. Reading `cases` to score is forbidden.** One live boolean per player, for the gate, and
nothing more. *Settles up* is `player_score`'s to compute and publish from the historical record
— **shares that fell due against shares settled without a case being opened** — which corrects
the prototype, where the strand *is* the live case. A held player is both excluded by the gate
and carrying a low *settles up*; that is the intended double reach and not a duplication to be
tidied away later.

## Consequences

- **The expensive mistake becomes impossible rather than unlikely.** `player_score` cannot ship
  as one number, because the adapter that would do so cannot pass its own contract suite. That
  is the whole return on this record.
- **A build that has never had a `matches` context has a red-capable test suite about it.** New
  engineers will find contract tests for three contexts that do not exist and assume they are
  dead. The null adapters are named for the facts they assert precisely so the answer is legible
  at the call site.
- **The matcher has taken an opinion about a context it does not own.** Naming the denominator
  of *keeps plans* is a demand on whoever builds `matches`, and they may arrive with a better
  one. That is a conversation, and it amends this record; it is not a licence to publish a
  different number under the same name.
- ***Settles up* will stand down long after the other five are live.** It depends on court
  money, which the map rules out of scope. Expected, written down, and not a defect.
- **Two hypotheses now carry the matcher's name rather than the document's.** §24's constants
  table has no reliability freshness constant at all; `RELIABILITY_MIN_OBSERVATIONS` and
  `RELIABILITY_HORIZON_DAYS` are invented here and owe their falsifiers, recorded in the spec.
- **The pairwise read is a per-search cost the index was designed to avoid.** It is one bounded
  read keyed on the searcher, and #161's measurements say it disappears against the scoring
  loop — but it is the first thing to look at if search latency regresses.
- **A degraded search is now silent in a new way.** When the history read fails soft, the player
  gets a shortlist with no familiarity and no sign that anything was missing. The per-term
  `NoEvidence` rate in §19.3 is what makes that visible; it is load-bearing, not garnish.
