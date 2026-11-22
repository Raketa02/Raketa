# ADR-0161 — The game screen draws its court's pairing, read beside the game and never on it

- **Status:** Accepted — **what a friendly draws narrowed 2026-11-22 by
  [ADR-0207](0207-for-fun-is-built-by-shared-social-tags-and-every-for-fun-game-carries-a-social-vibe.md)
  §5**: a For-fun game draws the **Social vibe card**, read from the same pairing, where it drew the
  forecast with *A friendly — nothing moves.* The pairing still sends the forecast, for the apps
  already on phones, and a counted game draws the forecast and its stakes as before.
- **Date:** 2026-09-11
- **Extends [ADR-0143](0143-the-challenge-is-the-gate-and-the-card-is-recomputed-for-the-reader.md)
  a third time** — the third use of *this game has not happened*, after the challenge card and
  the plan — and **narrows its §8** to the arrangement's screen: `ON` still draws no card on
  the *challenge*, and the game it became now draws a pairing of its own, through a port.
- **Amends [ADR-0149](0149-a-game-is-composed-at-the-surface-and-the-chat-door-is-a-join.md)
  §6**: *no pairing, Fit, level, band, confidence or `at_stake` is drawn on `GameScreen`* is
  narrowed to *none of it is drawn from `GameSchema`*. The forecast, the split, what is at
  stake and each seat's Level are drawn from `GET /games/{game_id}/pairing`; a Fit is still
  drawn nowhere on a game.
- **Amends [ADR-0141](0141-a-game-names-its-court-and-the-court-is-the-gate.md) in one
  sentence**: the seat on `GET /games` still carries the handle and nothing else; a seat's
  Level is read *beside* the game, through a port, for the duration of `AWAITING_ENTRY`, and
  ADR-0141's *no `player_card` to hang them on later* stays true.
