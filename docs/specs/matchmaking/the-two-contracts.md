# The two contracts

**What the backend serves the client, and what the backend hands the matcher.**

Produced by [The two contracts: client to backend, backend to matcher](https://github.com/Raketa02/Raketa/issues/170)
on the map [The matchmaking engine: who sits down, and why](https://github.com/Raketa02/Raketa/issues/155).

**The decision lives in an ADR; this file is the shape to check work against.** The evidence
vocabulary, the two spellings of absence and the configuration/contract line are
[ADR-0106](../../adr/0106-evidence-vocabulary-is-contract-weights-are-configuration.md).

> **This is a shape, not a schema.** Field names are the commitment; Pydantic models,
> validators and OpenAPI descriptions are the build's. Nothing here is code and no snippet
> below should be pasted into `app/`.

---

## 0. Where the boundaries actually are

[ADR-0093](../../adr/0093-matcher-in-the-backend-with-a-pure-match-fit-engine.md) discarded
§15 and §16, so *"backend to matcher"* is no longer HTTP and there is no internal service
contract to write. There are **two Python boundaries and one HTTP one**:

| Boundary | Between | Carries |
| --- | --- | --- |
| **Public** | `frontend_player/` → backend | HTTP, `openapi.player.json`, generated client types (ADR-0006) |
| **Module** | API layer → `app/modules/matchmaking/` | A use case. Application types, all the I/O |
| **Engine** | `modules/matchmaking/` → `app/engines/matchfit/` | A pure call. **The privacy fence** |

**The fence is the package boundary, with no exceptions in it.** Gating and candidate
generation live in the *module*, where the I/O is — blocks, holds, the box, the searcher's
radius, [ADR-0096](../../adr/0096-gender-preference-mutual-gate-invisible-to-the-scorer.md)'s
ninth gate, [ADR-0103](../../adr/0103-where-the-curve-saturates-the-gate-begins.md)'s tenth.
`matchfit` receives an already-gated, already-fenced set and does scoring, modifiers, liveness,
the floor, ranking, group optimisation and arrangement.

The alternative — splitting gates by kind, *identity* gates outside and *arithmetic* gates
inside — was rejected. "Arithmetic gate" is not a category anyone can defend in review, and a
fence with a judgement call in it is not a fence. ADR-0103's level gate is the awkward case
and costs one precomputed field on the gated set; that is the whole price of a rule you can
state in one sentence.

A `ScorableCandidate` has **no gender, no name, no photo, no birthdate, no precise location**
and no `shard_key` ([ADR-0101](../../adr/0101-partition-derived-never-a-matching-criterion.md)),
so §7.2's sentence — *a term cannot read a protected characteristic because the value is not
in the process* — stays literally true. Two build-failing assertions at `app/engines/matchfit/`
say so.

---

## 1. The public surface: four routes

Flat resource prefixes, matching every other router in this backend
(`/api/v1/assessments`, `/ratings`, `/players/me`). No `matchmaking/` segment: OpenAPI `tags`
already carry that, and it would be the only context segment in the document.

| Route | Surface | Returns |
| --- | --- | --- |
| `POST /api/v1/searches` | `SHORTLIST` | A ranked shortlist with full breakdowns |
| `POST /api/v1/lineups` | `LINEUP` / `FILL_SEATS` | The pool it seated from, a seated line-up, three arrangements, forecasts |
| `POST /api/v1/deck` | `DECK` | One deal: an ordered batch of cards |
| `GET /api/v1/searches/{id}` | — | Any of the above, read back |

**All three are `POST`s that create a search, and that is honest rather than tidy.**
[ADR-0104](../../adr/0104-the-search-record-is-the-answer-and-never-expires.md) makes every
engine invocation a durable, unexpiring `search` row; a `GET` that writes one would be the
only route in this backend lying about its verb.

**`LINEUP` and `FILL_SEATS` are one route.** They differ by `locked_seats` being non-empty,
which is a property of the request. `search.surface` still records four values
([`search-telemetry.md`](search-telemetry.md) §2), derived at write time.

**The deck is a separate route because it genuinely has no `mode`** — a check constraint, not
a convention — and returns cards rather than a ranked list. Collapsing it into a generic
endpoint would put a nullable field in the contract whose meaning is *"wrong endpoint"*.

**`GET /searches/{id}` returns the same schema the `POST` did.** Not a fuller one, not a
slimmer one — the same. A test asserts a round trip through the record reproduces the
response.

> **Narrowed by [ADR-0109](../../adr/0109-a-read-back-names-what-it-withholds.md).** The
> read-back **re-verifies the fail-closed gates** and withholds a row for somebody who has since
> blocked the searcher — [ADR-0095](../../adr/0095-block-directed-record-symmetric-effect-gates-fail-closed.md)
> reaches every surface that shows one player to another, and a stored search is that surface
> with a longer memory. A withheld row is **stated, never vanished**. So the assertion is: the
> round trip reproduces **the recorded answer plus live gate state**, over the record's *fields*
> — not a byte-identical payload, since the photo URL is re-minted per response by design
> ([ADR-0107](../../adr/0107-the-player-card-is-assembled-outside-the-engine.md)). Both halves
> are asserted. Written down because a test drafted against the whole payload will fail on a
> re-verified row and the temptation will be to loosen it.
>
> **And narrowed again by [ADR-0130](../../adr/0130-a-withheld-row-is-stated-and-the-gate-is-not-named.md).**
> A withheld row is stated and the **gate is not named** — `withheld: BLOCKED` is the trace
> [ADR-0095](../../adr/0095-block-directed-record-symmetric-effect-gates-fail-closed.md) says
> the other side sees nowhere in any response. It is a separate wire shape carrying one field,
> so a withheld row has no id and no card to render.

**Three more routes exist, added by [#171](https://github.com/Raketa02/Raketa/issues/171)** and
specified in [`the-play-screens.md`](the-play-screens.md): `POST /forecasts`
([ADR-0108](../../adr/0108-a-forecast-is-a-route-not-a-search.md) — deliberately records
nothing), `POST /passes`, and `GET /interest`. A fourth was added by
[#237](https://github.com/Raketa02/Raketa/issues/237): `POST /prompt-declines`, write-only and
with no Origin key, which answers *not now* to a prompt and writes no value anywhere. The four
above are the ones that create searches, and that is what §1 is about.

**And one route answers the matcher's numbers from another context's router**
([ADR-0161](../../adr/0161-the-game-screen-draws-its-courts-pairing.md)):

| Route | Surface | Returns |
| --- | --- | --- |
| `GET /api/v1/games/{game_id}/pairing` | — | One game's court priced for the reader: the forecast, the split, what is at stake, each seat's Level |

It is `games`' route over `games`' port, signed by an adapter in the matcher's infrastructure,
and it records nothing — the shape is in §5a below. It is here because the numbers are this
engine's and the rule that produces them is stated in this file.

### `POST /searches` is deliberately not idempotent

Two taps are two searches. The index moved between them, and §19's denominator is *searches
run*; `MIN_SHORTLIST`'s falsifier is literally whether the rung offers were computed, read off
row counts. Collapsing a double tap would put a lie in the one table the product uses to judge
itself. There is no idempotency window and no `Idempotency-Key`.

This is the opposite of the assessments router's idiom (`POST` returning `200` with the
existing run) and the difference is the point: an assessment is a thing you are in the middle
of, a search is a thing that happened.

---

## 2. What the client may send: asks only

**The client sends what it is asking for. It never sends a fact about the searcher.** The
backend reads the profile, the grid, the radius, the tags, the rating, the intent and the
gender preference itself, at request time, and *that* read is what travels inward — which is
also why the searcher's facts are passed in to `matchfit` rather than looked up there: the
index copy may lag, and the searcher's own facts must be exactly what the backend just read.

| Field | Route | Notes |
| --- | --- | --- |
| `sport` | all | Fixes the seat count (`kernel/sports.py`) |
| `mode` | searches, lineups | `COMPETITIVE \| FOR_FUN`. **Absent on the deck** |
| `availability_override` | searches, lineups | The one ask that looks like a fact and is not — ADR-0099 rung A rides it |
| `locked_seats[]` | lineups | Player ids already seated. Non-empty ⇒ `FILL_SEATS` |
| `offered_by_search_id` + `rung` | searches, lineups | Taking a rung offer is a **new search** citing the one that offered it |

**There is no per-search radius input.** Widening happens only by taking a rung offer, clamped
to the profile's own 1–50 km bounds — the cap already existed and
[`the-five-numbers.md`](the-five-numbers.md) did not invent it. A searcher at 50 km gets no
radius rung at all.

**§8.1's `meetup_id?` is dropped.** Meetups are the prototype's social half, out of scope on
this map.

Every fact a client could helpfully send is one the backend must read anyway to be safe: a
stale radius supplied by a client is a gate evaluated on a lie.

---

## 3. The search envelope

One object, identical on all four routes, holding every fact about *the search* rather than
about a candidate. One renderer, one type.

```
search: {
  search_id, at, surface, mode?, ruleset_version, engine_version,
  optimised_for: SEARCHER | GROUP,
  index_stale: bool,
  pool: { sport, radius_km_used, players_in_range, window, post_gate: true },
  rung_offers: [ { rung, ask: TIMES | RADIUS, radius_km?, slot?,
                   candidates_above_floor, window } ] | null,
  radius_clamp: bool,
  sorts_available: [ BEST_FIT | CLOSEST | EVENEST | MOST_RELIABLE ]
}
```

**`sorts_available[]` was added by [#171](https://github.com/Raketa02/Raketa/issues/171) and is
recorded here** — [`the-play-screens.md`](the-play-screens.md) §4 decides it, and it belongs in
this shape because it is a fact about *the search* and not about a candidate. A closed vocabulary,
server-driven: a client deriving offerability from `degraded_terms` would be encoding a
sort-to-term mapping, which is the objection that promoted `distance_km` in the first place.
*Most reliable* is absent from the list on day one and the control **is not drawn** — a visible
control that reorders nothing is the product lying quietly.

**The staged pool counts do not cross the wire.** `n_generated`, `excluded_by_gate`,
`n_scored`, `n_cleared_floor` live on the record, where an analyst reads them. The client gets
exactly ADR-0099's post-gate description and nothing else, because
[ADR-0096](../../adr/0096-gender-preference-mutual-gate-invisible-to-the-scorer.md)'s ninth
gate makes a pre-gate count and a post-gate count differ **per searcher**, and the delta would
be readable — which is precisely what a mutual gate must never be. The originating ticket
asked for "the pool counts at each stage"; ADR-0099 wins.

**`window` is on the response and on every rung offer**, as a code —
`TODAY | TOMORROW | WEEKEND | THIS_WEEK | ANY`. The **backend** derives it, at search time,
from the grid the search actually ran on;
[ADR-0100](../../adr/0100-challenge-window-derived-never-chosen.md)'s *the matcher never emits
a window* is untouched, and its *the backend derives it at challenge creation* becomes a
**re-derivation** from the stored search's own grid rather than a first derivation. Reading a
stored label back would be how a stale label ships the day `window_of` changes; re-deriving
from the stored grid is deterministic and self-checking.

A rung offer carries its own window because a challenge sliding from `WEEKEND` to `THIS_WEEK`
is part of what widening costs, and ADR-0099's whole argument for offered-not-applied is that
the player sees the cost before paying it.

**`rung_offers: null`** means the offers were not computed at all — the shortlist cleared
`MIN_SHORTLIST`. An **empty list** means computed and none available, and it has two causes the
client does not have to tell apart: there was nothing left to offer, or **this search took a rung
and the ladder does not chain**. One climb per search screen, so the widest any accepted offer
reaches is ×2.0 of the radius the player saved. The two empties are told apart on the **record**,
by `rung_taken` beside the list ([`search-telemetry.md`](search-telemetry.md) §2) — **no field was
added to this envelope for it**, and a client that renders an empty list as *nothing left to
offer* is right either way. See §7.

**`index_stale`** is the flag; the threshold that turns it into a refusal belongs to
[The matcher's picture of the city](https://github.com/Raketa02/Raketa/issues/173), not here.

---

## 4. The candidate

Carried in full on every returned row, on every route, on the `POST` and on the `GET`.

```
candidate: {
  player_id, fit, distance_km,
  player_card: { nickname, photo_id?, photo_url?, review?, area_code, social_tags[],
                 level, band, range,
                 player_score?, counted_games?, last_five? },
  concerns: [ { term } ],
  terms: [ { term, weight, value, contribution, evidence: <closed union> } ],
  degraded_terms: [ { term, reason: DegradedReason } ],
  modifiers: [ { code, points } ],
  liveness_reasons: [ code ],
  inclusion_reason?: INTEREST_LIFT,
  at_stake?: { win_delta, loss_delta },
  would_be_forecast?: <Forecast>
}
```

**The full breakdown ships with the search, not behind a tap.** *Why 78?* has to open
instantly and offline-tolerantly, because it is the moment the product's central claim is
being tested and a spinner there is the claim failing. §12's *"the card shows the top three
reasons"* is a **rendering** decision the client makes over data it already holds. Twenty rows
of codes and numbers is tens of kilobytes; two payload shapes for one concept is two generated
types that drift.

**`degraded_terms` is lifted out of `terms`** for the same reason
[`search-telemetry.md`](search-telemetry.md) lifts it out of the blob: it is the
renormalisation basis, and without it a Fit is uninterpretable — §10 renormalises per
comparison, so which terms fired *is* the reading.

**Each entry says whose gap it is, over a three-value `DegradedReason`** —
`NOT_YET_ON_THIS_PLATFORM | NOTHING_FROM_YOU | NOTHING_FROM_THEM`, settled by
[#233](https://github.com/Raketa02/Raketa/issues/233). A flat list of `Term` held *reliability
is not a thing on this platform yet* and *they have not said what kind of evening they want*
as the same fact, twenty times a search — the exact conflation `floor.py` refuses by name at
the point it changes a number: *the gate counts person-specific gaps and never platform-wide
absence.*

It is a **code and not a sentence**, on this file's own rule and
[ADR-0106](../../adr/0106-evidence-vocabulary-is-contract-weights-are-configuration.md)'s: a
client writing *"they haven't declared"* from a bare `INTENT_ALIGNMENT` is an engine rule in
TypeScript, and *"nobody has a record yet"* goes silently false the day `matches` ships, with
nothing that goes red. `NOTHING_FROM_THEM` **deliberately swallows every reason a record could
not be read** — no record, an observation past the horizon, no strand clearing the bar — so
that §5's recency refusal is held by the shape of the vocabulary rather than by a reviewer
noticing it in a later ticket. `NOTHING_FROM_YOU` wins a tie, because it is the only one of
the two the reader can act on.

**Two authors, and neither can be the other.** Only the term function knows which side was
empty; only the layer holding `absent` knows a term has no provider at all, and that set is
built in the composition root rather than read off the ruleset. So a term in `absent` reports
`NOT_YET_ON_THIS_PLATFORM` **whatever the term said**, overwritten one layer out where
`Admission.live` already is, and the scorer never learns which contexts this platform has
built.

**The platform tier repeats on every row and is drawn once.** It stays on the row because it
is that candidate's renormalisation basis and a card whose basis is incomplete cannot be read;
[`the-play-screens.md`](the-play-screens.md) §8 puts it in the sheet's footer beside the
version stamps, where the per-person gaps stay with the person. Suppressing it on the wire
instead was refused: the basis is not decoration.

**No liveness number.** Reasons only. There is no field to write one to
([ADR-0106](../../adr/0106-evidence-vocabulary-is-contract-weights-are-configuration.md) §5).

**`inclusion_reason` carries one code, and that is a correction rather than a loss.**
[#175](https://github.com/Raketa02/Raketa/issues/175) found the field describing one of its three
values: since [ADR-0099](../../adr/0099-relaxation-offers-the-searchers-own-asks.md) only the
interest lift **admits** anybody, and the other two **reorder**. So `NEWCOMER_WINDOW` moves to
`liveness_reasons[]`, where a printable reorder belongs, and `ZERO_EXPOSURE` **never crosses the
wire at all** — *you are seeing this person because nobody has been shown them all week* is a
third party's unpopularity, and the searcher is owed no version of it. It stays in
`search_candidate.inclusion_reason`, which keeps all three values: **the store is open where the
wire is closed**, and `ZERO_EXPOSURE` is the first code that lives only there. The field stays a
union of one so the next reason that genuinely admits somebody has somewhere to go.

**`at_stake` is filled by the backend, never the matcher** — the one candidate field with a
different author. It is `AtStakeQuery` over `rating`
([`consumer-driven-contracts.md`](consumer-driven-contracts.md)), attached after `matchfit`
returns, because ADR-0021 forbids the client computing it and ADR-0098 forbids the matcher
re-deriving it. **Omitted in for-fun** (meaningless — §23 Q11) and, in competitive, **omitted
only for a pair with no Level between them** — the rule ships
([ADR-0139](../../adr/0139-a-confirmed-result-is-evidence-and-a-level-moves-by-what-it-taught.md)).
The card shows no block when it is absent, and the client needs no branch either way.

**`player_card`, `distance_km` and `concerns` are [#171](https://github.com/Raketa02/Raketa/issues/171)'s
additions.** The card is attached by the **backend** after `matchfit` returns — the second field
family with a different author, for the same reason as `at_stake` — and its contents are a closed
list with two permanent refusals in it, a bio and activity recency
([ADR-0107](../../adr/0107-the-player-card-is-assembled-outside-the-engine.md)). `distance_km` is
promoted out of the distance term's evidence and is an **integer**, so the *Closest* sort reads a
field rather than reaching into a variant. `concerns` is the engine's own statement that a term is
genuinely weak — §12's warning line, judged where the weights are rather than by a client
thresholding a value. Detail in [`the-play-screens.md`](the-play-screens.md) §1.

**The near-miss band is never returned.** Layer 3 of the telemetry is engine-internal, on the
line §21 draws around passes and declines.

**The shortlist is bounded and unpaginated** — `n_returned ≤ SHORTLIST_MAX`, **20**. There is no
page two; past the last row there are rung offers or an honest empty state. The bound is ruleset
data and not a contract number, so a client never reads 20 from anywhere: it renders the rows it
is given ([`ranking-weights.md`](ranking-weights.md) §13).

---

## 5. The line-up

```
lineup: {
  arrangements: [ { pairing_id, is_current, is_best, is_evenest,
                    sides: { A: [seat], B: [seat] },
                    forecast: <Forecast>, split: <Split> } ],
  seats: [ { side, seat_index, relationship: SELF | PARTNER | OPPONENT,
             candidate? , unfilled_reason?: code } ],
  group_reason: EVENEST_ARRANGEMENT | STRONGEST_WEAKEST_SEAT | BEST_AVERAGE_FIT
              | MOST_SHARED_SLOTS   | GROUP_RAPPORT
}
```

**`group_reason` and `is_evenest` are [#180](https://github.com/Raketa02/Raketa/issues/180)'s
additions**, specified in [`the-group-objective.md`](the-group-objective.md) §5 and recorded in
this shape. `is_best` now means ***best by `G`***; `is_evenest` is the min-gap arrangement *Even
it out* selects, and the two are separate booleans because the new fact the builder can state is
that they **differ** — which happens precisely when a four's levels are near-equal and balance has
nothing left to say. **`G` itself is never returned**: a second score the player must trust is
worse than none, so the evidence half is paid by one closed code naming the term with the largest
margin between the winning combination and the runner-up.

**`is_current` on a line-up is the *evenest* arrangement**, in both modes
([#289](https://github.com/Raketa02/Raketa/issues/289)). Who is on the court does not change:
the group objective still chose the four and `group_reason` still says why. What changes is
which way round they sit — the same re-seating *Even it out* performs by hand, so a builder
that opened on `is_best` would be showing a court the player's first tap undoes. `is_best`
keeps its meaning and keeps crossing, and `lineup.seats` follows `is_current`, so the seating
in the response is the evenest seating. **`ForecastResponse.is_current` is untouched** — there
it means *the seat order you sent*, and a client that sends an arrangement must get that one
back marked current or a swap cannot be drawn.

**All three arrangements cross, each with its own forecast.** There are exactly three pairings
of four people and `arrange()` already walks all of them to pick the min-gap one. Returning
what the engine already knows costs nothing and makes §9.9's *"both functions live in the
matcher and neither is reimplemented on the client"* **enforceable** rather than aspirational:
every swap the builder permits is one of the three, so there is no arithmetic left for the
client to be tempted by. *Even it out* is a selection, not a computation. Singles carries one
arrangement and no swap.

**`relationship` is stated, never inferred from `side`.** §9.9's entire asymmetry —
`PARTNER_STYLE_MULTIPLIER` against `OPPONENT_STYLE_MULTIPLIER` — hangs on it, and a client
deriving it is a second implementation of a domain rule.

**`optimised_for: GROUP`** rides in the search envelope, and §8.4 is the reason it exists: with
seats locked the matcher is no longer optimising for the searcher, who may end up with a worse
individual match than an empty builder would have given them. The screen has to say so.

**A seat may be unfilled and the line-up is still a `200`** — a partial line-up is the honest
answer, and no seat is ever filled below `QUALITY_FLOOR` to complete a four (ADR-0099).
**The `unfilled_reason` vocabulary is settled** by
[`the-group-objective.md`](the-group-objective.md) §5.1: `NO_CANDIDATE_ABOVE_FLOOR`,
`NO_ADMISSIBLE_COMBINATION`, `POOL_EXHAUSTED`, `NO_SHARED_SLOTS`. ***Three of four* is not a
different shape from *nobody*** — both are this shape, with one or three seats carrying a reason,
and there is no separate empty state for a line-up.

> **One closed vocabulary, two places on the wire.** The build found that the fourth code cannot
> sit on a seat: §5.1 defines `NO_SHARED_SLOTS` as *seated, but the four-way intersection is
> empty — a dock, never a refusal*, which is a statement about the whole line-up and about
> nobody's seat. It rides as **`lineup.dock`**, in the same enum, and the other three ride as
> `seats[].unfilled_reason`. Recorded there in full.

### The forecast

One type, everywhere it appears:

```
Forecast: { pct, sigma_group, provisional: bool, assumption?: code }
Split:    { your_side, their_side, gap }        // on the arrangement, not the forecast
```

**`provisional` travels inside the forecast, not beside it.** The failure §9.9 is guarding
against is a screen showing the number without its caveat, and a sibling boolean is exactly
how the two get separated in a refactor. `sigma_group` crosses because the confidence is part
of the claim — §12 rule 1 wants the evidence named, not a category. `assumption` is what makes
*"as if the missing player matched the one already there"* renderable in the client's own
words.

§9.9's equality test stands: the moment the last seat is taken, the provisional figure and the
arranged figure agree exactly.

**The split is the evidence behind the percentage** ([#289](https://github.com/Raketa02/Raketa/issues/289),
[ADR-0136](../../adr/0136-the-split-is-evidence-for-the-forecast-not-a-second-score.md)). The card
the builder is built against prints two side strengths, the gap between them and a two-segment
bar, and every one of those is a number **only the engine has**: a side's strength is not the
mean of the two people on it (§3.1's `TEAM_STRENGTH_SHARE`), so a client drawing them would be
averaging seated levels — which is §11.3's *"no forecast arithmetic on the client"*, the one rule
whose check is looking for arithmetic rather than reading intent. §12 rule 1 is the argument:
**name the evidence, not a category** — the same rule that put `sigma_group` beside `pct`. `pct`
says *how even*; the split says *between what and what*, on the scale players already read levels
on.

**It is not the group objective and must not become one.** `is_best`'s own refusal — *a second
score you would have to trust is worse than none* — stands unchanged, and `G` still never
crosses in any shape. What crosses here is an **input** to a figure already served.

Four rules, each a way the four numbers could come apart:

- **On the arrangement, not on the `Forecast`.** `Forecast` is *one type, everywhere it appears*
  and rides on every shortlist row's `would_be_forecast`; a response carries at most three
  arrangements and tens of candidate rows, and this is a fact about an arrangement.
- **`gap` is served rather than left to a subtraction.** A client subtracting two rounded figures
  and an engine subtracting two unrounded ones disagree at the boundary, and the card prints all
  three.
- **`gap` is signed** — `your_side − their_side` — because the client's bar takes an *advantage*
  ([`design-system.md`](../../../frontend_player/docs/design-system.md) 7.11: `BalanceBar.advantage`
  is *your side's strength minus theirs*). An unsigned gap would leave the client deciding which
  half of the bar is bigger, which is the same arithmetic in a smaller disguise.
- **The four numbers are one computation.** `pct`, `your_side`, `their_side` and `gap` come off
  one reading of the two sides — a card showing `gap 0,00` beside `74% · fairly even` is the
  failure this exists to prevent.

**Singles** carries one arrangement and no swap, so the split is two player strengths and their
difference. **A provisional arrangement carries a split like any other**, under the same
assumption `pct` is carried under — the empty seat is read *as if the missing player matched the
one already there* — and `provisional` carries that caveat for all four numbers at once.

**`would_be_forecast`** is §8.2's one exception to client-side sorting: *Evenest* with a single
seat left needs an arranged forecast per candidate, so the engine precomputes one per shortlist
row when `open_seats == 1` and **omits it otherwise**. Everything else — *Best fit*, *Closest*,
*Most reliable* — sorts client-side over fields already in the response, because a round trip
per sort tap is latency spent on nothing.

> **Amended 2026-09-11 by [#407](https://github.com/Raketa02/Raketa/issues/407): `candidates[]` on
> a line-up is the pool it seated from, and not the seated alone.** The returned band used to be
> exactly the people who sat down, in seat order — *a court is its answer, not a list*. It is also
> the only list the builder reached from a challenge has: that journey mints no shortlist,
> `POST /forecasts` and the send both refuse anybody the cited search never returned (ADR-0108
> §3, `search_court_origin.py`), and a plain `POST /searches` is gated by the very challenge being
> completed. So the pool over a fill court offered the one person just taken off a seat, or nobody.
>
> Now `candidates[]` is **`pool_for`'s top `K` by Fit, in Fit order, with the seated among them** —
> `lineup.seats[].player_id` is looked up there, as `LineupSeatSchema` always said. `K` is ruleset
> data (24 today) and a client never reads it from anywhere, exactly as it never reads twenty.
> `position` on a line-up's recorded row is therefore a **place in the pool** and no longer a
> seat — the Fit rank, unless a row above was dropped for a card that could not be assembled,
> exactly as on a shortlist; who sat down is the response's `lineup` and, on the record, layer 4's
> `seated` ([`the-group-objective.md`](the-group-objective.md) §6). **Exposure still counts the
> seated only** — the court is what was shown, the rest of the pool is shown only if the player
> opens the list, and a ⚡ that counted two dozen appearances would sink the top of every ranking
> under the ±6 adjustment. A list opened off the record is shown and *under*-counted, the opposite
> error from a shortlist's rows past the fold; neither is a gate. `POST /searches`
> growing `completing_challenge_id` was the other shape and was refused: a shortlist is twenty by
> rank key, so an accepted seat is not guaranteed a row on it, and a pick that moved the court
> onto such a list would drop a seat ADR-0150 §8 says is not a control.

### 5a. The game's pairing — `GET /games/{game_id}/pairing`

[ADR-0161](../../adr/0161-the-game-screen-draws-its-courts-pairing.md). The forecast above,
read for a court whose line-up is **frozen**, by somebody on it, while the game has not
happened. One shape:

```
GamePairingResponse
  read_at:   instant
  forecast?: Forecast                          — the type above, omitted together with split
  split?:    { your_side, their_side, gap }    — in the reader's direction
  at_stake?: { win_delta, loss_delta }         — the reader's own
  seats:     [ { player_id, level, band, range: {low, high}, confidence } ]
```

**It is the challenge card's number.** The read goes through the same use case the challenge
detail's card is built on, so the forecast the challenge screen drew while the court was being
arranged equals the game's once the line-up completes — asserted over HTTP. §9.9's equality
test has a third reading: challenge card, game pairing, one figure.

**In the reader's direction.** `split.gap == your_side − their_side`, signed and served, so two
readers on opposite sides see the sign flip and the same `pct`. `at_stake` is the reader's own
pair, and on a game it is priced **side against side** — every seat is known, and that is the
pair the result will deliver (`one_side` in the rating engine's rule). The candidate card's
`at_stake` prices *you against this person* because the other seats are unknown when a card is
drawn; the two are different questions and, in a four, different numbers.

**Three absences.** `forecast` and `split` are omitted together when the pairing cannot be
computed — somebody on the court holds no rating in the sport, or a seat could not be priced —
and there is **no reason beside the absence**. `provisional` is never `true` on a game and
the field is kept because the shape is the court's: when a seat can be open, the answer is
*omitted*, never a half-read forecast. `at_stake` is omitted on a friendly (meaningless rather
than unavailable) and where the rule has nothing to move or nothing to price against — the reader
unrated, or a whole side unrated; a side with one unrated seat is priced over its rated members,
exactly as the update prices it. Never a pair of zeros. `seats`
names whoever holds a rating, in the court's own order, from `rating`'s published figures and
never from the index — and a court with an unrated member still names the rated ones.

**Who and when.** Only somebody on the court — `404 game_not_found`, one code for two cases —
and only while the game is `AWAITING_ENTRY` — `409 pairing_is_history` after. Nothing changes
on `GET /games`: the seat there carries a handle and nothing else (ADR-0141).

---

## 6. The deck

`POST /api/v1/deck` takes **the sport and the week you are asking about** — and nothing
else — and returns one deal: an ordered batch of cards, one `search` row, one `search_id`
shared by every card in the deal.

**The three refusals this body is written under are a mode, a widening and a pass window,
and a grid is none of them.** *Match me* is reached from the screen the week is edited on,
so a deal that ignored the edit would rank on a week the player had just replaced; the
client cannot compute the difference itself, because a search that took a times rung ran on
a grid with a slot the player never ticked and only the backend holds that. Like the
shortlist's, it is an **ask and never a correction**: it writes no profile, and the offer to
keep it — `KEEP_THESE_TIMES` — rides back on the response of the route that used it.

**A deal is at most `DECK_DEAL_MAX` cards, 10**, and a spent deal deals again — a new request, a
new `search_id`, the same exclusions plus everybody already dealt. **Exhausting a deal is not
exhausting the pool**: the honest empty state belongs to a fresh deal that came back with nothing,
never to a player who has seen ten of forty.

**One-at-a-time is how the deck is shown, not how it is computed.** §9.11's ordering policy —
people who already said yes, then high liveness above the floor, then the rest — is a property of
a whole deal and cannot be evaluated one card at a time. **Its third band is no longer spread:**
§9.11's λ = 14 is struck with the stage it belonged to
([ADR-0126](../../adr/0126-position-moves-on-a-fact-about-the-player-never-about-the-list.md)), so
the deck's variety is that three-band order and `PASS_SUPPRESS`, and nothing in a deal moves on a
fact about the other cards. Per-card searches would also make the deck the highest-volume writer in the system
by an order of magnitude for no analytic gain: the interesting unit is the deal, and *which
card was accepted* is `position` on `search_candidate`, which already exists.

**The weight vector is resolved backend-side and no mode crosses the wire.** The deck reads
the viewer's declared `PlayIntent` for that sport: `COMPETITIVE → comp`, `FOR_FUN → fun`,
**`NO_PREFERENCE → fun`**, not a third ruleset. The client deriving that mapping would be a
domain rule in TypeScript; the response echoing a `mode` would fight the telemetry constraint
that `mode` is `NULL` exactly when `surface = DECK`.

> **Amendment to [`search-telemetry.md`](search-telemetry.md), found here.** That constraint
> left the deck's own weight vector **unrecorded**: nothing on the `search` row says which
> vector ran, while ADR-0104 makes the row the reproducible answer and
> [ADR-0105](../../adr/0105-determinism-is-a-set-iteration-problem-in-python.md) makes
> determinism a property test. It is recoverable from `search_candidate.terms` only by reading
> a *candidate* row to learn a fact about the *search* — and not at all when the deal was
> empty. **`search` gains `intent_read`** — `COMPETITIVE | FOR_FUN | NO_PREFERENCE`, non-null
> exactly when `surface = DECK`, the mirror of `mode`'s constraint. It records the
> **declaration as it stood**, not the vector it mapped to, so a later change to the mapping
> does not rewrite history.

**The relaxation ladder does not reach the deck** (ADR-0099): no rung offers, no
`pool_description` ladder. The deck's own exclusions — passed within `PASS_SUPPRESS`, already
asked, already has an open game with you — are gates, and their numbers are **set**:
`PASS_SUPPRESS = 30 d`, `INTEREST_TTL = 21 d`, `OUTSTANDING_INTEREST_CAP = 20` per sport
([#194](https://github.com/Raketa02/Raketa/issues/194)). **None of the three crosses the wire as
a number** — see §7.

---

## 7. Interest

`POST /api/v1/interest`, `{ sport, player_id, search_id }`.

**A top-level resource, not a sub-resource of a search.** Interest outlives the search that
surfaced it — days against a search run once — and a nested route would say the opposite.
`search_id` is **required and non-nullable**: it is the origin key, and
[`search-telemetry.md`](search-telemetry.md) §4 makes an interest citing an unknown or foreign
`search_id` **refused, never linked as null**, because a silently dropped link is a denominator
that lies.

**Idempotent per `(from, to, sport)`** — a second yes returns `200` and creates nothing.

**The cap is hard, and it is shown before it bites.** `OUTSTANDING_INTEREST_CAP = 20` **per
sport**, and the write is **refused** at the cap with a closed reason code
([ADR-0127](../../adr/0127-a-signal-expires-or-is-refused-never-quietly-decays.md)). §9.5.1's
*soft* cap — *past it the oldest decays faster* — is refused: it reaches backwards and shortens
the life of yeses already sent, under a rule the player was never told, because a twenty-first
arrived. **Outstanding** means sent, unexpired and **not yet mutual**; a mutual has been answered
and is no longer in flight.

`GET /api/v1/interest` carries the **per-sport `outstanding` count and the `cap` in force**,
because a cap the player cannot see is a refusal they cannot predict. Every outgoing row carries
**`expires_at`**, dated when the yes was created — `INTEREST_TTL = 21 d`. On expiry the row is
simply gone: there is no *expired* state and no archive, because a list of yeses that were not
returned is the inverted shape of what
[ADR-0109](../../adr/0109-a-read-back-names-what-it-withholds.md) refused.

**Which side of ADR-0106's line all three sit on.** All three numbers are **ruleset
configuration**; none is a contract fact. What is *contract* is three shapes around them —
`expires_at` on an outgoing row, the `outstanding` / `cap` pair plus the refusal code, and, for
`PASS_SUPPRESS`, **nothing at all**. So: **the client never hardcodes any of the three and never
computes an expiry.** It renders a number the backend sent and reads a moment the backend
computed — which is the whole reason ADR-0106 drew the line where it did, since a phone in
somebody's hand can be months behind the backend.

Interest is the deck's own mechanic and is in scope. The **challenge** it may become belongs to
`matches`, which is not.

---

## 8. Errors, and which reads may fail soft

One envelope — `{code, message, trace_id, details?}` — because this backend already has one and
clients branch on `code` only. §18's table was written for a Go service behind an 800 ms
circuit breaker; ADR-0093 deleted that architecture, and in-process the matcher cannot be
unreachable, only raise.

| Status | Code | When |
| --- | --- | --- |
| 503 | `matchmaking_unavailable` | The engine raised |
| 503 | `gate_data_unavailable` | A fail-closed read failed |
| 503 | `index_too_stale` | Past #173's threshold |
| 503 | `search_not_recorded` | ADR-0104: a search whose record cannot be written is not returned |
| 409 | `sport_not_rated` | §9.1's gate on the searcher — mirrors the shipped `sport_already_rated` |
| 409 | `play_intent_not_declared` | ADR-0094's interstitial |
| 403 | `account_held` | ADR-0095 points both ways |

Distinct codes at the same status, because a client must be able to tell a transient outage
from a refusal about *you*. **An empty shortlist is a `200`** with `pool` described — the
honest empty state is an answer, not a failure.

**Never a fallback list.** When the engine is down the feature is down. A hand-rolled backend
ranker arriving as a hotfix is how a second, worse, unexplainable ranking implementation enters
the system permanently.

| Read | Fails | Why |
| --- | --- | --- |
| Block set, hold flag | **Closed** — the search refuses | ADR-0095: a gate that cannot be evaluated excludes |
| Pairwise history, open-challenge pair set | **Soft** | ADR-0098: the backend's live re-verify is a second net |
| Exposure, suppression | **Soft** | Stated here |

**Suppression fails soft, and it is worth saying out loud** because ADR-0095's rule reads like
it should not. Applying *a gate that cannot be evaluated excludes* to suppression would empty
the deck rather than protect anybody: suppression is a courtesy — *do not show me that person
again just yet* — and a block is a safety control. Classifying every read as one or the other,
in one table, is what stops the next person having to guess.

---

## 9. The internal boundary

`SearchContext` is the module's type: the searcher's own facts as the backend just read them,
plus the live gate facts. It carries gender preference and `exclude_player_ids`; it does not
reach `matchfit`.

**The searcher's pairwise counterparts are bounded at 500 and ordered most-recent-first**
(ADR-0098, settled by [#164](https://github.com/Raketa02/Raketa/issues/164)). One line and one
property test, and it is load-bearing: it makes a counterpart truncated by the bound and one
fully decayed by time **indistinguishable by construction**, which is what keeps familiarity's
signed decay honest at the tail instead of reading a repetition-seeker's regular partner as a
stranger.

---

## 10. What this file does not decide

- ~~**What each Play screen needs from any of this**~~ — settled by
  [#171](https://github.com/Raketa02/Raketa/issues/171) in
  [`the-play-screens.md`](the-play-screens.md), which added three routes and two candidate field
  families to this file.
- ~~**The `unfilled_reason` vocabulary and the doubles objective**~~ — settled by
  [#180](https://github.com/Raketa02/Raketa/issues/180) in
  [`the-group-objective.md`](the-group-objective.md), which also makes `is_best` mean *best by
  `G`* rather than *evenest* (§3.1) and adds `group_reason` to the line-up envelope (§5).
- **The staleness threshold behind `index_stale` / `index_too_stale`, and `snapshot_version`** — [#173](https://github.com/Raketa02/Raketa/issues/173).
- ~~**`INTEREST_TTL`, `OUTSTANDING_INTEREST_CAP`, `PASS_SUPPRESS`**~~ — **set** by
  [#194](https://github.com/Raketa02/Raketa/issues/194): 21 d flat, 20 per sport refusing, 30 d
  deck-only. All three are configuration; §7 carries the three contract shapes around them.
- **The tag relationship matrix behind the style and vibe evidence codes** — [#179](https://github.com/Raketa02/Raketa/issues/179).
