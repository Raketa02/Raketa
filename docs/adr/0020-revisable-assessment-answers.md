# ADR-0020 — Revising an assessment answer truncates the transcript and replays

- **Status:** Accepted
- **Date:** 2026-08-15

Supersedes the **irreversibility rule** of [ADR-0017](0017-rating-context-event-sourced.md)
— *"Answers are append-only. No retraction event and no replay branching."* Every other
decision in ADR-0017 stands: both aggregates remain event-sourced, the stream remains
append-only, completion remains one transaction, and `expected_version` remains the
concurrency guard.

## Context

ADR-0017 made answers irreversible and named the cost in writing: *"it costs the player the
ability to change their mind two questions later."* That cost lands in the worst available
place. Onboarding is the first thing anybody does in this application, and the
questionnaire is the **entire** evidence surface for the resulting Skill rating — no
cross-sport transfer, no external rating, no coach assessment. A mis-tap on question three
is therefore not a small blemish on a large body of evidence; it is a permanent distortion
of a Level every later feature reads.

Three things follow, and the third is the one that made this urgent.

**A mistake is unfixable.** The five options on an execution question are close in meaning
by design and the screens move quickly. A player who realises at question six that they
misread question two has exactly one remedy: abandon the run and start the sport again from
the first question.

**The player never sees their answers as a whole.** One question at a time, with the
running estimate deliberately hidden — so a player commits to a rating built from six to
nine answers they have never seen assembled anywhere.

**Revisability disappeared without warning.** The confirm control's label is identical on
every question, necessarily: the engine decides it has heard enough only *after* an answer
arrives, so the client genuinely cannot know which question is the last one. A player taps
confirm on question eight exactly as they tapped it on the other seven and lands on a
result screen where their rating already exists.

**The irreversibility was already porous, which is why removing it costs less than it
looks.** The start guard is scoped to runs *in progress*, never to any run that ever
existed, so a player who wants to rehearse the questionnaire abandons and restarts — from a
control already on the screen. Revision inside one run is a strictly weaker affordance.
What actually keeps Contradiction detection from becoming opt-out is the **absence of
feedback**: no running estimate is shown at any point, and the tie-breaker arrives looking
like any other execution question. That property is untouched here and must stay untouched.

### The alternatives, measured rather than argued about

Three redesigns would have made the questionnaire revisable *on the device*, and each was
rejected on a figure rather than on taste.

- **Move question selection to the client.** `next_step` and `finalize` are siblings on a
  shared base of nine helpers, and that base *is* the evidence-and-fusion layer: the
  population prior, the self-report bias, the contradiction tolerance, and every answer
  option's (μ, σ) pair. Shipping it to the client means the fusion arithmetic exists twice,
  in two languages, in binaries that live on real phones for months — and it puts the
  engine's anchors where a player can read them and rehearse against them.
- **Ship a precomputed decision tree.** Enumerating the real tree gives **178 812 nodes and
  136 047 leaves for padel alone**, roughly 715 000 across the four Sports, before any
  question copy is attached.
- **Rebuild the questionnaire as a routing stage plus fixed level-specific modules.** This
  founders on the σ floor: three claim answers already put Uncertainty at **0,819–0,833**
  against a floor of **0,84**, so no module of any length can raise Confidence above the
  30% ceiling. With no ground-truth dataset, *"no less accurate"* could not have been shown
  for a new engine — only asserted.

## Decision

We will make an assessment answer **revisable for as long as the run is, and no longer.**

**Submitting an answer for a question the transcript already holds truncates the transcript
at that question and replays the engine from the resulting prefix.** Every answer after the
revised one is discarded.

**Truncation is the whole design, and it is what makes revision free.** An answer's numeric
meaning depends on the difficulty tier it was asked at, and that tier was chosen from the
estimate as it then stood — so an answer that outlived a change to an earlier one would
mean something the player never said. Because `next_step` and `finalize` are pure functions
of the transcript ([ADR-0015](0015-engines-as-a-pure-versioned-layer.md)'s no-hidden-state
rule), a truncated transcript is simply a transcript, and the engine asks whatever it would
have asked a player who answered that way in the first place.

