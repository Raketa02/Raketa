# ADR-0196 — Only Rakieta until Rakieta is the club's booking software, and a club's cancel moves the game when nothing changes

- **Status:** Accepted — **its §3's *an official group stays at its home club*, and §1's *What
  stays*' *the official group's other clubs' courts*, amended 2026-11-06 by
  [ADR-0202](0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md)** §7. An official
  group's courts are read **hour by hour**: other clubs within the club's distance are offered only
  at an hour its own club has no free court, and the club's switch is on by default. So the owed
  card's second step, *another club at the same day and hour*, reaches an official group too,
  whenever its club has no free court at that hour and the switch is on.
- **Date:** 2026-10-12
- **Amends [ADR-0189](0189-a-yes-books-a-court-and-the-club-is-the-seller.md)** in six places:
  - **§3's three ways of working.** **Only Rakieta is the one way** until Rakieta is the club's
    booking software. *Instant* and *On request* are removed, with the choice itself (§1).
  - **§2's book-by.** It is **always the release time**. *The start minus its minimum notice* goes
    with the minimum notice (§1).
  - **§5's table.** Club courts loses *the way of working*. The Booking loses *the club's answer (On
    request)* and *waiting for the club*: **a booking is born booked** (§1).
  - **§7's club website.** Bookings loses *Accept / Refuse*. *Cancel* first tries a move (§2), and
    the Overview, once live, no longer lists *what is waiting for its answer* (§1).
  - **The *Consequences*' *Clubs on Instant can double-sell … On request trades that risk for a
    wait the club sets*.** Neither way exists. A club can still sell a handed-over hour at its own
    desk by mistake, so *double booking* stays as a cancel reason (§1).
  - **The 2026-10-09 and 2026-10-10 amendments, where they speak of a club's yes**: *It's a game!*
    with when the club answers, the club's no and silence emailed, the club's yes and court kept
    through a time to pay, and a share held at an On request club's yes. Each goes. Everything they
    decide about the fill itself stands (§1, §8).
- **Amends [ADR-0190](0190-money-goes-through-one-port-and-a-notice-is-read-once.md)'s 2026-10-10
  amendment** in one place: a share is held at the fill, at its holding time or at a rescue, and
  never at a club's yes (§1). The port is unchanged.
- **Amends [ADR-0193](0193-a-block-keeps-two-people-off-one-court-and-the-blocker-can-see-it.md)
  §4**, with its header's reach into ADR-0095 §7 and its *Consequences*' *a waiting game drops back to
  filling*. No booking waits for a club any more, so a block takes back the blocker's yeses on
  proposals still filling, and **never touches a booking** (§1).
- **Amends [ADR-0194](0194-the-games-test-console-acts-as-seed-accounts-and-writes-history-never-time.md)**
  where it names requests: the *Context*'s *the club website open in another window, to accept a
  request*, §4's *Needs Ania's yes, Instant club*, §5's *the club's answer timeout*, and the
  *Consequences*' *an On request answer*. The request situations, presses and job go, and the club
  gains three presses (§6). Its rules stand.
- **Reverses** the mechanics' decisions of three ways (Q1, Q12) and their settings (Q43's minimum
  notice and time to confirm). Ends On request's own rules: Q98, Q103's club half, Q104's and Q106's
  *asked again*, Q105, Q109's and Q112's club's yes, and Q113's *at an On request club's yes*. Keeps
  Q107's new card, which now has one source, a club's cancel (§3).
