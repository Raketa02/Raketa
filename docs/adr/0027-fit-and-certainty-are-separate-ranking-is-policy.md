# ADR-0027 — Fit and certainty are separate numbers, and ranking a list is policy

- **Status:** Accepted
- **Date:** 2026-08-17

## Context

Match Fit collapses a six- or seven-dimensional decision into one comparable score so that a
list of ten open matches becomes rankable. The prototype builds that score from seven weighted
terms summing to 100, and gives three of them a friendly default when the underlying fact is
unavailable: skill overlap scores a perfect **1,0** when nobody is seated yet, predicted balance
defaults to **0,70** when there are too few players to forecast, group reliability defaults to
**0,80** when there is nobody else to be reliable.

Score an empty match with those defaults — counted, cheap, nearby — and it comes to **90,5**.
Score the prototype's own canonical fully-formed, well-balanced, well-priced match and it comes
to **84**.

That is not a tuning problem. **The score is monotonically decreasing in information**: the more
the platform knows about a match, the lower it scores. A home list built this way is topped by
matches nobody has joined, which is self-reinforcing — the best-ranked cards have the least
evidence, players tap them, find them empty, and stop believing the list. The cause is
structural: "we don't know" and "it's good" are encoded as the same kind of number, so nothing
downstream can tell them apart.

The rating context already resolved the same problem in its own domain and wrote the rule down:
*"Skill and certainty are separate variables — two players both showing 3,0, at ±0,15 and ±0,90,
are not the same player, and matchmaking reads the record rather than the headline."* Match Fit
had quietly re-collapsed exactly that distinction.

A second force points the same way. Rakieta is a two-sided marketplace, and a list ranked purely
by fit-to-this-player starves the supply side: a newly created match has little evidence, ranks
low, gets no impressions, does not fill, and confirms its own score. Fixing that needs
exploration — deliberately showing some matches the score does not yet favour — and exploration
needs controlled randomness, configuration and experiments. An engine that is pure,
deterministic and reproducible by decree ([ADR-0015](0015-engines-as-a-pure-versioned-layer.md))
is the wrong place for every one of those.

The alternatives considered:

- **Keep one score and tune the defaults down.** Cheap, and it moves the symptom without
  removing it: any default is still a fabricated observation, and the next person to add a term
  with a friendly-looking fallback reintroduces the bug. It also leaves nothing able to answer
  *"how much of this score is real?"*
- **Keep one score and subtract an uncertainty penalty**, as the balance forecast originally
  did with its spread term. This makes a thin score and a mediocre score indistinguishable,
  which is the same collapse in the other direction — and it hard-codes one trade-off between
  quality and confidence for every consumer of the score.
- **Put exploration and diversity into the engine as more terms.** Keeps one component, and
  breaks reproducibility: either the engine draws randomness, or exploration is not exploration.
- **Two numbers from the engine, and a separate policy that ranks with them.**

## Decision

We will have the engine report **fit and coverage as two numbers**, type every term by what its
absence means, and put **ranking policy outside the engines layer entirely**.

- **Every signal is a term.** The prototype's `+8` / `+5` / `−8` modifiers, applied after the
  weighted sum and pushing the score outside 0–100 before clamping, are abolished; ladder
  qualification and familiarity become terms with weights. A bonus added outside the weighting
  has no defined meaning once weights are renormalised, and renormalising is now the mechanism.
- **A term is a *constraint* or a piece of *evidence*, and the kind is a property of the term,
  not a convention.**
  - A **constraint term** encodes a limit the player declared — price, distance, hours, match
    type. An undeclared limit is genuinely no limit: the term scores full marks, keeps its
    weight, and coverage is unaffected. This is the intent pool's partial-profile rule, which
    already says a missing price ceiling means *eligible at any price*.
  - An **evidence term** encodes something the platform observed — skill overlap, predicted
    balance, reliability, familiarity. Absent evidence is **not** a good score. The term is
    excluded, the surviving weights are renormalised over what actually ran, and coverage falls.
- **Skill overlap is evidence.** With nobody seated there is no target to overlap with, so it is
  excluded rather than scored 1,0 against the player's own level. That single reclassification
  removes 30 of the 90,5 points that made an empty match outrank a good one.
- **Coverage is reported, never blended.** The engine returns the fit score and how much of the
  weight produced it. A thin score and a strong score are different facts.
- **Terms may ship dark.** Reliability and familiarity depend on contexts that do not exist;
  their snapshot fields are present and absent from day one, so they are simply excluded and
  coverage says so. A term that ships *absent* can be introduced later without invalidating any
  historical score. A term that ships as a fabricated `0,8` has already poisoned every score
  ever computed, and nothing can afterwards say which.
- **Ranking is a policy object in the calling module's application layer, not an engine.** It
  composes fit and coverage and owns exploration, diversity caps (per club, per time slot),
  freshness, the impressions an unfilled match is owed, and where the tail is cut. It may read
  configuration, run experiments and draw randomness, because it is not an engine and makes no
  claim to reproducibility.
- **Candidate generation excludes on facts, never on preferences.** Sport, seats remaining, the
  join cutoff, live inventory and calendar conflicts are hard filters. Distance, price and level
  are never exclusions — the intent pool's rules are explicit that *nothing is ever excluded on
  distance* and that price is *a condition, not a rejection* — so they reach the player as a
  lower score, not as an absence.

## Consequences

**Easier**

- Absence can no longer flatter a match, and it is now checkable rather than hoped for:
  excluding a term must never raise a score, which is a property test.
- Every consumer picks its own quality-versus-confidence trade-off from the same two numbers,
  instead of inheriting one baked into a single figure.
- The engines stay pure and deterministic while the list stays adaptive, because the adaptive
  part is somewhere else.
- *"Does the policy starve the tail?"* becomes a property test over the ranker alone, with no
  engine, no database and no HTTP.
- Launch coverage will be genuinely low and will report itself, which is the correct account of
  a platform that has not yet observed anything.

**Harder**

- **Two numbers are harder to explain than one**, to a reader of the code and to a player. A
  score of 84 at 60% coverage is a more honest and less immediately legible thing than a score
  of 84.
- **Renormalisation makes scores less comparable across matches** than a fixed denominator does:
  two matches scoring 80 may have been scored over different term sets. Coverage is what makes
  that visible, but it does not make it go away, and a naive sort across mixed coverage will
  mislead.
- **A second place where product judgement lives.** Constants are in the engine, policy is in the
  ranker, and answering "why did this rank first" now means reading both.
- **Exploration deliberately shows players matches the score does not favour**, and some of those
  will be worse experiences. That cost is real and is being paid to keep supply alive.
- Term kinds are a new thing to get right, and getting one wrong is a silent scoring bug rather
  than a failure.

**Neutral**

- The weights themselves are unaffected by this record; they are v1 hypotheses carrying their own
  falsifying measurements, as every engine constant must
  ([ADR-0015](0015-engines-as-a-pure-versioned-layer.md)).
- The same estimate-plus-margin shape appears in the balance forecast, where the point estimate
  ranks and the margin decides whether the card prints it. Both are the same rule: report what
  you believe and how much you believe it, separately.
