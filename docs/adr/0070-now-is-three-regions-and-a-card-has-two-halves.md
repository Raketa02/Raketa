# ADR-0070 — Now is three regions, and a card has two halves

- **Status:** Accepted
- **Date:** 2026-08-21

## Context

Everything Now needs was decided except the shape it crosses the wire in.
[ADR-0068](0068-now-is-one-request-and-the-caches-serve-the-screens-two-clocks.md) fixed that
there is **one** request and explicitly left the envelope to
[`Raketa02/Raketa#41`](https://github.com/Raketa02/Raketa/issues/41). The slate was blank:
[#6](https://github.com/Raketa02/Raketa/issues/6) established that no route, no schema and no
OpenAPI path exposes any of this today, so every field name was free.

Four constraints arrived from decisions already made, and between them they do most of the work:

- **The phone holds no rules.** [ADR-0053](0053-the-phone-holds-no-rules-and-only-subtracts.md)
  fixes that a client's only derivation is subtracting the current time from a moment it was
  handed. Every question below that could be answered *"the phone works it out"* is answered
  *"the server says so"* instead.
- **Copy is the client's.** [ADR-0041](0041-tone-is-editorial-so-the-wire-carries-a-situation-and-its-facts.md)
  carries `{situation, facts}` and neither the tag nor the tone, because a tag is a display
  string in English on a Polish product.
- **Order is a property of the composed screen.**
  [ADR-0032](0032-order-is-a-property-of-the-composed-screen.md) requires the contract to
  distinguish **compose** from **update**, and forbids an update from moving a card's position.
- **Nothing ticks.** [ADR-0054](0054-now-refreshes-when-asked-never-on-a-timer.md) leaves four
  moments that count as asking, and no timer anywhere.

Two facts found while drawing the envelope changed answers rather than confirming them.

**The screen is three regions, not two.** An offered seat sits in its own block **above** the
enrolled strip ([ADR-0052](0052-a-vacancy-is-offered-not-announced.md), amended by
[ADR-0061](0061-the-invitation-ladder-is-an-order-and-one-open-call.md)) — it is not a match the
player is in and not a suggestion, and it is ordered soonest-to-expire where the strip is
chronological. A shape drawn around the strip and the shelves alone would have had to absorb it
later, and the natural absorption — folding it into the strip — would have sorted a player's
offers by when the game is instead of by when the offer dies.

**Neither client validates the wire at runtime.** Both generate types with `openapi-typescript`
(`make gen-api`, [ADR-0006](0006-backend-owns-api-contract.md)) — types only, erased at build.
This matters twice below: it is why an unknown field costs nothing (see
[ADR-0071](0071-two-fields-with-no-reader-are-not-forwards-compatibility.md)), and it is why an
unknown **situation** is a rendering problem rather than a parse failure.

The alternatives that had to be argued down are recorded in the Decision, because each is what a
later session will reach for.

## Decision

**We will serve Now as three ordered regions, a small set of facts about the viewer, and a card
that is split into the half every phone can draw and the half only a current one can.**

### The route, and what the phone sends

- **`GET /api/v1/now`**, under the same version prefix as every other route in the product. The
  specification set writes `GET /now`, which is a name for the screen rather than an address;
  being the one route outside the prefix is a cost that buys nothing, and this ADR is where the
  shorthand becomes a URL.
- **The request carries the selected sport and nothing else.** In particular it carries **no
  stamp of what the phone is holding**, and the server never answers *nothing has changed*. Now
  is asked for rarely and only on arrival, a pull, or a countdown reaching zero (ADR-0054) —
  every one of them a moment where the player is explicitly asking — and pull-to-refresh carries
  a promise ([ADR-0068](0068-now-is-one-request-and-the-caches-serve-the-screens-two-clocks.md))
  that a saved payload would break. Which sports the bar offers is
  [#51](https://github.com/Raketa02/Raketa/issues/51)'s; that the sport rides on the request is
  fixed here.
- **Switching sport is a new request**, not a filter over a payload holding every sport. The
  alternative pays for a rare act — switching — at the expense of the overwhelmingly common one,
  opening the app, and would run the whole funnel once per declared sport for a screen mostly
  looked at once. ADR-0050 already filters every shelf by sport, so a screen is about exactly one
  sport and its composed order means one thing.

### The screen

**Three regions, each an ordered list of cards, in this order:**

| Region | Order | Floor | Cap | Caption | Tail card |
|---|---|---|---|---|---|
| **Offers** | soonest-to-expire | none | none | no | no |
| **Your matches** | chronological | none | none | no | no |
| **Shelves** | the server's fixed list of five | per shelf | per shelf | optional | yes |

- **The offers block is its own region, not a sixth shelf and not part of the strip.** As a shelf
  it would inherit a floor, a cap, a caption and a tail card into Find — all wrong for it — and,
  worse, become something the server could order *below* a suggestion, when *above everything* is
  the whole point. As part of the strip it would be sorted chronologically, which sorts a
  player's offers by when the game is rather than by when the offer dies.
- **Your matches is not a shelf either.** It re-orders on the player's own action and the shelves
  never do; it has no floor, no cap, no caption and no tail card, where every shelf has all four;
  and it holds a different card. A uniform row type would leave four of its fields permanently
  empty for the strip, and would invite exactly the mistake this map has spent itself avoiding —
  someone giving a player's own matches a quality floor.
- **A shelf carries a code, never a title string.** `bestFit | sameLevel | recentlyViewed |
  newPlayers | newClubs`, and an optional **caption code** rather than a caption sentence.
  ADR-0066 requires the caption to be *composed by the server* and the client to *evaluate
  nothing* — both hold: the server decides whether a caption fires and which one it is, and the
  phone draws the one it was handed. What the server does **not** do is hold Polish. The words
  were never the part that needed to move without a client release; shelf **presence** and shelf
  **order** were, and both stay server-owned.
- **A shelf with nothing is absent; a region with nothing is present and empty.** ADR-0050's
  absence rule is about a **claim** — a row that appears every week saying *nothing worth waiting
  for* is a row players learn to scroll past — and a region makes no claim. Sending all three
  always gives the client one code path, makes the strip's drawn empty state an ordinary render
  rather than an absence to interpret, and removes the most productive bug in this class, which
  is *not there* and *there and empty* being handled in one place and not the other.
- **The tail card is not in the contract.** Every shelf has one unconditionally
  ([ADR-0068](0068-now-is-one-request-and-the-caches-serve-the-screens-two-clocks.md)), so a flag
  would be `true` on every shelf of every screen forever, and putting Find's pre-filter on the
  wire means authoring Find's query vocabulary inside a ticket that is not about Find. The client
  appends the card and routes on the shelf code and the sport it already holds. **This is not a
  rule on the phone**: it derives nothing about matches, it decides where a tap goes, which it
  already does for every button on the screen. When Find lands with a real query vocabulary a
  shelf may gain a typed filter and the local mapping retires — an **added** field, which costs
  nothing (ADR-0071).

**Facts about the viewer ride on the envelope, beside the regions.** In v1 there is exactly one:
the **debt line** — an amount, its currency, and one boolean meaning *this player may not create
a match or book a court*.

- **A boolean, not a list of blocked acts and not the amount alone.** The amount alone would make
  the phone conclude *she owes, therefore the create button is dead*, which is a rule, and the
  phone holds none. A list of blockable acts invents a vocabulary to describe two things that
  nothing else in the product would ever read. The boolean states the consequence, and the phone
  writes the sentence like every other.
- **A screen fact, not a fourth region.** The three regions are ordered lists of tappable cards,
  which is what makes the shape worth having; a region holding one untappable sentence breaks
  that on its first use.
- **The slot is not an invitation.** ADR-0050's rule stands — a row that is neither a thing the
  player is in nor a thing they could join is furniture — and the debt line earns its place on a
  specific argument ([ADR-0058](0058-one-balance-and-it-never-goes-above-zero.md)): the player
  cannot create or book, Now renders the create tab, and without the line they meet the block as
  a bare refusal. **That argument, not the slot, is the entry fee**, and the next thing proposed
  here has to make it again.

**The header is not on this screen.** The greeting and the city come from the *who am I* answer
the app already fetches and holds; `GET /now` carries neither. The city is a fact about the
**player** ([ADR-0063](0063-where-a-player-plays-is-declared-and-precision-follows-the-anchor.md))
and cannot change during a session, because the screen that would change it is out of scope.
Repeating it in two answers is how two answers come to disagree.

### Compose and update

**A compose** is the whole screen: three regions and the viewer's facts. It happens on the four
occasions ADR-0054 names.

**An update** is **the one card that changed, plus any of the two viewer-owned regions whose
contents or order changed, whole.** The shelves are **never** in an update.

- This is what keeps ADR-0032's promise true. Dropping a joined match out of *Best fit* would be
  re-ordering a shelf under the player's thumb; it waits for the next compose. The match the
  player just joined appearing in their own strip is caused by their own tap and is the region
  the tap was about.
- **A region comes back whole rather than as removals.** An accepted offer changes three things
  at once — the offer is gone, the match belongs in the strip, and the shelf copy of that match
  now says *you are in*. The first is expressed by a fresh offers region, the same shape a fresh
  strip already uses. The alternatives were the client inferring the removal — a domain inference
  the phone must not make — or a list of removals beside the list of updates, a second vocabulary
  that must be kept honest against the first forever.
- **A refusal is not a second shape.** Tapping an offer somebody else already took returns what a
  success returns: what is true now. One path on the client instead of two, and it honours
  ADR-0053's rule that a client may stop offering something and may never start — the card that
  comes back no longer offers the seat, and the player **sees** that rather than being told it.
  The one-card answer must therefore be able to say *this card is no longer on your screen*, not
  only *here is its new content*. The player still needs an acknowledgement, and that is a
  sentence the client writes over a screen the server has already corrected.

### A card

**A card is identified by the thing it is about** — a match, a person, a club — never by its
position or by the shelf it sits in.

ADR-0050 permits a match on more than one shelf, so one match can be two cards on one screen.
Under position identity, joining from *Best fit* would leave a live **Join** button on the copy
in *Recently viewed* until the next pull — a button the player's own app would then refuse. Under
thing identity, one answer corrects every copy. It also settles what the card stamp stamps: the
match's card, not one shelf's copy of it, so the future live channel has one thing to compare
rather than five.

**A card is two nested halves.**

| Half | Holds | Read by |
|---|---|---|
| **Spine** | which thing, the moment it is about, where, how much, the fit badge, the emphasis flag, the card stamp | always |
| **Situation** | the situation and its facts (ADR-0041) | only when the client knows that situation |

- **[#42](https://github.com/Raketa02/Raketa/issues/42) owns the situation half and never touches
  the spine.** It decides what the 33 situations carry, against a shape rather than a blank page.
- **A flat card was refused.** It would leave the unknown-situation rule below as a *discipline*
  rather than a shape, and the first person to add a situation-dependent field at the top level
  breaks it silently — an old phone drawing a confirm deadline under a state it cannot name.

**Every card carries exactly one clock slot** — the one moment the card is about, as an instant,
sometimes empty. The client's whole rule is *if there is a moment here, count to it*. ADR-0053
requires the card to name its own moment and left the field to this contract; making it one of
the ordinary situation facts would put a 33-row rule on the phone about which fact is the clock,
and make a 34th situation with a new deadline a client release. The moment may **also** appear as
an ordinary fact where the card prints it as words — printing it and counting to it are different
jobs.

**The moment carries the club's zone beside it.** An `Instant` is UTC and never a clock face
([ADR-0024](0024-instant-as-aware-datetime-minute-coordinates.md)), and the zone is a fact about
the **club** — the clock face a match at it starts on. A phone formatting in its own zone is
correct for every player at home and wrong for every player travelling, which is the worst
available bug: invisible in testing, and aimed at a person ADR-0063 explicitly builds for. A
server-formatted *"Tue 19:00"* was refused twice over: it is copy, and it is the second answer to
a timezone question that `matchmaking.py` already warns disagrees with the first for two hours
either side of a Warsaw midnight. **The header eyebrow is the exception and stays on the device's
clock** — that line is about the player, not about a club.

**Money crosses as integer grosze with a currency beside it.**
[ADR-0023](0023-money-integer-grosze-gross-whole-zloty.md) already fixes the integer; the comma
in *38,00 zł* is formatting and formatting is the client's. The currency ships even though there
is one market, for ADR-0063's own reason: a city field exists precisely so no reader may assume
one market, and a hard-coded currency beside it would assume the thing the city field exists to
prevent. This does not make Raketa multi-currency. It stops the **contract** claiming Raketa
never can be.

**Three card types, not one with holes:** match, person, club. A shelf's code already fixes what
it holds — a shelf's title is its claim, so *New on Raketa* holds people and always will. One
union type would give every person card an always-empty situation half, an always-empty clock, an
always-empty price and an emphasis flag that can never be set, with nothing preventing a later
session filling one in.

**Two spine fields are the composition's judgement, not the match's.**

- **The fit badge is optional.** ADR-0069's degrade leaves *Same level* and *Recently viewed*
  rendering without one.
- **At most one card on the whole screen carries emphasis** (ADR-0051), read off the finished
  composed order rather than recomputed from scores, and **an offer anywhere on the screen
  silences it entirely** (ADR-0052).

Both live in the **spine**, because neither depends on which of the 33 situations the card is in,
and putting them in the situation half would make an old phone lose the badge and the emphasis as
collateral damage — which is not what the rule below chooses. Both are things the client must
never derive, and it now has no way to.

### An old phone meeting a new situation

**A client that does not recognise a situation renders the spine and omits the status line.** The
match, its moment, its club, its price, its badge and its button; everything except the sentence
it has no words for.

ADR-0040's generated union is a **compile** fence — it stops us shipping a client missing a row.
It does nothing for a phone already in somebody's hand, and ADR-0038's own premise is that
installed phones cannot be forced to update.

- **Skipping the card was refused outright.** An app hiding a match the player has paid for is
  the worst outcome on the list and reads as *your app lost my booking*.
- **A server-side compatibility map was refused.** Telling an old phone that a 34th situation is
  really one of its 33 means keeping that table forever and telling the player a small lie about
  the state of their own match.

Losing the sentence loses exactly the thing that is actually missing.

### The stamps

**One monotonically increasing stamp per region, and one per card.** No screen-level stamp: a
screen is never replaced as a unit except by a compose, and a compose is three stamped regions
arriving together.

The scenario they exist for is a pull and a tap racing — a compose composed *before* the action
landing *after* it, undoing in front of the player what they just did. Per-card stamps alone
cannot resolve it, because the race is over **membership and order**, which no per-card value can
express. A single screen stamp would discard a late compose whole, including the majority of it
that was genuinely newer. A region is the unit an update already replaces, so it is the unit that
can be compared.

**Increasing integers, not opaque strings.** The reader they are waiting for is the deferred live
channel ([`deltas/live-delivery.md`](../specs/now/deltas/live-delivery.md)), whose monotonic
acceptance asks *is this newer than what I hold* — a question that needs an order.

### What the wire does not carry

- **No degrade marker.** ADR-0069's fallback is expressed as what it already is: a `sameLevel`
  shelf and cards without badges. A marker would be a fact about our infrastructure printed on a
  player's home screen, and would immediately become a rule the client has to hold about what to
  do differently — when the answer is nothing.
- **No policy version.** ADR-0051 reconstructs what a player saw from the shelf titles and the
  policy version; support is us, reading our own logs. The case for shipping it is an agent
  working from a screenshot, and a screenshot has a timestamp, which is enough to find the
  composition.
- **`serverTime` and `nextTransition` are dropped** — see
  [ADR-0071](0071-two-fields-with-no-reader-are-not-forwards-compatibility.md).

## Consequences

**Easier**

- [#42](https://github.com/Raketa02/Raketa/issues/42) inherits a shape instead of a blank page:
  fill the situation half for 33 situations, never touch the spine, and stop.
- The client has one code path for a compose, one for an update, and one for a refusal, and no
  branch anywhere that asks *did this region come back or not*.
- A 34th situation is additive: new server, old phones lose one sentence on the cards in that
  state and nothing else.
- Three card types mean the person and club shelves cannot silently acquire match machinery.

**Harder**

- **Three regions and three card types is more contract than one list of rows.** The cost is paid
  in the schema and in `make gen-api`'s output, permanently, to buy shapes that cannot express
  the wrong thing.
- **The client now owns two vocabularies of copy** — the 33 situations and the shelf and caption
  codes — and rewording either is an app release. This is the deliberate price of ADR-0041's
  rule; what stayed server-owned is what actually needed to move without a release, which is
  which shelves appear and in what order.
- **The client owns the mapping from a shelf code to a Find pre-filter**, until Find exists and
  can be asked properly. It is routing rather than derivation, but it is a table in two places
  the day Find ships, and retiring it is a job somebody has to remember to do.
- **A card carries a timezone string it will almost never need.** Every player at home renders
  identically without it. It is paid on every card of every screen to be correct for the
  travelling player.
- **The regions must be sent even when empty**, so a brand-new player's screen is mostly empty
  structure — the honest cost of not making the client interpret an absence.

**Neutral**

- The offers region is uncapped and unfloored by ADR-0061, so the payload ceiling in
  [ADR-0069](0069-the-budget-is-two-budgets-and-both-fail-the-build.md) is sized against 29 shelf
  cards plus a strip and an offers block that are both bounded only by what the player is
  actually in. Neither has ever been measured, for the reason ADR-0069 already records: no
  composed Now exists to profile, so the first implementation is also the first measurement.
- Nothing here is built. No route, schema or OpenAPI path exists yet, so this ADR describes a
  contract that `make gen-api` has never emitted.
