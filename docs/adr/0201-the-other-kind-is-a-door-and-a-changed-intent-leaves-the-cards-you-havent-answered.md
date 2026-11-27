# ADR-0201 — The other kind is a door, and a changed intent leaves the cards you haven't answered

- **Status:** Accepted — **§2 noted 2026-11-24
  ([#859](https://github.com/Raketa02/Raketa/issues/859), decided and not yet built): the switch
  becomes the Games tab's menu, and the door a line in it**
- **Date:** 2026-11-05
- **Amends [ADR-0094](0094-play-intent-declared-per-sport-in-its-own-aggregate.md)'s 2026-10-06
  note**, *the You tab is the other place a player changes it*. The Games deck's switch is a further
  place: the kind the intent doesn't want is a door to an in-place change, still reported on the
  **`DECK`** surface, so the closed five stand (§2).
- **Mirrors [ADR-0195](0195-reliability-is-points-a-no-show-is-caught-at-the-court-and-a-right-score-needs-no-tap.md)
  §6's *from then on*** for Play intent. A name not yet In whose intent no longer wants a card's
  kind holds no seat on it, and the yeses already given stand (§3).
- **Amends the proposals rule *no route makes a proposal*** (`backend/.claude/rules/proposals.md`,
  written with the proposer by [#540](https://github.com/Raketa02/Raketa/issues/540); no ADR
  decided it). `POST /pools/{id}/deal` runs the card-builder's batch for one pool on the request
  path. The route never makes a card itself (§5). The rule's line is rewritten by
  [#739](https://github.com/Raketa02/Raketa/issues/739), with the route, and stays true of the code
  until then.
- **Leaves standing** ADR-0094's aggregate, its event, its three values and the unkeyed
  `PUT /play-intents/{sport}`: **Play intent** stays one setting, what a player is dealt *and* who
  they are dealt to (§1). It also leaves standing
  [ADR-0189](0189-a-yes-books-a-court-and-the-club-is-the-seller.md)'s deck as *a projection,
  recomputed at every read and stored nowhere*, which §3's rule is read through; and
  [ADR-0197](0197-a-deck-re-read-is-cheap-and-told-never-polled.md), still Proposed. The finding
  state is one answer's one re-read, not a poll, and telling the phone about new cards in general
  stays that record's §3 (§4).
- **Does not decide** a way for an *Either suits me* player to narrow from the group page; any split
  of what a player is shown from who finds them; telling the phone when cards are dealt for any
  other reason; the Friends tab's switch, Post a game's Kind step and the first-time question's
  words; or any change to how cards are built, beyond a gone name freeing its seat.
- Settles PRD [#736](https://github.com/Raketa02/Raketa/issues/736), decided in the intent grilling
  on 2026-11-05 (Q1–Q8 there, the mechanics' Q127) and written by
  [#737](https://github.com/Raketa02/Raketa/issues/737). Built by
  [#738](https://github.com/Raketa02/Raketa/issues/738) (the dropped-kind rule),
  [#739](https://github.com/Raketa02/Raketa/issues/739) (the deal and the deck counts),
  [#740](https://github.com/Raketa02/Raketa/issues/740) (the door and its panel),
  [#741](https://github.com/Raketa02/Raketa/issues/741) (finding) and
  [#742](https://github.com/Raketa02/Raketa/issues/742) (the You tab's lines).

## Context

**Ania sees one kind of game, and nothing says there is another.** Ania plays padel in *Padel po
pracy*. When she first opened Games she answered *Your usual game at padel* with **Competitive**, so
her switch reads `Competitive · 7` and nothing else. Kuba, in the same group, answered **For fun**
and sees only `For fun · 3`. Zofia answered **Either suits me** and sees both.

One Saturday Ania would like a relaxed game:

- Nothing on the group page tells her for-fun games exist, or how to get them.
- The only way is You › *What kind of game* › Padel. She has to leave the group, guess that this is
  the place, change her answer, and find her way back.
- Back on Games, For fun reads *Nothing picked right now*. Her change marks her groups due, and the
  card-builder deals her for-fun games a few seconds later, but nothing tells the phone. The cards
  appear only the next time she opens the page, so she may think the switch did nothing.

**The first-time question has the same empty moment.** Right after *Your usual game at padel* is
answered, the deck is read again, before anything has been built for her.

**A change leaves her on other people's cards.** Ania is named on Marek's Saturday 10:00 competitive
card and hasn't answered it. An intent change does nothing to cards already dealt, so when she
switches to For fun:

- the card leaves her phone, because her deck no longer shows the competitive kind;
- Marek still sees her name on it, waiting for an answer she can no longer give;
- the card-builder keeps her seat for her, so the card is offered to nobody else;
- opened from an old notice, the card still takes her yes, because a yes on a pick doesn't ask the
  kind. She can join a kind of game she has just said she doesn't want.

**What a player is shown and who finds them are one fact.** A card is not a search result. It is one
game, with four names on it, that all four must say yes to before the court is booked and 40 zł is
held from each. Kuba sees the exact same card, with Ania's name on it. So showing Ania for-fun cards
*is* putting her in for-fun games. Today the deck shows only the kinds her intent wants, and the
card-builder deals only members whose intent wants the card's kind (*may play*). They are the same
rule read in two places.

**The alternatives:**

- **Split the two.** Ania stays Competitive, but can open For fun at any time. Rakieta then has to put
  her in for-fun games all the time, because a card she is shown is a game she is on. That costs
  four things:
  - **Stalled cards.** Kuba's for-fun cards wait on her while she never opens that tab.
  - **Hours used up.** Her Thursday 19:00 can go on a for-fun card she'll never look at, which
    keeps her off a competitive one at the same hour.
  - **Intent that protects nobody.** Kuba chose For fun, and it would keep him from no one.
  - **Counts that lie.** `For fun · 7` would count cards waiting on people who never look.

  Every variant has the same shape and was rejected with it: a private search, a *just this week*
  widening, browsing other people's posts of the other kind (Q1).
- **A `+ For fun` tab.** The plus says Rakieta adds games on its own, when the choice is the player's
  (Q4).
- **Send the player to the You tab.** That is where the change is made today, and it is the
  problem (Q2).
- **A line under the switch for an *Either suits me* player**, so they can narrow from the group
  page. It takes height from the cards and could cut them (Q7).
- **Leave the dropped kind's cards as they are.** That is today: a name nobody can answer for, a
  seat nobody else is offered, and a yes still taken on a kind she said she doesn't want.
- **Record the drop as a no on each card.** A no is final (the mechanics §5.3), so switching back
  would cost her those cards. It would also write a domain fact for a preference, which ADR-0094
  argues is not a consent.
- **End the finding state on a timer.** Any guess at how long the card-builder takes is too short on
  a busy pool and too long on a quiet one.

## Decision

### 1. One setting is kept

Play intent stays the one per-sport setting that says both **what a player is dealt** and **who
they are dealt to**. A card is one game that everybody on it sees, so the two cannot differ.

The aggregate, its event and `PUT /play-intents/{sport}` are unchanged. Intent stays per sport:
Ania can be Competitive in padel and For fun in tennis. How cards are built is unchanged, except
that a gone name frees its seat (§3).

### 2. The switch always shows both kinds, and the unwanted one is a door

- **Both kinds are always on the switch.** Ania's reads `Competitive · 7` and a **dimmed `For fun`,
  with no number**. Kuba's is the mirror: a dimmed `Competitive` and `For fun · 3`. Zofia's is
  unchanged, with both live.
- **Dimmed, never disabled.** The door is the same size as the live kind and just as easy to press.
  It reads *not yours yet*.
- **The deck never opens on it**, even when the phone last stood on that kind in another sport or
  group. The position the switch remembers stays one for the app, as today, and is corrected to a
  live kind. Tapping the door doesn't move it.
- **A tap opens a panel in place, on the group page.** It is an overlay inside the deck's area, not a
  new route and never a trip to the You tab:

  > **You play padel competitively, so Rakieta only puts you in competitive games.**
  > Want for-fun games too?
  >
  > **Either suits me** — *Keep your 7 competitive cards and get for-fun ones too.*
  > **For fun** — *Your 7 competitive cards go. Games you're In on stay.*
  > **Keep competitive**

  - *Either suits me* comes first and is highlighted. The answers use the first-time question's and
    the You tab's words.
  - The number is her own count of cards of that kind in this group, the one her switch shows. With
    one card the line says *card goes*; with none it drops the number (the-words §28).
  - An answer changes **this sport only**. It sends `PUT /play-intents/{sport}` with the `DECK`
    surface, and she lands on the kind she tapped.
  - *Keep competitive* closes the panel and sends nothing.
  - Kuba's panel is the mirror: *You play padel for fun, so Rakieta only puts you in for-fun games.
    Want competitive games too?*
- **An *Either suits me* player narrows on the You tab only** (Q7).
- **Untouched:** the Friends tab's switch, Post a game's Kind step and the first-time question's
  words. Post a game still lets Ania post a for-fun game as a one-off.

> **Note — the switch moves into the tab (2026-11-24, [#859](https://github.com/Raketa02/Raketa/issues/859); decided and not yet built).**
> The switch under the tabs becomes **the Games tab's menu**: a chevron on the selected Games tab,
> and a tap on that tab opens a menu with two lines, Competitive then For fun, each live line with
> the count the switch shows today. **The door is a line in it**, still dimmed, still numberless and
> never disabled. A tap on it closes the menu and opens the same panel, with the same three answers.
> What this section decides is unchanged: both kinds are always offered, the deck never opens on the
> door, the remembered kind stays one for the app, and an *Either suits me* player narrows on the
> You tab only. The Friends tab's switch, which this record doesn't decide, moves into that tab's
> own menu ([the Friends screens §7.1](../specs/friends/the-screens.md#71-the-court);
> [ADR-0202](0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md)
> still governs it). A change of layout with no new record; specified in
> [`docs/specs/games-and-fill-in/`](../specs/games-and-fill-in/the-screens.md#a1-where-things-live),
> its record in [`docs/specs/tab-menu/`](../specs/tab-menu/README.md).

### 3. A changed intent leaves the cards you haven't answered

**The dropped-kind rule.** A name on a card who is **not In**, and whose Play intent no longer wants
the card's kind, **holds no seat on it**.

- **It is read live and recorded nowhere.** It is not a no and records no event. Whether the name
  holds a seat is read off their intent at every read and every run, like a name that no longer
  fits.
- **Others' decks and the card's details leave the name off**, the way they leave off a name that no
  longer fits today.
- **The card-builder treats the name as gone**, as after a no:
  - its seat is dealt to up to three next best fits at the next run, one in singles;
  - widening counts it as gone wherever the builder asks who is still named.
- **A player who is In is never gone this way.** Her yes holds its seat, and no extra fit is dealt
  for it.
- **If her intent wants the kind again**, she is a name on the card again, as long as nobody has
  taken her seat. The first yes takes the seat, as for any next best fit. The builder's version
  invariants still hold.
- **A new yes** on a card of a kind her intent doesn't want is refused with **`no_longer_fits`**,
  naming no rule. A join on a post is already refused with `post_not_open_to_you`, through *may
  play*.
- **Yeses already given stand**, and nothing asks them about the kind: not the fill's re-check, not
  a paused yes coming back, not a kept seat confirmed. Ania's Thursday 19:00 (competitive, 2 of 4
  In) stays, because she promised three people that game. She can still take her yes back from
  *You're In*.
- **Seat open offers** already read intent live, through the members' read, and are unchanged.

The rule applies wherever the intent changes: the door, the first-time question and the You tab.
It is ADR-0195 §6's *from then on*: the reliability filter keeps a player off new courts and takes
no yes back, and so does a changed intent.

### 4. After an answer on Games, the tab says it is finding

Right after any intent answer on Games, from the door's panel or the first-time question:

1. The phone sends the `PUT`, then asks Rakieta to deal that group now (§5).
2. While that request is in flight, the tab reads ***Finding for-fun games for you…***, or
   ***Finding games for you…*** after *Either suits me* on the first-time question.
3. Then the phone re-reads the deck. It shows her cards, or *Nothing picked right now* with **Post a
   game** if no hour works.

A failed deal request falls through to the re-read, and nothing is retried. The finding state is one
answer's one re-read, not a poll. It covers only the player's own answer, and tells the phone nothing
about cards dealt for any other reason (ADR-0197 §3).

### 5. One route deals a group now

**`POST /pools/{id}/deal`** runs the card-builder's batch for that one pool, over every sport it
plays, and answers `204` once the batch has been applied.

- It is refused with `pool_not_found` for a pool that doesn't exist or that the caller isn't in, as
  the deck is.
- It is safe beside the jobs and beside itself, by the builder's own construction
  ([ADR-0092](0092-periodic-jobs-as-embedded-loops.md)). A repeat deals nothing new.

**This amends the rule *no route makes a proposal*.** The route never makes a card itself: it runs
the batch the jobs run, and the card-builder still makes every card. What changes is that the
builder may now run on the request path, for one pool, when a player asks.

### 6. The You tab says what a change costs

On You › *What kind of game*, expanding a sport's row draws a line under each answer that would
change something. A line that drops a kind says what the panel's says, **counted across all the
player's groups**: *Your 7 competitive cards in your groups go. Games you're In on stay.* The line
under *Either suits me* carries no count: *Keep your competitive cards and get for-fun ones too.*
The current answer gets no line. An undeclared sport gets no lines and keeps its footnote.

The count is **`GET /players/me/deck-counts?sport=`**, which answers `{sport, competitive,
for_fun}`: how many cards each kind deals the caller now in that sport, summed over every group
they're in.

- Each group's number is exactly the count its switch shows, Seat open cards included.
- A kind the caller's intent doesn't show is 0, and an undeclared sport is 0 and 0.

## Consequences

**Easier**

- **A player learns the other kind exists** on the page where it would be played, and changes their
  intent there.
- **A change says what it costs before the tap**, in the same words on Games and on You.
- **Nobody waits on a name that can't answer.** Marek's card stops naming Ania, and her seat goes to
  the next best fits.
- **A first deck is no longer a false *Nothing picked right now*.**
- **No new fact is stored.** The rule is read live, so switching back costs nothing while the seat
  is free.

**Harder**

- **Every read that says who holds a seat must ask the intent**: others' decks, the details, and the
  builder's gone and widening. A read that forgets it shows a name nobody can answer for. It is one
  more input on reads ADR-0197 measured as expensive.
- **The card-builder now runs on the request path.** Its batch is CPU on the task's only event loop
  (ADR-0197's concern) for its whole length: on a busy pool the phone waits, and so does every other
  request on that task. #739 measures it on the seed's busiest pool and records the figure in its
  handover; that is the number to watch. A repeat deals nothing new but costs the same, and there is
  no rate limit.
- **A name can now leave a card and come back without a no.** Her seat is dealt to next best fits
  while she is gone, so switching back can put more names on a card than it has seats, and the
  first yes settles it. #738 must keep the builder's version invariants through that: at most three
  versions, one per person.
- **Switching back is no guarantee.** Once a next best fit takes her seat, her old card is gone for
  her.
- **Two counts must agree**: the switch's and the You tab's. Computed apart, they can drift, so
  #739's tests hold each group's number equal to its switch's.
- **The panel's number can be stale.** It is the count the switch showed when the deck was read; a
  card dealt or taken since is not in it.
- **A dimmed tab that can be pressed is an affordance the design system has to carry.** If it reads
  as disabled, nobody opens it.
- **The player app's drift check is red** from #739 until the first player ticket regenerates its
  types, accepted until the branch's end.

**Neutral**

- `DECK` stays one of the closed five. The door reports the same surface as the first-time
  question.
- Post a game's Kind step still lets a player post the other kind as a one-off, with no change of
  intent.
- Intent stays per sport. Changing padel never touches tennis.
