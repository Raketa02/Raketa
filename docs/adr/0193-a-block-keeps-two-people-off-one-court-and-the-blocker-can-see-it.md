# ADR-0193 — A block keeps two people off one court, and the blocker can see it

- **Status:** Accepted — **§2 superseded for the record, and §3's record read retired, on 2026-11-07
  by [ADR-0203](0203-a-ranking-per-sport-sorted-by-the-level.md)** (Q130) — **ADR-0203's *disappear from each other's … rankings holds
  again* reversed for the ranking 2026-11-14 by [ADR-0204](0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md)** (Q131): a blocked pair sees each other
  in the ranking, Top 10 and group sheets, and is kept out of each other's people rows on Home; the
  record stays closed both ways
- **Date:** 2026-10-06
- **§1 extended 2026-10-11 by [ADR-0195](0195-reliability-is-points-a-no-show-is-caught-at-the-court-and-a-right-score-needs-no-tap.md)**
  §6: the pair rule gains one more clause, the **reliability filter**, asked exactly where a block
  is asked. Unlike §4, it takes no yes back: yeses already given stand.
- **§4, its header's reach into ADR-0095 §7, and its *Consequences*' *a waiting game drops back to
  filling*, amended 2026-10-12 by [ADR-0196](0196-only-raketa-until-raketa-is-the-clubs-booking-software-and-a-clubs-cancel-moves-the-game.md)** §1. *On request* is removed,
  so no booking waits for a club. A block takes back the blocker's yeses on **proposals still
  filling** and **never touches a booking**. The second case of §4, *a booking waiting for the club*,
  which told the others In that the blocker left, has nothing left to apply to.
- **§2's *it reaches nothing else* extended 2026-11-06 by
  [ADR-0202](0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md)** §2. A block also
  **ends a friendship**, and any open request between the pair, silently and in either direction, and
  a request the blocked person sends later is **never shown to the blocker**. §3's *byte for byte the
  same* now holds against a removal: what the blocked person reads is exactly what a silent removal,
  or a request set aside, would show them. A friends game's line-up with a blocked pair in it is
  refused naming nobody, as a yes is.
- **§2 superseded for the record, §3's record read retired, and the *Consequences*' *now false*
  corrected, 2026-11-07 by [ADR-0203](0203-a-ranking-per-sport-sorted-by-the-level.md)** §8 (the mechanics Q130):
  - **a block closes the record in both directions, everywhere, group-mates included.** It is again
    a gate the record is admitted under, refused with the record's one refusal. §2's *the blocker
    opens the record to unblock* and its *byte for byte the same* read no longer hold for the
    record;
  - **Unblock lives in You › Blocked players**, and the record's Unblock button goes. §3's second read,
    *the player record says whether the reader has blocked the subject*, leaves the contract:
    **Blocked players is the one read that carries the reader's own blocks**, and the contract walk
    allows that one place;
  - **a block also hides the pair's rows from each other in the ranking**, in both views;
  - the prototype's *"you disappear from each other's … rankings"*, called false below, **holds of
    the ranking**, as [ADR-0095](0095-block-directed-record-symmetric-effect-gates-fail-closed.md) §7
    said it would.

  §1, §4–§6, and §2 for groups, Members lists, booked games and chats, stand. Dated notes mark §2,
  §3 and the *Consequences*.
- **Amends [ADR-0095](0095-block-directed-record-symmetric-effect-gates-fail-closed.md)** in five
  places:
  - **§3's** *"from any surface where that player is visible"* becomes **no surface is recorded**
    (§5). **§2's event table** follows: `blocks.player_blocked` moves to v2, without `surface`.
  - **§7's** *"Sideways — everywhere"* becomes **the pair is kept off one court; groups and Members
    lists are untouched** (§1–§2).
  - **§7's** *"Backwards — not at all"* gains one reach: a block **takes back the blocker's yeses on
    proposals still filling, and on bookings still waiting for the club**, where the other person
    is In. **A booking the club has confirmed is never touched** (§4).
  - **§8's** *"unrepresentable in a response"* becomes **a response may carry the reader's own
    blocks, never anyone's block of the reader** (§3).
  - **§2's** *"neither party can ever discover which way it went"* now holds of the **blocked**
    party only. The blocker sees their own blocks (§3).

  Nothing else in it moves. The record stays directed and the effect symmetric, and §5's *a gate
  that cannot be evaluated excludes* still holds wherever a block is asked.
- **Supersedes [ADR-0183](0183-a-group-is-a-crowd-at-a-home-club-and-its-link-never-changes.md)
  §10.** A block hides nobody in a Members list (§2). *Counts don't change* stands, now because
  nothing is hidden.
