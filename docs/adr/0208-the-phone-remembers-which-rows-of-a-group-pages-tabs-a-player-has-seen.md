# ADR-0208 — The phone remembers which rows of a group page's tabs a player has seen

- **Status:** Accepted
- **Date:** 2026-11-23
- **Is the new record [ADR-0188](0188-the-phone-remembers-three-choices-per-account-and-forgets-them-at-sign-out.md)
  §5 asks for**: *"Adding a fourth value is a new record, not an edit to this one's table."*
  [ADR-0200](0200-a-level-is-asked-where-play-begins.md) §8 and
  [ADR-0203](0203-a-ranking-per-sport-sorted-by-the-level.md) §5 were such records before it.
- **Amends ADR-0188 §2**, with a new value: *the rows of a group page's tabs a player has seen*.
  It is **per account and forgotten at sign-out**, like the three in the table (§1, §3).
- **Amends ADR-0188 §5** on two of its lines:
  - *"which tab a group page was on"* **still isn't kept**. This record keeps rows, not the tab, and
    a group page still opens on Games.
  - *"anything the server knows"* **still isn't kept**. The ids are the server's, but the fact that
    this player had them on screen is not: no read says it, and nothing here is a copy of a row
    (§2).
- **Narrows ADR-0188 §4, for this value only.** §4's *"It is read before the first screen that
  uses it, so no screen draws one choice and then jumps to another"* doesn't hold here: the page
  draws without it, and a badge appears once it has been read, outside the layout, so nothing jumps
  (§5). §4's *a stale or unreadable value is its default* stands, and here the default is *nothing
  seen*.
