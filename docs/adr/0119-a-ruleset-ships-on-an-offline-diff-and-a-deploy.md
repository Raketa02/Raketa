# ADR-0119 — A ruleset ships on an offline diff and a deploy; shadow and canary are priced, not built

- **Status:** Accepted
- **Date:** 2026-08-26

> **Note — the Classic play removal (2026-10-06, [#569](https://github.com/Raketa02/Raketa/issues/569)).** The offline diff and its gate are gone — `check-ruleset-diff.sh`, the replay harness's corpora and the searches they read (#572, #579) — and with no search there is nothing to shadow or canary, so §1–§4 and §5's first paragraph describe nothing that runs. The one live dataset, `2026.09.15-a`, was then trimmed in place (#580): the ranking's sections were cut, no number moved, and the two older releases were deleted. What stands is §6 — the ruleset is validated at import, and a malformed one fails the deploy and never falls back — and §5's rule that a pull request moving a number carries one line per changed constant with its hypothesis and its falsifier. Since the trim, a released dataset is never edited again.

## Context

`matchmaking-engine.md` §22 ends with one rollout
for every phase: **shadow** (the matcher runs, logs its answers, serves nothing) → **canary**
(5% of searches, watch acceptance and empty rate) → **full**, and *"ruleset changes always go
through §20.3 first."* §11 adds that A/B falls out for free — a search can be assigned a ruleset
by a stable hash of the searcher id.

That was written for a separately deployed Go service with a runtime config store.
[ADR-0093](0093-matcher-in-the-backend-with-a-pure-match-fit-engine.md) made the matcher a
backend module whose ruleset **ships embedded with the code**, and deferred the runtime store;
[ADR-0028](0028-four-environment-model-and-typed-configuration.md) leaves only `local` running.
So *"ships"* means a deploy, and each rung of the ladder has to earn its place against that.

**Canary's obstacle is not the one the ticket named.** Hash assignment needs no routing surface —
it is an in-process branch over two embedded rulesets — and `ruleset_version` is on every `search`
row (`search-telemetry.md` §2), so every rate in §19.1
stays computable per arm. Nothing about it is
ADR-0101's trigger 2. The obstacle is that
**a canary's success metric is acceptance**, and the outcome half of the telemetry chain needs the
`matches` context, which does not exist. At §17's peak — 1–20 searches a second in one launch
city — 5% is a handful of searches a day, measured against a rate nobody can compute.

**Shadow's obstacle is that something cheaper already answers most of the question.** Shadow is
the *only* full-fidelity instrument on real traffic: it runs at the one moment the live inputs
exist, so it applies the block and hold gates and can promote candidates from outside the recorded
band, which ADR-0118's offline diff cannot. Its price
is honest and it is not the scoring cost. Doubling the scoring call moves the duty cycle from
**0.07 to 0.14**, comfortably inside trigger 1's **0.25**
(`scale-posture.md` §4) — affordable, which is not the
same as worth spending. What it actually costs is **a second deploy and a wait before the real
one**, forward-only sampling at launch traffic, and a doubling of `search_candidate`, already the
largest table in the system with a 100-million-row revisit trigger
(ADR-0104 §3).

**The enforcement idiom is already in this repository, twice.** `check-contract-drift.sh` with
`make test-drift`, and `check-poetry-pin-drift.sh` with `make test-poetry-pin` — each driving its
own check against a deliberately broken tree and asserting it goes red, on `CLAUDE.md`'s stated
reason that *a guardrail that silently stops matching is worse than none, because you stop
watching for it.*

## Decision

**We will ship a ruleset on an offline diff and a deploy. Shadow and canary are named with
reachable triggers and not built.**

### 1. Rollout is one gate and one deploy

Offline diff (ADR-0118) → deploy → watch the search-side rates that already exist. §22's three
rungs collapse, and nothing in the collapse is deferred work: the diff answers *what would this
ruleset have done*, and the search-side rates — empty results, shortlist length, floor clearance,
rung-offer computation — answer *what is it doing now*, from the first search after the deploy.

### 2. Canary is deferred, and the reason is the missing metric

Written down because **the infrastructure reason is wrong and would be believed**: it is not a
routing surface, it is not trigger 2, and anybody re-deriving it from §11 will correctly conclude
it is nearly free to build. It is deferred because it cannot measure its own success.

**Trigger to return:** the outcome half of the chain exists, **and** somebody states the effect
size worth detecting and the weeks of traffic that would detect it. A canary that cannot name its
own power is theatre with a deploy attached.

### 3. Shadow is deferred, with a trigger that is actually reachable

**Trigger to build it:** the first time ADR-0118 §3's classifier calls a change **shape-class**
*and* the owner in §5 judges the synthetic corpus insufficient to sign it. That is the precise
condition under which nothing else can answer — and until it occurs, shadow buys a slower version
of an answer already on hand.

### 4. The gate is half mechanical and half signed, and the split is stated

*No ruleset ships without a diff* stops being a sentence.

- **The synthetic diff is a committed artifact.** CI regenerates it and fails if it differs, in
  `check-ruleset-diff.sh`; `make test-ruleset-diff` drives that check against a deliberately
  broken tree and asserts it goes red. A ruleset edited without regenerating its diff fails the
  build, exactly as a contract changed without its client types does.
- **CI regenerates it under a different `PYTHONHASHSEED` than the one that produced the committed
  file.** This is the sanctioned exception ADR-0105 §4 already carves out — *"the one place a seed
  is set deliberately is the test in §2, which sets two of them and compares"* — and it is a
  second instance of it, not a breach. It costs one environment variable and turns the artifact
  into a **continuous whole-pipeline determinism assertion**, where §2 asserts determinism over
  one test.
- **The recorded-corpus diff cannot run in CI.** There is no database, and ADR-0118 §7 restricts
  it to a restore. CI asserts that the pull request carries a report block naming its **corpus
  window** and its **coverage figure** — **presence, not truth**. Half of this gate is a machine
  and half is a signature, and pretending otherwise would be the decoration this map exists to
  refuse.

### 5. A named owner signs, and the PR carries the argument

**The same person accountable for the quality floor** (§23 Q10,
`ranking-weights.md` §10) signs a ruleset release. One
number decides when the product says nothing rather than something, and the numbers around it
decide what it says instead; splitting the accountability makes each owner reasonable and the pair
of them wrong.

The pull request carries the diff plus **one line per changed constant: the hypothesis, and what
would falsify it** — §24's and `ranking-weights.md` §13's existing discipline, applied at the
moment a constant actually moves rather than only when it is first written down.

### 6. §11's fallback is restated for an embedded ruleset

*"A malformed ruleset refuses to load and the previous one keeps serving"* has no hot reload to
fall back through. **Validation runs at startup; a bad ruleset fails the deploy; the previous
version keeps serving because the old pods are still up.** Same guarantee, different mechanism —
including `scale-posture.md` §6's engine-side ceiling that refuses a ruleset exceeding `K = 24`.

This stops being true the day the runtime ruleset store lands, which is one more thing that
deferral owes.

## Consequences

**Easier**

- **A weight change is one pull request and one deploy**, with a diff attached that reaches back
  to the first search ever recorded. That is the friction ADR-0106 wanted at this boundary — cheap
  to move a number, expensive to change what the product claims it can explain — with nothing
  extra bolted on.
- **Two mechanisms stop being half-built.** Shadow and canary each have a written price and a
  condition, so neither is reached for out of habit nor rediscovered from scratch.
- **Determinism gets a second, continuous enforcement for the price of an environment variable.**

**Harder**

- **Half the gate is a signature, and a signature can be given without reading.** The mechanical
  half cannot see the recorded-corpus diff at all. This is the weakest joint in the decision and
  it is named rather than dressed.
- **No live A/B, so no weight change is ever justified by a measured outcome** until the outcome
  half of the chain exists. Every release until then is argued from a diff and from search-side
  rates — which is strictly more than the document's *"I think vibe should be 24"* and strictly
  less than the experiment §11 promised.
- **The rollout ladder in §22 no longer describes what happens**, and a reader who takes it
  literally will look for a shadow phase that is not there. The conflict table carries the row.
- **`check-ruleset-diff.sh` is a fourth check of the same shape**, and the four now share a failure
  mode: each is only as good as the `make test-*` that proves it still fires. That is the argument
  for the pattern, restated as its cost.