- **Lifts a rule nobody ruled on**: *the same players are never dealt the club and hour that turned
  them down*, which the On request build (#543) wrote for a refusal and the club's bookings build
  (#547) applied to a cancel (§3).
- **Replaces** PRD [#530](https://github.com/Rakieta02/Rakieta/issues/530)'s out-of-scope line *a live
  link to a club's own booking system — the Instant way, automated, later*. **Rakieta will become the
  club's booking software** instead, and a later ADR decides its shape (§1).
- Decided in the grilling of story S-01E's findings F-REQUEST-3.1, F-REQUEST-23.1 and
  F-REQUEST-22.1, with F-REQUEST-44.1 and 45.1, on 2026-10-12, and confirmed by the product owner
  ([the decisions comment on #609](https://github.com/Rakieta02/Rakieta/issues/609#issuecomment-6120454776)).
  Specified by PRD [#667](https://github.com/Rakieta02/Rakieta/issues/667), and logged as **Q121–Q123**
  in the mechanics' decision log. Built by the backend's
  [#669](https://github.com/Rakieta02/Rakieta/issues/669)–[#673](https://github.com/Rakieta02/Rakieta/issues/673),
  the club website's [#674](https://github.com/Rakieta02/Rakieta/issues/674) and
  [#675](https://github.com/Rakieta02/Rakieta/issues/675), and the player app's
  [#676](https://github.com/Rakieta02/Rakieta/issues/676) and
  [#677](https://github.com/Rakieta02/Rakieta/issues/677).

## Context

ADR-0189 §3 let a club choose one of three **ways of working**, so that clubs which keep selling at
their own desk could join. Two of them hurt the people they were meant to serve. Separately, a
club's cancel threw a game away even when nothing about it needed to change.

**On request makes a full game wait on a desk, and a shut desk kills it.** Kazimierz Padel opens
Tuesday to Sunday from 16:00 and charges 100 zł a court-hour, 25 zł a share. On Wednesday at 10:15
Paula's yes fills Marta's Thursday 19:00 game, and the four read *Kazimierz Padel answers by 11:15 ·
Nobody pays until it confirms*. Nobody is at the desk until 16:00. At 11:15 the request runs out and
the four are told the club didn't answer in time. At 16:00 the desk finds a 100 zł sale it never
saw, marked *Called off · No answer*. Every game that fills there in the morning dies the same way,
and Marta starts the WhatsApp round again. The desk, for its part, must watch a website all day,
because every request has a countdown measured in minutes.

**Instant asks the desk to keep two calendars true by hand, in both directions, for ever.** Bonarka
Arena charges 160 zł a weekday court-hour and sells the same hours at its desk and on Rakieta. It
must close in Rakieta every hour it sells by phone, at the desk or in its own system, and type every
Rakieta game into its own system. One missed entry is a double booking, the club cancels, and four
players lose their game.

**The market does neither.** Research of 6 and 12 October 2026, read from the platforms' own help
pages, terms and interface text:

- **No court platform makes a club confirm a booking.** Playtomic, MATCHi, Padel Mates, Eversports,
  ClubSpark, tenis4U, Playmore and kluby.org confirm at once. Playmore's open games book the court
  the moment a game is posted: *"Komplet graczy - gra potwierdzona, kort opłacony w całości"*
  ([Playmore, gry otwarte](https://join.playmore.pl/gry-otwarte/)). The one exception is
  CourtReserve's opt-in *Reservation Approval*, which a club uses *"to … control guest bookings, or
  review certain membership types"*
  ([CourtReserve](https://help.courtreserve.com/en/articles/4299937-optional-approval-processes-in-courtreserve)).
- **No competitor relies on a desk closing hours by hand.**
- **Every competitor that is effortless for the club has one calendar.** Either the platform *is*
  the club's booking software — Playtomic Manager handles *"incoming reservations seamlessly, both
  online and offline"* ([Playtomic](https://helpmanager.playtomic.com/hc/en-gb/articles/20535516949009)),
  and Playtomic grew by buying club software, not by linking to it — or a marketplace writes into
  the club's software through the vendor's API, and that software refuses a taken hour: *"a slot
  that's already taken will be rejected"*
  ([MATCHi ← Matchable](https://matchi.zendesk.com/hc/en-gb/articles/27989311536029)); Anybuddy's
  rented slots *"appear in your calendars just like ordinary bookings"*
  ([OpenResa](https://openresa.com/en/help/manager/billing/anybuddy)).
- **Kraków's systems have no way in.** Most of its padel and tennis clubs run on tenis4U, its squash
  clubs on Playmore, and some on kluby.org. None offers a public API, a feed or a calendar export,
  and nobody is known to write bookings into any of them. **tenis4U's terms forbid reading its site**
  by software, *"do automatycznego lub ręcznego pobierania fragmentów lub całości strony"*, or for
  *"data miningu', 'parsowania'"* ([regulamin §7](https://tenis4u.pl/regulamin/)), and its own player
  app already carries *"Otwarte sparingi"* and *"Rezerwacje współdzielone"*: it is building what
  Rakieta builds.

So the product owner decided that **Rakieta will become the club's booking software**, the one
calendar for the desk, the phone, walk-ins, season bookings, players' own bookings and the Games
deck. That work gets its own grilling. Until it ships, **Only Rakieta**, where the club hands Rakieta a
block of hours, is the one way that works without the desk.

**A club's cancel threw a game away even when another court was free.** On Thursday at 15:00 the
lights on Bonarka Arena's Court 2 fail, and the desk cancels Marta's 19:00 game. Court 3 is free at
19:00 at the same 160 zł; *Move* could have used it, but *Cancel* never offers it. The four 40 zł
holds are let go and the game is called off. Within seconds the four are dealt a new card, and under
a rule written for a club that *refused* a game it can **never** be Bonarka at Thursday 19:00 again.
The new card lands **eleventh of 33** in Marta's deck, behind every card dealt to her before it,
though the email promised *We'll look for another game for you first*.

**Players never see whether a court is indoor or outdoor.** A club records it on each court, and the
club website's own help says it is shown on a player's card. No card, Home row or game detail shows
it. When a club moves a game today, nobody is told.

Considered and rejected:

- **Keep On request with a longer time to confirm, or one that waits for the desk's opening
  hours.** A game that fills in the morning still waits most of a day, so its players still
  can't count on it, and the desk still answers every game by hand. No court platform makes a club
  confirm a booking.
- **Keep Instant, with a one-click close for an hour sold at the desk.** It is still two calendars
  kept true by hand, for ever, and one missed click is four players' cancelled game. Nobody in the
  market relies on it.
- **Read a club's own system for its free hours**, or write Rakieta's games into it. No Kraków system
  offers a way, tenis4U's terms forbid reading its site, and a vendor building open sparring of its
  own has every reason to refuse a deal. A link of that kind is out of scope, and is not a path
  Rakieta controls.
- **A release lead in hours, down to 2 hours,** so that a club keeps Rakieta's hours for Rakieta until
  shortly before the game and a game for tonight can still fill. It is a one-line change if
  last-minute games matter more. The range stays as decided (call 1, §7).
- **Move a cancelled game to any free court, or to another club or hour, without asking.** A court of
  the other kind, another club, another hour or another price changes what the players chose. Any of
  those is a new card, which each of them may say no to.
- **Move an outdoor game cancelled for weather to another outdoor court.** It rains on that one too.
- **Keep *never at this club and hour* for a cancel.** It hid the closest good game: the same hour at
  the same club, on the other kind of court or at a new price. It was written for a club that refused
  a game, and a refusal no longer exists.
- **Mark the owed card** with a ribbon or a tag. The product owner ruled no mark, for anybody. Its
  notice already opens the deck on it, and being first is enough.
- **Ask a player whether they want indoor or outdoor.** Players see the kind; they don't choose by
  it. A preference or a filter is out of scope.

## Decision

### 1. One way of working: Only Rakieta, until Rakieta is the club's booking software

**Only Rakieta is the one way.** A club hands Rakieta a block of hours: the courts and hours it offers,
which Rakieta sells alone until the **release lead** before each game. After that, unsold hours go
back to the club. **Rakieta becomes the club's booking software** later; a later ADR decides its
shape, and its features and business model get their own grilling.

**What goes**, everywhere: the club website, the player app, the backend, the test console, the seed
and these documents.

- *Instant* and *On request*, and the **way of working** as a choice: its command, route, event,
  place in the settings, and step in the setup checklist.
- The **minimum notice** and the **time to confirm**, with their bounds and the rule tying one to the
  other.
- **Requests**: the request and its acts (accept, refuse, time out, withdraw, ask again); the
  booking's *waiting for the club* and *waiting for a payment at the club's yes*; the *refused*, *no
  answer* and *a payment not in time after the club's yes* called-off reasons; the answer-by and
  taken-back fields; the seven request events and their handlers; the request-timeout job, with its
  switch, its interval and its row in the jobs register.
- **What requests told:** the desk's emails *A booking is waiting for your answer*, *X said no* / *X
  didn't answer in time* and *A game didn't go ahead*; the players' notices *It's a game! · X answers
  by …*, *X confirmed your game* and *X couldn't take your game*, said no or didn't answer in time.
- **What requests showed:** for players, *Waiting for the club*, *answers by*, *club confirms* and
  It's a game!'s *answers by · Nobody pays until it confirms*. For the club, *Waiting for you* (its
  filter, its count and its 30-second badge), Accept, Refuse and its dialog, the countdown,
  *Accepted · waiting for one player's payment*, and the Overview's list of what waits for an answer.

**What changes.**

- **The book-by is always the release time**: the game's start minus the club's release lead, 1–13
  days, 3 by default.
- **A full game books the moment its last yes lands, at every club.** A booking is born *booked*,
  its court picked as today.
- **A consequence, kept as decided (call 1):** no game can fill later than a day before its start,
  and by default three days. A game less than a day away can no longer be made from a fresh card.
  Rescues of a booked game's open seat are unaffected, because a rescue lives until the start. And with the
  default cut-off of 24 hours, a card can no longer be dealt past its cut-off (*No free
  cancellation*). Only a club whose cut-off is longer than its release lead still deals one.
- **Setup is four steps**: connect payments, add courts, set hours and prices, and check the
  settings. A club is **live** when the four are done.
- **Rakieta settings** are the release lead, the cut-off, other clubs' courts for the club's groups,
  and the pause.
- **The Overview, once live,** says the club is live on Rakieta and links to today's Bookings (call
  13). The statistics stay out of scope.
- **The payment wait is the fill's alone.** A player whose card is refused when their game fills
  still has their **time to fix the card** before the cut-off, or **time to pay** after it, and the
  game is *Waiting for one payment* meanwhile. The booking-level wait at a club's yes goes with the
  club's yes. Leaving during a payment wait keeps working, under a name that says so.
- **A share is held** at the fill, at its holding time, or at a rescue: never at a club's yes.
  ADR-0190's port is unchanged.
- **A block takes back the blocker's yeses on proposals still filling**, and never touches a
  booking. ADR-0193 §4's *as if she left a booking waiting for the club* has no case left.

**What stays.**

- **The *double booking* cancel reason** (call 14). A club can still sell a handed-over hour at its
  own desk by mistake, and should be able to say so honestly.
- The release lead, its range and its default; the cut-off; Q113's money; rescues; the official
  group's other clubs' courts.
  *(Amended 2026-11-06 by [ADR-0202](0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md) §7: the official group's other
  clubs' courts are read hour by hour, and the switch is on by default.)*

**Every seeded club works Only Rakieta** (call 16). Each keeps a release lead that leaves its seeded
games fillable, and at least one has indoor and outdoor courts of one sport at the same hours.

**A clean cut** (call 15). The removed events, fields and values leave the code without decoders.
The local event store is reset and re-seeded, because only `local` has ever run. A new migration, at
the next free number:

- drops the bookings' answer-by column and its index;
- drops the proposals' *waiting for the club* column;
- narrows the proposals' ended check to drop *turned down*.

The booking state, the partial court-hour index, the nullable game and booked-at columns, the
notices' *until* column and the *club cancelled* flag stay, because other features use them.

### 2. A club's cancel is absorbed by a free court of the same club when nothing changes

When a club cancels a booked game, Rakieta **first looks at the same club** for another court that is
free and has all of these:

- the same **sport**, **day** and **hour**;
- the same **price** (call 2: price is per club per sport today, so this always holds at the same
  club and hour; the rule keeps it so that it still holds when the club software prices per court);
- **the same kind of court, or indoor for an outdoor game**, because an upgrade leaves nobody worse
  off;
- for a ***weather*** cancel, **indoor only** (call 4), because an outdoor court at the same hour is
  rained on too.

**Which court is picked:** the same kind first, then indoor; within each, the club's own court order
(call 5).

**If one is free, the game moves there**: a **move by cancel**.

- The booking moves to that court. The game is **never called off**, and nobody is owed a card.
- **Every hold, or every share already taken, stays exactly as it was.** Nothing is refunded, let
  go or released: the club is still the seller, and the price hasn't changed. After the cut-off, the
  taken shares stay taken and nobody is refunded.
- The existing court-moved event records it, extended with the cancel's **reason** and the new
  court's **kind**.
- **Nobody swipes anything.** The players are told (below).

**For the desk.** The cancel dialog takes the reason and shows a **preview** of what this cancel
would do: *This game moves to Court 3 · indoor · the players are told, nobody is refunded*, or *This
game is called off: …* with the money as today. When it would move, the dialog also offers ***Cancel
the game anyway*** (call 6), for a club closing the whole hour: an event, a power cut. **The cancel
decides afresh when the club confirms.** A court taken in between moves the game to the next
absorbing court, or calls it off, and the answer says which.

**For the players**, a new always-on notice, ***Game moved***, to every player on the booking. It
opens the booked game and isn't emailed (call 8):

> **Bonarka Arena moved your game to Court 3 · Thu 19:00**
> Court 2 can't be played · Padel · indoor · nothing else changes

The reason's words follow the cancel's reason: *weather*, *repair*, *double booking* or *other*.

**Otherwise the game is called off exactly as today**: with *Cancel the game anyway*, or when no
court absorbs it (an indoor game with only an outdoor court free, or no court at all). Before the cut-off every
hold is let go; after it everyone still in is refunded in full and the club bears the fees. It goes on
nobody's record, and the players still in are **owed a card** (§3).

**The club's own *Move* keeps the kind and tells the players** (call 7):

- it offers only free courts of the **same kind**, or an **indoor court for an outdoor game**, each
  listed with its kind;
- it tells the players with the same *Game moved* title, with the body *Padel · indoor · nothing else
  changes*. Today it tells nobody.

**A move never changes the club, the day, the hour or the price, and never puts an indoor game
outdoors.** Any of those is a new card the players swipe again.

### 3. The owed card is the closest game to the one a club's cancel took, and comes first

An **owed card** is the new card dealt first to the players still in a game that a club's cancel
called off. With On request gone, a club's cancel is its one source. A leaver the cancel refunds was
never promised one, and still isn't.

**The new card is chosen closest to the cancelled game first:**

1. **The same club, day and hour**, on a court of the other kind or at a new price;
2. **for a player group only, another club at the same day and hour**, nearest first;
3. **the closest hour in time**, the home club first.

- **An official group stays at its home club**, unless its courts have no hour its players share in
  the next 14 days and the club offers other clubs' courts. That rule is unchanged.
  *(Amended 2026-11-06 by [ADR-0202](0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md) §7: the rule is hour by
  hour, and the switch is on by default, so step 2 reaches an official group whenever its club has
  no free court at that hour.)*
- **The *never at this club and hour* rule goes entirely** (call 10). A refusal was its only other
  source.
- **It is a card like any other.** Its players must all be free for its whole hour and fit each
  other, and they swipe it. A game that stays owed because no hour is found stays owed until its old
  hour passes, as today.

**It is first in the deck for each player it is owed to** (call 11). Whenever that player's group deck
opens, the owed card is first, until they answer it or it is gone. Two owed cards are shown soonest
first, and the deck's usual order follows. Other members' decks are unaffected.

- **The new card records the players it is owed to** (call 12), and the deck orders by that, never by
  a link back to the old game. The phone keeps lifting a card a notice opened on top, as today.
- **It carries no mark** (call 11), for anybody, including a player with push off.

**What the players are told.**

- **The cancel notice** gains the line the email already has: ***We'll look for another game for you
  first*** (call 9). A leaver's cancel notice promises nothing and is unchanged.
- ***Your new game*** is unchanged: it opens the deck on the card, and goes only to a player whose deck
  shows it. For a card at the same club and hour, its body names the kind: *The same players ·
  outdoor · 40 zł a share — say yes to book it*.

### 4. Players see the kind of court

The **kind of court** is indoor or outdoor. A club already records it on each court; players now see
it (call 3).

- **A booked game always shows its court's kind**: on Home's booked row, on the booked details beside
  the court number (*Court 3 · indoor*), and in *Game moved*.
- **A card shows *Indoor* or *Outdoor* when every free court it could be booked on is of that kind**,
  and nothing when the kind is mixed. A card promises a court at a club and an hour, and the court is
  picked at booking. The kind is read when the card is read, from the free courts of its sport at its
  club and hour, on the deck card and on the game's details.
- **It is not a preference or a filter.** Players see the kind; they don't choose by it.

### 5. What the wire carries (a public behaviour change)

**The player document.**

- **Goes:** *waiting for the club* on the yes answer; *club confirms* on the deck card, Home, the
  booked details and the proposal details; *answer by* on Home, the booked details and the proposal
  details; the *waiting for the club* and *turned down* statuses; the *refused* and *no answer*
  reasons; the three request notice kinds. The score's own *answer by* is untouched.
- **Comes:** an optional *indoor* on the deck card, the proposal details, Home's booked rows and the
  booked details; the *game moved* notice kind, opening the booked game.

**The club document.**

- **Goes:** the waiting, acceptance and refusal paths and their six schemas; *way of working*,
  *minimum notice* and *time to confirm* on the settings; the *waiting for you* and *waiting for a
  payment* statuses, the *waiting for you* filter and count, and the *answer by* on a booking row; the
  *refused* and *no answer* reasons.
- **Comes:** the cancel preview; the cancel's *anyway* flag, and its answer saying *moved*, with the
  court and its kind, or *called off*; the court's kind on the free courts and on a booking row.

**The dev document.** The request presses and situations go, and the move and cancel presses gain the
new outcomes (§6).

Every client regenerates with `make gen-api`, and the freshness and drift checks diff every one.

### 6. The test console and the seed

The games test console (ADR-0194) follows:

- **Goes:** the *needs her yes at an On request club* situation; the Accept and Refuse presses; the
  request-timeout job's *Run it now*; the board's *club answer due* column; the club pane's *confirms
  each game*, the game pane's *waiting for the club* and the booking pane's *answer by*.
- **The hours finder** loses its *on request* filter. The situations that used it find Only Rakieta
  hours instead.
- **Comes**, acting as a club: a cancel with a reason, which moves the game when a court absorbs it;
  *Cancel the game anyway*; and a move to a chosen court.
- Its rules stand: it acts only as seed accounts, every press runs the club's own use case, and it
  writes history, never time. Its guard test still fails a registered job with no press.

The seed changes every club to Only Rakieta: Kazimierz Padel and Prądnik Tennis (On request), and
Ogrody 33, Bonarka Arena, Nowa Huta Squash and the other Instant clubs. Marta's game at Kazimierz
Padel is booked when it fills. The seed's own assertions that all three ways are seeded go. Seeding
stays fixture-only, through the real use cases (ADR-0029).

### 7. The calls made without a ruling

PRD #667 made sixteen calls the product owner hasn't ruled on. Each is a rule until overruled, and
each is marked *a call* where it stands: in the mechanics, or, for the store and the seed (15 and
16), in the screens' Part C and Part D:

1. **The release lead keeps its range of 1–13 days**, so no game fills later than a day before its
   start (§1). The alternative is a release lead in hours, down to 2 hours.
2. **The same price** is part of the move's rule, though price is per club per sport today (§2).
3. **Players see the kind of court**: a booked game always, a card only when every free court it
   could be booked on is of one kind (§4).
4. **A weather cancel moves only to an indoor court** (§2).
5. **Of two absorbing courts, the same kind comes first, then indoor**, and within that the club's
   court order (§2).
6. **The cancel dialog previews the move and offers *Cancel the game anyway***, and the cancel decides
   afresh at the confirm (§2).
7. **The club's own *Move* follows the same kind rule and now tells the players** (§2).
8. ***Game moved* is always on, opens the booked game, and isn't emailed** (§2).
9. **The cancel notice gains *We'll look for another game for you first*** (§3).
10. **The *never at this club and hour* rule goes entirely**, not only for a cancel (§3).
11. **The owed card is first for each player it is owed to**, soonest first, ahead of the deck's
    usual order, and carries no mark for anyone, a player with push off included (§3).
12. **The new card records the players it is owed to**, and the deck orders by that (§3).
13. **The Overview, once live,** says the club is live and links to today's Bookings (§1).
14. ***Double booking* stays** as a cancel reason (§1).
15. **A clean cut**, with the local store reset and a migration that drops only what requests alone
    used (§1).
16. **Every seeded club works Only Rakieta**, with a release lead that keeps its seeded games
    fillable, and at least one club has indoor and outdoor courts of one sport at the same hours
    (§6).

### 8. What stands

- **ADR-0189:** a yes is free and silent; the last yes books the game and holds every share
  together, all or nothing, after a ten-second undo; the club is the seller; a card promises a court
  at a club at an hour, and the number is given at booking; every game is one hour; Fill in offers
  only rescues; *Move* and *Cancel* until the start.
- **ADR-0189's 2026-10-09 amendment**, at the fill: the bell's number; *It's a game!* when the four
  are matched, and *Waiting for one payment* while one card is refused; every ending and fall-back
  of a full game told to everyone still in it; a leaver told only what touches them; the new card
  announced (*Your new game*); time to pay.
- **ADR-0189's 2026-10-10 amendment and ADR-0190's:** the share held at the fill and taken at the
  club's cut-off, leaving before it free, the card check and holding time, time to fix the card, the
  exact late refund, a club's cancel before the cut-off letting every hold go and after it refunding
  in full.
- **ADR-0193:** a block keeps two people off one court, through the pair rule, and unblocking brings
  no yes back.
- **ADR-0194:** every rule of the console.

## Consequences

**Easier**

- **A full game is booked the moment it fills, at every club.** *It's a game!* always means the court
  is theirs. Nothing ends a full game but a club's cancel or the cut-off, and a newcomer has no
  *waiting for the club* to learn.
- **The desk does nothing per booking.** No countdown, no Accept, no Refuse, no email to answer, and
  four setup steps instead of five.
- **A broken court costs nobody anything** when another court of the same club qualifies: no refund,
  no let-go hold, no card fee and no swipe, and the players know which court to walk to. A desk that
  sold a handed-over hour by mistake is absorbed the same way.
- **The owed card is the closest game to the lost one, and is reachable**: first in the deck, one tap
  from its notice.
- **Less to build and keep:** one job, seven events, three notice kinds, two club settings, a setup
  step, a club page's filter and its badge, and a migration's worth of columns go.

**Harder**

- **No game fills later than a day before its start**, three by default. A game less than a day
  away can be made only by rescuing a booked game's seat. If last-minute games matter more, the
  release lead in hours is the change to make.
- **Clubs that keep selling the same hours at their own desk can't join until the club software
  ships.** A club must hand over a block of hours and keep them out of its own system: two
  calendars still, but set once and in one direction. Fewer clubs may go live at first.
- **The product is now committed to becoming the club's booking software**: the desk calendar, direct
  bookings, season bookings, blocks, customers, coaches, and importing from tenis4U, Playmore and
  kluby.org. It is a large build, with its own grilling.
- **A weather cancel at a club with no indoor court always calls the game off.** Only an indoor court
  is safe from the rain.
- **The preview can be wrong by the time the club confirms.** The cancel decides afresh, and its
  answer says what happened.
- **A card's kind is shown only when it is certain.** At a club with both kinds, a card shows nothing,
  and the court picked at booking may be outdoor for a player who hoped for indoor.
- **The owed card overrides the deck's order.** A card with a sooner deadline, or with more people
  In, sits behind it for its players until they answer it.
- **For a player group, the owed card may be at another club** at the same hour, up to 10 km away,
  before a card on another day at the home club.
- **The local event store is reset** once more, and every seeded game is made again.

**Neutral**

- **The money rules are unchanged.** Q113 holds, the payment wait at the fill stays, and a club's
  cancel that calls a game off costs what it cost.
- **The release lead's range, unit and default are unchanged.**
- **The kind of court was always recorded**; it is only shown now.
- **A move by cancel is recorded by the existing court-moved event**, extended, not by a new one.