- **Leaves standing** ADR-0188 §1 (the store is still the one module of its kind, and the
  AsyncStorage allow-list doesn't grow) and §3 (sign-out empties it). It also leaves standing
  [ADR-0197](0197-a-deck-re-read-is-cheap-and-told-never-polled.md): nothing is read more often
  because of it.
- **Does not decide** the split of the group page into four tabs. That is a change of layout, not
  a decision about the system (the grilling's Q8), so the specs, the glossary, the feature docs and
  the design system carry it. It also doesn't decide Home's *Needs your answer* badge, which keeps
  its own "seen" on the server
  ([ADR-0205](0205-what-waits-for-your-answer-goes-behind-an-envelope-and-homes-rows-fold-into-for-you.md),
  #819).
- Settles the phone's half of PRD [#844](https://github.com/Raketa02/Raketa/issues/844), decided
  in the Fill in refactor grilling on 2026-11-23 (Q2b, Q10–Q12) and written by
  [#845](https://github.com/Raketa02/Raketa/issues/845). The decision log is
  [`docs/specs/fill-in-split/decisions.md`](../specs/fill-in-split/decisions.md), §6 and §11. Built
  by [#849](https://github.com/Raketa02/Raketa/issues/849) (Fill in and You’re in) and
  [#850](https://github.com/Raketa02/Raketa/issues/850) (Games, on the deck's new ids field from
  [#846](https://github.com/Raketa02/Raketa/issues/846)).

## Context

PRD #844 splits a group page's Fill in tab in two, so the page has four tabs: **Games · Fill in ·
You’re in · Friends**. Three of them carry a coral count:

- **Games** counts the cards with somebody In with the reader, across both kinds;
- **Fill in** counts the rescues the reader fits and is free for;
- **You’re in** counts the reader's live yeses in this group and sport.

**Today a badge never clears.** The segment draws its badge whenever the count is above 0,
whether the tab is selected or not, and no visit changes the count. When Marta reads both rescues
on Fill in and leaves, *Fill in 2* is back the next time and every time after, until those games
are gone. A badge that never clears stops saying *something happened*, and nobody follows it into
the tab any more.

The product owner ruled that **a badge counts what you haven't seen** (Q2b), on all three tabs:

- what a tab shows is seen while it is on screen, and on Games that is the kind the switch is on;
  the tab on screen draws no badge, whatever it counts (Q10);
- a row is known by its id, so a row that only changed stays seen (Q10);
- only a row the player has not had on screen brings the badge back.

Someone has to remember which ids were seen, and it has to outlive the page. The product owner's
rule for every choice below is theirs, in their words: *"The badges are there just to inform that
something new had happened to make the user engage with the tab."* **A badge is a nudge, not a
ledger**:

- it never costs an extra request;
- it never holds up a tab switch or a navigation;
- it never adds machinery for the sake of being exact;
- **wherever being exact would cost one of those, the simpler rule wins.**

The ids are already on the phone. The Fill in read carries the bookings it counts, the live-yeses
read carries the proposals, and from #846 the deck read carries the ids of the cards with somebody
In, across both kinds.

**The phone already keeps lists like this one.** Home's *new until opened* keeps the booked games
whose details this account opened (`openedGames`, #556), and the called-off games it removed from
Home (`dismissedGames`). Both sit in the phone-preferences store, per account, forgotten at sign-out,
and **both still stand outside ADR-0188 §2's table**: the store's own comment says their record is
owed. This record doesn't settle them. It is written first so that this value doesn't join them.

**Why the phone.** What the phone-preferences store keeps **survives Android killing the app**, and
reading or writing it **costs no request**. Those are the two things a nudge needs.

Rejected on the way (Q11):

- **"Seen" on the server**, shared by the player's phones. It needs new endpoints and new storage,
  a write on every tab switch, and a read before a badge could be drawn. Home's envelope pays that
  price because what it counts is already the server's (ADR-0205); a group page's tabs don't need
  to.
- **Memory only**, for as long as the page or the app is open. Android kills a backgrounded app
  freely, and every badge the player had cleared would come back on the next open. That is exactly
  the furniture the ruling is meant to remove.
- **The keychain.** It is the credentials store (ADR-0008), for the reason ADR-0188 already gives.

## Decision

### 1. A new value in the phone-preferences store: the rows seen on a group page's tabs

The store gains one value: **the ids a player has seen on a group page's tab**. It is kept

- **per account**, as every value in ADR-0188 §2 is, so a second account on the phone starts with
  nothing seen;
- **per group, sport and tab**, and **on Games also per kind** (Competitive or For fun), because
  the deck shows one kind at a time, and the other kind's cards stay unseen until the switch moves
  to it.

| Tab | A row is | Known by |
| --- | --- | --- |
| **Games** | a card with somebody In with the reader, of the kind on screen | the card's id on the wire, from the deck's ids field |
| **Fill in** | a rescue still standing | its booking |
| **You’re in** | a live yes in this group and sport | its proposal |

**A badge is the ids its tab counts now, minus the ids seen.** A count of 0 draws nothing. It is a
pure rule in the player app's proposals domain, beside the Fill in rules, and the store only keeps
its result.

### 2. Only ids, and only the ones a tab still counts

**What is kept is a set of ids and nothing else**: never a row, a time, a count or anything the
server would need. Each time a tab's set is written, it is **cut back to the ids the tab still
counts**, so a game that has gone leaves the set with it. The set is never bigger than the tab, and
the value can't grow without limit.

### 3. Forgotten at sign-out

It is emptied with the rest of the store, **whichever way the session ends**: a tap on *Sign out*,
or the server refusing the credentials (ADR-0188 §3). The next person on the phone starts with
nothing seen, and their badges show their own news.

### 4. A stale or unreadable value means *nothing seen*

As ADR-0188 §4 says for every value, **a value the store can't read, or doesn't recognise, gives
the default**, and here the default is *nothing seen*. It is never an error and never a screen.
The worst it can do is show a badge the player had already cleared. An id that has stopped being
counted is simply dropped at the next write (§2).

### 5. Never waited on

- **Read once**, when the page needs it, and never before a first frame. This is where it departs
  from ADR-0188 §4, which reads a value before the first screen that uses it.
- **Until it has been read, no badge is drawn.** The badge sits outside the layout, so when it
  arrives nothing moves, and it never shows a wrong number that changes. That keeps §4's purpose,
  no screen drawing one thing and then jumping to another, without its read on the way in.
- **Written without waiting.** No tab switch, navigation or first frame waits on a write, and a
  write that fails loses only the next launch's copy, as every write to the store does.

### 6. Per phone, on purpose

Each phone keeps its own "seen". A quick look on one phone doesn't clear a badge on the other.
That is accepted: the cost of the other answer is the server storage rejected above.

### 7. Where being exact costs, the simpler rule wins

Every detail the tickets meet that this record doesn't settle follows the product owner's rule
above. One is settled already: *on screen* means the page is visible and not covered by a pushed
screen or a sheet, but **marking a tab's ids seen when the tab is opened and again when it is left
is enough**, if following the cover turns out to be fiddly.

## Consequences

**Easier**

- A badge means one thing across the bar: *something happened since you last looked*. One look
  clears it, and only real news brings it back.
- No new endpoint and no table. The badges run on the reads the page already makes, and older
  installed apps are untouched.
- The store's table has a record for every per-account value except the two this record found
  already there (`openedGames` and `dismissedGames`), and those two are named as owed.

**Harder**

- **The store now holds five recorded per-account values, plus the two owed, and the argument for
  the next is easier than ever.** ADR-0188 warned of this. Holding the line is still a review
  discipline, not a lint rule.
- **"Seen" is per phone.** A player with two phones sees a badge on the second that they already
  cleared on the first. The ruling accepts it; nothing in this record fixes it.
- **The phone decides a number it once read from the server.** Fill in's `badge` and the deck's
  `games_badge` stop being read, and the phone works the count out from rows. Both fields stay on
  the wire, because older installed apps still read them, so for a while two answers to *how many*
  exist with different meanings. Retiring them is a later contract change, if ever.
- **A row's id is the identity, so a row that changes never counts again.** A new version dealt, a
  join, a deadline moved: none of them brings the badge back. That is the ruling (Q10), but it
  means a big change to a game the player has already seen can pass without a badge.
- **The live-yeses read moves to every page open.** You’re in's badge needs it, so it starts as
  the page opens instead of when the tab is drawn. It is the read the tab makes anyway, made earlier
  and never waited on, but a visit that never opens You’re in now makes it too (the log's §12, call
  2, accepted in PRD #844).
- **On Games, the other kind's unseen cards hide while you're on Games.** The tab on screen draws
  no badge, so they show only once you leave the tab. That is the ruling (Q2b, Q10), and moving
  the switch to that kind is what marks them seen.
- **The first run after shipping shows today's counts**, because nothing has been seen yet. Each
  badge clears on the first visit to its tab.
- **A cleared phone or a failed read brings old badges back.** It is the safe side of the mistake
  (§4), but the player sees a badge for something they had already looked at.
- **A write is a JSON list per group, sport and tab.** It is small and bounded by the tab (§2), but
  a player in many groups and sports keeps many short lists, and they are only cut back when that
  tab is written again.
