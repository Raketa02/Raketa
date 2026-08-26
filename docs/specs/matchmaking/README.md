# Matchmaking source documents

The two documents the matchmaking map is argued against, landed here **verbatim** so a
ticket can cite `§9.3.4` or *the Build the four screen* and a fresh session can resolve it.

They are **input material, not accepted design.** Nothing in either file is decided
because it appears in either file. What is decided lives in ADRs, in the root
[`CONTEXT.md`](../../../CONTEXT.md), and in the spec set this map produces beside them —
today [`consumer-driven-contracts.md`](consumer-driven-contracts.md), which records what the
matcher demands of `player_score`, `matches` and `cases`.

Charted by [The matchmaking engine: who sits down, and why](https://github.com/Raketa02/Raketa/issues/155);
landed by [Land the matchmaking input documents in the repo](https://github.com/Raketa02/Raketa/issues/156)
on 2026-08-26.

| File | What it is | What it is worth |
| --- | --- | --- |
| [`matchmaking-engine.md`](matchmaking-engine.md) | A 2392-line design document: architecture, algorithm, operations | **Its structure is accepted; its numbers are not.** |
| [`social-prototype-v1.html`](social-prototype-v1.html) | A single-file working prototype, 4990 lines, no build step — open it in a browser | **The only artefact that shows what the screens actually do.** |

## The three rules for reading them

**1. Where either document conflicts with an ADR, the ADR wins — by default.** The conflict
table below records each one as it is found. The default is rebuttable and rarely rebutted: a
document overturns an ADR only on an argued case that its way produces **materially better
matchmaking or more value for the player**, never on preference or on the document having said
it first. Winning that argument does not bend the ADR quietly — it **amends** it, in a new
record that says so. Absent the argument, the ADR stands and the discussion is over.

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
| §23 Q8 · §7.2 | A gender or format preference is supported **only as a format declaration attached to a game** — *mixed doubles*, *women's doubles* — and **never as a browse filter over individuals**; and the candidate index holds no gender field, because *"the fields do not exist"* | The product owner rules that a player may say who they want to play with, out of the box | **The document loses, under rule 1's rebuttal.** [ADR-0096](../../adr/0096-gender-preference-mutual-gate-invisible-to-the-scorer.md): a **Gender preference** over people, made **mutual** so it protects an inbox and not only a search. §23 Q8's middle path is unavailable here — the surface that would make it honest (joining a game somebody else built) is out of scope on this map, so inside scope it is the same mechanism under a better name. §7.2 is **amended, not deleted**: the value reaches gating and is absent from the scorer's input type, so its sentence — *a term cannot read a protected characteristic because the value is not in the process* — stays literally true, and its schema test moves to `app/engines/matchfit/`. `kernel/sports.py`'s refusal of a `Format` dimension is left undisturbed, and *mixed doubles* would have breached it |
| §6.2 · §23 Q16 | Play intent is a `Mapping[Sport, PlayIntent]` field on `PlayerProfile` — *"the first per-sport fact on an aggregate that is deliberately not per sport"* | `PlayerProfile` is the first aggregate in the domain **without** a sport dimension, and ADR-0089 argued for that property rather than conceding it | **The rule wins.** [ADR-0094](../../adr/0094-play-intent-declared-per-sport-in-its-own-aggregate.md) puts it in its own aggregate, `PlayIntentDeclaration`, one stream per `(player, sport)`. The document did not see the ordering constraint that decides it: a profile does not exist until part 2's commit, so a profile field could only ever be asked once, for the sports rated that day. **§6.1, §6.3, §6.4 and §6.5 transfer unchanged**, and §6.2's durable event name is kept exactly as proposed |
| §7.2 · §9.3.4 | The six Player Score strands reach the matcher as bare values — `strand_shows_up uint8 \| null` and five siblings on the candidate row — and *"until the `player_score` context lands, every strand is `null`"* | A demand that is not written down is satisfiable by accident, and a fact whose absence is indistinguishable from a bad value cannot carry the rule *no record is not a bad record* | **The document is amended, not overruled.** [ADR-0098](../../adr/0098-matcher-demands-as-executable-contracts.md): every strand crosses as **value + numerator + denominator + the moment of the most recent observation**, and opponent variety as a seventh published statistic that is not a strand. The bare value cannot distinguish one no-show out of one game from thirty-five of thirty-eight, and makes the absence rule a matter of trusting somebody else's `null` discipline. §9.3.4's decomposition argument and §10's `NoEvidence` renormalisation transfer **unchanged** — this widens what crosses the wire, not what the term does with it. §7.2's per-player row is otherwise untouched: the strands stay on it |
| §7.2 · §7.1 · prototype `:3376` | The candidate index is one row per `(player, sport)`, and §7.1 lists *"History together — games played, when, how they went, previous declines and accepts"* as a signal without ever saying where it lives. The prototype computes *settles up* from a **live open case** (`0.15` while a share is unsettled) | The index row is per player, so it has nowhere to hold a fact about a **pair**; and a safety gate is verified against live state on the side that owns the truth, while a term is weighed | **The rules win, on a gap the document left open.** [ADR-0098](../../adr/0098-matcher-demands-as-executable-contracts.md) carries [ADR-0095](../../adr/0095-block-directed-record-symmetric-effect-gates-fail-closed.md)'s answer for blocks across to history: **the searcher's own pairwise set travels in the `SearchContext`, bounded at 500 counterparts plus every open challenge, and the index holds none of it** — only the per-player open-challenge count §7.2 already has. And *settles up* is **the historical record, never the live case**: the open case is the Hold and does its work at the gate, so the matcher never reads `cases` to score |
| §9.8 · §9.7 | The relaxation ladder has four rungs — familiarity, distance, availability, level — applied one at a time by the engine and announced afterwards, and `MAX_RELAXATION_RUNG = 4` | A term that cannot be evaluated stands down; a term may **never** be honestly neutral, the test being whether a zero would be *measured* or *invented*; and the environment may never select behaviour a domain test could observe | **The rules win.** [ADR-0099](../../adr/0099-relaxation-offers-the-searchers-own-asks.md): candidate generation is `shard ∧ sport ∧ box ∧ gates`, so familiarity (a modifier), availability overlap (a term) and level fit (a term) exclude nobody. Rungs 1, 3 and 4 raise scores against a fixed floor instead of widening the catchment — the Wikimedia move — and rung 3 converts a **measured** zero into `NoEvidence`. **Rungs 1, 3 and 4 are struck.** The ladder becomes three rungs over the searcher's *own asks* — times, radius ×1.5, radius ×2.0 — **offered rather than applied**, since only the player can widen their grid truthfully. The stopping rung stays a number for [#167](https://github.com/Raketa02/Raketa/issues/167) |
| §9.2 · §9.7 | *Guaranteed inclusions* — interest-lifted, newcomer-window and zero-exposure candidates — **bypass the fit cut**; and §9.7 says that below `QUALITY_FLOOR` a candidate is *"not shown at all"* | Both cannot be true at once | **§9.7 wins, with one carve-out.** [ADR-0099](../../adr/0099-relaxation-offers-the-searchers-own-asks.md): an **interest lift is a human's own yes** and outranks the engine's opinion, so it may sit below the floor with its reason printed. The newcomer-window and zero-exposure lifts may **reorder** but never **admit** below the floor — exposure fairness is not a reason to show somebody a bad evening |
| §9.8 | The empty response carries a `pool_description` string — *"Four padel players within 8 km this week"* | The kernel *"emits values and stable machine codes, never display text"*, and the map extends it to the matcher unchanged | **The rule wins.** [ADR-0099](../../adr/0099-relaxation-offers-the-searchers-own-asks.md): `{sport, radius_km_used, players_in_range, window, post_gate: true}` plus reason codes, and the client writes the sentence. The count is always **post-gate** and no pre-gate count is ever carried, because [ADR-0096](../../adr/0096-gender-preference-mutual-gate-invisible-to-the-scorer.md)'s ninth gate makes the two differ per searcher and the delta would be readable — which a block must never be |

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

**And one place the arithmetic does not agree with itself.** Found while resolving
[#161](https://github.com/Raketa02/Raketa/issues/161), and verified against the source: the
index sizing is stated three incompatible ways, so a ticket quoting "the document's number"
has to say *which* one.

- **§7.2** says *"approximately 160 bytes per row"* and *"a city of 50 000 players across four
  sports is roughly 32 MB"*. That arithmetic needs **4 rows per player**.
- **§17's capacity table** says *"candidate rows (player × sport) ~2.5 × players"* — which at
  160 bytes is **20 MB**, not the 32 MB the same table then repeats.
- **§17's sharding note** says *"10⁶ rows per instance (~200 MB)"*, which is **200 bytes a
  row**, not 160.

None of the three is authoritative and the discrepancy is not the interesting part: the
measured figure is **782 bytes a row as plain Python objects**, and it is held once per
worker. See [`docs/research/matcher-scale-in-python.md`](../../research/matcher-scale-in-python.md)
and [ADR-0093's trigger 4](../../adr/0093-matcher-in-the-backend-with-a-pure-match-fit-engine.md),
which [#165](https://github.com/Raketa02/Raketa/issues/165) restates in rows.

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
