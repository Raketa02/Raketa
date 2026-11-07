# ADR-0202 — Friends: a request between group-mates, and a game among them that books the court when it is sent

- **Status:** Accepted — **§4 amended [below](#amendment--2026-11-07-a-friends-ask-for-a-level-waits-on-their-home) on 2026-11-07** (Q129)
- **Date:** 2026-11-06
- **Supersedes [ADR-0199](0199-a-player-is-known-by-their-nickname.md)'s line *"there is no
  friendship in Raketa (the Friends tab is out of scope)"***, in its rejected alternative *Keep the
  name, show it to friends only*. There is now friendship (§1). The alternative stays rejected: the
  Name is retired, and a friend reads the same nickname as everybody else.
- **Supersedes [ADR-0183](0183-a-group-is-a-crowd-at-a-home-club-and-its-link-never-changes.md)
  §13's *no friends list***, the half of §13 that
  [ADR-0189](0189-a-yes-books-a-court-and-the-club-is-the-seller.md) §8 kept standing. A player has
  friends, held across all their groups (§1). *No removing members* still stands.
- **Amends ADR-0189** in three places, and its *Specified by* range now reads Q1–Q128:
  - **§8's bullet on 0183 §13.** *No friends list* no longer stands (above).
  - **§2's *the last yes books the game*.** A Booking has a second birth: a **friends game**, booked
    the moment its sender sends it, before anybody else says yes (§5). The deck's games still book on
    their last yes.
  - **§4's *nobody ever pays more for an empty seat*, and the mechanics §12.1's *no player ever pays
    another player's share*.** Both gain one exception, the **Cover**: the sender of a friends game
    pays for a seat that isn't his, and only up to the maximum he agreed to above his button (§6).
    It applies to friends games alone; the deck's, Post a game's and rescues' money is unchanged.
- **Amends the official-group court rule** of the mechanics §4.3 and Q29, *another club's court
  only when the club has no court at any hour those players share in the next 14 days*, which no
  ADR decided and [ADR-0196](0196-only-raketa-until-raketa-is-the-clubs-booking-software-and-a-clubs-cancel-moves-the-game.md)
  §3 restated for the owed card and §1 kept among *What stays*. **The rule is now hour by hour, and the club's switch is on by
  default** (§7). It serves the Games deck (the owed card included), Post a game and the friends
  card alike. The proposals rule note that states the old rule
  (`backend/.claude/rules/proposals.md`) is rewritten by
  [#746](https://github.com/Raketa02/Raketa/issues/746), with the code, and stays true of the code
  until then.
- **Extends [ADR-0193](0193-a-block-keeps-two-people-off-one-court-and-the-blocker-can-see-it.md)
  §2's *it reaches nothing else*** by one reach. A block also **ends a friendship** and any open
  request between the pair, and a request the blocked person sends later is **never shown to the
  blocker** (§2). §3's *byte for byte the same whether or not she blocked him* now holds against a
  removal: what the blocked person reads is exactly what a silent removal, or a request set aside,
  would show them.
- **Leaves standing** [ADR-0190](0190-money-goes-through-one-port-and-a-notice-is-read-once.md)'s
  one port (a cover is a Seat charge, held, taken and let go by the steps every seat charge uses);
  the club's cut-off as **the one deadline, the same for everyone in the game** (ADR-0189's
  2026-10-10 amendment); [ADR-0201](0201-the-other-kind-is-a-door-and-a-changed-intent-leaves-the-cards-you-havent-answered.md)'s
  one setting (the Friends tab's switch sets one game's kind, never intent); the proposals rule
  *no route makes a proposal* (the friends card is a read, and a friends game is no proposal); and
  ADR-0183 §4's **Group link**, which a **Friend link** is not.
- **Does not decide** finding players outside your groups, friend suggestions, mutual friends or a
  friends feed; chatting with a friend outside a game; a limit on friends; a friends-first head
  start on rescues, which was removed before and stays removed; changing a sent game's court or
  hour; a friend taking over the sender's cover; iOS keeping a link through an install with no
  second tap; the club website showing friends games differently from other bookings; and what a
  club's cancel that no court absorbs owes a friends game's **guests**, who have no deck in its
  group to be dealt an owed card in.
- Settles PRD [#743](https://github.com/Raketa02/Raketa/issues/743), decided in the friends grilling
  on 2026-11-05/06 (Q1–Q46 there, the mechanics' Q128) and written by
  [#744](https://github.com/Raketa02/Raketa/issues/744). Specified by
  [`docs/specs/friends/`](../specs/friends/README.md). Built by the backend's
  [#745](https://github.com/Raketa02/Raketa/issues/745) (friendships),
  [#746](https://github.com/Raketa02/Raketa/issues/746) (courts hour by hour),
  [#748](https://github.com/Raketa02/Raketa/issues/748) (the link),
  [#749](https://github.com/Raketa02/Raketa/issues/749) (asking for a level),
  [#750](https://github.com/Raketa02/Raketa/issues/750) (the friends card),
  [#751](https://github.com/Raketa02/Raketa/issues/751) (sending) and
  [#752](https://github.com/Raketa02/Raketa/issues/752) (empty seats, the warning and leaving); the
  club website's [#747](https://github.com/Raketa02/Raketa/issues/747); the public site's
  [#755](https://github.com/Raketa02/Raketa/issues/755); and the player app's
  [#753](https://github.com/Raketa02/Raketa/issues/753),
  [#754](https://github.com/Raketa02/Raketa/issues/754),
  [#756](https://github.com/Raketa02/Raketa/issues/756)–[#760](https://github.com/Raketa02/Raketa/issues/760).
  Walked by [#761](https://github.com/Raketa02/Raketa/issues/761).
- **§4 amended 2026-11-07** by [its own amendment](#amendment--2026-11-07-a-friends-ask-for-a-level-waits-on-their-home) (the mechanics Q129, PRD
  [#762](https://github.com/Raketa02/Raketa/issues/762), written by
  [#763](https://github.com/Raketa02/Raketa/issues/763)): an ask waiting on a friend is a card on their
  Home, one per sport, until they have the level or say *Not now*, and its bell row lives only while
  the card does. It also amends [ADR-0200](0200-a-level-is-asked-where-play-begins.md) §7's Home card,
  which the ask's card is drawn instead of while it is there.

## Context

**Tomek can't play with the people he knows.** Tomek plays padel at 2,71. He is in two groups:
**Ogrody open play**, the official group of the club Ogrody 33, where Ewa and Magda play, and
**Kazimierz crew**, a group players made, where Ania plays. He would like to play this Saturday
morning with the three of them.

- **Raketa has no friendship.** The group page already has a Friends tab, which draws a court with
  Tomek in one seat and a **+ Friends** button. The picker behind it always reads *"Nobody you know
  here yet"*, and ADR-0199 says *"there is no friendship in Raketa"*.
- **The only way to play together is luck.** Tomek can hope the Games deck deals the four of them
  onto one card, or post a game and hope Raketa offers it to them first. Ania isn't in Ogrody, so no
  Ogrody card can ever name her.
- **Nothing keeps a good partner.** Members lists the people Tomek meets, and the result screen
  shows who he just played with, but neither lets him keep them.
- **A friend who isn't on Raketa can't be brought in.** Zofia plays with Tomek every week and has
  never installed the app. The only link Tomek can share is his group's.

**Official groups run out of courts.** Ogrody 33 gives Raketa 20 court hours a week, and by Friday
most are booked. An official group plays only at its own club unless the club switches on *"Offer
our groups other clubs' courts when ours are full"*, which is off by default. Even then, another club
is used only when the players share **no hour at all** at the club in the next 14 days. Tomek and his
friends share Saturday mornings and Tuesday 21:00. Saturday 10:00 at Ogrody 33 is gone, and Wisła
Park, 4 km away, has a court free then. Because they still share Tuesday 21:00, they get Tuesday or
nothing. Players who can't book drift away, and the club loses them too.

**A friends game can't wait for its last yes the way a deck card does.** A deck card holds no court
while it fills: the court goes to whichever card fills first. Four friends who agreed on WhatsApp
to play Saturday 10:00 would lose the court to a stranger's card while Ania looks for her phone.

**The alternatives:**

- **Book when the last friend accepts**, as the deck does (the brief's own wording). The court is
  sold to whoever fills first, so the game the friends agreed on is the one most likely to vanish.
- **Hold the court, without money, while friends answer.** It keeps the hour off sale with nothing
  guaranteed, which the product owner ruled out: a held court that nobody pays for costs the club a
  sale.
- **Book at send, each friend paying only their own share.** Then nobody stands behind an empty
  seat. The court was sold at send, so an empty seat at the cut-off would either call off a game the
  club already sold or leave the club unpaid for it.
- **Make friends on a link by itself** (the brief: *"when they sign up through it, you are friends
  automatically"*). A link pasted into a big chat would make dozens of friends nobody chose, and
  MATCHi's shared profile link adds nobody by itself either.
- **A link from the nickname** (mock 4's `rakieta.app/f/tomek-k`). Anybody could guess anybody's
  link, and a rename would break it.
- **Tell a sender that the request was declined.** LinkedIn and Strava don't, and a *no* between
  two people who still meet in a group is a confrontation nobody asked for.
- **Friends per group.** A partner from Kazimierz crew could never be seated in an Ogrody game, which
  is exactly Tomek's Saturday.
- **Use other clubs above a fill threshold** (the brief's *70%*). At 70% booked, Saturday 10:00 at
  Ogrody 33 may still be free, and a threshold would offer Wisła Park beside it, sending the club's
  own players away from an hour it could sell. At 30% booked, the one hour four friends share may
  already be gone, and they would get nothing. Raketa has no measure of a club's fullness today.

**Every rival books at once and holds one person responsible.** Playtomic's split booking has *"the
owner"* book, the others pay until 2 hours after the match, and the unpaid rest is charged to the
owner. MATCHi holds the full court on the booker's card and charges unpaid seats at the regular
price. Playmore's organiser pays the whole court, and its challenge reserves the court at once,
*"you pay only when the rival accepts, at the latest a day before the match"*.

## Decision

### 1. A friend is someone who asked, and was answered yes

A **Friend** is someone from your groups whom you asked and who said yes, or someone who opened
your link and said yes (§3). **Friendships are per pair of players, across all their groups.** A
friendship survives either of them leaving a group, and ends when either account is deleted.

**A Friend request** is a request and an answer:

- **Asking.** Nobody asks themselves, and nobody asks while a request of theirs to that person is
  open. The request records **where it was made**: a group (Members, or a game's faces in it), the
  record, a result, or a link.
- **Accept** makes them friends. The requester is told *"Kuba said yes — you're friends"*, and the
  tag turns to *friend* everywhere at once.
- **Not now sets the request aside without ending it.** The card leaves the reader's Home, and the
  request stays open. The requester keeps reading *request sent*, is never told, and can't ask a
  second time. The reader can still accept later, from the requester's Members row, their record, or
  You › Friends › *Asked you*.
- **Crossed requests make friends at once.** When two people ask each other before either answers,
  nobody has to accept.
- **Cancel and remove are silent.** The requester cancels from the person's record. Either friend
  removes the other from the record, behind a confirmation. Nobody is told, and removing a friend
  never touches a game already sent or booked.

**Where it happens:**

- **Members**: a black **+ Add** pill on everybody who isn't your friend, *request sent* (amber) once
  you asked, *friend* (green), and a black **Accept** on somebody who asked you. The rows keep
  today's design; only the pill or tag on the right is new. The administrator's view of an official
  group's Members has no pills.
- **The player record**, which opens from any face: **Add friend** and **Block** side by side at its
  foot. The left button follows the relation: **Request sent ▾** (Cancel request), **Accept**
  (coral), **Friend ✓ ▾** (Remove friend). Somebody you blocked shows only **Unblock**, full width.
  Your own record has neither.
- **The result screen**: a **PLAYED WITH** card between the score and the sportsmanship card, with
  Members' pills, hidden once everybody on it is your friend.
- **You › Friends**: three tabs, **Friends · Asked you · You asked**, a count on *Asked you* while
  requests wait, **Accept** and **Cancel** on the rows. **+ Add friends** opens a sheet: your groups,
  each with *"8 members · 2 to add"*, opening its Members; and your link (§3).
- **Home**: a **FRIEND REQUESTS · n** row under the friends game invitations and above Your games,
  each card naming the group the request was made in and its sport, with **Not now** and **Accept**.
  The row and its title are gone once every request is answered.

**Notices**: a friend request (pushed once per request, never again for it) and *you're friends*,
both always on, pushed and kept in the bell. Answering a request on Home clears it from the bell.

### 2. Only the reader's own relations cross, and a block ends a friendship

**A response carries only its reader's relations.** The reader's relation to a player is one of
**none · sent · asked you · friend**. It is lent, for a set of players, to Members, the record, deck
tiles, game details, booked games, Fill in and the result. **Faces carry only *friend***, and only
the reader's own: Kuba never learns that Tomek and Magda are friends. The mechanics' Q68 tag,
*FRIEND*, now applies.

**A block ends a friendship.** When either of two friends blocks the other, the friendship and any
open request between them end, silently, with nobody told. **A request from a player the reader
blocked is never shown to the reader**, read live from the blocks: Michał, whom Tomek blocked, can
ask again, reads *request sent* forever, and Tomek never sees it.

This is one more reach for a block, beyond ADR-0193 §2's *one court*. It keeps §3's promise: nothing
Michał reads tells a block from a removal, and his *request sent* reads exactly like one set aside.
**A friends game respects blocks as the deck does**: a line-up with a blocked pair in it, either way
round, is refused with *"These four can't all play together. Swap someone."*, which names nobody.

### 3. The friend link puts its owner's request on the opener's Home

**A Friend link** is the public site's `/f/` and a **code**: random, shaped like a group's code, made
on its owner's first read of it, never reused, and one per player. **New link** replaces it, and the
old code then reads as not found (`friend_link_not_found`).

**Opening a code never makes friends by itself.** As a signed-in player, it records the owner's
request to the opener, made by *link*, which Home shows as *"Tomek wants to be your friend · Invited
you to Raketa"* with **Accept** and **Not now**. This is true for a new player like Zofia and for Ania,
who already has the app. Unless:

- the opener is the owner, or they are already friends: nothing happens;
- the opener already asked the owner: the requests cross, and they are friends (§1);
- the owner blocked the opener: the owner's request is swallowed, and nothing reaches the opener's
  Home.

**It travels as a group link does.** In production it is a universal link on iPhone and an app link
on Android, like `join/`:

- **App installed, signed in**: Raketa opens, and the request is at the top of Home.
- **Signed out, or no account**: Raketa opens on sign-up. The link waits through sign-up and
  onboarding, then lands on Home with the request.
- **Not installed**: the public site's page reads *"Tomek invited you to play on Raketa"*, with his
  face, the store buttons and **Open in Raketa**. After installing, an iPhone has forgotten the link,
  so she taps *Open in Raketa* once more. On Android the store button carries the link as the
  **install referrer**, which the app reads once on first launch, **for group links too**. A replaced
  or unknown code shows *Nothing at that link*.

The public surface gains one read of a code: the owner's nickname and face, or
`friend_link_not_found`, and nothing else about them.

### 4. A friend can be asked to get a level

A friend with no level in the picker's sport is greyed with *No padel level yet* and an **Ask Zofia
to get a padel level** button. **Ask for a level** sends her a notice, *"Tomek wants to play padel
with you. Get your padel level so Tomek can add you."*, which opens that sport's questionnaire. When
her first level in that sport arrives, Tomek is told *"Zofia has a padel level — you can seat Zofia
now."* **He can ask her once per sport**; a second ask is refused. Both notices are always on,
pushed and kept in the bell.

*(Amended 2026-11-07 — see [the amendment below](#amendment--2026-11-07-a-friends-ask-for-a-level-waits-on-their-home): the ask is also a card on her
Home, one per sport, until she has the level or says Not now, and the *level asked* row is kept in the
bell only while that card is on Home.)*

**No sentence says *her* or *him* about another player.** A gender never crosses to another player
([ADR-0096](0096-gender-preference-mutual-gate-invisible-to-the-scorer.md); the glossary's
**Gender**), so PRD #743's *her padel level*, *so he can add you* and *seat her now* are written
without one ([the words §29](../specs/matchmaking/the-words.md#29-friends)).

### 5. A friends game is composed on a group's Friends tab and booked when it is sent

**Composing.** On a group's Friends tab, Tomek sits in one seat:

- He picks **Competitive** or **For fun** above the court, for **this game only**. It never changes
  his Play intent, and nobody's intent excludes them: the invitation names the kind and the friend
  decides.
- **+ Friends**, or a **+** on the court, opens his friends as a picker, sorted by level in this sport,
  highest first, each with *"2,75 · established"*. When the seats are full (three in doubles, one in
  singles) the remaining rows grey out.
- **Any friend may be seated**, from this group or any other. A friend who isn't a member plays as a
  **Guest**: the game is on her Home, in its chat and on its result, and she never sees the group's
  deck or Fill in.
- **On Done**, Raketa seats the picks into the **evenest sides**. Tapping one face and then another
  swaps them, and a face's × takes them off. Until every seat is filled the court reads *Seat 1 more
  friend*, and there is no card.

**The card.** Once every seat is filled, Raketa builds **the friends card** under the court: the
deck's card without the player tiles. It shows the sides, the balance, the overlap of the four
weeks, and a court with the share, *Court available · Sat 10:00 · Ogrody 33 · Court 3 · 25 zł each*.

- **The proposed court** is the soonest hour that can still be sold (its book-by ahead) up to 14
  days out where all four are free, a court is free under the group's court rule (§7), and none of
  the four already has a game. Failing that, it is the soonest such hour where most of them are
  free.
- **Pick a different court** opens *Find a court*: every bookable club, hour and court in that window
  under the court rule, by day, **tinted by how many of the four are free** (*Everybody free*, *Ania
  busy*, *Magda and Ania busy*), where *busy* means outside that player's weekly hours. Hours where one
  of them already has a game are left out. **Every row can be picked**, and picking one updates the
  card.
- **The card's rules**: blocks apply (§2); every seated player needs a level in the sport
  (`no_level`) and must be the sender's friend (`not_a_friend`). **The level window, the kind's
  tolerance and gender preferences don't apply**, because friends choose each other.
- **It is a read.** It makes no proposal and books nothing, so *no route makes a proposal* holds.

**Sending books the court.** *Send game and pay 25 zł* opens a send sheet that asks how to pay
(§6). Its button **books the court at once**:

- The court is booked on the court-hour's unique index; a send that loses the race is refused
  `court_just_taken`, and the phone re-reads the card.
- A **Booking** is born **booked by a friend**, with an id of its own, since no proposal precedes
  it. It records the sender (In), the **Invited seat** of each other player, the kind, the pay mode,
  the court and its number, the sides, the cut-off as the club set it, and the pool. It opens the
  Game and its chat at send, as the fill does; each invitee joins the chat on accepting.
- Sending withdraws the sender's other yeses at that hour, and accepting withdraws the invitee's, as
  a fill does.
- **A sender has at most 2 friends games waiting for answers**, and each friends game counts as one
  of every player's games that week. Accepting is refused, with a sentence, when the invitee's week
  is full or they already have a game at that hour.
- **A sent game's court and hour never change.** To change them, Tomek calls it off and sends again.
- **A club's cancel** moves a friends game, or calls it off, as it does any booked game. The club
  sees an ordinary booking.

**The invited seat** is held for its invitee for **24 hours**, never past the cut-off when the
invitation is made before it, and never past the start when made after it. It ends:

- **accepted**: she is In, and her card moves to her Your games;
- **declined**, with *Not this time*, which takes the card off her Home;
- **run out**: silence counts as *Not this time*.

The invitation is a push, a bell notice and a card in a **FRIENDS GAME · n** row at the very top of
Home: *"Tomek's game"*, the time left, the four faces (✓ on those In, faded on those still to
answer), the hour, club, court, sport and kind, and **Not this time** / **Accept and pay 25 zł**. Home
reads, top to bottom: friends game invitations, friend requests, Your games *(amended 2026-11-07: the
asks for a level stand between friend requests and Your games — [below](#amendment--2026-11-07-a-friends-ask-for-a-level-waits-on-their-home))*. Tomek's own game sits
under **Your games** from the moment he sends it (*2 of 3 friends in · waiting for Ania*), and the
Friends tab goes back to an empty court. When the last seat is taken, all four get *It's a game!*.

**An empty seat.** A declined or run-out seat is told to Tomek (*"Ania can't make it"*, *"Ania didn't
answer"*) with two choices. **Invite a friend** sends the same kind of invitation to another friend.
**Open to Ogrody** makes it a **Rescue**: a *Seat open* card in the decks of members who fit, a row in
Fill in's *Seats to fill*, and Fill in alerts, never offered to a guest.

- **An empty seat is not a rescue** until Tomek opens it, or the cut-off arrives (§6).
- **Anyone In may invite one of their own friends** into an empty seat, before or after the cut-off.
  The first to accept and pay, or the first rescuer, takes it, and other invitations into it end.
- **Opening a seat to the group is the sender's alone before the cut-off**, because until then the
  seat costs him money.

### 6. Split or Whole court, and the sender's cover

**The send sheet** offers two ways to pay, the **Pay mode**. *Split* below is short for *Split the
cost*, and never a forecast's **Split**:

- **Split the cost** (first): *"We hold 100 zł on your card until Fri 10:00. You pay 25 zł, plus 25 zł
  for any seat still empty then."* · **Send game and pay 25 zł**. Each friend pays her own share:
  **Accept and pay 25 zł** holds it on her card until the cut-off, like any Raketa seat.
- **Pay the whole court**: **Send game and pay 100 zł**. Friends **Accept** without paying, and their
  card says *"Tomek paid the court"*.

**The Cover** is a Seat charge paid by the sender for a seat that isn't his. **At send, the sender's
own share and one cover per other seat are authorised together, all or nothing, with the sender
present**, so a bank's confirmation is completed in the app at that moment, and a refused card books
nothing. With Split, an invitee's accept holds her share with her present; with Whole court, an
accept holds nothing.

- **Every cover stays held until the cut-off**, or is checked at send and held at the **Holding
  time** when the game is far off, like any seat charge. **At the cut-off a cover is taken only for a
  seat without its own payment, and let go otherwise.** Covers are never let go and held again in
  between: that would need a new hold on the sender's card without him there, which his bank can
  refuse or ask him to confirm, the day an accepted friend leaves.
- **While the sender covers the game** (Split with him In, or Whole court), **it is never called off
  at its cut-off.** Each seat without its own payment is covered and, if empty, opened as a Rescue.
  A later rescuer's share refunds the cover for that seat, less exactly the fee kept on it, as a
  late leaver is refunded.
- **The cover warning.** With Split, once, **24 hours before the cut-off**, when a seat still lacks
  its own payment: *"Saturday 10:00 · 1 seat still empty. At Fri 10:00 you pay 50 zł: your 25 zł and
  Ania's seat."*, with **Invite a friend**, **Open to Ogrody** and **Call it off**. A seat that empties
  inside those 24 hours puts the same line in the notice that tells him.

**Leaving.** A friend who accepted leaves free until the cut-off, like any Raketa game: her hold is
let go and her seat is empty again. Before the cut-off the sender has two choices:

- **Call it off for everyone**: every hold and cover is let go, everyone is told, nobody pays, and the
  court is the club's again.
- **Leave · the others play on**. With Split, his share and every cover are let go and **the booking
  becomes an ordinary one**: his seat and every seat without a player become rescues at once, and a
  seat still open at the cut-off calls the game off with nobody paying. With Whole court, his covers
  stay, and his own seat opens as a rescue whose taker pays him back.

Nobody else ever pays his share, and nobody takes his cover over. After the cut-off every leave,
his included, is a late leave, and the seat is a rescue at once.

**This is the one place a player pays for another player's seat.** It applies to friends games
alone, and only because the sender agreed to the maximum shown above his button: the Payment
Services Act's art. 49b (PSD2 art. 75) allows blocking an amount only with the payer's consent to
that exact amount, and under the Civil Code the cover is his own obligation, taken on at send. **The
amount he agreed to is recorded with his terms acceptance.** A lawyer is asked before launch whether
*Send game and pay 25 zł*, with *"We hold 100 zł … plus 25 zł for any seat still empty"* stated above
it, makes a valid order for up to 100 zł under art. 17 ust. 3–4 of the consumer rights act.

### 7. Official groups use other clubs' courts hour by hour, and the switch is on by default

**The source of a pool's courts answers per hour.**

- **For an official group**, it answers the home club's free courts. **Only at an hour where the
  home club has none**, and its switch is on, it also answers other Raketa clubs within the club's
  distance (10 km by default), listed after the home club and **marked as offered because the home
  club is full**: *Ogrody 33 is full at 10:00*.
- **For a player group**, it is unchanged: the home club first, then other clubs within 10 km.
- **The club's switch** keeps its words, *"Offer our groups other clubs' courts when ours are
  full"*, and is now **on by default**, for existing clubs too. A club that turns it off gets today's
  *only ours*.

**One source serves every way a game is made in a group**: the Games deck (its picks and the owed
card), Post a game's grid and slot sheet, and the friends card with its court list. A group never
has two court rules. So ADR-0196 §3's second step, *another club at the same day and hour*, now
reaches an official group too, whenever its club has no free court at that hour and the switch is
on.

**Why hour by hour.** The club never loses an hour it could have sold, because its own court is the
only one offered whenever it has one. Players are never left without a game at an hour it can't
serve. No threshold has either property.

### 8. Where it lives

- **Friends** is a new bounded context, **event-sourced**. Its **Friendship**, one stream per pair,
  records a request and where it was made, setting it aside, cancelling it, a crossed request,
  friends made (accepted or crossed) and a friendship ended (removed or blocked). Its **Friend link**,
  one stream per player, records a code made and a code replaced. It records **Ask for a level**
  *(and, since [the 2026-11-07 amendment](#amendment--2026-11-07-a-friends-ask-for-a-level-waits-on-their-home), an ask set aside)*, and
  hears the rating context's first level in a sport to answer it, and the blocks to end a
  friendship. It lends the reader's relations through a demand port and tells Notifications.
- **Bookings** gains the birth *booked by a friend*, the Invited seat with its clock, the sender's
  choices and the covered booking's cut-off.
- **Payments** gains the Cover, a Seat charge whose payer is not its seat's player.
- **Proposals** gains the friends card and the court list, both reads, and Home's two new rows
  *(three since [the 2026-11-07 amendment](#amendment--2026-11-07-a-friends-ask-for-a-level-waits-on-their-home))*.
- **Notifications** gains, all always on, pushed and kept in the bell: the friend request, *you're
  friends*, the friends game invitation, *can't make it* and *didn't answer*, the seat invitation,
  *seat taken*, a friends game called off, the cover warning, *level asked* by a friend (not the
  once-per-account *Get your level*), and *level got*. *(Amended 2026-11-07, [below](#amendment--2026-11-07-a-friends-ask-for-a-level-waits-on-their-home):
  a *level asked* is kept in the bell only while its card is on Home.)*
- **Club courts**' setting defaults to on, and the club website says *"at an hour your courts are
  full"*.
- **The public site** gains `/f/<code>`, and the app-link files gain `/f/`.

## Consequences

**Easier**

- **Tomek plays with the people he knows**, from any of his groups, at the hour they pick, without
  waiting for the deck to deal them together.
- **The club sells the hour the moment it is sent**, and a friends game is never called off for an
  empty seat. Every rival's split booking works this way, so clubs and players already know it.
- **An official group can always find a court**: other clubs fill only the hours its own club can't,
  and the club loses none it could have sold.
- **A friend outside Raketa arrives through a link** that lands her on Tomek's request, and a
  leaked link is turned off with one tap.
- **A good game becomes a lasting partner**, from Members, the record or the result.

**Harder**

- **Raketa now moves one player's money for another's seat.** The money model carries an exception
  where it used to carry a rule. It rests on the words above the sender's button, on one lawyer's
  answer (open item O3), and on the amount being recorded with the terms. If the lawyer says no, the
  send needs a confirm step of its own before any friends game takes real money.
- **A Split sender's card carries the whole court for days**: four holds, 100 zł, from Monday to
  Friday, and with two games waiting, eight. A card near its limit refuses the send. A far-off game
  adds a card check at send and four holds again at the holding time, which open item O7 has not yet
  checked with Stripe.
- **A Booking now has two births, and an empty seat that isn't a rescue.** An invited seat has its own
  24-hour clock and job, and every read that shows a booking's seats must tell *waiting for Ania*,
  *empty*, *open to the group* and *paid* apart: Home, the details, Fill in, the deck and the club
  website's Bookings.
- **"A game plays full or not at all" gains an exception.** A covered booking is never called off at
  its cut-off, and it turns ordinary when its Split sender leaves. The cut-off job branches on whether
  a booking is covered, and a mistake there either charges a sender who left or calls off a game the
  club was paid for.
- **A booking's players are no longer all members of its pool.** A guest is on its Home, chat and
  result, and in no deck or Fill in of its group. Every read that assumed a booked player is a
  member must now say what a guest sees, and a rescue is never offered to one.
- **Every face carries a relation.** Members, the record, deck tiles, game details, booked games,
  Fill in and the result each ask Friends for the reader's relations, one more input on reads
  ADR-0197 already measured as expensive.
- **Not now never ends, and a block hides behind it.** A request set aside stays open with no
  expiry, so a player who pressed *Not now* by mistake must find the person to accept. The sender
  can't ask again. That silence is what keeps a block undetectable, so neither can be shortened
  without the other.
- **Clubs that never chose other clubs' courts now have them.** The default flips for existing clubs
  too, so an official group may play at Wisła Park on Saturday at 10:00 without its club ever
  touching the switch. The club website's line says so, and the switch still turns it off.
- **The court source changes under three readers at once.** The proposer's *no shared hour in 14
  days* refusal goes, and the deck, the posting grid and the owed card change with it, along with
  their seeds and tests ([#746](https://github.com/Raketa02/Raketa/issues/746)).
- **An iPhone forgets the link through an install**, so a new player taps *Open in Raketa* twice.
  Android carries it through the install referrer, for group links too.
- **A link is the one place a block could be guessed.** A blocked player who opens the blocker's
  link finds nothing on Home, where anybody else finds a request. Swallowing it is still right, since
  showing it would offer friendship across a block, but the silence is a tell §2 otherwise avoids.
- **The drift checks are red** between each backend ticket and the client ticket that regenerates from
  it, for the player app and the club website, accepted until the branch's end.

**Neutral**

- **The club sees an ordinary booking.** Its Bookings page, money and payouts are unchanged.
- **The Friends tab's switch sets one game's kind.** ADR-0201's door is a deck's, and a friends game's
  kind is chosen per game.
- **A friends-first hour on rescues stays removed** (the mechanics §22.1). An opened seat is a rescue
  like any other.
- **A Friend link is not a Group link.** One joins a group; the other asks a person.

## Amendment — 2026-11-07: a friend's ask for a level waits on their Home

§4 made an ask a notice and nothing else: a push, and a row in the bell. **A friend asked for a level
had nowhere to find the ask.** Tomek asks Zofia for a padel level from Ogrody's Friends tab, and his
picker reads *Asked*. The push arrives only on a phone that registered for push: with permission
refused, or on a simulator, nothing arrives. The bell's row is history once she opens the list, one
line among her last hundred notices. Home's *Get your level* card shows only to a player rated in no
sport, names neither friend nor sport, and Zofia is rated in tennis. **A missed ask left both of them
stuck**, because Tomek can ask once per sport, ever. And an old row misled: once she had a padel
level by another route, tapping it only said *You have a padel level already.* Everything else a
friend waits on you for, a friend request and a friends game invitation, already stays on Home until
it is done (friends Q13). The level ask was the one friend notice without a Home row.

The product owner ruled it on 2026-11-07, in the level-ask grilling (Q1–Q8 there), and confirmed PRD
[#762](https://github.com/Raketa02/Raketa/issues/762) the same day. It is **Q129** in the
[games and fill-in decision log](../specs/games-and-fill-in/the-mechanics.md#appendix-c--decision-log),
specified in [the friends mechanics §5.1](../specs/friends/the-mechanics.md#51-the-ask-waits-on-her-home-q129),
[the screens §6.4](../specs/friends/the-screens.md#64-asked-for-a-level--n-designed-no-mock) and
[the words §29.5](../specs/matchmaking/the-words.md#295-asking-for-a-level).

- **An ask waiting on a friend is a Home card, one per sport**, in an **ASKED FOR A LEVEL · n** row
  between FRIEND REQUESTS and Your games. It names every friend whose ask in that sport is waiting,
  newest first, every one not set aside, and its button starts that sport's questionnaire from Home, as the notice does. It
  names no group, as the notice doesn't. **Home now reads, top to bottom: friends game invitations,
  friend requests, asks for a level, Your games.**
- **Not now sets aside the asks the card named, and tells nobody.** The card leaves her Home on every
  phone, and its rows leave the bell. A set-aside ask is still waiting: her first level in the sport
  answers it, and every asker is told *level got*, set aside or not. This is a **Friend request**'s
  *Not now* (§1) applied to an ask, and for the same reason: a *no* between two people who still meet
  in a group is a confrontation nobody asked for, so the asker never learns it.
- **A new friend's ask brings the card back**, naming only the askers not set aside. An ask she has
  set aside never comes back by itself.
- **The card ends on a level by any route** (the card, a group's card, the passport), read live, so it
  is gone before *level got* is delivered, **or when no asker is still her friend**. A removal or a
  block takes that friend off the card. Her own block of an asker does so at once, as §2 hides a
  blocked person's request at once; an asker's block of her, once its delivery has ended the
  friendship. It never expires.
- **The *level asked* row is in the bell, and in its number, only while its card is on Home**, matched
  by asker and sport, which is unique because an ask is once per friend per sport, ever. A friend
  request's row already follows this rule (§1, *answering a request on Home clears it from the bell*).
- **For a player rated in no sport, the ask card is drawn instead of Home's *Get your level*** while
  it is there ([ADR-0200](0200-a-level-is-asked-where-play-begins.md) §7's card), and *Get your level*
  comes back if she sets the ask aside still rated in nothing.

**Unchanged:** once per friend per sport, ever, and the picker's *Asked*; the push, its words, and
where tapping it opens; *level got* to every asker; and Home's tab badge, which counts this row no
more than it counts friend requests or invitations. §4's *no sentence says her or him* holds for the
card: several askers are *they*.

**Where it lives.** §8's **Friends** also records setting an ask aside, as one event per ask the card
names on the Friendship stream, and refuses it to anybody but the friend asked. **Proposals** reads
Home's asks for a level through a port of its own, as it reads Home's friend requests. **Notifications**
leaves a *level asked* row out of the recent notices, and out of the bell's number, while its asker is
not on the reader's card. The backend is [#764](https://github.com/Raketa02/Raketa/issues/764), the
player app [#765](https://github.com/Raketa02/Raketa/issues/765).

**The alternatives:**

- **The bell alone**, as §4 had it. It is history once opened, and a push needs a permission and a
  token a simulator never has.
- **A mark on the You › Skill passport chip**, naming who asked. The passport is opened by a player
  already looking for a level, so it reaches nobody who missed the push. It stays out of scope.
- **Home's *Get your level* card**, with the asker added. It is drawn only for a player rated in
  nothing and opens the every-sport picker, so Zofia, rated in tennis, would still see nothing about
  padel.
- **Letting the asker ask again.** A second ask is a nag, and once per sport, ever, stays (Q5 there).
- **An expiry.** An ask that ran out would be the dead end this amendment closes.

**Consequences.**

- **Easier:** an ask is found however it arrived, on a phone with or without push, and however far
  down the bell its row has sunk. A bell row never asks for a level the player already has.
- **Harder:** *Not now* on an ask is a second kind of state on the Friendship stream, beside a
  request's. The bell's list now filters two kinds live against Home, the friend request and the
  *level asked*, so each read of the recent notices asks Friends one more question. A set-aside ask
  is invisible to its friend and still waiting, so the asker's *Asked* can't tell a set-aside ask from
  an unseen one, which is the point, and a player who pressed *Not now* by mistake must find the
  passport, which the toast names, and its *Rate Padel* chip.
- **Neutral:** the asker's side is untouched, and the card reuses the friend request's shape rather
  than the dark *Get your level* card.
