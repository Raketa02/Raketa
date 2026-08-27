# The Play screens

**What the contract owes each surface, and which screen behaviours are decisions rather than
interface choices.**

Produced by [What each Play screen needs from the contract](https://github.com/Raketa02/Raketa/issues/171)
on the map [The matchmaking engine: who sits down, and why](https://github.com/Raketa02/Raketa/issues/155).

**The decisions live in ADRs; this file is the shape to check work against.** The player card
and its refusals are [ADR-0107](../../adr/0107-the-player-card-is-assembled-outside-the-engine.md),
the forecast route is [ADR-0108](../../adr/0108-a-forecast-is-a-route-not-a-search.md), the
read-back and the silent yes are
[ADR-0109](../../adr/0109-a-read-back-names-what-it-withholds.md).

> **This does not design the interface.** The Play screens' UI build is its own effort with its
> own design lane. What is here is what the *contract* owes each surface, plus the handful of
> screen behaviours that are load-bearing enough that leaving them to the interface would let
> the product quietly change what it claims.

---

## 0. The routes, after this ticket

[`the-two-contracts.md`](the-two-contracts.md) §1 fixed four routes. The Play screens need
three more. That file's §1 stands as written for the four that create searches.

| Route | Creates a search | Added by |
| --- | --- | --- |
| `POST /api/v1/searches` | yes | [#170](https://github.com/Raketa02/Raketa/issues/170) |
| `POST /api/v1/lineups` | yes | [#170](https://github.com/Raketa02/Raketa/issues/170) |
| `POST /api/v1/deck` | yes | [#170](https://github.com/Raketa02/Raketa/issues/170) |
| `GET /api/v1/searches/{id}` | no | [#170](https://github.com/Raketa02/Raketa/issues/170) |
| `POST /api/v1/interest` | no | [#170](https://github.com/Raketa02/Raketa/issues/170) |
| **`POST /api/v1/forecasts`** | **no — deliberately** | [ADR-0108](../../adr/0108-a-forecast-is-a-route-not-a-search.md) |
| **`POST /api/v1/passes`** | no | §7 below |
| **`GET /api/v1/interest`** | no | [ADR-0109](../../adr/0109-a-read-back-names-what-it-withholds.md) |

**And two writes that are not matchmaking's at all.** The search screen is the edit surface
for both, so they are noticed here and owned by `player_profile`: declaring or updating a
**Play intent** ([ADR-0094](../../adr/0094-play-intent-declared-per-sport-in-its-own-aggregate.md))
and writing the **availability grid** back to the profile — *Keep these times?*, specced to
ADR-0094's shape with no long suppression by
[#164](https://github.com/Raketa02/Raketa/issues/164).

---

## 1. The candidate, as a screen sees it

Every returned row carries the pairing block
([`the-two-contracts.md`](the-two-contracts.md) §4) **and** a `player_card`, attached by the
backend after `matchfit` returns — the same seam `at_stake` already rides
([ADR-0107](../../adr/0107-the-player-card-is-assembled-outside-the-engine.md)).

```
candidate:   { player_id, fit, distance_km, player_card, ... }
player_card: { nickname, photo_id?, area_code,
               social_tags[], level, band, counted_games }
```

Closed list. `photo_id` is **omitted** (not null) when the player has no photo, and the client
draws the generated court poster.

> **`distance_km` sits on the candidate and not inside the card**, matching
> [`the-two-contracts.md`](the-two-contracts.md) §4. An earlier draft of this section had it
> inside the card, which is the one placement ADR-0107 rules out: **a card says only what its
> subject published**, and every field on it is a fact about *that person alone*. A distance is a
> fact about a **pair** — it is the distance term's own reading, computed by the engine against
> the searcher's centroid, where every other field of the card is assembled by the backend from
> what the player themselves put there. Putting it on the card would make it the single field
> whose value changes depending on who is looking.
>
> It is an **integer**, and it is **omitted** rather than `0` when the distance term stood down —
> the two spellings of absence ([ADR-0106](../../adr/0106-evidence-vocabulary-is-contract-weights-are-configuration.md)
> §4), which is what lets *Closest* sort a stood-down row last instead of first.

**Never on a card, ever:**

| | Why |
| --- | --- |
| a bio, or any free text a player wrote | the platform's first player-authored text field, and a moderation surface out of scope |
| activity recency, at any granularity | row three of §9.5's Liveness table — [ADR-0106](../../adr/0106-evidence-vocabulary-is-contract-weights-are-configuration.md) §5 |
| gender | [ADR-0096](../../adr/0096-gender-preference-mutual-gate-invisible-to-the-scorer.md) |
| a Liveness number | [ADR-0106](../../adr/0106-evidence-vocabulary-is-contract-weights-are-configuration.md) §5 — reasons only |
| a block, a pass or a decline | §21, and [ADR-0109](../../adr/0109-a-read-back-names-what-it-withholds.md) |
| an unsettled case | the matcher never reads `cases`; the hold does its work at the gate |

**Absent today, arriving through ports that exist:** last-5 form (`MatchHistoryQuery`),
Player Score (`PlayerScoreQuery`), `at_stake` in competitive (`NoResultUpdateRuleExists`).
Gaps, not refusals.

**A nickname is not shortenable.** There is no name in this platform. Every sentence naming
somebody uses the whole handle or names nobody.

### Reasons, concerns and the two rules about words

- **The full breakdown ships with the search**, not behind a tap
  ([`the-two-contracts.md`](the-two-contracts.md) §4). The card renders three of it.
- **The engine ranks the reasons by contribution; the client picks how many to show.** The
  ordering is arithmetic and is not the client's.
- **`concerns[]` is emitted by the engine, keyed by `term`, ranked.** What counts as a
  *genuinely weak* term is a product judgement about weights and curves and belongs where the
  weights and curves are — a client thresholding a term value would be that judgement in
  TypeScript, differently in every client. The **cap is the client's**: a card shows one,
  *Why 78?* shows all of them, because capping in the engine would throw away exactly the rows
  that explain a low Fit on the screen built to explain it.
- **A reason line never restates a value the card already renders.** This is §12 rule 3,
  narrowed — see §10.

---

## 2. Find me a game

Sport, then **Mode**, then the 7×3 grid — the same grid as onboarding, because asking twice in
two shapes is how availability data goes stale.

**What the mode switch changes:** the weight vector for this search, and nothing else. It is a
`SearchMode` (two values), never a `PlayIntent` (three) — the distinct types that make §5's
collision a type error ([ADR-0094](../../adr/0094-play-intent-declared-per-sport-in-its-own-aggregate.md)).
Switching it offers to update the **declaration** inline, with 30-day suppression on decline.

**The grid edit is per-search by default and offers to write back.** *Keep these times?* is
ADR-0094's shape with **no** long suppression, because a grid legitimately differs per search
where an intent does not ([#164](https://github.com/Raketa02/Raketa/issues/164)).

**The two refusals are known before the tap, and the 409 is the backstop.** `sport_not_rated`
is settled by construction — the sport chips are drawn only for rated sports.
`play_intent_not_declared` is a screen the client opens **knowingly**, because ADR-0094 made
this the edit surface; the `409` still exists for a stale profile on a second device, and it is
never the designed path.

---

## 3. ⚡ Let the engine fill the seats

`POST /lineups`. The response carries the seated line-up, all three arrangements with a
forecast each, and `optimised_for` in the envelope.

**The animation is presentation over a completed answer, and the client may take its time.**
Animating a finished response is ordinary interface craft; the product's promise is that the
*number* is checkable, not that the spinner is proportional to work. Two lines it may not
cross, and both are testable without a field:

- **The server never delays to make a search feel substantial.** No stall, no streamed
  progress, no fake stages.
- **The count the animation prints is `players_in_range` from the response** — post-gate,
  ADR-0096 — and never a number the client grew to fill the time.

---

## 4. Pick players myself

The same ranked candidates, the button changed from *challenge* to *add*.

**Sorting is client-side over fields already in the response**, and **which sorts are offered
is server-driven**: the envelope carries `sorts_available[]`, a closed vocabulary. A client
deriving offerability from `degraded_terms` would be encoding a sort-to-term mapping, which is
the objection that promoted `distance_km` in the first place.

| Sort | Reads | Day one |
| --- | --- | --- |
| **Best fit** | `fit` | offered |
| **Closest** | `distance_km` | offered; a stood-down distance sorts last, never as a zero |
| **Evenest** | `would_be_forecast` | offered whenever any seat is filled on both sides, provisional until the last seat |
| **Most reliable** | published Player Score | **not offered** — the reliability term stands down for everybody |

*Most reliable* is not a sort that does nothing. It is a control that **is not drawn**: a
visible control that reorders nothing is the product lying quietly.

**The card says what the candidate would leave on court** — `would_be_forecast`, labelled
provisional while seats remain open.

---

## 5. The court, once full

**All three arrangements cross with a forecast each**, so *Even it out* is a selection
([`the-two-contracts.md`](the-two-contracts.md) §5). The two forecasts stay distinct words:
**best-of-three** answers *are these the right people*, **arranged** answers *is this the right
way round*, and conflating them is how a screen stops changing when somebody is moved across
the net.

**Composing a line-up the engine never scored goes to `POST /forecasts`**
([ADR-0108](../../adr/0108-a-forecast-is-a-route-not-a-search.md)) — bound to the citing
search, re-verifying blocks and holds, stamping `ruleset_version` and `engine_version`,
recording nothing. **No forecast arithmetic runs on the client**, and the check for that is
looking for arithmetic, not reading intent.

---

## 6. Provisional forecasts

Same route, same `Forecast` type, `provisional` **inside** it with its `assumption` code. A
half-empty side is read as if the missing player matched the one already there, and everything
built on it is labelled — header, seat lines, and a sentence stating the assumption.

**One implementation produces both figures, so §9.9's equality is a property test:** fill the
last seat and the provisional figure and the arranged figure are the same number.

---

## 7. Match me — the deck

`POST /deck`, sport only. One deal, one `search_id`, an ordered batch of at most
**`DECK_DEAL_MAX` = 10** cards. The weight vector is resolved backend-side from the viewer's
declared intent, `NO_PREFERENCE → fun`, and no `mode` crosses
([`the-two-contracts.md`](the-two-contracts.md) §6).

**A spent deal deals again**, as a new request with a new `search_id`. The screen runs out of
cards long before the pool does, and only a fresh deal that comes back empty is the empty state.

**A pass is `POST /passes`, carrying the Origin key** — `(search_id, position)`, required. It
needs the origin because `PASS_SUPPRESS`'s own falsifier is *the pass rate on re-shown
profiles*, which is unmeasurable otherwise.

**A pass is write-only.** It is recorded, it suppresses, and **no route ever returns one** —
not to the passer, not as a count, not as *"you have passed on 12 people"*. §21's refusal, and
its enforcement is a schema test over every response type.

**`PASS_SUPPRESS` = 30 days, and it has three boundaries**
([ADR-0128](../../adr/0128-a-pass-is-about-my-deck-a-block-is-about-a-person.md)), all of them
the opposite of a Block's, because **a pass is a statement about my deck and a block is a
statement about a person**:

- **Deck only.** It never reaches the shortlist, the line-up or a forecast. A passed player is a
  full candidate everywhere else, immediately. The deck is a judgement surface — one person, yes
  or no — while a search is a question about the pool, and a search that hides people because of
  a swipe lies about the city. **The named cost: pass on somebody tonight, find them third in
  your shortlist tomorrow.** If that reads as the product ignoring you, the fix is a sentence on
  the deck about what a pass does, never a wider suppression.
- **One-directional.** My pass suppresses in **my** deck and nowhere else, keeping §9.5.1's own
  promise that a pass *costs the other person nothing* literally true. A block has to be
  symmetric or it is worth nothing; a pass carries no claim about the other person at all.
- **Never escalates.** A second pass buys the same 30 days. §9.5.1's *repeated passes are a soft
  signal respected quietly* is struck — it cannot print, it cannot enter ADR-0123's closed silent
  roster, and where it leads is a Block, which exists, is reversible, and requires somebody to
  mean it. A second pass is only possible 30 days after the first, so anybody who wants more has
  had a month to reach for the gesture that means it.

**And the pass record is durable, though the suppression is not.** The falsifier is *pass rate on
**re-shown** profiles*, and a Redis suppression that has lapsed leaves no trace the pair was ever
passed — so the Origin key alone does not pay for it after all. The row is kept; the 30-day
suppression stays the Redis TTL, derived from it (`the-engine.md` §12). The gate is the cache,
the evidence is the row.

**There is still no *Show them again*.** The prototype offers a button clearing every pass at once.
It makes `PASS_SUPPRESS` unmeasurable and makes the suppression a suggestion, and it solves a
problem a real pool does not have. The **exhausted pool** is the honest empty state: the pool
description, and the count of the player's **own outgoing** yeses still waiting.

**A mutual yes is told to both, and arranging the game is theirs.** The challenge belongs to
`matches`, which is out of scope — so the product says *both of you said yes* and stops,
recorded as a demand against `matches` in
[ADR-0098](../../adr/0098-matcher-demands-as-executable-contracts.md)'s shape. Sitting on a
mutual yes would be the product declining to do the one thing it just got permission for.

**`GET /interest` returns outgoing and mutuals. Incoming-and-not-mutual never crosses**
([ADR-0109](../../adr/0109-a-read-back-names-what-it-withholds.md)). A one-sided yes reaches
its recipient only as an interest lift, in a search they chose to run.

**There is no notification.** Nothing in this repository can push anything, so two people who
both said yes find out by opening the app. Said out loud rather than designed around; the push
is in the map's fog with what it will owe already named.

---

## 8. Why 78?

Reads the stored record; **never recomputes**
([ADR-0104](../../adr/0104-the-search-record-is-the-answer-and-never-expires.md)).
`GET /searches/{id}` returns the same schema the `POST` did.

**What the sheet is entitled to show:** every term with its weight, value, contribution and
evidence; the degraded terms and what they renormalised; every modifier with its points; every
liveness **reason**; the concerns; the inclusion reason; the ruleset and engine versions. An
evidence kind the build cannot render is a **named gap saying the app is out of date**, never
a silently shorter list ([ADR-0106](../../adr/0106-evidence-vocabulary-is-contract-weights-are-configuration.md) §6).

**Never:** a Liveness number, a near-miss row, a pre-gate pool count, another player's
breakdown.

**The read-back re-verifies and names what it withholds**
([ADR-0109](../../adr/0109-a-read-back-names-what-it-withholds.md)). The record is immutable;
the response is the recorded answer **plus live gate state**. The round-trip test asserts both
halves — and it is asserted over the record's fields, not over a byte-identical payload, since
the photo URL is re-minted per response by design
([ADR-0107](../../adr/0107-the-player-card-is-assembled-outside-the-engine.md)).

---

## 9. Completing a half-built game

**Split.** The mechanism is decided and live on day one; only the entry point waits.

- **In scope, and exercised today:** `locked_seats`, the `FILL_SEATS` surface,
  `optimised_for: GROUP` and the screen saying so, and *change sides, never seats*. Hand-seating
  somebody in the builder and pressing ⚡ is the same shape and needs no other context.
- **Out of scope:** *opening the builder from an accepted challenge*. It needs a challenge with
  partial acceptances — `matches`. Past the destination rather than unsharp, so it is a scope
  boundary and not fog.

---

## 10. The cross-cutting rule, narrowed

§12 rule 3 — *the card never says in words what it has already drawn* — arrives claiming a test
already asserts it in this codebase's client. **It does not.** There is no matchmaking code in
`frontend_player/`, and the nearest shipped test asserts the **opposite** discipline on
purpose: `radiusPresentation.test.ts` renders 12 km as a figure *and* as *"Across your town"*,
because *"a number in kilometres means nothing to a player who does not think in kilometres"*
and *"the words are the assertion worth having."*

**The rule as written would delete that pattern.** So it is narrowed to what it was protecting
— and the prototype's own implementation says which that is: it filters the **reason list**,
dropping lines that repeat the forecast bar, the Fit chip and the level gap.

> **A reason line never restates a value the card already renders.**

A figure beside its plain-word reading is one fact in two registers for a reader who needs the
second, and this client already decided that deliberately. Stating the rule narrowly is what
makes it testable; stating it broadly is what gets it deleted the first time it fights the
radius pattern.

---

## 11. What the player app owes, when it is built

Recorded here rather than filed, because there is nothing to correct — there is no card yet,
and the UI build is its own effort. The effort that builds these screens inherits a list:

1. **A reason line never restates a value the card already renders** (§10).
2. **`optimised_for: GROUP` is rendered**, in the same voice the app uses to say a forecast is
   provisional — §8.4 asks for this test by name.
3. **No forecast arithmetic** — the client selects among arrangements and renders numbers it
   was given.
4. **No familiar form derived from a nickname**
   ([ADR-0107](../../adr/0107-the-player-card-is-assembled-outside-the-engine.md)).
5. **An unknown evidence kind renders a named gap**, never a shorter list
   ([ADR-0106](../../adr/0106-evidence-vocabulary-is-contract-weights-are-configuration.md) §6).
6. **The animation's count comes from the response** (§3).

---

## 12. What this file does not decide

- ~~**The `unfilled_reason` vocabulary and the doubles objective**~~ — settled by
  [#180](https://github.com/Raketa02/Raketa/issues/180) in
  [`the-group-objective.md`](the-group-objective.md).
- ~~**`INTEREST_TTL`, `OUTSTANDING_INTEREST_CAP`, `PASS_SUPPRESS`**~~ — **set** by
  [#194](https://github.com/Raketa02/Raketa/issues/194) (ADR-0127, ADR-0128). §7 carries the pass
  half; `GET /interest` now returns `expires_at` per outgoing row and the per-sport
  `outstanding` / `cap` pair.
- **The staleness threshold behind `index_stale`** — [#173](https://github.com/Raketa02/Raketa/issues/173).
- **The tag relationship matrix** — [#179](https://github.com/Raketa02/Raketa/issues/179).
- **The Play screens' interface** — out of scope on this map.
- **A notification mechanism** — no context in this repository can push anything; in the map's fog.