- **Narrows [ADR-0159](0159-a-record-is-read-through-a-prior-disclosure-and-the-refusal-names-nothing.md)
  §4–§5, and its 2026-10-02 amendment.** A block is no longer one of the gates a record is
  admitted under, in either direction (§2). The gates that remain still answer with one refusal
  that names nothing.
- Decided in the 2026-10-05 grilling that removed Classic play (Q9, Q17–Q20), for PRD
  [#571](https://github.com/Raketa02/Raketa/issues/571). A game **waiting for the club** was ruled
  by the product owner on 2026-10-06 (§4). Settles
  [#585](https://github.com/Raketa02/Raketa/issues/585). Built by the backend's
  [#586](https://github.com/Raketa02/Raketa/issues/586) and the player app's
  [#587](https://github.com/Raketa02/Raketa/issues/587).

## Context

ADR-0095 made the block for a matcher. A block removed each person from the other's view **on every
surface that shows one player to another**: the shortlist, the line-up, the deck, a standing
search's notification. It was unrepresentable in any response, even to the person who made it. It
recorded which of those four screens it was made from. And it reached nothing already agreed,
because no game could exist yet.

**The Classic play removal ([#569](https://github.com/Raketa02/Raketa/issues/569)) deletes all four
screens**, and the search that *"everywhere"* was written around. What is left shows one player to
another in five places:

- the group's **Games deck**, whose cards show the people In and the people dealt;
- **Fill in**, whose rescue seats sit on booked games;
- a **booked game's** details and its chat;
- a group's **Members** list;
- the **player record**, opened from any of the faces above.

Only the first two can put two people on one court. The new games already keep a blocked pair off
it. Every proposal, version, yes, rescue and post asks one pair rule, Proposals' `PlayerFit`: no
block either way, mutual gender preference, Levels within the kind's window. **But the app has no
Block button anywhere.** Ania, dealt game after game with Kuba from her own group, has no way to say
*not him*. Building that button runs into four things the old rule decided wrongly for this world:

1. **The screen it records.** A block names which of four screens it came from, and all four are
   being deleted. A field whose every legal value names a screen that doesn't exist is a field
   somebody fills with a lie.
2. **Seeing her own blocks.** *Unrepresentable* includes to the blocker. So Ania could never see whom
   she blocked, and an unblock would have to be typed blind. A control nobody can undo is a control
   people are afraid to use.
3. **Games under way.** If Ania blocks Kuba while both of them are In on a game still filling, nothing
   takes her out. A minute later the last yes lands. The fill re-checks the pair rule before it books
   (`NO_LONGER_FITS`), and reopens the seat of **whichever of them said yes later**. Half the time
   that is Kuba, who loses his place over something he can't see.
4. **Hiding is the tell.** ADR-0183 §10 carried *everywhere* into Members lists: the pair is left out
   of each other's list in every group. A group is a crowd at a home club that mirrors a WhatsApp
   group, and its members know who is in it. When Ania is missing from a list Kuba knows she's on,
   that tells him more than anything a response could carry. The record (ADR-0159 §5) refuses on a
   block too, with a 404 byte-identical to *never disclosed*. That is honest about a stranger from a
   search, and a giveaway about a co-member whose face is on the group page. It also locks Ania out
   of the one screen where she'd look to undo her block.

Considered and rejected:

- **Keep *everywhere* and only add the button.** Members and the record would hide Kuba from Ania.
  Then she couldn't reach his record to unblock, and he would find her missing from a list everybody
  in their WhatsApp group can check.
- **Tell both sides.** A block that costs a social scene is a block nobody uses. The control exists
  for the moment somebody would rather not explain.
- **Take the blocker out of booked games too, with a refund.** That moves money on its own. A booked
  game was agreed by four people and a club, and the court is paid for. Leaving one stays the
  player's choice, by the ordinary rules.
- **Take back both people's yeses.** Ania's alone is enough to keep them apart, and it is her
  decision. Taking Kuba's too would cost him a game for a reason he can never see. The blocked
  person is kept off one person's court and is otherwise left alone.
- **Keep the surface as optional context.** That means a nullable field no client can honestly fill,
  in an event that will outlive every screen this app draws.

## Decision

### 1. A block keeps two people off one court

A blocked pair, in **either** direction, is never:

- dealt a version together;
- both **In** on one proposal;
- offered each other's **Rescue**, whether as a Seat open card or by taking the seat;
- joined onto each other's **Post**.

All of these ask the one pair rule, `PlayerFit`. A yes the rule refuses is refused **without naming
why**, as any yes that doesn't fit is. Nothing ranks on a block, and an unreadable block state still
refuses rather than calling the pair fit (ADR-0095 §5).

### 2. It reaches nothing else

**Groups, Members lists, the player record, booked games and chats already shared are untouched.**
Both people stay in the group. Each sees the other in its Members list and can open the other's
record, as any co-member can.

- **Members lists hide nobody for a block.** This supersedes ADR-0183 §10.
- **A block is not a record gate**, in either direction. Ania opens Kuba's record to unblock him (§3).
  Kuba opens Ania's exactly as before, and gets a response that is **byte for byte the same whether
  or not she blocked him**. The record's other gates, and their one refusal, are unchanged.
- **A chat they already share keeps working.** A booked game's arrangements are not cut off by a
  block on either side.

> **Extended 2026-11-06 by [ADR-0202](0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md) §2.** A block now reaches one
> more thing, a friendship: it ends the friendship and any open request between the pair, and a
> request the blocked person sends later is never shown to the blocker, who reads nothing. The
> blocked person keeps reading *request sent*, as after a request set aside.

> **Superseded for the record 2026-11-07 by [ADR-0203](0203-a-ranking-per-sport-sorted-by-the-level.md) §8.** A block closes the record in both
> directions, everywhere, group-mates included, with the record's one refusal. Ania no longer opens
> Kuba's record to unblock: Unblock is in You › Blocked players. Kuba's read of Ania's record is no
> longer the same byte for byte as an unblocked read: it is refused, as a hold or an account that may
> not be shown is. A block also hides the pair's rows from each other in the ranking. **Groups, Members
> lists, booked games and chats already shared stay as above.**

### 3. Nobody is shown that they were blocked, and you can see your own blocks

**A response may carry the reader's own blocks, never anyone's block of the reader.** Two reads carry
them:

- **Blocked players** — the caller's own blocks: each person's id, name and photo, and when the block
  was made. It lists only blocks the caller made.
- **The player record** says whether **the reader** has blocked the subject. Nothing on it answers
  the other direction.

The test that walks the emitted contract for a block is **narrowed to this direction, not dropped**.
A block may cross on those two reads, and only as the reader's own. Nobody is notified of a block or
an unblock, in either direction.

The record stays directed, so this is per person. If both have blocked, each sees only their own.
Unblocking lifts only the caller's block, never 404s, and says nothing about the other one.

> **Amended 2026-11-07 by [ADR-0203](0203-a-ranking-per-sport-sorted-by-the-level.md) §8.** The record no longer opens for a blocked pair, so it
> no longer says whether the reader has blocked the subject. **Blocked players is the one read that
> carries the reader's own blocks**, and the contract walk allows that one place.

### 4. A block takes back the blocker's yeses until the club confirms, and never touches a confirmed booking

When a block is recorded, Proposals takes back **the blocker's** yeses wherever the blocked player
is In on a **proposal still filling** or a **booking still waiting for the club**. That covers
Picked for you games and Posts alike, including a post the blocker made or joined.

- **On a proposal still filling**, it is the ordinary **Withdraw**: free, silent, and the seat is open
  again. Momentum, decks and notices behave exactly as when a player withdraws by hand, so nothing
  tells this withdrawal apart from any other.
- **On a booking waiting for the club** (On request), the game is treated as still filling, as ruled
  on 2026-10-06. The blocker's place is taken back exactly as when she leaves it herself: the request
  is withdrawn and the game is filling again with her seat open. Nobody has paid, so nobody is
  refunded. **The others In are told she left**, the notice any departure from a waiting game sends
  (*someone left*, filling again). It names her and never the reason. This is the one place a block
  causes a notice, and it reads exactly like her leaving by hand.
- **Only the blocker's yeses.** The blocked player's yes stands.
- **A booking the club has confirmed is never touched.** That includes a booked game, a seat open on
  one, and one already played. No money moves and no court is cancelled because of a block. Leaving
  one stays the player's choice, by the Leaver rules.
- **Unblocking brings no yes back.** Nothing reappears on the blocker's behalf.
- **Any later yes that would pair them is refused** by §1's rule.

> **Amended 2026-10-12 by [ADR-0196](0196-only-raketa-until-raketa-is-the-clubs-booking-software-and-a-clubs-cancel-moves-the-game.md) §1.** No booking waits for a club any more: *On
> request* is removed, and a full game books the moment it fills. So the second bullet above has no
> case, and *until the club confirms* now reads *until the game is booked*. Every withdrawal a block
> makes is the ordinary one, from a proposal still filling. The fill's re-check of the pair rule
> before it books stands.

The guarantee doesn't depend on the timing. A game that fills between the block and this withdrawal
still never books the pair, because the fill re-checks the pair rule before it books and before it
accepts a club's yes. There, the seat that reopens is whoever said yes later. The withdrawal is what
makes it the blocker's place that goes, every other time.

### 5. No screen is recorded

The block request carries **only the other player**. `blocks.player_blocked` moves to **v2**, with
`blocker_id` and `blocked_id`. **v1, which named the screen, still folds**: its surface is read and
dropped, and nothing is rewritten in the store. `BlockSurface` is deleted with its four values.
`blocks.player_unblocked` stays v1; it never had a surface.

### 6. What stays

From ADR-0095, unchanged:

- one event-sourced stream per **ordered** pair, and a directed record with a symmetric effect;
- blocking is **idempotent**, and blocking yourself is an error;
- **no cap, no cooldown, no rate limit**;
- no reason field and no free text: a reason belongs to a Report, which is not a term yet;
- erasing a player erases every stream they appear in, on either side;
- the `BlockQuery` port **fails closed**.

## Consequences

**Easier**

- **Blocking can be offered.** A person can block, see whom they blocked and undo it, from the record
  where they recognised somebody or from a list under You.
- **A block is a rule about courts, and the code that keeps courts is the code that enforces it.** One
  pair rule answers every route onto a court. The surfaces that only *show* people stop asking about
  blocks at all: Members drops its `HiddenMembers` port, and the record drops a gate.
- **Fewer things fail when the block state can't be read.** Under *everywhere*, an unreadable block
  state was an outage of every people-listing surface: Members answered 503 and the record refused.
  Now it stops only what would put two people on a court.
- **No stored field names a screen that doesn't exist.**

**Harder**

- **Kuba still sees Ania.** He sees her in the group's Members list, on her record, and on the faces
  of booked games they were already in. A person who wants somebody out of sight entirely gets less
  than ADR-0095 promised, and the prototype copy that promised *"you disappear from each other's …
  decks, radar and rankings"* is now false, as is the block route's own description (*"disappear
  from each other's view everywhere"*), which #586 rewrites. That is deliberate: everyone in the
  group can see who is in it, so hiding a member could never be silent. A player who needs more
  than this needs a Report and moderation, and neither exists.

  > **Corrected 2026-11-07 by [ADR-0203](0203-a-ranking-per-sport-sorted-by-the-level.md) §8.** In the ranking the promise is true again: a
  > blocked pair never sees each other's row, and neither opens the other's record, anywhere. Kuba
  > still sees Ania in Members and on the faces of booked games they share, and Ania's record now
  > refuses Kuba, which in a group is a tell this record avoided. The product owner chose the clean break (Q12
  > there).
- **The blocker sees the direction.** *Neither party can discover which way it went* is now true of
  the blocked party only. A Blocked players list is a stored, readable list of whom somebody chose to
  avoid. It is shown only to its author, and it becomes one more thing a future data export has to
  include and an erasure has to reach.
- **The rule about leaks is narrower, so it is easier to break.** The contract walk used to be one
  regex: no field named for a block, anywhere. Now it is a walk with two allowed places, and a third
  would be a review question, not a red build. The test must keep both allowed places named, and
  forbid every other one.
- **A block can cost the blocker a game.** If she was In on three filling games with him, she is In on
  none of them a second later, and nothing brings them back on unblock. The confirm sheet must say
  what blocking does, because nothing afterwards will.
- **A waiting game drops back to filling, and that is not silent.** At an On request club, the
  request the club was about to answer disappears, and the others In are told the blocker left, at
  the moment she blocks. That is what any departure from a waiting game sends, and nothing names a
  block. But Kuba gets *"Ania left"* a second after she blocks him, which a withdrawal from a game
  still filling never does.

  > **Amended 2026-10-12 by [ADR-0196](0196-only-raketa-until-raketa-is-the-clubs-booking-software-and-a-clubs-cancel-moves-the-game.md) §1.** This cost went with *On request*: no
  > game waits for a club, so no request disappears under it. A block's withdrawal is the ordinary
  > one, from a proposal still filling.
- **Old v1 events carry a field nobody reads.** The decoder keeps one more shape for as long as the
  store holds a v1 block.

**Neutral**

- **Blocks still bind all six pairs of a four.** `PlayerFit` checks every pair among the people In, so
  two other players who blocked each other are kept apart on a game the reader is In on, and nobody
  is told who.
- **Members lists, records and chats now have a block-free contract.** The day somebody proposes
  hiding a blocked person from a card or a list, it is a new decision against §2, not a gap in this
  one. PRD #571 lists it as out of scope.

  > **2026-11-07:** [ADR-0203](0203-a-ranking-per-sport-sorted-by-the-level.md) is that decision for the ranking's lists and for the record. Members
  > lists and chats keep a block-free contract.