- **Settles [#346](https://github.com/Raketa02/Raketa/issues/346) the other way**, on the
  argument that issue itself named as the one that would win, by the author's decision in
  [#410](https://github.com/Raketa02/Raketa/issues/410). Built by
  [#412](https://github.com/Raketa02/Raketa/issues/412).

> **Note — the Classic play removal (2026-10-06, [#569](https://github.com/Raketa02/Raketa/issues/569)).** The challenge card, `PairWithACourt`, the candidate index and the Match Fit ranking are gone, so §3's identity with the challenge card, §2's index-and-ledger provider and Fit mode, and the Consequences that compare two at-stake figures describe nothing. The pairing is now read side against side from rating's estimates through `forecast_the_sides` — the engine's `forecast_and_split` under the live ruleset's balance rules — with no index behind it (#575), the same reading a Games card makes of the same people. §1's route, court gate and `AWAITING_ENTRY` lifetime, §2's port in `games`' own words, §4's absences and stakes, and §5 stand.

## Context

**The Planning details design draws two blocks a game screen refuses.** `BALANCE FORECAST` —
two side strengths, a gap, a percentage, *If you win / If you lose* — and `PLAYERS`, a row per
seat with a Level, a band and a certainty. Three records refused them by name: ADR-0141 (*a
seat carries a handle and nothing else about the person*), ADR-0143 §8 (*`ON` draws neither …
a card here would be a second, worse copy of the game screen*), and ADR-0149 §6, which upheld
both on the game screen. #346 asked whether the refusal should stand and closed *wontfix*.

### What #346 decided, and why it does not hold

The *wontfix* rested on reading ADR-0143 §2's reason for admitting a card as **two conjoined
clauses** — *the game has not happened, the values genuinely are as-of-now, and the person
reading is doing precisely what a searcher does: deciding about a game that might happen* —
and finding that only the first survives on a game screen. Everybody has accepted; nothing is
left to decide; *a forecast exists to help you decide whether to play somebody, and on this
screen you have already decided*.

That argument mistakes what the forecast is **for**. A forecast is not a decision aid that
happens to be honest; it is a claim about a game, and its honesty is the whole of its
admission. ADR-0143 §3 is where the values come from and §2 is why they may be shown, and §2's
test is stated on the *values*: they are admissible because they *mean exactly what a card
means*. A Planning game has not happened, so a forecast on it is exactly as true as the same
forecast on the challenge that became it — the same four people, the same ruleset, the same
number. #346 itself wrote the sentence: *the honest case for the forecast is that a Planning
game has not happened, which is ADR-0143's own reason for allowing a card on a challenge. If
that argument transfers, the refusal is narrower than it reads and the reversal is an extension
of ADR-0143 rather than a contradiction of it.* It transfers. What the *deciding* clause
governs is the card's **lifetime** on the arrangement — it stops when the deciding does — and
that clause is untouched: the *challenge* in `ON` still draws no card. What it does not govern
is a different screen, about a different record, that is honest for a different reason.

What the four remaining objections in #346 priced is real and is paid rather than argued away.

- **`GameSchema` carries no pairing**, and it still does not. ADR-0149 §6's own consequence
  named the cost of refusing — *what is bought is that no port from `games` into `matchmaking`
  has to exist* — and this record pays exactly that: one port, in `games`' own words, signed
  on the matcher's side of the arrow. #346's *out of bounds* — *anything that puts a pairing on
  `GameSchema` rather than behind a port* — is honoured.
- **ADR-0143's apparatus is not built a second time.** The read goes through the challenge
  card's own use case, so the challenge card and the game screen come to one number for one
  court because they are one computation. §3 below is the identity, and a test asserts it.
- **An as-of-now claim on a record read for as long as the game exists** is answered the way
  ADR-0143 §8 answered it for the arrangement: by a **lifetime**. The read answers only while
  the game is `AWAITING_ENTRY`, and refuses afterwards. A game that has happened, or that never
  will, has no pairing to read.
- **`at_stake` is singles only on the client** because *a win against one named person isn't a
  thing that exists until the other three seats are known*. On a game the other three seats
  **are** known — the line-up is frozen at the plan — and §4 prices it the way the result will
  be priced.

## Decision

**We will answer the game screen's pairing from a new route on `games`, gate it on the court,
compute it for the reader through a port `games` publishes and the matcher signs, and answer
only while the game has not happened.**

### 1. A new route, beside the game and never on it

`GET /games/{game_id}/pairing` answers, for one game and for the person reading it:

```
GamePairingResponse
  read_at:   instant
  forecast?: { pct, sigma_group, provisional, assumption }   — omitted together with split
  split?:    { your_side, their_side, gap }                  — in the reader's direction
  at_stake?: { win_delta, loss_delta }                       — the reader's own
  seats:     [ { player_id, level, band, range: {low, high}, confidence } ]
```

`GET /games` is untouched: the seat there carries a handle and nothing else, and the list
stays the cheap read ADR-0143 §1 kept it. The pairing is opened by a tap and costs a
cross-context read, which is the bound ADR-0141 objected to losing and the one ADR-0143 §1
already accepted for the detail screen.

**Who may read it.** Only somebody on that court — `404 game_not_found` otherwise, one code
for two cases, on `challenge_not_found`'s argument verbatim: a read keyed on an id is the
shape a directory is probed through, and separating *no such game* from *not your game* would
answer *is this id real* about four strangers' evening. The acts on a game keep their `403`;
an act is made by somebody holding an id the list already gave them.

**When.** Only while the game is `AWAITING_ENTRY` — `409 pairing_is_history` after. After
*we played* the values are a claim about people made from a stale record; after the entry
window closed on silence there is no game for them to be about.

### 2. The port is `games`', and the arrow keeps its direction

`games/domain/ports.py` declares `CourtPairing` —
`pairing_for(sport, kind, line_up, reader_id) -> Pairing | None` — in **games' own
vocabulary**: `GameSide`, the kernel's `Sport`, and four types declared there (`SeatLevel`,
`CourtForecast`, `CourtSplit`, `LevelDeltas`). No `Forecast`, no `Split` and no `Stakes` is
borrowed from the engines or the matcher, because a provider that reached for the type one
directory over would be the second-spelling trap the import contract's own comment names.
`games` may not import `matchmaking`, and does not; the existing `.importlinter` contract is
unchanged and is the proof of direction.

The adapter, `matchmaking/infrastructure/games_court_pairing.py`, lives on the matcher's side
of the arrow — `OriginSearchQuery`'s seam, `CourtPairingQuery`'s seam, one screen later — and
is wired in the composition root and enrolled on a register of its own,
`app/bootstrap/game_demands.py`, on the rule that a new consumer gets a new register. It
recomputes rather than replays, fails closed with no trace, and answers the three ways ADR-0143
§6 named: present; absent because there is nothing to compute; absent because it could not be
read.

**Two providers stand behind the one port, and each fails on its own.** The forecast and the
split are the matcher's and need the index and the ledger behind Redis; the seats' Levels and
the stakes are the rating context's and need the streams alone. A process with no index, or an
outage on the matcher's side, costs exactly the two matcher blocks — the adapter is built with
no arranger rather than replaced by a null object — because a screen that dropped four Levels
over an index that was behind would be conflating two providers' availability. The port takes
no instant: nothing it answers is folded against a clock, and the one thing bounded by one —
the index's staleness — is read against the matcher's own.

**`kind` crosses the port.** A friendly is never priced: what a counted result would do to a
Level is not a question about a game that will not be counted, and the adapter refuses it by
not asking — and the use case holds the same rule as an invariant on what comes back, so a
provider that priced one anyway is loud rather than rendered. The mode the matcher's Fit runs
under is the game's kind and not the reader's declaration — a challenge card resolves a
mutual-born challenge through the deck's rule because that surface asked nobody what kind of
evening it was; a game has answered at the plan.

### 3. One apparatus, and the identity is by construction

The adapter reads the challenge card's own use case, `PairWithACourt`, and translates. That is
the whole of *do not build a second forecast apparatus*: the forecast the challenge screen drew
while the court was being arranged is the forecast the game draws once the line-up completes,
and `test_the_games_forecast_is_the_challenge_cards_forecast` says so over HTTP.

The one change to that use case is that it stops discarding the split. `arranged(…)` always
returned the two side strengths beside the percentage; the card printed only the percentage
and threw the rest away. `PairedSeat` now carries the whole `Arranged`, and the court's
arrangement is a pure module function — `arrange_the_court` — that both the card and the
determinism probe call, because the walk it makes is the one place a court could be arranged
differently on two processes (ADR-0105).

### 4. Three absences, and what each one is

**`forecast` and `split` are omitted together**, because they are one computation, and they
are omitted when the pairing cannot be computed: the reader holds no rating or no declaration
in the sport, or a seat the index cannot describe. **There is deliberately no reason beside the
absence.** ADR-0143 §6 gave the challenge screen three answers because *an outage drawing the
identical absence as an unrated sport* is a collapse a person answering a challenge is owed
better than. The game screen is not an answering surface — there is no button behind the
block — and #410 decided it draws nothing and says nothing. The two remain two values on the
port: a `Pairing` with nothing in it, and `None`; the log tells them apart and the wire does
not.

**Omitted, never provisional.** A line-up is frozen at the plan, so no side is short today and
`provisional` is always `false`; the field is kept because the shape is the court's. When a
seat can be open (#416), the answer is an absence: `arranged` reads a short side *as if the
missing player matched the one beside them*, which is honest on a court still filling and a
half-read forecast on a game whose whole line-up is known — exactly the thing #346 argued
against.

**`at_stake` is omitted on a friendly** — *meaningless rather than unavailable* — and where the
rule has nothing to move or nothing to price against. **It is priced side against side.** The
challenge card prices *you against this person* with the sport's share applied, because a
card is drawn before the other seats are known and averaging against an imaginary partner
would invent the very thing the read has no basis for. On a game every seat is known, and the
result will be priced the way `settle_results.py` prices it: each side folded to one player by
`one_side`, the pair read off that, the same pair for everybody on the side. A game screen
printing the head-to-head figure in a four would promise a figure the update then contradicts,
which is the one thing *at stake* exists not to do (`CONTEXT.md`: *it is not a preview of the
rule; it is the rule*). So `AtStakeQuery` gains a court-shaped read,
`counted_game_deltas_on_court`, signed by the same adapter that signs the pair read, and the
demands suite holds it to `rating_after`'s own stakes. In singles the two readings are one
number and the suite says that too.

**And it mirrors the rule about an unrated seat rather than improving on it.** `settle_results`
folds a side over the people on it who hold a rating and moves the rated ones; it refuses only
when a whole side holds no Level — *there is nothing to price the other side against*. So a
court with one unrated opponent is priced against the rated opponent alone, because that is
what a confirmed result would do, and the absences are the update's own two: the reader
unrated, or a whole side unrated. A read that omitted the half-rated case would be a preview
of the rule and not the rule. The forecast is still absent on that court — a Level the matcher
cannot describe is a side short, and §4's first rule holds — so the screen may draw the
stakes with no forecast beside them, which is two providers answering two questions.

**`seats` names whoever holds a rating in the sport**, in the court's own order, from
`rating`'s **published** read — a third method on `RatedPlayerQuery`, `published_for`: the
batch's shape with the record's payload, so a seat prints the band's published name and the
range the engine rounded and derives neither. Not from the index, which is the matcher's
projection for ranking and holds only what a player changes about themselves; a seat's Level is
a fact about a person printed beside their name. A court with an unrated member still names the
rated ones.

### 5. Nothing is re-gated, and the court is the whole of the permission

The four fail-closed gates ran when the challenge was minted and are not run again — ADR-0143
§2's rule, and ADR-0141's *the court is the gate*. What makes that safe is the recompute: a
seat that cannot be priced today has no figure, and the same absence is drawn for every cause.

## Consequences

**Easier**

- **The Planning details screen can draw its two richest blocks**, which #410 designed and
  #346 had closed, and it draws them from numbers that are the challenge card's own.
- **The next surface that wants a court priced for somebody already on it starts from §2** —
  a port in its own words, the matcher's use case behind it, the lifetime stated — rather than
  from ADR-0143's *`ON` draws neither* read as a rule about every screen.
- The route, the schemas and the two port widenings are additive; nothing shipped breaks.

**Harder**

- **`games` now makes an outward demand on the matcher**, which ADR-0149 §6 had bought its way
  out of. The port is one method wide and declared in `games`' own types, and the composing
  adapter is the third of its shape — but it is a real edge, and the next person to widen it
  should say so. It is on a register of its own, `game_demands.py`, which is the tenth and the
  rule for the next: a consumer's demand is its own kind of claim, filed on its own list.
- **The at-stake figure on a doubles game is not the at-stake figure on the challenge card for
  the same two people.** §4 is why, and the ADR states it rather than hiding it: the card
  prices a pair, the game prices a court, and the game's number is the one the result will
  deliver. A client drawing both beside each other would have to say which is which.
- **Two more reads per screen.** The pairing pays the whole Fit stack over the court plus a
  court's worth of rating replays for the seats and again for the stakes. It is opened by a
  tap and answers only in one standing, so the cost is bounded by open games rather than by
  history.
- **The wire draws one absence for two causes**, and a reader who wants to know whether the
  matcher was down or the reader is unrated cannot tell from the screen. #410 decided that;
  if a later surface needs the code, the port already carries the distinction.

**Neutral**

- `PairWithACourt` grew nothing a challenge reads — the split it now carries was always
  computed — and `NOTHING_TO_COMPUTE` moved onto the use case that raises it, where both
  adapters over it read it from.
- The client change is #415's session and #415's commit, with `make gen-api` between them, as
  the contract invariant requires; this record commits the regenerated contract and the
  client's generated types together.
