# ADR-0036 — A UI document is final on the screen, never on the arithmetic

- **Status:** Accepted
- **Date:** 2026-08-19

## Context

Two of the documents in `docs/specs/now/` are declared **final**: `README.md` L15–19 makes
`rakieta-now-section-ui-spec.md` and `1-now_screen_production_spec.md` *"final on every value
they state"*, and `now-section-domain-spec.md` §A.0 breaks ties only among the rest. That rule
was written for pixels, and it worked for pixels.

It does not survive contact with `1-now_screen_production_spec.md` §5.2, because that section
is not about the screen. It specifies **how Match Fit is computed** — seven weighted terms
summing to 100, three modifiers applied after the weighted sum, and a final clamp to 20–99 —
inside a document the README makes final. And the engine that shipped computes it from **ten**
terms, applies **no** modifiers and **no** clamp, having been rebuilt deliberately by
[ADR-0027](0027-fit-and-certainty-are-separate-ranking-is-policy.md) to remove a defect the
seven-term model provably had: an empty match scored **90,5** where a well-formed one scored
**84**, so the list would have been topped by matches nobody had joined.

Read literally, the authority rule says the superseded model wins, because it is written in a
final document. `now-section-domain-spec.md` knows this is wrong and cannot fix it: it flags
the supersession `[SUPERSEDED-A1]` five times and still rules the seven-term model normative
*within itself* (`now-section-domain-spec.md` L20). Doc 5's finding A1 names the collision and
stops there, because a review of documents cannot settle which document governs.

What made the answer decidable was measurement rather than argument. `Raketa02/Raketa#6`
executed the shipped engine ~215 000 times and found the defect ADR-0027 was accepted to
remove is **gone from the arithmetic**: fit and coverage are positively correlated
(r = **+0,445**), and an empty court averages **63,0** against a full one's **76,4**. The
specified model is not merely older than the built one; it is the one with the bug.

The alternatives considered:

- **Honour the letter of the authority rule** and rebuild the seven-term model. Reintroduces a
  measured defect on the strength of a filing convention, and discards ~215 000 measurements
  and 757 tests in favour of prose describing a browser prototype.
- **Rewrite the two final documents in place** so the conflict disappears. Destroys the
  citation graph the set depends on — 27 bare-filename cross-references and 486 `[SRC: line N]`
  citations, the latter already build-specific and fragile — and makes a document that was
  reviewed unreviewable, because nobody can see what changed.
- **Treat every collision case by case.** What has happened so far, and it does not scale: four
  further tickets on this map hit the same collision, and re-deciding the authority question
  each time invites four different answers.
- **Draw the boundary inside the authority rule**, by subject rather than by document.

## Decision

We will hold that **a document's finality is bounded by its subject, not by its filename.**

- The two UI documents remain **final on the screen**: geometry, type, colour, tone, copy,
  what is shown, what is hidden, what a threshold changes. On those values they are not merely
  authoritative — they are the only source, and a native equivalent may be substituted only
  where React Native has none for what v37 states.
- They are **not final on how a number is computed.** Where a final document specifies a model,
  a formula, a weight table or a threshold *inside the engines layer*, and shipped engine code
  disagrees, **the code is the fixed point and the document is amended to it.**
- The amendment is recorded as a **spec delta** under `docs/specs/now/deltas/`, never by editing
  the document. The set's files are immutable for the same reason ADRs are: the reason a past
  version looked right is itself information, and 486 line citations resolve against the bytes.
- **Reopening a shipped engine's constants is a separate decision with its own evidence.** A
  product argument that lost its home when the engine was rebuilt does not win by being older;
  it must be re-homed on its own merits, and the ranking layer is usually where it belongs.
- **The code wins because it is measured, not because it is code.** An engine with no
  falsifying measurement behind a constant has no claim over a document; what settles a
  collision is evidence, and `ADR-0015`'s requirement that every engine constant carry its own
  falsifying measurement is what makes the engines the side that usually has it.

The boundary is not a licence to overrule the screen. Applied to the collision that motivated
this record, **not one value either UI document states was overturned**: the 20–99 range was
kept and relocated from the model to the display, the badge's omission for an unrated viewer
was kept and its key corrected, the two-band rule and the geometry were untouched, and the one
value that did change — the coral trigger — was listed as undecided in the UI document's own
open-decisions table.

## Consequences

**Easier**

- The remaining tickets on this map inherit a decided question. A collision between a landed
  specification and a shipped engine now has a default outcome, and arguing it again requires
  new evidence rather than a re-reading.
- The specification set stops being self-contradictory without being edited. Its finality
  survives where it was earned, and the citation graph survives entirely.
- A spec delta directory makes the drift **legible**: what the documents say, what the code
  does, and which one governs, in one place a reader can diff.

**Harder**

- **This privileges whichever artefact was built first**, and that is a real hazard rather than
  a neutral one. A future engine built ahead of its specification acquires authority it may not
  deserve, and the only guard is the requirement that its constants carry measurements.
- **A specification can no longer drive an engine change on its own authority.** Wanting the
  model to be different is now a request to reopen the engine, with its own evidence and its
  own record — slower by design, and it will feel like obstruction the first time product
  judgement is right and the code is merely earlier.
- **The boundary needs judgement at the edge.** *"Clamped 20…99"* was a model rule and a display
  rule at the same time, and reading it as one or the other was the whole of the decision. There
  will be more such values, and this record gives a principle rather than a test.
- **Two places to read.** Whoever needs the current model must read the document and then its
  delta, and a delta nobody maintains is worse than no delta, because it will be trusted.

**Neutral**

- Nothing about the engines layer changes. The thirteen decisions taken on
  `Raketa02/Raketa#10` under this rule touch the response shape, the ranking layer and the
  client, and **not one line of `backend/app/engines/`** — including the warning threshold,
  where the code's `0,40` was ratified rather than altered.
- The tie-breaker in `now-section-domain-spec.md` §A.0 is unaffected. It orders the non-final
  documents among themselves and never spoke to this collision.
