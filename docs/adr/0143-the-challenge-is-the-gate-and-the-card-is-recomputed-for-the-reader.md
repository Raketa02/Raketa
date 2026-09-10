# ADR-0143 — The challenge is the gate, and the card is recomputed for the reader

- **Status:** Accepted
- **Date:** 2026-09-07
- **Extends [ADR-0141](0141-a-game-names-its-court-and-the-court-is-the-gate.md)**, whose
  argument transfers whole and whose two refusals do not. That record settled what a
  **record of a game that happened** may say about the people in it; this one settles what
  an **arrangement still being decided** may, and the distinction it turns on is the one
  ADR-0141 left implicit.
- **Applies [ADR-0107](0107-the-player-card-is-assembled-outside-the-engine.md)** — the card
  is assembled outside the engine, and §4's *nothing may derive a familiar form from a
  handle* is untouched.
- **Cites [ADR-0095](0095-block-directed-record-symmetric-effect-gates-fail-closed.md) §7
  and §8** for the gate, in the same shape ADR-0141 cited them.
- Settles [#328](https://github.com/Raketa02/Raketa/issues/328) on the map
  [#321](https://github.com/Raketa02/Raketa/issues/321).

## Context

**`a_challenge_for_you.png` draws a candidate card, and `ChallengeSchema` returns none of
it.** The wire carries `challenge_id · sport · mode · window · organiser_id · standing ·
opened_at · seats`, and `SeatSchema` is `side · player_id · answer · answer_by`. The design
draws a poster, a handle, a *For fun* pill, `Squash 2,44 · band 2,18–2,70 · 3,1 km · Score
91`, an availability line, a deadline with a countdown, a Fit, a predicted balance, four
reasons and one concern. **There is no screen today that lists a challenge for you at all**:
`GET /challenges` has exactly one caller, and it is the pair rule's naming after a send was
refused with `open_challenge_stands`
([#326](https://github.com/Raketa02/Raketa/issues/326)).

So the question is not which fields to add. It is **whether a person being asked to play may
be shown as a card**, and ADR-0141 appears to have answered *no* four weeks ago.

### ADR-0141 refused exactly this shape, and the refusal has to be read for its reason

Its rejected alternative is written in as many words: *"A `player_card` on the seat, as
`CandidateSchema` carries. Rejected on ADR-0107's own rule read forward: a card is what a
**searcher** reads to decide about a game that might happen, and every value on one is
as-of-now. Stapled to a record of an evening in the past it makes a Level, a band, a likely
range and a run of form say something they do not mean."*

**Every clause of that is about the past.** A `GET /games` row is a record of an evening that
already happened; a card beside it claims as-of-now things about an as-of-then event, and the
mismatch is the whole objection. A challenge in `AWAITING_ANSWERS` is the other case
entirely: **the game has not happened**, the values genuinely are as-of-now, and the person
reading is doing precisely what a searcher does — deciding about a game that might happen.
ADR-0141's rule, read forward rather than quoted, **admits** the card here.

Its second refusal — *a route that turns ids into names* — does not transfer either, and for
a reason that is easy to lose. It was refused as *"a route keyed on a stranger's id answers*
is this id real*, which is precisely what the single `you_were_not_on_this_court` code exists
to refuse."* A route keyed on a **challenge** id answers nothing of the kind, and the
refusal it needs is already written on the two answer routes: `challenge_not_found` — *"no
challenge of **yours** has that id. One code for two cases — it does not exist, or you are
not on its court — because separating them would answer* is this id real *about a stranger's
evening."*

### Three facts about the record that decide where the values come from

The obvious shape is to stamp the organiser's shortlist row onto the challenge, or to have
the invitee re-read the search it came from. Both are dead, and the second and third reasons
are not visible from the schemas.

**The invitee cannot read the organiser's search.** `GET /searches/{search_id}` is *"a
searcher may read their own search and nobody else's"*, and `search_not_found` is what
everybody else gets. The one person who most needs the screen has no access to the record it
would be built from.

**A challenge born of a mutual yes has no search at all.** `challenges/domain/origins.py`
is `SentFromSearch | SentOutsideASearch` — *"two answers, and never a third"* — and a
deck-born challenge carries `OUTSIDE`, with no `search_id`, no position, `mode: null` and
`window: null`. The map's Decision 9 holds that such a conversation is the same conversation
as any other; a design that leans on the search leaves this one blank.

**The Fit is asymmetric, and the reverse one was built not to be published.**
`shortlist.py` records `Reciprocal(fit_ab=…, fit_ba=…)` over the shortlist after the floor,
and `_searcher_as_candidate` sets the searcher's own reliability to `None` **deliberately**:
*"the reverse Fit exists to price how good a bet the searcher looks from the other side, and
the module reads a Player Score for candidates rather than for the person searching."* It
feeds the `RECIPROCAL_ASYMMETRY` liveness signal and reaches no wire. So the design's *"Match
score for you — + 74"* can be **neither stored figure**: `fit_ab` is the organiser's reading
of the invitee printed under a label that says *for you*, and `fit_ba` is a knowingly
incomplete number that was never meant to leave the engine.

## Decision

**We will answer the detail screen from a new route on `challenges`, gate it on the challenge
rather than on the reader, recompute the pairing in the reader's own direction, and draw it
only while the arrangement is still being decided.**

### 1. A new route, and the list stays cheap

`GET /challenges/{challenge_id}` answers one challenge richly. `GET /challenges` keeps its
shape and gains two fields (§7).

Widening `ChallengeSchema` was refused on ADR-0141's own cost objection. That record priced a
card at *"a profile read and an object-store `HEAD` per person"* and called it *"the most
expensive shape by a distance … bounded today by a shortlist of twenty."* On a list that is
*"every challenge you hold a seat in"* with **ended ones deliberately in it**, the bound is
somebody's whole history of being asked. The detail is opened by a tap, so the second round
trip is a cost nobody perceives, and the list keeps answering the question it has today.

The route's refusal is `challenge_not_found`, unchanged and for its written reason.

### 2. The challenge is the gate, and nothing is re-evaluated against the reader

The four fail-closed gates — a block either way, a hold, an account that may not be shown,
and the mutual gender preference — ran over every pair of the court in the send's own
transaction (`court_safety.py`'s `admits`). **They are not run again.**

This is not economy: `CourtSafety` lives in `challenges` and a re-gate is buildable today on
ports that already exist. It is **the rule the answer routes already state**, applied to the
screen the answer is made on: *"Answering is not gated. The gates run when a challenge is
minted, because that is the act that puts two people in front of each other; refusing an
answer on one would tell the answerer that something changed about somebody else on the
court, which is the one thing a safety gate may never say."* A card that vanished from behind
two buttons that still work is that same disclosure by a slower route, and ADR-0095 §8's
*"the other side sees no trace anywhere in any response"* names it exactly. §7 supplies the
other half: a block is **forward-looking** and *"does not reach into a game already agreed or
a chat already open"* — an open invitation is an arrangement the reader is already inside.

Both mutual gates were passed **in the reader's own direction** at mint, by construction: the
gender preference is mutual, and a block is symmetric in effect. *The challenge is the gate*
is therefore a permission the reader holds themselves, not one inherited from the organiser.

**The disanalogy with ADR-0141 is real, and §3 is what answers it.** A handle on a past game
is what these people already called each other; a card is as-of-now, so re-gating nothing
would in principle show a live photograph, a live Level and a live area to somebody the other
party has since blocked. What makes that safe is that the pairing is **recomputed rather than
replayed**: a card that cannot be assembled today has no card. That is fail-closed **without
leaving a trace**, because the same absence is what an unrated sport and an outage produce
(§6).

### 3. The pairing is recomputed at read, in the reader's own direction

Nothing is copied at send and nothing is replayed. The screen's pairing values are computed
when the screen is opened, for the reader, against the person who asked them.

This dissolves the staleness question rather than answering it — there is no stored figure to
go stale — and it is the only shape that runs the **same code path** for a challenge born of
a search and one born of a mutual yes. It is also the only shape under which *"Match score
for you"* is true: the number printed is the reader's own, and neither `fit_ab` nor `fit_ba`
is ever published.

The facts that are genuinely about the **pair** are not computed twice from opposite ends.
`evidence.py` states the principle — *"overlap is a fact about a pair where a calendar is a
fact about a person"* — and `_searcher_as_candidate` already reuses the pair's combined
uncertainty and distance rather than recomputing them, *"two chances to disagree about one
number."*

**The cost is a real absence and is stated rather than hidden.** A search refuses with
`sport_not_rated`, `play_intent_not_declared` and `player_profile_not_committed`. **A reader
who holds no rating, or has declared no intent, in the sport they were challenged in has no
pairing to be shown** — and being asked to play a sport you never declared for is how this
feature works, not a corner of it. The screen draws the arrangement and the handle, omits the
pairing block, and does not apologise for it.

### 4. One port, one question, one set read, and `challenges` never touches the photo store

The seam is `OriginSearchQuery`'s, unchanged: the port is declared in
`challenges/domain/ports.py`, signed by an adapter on the matcher's side of the arrow in
`matchmaking/infrastructure/`, and wired in `app/bootstrap/composition.py`. `challenges` may
not import `matchmaking`, and does not.

**One question and not three**, carrying that port's own sentence: the card, the pairing and
the photo link come back **together**, because *"a caller that asked which sport, which window
and where did each of them sit separately would be three reads of one immutable record, and a
court assembled from two of them and refused on the third."*

**Asked once for the whole court, and the union handed over sorted** — ADR-0141 §4 applied
unchanged, including its ordering rule, which
[ADR-0105](0105-determinism-is-a-set-iteration-problem-in-python.md) §1 states on the
collection rather than on what happens to be observable *"because what is safe today is what
changes silently."*

**The photograph crosses, and it is minted where the photo store already is.** `photo_url` is
a short-lived signed link minted per response by `CardPhotoLinks`
(`matchmaking/infrastructure/card_photo_links.py`), and the adapter signing this port mints it
there, exactly as the shortlist, deck and line-up routes do. Refusing the photograph would
make **the person who asked you to play more anonymous than a stranger in your deck**, which
is the wrong way round. `photo_id` and `photo_url` are present exactly together; no photo
means the client draws the generated court poster, which
[ADR-0134](0134-the-poster-draws-a-player-and-no-value-is-invented.md) has it choose by hash
and which needs nothing from the wire.

### 5. `challenges` spells its own schema, and it is narrower than the card

`PlayerCardSchema` and `ForecastSchema` live in `matchmaking` and appear nowhere else; there
is no shared presentation-schema home and this record does not invent one. `origins.py`
already made this call and wrote the argument, which transfers verbatim: *"deliberately a
second spelling … `challenges` may not import `matchmaking`, so the alternative to two
spellings is the matcher owning the vocabulary of the context that was built to take it off
him."*

**Two blocks, because they have two different authors.**

- **The person** — the whole handle, `photo_id` + `photo_url`, the coarse area, the Level,
  the band, the likely range, and the Player Score.
- **The pairing** — the Fit, the whole-kilometre distance, the scored terms ranked by
  contribution with their evidence, the degraded terms, the concerns, the forecast, and what
  is at stake.

**What is refused, each for its own reason.** `liveness_reasons` answers *why did this person
move* and `inclusion_reason` answers *why are they in the list at all* — **neither question
exists when somebody asked you directly**, and there is no list. `modifiers` is engine
internals. `counted_games`, `last_five`, `social_tags` and the photo `review` are card
furniture this screen does not draw.

**The degraded terms ship even though no *Why?* sheet is drawn over them**, because their own
contract is the reason: *"without it a Fit is uninterpretable — a 78 built on four terms and a
78 built on seven are different readings of the same number."* Printing a Fit without its
renormalisation basis is the exact failure that field exists to prevent, and the alternative —
printing no Fit — throws away the one number the screen exists to give.

**What is at stake ships**, on the card's own rule unchanged: omitted in for-fun where a
counted result is meaningless rather than unavailable, omitted when either player holds no
rating in the sport, and **never a pair of zeros**. It is not in the design. *What a counted
game against this person would do to your Level* is more useful when deciding whether to
accept than when browsing, which is the only place it appears today.

**The Player Score is the card's field unchanged** — *"the published figure and never a
re-derivation of it"*, omitted where the platform has watched nothing and **never `0`**
([ADR-0140](0140-a-player-score-is-what-the-platform-watched-and-two-strands-is-what-it-can-see.md)).
The decision it forces is about the **row**: the design's `Squash 2,44 · band 2,18–2,70 ·
3,1 km · Score 91` draws a figure most players do not have, so the segment disappears rather
than reading `Score 0`.

**The bio stays refused, and the refusal is stronger here than where it was written.**
`PlayerCardSchema` says *"No bio and no free text of any kind, ever"*, and
[#218](https://github.com/Raketa02/Raketa/issues/218) recorded why: it would be the
platform's first player-authored text shown to strangers, and the moderation story is out of
scope beyond the block. A searcher chose to look; **an invitee was put in front of somebody
without asking**. Nothing about a challenge weakens that argument.

### 6. Three answers, not two, when the pairing cannot be computed

§3 established that *nothing to compute* is a first-class absence. An outage drawing the
**identical** absence is the collapse ADR-0141's Consequences refused in as many words — *"a
games list that silently went anonymous would be indistinguishable from four erased
accounts."* But refusing the whole read with a `503` is worse: it turns an unrelated
matchmaking outage into **you cannot answer your challenge**, and answering is not gated.

**The arrangement always answers; the pairing block says whose gap it is.** Three answers:
present; absent because there is nothing to compute; absent because it could not be read.
That is the discipline the photo `review` already runs on — *"Omitted is not `allowed` … Three
answers, not two"* — in the shape `DegradedTermSchema` uses for *whose gap this is*. **The
codes are the contract and the client writes both sentences**
([ADR-0106](0106-evidence-vocabulary-is-contract-weights-are-configuration.md)).

### 7. `read_at` on the list, and a handle on the seat

**`read_at` on `ChallengeListResponse`, at the envelope**, matching `GameListResponse` field
for field and for its written reason: *"the instant every standing and deadline here was
folded against. It travels so a client's countdowns and the standings beside them cannot come
from two different readings of the clock."* The detail response carries **its own**, because
it is its own fold against its own instant.

**`nickname` on challenges' `SeatSchema`**, on ADR-0141 §1's test verbatim — *a record of a
game may say what the people in it were already calling each other, and nothing that a gate
decided somebody may see* — and its §3 rule unchanged: `null` where `users` no longer has the
account, and **the seat stays**, because a seat with no nickname is still a person who was
asked. ADR-0107 §4 applies, so it is a whole handle and nothing shortens it.

### 8. The card's lifetime is the arrangement's lifetime

**The person block and the pairing block are drawn in `AWAITING_ANSWERS` and
`LINE_UP_INCOMPLETE`, and in no other standing.** Every other standing draws neither, and
this is **one rule rather than a list of exceptions** — stated on the two that draw a card
rather than on the ones that do not, so a standing added later is silent by default.

- **`DECLINED` and `LAPSED`** keep their row and their screen
  ([#324](https://github.com/Raketa02/Raketa/issues/324)) and draw the arrangement and the
  handle alone. [ADR-0142](0142-a-withdrawn-challenge-is-the-one-conclusion-the-seats-cannot-reach.md)
  and `domain/challenge.ts` both hold that the pair **releases** when a seat leaves — *"that
  person is a stranger to you once more the moment they leave"* — and a live, as-of-now card
  of a stranger on a screen reopenable for ever is ADR-0141's own phrase for what it refused:
  a directory with extra steps. **The handle stays**, because `standingLine`'s `DECLINED` and
  `LAPSED` sentences quote `{name}`: that is §7's test met exactly, and the reason the field
  is on the seat at all.
- **`ON`** draws neither. The game's standing owns it the moment a game exists (#324), and
  that game's seats carry handles under ADR-0141; a card here would be a second, worse copy
  of the game screen.
- **`WITHDRAWN`**, when ADR-0142's decision is built, draws neither for `DECLINED`'s reason:
  that record releases the pair on it. It falls under the rule rather than being an addition
  to it, which is what stating the rule on the two positively is for.
- **One level down, the same rule per seat.** A seat that declined or lapsed inside a
  still-open `LINE_UP_INCOMPLETE` gets no card either. They have left, and `playersStillIn`
  and ADR-0142's `answering_for` already drop them.

This **refines** §2 rather than contradicting it. Nothing is re-gated against the reader; a
card is part of an arrangement being decided, and it stops when the deciding does.

**The two answer routes are untouched.** They return `ChallengeSchema` and keep returning it,
so [#327](https://github.com/Raketa02/Raketa/issues/327)'s *the reply is the redraw* stands
and costs no second shape. A doubles accept that leaves the challenge in
`LINE_UP_INCOMPLETE` keeps the card block the client already holds — nothing about accepting
changes who those people are — and an accept or decline that ends the arrangement drops it
**by this rule**, not by a refetch.

### 9. The reverse Fit stays unpublished, and this is where that is written down

`Reciprocal.fit_ba` is not a wire value and is not a candidate to become one. It is scored
with the searcher's own reliability deliberately set to `None`, which makes it a **priced
signal about asymmetry** rather than a Fit anybody could read. The next person to look will
find a stored number that appears to be exactly what a *for you* label wants, and they will
be wrong for a reason that is otherwise one comment deep in `shortlist.py`.

## Consequences

**Easier**

- **A challenge can be answered by somebody who can see who is asking**, which is the whole
  of what [#328](https://github.com/Raketa02/Raketa/issues/328) opened on, and it is the same
  gap ADR-0141 closed one surface earlier.
- **The mutual-born challenge stops being a special case.** Recomputing means the deck-born
  conversation and the search-born one render through one path, which is what the map's
  Decision 9 asked for.
- **The next surface that shows a person you are arranging with starts from §2** — the plan,
  the conversation and its header — rather than re-deciding the gate. That is the thing
  ADR-0141's Consequences asked for and left open, one step further along.
- The `read_at` and handle additions are additive and nothing shipped breaks on them.

**Harder**

- **A screen now costs a cross-context read that can fail, on a route whose whole purpose is
  to let somebody answer.** §6 is the mitigation and it is a real one — the arrangement
  answers regardless — but the pairing block has three states where a simpler design would
  have one, and every client draws all three.
- **`challenges` publishes a second spelling of the card**, so the OpenAPI document holds two
  card-shaped objects and the client generates two types for what a designer sees as one
  component. §5 is why, and the cost is a second mapper.
- **Somebody will propose re-gating**, because *the send checked the gates in August and this
  is September* is a reasonable-sounding sentence. §2 is written so that proposal starts from
  the answer routes' own rule rather than from the field.
- **Somebody will propose publishing `fit_ba`**, and §9 exists so that proposal starts from
  the reason.
- **A reader with no rating or no declared intent in the challenged sport sees a materially
  thinner screen than the design.** This is not rare, and it is the price of refusing to
  print somebody else's number under a label that says *for you*.

**Neutral**

- **The expensive read runs only where somebody is deciding.** §8 means three of the five
  standings never assemble a card, so the cost is bounded by open arrangements rather than by
  history — which is the bound ADR-0141 objected to losing.
- The client change is a separate session and a separate commit, with `make gen-api` between
  them, as the contract invariant requires.

## Amendment — 2026-09-10: the card is the reader's decision aid, and a reader who has left is drawn none

§8 stated the card block's lifetime at two levels — per challenge, then per seat — and both hold.
**It needed a third, per reader**, and the case it missed was found by
[#392](https://github.com/Raketa02/Raketa/issues/392): `standing_of` returns `AWAITING_ANSWERS`
while **any** seat is awaiting, so a padel four sits in that standing with the reader's own answer
already given, and §8's rules let them be drawn a full court of cards. The client drew one there
and, for the same reader, none in `LINE_UP_INCOMPLETE` — the same person, released by the same
rule, drawn two ways.

> **A reader whose own seat has left — declined or lapsed — is drawn no card block, in either
> live standing.**

**Two reasons, and the second is the stronger.** The card exists to price somebody you are about to
say `I'm in` or `Not this time` about, so a reader who has left has nothing for it to do. And the
pair **releases the moment a seat leaves**, which makes those people strangers to this reader once
more — and a live as-of-now card of a stranger is exactly what ADR-0141 called *a directory with
extra steps*. The release is the backend's own behaviour and not an inference from this record:
`open_pairs_among` folds `players_in_it_at`, which keeps only seats that are `is_live_at`, and
`Seat.is_open_at` is *declined, or lapsed by the clock*. §8 asserts the same thing but cites
ADR-0142 and the **client's** `domain/challenge.ts`, so the server evidence is written here rather
than borrowed.

**§8's own test is the objection, and it is met rather than dodged.** *"A card is part of an
arrangement being decided, and it stops when the deciding does"* — and in `AWAITING_ANSWERS` the
arrangement **is** still being decided, so read at the level §8 wrote it, that clause argues for
drawing this reader a card. What answers it is that the clause is about the wrong subject's
deciding: **this reader's part in it is over.** They cannot change the arrangement, cannot be asked
again, and have been released from the pair by leaving. The arrangement continues without them, and
a card is not a report on an arrangement — it is the thing you answer against.

**An accepted reader keeps their card.** They have no answer left either, so the two reasons
disagree here, and the pair decides it: they are still on the court and it still holds them. The
predicate is *has this reader left*, never *has this reader answered*.

**This is not a second gate against the reader, and §2 is untouched.** *The challenge is the gate,
and nothing is re-evaluated against the reader* is about **permission** — holding a seat is the
whole of it, decided once, and this amendment does not add a check there. What it settles is what
the card block is **for**, which is a question about the block and not about access. §8's closing
*nothing is re-gated against the reader* is narrowed to that reading; anybody who holds a seat can
still read the challenge and everything else on it.

**The enforcement belongs on the server, and the client is defence in depth.** The style is the
argument, and it is the server's own: `ReadChallenge._court` says the per-seat rule is enforced
*"by not putting them in the question — so there is no card computed, no photograph signed and
nothing to leak."* §8 states the rule; that docstring is where it says how, and it is quoted from
there rather than from here. A reader who has left is owed that, and
today the server still computes their cards and signs the URLs; the client merely declines to draw
them. The server half is filed as
[#394](https://github.com/Raketa02/Raketa/issues/394) and cites this amendment.

**One gap is stated rather than closed.** Both sides read the answer the wire sends, so a seat past
its window whose lapse has not been swept is not *left* yet and still draws a card. Deriving the
lapse client-side would give that side a second clock, which its own domain module refuses; the
sweep closes it.

**Cost named:** a reader who has left keeps the arrangement and the handles and loses the numbers,
so the screen tells them what happened and no longer prices the people it happened with. That is
the intent, and §8's `DECLINED`/`LAPSED` bullet already pays the same price one standing later.
