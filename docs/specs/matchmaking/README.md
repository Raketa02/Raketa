# Matchmaking source documents

The two documents the matchmaking map is argued against, landed here **verbatim** so a
ticket can cite `§9.3.4` or *the Build the four screen* and a fresh session can resolve it.

They are **input material, not accepted design.** Nothing in either file is decided
because it appears in either file. What is decided lives in ADRs, in the root
[`CONTEXT.md`](../../../CONTEXT.md), and in the spec set this map produces beside them.

Charted by [The matchmaking engine: who sits down, and why](https://github.com/Raketa02/Raketa/issues/155);
landed by [Land the matchmaking input documents in the repo](https://github.com/Raketa02/Raketa/issues/156)
on 2026-08-26.

| File | What it is | What it is worth |
| --- | --- | --- |
| [`matchmaking-engine.md`](matchmaking-engine.md) | A 2392-line design document: architecture, algorithm, operations | **Its structure is accepted; its numbers are not.** |
| [`social-prototype-v1.html`](social-prototype-v1.html) | A single-file working prototype, 4990 lines, no build step — open it in a browser | **The only artefact that shows what the screens actually do.** |

## The three rules for reading them

**1. Where either document conflicts with an ADR, the ADR wins.** Without exception, and
without a discussion. The conflict table below records each one as it is found.

**2. Structure accepted, numbers open.** The document's shape — the stages, the eight
terms, gates before scoring, evidence as codes, weights as versioned configuration — is
the frame the map works inside. Every *constant* in it is an admitted hypothesis, and so
is every one of the eighteen product questions in its §23. The document says this about
itself in §24; take it at its word.

**3. The document wins on algorithm; the prototype wins on surface.** Where the document
corrects the prototype's maths, the document is right — it was written to. Where the
prototype has a screen behaviour the document never addresses, **the behaviour survives**
and gets specced, rather than being deleted by the document's silence. The six known
disagreements are worked in
[The six places the prototype and the design document disagree](https://github.com/Raketa02/Raketa/issues/164).

## Do not edit either file

An input document that has been tidied is no longer the thing the decisions were argued
against, and every citation into it becomes a guess. Both files are byte-identical to
their sources and must stay that way — including the typos, the stale claims, and the
numbering quirks catalogued below.

Corrections go in an ADR, or in the conflict table here. **Never in the source.**

```
158af79d0d518504961fb2efa6893f8f8012fcdcdd7fe29512c1c01e1c98875b  matchmaking-engine.md
f50cf0fa7b9efc4c3e5983a43538cc62f900c0d573bf327086515df53d39f9cc  social-prototype-v1.html
```

Imported once, from one developer's Desktop. **This repo is now their only home** — there
is no upstream to re-sync from.

## Conflicts with an accepted ADR

<!-- one row per conflict found while working the map; the ADR wins in every one -->

| § | What the document says | What the rule says | How it is resolved |
| --- | --- | --- | --- |
| §4 | The matcher is a separate deployable written in Go at `matcher/`, reached over internal HTTP | Apps in this repo are independently deployable and the boundary is HTTP; and a computation engine is a pure layer, **never** a microservice — *"a pure function behind a network call has no state to own and no independent lifecycle"* | **The rules win.** [ADR-0093](../../adr/0093-matcher-in-the-backend-with-a-pure-match-fit-engine.md) puts the matcher in the backend: the pure scorer at `app/engines/matchfit/`, the index and ledgers at `app/modules/matchmaking/`. The document's counter — *the matcher is not a pure function* — is accepted, and answered by the split rather than by a fourth app. **§15 and §16 are discarded; §9 transfers unchanged**, exactly as §4.4 says it would |
| §11 | The weights are configuration, hot-reloaded at runtime from a config store | A number that is an admitted hypothesis lives with the engine version that uses it, frozen, and hashed into that version's output — *term weights* are the named example | **Both, at two levels.** [ADR-0093](../../adr/0093-matcher-in-the-backend-with-a-pure-match-fit-engine.md): the **engine version** stamps how the maths works, the **ruleset version** stamps what the numbers were. A ruleset is a named, dated, frozen dataset, immutable once released, embedded with the code today. The runtime store is deferred; when it lands it changes only where the file is read from, never what the stamp guarantees |
| §11 | A ruleset may be overridden at runtime per deployment | The environment may select configuration defaults; it may **never** select behaviour a domain test could observe | **The rule wins.** A weight is the product's opinion about who a player should meet — behaviour, not a setting. All four environments run the same numbers unless a differently-named ruleset is deliberately released |

---

## Navigating `matchmaking-engine.md`

26 numbered top-level sections. Citations are by section number — `§9.3.4`, `§14.5` —
and they are stable, because the file does not change.

**Four numbering quirks a citing ticket will trip over:**

- **Stage numbers and section numbers diverge inside §9.** §9.1 is Stage 1, §9.2 Stage 2,
  §9.3 Stage 3, §9.4 Stage 4 — and then **§9.5 is "Stage 6"** and §9.6 is "Stage 7".
  **There is no Stage 5 anywhere in the document.** Cite the section number; mention the
  stage name only when quoting the heading.
- **§9.4's two subsections are unnumbered.** The modifiers are *"Familiarity, and the sign
  flip the current design gets backwards"* and *"Calibration value"* — there is no
  `9.4.1`. Cite them as `§9.4 (Familiarity)` and `§9.4 (Calibration value)`.
- **§22's phases are unnumbered too** — *Phase 0 — Decide*, *Phase 1*, *Phase 2*,
  *Phase 3*, then *Rollout, for every phase*. Cite as `§22 Phase 1`.
- **§23's eighteen questions are numbered 1–18 in a table, and 15–18 are bolded.** The
  bold marks the four the design document surfaced itself; 1–14 came from the earlier
  mechanics document. Cite as `§23 Q7`.

The sections a ticket is most likely to want:

| Want | Section |
| --- | --- |
| Where the engine lives, and the two ADR tensions | §4, and §4.3 for the tensions argued |
| The ~13 new domain terms | §5 |
| Play intent | §6, and §6.2 for what the backend must add |
| The candidate index — the privacy line as a schema fact | §7.2 |
| The eight Fit terms | §9.3, one `§9.3.n` per term |
| The modifiers | §9.4 |
| Liveness, and *Let's play* | §9.5 |
| Relaxation ladder and the quality floor | §9.7, §9.8 |
| Doubles as a group objective | §9.9 |
| The deck | §9.11 |
| Graceful term degradation | §10 |
| Rulesets — weights as configuration | §11 |
| Explainability: reason codes, never sentences | §12, and §12.1 for the wire rule |
| Fairness, exposure, load, the sweeper | §14 |
| The internal contract | §16 |
| Scale and SLOs | §17 |
| Telemetry | §19.2 |
| The eighteen open product questions | §23 |
| Every constant, with what would falsify it | §24 |

## Navigating `social-prototype-v1.html`

One self-contained file: CSS at lines 13–349, markup at 351, then a single `<script>` at
388–4988 holding all state, data and views. Open it in a browser to click through it —
there is nothing to install.

**How to find a screen.** Every screen is a function on the `V` object (declared at
line 2057) returning a string of HTML; `go(view, params)` at line 2019 pushes onto a
navigation stack and `render()` at line 3928 dispatches. To read a screen, read its
`V.<name>` function.

The **Play** screens the map cares about:

| Screen | Function | Line |
| --- | --- | --- |
| Play — the entry screen | `V.mm` | 2391 |
| The search sheet | `V.mmsearch` | 2434 |
| The deck — one at a time | `V.deck` | 2521 |
| Build the four — the seated line-up | `V.four` | 2610 |
| Pick players myself — the ranked list | `V.pickpool` | 2734 |

**How to find the maths.** The scorer is **`compat(pid, sport, mode)`** at line 1309 —
the prototype's whole ranking function, seven weighted terms against the design
document's eight. Its weights are `MM_W` at line 1264, one set for `comp` and one for
`fun`. The rest of the engine is the fifty lines either side of it:

| Piece | Function | Line |
| --- | --- | --- |
| The weights, `comp` and `fun` | `MM_W` | 1264 |
| Availability overlap, and the shared slots it found | `availOverlap`, `sharedSlots` | 1266, 1272 |
| Predicted balance for a pair | `pairBalance` | 1277 |
| Vibe-tag overlap | `vibeOverlap` | 1282 |
| The rough window a challenge carries | `avWindow` | 1300 |
| **The scorer** | `compat` | 1309 |
| The *Let's play* lift on the ranked order | `WAVE_LIFT`, `rankScore` | 1352, 1353 |
| Candidate generation | `mmPool` | 1354 |
| Team strength, best pairing, the four's forecast | `teamStrength`, `bestPairing`, `fourForecast` | 1363, 1364, 1373 |

Other landmarks: `SPORTS` at 398, the vibe `TAGS` at 414, and `PLAYERS` at 431–490 —
**fourteen seeded players**, of which `POOL` (line 491) is the thirteen who are not `me`.

Everything past the Play screens — `V.around`, `V.gathnew`, `V.meetup`, `V.cases`,
`V.states`, the court and money screens — is the social and matches half, **ruled out of
scope** on the map. It is here because the file is one file, not because it is in play.
