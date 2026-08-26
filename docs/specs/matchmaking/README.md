# Matchmaking source documents

The two documents the matchmaking map is argued against, landed here **verbatim** so a
ticket can cite `§9.3.4` or *the Build the four screen* and a fresh session can resolve it.

They are **input material, not accepted design.** Nothing in either file is decided
because it appears in either file. What is decided lives in ADRs, in the root
[`CONTEXT.md`](../../../CONTEXT.md), and in the spec set this map produces beside them —
today [`consumer-driven-contracts.md`](consumer-driven-contracts.md), which records what the
matcher demands of `player_score`, `matches` and `cases` — and, since
[#164](https://github.com/Raketa02/Raketa/issues/164), of `rating` — and
[`scale-posture.md`](scale-posture.md), which records what the engine is designed for, the
measured cost of a search in CPython, and the ladder that is climbed before ADR-0093 is
reversed, and [`ranking-weights.md`](ranking-weights.md), which fixes every number that reorders
a list and what would prove each of them wrong, and [`the-five-numbers.md`](the-five-numbers.md)
and [`search-telemetry.md`](search-telemetry.md) — the numbers that decide whether the product
says nothing at all, and the record that is the only thing able to prove any of them wrong.

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
| §9.2 · §7.2 · §17 | The shard key is *"a shard, not a matching criterion"* — and §9.2's generation predicate then opens with `shard_key == searcher.shard_key`, ANDed with the sport, the box and the gates | An equality inside the generation conjunction **excludes**; and no relaxation rung may widen anything the searcher did not themselves ask for, so nothing reaches it | **The rule wins, against the document's own stated rule.** [ADR-0101](../../adr/0101-partition-derived-never-a-matching-criterion.md): the conjunct is struck and **the box is the only spatial truth**. The partition is *derived* — `(sport)` today, `(sport, cell)` at trigger 4 — so there is no field for a future conjunct to attach to, and no metro boundary that can be wrong about a person. `shard_key` is **not a field**: nothing in this backend produces one, it is derivable from the area for reporting, and a schema test asserts it absent beside §7.2's forbidden name, photo and precise location. §9.2's guaranteed inclusions and everything else in §7.2 transfer |
| §6.4 · §9.5 | A directly opposite intent declaration scores **0.00** on the alignment term **and** takes a further `intent_opposed` modifier of −6 | The same piece of evidence may not move two parts of the score — §6.5 and §9.3.6 each rule it out in this document's own words | **The document loses to itself.** [`the-five-numbers.md`](the-five-numbers.md) deletes the modifier: a candidate who has not declared has the term renormalised away, a candidate who declared the opposite loses its entire weight, so opposition already costs strictly more than silence without a second charge. The modifier existed to *bury* the candidate, which is a gate wearing a modifier's clothes, and [ADR-0094](../../adr/0094-play-intent-declared-per-sport-in-its-own-aggregate.md) settled intent as a weight. The six cells are unchanged |
| §9.3.4 | *"A stack of small positives must never lift somebody over a recent no-show"*, enforced by a flat **−12** outside the ±10 modifier budget | The sentence claims more than the number does: the penalty binds the modifier stack and does nothing against the main score | **The number is derived and the sentence is corrected.** [`the-five-numbers.md`](the-five-numbers.md): the penalty is `MODIFIER_BUDGET + 1` — **11** today, and it moves by itself if the budget does — the smallest value that keeps the stated promise, where 12 had no separate argument. The bar stays a **dock, not an exclusion**: an otherwise superb match still appears, low, with the reason printed, because refusing to show a good match over one missed game is the block's job and not the scorer's. The bar reads the **published** score, not the matcher's per-mode blend — the one deliberate place the matcher reads the blend |
| §7.2 · §9.3.5 · `availability.py` | An empty availability grid is *"no preference … it scores no overlap"* in shipped code, `NoEvidence` in [ADR-0099](../../adr/0099-relaxation-offers-the-searchers-own-asks.md), and *any time suits me* in plain English | A term may never be honestly neutral, the test being whether a zero would be *measured* or *invented* | **The rule wins, and the field becomes required.** [ADR-0102](../../adr/0102-silence-is-never-scored.md): at least one ticked cell at profile commit, and a blank grid met anyway means *we do not know*, so the term stands down. Scoring silence as no overlap invents a zero and charges the quietest player fifteen points for their quietness; scoring it as full overlap makes the blank grid the optimal play. The glossary's *an unanswered field is never a negative filter* is kept by removing the unanswered case |
| §9.7 · §24 | `QUALITY_FLOOR` starts at **52**, with an accountable owner still to be named (§23.10) | A constant that decides whether the product says nothing owes an argument, not a provenance — and it cannot be calibrated against a distribution that does not exist | **Neither adopted nor rejected: 52 is not yet an answer to anything.** [`the-five-numbers.md`](the-five-numbers.md) defines the floor by **six judged pairings** it must satisfy, and hands the constraint to [#168](https://github.com/Raketa02/Raketa/issues/168), which fixes the integer. `MIN_SHORTLIST` rises from 3 to **5**, and its job changes: after [ADR-0099](../../adr/0099-relaxation-offers-the-searchers-own-asks.md) it triggers nothing and instead decides whether the rung offers are computed at all |
| §9.3.6 · §9.3.7 | Playing style **is** the `ON_THE_COURT` group and social vibe **is** `AFTER_THE_MATCH + WHY_YOU_ARE_HERE` — the two terms are split by which group a tag was printed in | A split must be able to classify the things it splits | **The document loses to its own table.** Of the eleven relationships §9.3.6 lists, exactly **one** lies wholly inside `ON_THE_COURT`, four lie wholly inside the other two groups, and **five cross** — including the only clash marked *Real*, `TALKS_THROUGH_THE_MATCH` ↔ `QUIET_AND_FOCUSED`, which is unmistakably about the hour on court while one of its tags is in `AFTER_THE_MATCH`. [`ranking-weights.md`](ranking-weights.md) §1 splits **by relationship**: every matrix entry carries a `column`, a matched single tag falls to its own group's, and a term is *a group of claims about pairs* rather than a group of tags. Both headings are wrong as written and neither is the definition of its term. §23 Q18 is confirmed — product owns the matrix, and the new column too |
| §9.3.6 | `style = clamp(dr(matches) + 0.7·dr(complements) − Σ clash_severity, **0**, 1)` | A term's zero is its worst outcome, never its most common one | **The document repeats, in a term nobody checked, the defect it caught in another.** The clamp at zero makes *"you two clash badly"* numerically identical to *"you two share nothing"*, so the clash arm is invisible whenever there are no matches — which is most comparisons: two random four-tag draws from nineteen overlap **0.84** times on average. This is §9.3.2's own *"wastes the bottom 35 points of the range"* complaint, one term over. [`ranking-weights.md`](ranking-weights.md) §5 normalises over `[−CLASH_CAP, 1]`: no relationship fired → **0.20**, a capped clash → **0.00** |
| §9.7 · §9.3.1 | The quality floor is what stops *"the evening §9.7 exists to prevent"*; the for-fun level curve expresses its floor — *nobody spends the evening watching* — as `LEVEL_TOL_FUN` | A bar over a score cannot discriminate what the score cannot see | **Neither instrument does the job, and the arithmetic proves it.** [`the-five-numbers.md`](the-five-numbers.md)'s judged pairings **fail in for-fun**: case 3 (*two levels above, lopsided*, **not shown**) scores **60.4** against case 2's **52.6** (**shown**). Past `LEVEL_TOL` the level term is pinned at 0 and predicted balance has been pinned at `BALANCE_PCT_MIN` since **Δμ ≈ 0.34**, so the engine cannot tell a 0.9 gap from a 2.5 gap and ranks the mismatch on sociability and geography alone. [ADR-0103](../../adr/0103-where-the-curve-saturates-the-gate-begins.md): a **tenth gate** at `Δμ ≥ LEVEL_TOL_mode` — no new constant, joins the never-relaxed list, and does not resurrect §9.8's struck rung 4 because nobody asks for a level range |
| §9.5 · §9.5.1 | A previous decline between two players docks **−10** and is *"never, under any circumstance, shown to either side"*; and anything Liveness moves more than `MOVE_NOTICE = 6` **must print its dominant reason** | Both cannot be true at once | **The rule is stated and the numbers move.** [`ranking-weights.md`](ranking-weights.md) §9: **a silent movement never exceeds the movement that owes an explanation** — `\|silent movement\| < MOVE_NOTICE`, enforced beside §12.2's two-numbers rule. Previous decline becomes **−6** and the exposure adjustment **−6 … +6**; every other signal already prints, with the challenge-load dock printing a coarse code and never the number |
| §9.3.8 · §9.5.2 | A searcher outside the candidate's ring takes a flat **−8** Liveness dock; and reciprocal fit computes `fit_ba`, the candidate's whole Fit for the searcher | The same piece of evidence may not move two parts of the score — §6.5 and §9.3.6 each rule it out in this document's own words | **The standalone dock is struck.** `fit_ba` already contains the candidate's distance term against the candidate's own radius, so the fact was charged twice — and reciprocal asymmetry prices it *proportionately*, which a flat −8 does not. `outside_their_radius` still prints on the card, as [ADR-0099](../../adr/0099-relaxation-offers-the-searchers-own-asks.md) requires; only the second charge disappears |
| §9.4 | A **Language** modifier, `0 … +2`, for *"a shared language beyond the local default"* | No name, photo, email, date of birth, **nationality** or precise location exists anywhere in the index; and **a protected characteristic may gate, it may never score** | **Struck, not deferred.** It reads a field that exists nowhere in the backend and that no ticket creates, and a shared-language bonus is the nearest available proxy for the nationality the privacy line excludes by name — so [ADR-0096](../../adr/0096-gender-preference-mutual-gate-invisible-to-the-scorer.md)'s rule bites: this *scores*. If it returns it returns as its own decision under that rule, not as a leftover row in a table |
| §24 · §23 Q10 | `QUALITY_FLOOR` starts at **52** | The floor is defined by the six judged pairings it must satisfy | **52 is refuted, and the case that refutes it is named.** With the level gate and the tag normalisation applied, the median stranger — case 5, whose stated job is *"this is where the bar sits"* — scores **46.0** in competitive, so 52 hides them. [`ranking-weights.md`](ranking-weights.md) §10 sets **44**, inside `24.2 < FLOOR ≤ 46.0`. Case 3 is now excluded by the gate rather than the floor and is replaced as the lower bound by **case 3′**, the worst pairing still admitted to scoring; and all six now carry explicit term-value readings, so the floor is re-derivable by machine at every ruleset release |
| §9.9 | `K` — the doubles candidate cap — *"moves; it is a config change, not a rewrite"* | A number that can destroy the latency budget is not configuration | **True in Go, false in Python.** The enumeration is cubic with a flat per-combination cost: K=15 is 2.08 ms, **K=32 is 20 ms**, K=48 is 69 ms, K=64 is 169 ms. [`scale-posture.md`](scale-posture.md) sets **`K = 24`** — 27% of the 90 ms line-up budget once derated — as a ruleset constant with an **engine-side ceiling that refuses to load a ruleset exceeding it**, on §11's own malformed-ruleset rule. Everything else in §9.9 transfers |
| §8.3 · §14.1 · §15.3 · §19.2 | The stored search result lives in Redis at `search:{id}` under a **30-minute TTL**, listed among the mutable ledgers; and §19.2 separately requires a `search_candidate` table holding the same Fit, the same terms and the same contributions | One number may not have two homes free to disagree — §8.3's own rule is that *Why 78?* must read the stored result and never recompute, *"in a product whose one promise is that its numbers are checkable"* | **The document loses to itself, once [ADR-0093](../../adr/0093-matcher-in-the-backend-with-a-pure-match-fit-engine.md) removed the architecture that justified the split.** [ADR-0104](../../adr/0104-the-search-record-is-the-answer-and-never-expires.md): **one store**, two append-only tables in `modules/matchmaking/`, and *Why 78?* is a primary-key lookup on the row the request just wrote. `search:{id}` is deleted; the 30-minute TTL was the disagreement, scheduled. The record is **durable and unexpiring**, and a search whose record cannot be written is **not returned** — the `search_id` is the response's own identity, not an analytics field. Nothing in this repository has ever opened a Redis connection: `redis` is a pin and a Compose container and no client, no port, no adapter |
| §19.2 | Three tables — the third, `search_outcome_link`, holds the `search_id` and position a challenge was sent from | The **Origin key** is already glossed as *carried by the challenge itself, required, never optional*; and `matches` does not exist, so today the terminal record is an interest declaration | **Two tables, not three.** [ADR-0104](../../adr/0104-the-search-record-is-the-answer-and-never-expires.md) and [`search-telemetry.md`](search-telemetry.md) §4: the origin key is two columns on the record that expresses interest. The link is 1:1, a table buys a join for nothing, and when `matches` lands the chain is `match ← interest ← search` — still foreign keys, still no third table. An interest citing an unknown or foreign `search_id` is **refused, never linked as null**: a silently-dropped link is a denominator that lies |
| §19.2 · §7 of [`the-five-numbers.md`](the-five-numbers.md) | Record the shortlist; and separately, record the evidence basis and the reliability-penalty outcome **per scored candidate** — ~500 a search | Recording every scored candidate is 25× the volume and a durable record of who was excluded for whom | **Neither, and the third answer is better than both.** [`search-telemetry.md`](search-telemetry.md) §1: **three layers** — per-search counters by reason, the returned rows in full, and a **near-miss band** of the best `NEAR_MISS_RECORDED = 10` that did not clear. Both per-scored-candidate demands are about interpreting a Fit that was *kept* or explaining a candidate who *just missed*; the band contains the best-withheld candidate — §7's *"entire falsifier"* — by construction. The band is **engine-internal and never returned to anybody**, on the line §21 already draws around passes and declines |
| §13 | *"No map-iteration order dependence. Go randomises map iteration; every ordered traversal goes through a sorted slice"* | Python dicts have been insertion-ordered since 3.7 | **The rule guards the wrong collection, and by naming maps hides sets.** [ADR-0105](../../adr/0105-determinism-is-a-set-iteration-problem-in-python.md): `str` hashing is seeded per interpreter, so a set of ids reorders **between** processes and never **within** one — measured on this interpreter — which is every test green and two gunicorn workers disagreeing about a shortlist. A set is never the source of an order; enforcement is two subprocesses with different `PYTHONHASHSEED` values, and the seed is **never pinned**, because [ADR-0028](../../adr/0028-four-environment-model-and-typed-configuration.md) refuses an environment variable that selects behaviour a domain test can observe. §13's four promises are all kept |
| §9.1 · §1.1 | `SearchContext` carries `surface: HUMAN_INITIATED \| ENGINE_INITIATED` to gate the proposals opt-in; §1.1 uses **surface** for the four things a search can be, and is titled *"Two surfaces"* while listing four | One word, two meanings, and the two are orthogonal | **Two columns and one rename.** [`search-telemetry.md`](search-telemetry.md) §2: **Surface** keeps §1.1's meaning — shortlist, line-up, deck, completing a half-built game — and the gate's field becomes **initiation**, which is what its own values say. An engine-pushed deck card is `DECK` + `ENGINE`; collapsing them would either break the consent promise or empty the pool. `mode` is `NULL` exactly for the deck, which has none and reads declared Play intent instead |
| §18 · §8.1 | The backend **circuit-breaks after 800 ms** on a matcher that is unreachable or timing out and returns an `Unavailable` reason; and with Redis down, *Why 78?* *"recomputes with a stated caveat"* | [ADR-0093](../../adr/0093-matcher-in-the-backend-with-a-pure-match-fit-engine.md) put the matcher in the same process, so there is nothing to be unreachable from; and [ADR-0104](../../adr/0104-the-search-record-is-the-answer-and-never-expires.md) makes §8.3's own rule absolute — the breakdown reads the stored result and **never** recomputes | **Both halves fall with the architecture that produced them.** [`the-two-contracts.md`](the-two-contracts.md) §8: the matcher raises, it does not time out, and the failure table becomes structured codes on the backend's existing error envelope — `matchmaking_unavailable`, `gate_data_unavailable`, `index_too_stale`, `search_not_recorded` — distinct codes at one status, because a client must tell a transient outage from a refusal about *you*. *Why 78?* has no recompute path at all: there is no Redis to lose, the record is durable and unexpiring, and a caveated recomputation is the disagreement §8.3 calls fatal, merely labelled. §18's two convictions transfer untouched — **never a fallback list**, and **no fabricated confidence** — and its Redis row survives only as *exposure and suppression fail soft*, stated beside the fail-closed reads rather than left to be inferred |
| §8.1 · §8.2 | The response's honesty fields include *"the pool counts at each stage"*, and §8.1's request body carries `meetup_id?` | The count is **always post-gate** and no pre-gate count is ever carried, because the ninth gate makes the two differ per searcher and the delta would be readable; and meetups are the prototype's social half, ruled out of scope | **[ADR-0099](../../adr/0099-relaxation-offers-the-searchers-own-asks.md) wins over the ticket that asked for more.** [`the-two-contracts.md`](the-two-contracts.md) §3: `n_generated`, `excluded_by_gate`, `n_scored` and `n_cleared_floor` stay on the telemetry row where an analyst reads them, and the client receives exactly one number — `players_in_range`, post-gate. A readable pre-gate delta would tell a searcher how many people a mutual gate hid from them, which is precisely what [ADR-0096](../../adr/0096-gender-preference-mutual-gate-invisible-to-the-scorer.md) forbids. `meetup_id` is dropped from the request |
| §21 | *"A player's rows are deleted from the index and the ledgers on the backend's erasure event"* | There is no erasure event, no account deletion, and no code path in `app/` that removes a player | **The promise has nothing to listen to, and [ADR-0104](../../adr/0104-the-search-record-is-the-answer-and-never-expires.md) makes it load-bearing** by keeping every row forever. Written down as a demand in [ADR-0098](../../adr/0098-matcher-demands-as-executable-contracts.md)'s shape: erasure deletes a player's `search` rows **and** their `search_candidate` rows **in both roles**, as searcher and as recorded candidate, and the denominator loses them. Choosing to keep rows forever is what creates the obligation, so it cannot also be left to memory. Pseudonymising at write time was rejected: a mapping table that is itself the personal data, plus broken joins to every other context |

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
worker. See [`docs/research/matcher-scale-in-python.md`](../../research/matcher-scale-in-python.md).
[ADR-0101](../../adr/0101-partition-derived-never-a-matching-criterion.md) has since restated
ADR-0093's trigger 4 in **rows and workers**, and
[`scale-posture.md`](scale-posture.md) carries the measured table — so quote neither §7.2 nor
§17 for a size, and **write every threshold in rows, never in players**.

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
