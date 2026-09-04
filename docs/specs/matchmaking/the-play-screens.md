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
four more — three from this ticket, and the decline
[#237](https://github.com/Raketa02/Raketa/issues/237) added later. That file's §1 stands as
written for the four that create searches.

| Route | Creates a search | Added by |
| --- | --- | --- |
| `POST /api/v1/searches` | yes | [#170](https://github.com/Raketa02/Raketa/issues/170) |
| `POST /api/v1/lineups` | yes | [#170](https://github.com/Raketa02/Raketa/issues/170) |
| `POST /api/v1/deck` | yes | [#170](https://github.com/Raketa02/Raketa/issues/170) |
| `GET /api/v1/searches/{id}` | no | [#170](https://github.com/Raketa02/Raketa/issues/170) |
| `POST /api/v1/interest` | no | [#170](https://github.com/Raketa02/Raketa/issues/170) |
| **`POST /api/v1/forecasts`** | **no — deliberately** | [ADR-0108](../../adr/0108-a-forecast-is-a-route-not-a-search.md) |
| **`POST /api/v1/passes`** | no | §7 below |
| **`POST /api/v1/prompt-declines`** | no | §2 below, [#237](https://github.com/Raketa02/Raketa/issues/237) |
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
player_card: { nickname, photo_id?, photo_url?, review?, area_code,
               social_tags[], level, band, range,
               player_score?, counted_games?, last_five? }
```

Closed list. `photo_id` and `photo_url` are **omitted together** (not null) when the player has
no photo, and the client draws the generated court poster. **The id is what is stored and the
URL is what is drawn** — minted per response and recorded nowhere, because the client cannot
sign one for another player's photo and `GET /photos/{id}` refuses to
([`the-play-components.md`](the-play-components.md) §9).

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

> **`range` is on the card for the same reason `distance_km` is not.** It is the **likely
> range** — μ ± σ as `rating` published it — and it is a fact about that person alone, which
> is precisely the test ADR-0107 applies. It travels as `{low, high}`, **projected** onto the
> index row from `rating.rating_initialised`, which has carried `range_low` / `range_high`
> all along; it is never derived at assembly, because `likely_range()` returns unrounded
> values and the rounding lives in the engine — deriving it here would put a second set of
> drawing constants one layer further out, which is the defect the boundaries-travel-on-the-
> estimate rule exists to prevent.
>
> **The band's numeric edges stay off the card.** Only the band bar would draw them and it
> lives on the player record sheet, which is out of scope; the glossary refuses them as a
> second range in any case. `band` remains the published name.
>
> The level row that draws all three is [`the-words.md`](the-words.md) §6.4.

**Never on a card, ever:**

| | Why |
| --- | --- |
| a bio, or any free text a player wrote | the platform's first player-authored text field, and a moderation surface out of scope |
| activity recency, at any granularity | row three of §9.5's Liveness table — [ADR-0106](../../adr/0106-evidence-vocabulary-is-contract-weights-are-configuration.md) §5 |
| gender | [ADR-0096](../../adr/0096-gender-preference-mutual-gate-invisible-to-the-scorer.md) |
| a Liveness number | [ADR-0106](../../adr/0106-evidence-vocabulary-is-contract-weights-are-configuration.md) §5 — reasons only |
| a block, a pass or a decline | §21, and [ADR-0109](../../adr/0109-a-read-back-names-what-it-withholds.md) |
| an unsettled case | the matcher never reads `cases`; the hold does its work at the gate |

### The record block, and the one spelling absence has

**Three fields say what the platform has watched this person do**, and every one of them is
**omitted rather than nought** where it has watched nothing
([#306](https://github.com/Raketa02/Raketa/issues/306)).

| Field | Shape | Omitted when |
| --- | --- | --- |
| `player_score` | `int` 0–100, the **published** number — the same figure this player's own profile prints, at the same player-facing weights ([ADR-0140](../../adr/0140-a-player-score-is-what-the-platform-watched-and-two-strands-is-what-it-can-see.md)) | nothing has ever been arranged for them. **Never `0`** — somebody nobody arranged anything for has not failed to turn up |
| `counted_games` | `int` ≥ 1, friendlies excluded, unscored games **included** ([ADR-0137](../../adr/0137-a-result-is-the-record-that-a-game-happened.md)) | none of the counted games was theirs. `games` measures that zero for its own callers and the card does not print one: here *nought games* and *no record* would be one absence in two spellings |
| `last_five` | up to five `WIN` / `LOSS`, **oldest to newest** | nothing of theirs was counted **and agreed**. Fewer than five is a real answer and is **never padded** — the card draws the gap |

**`counted_games` present with no `last_five` is not an inconsistency.** An unscored game is
*an evening, not evidence*: it says these people were on a court and it moved nobody's Level,
so it is in the count and out of the run.

**No dates, at any granularity** — `last_five` is outcomes in order and nothing else. A moment
beside one of them is row three of §9.5's Liveness table, which
[ADR-0106](../../adr/0106-evidence-vocabulary-is-contract-weights-are-configuration.md) §5
refuses. It is asserted centrally over the emitted contract, not per route.

**None of the three comes off the candidate index**, which
[ADR-0111](../../adr/0111-the-index-holds-only-what-a-player-changes-about-themselves.md)
reserves for what a player changes about themselves — and a Player Score, a game count and a
run of form are all the platform's observations *of* them. They arrive **through ports at
assembly time**, on the seam `at_stake` and the nickname already ride: the two `games` facts
through a source of their own, and the Player Score through `PlayerScoreQuery`, **read again
there** ([ADR-0140](../../adr/0140-a-player-score-is-what-the-platform-watched-and-two-strands-is-what-it-can-see.md) §6).

**The second read is the decision and not an oversight.** The engine reads the same port when
the search binds, and that read prices a *term* over everybody who might be scored — it is
bounded by the box. This one prints a *number* and is bounded by the shortlist. Taking the
card's figure off the engine's record instead would make what a player is shown a consequence
of whatever the reliability term happens to carry, and the day that record is narrowed the card
would quietly stop saying anything.

**`at_stake` rides the same seam and sits on the candidate rather than on the card** — it is
a fact about a *pair*, which is `distance_km`'s placement for `distance_km`'s reason. It is the
rating engine's own update rule read forward
([ADR-0139](../../adr/0139-a-confirmed-result-is-evidence-and-a-level-moves-by-what-it-taught.md)),
present in competitive and omitted in for fun — where a counted result is *meaningless* rather
than unavailable — and omitted in competitive only where one of the two holds no rating in
this sport.

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

**And the other three prompts do suppress, on a decline that is a durable row.**
`KEEP_THIS_RADIUS`, `UPDATE_PLAY_INTENT` and `REFRESH_YOUR_TIMES` each go quiet for thirty days
when the player says no, keyed by the prompt's own identity and never by the value it quoted —
so declining *keep 22 km?* also answers *keep 32 km?* next week, because the player answered
about a habit rather than about a number
([#237](https://github.com/Raketa02/Raketa/issues/237)). The dividing line against *Keep these
times?* is not per-search versus loop: it is **whether the condition outlives the act**. An
improvised grid is gone when the search ends; a widening habit, a drift and a week described
months ago are all still true tomorrow, which is why only they can nag. The decline is
`POST /api/v1/prompt-declines` — write-only, append-only, no Origin key — and the sheet says
what it buys.

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
| **Most reliable** | published Player Score | offered on a search whose candidates have one; **a player with no record sorts last, never as a zero** |

*Most reliable* is not a sort that does nothing. Where nobody on the list has a record it is a
control that **is not drawn**: a visible control that reorders nothing is the product lying
quietly, and a sort whose readings are all equal reshuffles the list into player-id order while
carrying nothing. Its condition is a fact about **the search**, re-derived per search rather
than hardcoded, so it appears by itself the moment two candidates carry scores that tell them
apart — and most searches still do not draw it, because most people have no record.

**A read-back draws it from the score the row recorded**, never from one that route goes and
asks for: the record reproduces the answer that was given, so a control it offers has to be
orderable by a reading the row itself holds. A row written before the card carried one reads as
absent and sorts last — which is `distance_km`'s rule, for `distance_km`'s reason.

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

### 5.1 The send re-checks, and refuses whole

**Five facts, re-verified server-side in the send's own transaction.** Four are the
fail-closed gates the read-back already re-evaluates — a block either way, a hold, an account
`users` may not show, and the mutual gender preference — and the fifth is `OPEN_CHALLENGE`,
the one gate deliberately left **soft and out of the read-back** with the send named as its
backstop ([#222](https://github.com/Raketa02/Raketa/issues/222)). Nothing in Play
background-refetches ([#228](https://github.com/Raketa02/Raketa/issues/228)), so the client
cannot have noticed; and the searcher may have built this line-up an hour ago.

**Whole-send, never per-seat.** #221 already refuses a send with nobody new; a partial send
that silently dropped one invitee would hand the organiser an arrangement they did not
choose, which is H-18's harm arriving through the safety check. A refused send writes
nothing, so there is no half-sent challenge to reconcile.

**The organiser's own hold is refused at the entry point**, with the same `account_held` the
search returns. ADR-0130's own consequences settled this shape once — *"refusing them a fresh
search while handing back this morning's would be the hold ending at the one route that
remembers"* — and a hold that stops you searching but lets you send invitations is that hole
with the blast radius pointed at other people.

**Three refusals, in one order.** *Nobody new to invite* (#221, AC-154) comes **first**: it is
a fact about the send's shape, needs no reads, and is true regardless of anybody else's
state — telling an organiser their line-up went stale when they invited nobody sends them
refreshing a screen that was never wrong. Then the other two, and **both are reported for one
press**, because fixing one and being refused for the other is the same interruption twice.

| | |
| --- | --- |
| `line_up_no_longer_sendable` | **New**, `409`. The four fail-closed gates, indistinguishably. |
| the open-challenge refusal | **#221's**, already owed by the aggregate. Made a whole-send pre-check rather than something discovered on the way through. |

**Neither refusal names anybody, and neither carries a payload.** ADR-0130 admits exactly one
field against *nobody may ask who was withheld*, and says in its own words that the single
exemption is what keeps it a rule; a refusal is also the one place this backend has no typed
shape to put a payload in — `AppError.details` is `Dict[str, Any]`, which is invisible to
`test_no_response_carries_a_forbidden_fact.py` and would force the client to hand-write a DTO
against [ADR-0006](../../adr/0006-backend-owns-api-contract.md). So the refusal states the
class of problem and **the client re-reads the two sources it already owns** to find out who:

- `line_up_no_longer_sendable` → **read the origin search back.** The read-back re-evaluates
  the same four gates and marks the withheld rows, and #239 already turns those marks into
  marked seats. Nothing new is disclosed and no second exemption is bought.
- the open-challenge refusal → **read your own challenges.** An open game of the organiser's
  was always theirs to read, so naming the pair costs nothing ADR-0095 protects — #222 is
  explicit that this gate is *embarrassment, not safety*.

This is why `locked_seat_not_available` needs no correction: the send takes the same posture
one screen later, for the same reason, and points at nobody either.

**The remedy reads the origin back; it does not re-run the search.** A line-up is bound to one
`search_id` and `POST /forecasts` refuses anybody who did not appear in it, so re-running the
pool mints a new id the whole line-up must adopt — and its other three seats are only
*probably* in the new answer, since a re-rank or the twenty-row cap can drop a seat nobody
touched. That is H-18's harm arriving through the remedy rather than the fault. Re-running is
the fallback for the one case the read-back cannot serve: the origin search has nobody left to
swap in, and then it is honestly a new line-up.

**When the refusal and the refresh disagree, the court says so at court level.** The send
reads profiles live while the read-back reads the index, so they can differ — most plausibly
on the mutual preference, where the read-back excludes a candidate the partition no longer
holds and the send would read them live. Refused, refreshed, and every seat looks fine is a
dead end; it gets a sentence rather than silence, in the shape §B's shortfall statements
already use on this screen. **The send is not moved onto the index to close it**: that would
buy a rare confusing screen at the price of a safety gate inheriting index staleness, which is
the wrong direction on the one class of check that must not be stale.

**The mutual path runs the same check, and refuses by minting nothing.** `resolve_origin` has
**no freshness bound** — `SearchStore.find` reads any search of yours, ever, and the record
*"is immutable and never expires"* — so a *Let's play* can cite a month-old deck deal, and
#222 opens the mutual-born challenge **inline**. Two stale yeses with a block taken since
would otherwise walk a challenge past every gate in the product. There is no organiser
standing there and no screen to refuse to, so the check's whole observable is that **no
challenge exists afterwards**.

**One judgement, three callers.** `gender_satisfied` says in writing that it takes a row
rather than a context *"because the same gate is evaluated in two places… and a second
implementation of a mutual safety gate is exactly the thing that ends up satisfied in one
place and not the other."* The send makes three, and the arrow runs `matchmaking → challenges`
so the third cannot import the first. The **predicate** moves to `player_profile`, beside the
two enums it reads; the **reading** stays with each caller, because the docstring's fear is
about the rule and not about the source — and the send's should be live profiles. `challenges`
declares its own hold port with its own empty provider: a duplicated *null object*, which is
not the thing the fence was guarding. A platform-safety context owning all of this is the
honest long answer and is **not** taken here — it is a bounded context for two predicates, and
it would need its own record.

**No row is written for a refused send.** #237's test is whether the outcome is recoverable
from anything else, and here it partly is — the search record holds the line-up, `challenges`
holds the sends, and a refused send is the difference. More to the point, a prompt decline is
a player's declared habit and this is a race between two clocks; counting races is
instrumentation, which this map already holds as fog.

**What proves it.** Three demands through the `Challenge` aggregate: a send refused with an
invitee blocked in either direction, asserting **no challenge exists afterwards** — the
whole-send rule is provable only by the absence; a send refused on the pair rule where the
open challenge is in **another sport**, which is #221's across-sports rule and the thing a
build session is likeliest to get wrong; and a mutual formed from **two stale searches with a
block between them, minting nothing**, which is the only evidence the deck path was decided at
all.

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
a silently shorter list ([ADR-0106](../../adr/0106-evidence-vocabulary-is-contract-weights-are-configuration.md) §6),
and so is a `DegradedReason` it has never seen.

**A stood-down term is not a term row, and it says whose gap it is.** It has no weight, no
value, no contribution and no evidence — four of a row's five cells — so drawing it greyed
invents the shape of a reading that does not exist. The live terms are the rows; beneath them
sits a **not-counted block**, a list and not term rows, and each line pairs the term with its
`reason` ([`the-two-contracts.md`](the-two-contracts.md) §4). The client writes the sentence
and the engine names which: `INTENT_ALIGNMENT` and `SOCIAL_VIBE` under one code are two
different sentences, and a client deriving either from a bare `Term` would be an engine rule
in TypeScript.

**Two tiers, and the platform's own is stated once.** The per-person gaps —
`NOTHING_FROM_YOU`, `NOTHING_FROM_THEM` — sit in the candidate's not-counted block, because
they are facts about these two people. `NOT_YET_ON_THIS_PLATFORM` is a fact about the platform
and is drawn **once, in the footer beside the version stamps**; otherwise reliability's line
prints identically on twenty cards and reads as twenty separate shortfalls. Suppressing it
from the wire instead was refused: it is the renormalisation basis, and *a 78 built on four
terms and a 78 built on seven are different readings of the same number*.

**Never:** a Liveness number, a near-miss row, a pre-gate pool count, another player's
breakdown.

**The read-back re-verifies and states what it withholds**
([ADR-0109](../../adr/0109-a-read-back-names-what-it-withholds.md)). The record is immutable;
the response is the recorded answer **plus live gate state**. It does **not** name the gate
([ADR-0130](../../adr/0130-a-withheld-row-is-stated-and-the-gate-is-not-named.md)) — the row
says only that it is withheld, and carries no person. The round-trip test asserts both
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
7. **Nothing in Play retries without the player asking.** Every act in this tab is a
   mutation, and mutations already ship `retry: false`; the read-back of a search is the
   one exception and it gives the default up too. An automatic retry the player cannot see
   is a manual retry they cannot reach — it delays the *Try again* by a full timeout — and
   the retry itself belongs to the **act that failed**, never to the screen it failed on.
   That last clause is load-bearing: a search and a read-back are two acts with two ids, so
   a *retry* that re-ran the search would mint a new one and orphan the line-up bound to
   the old. **No record id, re-fire the `POST`; a record id exists, re-read** — the client
   holds that as `features/play/domain/retryTarget.ts`. Placement follows from it rather
   than being chosen per screen: **three of the four waits reuse a control the screen
   already has** — Find a game's *Search*, the court's ⚡ fill, and the pool's re-read — and
   **only the forecast gains one**, because a player who has stopped changing seats would
   otherwise sit with no number and no way to ask again.
8. **The send fails when offline; the deck's two pause.** Both are correct, and the test
   that separates them is *does this act carry a deadline the player chose*. A challenge's
   answer window is derived **at send** (§G1's answer), so a send deferred to the next
   reconnect carries a deadline nobody picked — the tap and the send must be one moment. A
   pass is an append-only row and a mutual-born challenge has no window at all, so a queue
   of them draining on reconnect is the behaviour you want. Two `networkMode` values in one
   tab is deliberate; left unwritten, the next reader unifies them.
9. **A refused send is followed by a re-read, never by a payload.** The refusal names the
   class of problem and nobody in it (§5.1). `line_up_no_longer_sendable` is followed by
   reading the origin search back and marking the seats its withheld rows identify;
   the open-challenge refusal is followed by reading the player's own challenges. A client
   that renders a name straight off a refusal has found a shape this contract does not have.
10. **The pre-send sheet names no duration.** `SH.propose` states the irreversibility and
   nothing about how long the wait is; the real deadline is per seat and arrives after the
   send, rendered from that seat's own `answer_by`
   ([`the-words.md`](the-words.md) §14, §21).

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
- **The Play screens' interface** — out of scope on *this* map, and taken up by the next one
  ([#217](https://github.com/Raketa02/Raketa/issues/217)):
  [`the-words.md`](the-words.md) owns every sentence and every accessible name, and
  [`the-play-components.md`](the-play-components.md) owns where one component stops and the
  next begins.
- **A notification mechanism** — no context in this repository can push anything; in the map's fog.