**The engine is not modified.** No constant, question, tier, stopping rule, golden persona
or engine version changes. This is load-bearing rather than incidental: it is what makes
*"revising costs nothing in accuracy"* structural rather than measured. The regression
signal is that every existing engine test passes unchanged.

**The stream stays append-only.** A revision is an **appended** `AnswerRevised`; the
transcript is a *projection* over the stream that truncates when it replays one. Nothing is
deleted, and the record that the player changed their mind — and to what — is kept, because
it is exactly the kind of gap a future model would otherwise learn from. *A revision
shortens the past; it never edits it.*

**The revision event records what was chosen, not what it replaced.** The superseded option
and the discarded answers are already on the stream in the events before it; recording them
again would be the same facts in two places and so two places for them to disagree.

**One route, one request shape.** A revision is `POST /answers` with a `question_id` the
run has already answered — the client is never asked to know which of the two it is doing,
because the *server* is the only party that knows what the transcript holds.

**Re-selecting the option already recorded records nothing** and returns the current step.
This is one rule serving two situations: a response lost in flight and retried, and a
player who changed their mind and changed it back. It also subsumes the narrower
just-answered-question replay rule it replaces — a replay is now a replay of any answer,
not only of the most recent one.

**Revising is refused once the Skill rating exists**, with `answer_not_revisable` — a code
distinguishable from the other conflicts, because its recovery is opposite: there is no
question to refetch and re-render, only a rating to show. A Level is proved, never
declared, and the account of a player stops moving when the platform starts relying on it.

**Concurrency is unchanged in mechanism.** A revision is an append with an expected
version, so two devices revising one run at once fail loudly exactly as two simultaneous
answers do today. Deterministic stream ids
([ADR-0019](0019-deterministic-assessment-stream-ids.md)) are untouched.

**Answer carry-forward is deliberately not built.** Re-applying answers wherever the engine
asks the same question id again is semantically exact — a question id determines its tier,
and `finalize` is order-independent — but it turns the transcript from a *prefix* into a
*merge*, and appends answers the player did not give at that moment. It remains available
later as a backend-only change with no wire impact.

## Consequences

**Easier**

- A mis-tap is correctable, at the only cost that is honest: the answers that genuinely
  depended on it.
- The rating a revising player leaves with is, to the digit, the rating that transcript
  always would have produced — by construction rather than by measurement. One test at the
  HTTP seam states it: two players reach one transcript, one straight through and one by
  revising, and their ratings are identical in every field that is not an identifier or a
  timestamp. **That test must never be deleted.**
- *How much did this player revise, and from what* becomes answerable from stored history,
  for the integrity engine and for a support agent asked why a player has this Level.
- Nothing in the engine has to be re-baselined, so no golden persona moves and no existing
  rating changes value.

**Harder**

- **The transcript is now a projection with a rule, not a concatenation.** Replaying an
  assessment means knowing that `AnswerRevised` truncates. Anything that reads the stream
  directly — the training projection, most of all — has to apply the same rule, or it will
  learn from answers the engine never consumed.
- **A response can now describe *less* progress than the one before it.** A client that
  remembers what it last drew, rather than reading the served transcript, will be wrong in
  the one direction it cannot detect by counting.
- The question selection stays on the server, so every change costs a round trip. Moving
  over *answered* questions costs nothing, because the transcript is served alongside the
  step — but that is a payload that grows with progress. The bank is nine questions per
  Sport, so it is bounded and small.
- **A stopped-but-not-completed run can sit indefinitely**, which makes abandoned-assessment
  expiry — already identified and undecided — slightly more pressing.

**Neutral**

- The step-response invariant weakens from *exactly one* of question/result to *at most
  one*, with both absent meaning stopped and ready to finalise. Additive on the wire: no
  field moves, is renamed or is removed.
- Re-rating a Sport stays refused as it is today, and whether a second assessment should
  **replace** a rating stays open and stays the match-update engine's question.
- One honest wart is retired rather than inherited. The original design accepted that the
  confirm control's label could never change, because the engine decides only after an
  answer arrives. With the commitment moved off the last question, the identical label is
  now simply correct rather than a compromise.
