# Games and Fill in — the mechanics

> **Status:** agreed in a grilling session on 2026-09-28 and 2026-09-29 (Q1–Q67), and locked
> against the product owner's mocks in a second part (Q68–Q96), all logged in
> [Appendix C](#appendix-c--decision-log). Recorded by
> [ADR-0189](../../adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md). The club
> website's items marked **◇** were filled in while writing and then confirmed as a whole
> (Q86, Q95).
>
> **Its companion** is [the-screens.md](the-screens.md): the locked player-app designs (with the mocks under
> [`mocks/`](mocks/)), the club website's pages and flows, and the backend and seed data
> inferred from both. This document says what happens; that one says how it looks and what
> has to be built.
>
> **What it is:** the base document for building the **Games** tab and the **Fill in** tab
> of a group page. It says what happens, not how the screens look — the UI designs are in
> its companion. It is written so it can be read without knowing the code; the
> appendices hold what developers need on top.
>
> **What it replaces:** the two PDFs *"Rakieta — the deck: every card, and what a yes
> does"* (17 Sep 2026) and *"Rakieta — Games and Fill in inside a group"* (22 Sep 2026).
> Their holds on every swipe, their two clocks, their "matched game without a court" and
> their eight card types are gone.

---

## 1. The whole thing in one page

1. **The app builds games.** For every free court in the next 14 days at the group's
   clubs, the engine finds the members who are free for that hour, want that kind of game
   and fit each other, and deals the best four (or two) as a card to each of them.
2. **A swipe right is a free, silent yes.** "I'm in — if everybody is, book it and take my
   share at the club's cut-off." No money moves, no court is held, nobody is notified.
3. **Yeses are visible on the card.** Other players see your tile marked **In**, and cards
   with more people In rise to the top of their decks. The card that needs only you says
   **You complete it**.
4. **The last yes books the game.** Every player's share is **held** on their saved card at
   that moment, all together or not at all, the court is booked with the club, and everyone sees
   **It's a game!**. Nobody has to confirm anything. The shares are **taken at the club's
   cut-off**, the one deadline, the same for everyone in the game (Q113).
5. **Leaving before the club's cut-off is free.** Leave before it and nothing is taken: the hold
   on your card is let go, and your seat becomes a **rescue** that others can take. Leave after it
   and, only if someone takes your seat, you get your share back less exactly what was kept on
   your payment.
6. **A game is full at the cut-off, or it is off.** If a seat is still empty at the club's
   cut-off, the game is called off and every hold is let go: nobody pays anything. Nobody ever
   pays more for an empty seat; a seat left after the cut-off may stay empty, and the game goes
   ahead short ([§14.1](#141-home-and-the-statuses)).
7. **Fill in is the rescue board.** It holds the seats of booked games that lost a player,
   and a list of your own yeses that have not become games yet.
8. **Members can post a game.** They pick the hour and the court; the app deals it to their
   best fits as a **Challenge**.
9. **The club is the seller.** On the club website it lists its courts, hours and prices, and
   hands Raketa a block of hours to sell alone: **Only Raketa**, the one way until Raketa is the
   club's booking software (Q121). It moves and cancels booked games, and a cancel moves the game
   to another of its courts when nothing about it changes (Q122). It gets paid through Raketa
   after the game and pays the card fee as it would at its own terminal. Raketa earns nothing
   for now ([§16](#16-the-club-website)).
10. **After the game, only an exception asks anything** (Q114–Q119). A full game nobody recorded
    was played. A player who isn't there is caught at the court, in the first half of the game, by
    the people waiting for them. One *That's right*, or a day of silence, settles a score, and
    silence costs nothing. **Player reliability** is points from 100, and a player may choose to
    play only with players of at least High or Medium reliability ([§15](#15-on-the-day-and-after)).

---

## 2. Words used in this document

| Word | Meaning here |
| --- | --- |
| **Group** | A crowd of players at a home club (a player group) or a club's own community (an official group). This document is written for "a pool of players plus the courts around them"; a group is the first pool, a whole city (Explore) will be a later one. |
| **Court hour** | One court at one club for one hour. Every game lasts exactly **1 hour**, for every sport. |
| **Kind of court** | **Indoor** or **outdoor**, as the club records each court. A booked game always shows its court's kind; a card shows it only when every free court it could be booked on is of one kind ([§5.2](#52-what-a-card-promises), Q122). Not to be confused with a game's **kind**, below. |
| **Game** | Two or four players plus one court hour plus a kind. |
| **Kind** | **Competitive** (a counted game: a confirmed score moves levels) or **For fun** (a friendly: levels stay put). |
| **Share** | The court's price divided by the seats (4 for padel and badminton, 2 for tennis and squash). Fixed on the card. |
| **Card** | A game as one person sees it in their deck. |
| **Version** | One of up to three views of the same game, each shown to different people. All versions share their yeses ([§7](#7-one-game-several-versions)). |
| **Yes / No** | Swipe right / swipe left on a card. |
| **In** | A player who said yes to a game that has not filled yet. |
| **Momentum** | How many players are In on a game. |
| **Fills** | The moment the last seat says yes. The game is then **Booked**, at every club, and every share **held** on its player's card ([§11](#11-the-moment-a-game-fills), Q121). |
| **Book-by** | The latest moment a card can still fill: the club's release time, the release lead before the game ([§5.4](#54-the-only-deadline-the-courts-book-by), Q121). |
| **Only Raketa** | How every club works with Raketa: it hands Raketa a block of hours, which Raketa sells alone until the release lead before each game. The one way until Raketa is the club's booking software; *Instant* and *On request* were removed (Q121, [§16.3](#163-one-way-to-work-with-raketa)). |
| **Cut-off** | The club's free-cancellation deadline, for example 24 hours before the game. A club setting, and the one deadline in a game, the same for everyone: leaving before it is free, and at it a full game's shares are taken and a short game is called off ([§12.3](#123-leaving-before-and-after-the-cut-off)). |
| **Held · Taken** | A share is **held** when its amount is reserved on the player's card and nothing has moved; the hold is **let go** on a leave, a call-off or a club's cancel before the cut-off, and costs nobody anything. It is **taken** at the cut-off, or at once after it ([§12.2](#122-when-a-game-fills), Q113). A card hold is never called *a Hold*, which is the account gate in the glossary. |
| **Card check** | A share held for a few seconds and let go at the fill, when that seat's hold would not last until the cut-off. It proves the money is there that day ([§12.2](#122-when-a-game-fills)). |
| **Holding time** | When a seat's share is held to stay until the cut-off: at the fill when its hold reaches the cut-off, otherwise **four days before the cut-off** ([§12.2](#122-when-a-game-fills)). |
| **Time to fix the card** | The 30 minutes a player whose card was refused **before the cut-off** — at the fill, at the holding time, or taking a rescue — has to fix it, with their seat kept for them; nothing is paid. Never past the cut-off or the book-by ([§12.2](#122-when-a-game-fills)). |
| **Time to pay** | The 30 minutes a player whose payment failed **after the cut-off**, where money is taken at once — when the game filled, or taking a rescue — has to pay, with their seat held for them, never past the book-by (a rescue: never past the start) ([§12.2](#122-when-a-game-fills)). |
| **Rescue** | An open seat in a booked game that lost a player. |
| **Move by cancel** | A club's cancel that another free court of the same club absorbs: the same sport, day, hour and price, and the same kind of court or indoor for an outdoor game (indoor only for *weather*). The game moves and is never called off, and nobody's money changes ([§16.9](#169-cancelling-a-booking), Q122). |
| **Owed card** | The new card dealt first to the players still in a game that a club's cancel called off: the closest game to the lost one, first in their deck ([§8.2](#82-the-order), Q123). |
| **Post** | A game a member creates by picking the hour and the court. Its players see it as a **Challenge**. |
| **Home** | The first tab of the bottom bar: your games. |
| **Isn't here yet · Arrival** | The tap a player at the club makes, in the first half of the game, about another player on the court; and the moment that player is shown to be at the club, by their own *I'm here* or a courtmate's *They're here*. The arrival makes it **on time**, **Came late** or **Didn't come** ([§15.1](#151-attendance-at-the-court), Q115). |
| **Played · no score** | The end of a full booked game nobody recorded and nobody *Didn't come* to: played, for everyone, with no Level moved ([§15.3](#153-a-game-nobody-recorded-and-a-game-somebody-didnt-come-to), Q114). |
| **Player reliability** | A player's figure in **points**, from 100: a fixed price off for each failure, 5 back for each game played through, each failure dropping out after 6 months. Read with a band, *Very high · High · Medium · Low* ([§15.4](#154-the-record), Q117). |

---

## 3. Where everything lives

**The bottom bar** is **Home · ⚡ Play · You**.

- **Home** holds your games from the moment they fill until shortly after they are over. Its
  badge counts **games that need you**: a result to enter or confirm,
  a payment to confirm, a seat open in your game.
- **Play** opens on **Groups | Explore**. A group opens its page, with its sport switcher in
  the header.
- **You** holds your profile, your weekly hours, your payment method, your receipts
  (You › Payments) and your settings.
- **Players** and **Chats** are not in the bar. They were the older loop — the Players deck,
  the Chats tab, challenges with the where/day/hour plan, and Find a game — which was hidden
  behind a *Classic play* flag and then **removed on 2026-10-06**
  ([#569](https://github.com/Raketa02/Raketa/issues/569)). A group's Games deck is the one way
  a game is made.

**A group page** has four tabs: **Games · Fill in · Friends · Info**.

- **Games** is the deck, split by the **Competitive · N / For fun · N** switch (N = cards of
  that kind in this group and sport). You see only the segments that match your intent for that
  sport (both if you chose *Either*). Its badge counts the cards where somebody is already In
  with you. The same switch also stays on the **Friends** tab, which is out of scope.
- **Fill in** has two sections: **Seats to fill** (rescues you can take; its count is the tab's
  badge) and **You're In** (your yeses in this group that have not filled yet, including the
  games you posted). The **Post a game** button floats over it.
- **Friends** is out of scope. **Info** is unchanged.

**Chat** has no tab. Every chat belongs to one game and is opened from that game's details or
from the speech bubble on its Home card ([§14.3](#143-the-chat)).

---

## 4. Who and what a group draws on

### 4.1 Players

- Every member **rated in the sport** takes part. Being picked for games is always on; it
  cannot be switched off, because proposing games is what Raketa is for.
- **Intent.** The first time a member opens Games for a sport without an intent, the app asks
  once, inline: *Competitive / For fun / Either*. Nothing else is blocked. The answer is the
  existing per-sport Play intent, changeable later.
- **Blocks.** Two players, either of whom blocked the other, are never on the same card, in any
  group. Blocking somebody takes back your yeses where they are In, until the game is booked; your
  booked games stay ([ADR-0193](../../adr/0193-a-block-keeps-two-people-off-one-court-and-the-blocker-can-see-it.md)).
- **Gender preference** and the **level window** apply to every pair on a card, with the blocks
  above: together they are the pair rule of [§5.1](#51-what-it-does).

### 4.2 Weekly hours (availability)

- Availability becomes **hours, per day of the week**, 07:00–23:00: a grid of 7 days × 16
  one-hour cells (Q81). Tap an hour to toggle it; press and drag to paint or clear a run. No
  templates. At least one hour is required, as today.
- It is asked **during onboarding** and editable any time from **You**. It is a general
  pattern that applies to every week. There is no "not this week" switch.
- You count as free for a card only if your hours cover **the whole game**, not just its
  start.
- This replaces the 7 days × morning/afternoon/evening grid. Nothing is in production, so
  nobody has to be migrated; only the seed data changes.

### 4.3 Courts

- **Player group:** its home club first, then other Raketa clubs within **10 km** of the home
  club. At the same hour, the home club's court is preferred.
- **Official group:** only its own club's courts, unless the club switches on **"Offer our
  groups other clubs' courts when ours are full"** (off by default, with a distance the club
  sets, default 10 km). When it is on, another club's court is used for a set of players only
  when the club has **no court at any hour those players share in the next 14 days**. The
  club's own courts always win.
- The engine looks **14 days ahead**. Start times are the club's own.

### 4.4 Several groups

Each group has its own deck. A player can be In on games in several groups; when one of
their games fills, their yeses at that same hour in every other group are withdrawn.

---

## 5. How the engine builds games

### 5.1 What it does

Continuously, and whenever something changes (a court frees up, a member joins, someone
changes their hours), the engine looks at every free court hour in the group's reach for the
next 14 days and asks: *which members are rated in this sport, want this kind of game, are
free for this whole hour, and fit each other?* From those it builds the best game — the most
even four (or two) — and deals it as a **Picked for you** card to each of its players.

> **Corrected 2026-10-06** ([#569](https://github.com/Raketa02/Raketa/issues/569)). This
> section said the new games use *today's matchmaking engine unchanged* — level fit, predicted
> balance, intent, reliability, availability, playing style and social vibe, with separate
> Competitive and For fun weights. They never called that ranking, and it has been removed
> ([#580](https://github.com/Raketa02/Raketa/issues/580)). What they call is below.

The new games keep three pieces of the matchmaking engine, and nothing else of it:

- **The pair rule** (`PlayerFit`), asked of every pair a card, a fill, a rescue or a post would
  put on one court: **no block** either way, a **mutual gender preference**, Levels inside
  the kind's **level window**, whose tolerance per kind is the live ruleset's, and — since Q118 —
  the **reliability filter** either of them switched on: a pair is unfit when either player's
  minimum band is above the other's band, a *New* player passing every minimum. Unlike a block, the
  filter takes no yes back: a yes given before it was switched on, or before somebody dropped below
  it, stands, and the fill doesn't re-ask it for that yes ([§15.4](#154-the-record)).
  While either player is inside their **14-day newcomer window**, the pair is held to the
  Competitive window whatever the kind. A post's Level range starts from the same window.
- **The balance forecast** — the engine's own `forecast`, which the proposer reads directly and
  everything else through `forecast_the_sides`. It picks the most even four the proposer deals
  at an hour — a tie goes to the closest Levels — chooses the sides, ranks the next best fits for
  a seat a *No* left and for a rescue, and is the percentage a card and a booked game's details
  print.
- **Group availability**, which only grades a card's overlap grid (§8.1).

Who is free is each player's **weekly hours**, read for the whole hour; which kinds they are
dealt is their **Play intent**. **Distance stands down inside a group**: it decides only which
clubs a player group plays at (§4.3), and it will matter again at city scale. There is no
score and no weight, and one toggle: a player's own **reliability filter**, which is a clause of
the pair rule and ranks nothing. What is new is the assembly (people × hour × court).

> **Amended 2026-10-11** (Q118, [ADR-0195](../../adr/0195-reliability-is-points-a-no-show-is-caught-at-the-court-and-a-right-score-needs-no-tap.md)
> §6). This said *there is no score, no weight and no toggle*, and the correction of 2026-10-06
> above had made reliability play no part in which game the deck builds (rule R-ENGINE-15). It
> now plays one: an optional filter, off by default, that keeps a player off any court shared
> with somebody below the band they chose.

### 5.2 What a card promises

A card promises **a court at a club at an hour** — "Bonarka Arena, Sat 17:00" — not a court
number. The number is given when the game is booked. If Bonarka has four courts free at
17:00, four different cards can fill without colliding.

- Only when the **last** court at that club and hour goes do the other cards on it lose their
  court. A card then moves to another court number at the same club and hour if there is
  one, and nobody's yes changes. Otherwise the card disappears, and the players who were In
  are dealt a new card first ("You three were In — Sat 18:00?").
- The **price is fixed on the card**. A club changing its prices affects only new cards.
- **The kind of court** is on the card only when it is certain: *Indoor* or *Outdoor* when every
  free court of the sport at that club and hour is of that kind, and nothing when they are mixed.
  The court is picked at booking, and a booked game always shows its kind (Q122, *a call*).

### 5.3 Keeping the deck clean

- The same people never appear twice in one batch at different hours; only their best hour
  shows.
- A card you swiped left never comes back.
- The same court hour can appear on cards with different people. That is expected.
- You are never dealt a card at an hour where you already have a game.

### 5.4 The only deadline: the court's book-by

A card lives until its court's **book-by** time. Nobody chooses it; it comes from the club: it is
**the club's release time**, *N* days before the game (the release lead, a club setting from 1 to
13, default 3), after which unsold courts go back to the club.

> **Amended 2026-10-12** (Q121, [ADR-0196](../../adr/0196-only-raketa-until-raketa-is-the-clubs-booking-software-and-a-clubs-cancel-moves-the-game.md)
> §1). This was a table of two rows: the release time at an *Only Raketa* club, and the game's
> start minus the club's minimum notice (default 2 h) at an *Instant* or *On request* club. Both of
> those ways were removed, so every card's book-by is the release time. **No card can fill later
> than a day before its game, and by default three** *(a call: the release lead keeps its range of
> 1–13 days; the alternative is a release lead in hours, down to 2 hours)*. A game less than a day
> away is made only by a rescue ([§10.1](#101-seats-to-fill--the-rescue-board)), which lives until
> the start.

There are **no answer windows, no restarts and no ceilings**. A card shows a countdown only
when its book-by is less than 24 hours away. At book-by an unfilled card simply disappears:
nothing was charged, the yeses expire, and nobody is told. A game that **had filled** and went
back to filling is the exception: it is on its players' Home as *Seat open*, and its end is told
to everyone still In ([§14.1](#141-home-and-the-statuses), Q104, Q106).

A card whose club **cut-off has already passed** (a last-minute game) says **No free
cancellation** on it before anyone swipes: its shares are taken the moment it fills
([§12.3](#123-leaving-before-and-after-the-cut-off)). Since Q121 that happens only at a club whose
cut-off is longer than its release lead: with the default 24-hour cut-off, the book-by never comes
after it.

---

## 6. The swipe

### 6.1 A yes

- A yes means: **"I'm in. If everybody on this game says yes, book it and take my share at the
  club's cut-off."** Until the cut-off the share is only held, and leaving is free (Q113).
- It is **silent**: no push, no challenge sent, nothing in Home.
- **No money moves and no court is held.** The court stays available to every other card
  until some card fills.
- It is shown **on the card itself**: every other player who meets the card sees your tile
  marked **In**.
- A yes is to **this game**: this court, this hour, the people who are In, and anyone the app
  judges fit for the empty seats. A replacement must fit **everybody already In** (every pair
  of them, by the pair rule of §5.1).
- Before your **first** yes, the app asks you once to save a payment method and accept the
  terms ([§12.5](#125-saving-a-payment-method-and-the-terms)). Your yes lands as soon as that is done.

### 6.2 A no

- A no is also **silent**. You leave that card; nothing is recorded against you.
- Your seat is dealt, as a card, to the **next best fits** — up to 3 per open seat. The first
  of them to say yes takes it.

### 6.3 A player who has not swiped yet

"Answered" means swiped, either way. A named player who has not swiped the card at all keeps
their seat **until somebody else takes it**. The engine widens the game — no timer involved —
at one moment: **when the game reaches half its seats In** (2 of 4, or 1 of 2). At that moment
every named seat still without a swipe is also offered to the next best fits, as new versions
of the same game ([§7](#7-one-game-several-versions)). The named player keeps two advantages:
the card sits at the top of their deck, and they get the *You complete it* alert.

### 6.4 How another player finds out

Scenario: A and B are both on a card; A swipes yes. B finds out from the card, never from a
message:

- B is looking at that card → A's tile flips to **In** on screen.
- B has not reached it yet → next time B opens Games, the card has moved up and A's tile reads
  **In**; the Games badge went up by one.
- A's yes leaves B as the only seat missing → B gets the *You complete it* alert (if on).
- B already swiped left → B is off the card; nothing reaches B.

### 6.5 Undo

**Every action that moves money** — the yes that fills a game, and **every** rescue join, not
only the last seat (Q74); since Q113 they hold the share, or take it after the cut-off — shows a toast *"Booking in 10 s · Undo"* with a draining ring;
nothing is held or taken until the ten seconds are up. Any other yes is only a vote, and you can withdraw
it free from **Fill in › You're In** until its game fills.

**The control that moves money says Pay** (Q124). On the deck the stamp under your thumb reads
***PAY · 40 zł*** ([§8.1](#81-the-three-card-types)). Every button that moves money reads
***Pay 40 zł***: the Fill in seat row ([§10.1](#101-seats-to-fill--the-rescue-board)), a rescue's
details and the details of a *Book it now* game ([§14.2](#142-the-game-details)), and Post a game's
sheet, on a rescue or on a post's last seat ([§9.1](#91-the-steps)). The figure is always the share.
**Two controls keep their words:** the deck's ball button is ***I'm in*** whatever the card, and
the pill reads ***Booking in 10 s***. A vote's stamp carries the price too, as *I'M IN · 40 zł*, so the
word, not the price, tells a vote from a payment. The words are English until the app is translated.

### 6.6 Limits

- **Live yeses:** **no cap** (Q97). A yes can only book within your games per week and one
  game per hour, so how many games you are In on at once is not limited.
- **Games per week:** a free setting, **1–7, default 2**, counted Monday to Sunday. When you
  have that many booked games in a week, your other yeses for that week pause; they come back
  if one of those games is called off. **Cards for a capped week are not dealt at all** (Q73) —
  a slim line at the top of the deck says *"Your 2 games this week are booked — showing next
  week"* — and posting into that week is refused with the same reason. You never get more
  games than you asked for.
- **One game per hour:** when one of your games fills, every other yes of yours at that hour
  is withdrawn.
- **Most I'll pay per game:** optional; cards above it are never shown to you.

---

## 7. One game, several versions

A game can be shown to more people than it has seats. Each person sees **their own version**:
the people already In, themselves, and the rest of that version's named players. **All
versions share their yeses**: a yes on any version counts toward the one game, and the game
fills the moment enough people who said yes all fit each other.

**Why one game and not several:** if each version were its own game, yeses could split.
Example — Marek posts Saturday 17:00. Version 1 is Marek + B, C, D; version 2 is Marek + E, F, G.
B and C say yes on version 1, E says yes on version 2, and D, F, G never swipe. As separate
games nothing books; as one game, Marek + B + C + E is four, and it books the moment E says yes.

**Rules:**

- Versions are created **when a picked game reaches half its seats In** ([§6.3](#63-a-player-who-has-not-swiped-yet))
  and **when a member posts a game** ([§9](#9-posting-a-game)).
- **At most 3 versions per game. Each person gets one version** — nobody sees the same game
  twice with different partners.
- Each version shows its own people with **In** tags, plus a line such as *"4 people are In on
  this game"*. The balance forecast is computed for that version.
- When the game fills, **every version disappears**. Anybody who swipes a version a moment
  too late is told it just filled.
- The people who end up playing are those whose yeses filled it; the **sides are drawn at
  booking**, for the most even game. (E said yes to a card showing Marek + E, F, G and plays
  with Marek, B and C — that is what a yes means, [§6.1](#61-a-yes).)
- **Versions are not a card type.** A Challenge looks and behaves the same with one version
  or three; the number of versions only changes how many people received it.
- **Singles:** a version is the poster (or the first yes) plus **one** person, so every free
  best fit is a version. Up to 3 at once; the rest wait in reserve and are dealt a version when
  someone swipes left. A picked singles game is half In after its first yes, so at that moment
  up to 2 more versions go out.

---

## 8. The deck

### 8.1 The three card types

| Card | What it is | Its ribbon |
| --- | --- | --- |
| **Picked for you** | A game the engine built | *Picked for you* (dark teal) |
| **Challenge** | A game a member posted, dealt to you as a best fit | *Kuba challenged you*, or *The group challenged you* once the poster withdrew (dark teal) |
| **Seat open** | A rescue: a booked game that lost a player, and you are a top fit | *Seat open · court booked* (coral) |

Every card shows, top to bottom (the full anatomy is in [the-screens.md](the-screens.md)):

- **The tiles** — photo or generated poster, the player's **Name** (a tile may cut it short
  visually, never invent a first name — ADR-0171), level. The **IN** tag on a player who said
  yes is the only tag that signals momentum: a player who hasn't answered simply has no tag (Q69,
  Q91). A game dealt in versions adds its one line ([§7](#7-one-game-several-versions)). On a
  rescue the players read **paid** and the open seat is a dashed **You?** tile with your share.
  A **FRIEND** tag appears only once a friends feature exists (Q68).
- **The sides** — the two rows are the two sides; the *vs* line names them, and the balance bar
  names the same sides with **your side on the left** (Q70). On a rescue you take the leaver's
  seat and side.
- **The balance forecast** — the percentage and the bar, for this version.
- **The overlap grid** — the card's players' week as 7 days × 3 ranges (**Morning 07–12,
  Afternoon 12–17, Evening 17–23**): bright where everyone is free for at least one whole hour
  in the range, dim where all but one are, the game's range ringed in coral; labelled **High /
  Good / Slim overlap** by today's grading (Q71).
- **The court block** — *Day HH:MM · Club* (and the court number once booked, with its kind:
  *Court 6 · indoor*), *Indoor* or *Outdoor* when every free court the card could be booked on is
  of that kind (Q122), the share, and one state tag: **Court available** (your yes is a free
  vote), **Book it now** (your yes fills it) or **Booked** (a rescue). **No free cancellation**
  when the cut-off has passed.
- **The ribbon countdown** — only when the deadline is under 24 h: *21 h 00*, then *45 min*,
  coral under an hour (Q72).
- **The stamps** — while dragging, **NOT THIS TIME** on the left, and on the right one of two,
  each with the share (Q124):
  - **I'M IN · 32 zł** on a vote: a yes that only adds to a game still filling (*Court
    available*). Nothing is held until the game fills.
  - **PAY · 32 zł** on a yes that books at once (*Book it now*) or takes a seat (*Seat open*). It
    holds the share until the cut-off, or takes it at once after the cut-off.

  The share is the card's own, fixed when the card was made ([§5.2](#52-what-a-card-promises)).
  The deck's ball button stays *I'm in* and the pill stays *Booking in 10 s*
  ([§6.5](#65-undo)). Until Q124 a vote's stamp read *I'M IN* with no price, and a yes that booked
  at once read *I'M IN · 32 zł* (Q72); at an *On request* club it carried none, because the hold
  waited for the club.

### 8.2 The order

**An owed card comes first** (Q123). The card dealt to the players still in a game that a club's
cancel called off ([§16.9](#169-cancelling-a-booking)) is first in the deck of each player it is
owed to, whenever the deck opens, until they answer it or it is gone. Two owed cards are shown
soonest first. It carries **no mark**, for anybody, a player with push off included, and other
members' decks are unaffected *(a call)*. The card records the players it is owed to, and the deck
orders by that *(a call)*. A card a notice opened is still lifted on top by the phone, as before.

After the owed cards, within one group, one sport and one segment, cards are ordered by **how
likely you are to swipe right**:

1. **Seats still open after your yes, fewest first** — 0 (*you complete it*), then 1, 2, 3.
   Momentum is counted on the **game**, across all its versions.
2. **Same count:** Seat open, then Challenge, then Picked for you. (A rescue is a real booked
   court losing its game; a challenge is a person's own ask; a pick is the engine's suggestion.)
3. **Then the soonest deadline** (book-by; for a rescue, the cut-off, or the start once the
   cut-off has passed).
4. **Then the best fit for you** — the forecast of your own version, most even first.

Example Padel deck (Competitive):

| # | Card | Open after your yes |
| --- | --- | --- |
| 1 | Seat open · Fri 20:00 · a booked game lost Kuba · 3 In | 0 |
| 2 | Picked for you · Sat 17:00 · 3 In | 0 |
| 3 | Challenge · Marek · Sun 10:00 · 2 In | 1 |
| 4 | Picked for you · Tue 19:00 · 2 In | 1 |
| 5 | Challenge · Ewa · Wed 18:00 · only Ewa In | 2 |
| 6 | Picked for you · Thu 20:00 · 1 In | 2 |
| 7 | Picked for you · Mon 18:00 · nobody In yet | 3 |

For singles there are only two steps: *you complete it*, then fresh.

### 8.3 An empty deck

The Games tab keeps today's cards for a group with nothing to deal — *Just you so far*, *3 of 4*,
*Nothing picked right now*, with Share / Copy link — and **Nothing picked right now** gains
**Post a game** (Q96). The engine keeps working, and a card appears the moment one fits.

---

## 9. Posting a game

### 9.1 The steps

The **Post a game** button in Fill in walks through:

1. **Sport** — the sports you are rated in that the group plays.
2. **Kind** — Competitive or For fun (defaults to your intent). For fun is a friendly.
3. **Who** — *Anyone*, *Men*, *Women*, or *Mixed pairs* (in doubles, each side one man and one
   woman). Someone whose own gender preference excludes the game is never shown it.
4. **Level** — defaults to **the engine's own range for the chosen kind** around your level
   (Q78); two steppers narrow it in 0,05 steps, never widen it.
5. **When** — a two-week heatmap, one week at a time, of **7 days × 3 ranges** (Morning 07–12,
   Afternoon 12–17, Evening 17–23) (Q77). Your weekly hours and your best fits' (matching the
   kind, who and level) are grouped into the ranges: a cell's number is **how many of them are
   free together with you at the best hour in that range that has a free court** (Q92) — never
   people who overlap you at different hours. Its colour says whether a court is free and
   whether a full game's worth are free; a red dot says a game is already happening there.
   - No free court, or **nobody** who fits free: cannot be picked.
   - **Fewer fits than open seats** (3 in doubles, 1 in singles): can be picked, and says *"only
     2 fit · may not fill"*.
   - Outside your own weekly hours: dimmed and dashed, still pickable.
6. **Court** — tapping a cell opens its sheet: your best fits free then, and the **free courts**
   in that range, home club first — each with its hour, club, distance, share, book-by and its
   own *"n free"*. Tapping a court picks it (one hour, one court). **Already happening here**
   lists, first, **rescues** at that time you fit (**Pay 27 zł**, booked at once: held until
   the cut-off, or paid at once after it) and then
   **posts still filling** you fit (**I'm in**, free until it fills; **Pay 27 zł** on a post's
   last seat, because your yes fills it), so you can join instead of duplicating (Q79, Q93,
   Q124).
7. **Post — you're In** — disabled until a court is picked. There is no review card; posting is
   your yes. Guards, each explained under the button: a saved payment method (the setup opens
   if missing), at most 2 live posts, and your games per week (Q80).

### 9.2 What happens next

- Posting **is your yes**. Nothing is held until the game fills, and nothing taken until the
  club's cut-off.
- The engine builds **versions** from your best fits free at that hour: one per full set of
  them, **up to 3** (for doubles: 9 or more fits → 3 versions, 6–8 → 2, 3–5 → 1; fewer than 3 →
  one version with open seats). They see it in their decks as a **Challenge** — *Marek challenged
  you*.
- A **Challenges for you** alert tells them ([§17.2](#172-notifications)).
- Until book-by, the engine keeps dealing it to anyone who **becomes** a fit (a new member,
  someone changing their hours, someone newly rated), and every left swipe deals it to the next
  best fit.
- The post is **not** in *Seats to fill*. You see it under **Fill in › You're In**, with
  **Withdraw**.
- **Not full by book-by:** it disappears, nobody paid anything, and you are told *"Your
  Sat 17:00 didn't fill"*, with **Post again** one tap away.

### 9.3 Limits and withdrawing

- At most **2 posts live at once** (live = until it fills, you withdraw it, or book-by passes).
- A post is **your yes** and, if it fills, counts as **one of your games that week**. With your weekly games already booked, you cannot post for that
  week.
- **Withdrawing before it fills** is free, like any yes. If others are already In, the game
  carries on without you — their yeses stand — and its ribbon drops your name.
- **After it fills** you are a player like everyone else, not an owner.

---

## 10. Fill in

### 10.1 Seats to fill — the rescue board

Seats to fill holds **only rescues**: the open seats of **booked** games that lost players — one
seat in singles, one to three in doubles — **before or after the cut-off**.

- Shown to every member who **fits** (level, kind, gender preference, not blocked) and is
  **free for that hour**.
- The same seat is also dealt as a **Seat open** card to the best fits' decks, and announced to
  people who switched on **Fill in alerts** ([§17.2](#172-notifications)).
- **Pay 30 zł** (Q124) takes the seat at once, because the game already exists. The money follows
  the game's: before the cut-off your share is held, or checked and held at the holding time, and
  you are free to leave until the cut-off like everyone else; after it your share is taken at once
  ([§12.2](#122-when-a-game-fills), Q113). Every rescue join gets the 10-second undo
  ([§6.5](#65-undo)), then **It's a game!**, and the game goes straight to **Home**.
- **A rescuer whose card is refused keeps the seat** for themselves alone for 30 minutes — time to
  fix the card before the cut-off, time to pay after it — never past the game's start. Meanwhile
  the seat isn't offered to others; run out, it is offered again. *(A call made without a ruling,
  Q113: before, a refused rescuer simply didn't get the seat.)*
- Two people go for the same seat at once: the first wins; the second is told immediately.
- **How long a seat stays:** until the cut-off, whatever the number of open seats (a doubles
  that lost three keeps all three open, because a seat still empty at the cut-off calls the game
  off). After the cut-off, until the start, because a late leaver's refund depends on it.

Games that are still filling are **never offered** in Fill in — they are offered only in decks,
and *You're In* lists only your own yeses. Otherwise nobody would need to swipe.

### 10.2 You're In

Your yeses in this group that have not filled yet — **picks, challenges and your own posts
only**; a rescue join goes straight to Home, because that game is booked (Q76). Each row shows
the club, the book-by, who is In as filled squares and the open seats as dashed ones, and
**Withdraw**. The moment a game fills, it appears in **Home** and leaves this list. A full game
that goes back to filling before it is booked is here again, as any game still filling, and stays
on Home as *Seat open* ([§14.1](#141-home-and-the-statuses), Q106). Until Q121 a game waiting for
its *On request* club also stayed here, marked *waiting for the club*, with no Withdraw.

---

## 11. The moment a game fills

When the last yes lands (after the 10-second undo, when it applies):

1. **Every share is held together, or none is** ([§12.2](#122-when-a-game-fills)). Nothing is
   taken until the club's cut-off. A card that is refused gives its player **time to fix the
   card** (after the cut-off, **time to pay**), and the others' holds wait for it.
2. The court is booked with the club and gets its number, **at every club**: nobody at the club
   confirms anything (Q121, [§16.3](#163-one-way-to-work-with-raketa)).
3. **It's a game!** marks the four (or two) being **matched**, not only booked (Q103). The player
   whose yes filled it sees it full screen — the faces and one word, with **Open game** and
   **Later** — and so does a player whose confirmed payment completes a game waiting for it
   (Q110). When another player's payment failed, one line under the word says so: *Waiting for one
   payment · until 14:40 · Nobody pays until it's in* (Q110, [§12.2](#122-when-a-game-fills)).

   **Your own fill is never announced back to you** (Q102): that player gets no banner for it, and
   the bell doesn't count it, though the row is in their list
   ([§17.2](#172-notifications)).
4. Everyone else is told, and the game appears in their **Home**, marked new until opened:
   - **booked at once:** *It's a game! · 30 zł held* — after the cut-off, *It's a game! · you paid
     30 zł*. Each player gets an email from the club saying when the share is taken (*30 zł is held
     on your card and taken on Wed 19:00, the club's cut-off. Leave before then and nothing is
     taken.*; for a checked seat, *Your card was checked. 30 zł will be held from Sat 19:00 and
     taken on Wed 19:00, the club's cut-off. Leave before then and nothing is taken.*), and the
     receipt follows when the share is taken, also kept in You › Payments (Q113);
   - **while one payment is missing:** *It's a game! · waiting for one payment until 14:40*, and
     *Your Tue 19:00 is booked · 40 zł held* (*you paid 40 zł* after the cut-off) when it is in
     (Q110). Nobody is told *It's a game!* twice.
5. At the same moment:
   - every version and every card of that game disappears;
   - the players' other yeses at that hour are withdrawn;
   - one court at that club and hour leaves the pool;
   - a player who reached their games per week has their other yeses that week paused.
6. The game's **chat** opens, with the players as members.
7. The **sides** are drawn for the most even game.

> **Amended 2026-10-12** (Q121, [ADR-0196](../../adr/0196-only-raketa-until-raketa-is-the-clubs-booking-software-and-a-clubs-cancel-moves-the-game.md)
> §1). Steps 2–4 also described a game at an *On request* club: it waited for the club to confirm,
> within the club's time to confirm (30 minutes by default), before anything was held; its filler
> saw *It's a game!* with *Kazimierz Padel answers by 21:15 · Nobody pays until it confirms*; the
> others were told *It's a game! · Kazimierz Padel answers by 21:15*; and the club's yes was one more
> notice, *Kazimierz Padel confirmed your game · 25 zł held*. On request was removed, so every game
> is booked at its fill.

---

## 12. Money

### 12.1 The model

- **The club is the seller.** It is named on every payment screen, receipt and bank statement
  ("paid to Bonarka Arena"). It pays the card processing fee on its sales, as it does at its own
  terminal. Raketa takes **no fee** and pays none.
- **Money goes from players to the club through Raketa** — never from one player to another,
  and no player ever pays another player's share.
- **Nothing is held until a game exists, and nothing is taken until the club's cut-off.** A yes
  costs nothing; so does a card that never fills. When a game fills, each share is **held** on
  its player's card, and it is **taken** at the club's cut-off (Q113).
- **The club's cut-off is the one deadline, the same for everyone in the game.** Leaving before
  it is free; after it, it isn't. No player's card gives them a deadline of their own.
- **The club never pays for a player's leave.** Stripe charges nothing for letting a hold go and
  never returns its fee on a refund. So a leave before the cut-off costs nobody anything, and a
  late leaver whose seat is taken bears the fee kept on their own payment
  ([§12.3](#123-leaving-before-and-after-the-cut-off)).
- **The share** is the court's price divided by the seats, fixed on the card.
- **No estimated card fee is printed anywhere**, to players or to clubs. A fee is shown only once
  Stripe has reported it, on the payment it was kept on (Q113).

### 12.2 When a game fills

- Every player's share is **held** on their saved method **automatically — no screen, no tap** —
  exactly like a subscription: the screen before the first yes was the permission.
- It is **all or nothing**: each share is authorised on its player's card, and the game is booked
  only if every one succeeded, seconds apart. Nothing is taken.
- **A hold lasts only a few days**: 4 days 18 hours on a Visa charged without the player present,
  7 days on Mastercard ([Appendix A](#appendix-a--payments-with-stripe-notes-for-development)). A
  seat's hold **reaches the cut-off** when its last moment is **at least 6 hours after the
  cut-off** — Stripe captures its own delayed payments about 6 hours before a hold lapses. Such a
  hold simply stays until the cut-off.
- **A seat whose hold doesn't reach the cut-off gets a card check.** Its share is held for a few
  seconds and let go at once, all or nothing with the others, which proves the money is there that
  day. It is held again at its **holding time, four days before the cut-off**, inside the
  shortest documented window with margin. The reach margin (6 hours) and the holding lead (4 days)
  are domain constants, never configuration. *(A call made without a ruling, Q113.)*

  > Thursday 19:00's padel at Bonarka Arena has its cut-off on Wednesday at 19:00, and fills a week
  > ahead, on the Thursday before. Ivan's Visa hold wouldn't last until Wednesday, so his card is
  > **checked**: 40 zł held for seconds and let go. Oscar's Mastercard hold reaches Wednesday, so it
  > **stays**. On Saturday at 19:00, the holding time, Ivan's 40 zł is held again, and this time it
  > stays. On Wednesday at 19:00 both are **taken**. Until then either of them can leave, and
  > nothing is taken. Both read *40 zł · free to leave until Wed 19:00* from the moment the game
  > filled.

- **At the cut-off**, every held share of a full game is **taken**, and the real card fee is
  recorded once Stripe reports it. Each player's money line becomes *Paid · 40 zł*. The take is a
  quiet row in their recent notices, never pushed or bannered, and a receipt
  ([§17.2](#172-notifications)). *(A call made without a ruling, Q113: a quiet row, not a push.)*
  A game still short at its cut-off is called off and every hold is let go: nobody pays anything
  ([§12.3](#123-leaving-before-and-after-the-cut-off)).
- **After the cut-off, money is taken at once.** A game that fills after its cut-off (a last-minute
  game) and a rescue taken after it are authorised and taken in one go.
- **If your card is refused** — declined, or your bank asks you to confirm (rare, but allowed even
  with permission on file) — nobody pays, and your seat is kept for you alone for **30 minutes**.
  Which window it is depends on the cut-off:
  - **Before the cut-off: time to fix the card.** It covers a refusal at the fill, at the holding
    time, or taking a rescue. Nothing is being taken, so you are not
    asked to pay. You confirm with your bank in the app, or change card, and the same check or hold
    runs again at your press. Nothing is paid in that window. Your notice, your email and your
    *To confirm* row read *"Fix your card by 14:40 to keep your seat."*, and the email says nothing
    is paid now and the hold is only placed again. It is never past the cut-off or the book-by.
  - **After the cut-off: time to pay** (Q109), where the money is taken at once: *"Confirm your
    payment by 14:40 to keep your seat."* It is never past the book-by.
  - Taking a rescue, either window ends at the game's start at the latest
    ([§10.1](#101-seats-to-fill--the-rescue-board)).
- **While a refused card waits at the fill:**
  - The other players' holds stay on their cards, one they confirmed with their bank included. The
    court is not held, as for any game still filling.
  - The game is *Waiting for one payment* on everyone's Home
    ([§14.1](#141-home-and-the-statuses), Q111). The others are told *It's a game! · waiting for one
    payment until 14:40* (Q110). Nobody is told whose card it is. The
    others' words are the same in both windows; only the refused player's change. *(Written in
    while recording Q113.)*
  - **If you fix it, or pay, in time,** the game books at once on the holds already kept: nobody's
    bank is asked again. You see *It's a game!*; the others read *Your Tue 19:00 is booked · 40 zł
    held* (*you paid 40 zł* after the cut-off).
  - **If you don't,** the kept holds are let go and your seat is offered to others as any open seat
    of a game still filling. You owe nothing. You may still take it back while it is free:
    confirming in the app is your yes again, and if it goes through before somebody else takes the
    seat, the game fills and everyone else's share is held automatically. You are told your time ran
    out (*Your time to fix your card ran out*, or *Your time to pay ran out*), and the others that
    the game is filling again ([§17.2](#172-notifications)).
  - **If no time is left** before the book-by, the game is called off at once and everyone is
    told. So is a game whose court another card books during the wait; its people are dealt a new
    card first, as when any card loses its court
    ([§5.2](#52-what-a-card-promises)).
  - Nothing retries a card by itself.
- **A card refused at the holding time** is on a game already booked. The game stays booked while
  its player fixes the card, and the others aren't told. Fixed in time, the share is held. Not
  fixed, the player's seat opens as a **rescue** and goes to Fill in; they owe nothing, and the
  others are told as for a leave. On the record it counts as **leaving before the cut-off**: on it
  only if the game is then called off ([§15.4](#154-the-record)). *(A call made without a ruling,
  Q113.)*
- **The fallback, never expected under the documented windows.** A holding whose last moment still
  falls short of the cut-off plus 6 hours is **taken at its last safe moment**, its last moment
  less 6 hours. A leave before the cut-off after that is refunded in full, as is that share if the
  game is then called off. This is the one place the club could pay for a leave. *(A call made
  without a ruling, Q113.)*
- **BLIK can't be held** ([Appendix A](#appendix-a--payments-with-stripe-notes-for-development)).
  Its rule is decided when BLIK launches ([O1](#21-open-items)); until then, cards only.

> **Amended 2026-10-12** (Q121, [ADR-0196](../../adr/0196-only-raketa-until-raketa-is-the-clubs-booking-software-and-a-clubs-cancel-moves-the-game.md)
> §1). This section also held the shares at an *On request* club when the club accepted, took them at
> once for a club's yes after the cut-off, gave a card refused at the club's yes its time to fix the
> card or to pay, and kept the club's yes and its court through that window. No club gives a yes
> any more: a share is held at the fill, at its holding time or at a rescue.

### 12.3 Leaving, before and after the cut-off

| When | What happens to your money | Your seat |
| --- | --- | --- |
| **Before the club's cut-off** | **Nothing is taken.** The hold on your card is let go (a checked share has none yet): no refund, and no fee for you or for the club | Becomes a rescue |
| **At the cut-off, if the game is full** | Every share is **taken** | — |
| **At the cut-off, if a seat is still empty** | The game is **called off** and every hold is let go: nobody pays anything, the club included | The court goes back to the club |
| **After the cut-off** | Your share was taken. **Only if someone takes your seat**, you get it back less exactly what was kept on your payment — *38,24 zł* of a 40 zł share paid by a business card — shown to the grosz before you leave and on your receipt. Otherwise nothing comes back | Becomes a rescue until the start |
| **A last-minute game** (filled after its cut-off) | Taken at once; then as *after the cut-off*, from the start. Its card said **No free cancellation** | — |
| **The club cancels, and another of its courts takes the game** (a move by cancel), before or after the cut-off | **Nothing changes**: every hold, or every share already taken, stays as it was, and nobody is refunded | The game moves to that court, and you're told *Game moved* ([§16.9](#169-cancelling-a-booking), Q122) |
| **The club cancels and the game is off**, before the cut-off | Every hold is let go: nothing was taken, nobody is refunded, and nobody pays a fee, the club included | The game is off; an owed card first ([§16.9](#169-cancelling-a-booking), Q123) |
| **The club cancels and the game is off**, after the cut-off | Everyone still in is refunded **in full**, and the club bears the card fees, as the seller (Q44) | The same |

**What was kept on your payment** is Stripe's real fee on it, known once the share is taken: 1,5 % +
1 zł on a personal card from the EEA, 1,9 % + 1 zł on a business card, 2,5 % + 1 zł on a UK card
and 3,25 % + 1 zł on a card from outside Europe
([Appendix A](#appendix-a--payments-with-stripe-notes-for-development)). On a 40 zł share that is
38,40, 38,24, 38,00 or 37,70 zł back. The club neither earns nor loses on a late leave (Q47, as
Q113 amends it). For a club on its own negotiated Stripe pricing the fee arrives later: until it
does, the leave sheet gives no figure and no clause, and the refund waits until the fee is known.
**This deduction waits for the lawyer** (O3); if it is refused on personal EU cards, the fallback is
everything back on those cards ([§12.5](#125-saving-a-payment-method-and-the-terms)).

How long a refund takes to reach a card, up to two weeks, is shown when it is issued. Nothing
mentions BLIK while BLIK isn't offered.

### 12.4 Payment methods

- **At launch: cards, Google Pay, and Apple Pay** — Apple Pay only if it passes a real test
  (Stripe documents saving Apple Pay for regular recurring charges; Raketa's are one-off). The
  setup shows only the phone's own wallet: Apple Pay on iPhone, Google Pay on Android (Q82).
- **BLIK:** Stripe's BLIK page says a saved BLIK can be charged later without the player
  present; another Stripe page contradicts it, and the recurring version is a preview. **Confirm
  with Stripe before building.** If confirmed, BLIK launches beside cards; if not, it follows
  when Stripe opens it. See also open item [O1](#21-open-items). **BLIK can't be held** (Stripe:
  no manual capture), so it can't wait for the cut-off as a card does: its rule is decided when
  BLIK launches, and until then it is cards only (Q113).
- **Przelewy24** cannot be saved, so it cannot be used.

### 12.5 Saving a payment method, and the terms

Saving a method is **You › Payments**, a four-step setup (Q82; screens in [the-screens.md](the-screens.md)), opened by itself
the first time you say yes or post without one — never during onboarding (Q96):

1. **Choose how you pay** — Card · BLIK · the phone's wallet. BLIK shows *"launches when Stripe
   confirms saved BLIK"* and cannot continue yet.
2. **Card details** — Stripe's own secure fields, styled to the design; the app never touches a
   card number. A wallet skips this step.
3. **Accept the terms** — **before** anything is saved, as Stripe and the law require.
4. **Confirm with your bank** — this step saves the method; if the bank wants its one-time check
   it appears, otherwise the step ticks itself.

**Change** keeps the old method working until the new one is saved; **Remove this method** is
allowed only with no live yeses and no upcoming booked games (Q83).

The terms, in full (Q113):

> Your card is saved. When a game you said yes to fills, the club it is played at holds your
> share on your card — the court's price divided by the players. If that hold would not last until
> the club's cut-off, your card is checked when the game fills (your share held for a moment and
> let go), and your share is held four days before the cut-off. Your share is taken at the club's
> cut-off. Leave before the cut-off and nothing is taken. After the cut-off your seat is offered to
> others; if someone takes it, you get your share back less what was kept on your payment, and you
> see the exact sum before you leave. If a game is still missing a player at the cut-off, it is
> called off and nothing is taken.

**These are a new version of the terms.** The backend's version in force moves with the client's
text, and a game holds only the share of a player who accepted the version in force, so a player
who accepted the earlier words is asked to accept these, through the same step, before their next
game holds their money.

The wording is reviewed by a lawyer before launch. Beyond a new version of the terms, the app asks
again only if the bank changes the card's brand (Visa → Mastercard), because a changed brand cannot
be charged without it.

**A note for that review (Q113, O3):** before the cut-off nothing is ever taken, so the review
there is only the hold's disclosure. **The clause after the cut-off waits for the lawyer**:
keeping back exactly what was kept on a leaver's own payment when someone takes their seat. A
leaver after the cut-off has no right to money back (a dated sports booking carries no
withdrawal right), and the sum kept is the real cost, but Polish payment law bars a payee's charge
for using a personal card issued in the EU (art. 37a ust. 3 UUP). If the lawyer finds the
deduction is such a charge, **the fallback is everything back on personal EU cards**; business
cards and cards from outside the EU keep the rule. No figure is ever an estimate
([§12.3](#123-leaving-before-and-after-the-cut-off)).

**Two more questions for that review (Q124).** A swipe is the order, and Polish law reads only the
words on the control that binds a consumer to pay: they must say *"zamówienie z obowiązkiem
zapłaty"* or an equivalent, or no contract is made (art. 17 ust. 3–4 of the consumer rights act).
The EU Court applies this even when payment falls due only after a later condition (C-400/22), and
judges only the words on the control itself (C-249/21). No authority has ruled on a swipe.

1. **Can a swipe whose stamp reads *PAY · 40 zł* be the order under art. 17?**
2. **Does a vote whose stamp reads *I'M IN · 40 zł* bind the player to the share taken at the
   cut-off?**

**If the answer to (1) is no, the agreed fallback** is that a money-moving yes opens a confirm
screen with a ***Pay 40 zł*** button. **The words count legally only in Polish.** The app shows
English until it is translated, so the translation must land before a real club takes a player's
money.

### 12.6 The club's money

The club is paid **after the game is played**, as a normal payout. A share is the club's money
only once it is taken at the cut-off; a held share is not collected yet. Until the start, a late
leaver's refund can still happen, so the money stays where it can pay it. Wording in the app:
*"the club's payment is on its way"*, never *"the club is paid"*.

---

## 13. Leaving a game

**Leave the game** is at the bottom of the game details. A sheet says what it will cost
**before** you confirm:

| When | The sheet says |
| --- | --- |
| Before the cut-off | Leaving is free: *"Nothing is taken: the hold on your card is let go. Your seat is offered to others. On your record only if the game is then called off."* (a checked share has no hold yet: *"Nothing is taken."*). The line under the button says the same, and the toast reads *"You left the game. Nothing was taken."* (Q113) |
| After the cut-off | *"Your seat is offered to others. If someone takes it, you get 38,24 zł back (40 zł less the 1,76 zł kept on your payment); if nobody does, you won't. On your record if nobody takes it."* The figure is the exact one for that payment; while its fee isn't known yet, the sheet gives no figure and no clause (Q113) |
| Waiting for one payment | *"Nobody has paid yet. Leaving withdraws your yes."* The game goes back to filling, your seat open: the others stay In, and the game stays on their Home as *Seat open* until it is full again (Q106). A player whose card waits keeps their time to fix it, or to pay. (Until Q121 this row also served a game waiting for its *On request* club: the request was taken back, the game went back to the club when it refilled, and a leave after its book-by called it off.) |
| After the start | No button. |

The leaver's email says the same (Q113): before the cut-off, *You left the game · nothing was
taken* / *"The 40 zł hold on your card is let go. Your seat is offered to others."*; after it, *You
left the game* / *"Your seat is offered to others. If someone takes it, you get 38,24 zł back (40 zł
less the 1,76 zł kept on your payment)."*, with no figure while the fee isn't known yet. No email
says when a refund reaches BLIK. *(The bodies were written in while recording Q113.)*

The others in the game are told, with the new state of the game:

- from a booked game, *"Kuba left — the seat is open"*, in the chat and by notification;
- from a game waiting for one payment, *"Oscar Bertran left your game — it's filling again."*
  (Q104). A leave from a game waiting for its club after its book-by, which called it off
  (*"Oscar Bertran left after its last moment to book"*), went with *On request* (Q121).

**A leaver is told only when it touches them** (Q108). Once you have left, you hear about the game
again in two cases only. Apart from the refund a late leaver gets when someone takes their seat —
*"You've been refunded 38,24 zł · your seat was taken"* / *"40 zł less the 1,76 zł kept on your
payment."*, the notice and the email (Q113, [§17.2](#172-notifications)) — nothing else about it
reaches a leaver:

- **your empty seat called it off at the cut-off:** *"Tuesday's 19:00 at Bonarka Arena, which you
  left, was called off"* / *"Your seat stayed empty, so it counts on your record. Nothing was
  taken from you."* (Q113: a leave before the cut-off took nothing, so there is no refund to
  stand). It changes no money, so it isn't emailed. What it costs is §15.4's: 10 points since Q117;
- **the club's cancel refunded you** — you left after the cut-off and your seat was still paid
  for: you are told in a leaver's words, with the club's reason and your refund, and never promised
  a new game. The notice and the refund email both use those words. A cancel that moves the game
  to another court ([§16.9](#169-cancelling-a-booking), Q122) refunds nobody, so it doesn't reach
  you.

---

## 14. After booking

### 14.1 Home and the statuses

A game card in **Home** (and the status row of its details) shows one status. **Planning, Game
on, Needs a player** and **Held** are gone: the booking *is* the plan.

| Status | When | Money line |
| --- | --- | --- |
| **Waiting for one payment** | One player's card was refused when the game filled, and their time to fix the card (before the cut-off) or time to pay (after it) runs ([§12.2](#122-when-a-game-fills), Q111, Q113) | *Waiting for one payment · until 14:40 · Nobody pays until it's in*, in both windows. The refused player's own card reads *Fix your card by 14:40* before the cut-off and *Confirm your payment by 14:40* after it, beside their *To confirm* row |
| **Booked** | Full and booked | Before the cut-off, whether the share is held yet or only checked: *30 zł · free to leave until Sat 17:00*. After it, once the share is taken: *Paid · 30 zł* (Q113). A player whose card was refused at the holding time reads *Fix your card by 14:40* until it is fixed; the game stays booked, and the others' cards don't change |
| **Seat open** | Someone left a booked game | Before the cut-off: *1 seat open · fills by Sat 17:00 or the game is off and nothing is taken*. After: *1 seat open · offered to others · the game goes ahead* |
| **Seat open** | A full game went back to filling before it was booked (Q106) | *1 seat open · books when it's full · nobody paid* |
| **Needs result · Confirm the result · Counted · Uncounted · Played · no score** | After the hour ([§15.2](#152-results-and-sportsmanship), [§15.3](#153-a-game-nobody-recorded-and-a-game-somebody-didnt-come-to)). *Needs result* follows *How did it go?* on a Competitive game; *Played · no score* replaced *Never played* (Q114); *Uncounted* says why — a seat empty at the hour, or someone who didn't come (Q115) | — |
| **Called off** | A seat was empty at the cut-off; the club cancelled and no other court of the club took the game ([§16.9](#169-cancelling-a-booking)); a game that went back to filling reached its book-by; a failed payment had no time left before the book-by, or the court went to another card while it waited for that payment | The reason, and *nothing was taken* (the holds were let go: at the cut-off, or a club's cancel before it), *refunded 30 zł* (a club's cancel after the cut-off) or *nobody paid* |

**A full game that falls back stays on Home** (Q106). It goes back to filling before it is booked
when a player leaves it while it waits for one payment, when a yes is taken back meanwhile, or when
a player's time to fix the card or time to pay runs out. For those still In it reads *Seat open*,
as a booked game that lost a player does, and it is in *You're In* as well
([§10.2](#102-youre-in)). It becomes *Booked* when it refills, and *Called off · nobody paid* if
its book-by passes first. Until Q121 a game also fell back while its *On request* club decided,
and became *Waiting for the club* again when it refilled. A player who withdraws their own yes no
longer sees it on Home, and Home's badge doesn't count it: it asks nothing of those still In.

*Waiting for one payment* ends **Booked** when the payment comes in, or *Seat open* when the time
to pay runs out (Q111).

**A booked game names its court's kind** on its Home card and its details: *Court 3 · indoor*
(Q122).

The club's answer — *Kazimierz Padel said no* and *Kazimierz Padel didn't answer in time*, the same
on the called-off card, its details, the notice and the email (Q105) — went with *On request*
(Q121): no club answers a game. A club's cancel that calls a game off is told with its reason and
*We'll look for another game for you first* ([§17.2](#172-notifications), Q123).

*Free to leave until* names the club's cut-off, the same moment for everyone in the game. Until
then nothing has been taken, and leaving lets the hold go, so the word is true
([§13](#13-leaving-a-game); Q113, amending Q99, whose reason — never call a leave free when it
costs a fee — is now met). At the cut-off the share is taken and the line becomes *Paid · 30 zł*.

The game's details say when the share is held and when it is taken: *30 zł held on your card ·
taken Sat 17:00 · free to leave until then*, or for a checked share *30 zł held from Tue 17:00 ·
taken Sat 17:00*, and *Paid · 30 zł* after the cut-off ([§14.2](#142-the-game-details)). So a
40 zł hold that appeared and vanished the day a game filled far ahead is explained as the card
check.

*Answers by*, the end of an *On request* club's time to confirm on a game waiting for it (Q98),
went with *On request* (Q121, [§16.8](#168-answering-a-request-on-request)).

A game that **starts with a seat still open** (someone left after the cut-off and nobody took
it) cannot take a result. It ends **Uncounted · a seat was empty**: no levels move, and nothing
goes on the record of the players who stayed.

### 14.2 The game details

From the mocks (details 5–10, in [`mocks/game-details/`](mocks/game-details/)), locked:

- **Top bar:** back; the other players' faces (up to three); their names as the title;
  the sport and status as the subtitle; **Chat · 2** on the right while you are in the game and
  it is not over, lit volt when something is unread.
- **The game card:** status row (dot + status); player tiles — two rows for doubles, one for
  singles — with the *vs* line naming the sides; tapping a tile opens that player's record;
  the court facts (**WHERE** club · court · its kind · distance — *Bonarka Arena · Court 3 ·
  indoor · 3,1 km* (Q122) — **DAY**, **TIME** start–end, the money row,
  which says when the share is held and when it is taken — [§14.1](#141-home-and-the-statuses)).
- **The balance forecast**, as today. Hidden while a seat is open.
- **At the court:** from the hour's start to 30 minutes after it, *isn't here yet* beside each
  courtmate's tile, *I'm here* for yourself when you're the one waited for, *They're here* for a
  courtmate who was, and afterwards *I was there* and *Yes, they were here*
  ([§15.1](#151-attendance-at-the-court), Q115). There is no QR code and nothing to show at the
  desk (Q116).
- **After the hour:** *How did it go?* on a Competitive game, which leads to putting the score up,
  and *Is that right?* for the other side ([§15.2](#152-results-and-sportsmanship), Q119).
- **Leave the game** ([§13](#13-leaving-a-game)).

The same screen serves two more readers (Q75, Q96):

- **Before the game is booked** (tapping a card, its **i**, or a You're In row): the status row
  reads *Filling · 2 of 4 in* — or, for a game that had filled, *Seat open* or *Waiting for one
  payment*, as on Home ([§14.1](#141-home-and-the-statuses)); WHERE names the club with no court
  number, and *Indoor* or *Outdoor* when every free court it could be booked on is of that kind
  (Q122); the money row reads *"30 zł if it fills · book by Sat 13:00"*; the overlap grid and one
  plain paragraph on what a yes means follow; the actions are **I'm in / Not this time**, or
  **Pay 30 zł / Not this time** on a *Book it now* game, whose last seat your yes takes (Q124);
  **Withdraw** if you are In; and while it waits for one payment, **Leave the game** with its sheet
  ([§13](#13-leaving-a-game)). No Chat. Until Q121 it could also read *Waiting for the club*, with
  *nobody pays until Bonarka confirms* and *Bonarka answers by 20:45*.
- **A rescue, seen by a member who is not in it** (a Seat open card or a Seats to fill row):
  the paid tiles, the dashed *You?* tile, the court number, and **Pay 27 zł** (Q124) — said as
  *held until the cut-off* before it, and *paid now* after it (Q113). No Chat, no Leave.

### 14.3 The chat

- **One chat per game.** It opens **when the game is booked** — at its fill, at every club since
  Q121 — because there is nothing to talk about before, and yeses are silent.
- **Members are whoever is in the game now.** A leaver drops out with a line *"Kuba left — the
  seat is open"*; a joiner comes in and sees the history.
- Reached **from the game details** and **from the speech bubble on its Home card**, which
  opens it straight over Home (Q100). The back chevron returns to the screen it was opened from:
  the details, or Home. The chat room is only the conversation: no plan card, no Details button,
  no way into the details. From a chat opened on Home, Back lands on the card, which already
  shows the court and the hour.
- It closes as today: 48 hours after *we played*, when the result window closes, or when the
  game is called off.

---

## 15. On the day and after

### 15.1 Attendance at the court

Nobody checks in, and **everyone who arrives on time does nothing** (Q115, Q116). Whether somebody
came is caught by the people waiting for them, at the court, while it happens. Take Wednesday 14
Oct, tennis 17:00–18:00 at Ogrody 33, 40 zł each:

1. **From 17:00 to 17:30**, the first half of the game, Ivan can tap **"Oscar isn't here yet"** on
   the game's details. It works only from the club: the phone reads its location at that tap.
2. **Oscar is pushed at once:** *"Ivan is at Ogrody 33 and you're not there yet — tap I'm here when
   you arrive."*
3. **His arrival** is the first of two things, each made at the club: his own **I'm here**, or
   anyone on the court tapping **"Oscar's here"** when he walks in. Whoever tapped is told *Oscar is
   at the club*.
4. **The arrival time decides what it was:**
   - **on time** within 10 minutes of the start: nothing is recorded, and the tap vanishes;
   - **Came late** from 10 to 30 minutes after the start;
   - **Didn't come** if he wasn't there by 17:30.
5. **A phone that died gets one way back.** Within 24 hours of 17:30, Oscar taps **I was there**;
   the others on the court are asked *Were they there?*, and any of them can confirm it with **"Yes,
   he was here"**. That turns *Didn't come* into *Came late*, because the tap still proves he wasn't
   there when it was made. Until those 24 hours end, *Didn't come* is provisional.
6. **The tap costs the person who made it nothing.**

- **Who may tap** *(a call)*: any player on the court who is at the club, about any other, partner
  included; never about yourself; never while you are yourself absent and not yet arrived. Two
  absentees can each be tapped. *They're here* is checked for location too *(a call)*.
- **At the club** means within **300 m** of the club's map point, allowing for the fix's own stated
  accuracy up to 200 m, so that a large indoor hall still passes *(a call)*.
- **Location** is a precise, one-shot fix, read in the foreground only at the moment of the tap and
  sent with it. The backend compares it with the club's map point and keeps only *at the club, at
  that time*; **the coordinates are never stored**, on the phone or on the server *(a call)*.
  Background location stays off.
- **Refusals are plain sentences:** not at the club — *You can say so only from Ogrody 33*; location
  off — the phone asks for it and says why; outside the window — it says the window has passed.
- **What it changes.** *Didn't come*: the game takes no score and never counts, as a confirmed
  no-show did. *Came late*: the game carries on as usual, score and Level included. Each is priced on
  the record ([§15.4](#154-the-record)). The outcomes are read against the server's clock, never the
  phone's.
- **Money never moves on any of this.** Everyone paid, and the club was paid for the hour; nobody is
  refunded and nobody owes anything.
- **The club sees none of it.** Its Bookings reads *Played* for every game that reached its hour
  ([§16.7](#167-bookings)).
- **There is no desk check-in** (Q116). The *Show at the desk* QR card, the club's **Check in** page
  and its switch were removed on 2026-10-11 ([§16.10](#1610-check-in)).

### 15.2 Results and sportsmanship

**The score is asked for once, and is settled by one tap or by silence** (Q119). On a
**Competitive** booked game:

1. **No score is taken before the hour.** The entry window runs from the game's start until 24
   hours after its hour ends.
2. **When the hour ends, all of its players are asked *How did it go?*** Any of them puts the score
   up.
3. **The other side is asked *Is that right?*** One *That's right* from either of them settles it
   **at once** and closes the game. In doubles, the first agreement wins, and a later different
   score is refused.
4. **Silence settles it 24 hours after the score**, or after its last correction, and the screen
   says so truthfully: when silence makes the score the result, and that silence costs nothing.
5. **Corrections stop when the entry window closes.** Until then, either player of the side that
   put the score up may correct it while the other side hasn't answered.
6. **Levels move the moment the result settles**: within a minute of a *That's right*, or of the
   24-hour mark on silence.

When **two scores** stand when the answer window closes — one per side, neither accepted:

- **the same winner:** the game counts with the **closer** score, the one with the smaller
  difference in games won; on a tie, the first score put up *(a call)*;
- **different winners:** the game is **disputed**. No Level moves, and each of the two who put a
  score up gets a ***Results left in dispute*** line on their record. The line is information only
  and costs no points ([§15.4](#154-the-record)).

Nobody rules on a score — not the club, not Raketa.

A **For fun** game asks nothing and reads *Played*. A score can be added for fun; it stands at once
and needs no answer *(a call)*. No Level moves, as before.

The sportsmanship stars are unchanged from today.

### 15.3 A game nobody recorded, and a game somebody didn't come to

- **A game that was full counts as played** (Q114). A booked game that reached its hour full, that
  nobody recorded and that nobody *Didn't come* to, reads **Played · no score** for all of its
  players when its entry window closes. Each of them gains the 5 points of a game played through,
  and no Level moves. *Never played* is gone: there are no unbooked games left, and a booked, paid
  court is the evidence it stood in for.
- **A game somebody didn't come to** ([§15.1](#151-attendance-at-the-court)) takes no score and
  does not count, and no levels move. It reads *Uncounted*, with the reason. The player who didn't
  come had paid, so there is no debt, and nobody is refunded — the court was used.
- **The no-show report is gone** (Q115). Until 2026-10-11 the players who were there could tap
  *"Kuba didn't come"* while entering the result, from anywhere, and Kuba had 24 hours to dispute
  it. A game that held such a report reads *Played · no score*.

### 15.4 The record

**Player reliability is points** (Q117). Everyone starts at **100**. A failure takes a fixed price
off; every game **played through** — a booked game that reached its hour full with the player on
its court, on time and not called off, scored or *Played · no score* — gives 5 back, never above
100. Each failure drops out of the figure **6 months** after it happened. The window rolls, so
nothing ever resets everything at once.

| What happened | Part | Points |
| --- | --- | --- |
| **Didn't come** ([§15.1](#151-attendance-at-the-court)) | Shows up | −25 |
| **Came late** | Shows up | −10 |
| Leaving after the cut-off when nobody takes your seat, so the game is played short | Keeps plans | −15 |
| Leaving before the cut-off when your seat stays empty and the game is called off because of it | Keeps plans | −10 |
| Each game played through | — | +5, up to 100 |

**Never on the record:** swiping left · withdrawing a yes · a card or post that never filled · a
failed payment you fixed · leaving when your seat is taken, or before the cut-off when the game still
plays · a game the club cancelled · silence on a score · a disputed score (a line, never points).

A seat lost because its player's card wasn't fixed at the holding time counts as **leaving before
the cut-off**: on the record only if the game is then called off because of it
([§12.2](#122-when-a-game-fills)). *(A call made without a ruling, Q113.)*

- **A *Came late* game earns nothing back** *(a call)*: only a game played through on time earns +5.
  Otherwise a late arrival would net only −5. A game that started short earns the players who
  stayed nothing either way.
- **A *Didn't come* is priced once**, on Shows up, and no longer also breaks Keeps plans.
- **Bands**, shown under the figure: **Very high** 90–100 · **High** 75–89 · **Medium** 50–74 ·
  **Low** below 50 reliability. As a rule of thumb, one no-show keeps you High, two close together
  drop you to Medium, and three to Low.
- **New.** A player reads ***100 · New*** until their first 3 games are played through, ever, and
  passes every filter. Stopping for 6 months doesn't make anybody New again *(a call)*.
- **The record sheet shows counts only**, over the last 6 months: *Shows up* — turned up 12 of 13;
  *Keeps plans* — kept 13 of 14; *Being late* — late 1 time; *Results left in dispute* — 0. No ledger.
- **One figure per player, across sports**, computed whenever it is read — now including one read
  of the members' points per deal, for the filter below *(a call)*.

**The reliability filter** (Q118). The Player reliability screen has an optional switch, off by
default: ***Play only with players of at least High reliability*** (or *at least Medium*).

- **Where it applies.** It keeps the player off every court shared with somebody below that band,
  in both directions: *Picked for you*, *Challenges*, *Seat open* and Fill in. It is one more clause
  of the pair rule ([§5.1](#51-what-it-does)).
- **From when.** From the moment it is switched on, or the moment someone drops below it. Yeses
  already given stand *(a call: the fill doesn't re-ask it, unlike a block)*, and booked games never
  change.
- **What the filtering player sees:** *"Your filter hides 2 of the 11 players in your groups."*
- **What a hidden player sees, with nobody named:** *"Some players in your groups play only with
  High reliability or above. At 75 you're dealt with everyone again."*
- **A group's Members list** shows each member's points and band.

---

## 16. The club website

Everything the club does for Games and Fill in happens on the **club website** (`frontend_club`),
signed in with the club's own account. The player app never shows club tools, and Administrators
(players acting for a club in the app) never handle courts, bookings or money.

> Items marked **◇** were filled in while writing this section, after the grilling ended, to close
> gaps nobody had decided. They follow from the grilled decisions but were not themselves put to
> the product owner — overrule any of them freely.

### 16.1 What it has today, and what this adds

| Page | Today | With Games and Fill in |
| --- | --- | --- |
| **Overview** | The club's landing page | The setup checklist until the club is live ([§16.2](#162-getting-ready-to-take-bookings)); after that, a line that the club is live on Raketa and a link to today's Bookings (Q121, *a call*: it showed only what was waiting for the club's answer, Q86, Q95, and nothing waits any more). The statistics that will live here later are out of scope. |
| **Details** | Name, district, city, sports, map point | Unchanged |
| **Administrators** | Invite and manage Administrators | Unchanged |
| **Groups** | The club's official groups, their *Games* figure (reads 0 today) and Hand over | *Games* counts the games actually booked in each official group; the "other clubs' courts" setting links from here ([§16.13](#1613-official-groups-and-administrators)) |
| **Courts & prices** | — | **New** ([§16.4](#164-courts), [§16.5](#165-hours-and-prices)) |
| **Raketa settings** | — | **New** ([§16.3](#163-one-way-to-work-with-raketa), [§16.6](#166-settings)) |
| **Bookings** | — | **New** ([§16.7](#167-bookings)–[§16.9](#169-cancelling-a-booking)) |
| **Check in** | — | **Removed** on 2026-10-11 (Q116), after it was built: whether somebody came is caught at the court ([§15.1](#151-attendance-at-the-court), [§16.10](#1610-check-in)) |
| **Money** | — | **New** ([§16.11](#1611-money)) |

### 16.2 Getting ready to take bookings

A club's courts reach players' decks only when **all four** are done. The Overview shows them as a
checklist, says which one is missing, and drops the checklist once the club is live (Q95):

1. **Connect payments** — the club's Stripe account, through **Stripe's own hosted sign-up** (the
   club is sent to Stripe and comes back; company data with REGON, the representative and owners,
   a Polish IBAN). The club gets its **full Stripe dashboard** for payouts and disputes. The club
   is the seller, so without it nothing can be charged (Q86).
2. **Add your courts** ([§16.4](#164-courts)).
3. **Set hours and prices** ([§16.5](#165-hours-and-prices)).
4. **Check the settings** — the cut-off and the release lead ([§16.6](#166-settings)).

Until then the club still exists for search, groups and Administrators exactly as today. There were
five steps until Q121: the second was *Choose how you work with Raketa*, which went with the choice
([§16.3](#163-one-way-to-work-with-raketa)).

### 16.3 One way to work with Raketa

**Only Raketa** is the one way, for every club, **until Raketa is the club's booking software**
(Q121). The club hands Raketa a block of hours, its courts' Raketa hours
([§16.5](#165-hours-and-prices)):

- **Who sells the court:** Raketa alone, until the release time. The club keeps those hours off its
  own desk and its own system until then.
- **When a game fills:** it is booked at once. Nobody at the club confirms anything.
- **Book-by:** the release time — the release lead before the game, 1–13 days, 3 by default
  *(a call: the range stays in days)*. So no game fills later than a day before its start
  ([§5.4](#54-the-only-deadline-the-courts-book-by)).
- **After the release time:** unsold hours go back to the club and leave Raketa.
- **If it goes wrong:** the desk sold a handed-over hour by mistake. The club cancels with *double
  booking*, and a free court of the same club takes the game when one can
  ([§16.9](#169-cancelling-a-booking)).

> **Amended 2026-10-12** (Q121, [ADR-0196](../../adr/0196-only-raketa-until-raketa-is-the-clubs-booking-software-and-a-clubs-cancel-moves-the-game.md)
> §1). This section was *Three ways to work with Raketa*: each club chose one way for the whole club
> (Q12), **Only Raketa**, **Instant** — Raketa and the desk both sold, and the club closed by hand
> every hour it sold elsewhere, its book-by the start minus a minimum notice (default 2 h) — or
> **On request**, where the club confirmed each full game within a time it set (default 30 min) and
> nobody paid until it did. On request let a shut desk kill every game that filled while nobody was
> there, and Instant asked a desk to keep two calendars true by hand, for ever. No court platform
> makes a club confirm a booking, none relies on a desk closing hours by hand, and every one that is
> effortless for the club has one calendar; Kraków's tenis4U, Playmore and kluby.org offer no API,
> and tenis4U's terms forbid reading its site. So both ways were removed, and **Raketa will become
> the club's booking software**, its shape decided in a grilling of its own. The *future live link
> to the club's own booking system*, which this section called the Instant way kept up to date
> automatically, is replaced by that decision ([§20](#20-out-of-scope)).

### 16.4 Courts

- The club lists its courts ◇: a **name** as the club uses it (*Court 2*, *Kort centralny*), **one
  sport** per court, and **indoor or outdoor**, its **kind**, because it matters to players. Players
  see it since Q122: always on a booked game, and on a card when every free court it could be booked
  on is of one kind ([§5.2](#52-what-a-card-promises)).
- A court can be switched **off** (not offered to Raketa) without deleting it.
- Players never pick a court number. A card promises "a court at this club at this hour"; the
  number is **given at booking** — the first free court of that sport at that hour ([§5.2](#52-what-a-card-promises)).
- The club can **move** a booked game to another free court of the same sport at the same hour
  (a court needs repair, a better fit for the desk) ◇, of the **same kind, or indoor for an outdoor
  game** — never outdoors from indoors (Q122, *a call*). Players see the new number and are told
  *Game moved* · *Padel · indoor · nothing else changes* ([§17.2](#172-notifications)); nothing
  else changes. Until Q122 a move told nobody.

### 16.5 Hours and prices

- **Which hours go to Raketa** ◇: a weekly pattern per court in **1-hour slots** — for example
  *Courts 1–3, Mon–Fri 17:00–22:00, Sat–Sun 09:00–14:00* — set on a week grid. Every Raketa game is
  1 hour (Q30), so a club whose own grid runs in 90-minute slots publishes 1-hour slots for Raketa.
- **Exceptions** ◇: close a single hour, a day or a date range (a tournament, a holiday, a repair)
  without touching the pattern.
- **Prices** ◇: a price **per court per hour**, with optional price bands (for example weekday
  evenings and weekends dearer). The player's share is that price divided by the seats.
- **Changes apply forward.** A new price or a closed hour never changes a card already dealt or a
  game already booked:
  - a card already dealt keeps its price;
  - closing an hour that has **cards** on it (people In, not booked): the cards move to another
    free court at that hour, or disappear and the people who were In get a new card first; nobody
    was charged;
  - closing an hour that has a **booking**: not allowed from the calendar — the club cancels the
    booking instead ([§16.9](#169-cancelling-a-booking)).
- **Raketa's hours stay off the club's own desk** until their release time (Q121). *Instant* clubs,
  removed with Q121, had to close straight away every hour they sold at their own desk, one click
  per hour ◇.

### 16.6 Settings

| Setting | Default |
| --- | --- |
| Release lead: days before the game unsold courts return to us (1–13) | 3 days |
| Free-cancellation cut-off (players leave free until it; a game still short at it is called off) | 24 h before |
| Offer our groups other clubs' courts when ours are full ([§4.3](#43-courts)) | off · 10 km |
| Pause Raketa bookings ([§16.15](#1615-pausing-or-leaving-raketa)) ◇ | off |

A changed setting applies to games booked **after** the change; a booked game keeps the cut-off it
was booked with ◇. *We check players in* was removed with check-in on 2026-10-11 (Q116). *How we
work with Raketa*, the *minimum notice* (2 h) and the *time to confirm* (30 min) were removed with
*Instant* and *On request* on 2026-10-12 (Q121).

### 16.7 Bookings

One page, by day, listing every Raketa booking at the club ◇:

| Column | What it shows |
| --- | --- |
| **When · court** | Day, hour, court number and its kind (with **Move** to another free court of the same kind, or an indoor one for an outdoor game — Q122) |
| **Sport · kind** | Padel · Competitive, Tennis · friendly… |
| **Players** | Each player's name, and their share **held** or **taken** (Q113). Nothing about who came or the score (Q115, Q116) |
| **Status** | See below |
| **Money** | Court price, collected, refunded |
| **Where it came from** | The group it was booked in (official or player group) |

The statuses the club sees:

| Status | Meaning for the club |
| --- | --- |
| **Booked** | Full; its shares are held until the cut-off and taken at it. Before the cut-off it can still be called off if a player leaves and nobody replaces them |
| **Seat open** | A player left; Raketa is finding a replacement. Before the cut-off: if nobody is found, the game is called off at the cut-off and the court comes back to the club |
| **Called off** | With the reason: short at the cut-off, or cancelled by the club when no other court took the game ([§16.9](#169-cancelling-a-booking)). Every hold was let go, or everyone was refunded (a cancel after the cut-off); the hour is free again |
| **Played** | The hour has passed — whatever the players record about who came and the score, which the club never sees (Q115) |

Filters: all · seat open · called off
([the-screens.md B4](the-screens.md#b4-bookings)) ◇.

*Waiting for you* (a full game asking for the court, with **Accept** and **Refuse** before a
countdown), *Accepted · waiting for one player's payment* (Q112), the *refused* and *no answer*
reasons and the *waiting for you* filter went with *On request* (Q121).

### 16.8 Answering a request (On request)

**Removed on 2026-10-12** (Q121, [ADR-0196](../../adr/0196-only-raketa-until-raketa-is-the-clubs-booking-software-and-a-clubs-cancel-moves-the-game.md) §1), after it
was built. An *On request* club was shown each full game as a **Waiting for you** booking, with the
players, the hour, the sport, the price and a countdown, and emailed *A booking is waiting for your
answer*. **Accept** held every share and gave a court number; an Accept that met a refused card
waited on that player's payment, *Accepted · waiting for one player's payment until 21:20* (Q112),
and a lapse was emailed *A game didn't go ahead*. **Refuse**, or **no answer** in time, called the
game off as *refused* or *no answer*, the players read *Kazimierz Padel said no* or *… didn't
answer in time* (Q105), and they were dealt a new card first. While a request waited, the hour was
reserved for it.

A desk that was shut when a game filled let its request run out, so every game that filled while
nobody was there was called off, and the desk had to watch the website all day. No court platform
asks a club to confirm a booking. Every full game is now booked at its fill
([§16.3](#163-one-way-to-work-with-raketa)), and the club answers nothing.

### 16.9 Cancelling a booking

- **Cancel** on a booking, with a reason ◇: *weather*, *repair*, *double booking*, *other*.
  *Double booking* stays though *Instant* is gone (Q121, *a call*): a club can still sell a
  handed-over hour at its own desk by mistake.
- **A cancel first tries to move the game** (Q122). Raketa looks at the same club for another free
  court with the same **sport**, **day**, **hour** and **price** *(a call: price is per club and
  sport today, so it always holds; the rule keeps it for prices per court)*, of the **same kind, or
  indoor for an outdoor game** — and for a ***weather*** cancel, **indoor only** *(a call)*, because
  an outdoor court at the same hour is rained on too. The same kind is picked first, then indoor,
  each in the club's own court order *(a call)*.
- **If one is free, the game moves there: a move by cancel.** Every hold, or every share already
  taken, stays exactly as it was: nothing is refunded, let go or released, before or after the
  cut-off. The court number changes; nobody is owed a card, nobody swipes, and it is on nobody's
  record. Every player is told *Game moved* ([§17.2](#172-notifications)): *Bonarka Arena moved your
  game to Court 3 · Thu 19:00* / *Court 2 can't be played · Padel · indoor · nothing else
  changes*.
- **The cancel dialog shows what it will do** before the club confirms *(a call)*: *This game moves
  to Court 3 · indoor · the players are told, nobody is refunded*, or *This game is called off*
  with the consequence below. When it would move, the dialog also offers **Cancel the game
  anyway**, for a club closing the whole hour (an event, a power cut). The cancel decides afresh
  when the club confirms: a court taken in between moves the game to the next court that
  qualifies, or calls it off, and the answer says which.
- **Otherwise the game is called off**: with *Cancel the game anyway*, or when no court qualifies
  (an indoor game with only an outdoor court free, or no court at all). **Before the cut-off every
  hold is let go**: nothing was taken, nobody is refunded, and nobody pays a fee, the club included
  (Q113). **After the cut-off everyone is refunded in full.** Either way it goes on **nobody's
  record**, and the players still in are dealt an **owed card** first. They are told the club
  cancelled, with the reason and *We'll look for another game for you first* *(a call: the email
  already said it)*, and told again when the new card arrives ([§17.2](#172-notifications), Q107).
  A leaver the cancel refunds — one who left after the cut-off, whose seat was still paid — is told
  in a leaver's words and never promised a new game ([§13](#13-leaving-a-game), Q108).
- **The owed card is the closest game to the lost one** (Q123): first **the same club, day and
  hour**, on a court of the other kind or at a new price; then, **for a player group only, another
  club at the same day and hour**, nearest first; then **the closest hour in time**, the home club
  first. An official group stays at its home club unless its courts are full
  ([§4.3](#43-courts)). The rule that never dealt the same players that club and hour again is gone
  *(a call)*: it was written for a club that refused a game. The owed card is an ordinary card: its
  players must all be free for its hour and fit each other, and each swipes it. It is first in
  their decks ([§8.2](#82-the-order)). A game no hour is found for stays owed until its old hour
  passes.
- After the cut-off, the card fees on the payments a call-off refunds are not returned by Stripe;
  as the seller, **the club bears them** (Q44). The cancel dialog says which: before the cut-off
  *every hold is let go and nobody pays a fee*; after it *everyone is refunded in full; the card
  fees are not returned*.
- Not possible once the game has started ◇.
- Until Q121, an *Instant* club that sold the hour at its desk too cancelled here with *double
  booking*; a club that sells a handed-over hour by mistake still does.
- Raketa keeps count of a club's cancellations; frequent cancellations are a quality matter
  between Raketa and the club, not something players are shown ◇.

### 16.10 Check in

**Removed on 2026-10-11** (Q116). Clubs that switched on *We check players in* could scan a
player's QR code, or type its short code, on a **Check in** page; a checked-in player could never be
reported as a no-show. It solved a problem with no evidence that it was real, it only ever said that
somebody came, and it put a queue in front of the desk at every club that used it. The page, its
scanner and typed-code form, the switch, the Bookings *Check in* button and its *checked in ✓* mark
are gone. Players walk straight to the court; whether somebody came is caught there
([§15.1](#151-attendance-at-the-court)), and **money never depended on it** — the club is paid
whether people come or not.

### 16.11 Money

- **The club is the seller.** Its name is on the players' receipts and bank statements.
- **Collected:** each booking's shares **once taken** — at the club's cut-off, or at once for a
  game booked after it (Q113). A held share is not collected yet; Bookings shows it as *held*.
- **Holds are let go, never refunded** — a leaver before the cut-off, a game short at the
  cut-off, a club's cancel before it: nothing was taken, so nothing comes back and no fee arises.
- **Refunds happen automatically** — a leaver whose seat was taken after the cut-off (the share
  less the fee kept on their payment), a club's cancel after the cut-off (in full), and the
  fallback of [§12.2](#122-when-a-game-fills) (in full). The club never refunds anybody by hand ◇.
- **Fees:** Stripe's real card fee on each share taken, paid by the club as at its own terminal,
  shown once Stripe reports it — or *not yet known* for a club on its own negotiated Stripe
  pricing, whose fee arrives later. **No estimate is ever shown** (Q113). A hold let go costs
  nothing. Fees on refunded payments are not returned; on a late leaver's refund the fee kept is
  the leaver's, so the club neither earns nor loses on it. *(A call made without a ruling, Q113:
  the ruling named the players' screens; the club's figures drop the estimate too.)*
- **Payouts:** after the game is played, to the club's IBAN, as normal Stripe payouts. A hold let
  go counts as settled. Refunds before the start are paid from that money, which is why it waits
  (open item O2).
- **The Money page** ◇: per booking — collected, refunded, card fee, net; the list of payouts; a
  link to the club's own Stripe dashboard for the detail.
- **Disputes** (a player's bank reverses a payment): handled through Stripe on the club's account,
  where the dispute is raised; the club can answer with the booking's evidence (the booking and the
  terms the player accepted, which Stripe's list for a *not received* dispute names; there is no
  check-in since Q116).
  Stripe covers a negative balance under Raketa's setup ◇.
- **Receipts and invoices for the club's own accounting** (Polish fiscal-receipt and invoicing
  rules for online sales) are the club's, as the seller — open item O5.

### 16.12 What the club is told

On the website, and by **email** where marked ◇:

| Event | Email |
| --- | --- |
| A new booking | a daily summary |
| A booking lost a player (Seat open) | no |
| A game was called off at the cut-off — the hour is free again | yes, at once |
| A payout was sent | yes |
| Stripe needs something from you (account details, a dispute) | yes, at once |

The website's badges on Bookings and Overview counted requests waiting for an answer, and the desk
was emailed *A booking is waiting for your answer*, *… said no* / *… didn't answer in time*, and *A
game didn't go ahead* after an Accept that waited on a payment (Q112, Q113). All of them went with
*On request* (Q121); the cut-off email and the daily summary stay.

### 16.13 Official groups and administrators

- The **Groups** page's *Games* figure now counts the games booked in each official group.
- **Offer our groups other clubs' courts when ours are full** (off · 10 km): when it is on, a set of
  players in the club's official groups can be offered another Raketa club's court, but only when
  the club has **no court at any hour those players share in the next 14 days** ([§4.3](#43-courts)).
  The club's own courts always win.
- **Administrators** run the official groups in the player app. They never see bookings, money or
  court settings; they play in games like any member.

### 16.14 Who signs in, and what the club sees about players

- **One login per club**, as today ◇. Separate staff logins (desk staff, managers) come later; until
  then the desk uses the club's login.
- **About players** ◇, the club sees only what running the court needs: each player's **name**, and whether
  their share is **held** or **taken**. No email, no phone, no level, no record, no attendance and no
  score (Q115), no access to the game's chat. The club cannot message players; everything players need to know comes
  from Raketa.

### 16.15 Pausing or leaving Raketa

- **Pause Raketa bookings** ◇: no new cards are built on the club's courts. Games already booked are
  played as booked; games still filling keep their cards until their book-by and can still book.
- **Leaving Raketa** ◇ is a pause plus disconnecting payments once every booked game has been played
  and every payout sent. Disconnecting payments earlier is refused while bookings remain.

### 16.16 The club's edge cases

| Situation | What happens |
| --- | --- |
| The desk sold an hour it had handed to Raketa, and Raketa had booked it | The club cancels with *double booking*. A free court of the same club, the same kind or indoor for an outdoor game, takes the game, and nothing changes but the court; otherwise every hold is let go before the cut-off, a full refund after it; nobody's record; the players get an owed card first ([§16.9](#169-cancelling-a-booking)). |
| The club closes an hour that has cards on it but no booking | The cards move to another free court at that hour or disappear; nobody was charged. |
| A court breaks on the day | **Cancel** with *repair*: another free court of the same kind, or an indoor one for an outdoor game, takes the game, and the players are told *Game moved*. With none, the game is called off and its players get an owed card first. **Move** does the same by hand. |
| It rains on an outdoor game | **Cancel** with *weather*: only a free indoor court takes it; with none, the game is called off (Q122). |
| The club closes the whole hour (an event, a power cut) | **Cancel the game anyway**: the game is called off even when a court was free (Q122). |
| The club changes a price after cards were dealt | The dealt cards and booked games keep their price. |
| A player leaves after the cut-off and nobody replaces them | The game goes ahead short; every share was taken at the cut-off, so the club is paid in full. |
| A game is still short at the cut-off | Called off; every hold is let go, so nobody paid and no fee arises; the hour is free again for the club. |
| A player's bank disputes a payment | Handled on the club's Stripe account; the booking and the accepted terms are the evidence (no check-in since Q116). |
| The club's Stripe account needs attention | New cards stop until it is fixed; booked games are unaffected. |
| The club wants to stop | Pause, then disconnect once everything booked has been played and paid out. |

Until Q121 this table also held *The club forgets to answer a request* (it expired: nobody paid,
*Called off · no answer*, a new card first) and *A player's card is refused when the club accepts*
(*Accepted · waiting for one player's payment until …*, the court held for at most 30 minutes).
Both went with *On request*, and its *Instant* row became the handed-over hour sold by mistake.

### 16.17 The pages at a glance

The club website keeps its **top bar** (Q90):

```
Top bar:  Overview · Bookings · Courts & prices · Money · Groups · Administrators   [Club name ▾]
                                                                                    ├ Details
                                                                                    └ Raketa settings
Overview ........ setup checklist until live · then "you're live" and today's Bookings
Bookings ........ by day · Move · Cancel (moves the game when a court can take it)
Courts & prices . courts · weekly hours · exceptions · price bands
Money ........... per booking · payouts · link to the Stripe dashboard
Raketa settings . release · cut-off · other clubs' courts · pause
Groups .......... official groups · Games figure · other clubs' courts
Administrators .. unchanged
Details ......... unchanged
```

## 17. Player settings and notifications

### 17.1 Settings (You)

The You tab gains an **Account** group of three rows (screens in [the-screens.md](the-screens.md)):

- **Games & money** — **games per week** (1–7, default 2) and **most I'll pay per game** (Off ·
  35 · 45 · 60 zł; off by default). Saves as you tap. A bound line under both reads *"Your bound:
  at most 2 games · up to 70 zł a week"* (the money half only when a ceiling is set), and the
  row's subtitle repeats it. Settings apply across sports.
- **Payments** — the setup ([§12.5](#125-saving-a-payment-method-and-the-terms)) until a method is
  saved; then the method card, **LIVE YESES · n** (every yes that hasn't filled, across groups)
  and **RECEIPTS** (shares taken, holds let go and refunds, the club named as the seller).
- **Notifications** — the always-on list and the three choices ([§17.2](#172-notifications)).

**Your week** stays in *Finding players* ([§4.2](#42-weekly-hours-availability)).

### 17.2 Notifications

Delivered by **push** (built with this feature, through Expo's push service: free on Android;
on iPhone it needs the Apple Developer membership, which publishing the app needs anyway — and
switched on end to end on both since Q120, once a human has set up the Expo project, Firebase and
the Apple Developer Program at 99 USD a year), by an
**in-app banner** when the app is open, and in a **recent notices** list behind the bell on Home.
Every notice about money is **also emailed** — the standard for bookings and payments (Q85, Q94):
*It's a game! · 40 zł held* (the booking confirmation, saying when the share is taken; *you paid*
after the cut-off), *Game called off · nothing was taken* (or *with the refund*, after a club's
cancel after the cut-off), *You've been refunded*, *Fix your card by 14:40 to keep your seat* and
*Confirm your payment by 14:40 to keep your seat*; a leaver's own *You left the game* is emailed
too — *nothing was taken* before the cut-off, the exact refund if their seat is taken after it
([§13](#13-leaving-a-game), Q113). Until Q121 so were **the club's no and its silence** (Q105),
though no money moved; they went with *On request*.

**The take at the cut-off is quiet** (Q113): *Your 40 zł for Thu 19:00 was taken* is a row in the
recent notices, counted on the bell like any notice but never pushed or bannered, and a receipt —
emailed, and kept in You › Payments. It isn't a row of the settings below, which list the notices
that are pushed. *(A call made without a ruling, Q113: the booking already said when the money
would be taken, so its moment needs no push. The row's words were written in while recording it.)*

**The bell shows a number** (Q101): the notices given since the player last opened the list, *99+*
above 99. The server keeps it, so it is the same on every phone. Opening the list clears it, and
the rows that came since the last visit stand out on that visit. Nothing is marked read row by
row, and there is no *mark all*. The list stays the newest 30. The app icon's number waits for
push.

**Banners** (Q101, Q102):

- **Nothing comes down at launch.** What was told while Raketa was closed is in the number. Coming
  back from the background shows a banner for the newest notice only, and the number counts the
  rest.
- **Your own act is never announced back to you.** The player whose yes filled a game sees *It's a
  game!* and gets no banner for it, and the bell doesn't count it; the row is still in their list.
  The same holds for a payment confirmed in the app that completes a game. Their only banner is
  the one about money held or taken by someone else's act, such as *Your Tue 19:00 is booked ·
  40 zł held* when another player's payment comes in (until Q121, also *Kazimierz Padel confirmed
  your game · 25 zł held*).
- **Home is read again whenever a notice arrives**, so the game is there when the notice is tapped.

**Every ending and fall-back of a full game is told to everyone still in it** (Q104). A game that
ends reads *called off*, with why. A game that falls back to filling reads *"Your Fri 19:00 at
Kazimierz Padel is filling again"* / *"A seat opened — nobody paid."*, and never says whose card
failed, whose week filled or who no longer fits; a named leaver keeps *"Oscar Bertran left your
game — it's filling again."* ([§13](#13-leaving-a-game)). If a paused yes later comes back and
refills the game, all four are told as at any fill. A card that never filled still disappears
untold ([§5.4](#54-the-only-deadline-the-courts-book-by)).

**The game's own notices** (Q120). Five notices come from the game itself, each because it decides
somebody's record or result, so each is **always on** *(a call)*. Each opens **the game's result
screen**, and a **For fun** game is told none of them:

- ***Isn't here yet*** — to the absent player: *"Ivan is at Ogrody 33 and you're not there yet —
  tap I'm here when you arrive"* ([§15.1](#151-attendance-at-the-court));
- ***They're at the club*** — to whoever tapped, when the absent player arrives;
- ***How did it go?*** — to every player of a Competitive booked game, when its hour ends
  ([§15.2](#152-results-and-sportsmanship));
- ***Is that right?*** — to the other side, when a score goes up;
- ***Were they there?*** — to the others on the court, when an absent player claims *I was there*.

| Notification | Setting |
| --- | --- |
| **It's a game! · 30 zł held** (*you paid 30 zł* after the cut-off) — or, after one payment was missing, *Your Tue 19:00 is booked · 40 zł held* | always on |
| **Waiting for one payment** — *It's a game! · waiting for one payment until 14:40* ([§12.2](#122-when-a-game-fills), Q110) | always on · not emailed |
| **Fix your card by 14:40 to keep your seat** — before the cut-off; and *Your time to fix your card ran out*, when it did (Q113) | always on |
| **Confirm your payment by 14:40 to keep your seat** — after the cut-off; and *Your time to pay ran out*, when it did | always on |
| **Game called off** (with the reason, and *nothing was taken*, the refund, or *nobody paid*); after a club's cancel, also *We'll look for another game for you first*, as the email says, except to a leaver it refunds (Q123, *a call*) | always on · emailed with *nothing was taken* or a refund |
| **Game moved** — after a move by cancel, *Bonarka Arena moved your game to Court 3 · Thu 19:00* / *Court 2 can't be played · Padel · indoor · nothing else changes*, the reason worded per the cancel's reason (*weather*, *repair*, *double booking*, *other*); after the club's own Move, the same title with *Padel · indoor · nothing else changes* ([§16.9](#169-cancelling-a-booking), Q122). Opens the booked game | always on · not emailed (*a call*) |
| **Someone left your game**, or **it's filling again** | always on · not emailed |
| **You've been refunded** (you left after the cut-off and your seat was taken: the exact sum and the fee kept on your payment) | always on |
| **Your new game** — *Your new game · Sat 10:00 at Bonarka Arena* / *The same players · 40 zł a share — say yes to book it.*, to the players an owed card is dealt to after a club's cancel called their game off (Q107, Q123); for a card at the same club and hour, the body names the kind: *The same players · outdoor · 40 zł a share — say yes to book it*. It opens the deck on the card, and goes only to a player whose deck shows it | always on · not emailed |
| **A game you left** — called off by your empty seat, or cancelled by the club with your refund ([§13](#13-leaving-a-game), Q108) | always on · emailed only for the club's cancel |
| **Your post didn't fill** | always on |
| **Isn't here yet** · **They're at the club** · **How did it go?** · **Is that right?** · **Were they there?** — the game's own notices, above (Q120) | always on · not emailed (written in: none is about money or the club's answer) · never for For fun |
| **You complete it** — a card needs only you | on by default · at most 1 a day, bundled |
| **Challenges for you** — a member's post names you | on by default · at most 3 a day, bundled |
| **Fill in alerts** — a booked game you fit needs one more | off by default · at most 3 a day |

No notification is ever sent for a single swipe.

> **Amended 2026-10-12** (Q121–Q123, [ADR-0196](../../adr/0196-only-raketa-until-raketa-is-the-clubs-booking-software-and-a-clubs-cancel-moves-the-game.md)).
> Three kinds went with *On request*: *It's a game! · Kazimierz Padel answers by 21:15* (Q103), *The
> club confirmed / said no / didn't answer in time* (Q105), and the *at a club that confirms* words of
> *Waiting for one payment* (Q110). *Your new game* now follows only a club's cancel. *Game moved*
> and the cancel notice's new line are new.

---

## 18. Numbers in one place

| What | Value |
| --- | --- |
| Horizon | 14 days |
| Game length | 1 hour, every sport |
| Seats | 4 padel and badminton · 2 tennis and squash |
| Versions per game | at most 3 · each person one |
| Next best fits after a no | up to 3 per open seat |
| When a picked game widens | at half its seats In |
| Live yeses | no cap (Q97) |
| Games per week | 1–7, default 2, Monday to Sunday |
| Live posts | 2 |
| Undo | 10 seconds, on every action that moves money: the yes that fills a game and every rescue join |
| A card hold lasts (charged without the player present) | Visa 4 days 18 hours · Mastercard 7 days ([Appendix A](#appendix-a--payments-with-stripe-notes-for-development)) |
| A hold reaches the cut-off | when its last moment is at least **6 hours** after it (a domain constant; a call, Q113) |
| Holding time, when the fill's hold doesn't reach | **4 days** before the cut-off (a domain constant; a call, Q113) |
| Time to fix the card | 30 minutes, before the cut-off; never past the cut-off or the book-by |
| Time to pay | 30 minutes, after the cut-off; never past the last moment to book (the book-by) |
| A refused rescuer keeps the seat | 30 minutes (to fix the card, or to pay), never past the game's start (a call, Q113) |
| Recent notices | the newest 30 · the bell's number shows *99+* above 99 |
| Book-by | the release time: the game's start − the release lead, so never later than a day before the game (Q121, a call) |
| Club defaults | release lead 3 days (1–13) · cut-off 24 h · other clubs 10 km. The minimum notice (2 h) and the time to confirm (30 min) went with Q121 |
| A court that absorbs a club's cancel | the same club, sport, day, hour and price; the same kind, or indoor for an outdoor game; indoor only for *weather*; the same kind first, then indoor, in the club's court order (Q122) |
| An owed card's order | the same club, day and hour → for a player group, another club at the same day and hour, nearest first → the closest hour, home club first; first in each owed player's deck, soonest first (Q123) |
| Player group reach | home club + 10 km |
| Attendance tap window | from the hour's start to 30 minutes after it — the first half of a one-hour game (Q115) |
| On time · Came late · Didn't come | an arrival within 10 minutes of the start · 10 to 30 minutes after it · none by 30 minutes after it |
| Late claim (*I was there*) and its confirmation | within 24 hours of the tap window closing |
| At the club | within **300 m** of the club's map point, the fix's own accuracy allowed up to 200 m (a call, Q115) |
| Entry window (a score) | from the hour's start, never before, until 24 hours after the hour ends; corrections are refused once it closes (Q119) |
| Answer window | 24 hours from the score or its last correction |
| An acceptance settles | **at once** (the six-hour wait retired, Q119) |
| Levels move | within a minute of a result settling (a call, Q119) |
| Player reliability | from **100**: −25 *Didn't come* · −10 *Came late* · −15 a late leave with the seat left empty · −10 an early leave (or an unfixed card) when the empty seat calls the game off · +5 per game played through, never above 100 (Q117) |
| Its window | each failure drops out after **6 months**, rolling |
| Bands | Very high 90–100 · High 75–89 · Medium 50–74 · Low below 50 |
| New | fewer than **3** games played through, ever |
| Results left in dispute | counted over the same 6 months (a call); never points |
| Card fee | Stripe's real fee on each share taken, paid by the club; a leaver refunded after the cut-off bears the fee kept on their own payment. Known only once the share is taken, by card kind ([Appendix A](#appendix-a--payments-with-stripe-notes-for-development)), and **never estimated or printed in advance** (Q113) |

---

## 19. Edge cases

| Situation | What happens |
| --- | --- |
| Two players take the last seat at the same moment | The first wins; the second is told at once that it just filled. |
| You swipe a version a moment after the game filled | Told it just filled; the card leaves. |
| Your named seat was taken by a best fit before you swiped | Your card leaves your deck. Nothing on your record. |
| The last court at that club and hour is booked by another card | Your card moves to another court number there if one is free; otherwise it disappears and the people who were In get a new card first. |
| The club withdraws a court hour that had cards on it | The same as above. |
| You are In on two games at the same hour | The first to fill books; your other yes is withdrawn. |
| Your games per week are booked | Your other yeses that week pause; they come back if a game is called off. |
| You have no payment method yet | Your first yes opens the payment screen; the yes lands when it is done. |
| You have no intent for the sport | Asked once, inline, the first time you open Games for it. |
| Nobody in the group fits you | An empty deck with **Post a game**. |
| A card is refused when the game fills | Nobody pays; your seat is yours alone for 30 minutes — time to fix the card before the cut-off, never past it or the book-by; time to pay after it, never past the book-by — and the others' holds stay; fix it or pay in time and the game books. Otherwise your seat is offered to others, you owe nothing, and you can still take it back while it is free ([§12.2](#122-when-a-game-fills)). |
| A game fills far ahead of its cut-off | A seat whose hold wouldn't last until the cut-off is a card check at the fill, and its share is held four days before the cut-off; everyone is free to leave until the cut-off ([§12.2](#122-when-a-game-fills)). |
| A card is refused at the holding time | The game stays booked; the player has 30 minutes to fix the card. Not fixed, their seat opens as a rescue, they owe nothing, and it counts as leaving before the cut-off on their record ([§12.2](#122-when-a-game-fills), a call). |
| A holding still wouldn't last until the cut-off | Never expected: the share is taken at its last safe moment, and a leave before the cut-off after that is refunded in full ([§12.2](#122-when-a-game-fills), a call). |
| A rescuer's card is refused | The seat is theirs alone for 30 minutes — time to fix the card before the cut-off, time to pay after it — never past the game's start; then it is offered again ([§10.1](#101-seats-to-fill--the-rescue-board), a call). |
| Your card's brand changes | You are asked to accept the terms again; until then, a game filling fails your payment as above. |
| The poster withdraws | The game carries on if others are In; the ribbon drops the name. |
| A post or a picked card reaches book-by unfilled | It disappears; nobody paid; a poster is told. |
| A doubles loses three players before the cut-off | All three seats stay rescues until the cut-off; then the cut-off rule applies. |
| A game is still short at the cut-off | Called off; every hold is let go, so nobody pays anything; the leavers had nothing taken. |
| Someone leaves after the cut-off and nobody takes the seat | The game goes ahead short; it ends **Uncounted · a seat was empty**. |
| A last-minute game | Its shares are taken the moment it fills; no free cancellation from the start; the card said so. |
| A player leaves, or a yes is taken back, while the game waits for one payment | The game goes back to filling and stays on the others' Home as *Seat open*. They are told it is filling again: a leaver by name, anything else never why. |
| The desk sold a handed-over hour by mistake | The club cancels with *double booking*, and the cancel is handled as below. |
| The club cancels a booked game | A free court of the same club with the same sport, day, hour and price, of the same kind or indoor for an outdoor game (indoor only for *weather*), takes it: the game moves, every hold or payment stays, and everyone is told *Game moved* ([§16.9](#169-cancelling-a-booking), Q122). Otherwise, or with *Cancel the game anyway*, it is called off: before the cut-off every hold is let go and nobody pays a fee, after it a full refund; nobody's record; an owed card first. A leaver it refunds is told in a leaver's words, with no new card. |
| The club moves your game by hand | Only to a free court of the same kind, or an indoor one for an outdoor game; you're told *Game moved* (Q122). |
| You're owed a card | It is first in your group's deck whenever you open it, until you answer it or it's gone; two owed cards soonest first; no mark (Q123). |
| A game less than a day away | No fresh card can make it: every book-by is at least a day before its game, and by default three (Q121, a call). Only a rescue of a booked game's seat fills that late. |
| The club changes its prices | Only new cards carry the new price. |
| You leave a group | Your yeses there are withdrawn. Your booked games stay. |
| Somebody you blocked | Never on a card with you. Your yeses where they are In are taken back, until the game is booked. Your booked games stay. |
| Someone isn't there at the start | In the first half of the game, anyone at the club taps *isn't here yet*; they are pushed at once. Arriving within 10 minutes records nothing; 10 to 30 minutes is *Came late* (−10) and the game plays on; no arrival by 30 minutes is *Didn't come* (−25), and the game takes no score ([§15.1](#151-attendance-at-the-court)). |
| A tap from home, from 2 km away, after 30 minutes, or about yourself | Refused, in a plain sentence. |
| The person tapped was on another court | Their own *I'm here* from the club lifts it at once; the tap cost its maker nothing. |
| A phone died | *I was there* within 24 hours, confirmed by anyone else on the court, turns *Didn't come* into *Came late*. |
| Nobody records a full game | It reads *Played · no score* for everyone: 5 points each, no Level moved ([§15.3](#153-a-game-nobody-recorded-and-a-game-somebody-didnt-come-to)). |
| A score put up before the game | Refused. |
| *That's right*, then a different score from the other side | The first agreement settled it; the later score is refused. |
| Nobody answers a score | It settles 24 hours after it, and Levels move then; the silence costs nothing. |
| Two scores, the same winner | The game counts with the closer one. |
| Two scores, different winners | Disputed: no Level moves, and each of the two who put a score up gets a *Results left in dispute* line, never points. |
| A For fun game | Nobody is asked anything; it reads *Played*. |
| Your reliability filter hides someone | Never on a card, a rescue or a post with you; a yes you gave before stands; a booked game never changes. A *New* player always passes ([§15.4](#154-the-record)). |

Until Q121 this table also held *A card is refused when an On request club accepts* (the club's yes
and its court kept while the card was fixed), *An On request club refuses or does not answer*
(nobody paid; *said no* or *didn't answer in time*; a new card first) and *An Instant club
double-sold the court*. All three went with *On request* and *Instant*: no club confirms a game,
and a handed-over hour sold by mistake is cancelled as above.

---

## 20. Out of scope

- The UI design, which is [the-screens.md](the-screens.md)'s.
- Relaxing the level filter beyond what the engine allows.
- Any Raketa revenue: no fee, no subscription. (Playtomic charges Polish players a 20 %
  service fee capped at 1.24–3.99 zł per seat; Raketa's absence of one is an advantage.)
- The Friends tab.
- **"Classic play"**: the Players deck, the Chats tab, challenges with the where/day/hour plan,
  and Find a game. They stayed behind one flag, off by default, until they were **removed on
  2026-10-06** with the flag itself ([#569](https://github.com/Raketa02/Raketa/issues/569)).
- The city-level pool (Explore). These mechanics are written for "a pool"; the city is a later
  pool, and distance matters again there.
- **Raketa as the club's booking software**: the desk calendar, direct court bookings, season
  bookings, blocks, prices per court, customers, coaches, leagues, benefit cards, fiscal printing,
  staff roles, reports, importing from tenis4U, Playmore and kluby.org, and the business model. It
  is the direction (Q121); its own grilling decides its shape.
- **A link to a club's own booking system**, by deal or by reading its site. Decided against for
  now (Q121): no Kraków system offers one, and tenis4U's terms forbid reading it.
- **Indoor or outdoor as a player preference or filter.** Players see the kind; they don't choose
  by it (Q122).

---

## 21. Open items

To settle with Stripe (and a lawyer) before building payments:

- **O1 — BLIK with the club as the seller.** Because the club is the seller, each payment is
  made on the club's own Stripe account, with the player's card copied there for that payment.
  Stripe copies **cards only** — not BLIK. Ask Stripe: can a saved BLIK be used for a club's
  payments (for example, one approval in the bank app per club), and is saved BLIK available to
  Raketa at all? If neither, BLIK waits. Either way, **BLIK can't be held** (no manual capture),
  so it can't wait for the club's cut-off as a card does: when BLIK launches, its own rule for
  leaving and the cut-off is decided with it (Q113).
- **O2 — Keeping the club's money until after the game.** Refunds before the start come out of
  the club's Stripe balance. Confirm how Raketa can keep the club's payouts until after the game
  when the club is the seller.
- **O3 — The terms' wording** ([§12.5](#125-saving-a-payment-method-and-the-terms)), naming the club as
  the one charging, reviewed by a lawyer. Before the cut-off nothing is taken, so only the hold's
  disclosure is reviewed there. **The clause after the cut-off waits for the lawyer** (Q113): a
  late leaver whose seat is taken gets the share back less exactly what was kept on their own
  payment. If the lawyer finds that deduction a charge for using a personal card issued in the EU
  (art. 37a ust. 3 UUP), the fallback is everything back on those cards. **Two more questions
  since Q124:** whether a swipe stamped *PAY · 40 zł* is an order under art. 17 (if not, a
  money-moving yes opens a confirm screen with a *Pay 40 zł* button), and whether a vote stamped
  *I'M IN · 40 zł* binds the voter. The words count only in Polish, so the app's translation lands
  before a real club takes a player's money.
- **O4 — Apple Pay** for one-off charges without the player present: test before launch.
- **O5 — The club's receipts and invoices.** The club is the seller, so the Polish rules on fiscal
  receipts and invoices for online sales apply to the club. Confirm with a lawyer or accountant what
  a club needs (and whether Raketa should give it an export per booking) before the first club goes
  live ([§16.11](#1611-money)).
- **O6 — Apple Developer membership** (a human step): iPhone push needs it, as does publishing the
  app. Until it exists, iPhones get the in-app banner, the recent-notices list and the emails.
- **O7 — A Stripe test account** (a human step): its test keys go into `.env` by a person, never by
  an agent. Until then, everything runs on the fake payments adapter. Three questions Q113 left
  open are checked with it before launch: whether a manual capture's response carries the balance
  transaction (the fee) at once; whether the fee on a partial capture falls on the captured amount
  only; and whether Stripe objects to a second hold placed days after a card check was let go.

---

## 22. What this replaces

### 22.1 From the PDFs, removed on purpose

- A hold on the player's money at every swipe; the 5-second background queue built around it;
  the three-shares ceiling. (Holds came back with Q113, but only from the moment a game fills,
  never on a swipe.)
- The two clocks (a 2-hour answer window and a 4-hour court reservation restarted by every
  acceptance up to 12 hours) and the third clock before the first yes.
- The court *spoken for* by a swipe.
- The "matched game without a court" that waited for everybody to confirm a new court.
- The "already proposing this slot" collision card, the coach's court row, the "call with
  options", the "overlap only" and "stretch" cards.
- The friends-first hour on open seats (there is no friends feature).
- Silence on a challenge counting against the record.

### 22.2 In the repository — recorded by ADR-0189

[ADR-0189](../../adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md) records these,
claim by claim, and each record carries a note pointing at it:

- **ADR-0145** — "the hour is the agreement, and there will never be a booking".
- **ADR-0182 §8** — "a club isn't a court".
- **ADR-0183 §13** — a group "doesn't pick games, post games, offer or book courts, or handle
  money. It has no chat"; the disabled *Post a game*. **§11**'s *Games* figure now counts the
  games booked in each official group.
- **ADR-0179 §9** — the You tab gains an *Account* group.
- **ADR-0169** — the deck lives on Players (removed with Classic play; its swipe stage is the
  Games deck's).
- **ADR-0144, ADR-0164** — the plan (where · day · hour) belonging to a challenge.
- **ADR-0150** — "the fill" completing a challenge from Chats (the word *Fill in* now has one
  meaning).
- **ADR-0151, ADR-0100** — challenge answer windows.
- **ADR-0167** — the yes screen, reused with new words (*It's a game!*).
- **ADR-0175** — leaving only from the Chats row; the game screen gets **Leave the game** back.
- **ADR-0120, ADR-0102** — the availability term and grid, now hours per day.
- The glossary (`CONTEXT.md`): *Challenge, Game* ("nothing about when, where, money"), *Plan,
  Where, the Hour* ("nothing on this platform will ever hold a booking"), *Chats, Conversation,
  Departure, Call off*; new entries, in its **Part 2 — Decided, not yet built**: *Pool, Court,
  Court hour, Share, Book-by, Cut-off, Proposal, Post, Version, In, Booking, Rescue, Fill in, Seat
  charge, Weekly hours, Home, Classic play…*
- `docs/specs/the-loop/the-loop-screens.md` (deleted 2026-10-06, #569) — the states it refused
  by name (*Booked, Being booked, Cancelled…*) and the Now states *Planning, Game on, Needs a
  player*.

---

## Appendix A — Payments with Stripe: notes for development

Researched from Stripe's official documentation on 2026-09-28; the holds, their windows, the fees
and refunds were read again on 2026-10-10 for Q113. Every line has its source.

**Objects**

- **Players** are Stripe `Customer`s (v1) on Raketa's platform account — the React Native
  PaymentSheet accepts only those.
  [accept-payment (setup)](https://docs.stripe.com/payments/mobile/accept-payment?platform=react-native&type=setup)
- **Saving the method:** PaymentSheet in **setup mode**, one `SetupIntent` with
  `usage=off_session`; turn on Radar for saved payment methods.
  [save-and-reuse](https://docs.stripe.com/payments/save-and-reuse?payment-ui=elements),
  [setup-intents](https://docs.stripe.com/payments/setup-intents)
- **Clubs** are connected accounts (Accounts v2, `merchant` configuration;
  Standard/Express/Custom are deprecated for new platforms) with
  `fees_collector=stripe` and `losses_collector=stripe`: the club pays Stripe's fees, Stripe
  covers negative balances, Raketa pays no Connect fees.
  [accounts-v2](https://docs.stripe.com/connect/accounts-v2),
  [configuration](https://docs.stripe.com/connect/accounts-v2/connected-account-configuration),
  [integration-recommendations](https://docs.stripe.com/connect/integration-recommendations)
- **Direct charges:** for each seat, clone the player's card PaymentMethod to the club's account
  and create the PaymentIntent there. Only `card` (and `us_bank_account`) can be cloned; each
  clone is single-use; sharing carries the customer's permission.
  [direct-charges-multiple-accounts](https://docs.stripe.com/connect/direct-charges-multiple-accounts),
  [SCA for platforms](https://docs.stripe.com/strong-customer-authentication/connect-platforms)
- The club is **merchant of record** and must be named as the seller in the payment flow.
  [merchant-of-record](https://docs.stripe.com/connect/merchant-of-record)
- Polish club onboarding: full service agreement, company data with REGON, representative and
  owners, a Polish IBAN.
  [required-verification-information](https://docs.stripe.com/connect/required-verification-information)

**The fill (all or nothing)**

- For each seat: `capture_method=manual`, `off_session=true`, `confirm=true`, the saved method,
  an idempotency key. When every seat is `requires_capture`, **keep the holds** and capture them
  at the club's cut-off (Q113) — at once only when the game is booked after its cut-off; if any
  fails, cancel the others — cancelling an uncaptured payment costs nothing: *"You can cancel a
  payment before it's completed at no cost."*
  [place-a-hold](https://docs.stripe.com/payments/place-a-hold-on-a-payment-method),
  [refunds](https://docs.stripe.com/refunds)
- A seat whose hold doesn't reach the cut-off (below) is cancelled at once — the **card check** —
  and authorised again at its holding time, four days before the cut-off, as a second, separate
  off-session payment on the saved card.
- Off-session payments can still come back `authentication_required`; recovery is the player
  confirming **the same** PaymentIntent in the app (`confirmPayment`); for other declines, a new
  method on the same PaymentIntent. At most 8 retries.
  [save-and-reuse (recovery)](https://docs.stripe.com/payments/save-and-reuse-cards-only?platform=react-native),
  [declines](https://docs.stripe.com/declines/card)
- Merchant-initiated payments carry no 3-D Secure liability shift (Stripe covers losses under
  `losses_collector=stripe`).
  [SCA exemptions](https://docs.stripe.com/payments/3d-secure/strong-customer-authentication-exemptions)
- A card whose brand changed cannot be charged off-session until the player agrees again
  (`payment_method.automatically_updated`).
  [cits-and-mits](https://docs.stripe.com/payments/cits-and-mits)

**Holds (Q113)**

- **How long a hold lasts.** Online card authorisation windows, merchant-initiated against
  customer-initiated: Visa *"5 days\*"* against *"7 days"*, *"\* The exact authorization window is
  4 days and 18 hours"*; Mastercard, Amex and Discover 7 days either way. Raketa's charges are
  merchant-initiated, so a Visa hold lasts 4 days 18 hours and a Mastercard 7 days.
  [place-a-hold](https://docs.stripe.com/payments/place-a-hold-on-a-payment-method)
- **A hold's last moment** is the authorised charge's `payment_method_details.card.capture_before`
  — *"the most reliable and accurate way to determine your charge's authorization window"* —
  read on the club's account, where the direct charge lives.
  [cits-and-mits](https://docs.stripe.com/payments/cits-and-mits)
- **A lapsed hold is gone:** on expiry *"the funds are released and the payment status changes to
  `canceled`"*. Stripe's own delayed capture runs *"about 6 hours before the expiration time"*,
  which is where the reach margin comes from: a hold reaches the cut-off when its last moment is at
  least 6 hours after it.
  [place-a-hold](https://docs.stripe.com/payments/place-a-hold-on-a-payment-method)
- **Letting a hold go costs nothing**, and Stripe advises it for leaves close to the payment:
  *"Manual authorization and capture lets you better control costs by canceling payments before
  they're captured, or by reducing your captured amount rather than processing a refund."*
  [refunds, cost optimization](https://docs.stripe.com/refunds#cost-optimization)
- **Extended authorisation is not used.** It is offered on IC+ pricing (blended pricing must ask
  Stripe), costs 0,08 % more on Visa, and *"The extended window only applies to Customer-Initiated
  Transactions"*. Incremental authorisations *"don't extend the validity period"*.
  [extended-authorization](https://docs.stripe.com/payments/extended-authorization),
  [incremental-authorization](https://docs.stripe.com/payments/incremental-authorization)
- **Renewing a hold is undocumented.** Neither the hold page nor the CIT/MIT page mentions
  re-authorising after a hold lapses. The holding time therefore places a second, separate hold
  on the saved card, after the card check was cancelled, which uses only documented steps; whether
  Stripe objects to it is checked with the test account (O7).
  [cits-and-mits](https://docs.stripe.com/payments/cits-and-mits)
- **BLIK can't be held:** *"Manual capture support: No"*.
  [blik](https://docs.stripe.com/payments/blik)

**The fee, known only at capture (Q113)**

- *"A PaymentIntent must be captured and have a status of `succeeded` for the Stripe fees to be
  available"*; readiness is signalled by `charge.updated`. A direct charge's balance transaction
  is read on the club's account and *"includes a detailed fee breakdown"*.
  [expand use cases](https://docs.stripe.com/expand/use-cases),
  [direct-charges](https://docs.stripe.com/connect/direct-charges)
- A club on its own negotiated pricing gets no fee on the balance transaction: *"IC+ users can't
  retrieve payment fee information from the balance transaction"*, and under standalone fees it
  arrives *"typically within 36 hours"*. The port reports such a fee as **not yet known**, never
  a guess. [expand use cases](https://docs.stripe.com/expand/use-cases),
  [standalone-fees](https://docs.stripe.com/standalone-fees)
- **A card's price tier can't be known before the charge:** *"Stripe determines a card's
  classification based on information from card networks at the point of capture"*; no field of
  a saved card says business or personal. So no fee is printed before the share is taken.
  [standard and premium cards](https://support.stripe.com/questions/what-s-the-difference-between-standard-and-premium-cards),
  [PaymentMethod object](https://docs.stripe.com/api/payment_methods/object)

**Refunds and payouts**

- Refunds are free to issue, but the original processing fee is not returned: *"Stripe's
  processing fees from the original transaction aren't returned."* So **a refund is an exact
  amount** the caller computes — the share less the fee kept on that payment, or the whole share —
  never a flag asking Stripe to withhold a fee (Q113).
  [refunds](https://docs.stripe.com/refunds), [pricing FAQ](https://stripe.com/en-pl/pricing)
- A refund issued shortly after the charge may be a reversal, of which Stripe says it *"doesn't
  withhold any fees"*; whether the original fee then comes back is not stated. The refund amount
  is computed from the fee kept at capture either way.
  [refund and reversal](https://docs.stripe.com/refunds#refund-and-reversal)
- With direct charges, refunds come out of the club's balance and stay pending when it is empty
  — see open item O2. Default payouts in Poland: first after 7 days, then 3 business days.
  [connect charges](https://docs.stripe.com/connect/charges#refunds),
  [payouts](https://docs.stripe.com/payouts)

**Fees (Poland, standard)** — what Stripe keeps on a share once it is taken, which is never shown
as an estimate (Q113):

| Card | Fee | On a 40 zł share | Back to a late leaver whose seat is taken |
| --- | --- | --- | --- |
| A personal card from the EEA | 1,5 % + 1,00 zł | 1,60 zł | 38,40 zł |
| A business (premium) card | 1,9 % + 1,00 zł | 1,76 zł | 38,24 zł |
| A UK card | 2,5 % + 1,00 zł | 2,00 zł | 38,00 zł |
| A card from outside Europe | 3,25 % + 1,00 zł | 2,30 zł | 37,70 zł |

Each *"+ 2% if currency conversion is required"*. BLIK 1,6 % + 1,00 zł, dispute 90 zł, no fee for
cancelling an uncaptured payment. The fake payments adapter models the four card kinds with these
fees, and the hold windows above (ADR-0190, as amended).
[pricing](https://stripe.com/en-pl/pricing)

**Robustness**

- Idempotency keys may be forgotten after 24 h: Raketa's own records must prevent duplicates.
  [idempotent requests](https://docs.stripe.com/api/idempotent_requests)
- Webhooks: `setup_intent.succeeded/setup_failed`, `payment_intent.amount_capturable_updated`,
  `payment_intent.payment_failed`, `payment_intent.canceled`, `charge.captured`, `charge.updated`
  (the fee is ready),
  `charge.refunded`, `refund.*`, `charge.dispute.created`, `payment_method.automatically_updated`,
  account events. Direct-charge events arrive only on a **Connected accounts** endpoint; events
  can arrive twice and out of order.
  [event types](https://docs.stripe.com/api/events/types),
  [connect webhooks](https://docs.stripe.com/connect/webhooks)
- Rate limits: 100 requests/s overall, 25/s per endpoint; never mutate one PaymentIntent from two
  places at once.
  [rate-limits](https://docs.stripe.com/rate-limits)
- Card testers target card-saving: require sign-in and limit cards added per account.
  [card-testing](https://docs.stripe.com/disputes/prevention/card-testing)

**Payment methods**

- Cards, Google Pay, Apple Pay (card PaymentMethods): saveable and off-session. Apple Pay in
  React Native setup mode requires a recurring summary item, which does not describe Raketa's
  charges — open item O4.
  [apple-pay merchant tokens](https://docs.stripe.com/apple-pay/merchant-tokens)
- BLIK: no manual capture; saved ("reusable") BLIK is described on the BLIK page but marked
  private preview and contradicted by the support table; it cannot be cloned to a club — open
  item O1. [blik](https://docs.stripe.com/payments/blik),
  [blik set-up](https://docs.stripe.com/payments/blik/set-up-payment?payment-ui=direct-api)
- Przelewy24: not saveable, no manual capture.
  [p24](https://docs.stripe.com/payments/p24)

**Mobile:** `@stripe/stripe-react-native` needs a development build (not Expo Go) for Apple Pay
and Google Pay, the New Architecture, iOS dynamic frameworks and Android compile SDK 36+; direct
charges need the club's `stripeAccountId` when a player confirms a payment.
[stripe-react-native](https://github.com/stripe/stripe-react-native),
[direct charges (RN)](https://docs.stripe.com/connect/direct-charges?platform=react-native)

---

## Appendix B — How Playtomic does it

From Playtomic's player and club help centres and its Legal Conditions (articles updated
Aug–Sep 2026).

| | Playtomic (open matches) | Raketa |
| --- | --- | --- |
| When you pay | When you **join**, charged at once | Held when the game **fills**, taken at the club's cut-off (Q113) — nothing for games that never form |
| Court | Booked in stages (2 players > 12 h before, 3 > 4 h, 4 always) | Booked when the game fills |
| Not full | Cancelled about 1 h before; everyone refunded | Cards simply expire at book-by; nobody ever paid. A booked game short at its cut-off lets every hold go |
| Leaving | Free until 24 h before; then locked — only the club can swap | Free until the club's cut-off, nothing taken; after it, the seat is a rescue, and when it is taken you get your share back less the fee kept on your payment |
| A queue for freed seats | None (Polish users ask for one) | Rescues in Fill in, the deck and alerts |
| Poland | Cards, Apple Pay, Google Pay; no BLIK | Cards and wallets; BLIK when Stripe confirms |
| Player fee | 20 %, capped 1.24–3.99 zł per seat | None |
| No-shows | Reported by others within 7 days; charged the court as a debt. Arriving 10 minutes or more late is a no-show, and the others choose *Wait and Play* or *Declare No-Show* | Already paid; caught at the court in the first half of the game: on time within 10 minutes, *Came late* to 30, *Didn't come* after; no desk check-in (Q115, Q116) |
| A game nobody recorded | Ends *No score recorded* | *Played · no score*: played for everyone, no Level moved (Q114) |
| A score | One acceptance from the other team validates it at once; auto-confirmed after 24 h; a disagreement left open may be nullified | The same, and silence costs nothing; two scores naming the same winner count with the closer one, different winners end disputed (Q119) |
| Reliability | Confidence in the level, not attendance; no attendance score | Points from 100 for turning up and keeping plans, with an optional filter (Q117, Q118) |

---

## Appendix C — Decision log

| Q | Decision |
| --- | --- |
| 1 | Support both clubs that give Raketa courts to sell alone (release lead set by the club) and clubs that keep selling. → Q12 |
| 2 | A yes is conditional and charged only when the game is complete; no holds on a swipe. |
| 3 | A Picked-for-you card is a shared proposal; a yes holds no court; In tags; a short last-seat line. |
| 4 | The deck shows games that name you; Fill in is separate. → refined by Q38 |
| 5 | Raketa earns nothing for now; the share is the court price ÷ seats. |
| 6 | A booked group game lives like today's games (chat, details, result, stars, record). → amended by Q114, Q117, Q119 |
| 7 | Silent yes, visible momentum. |
| 8 | No push for a single swipe. → Q27 |
| 9 | A yes is to the game; empty seats can be filled by anyone who fits. |
| 10 | A card promises a court at a club and an hour; the number comes at booking. |
| 11 | The only deadline is the court's book-by; no clocks. |
| 12 | Three ways to work with Raketa, a per-club setting in the club website. |
| 13 | A live-yes cap plus games per week; never two games at one hour; a list of your yeses. → cap removed by Q97 |
| 14 | A game plays full or not at all; nobody pays more for an empty seat. → read at the cut-off since Q58 |
| 15 | Relaxing the level filter: out of scope. |
| 16 | No lightweight engine, no toggle; distance stands down inside groups. |
| 17 | Weekly hours per day, to the hour, asked in onboarding and editable in You; no "not this week". |
| 18 | Intent asked once, inline. |
| 19 | Members only, always taking part; courts per group kind. → Q29 |
| 20 | Written for a pool; the Players deck probably goes later. *Superseded 2026-10-06: the old loop and its flag were removed (#569).* |
| 21 | Another player learns of a yes from the card. |
| 22 | → replaced by Q38 |
| 23 | → replaced by Q54/Q58 |
| 24 | A failed payment at the fill: nobody pays, the seat reopens, the player can take it back. → amended by Q109 → amended by Q113 |
| 25 | The Leave button's rules. → updated by Q58 |
| 26 | The record's rules. |
| 27 | Settings: games per week, most I'll pay, notifications. |
| 28 | Games per week stays a free setting (default 2). |
| 29 | Official groups use other clubs only when theirs has no shared hour in 14 days; player groups home + 10 km. |
| 30 | 1-hour games; 14 days; hours must cover the game. |
| 31 | Post a game. → Q40 |
| 32 | The bottom tab is **Home**; the group tab stays **Games**; Players behind a flag. *Superseded 2026-10-06: the old loop and its flag were removed (#569).* |
| 33 | The old loop is retired into the flag. → Q42 *Superseded 2026-10-06: the old loop and its flag were removed (#569).* |
| 34 | Fill in has **You're In**, including your posts. |
| 35 | The moment a game fills. → amended by Q103/Q110 |
| 36 | The statuses. → updated by Q39/Q58/Q98/Q99/Q105/Q106/Q111/Q113/Q114 |
| 37 | The chat opens when the game fills. |
| 38 | Fill in is the rescue board; games that are still filling stay in the deck; three card types. |
| 39 | *Held/Booked* wording (Held later removed by Q54). |
| 40 | The posting steps; the court before the people. |
| 41 | Post limits (2 live, counts as a yes and toward games per week). |
| 42 | One "Classic play" flag brings back Players, Chats, challenges/plans and Find a game together. *Superseded 2026-10-06: the old loop and its flag were removed (#569).* |
| 43 | The club settings and defaults. |
| 44 | The club is the seller and pays the card fees. |
| 45 | Cards, Google Pay, Apple Pay if tested; BLIK evaluated in Q57. |
| 46 | → replaced by Q58 |
| 47 | A refunded leaver bears the card fee. → amended by Q113 |
| 48 | → replaced by Q59 |
| 49 | Versions at half-In. |
| 50 | Open seats stay until the cut-off, however many. |
| 51 | The deck order. |
| 52 | One game, shared yeses across versions. |
| 53 | Posts are not in Fill in; a Challenges alert, on by default. |
| 54 | Pay when the game fills; free to leave until the cut-off (B1), after researching Playtomic. → amended by Q113 |
| 55–56 | → replaced by Q58/Q59 |
| 57 | BLIK: confirm with Stripe first; cards and wallets launch either way. |
| 58 | The money timeline. → amended by Q113 |
| 59 | The screen before the first yes. |
| 60 | Versions are not a card type; thin posts; singles versions. |
| 61 | Nobody confirms anything at the fill; receipts by email and in the app. |
| 62 | No-shows reported in the result, 24 h to dispute; optional QR check-in that never gates money. → amended by Q115, Q116 |
| 63 | Price fixed on the card; club cancellations; leaving a group; blocks; the empty deck. |
| 64 | This document goes in the repo, the illustrated HTML on the Desktop; then the ADR, then the UI document, then building. |
| 65 | A 10-second undo, only on the yes that fills a game. → amended by Q74 |
| 66 | The club website's bookings and check-in pages. → the check-in page amended by Q116 |
| 67 | After the session, on request: a dedicated club-website section ([§16](#16-the-club-website)). Its **◇** items were filled in while writing, not grilled. |
| 68 | FRIEND shows only once a friends feature exists. |
| 69 | The *asked / no answer yet* tag is removed. |
| 70 | Rows are sides; the *vs* line and the bar name the same sides, yours on the left; a rescuer takes the leaver's seat and side. |
| 71 | Card and posting grid use ranges Morning 07–12, Afternoon 12–17, Evening 17–23; bright / dim / ringed; today's High / Good / Slim grading. |
| 72 | The stamp shows the price when the yes charges at once; countdown *21 h 00* / *45 min*, coral under 1 h; tile → record, card or **i** → details. → amended by Q124 |
| 73 | A week at its games-per-week cap is not dealt, with a slim line at the top of the deck. |
| 74 | Every action that moves money gets the 10-second undo, including every rescue join (amends Q65). |
| 75 | Game details serve a game that is still filling. |
| 76 | You're In holds picks, challenges and posts; a rescue join goes to Home. |
| 77 | The posting grid is 7 days × 3 ranges, grouping real hourly overlaps. |
| 78 | The posting level range defaults to the engine's range for the kind, narrowed in 0,05 steps. |
| 79 | Joining someone else's post from the sheet is allowed if you fit; *I'm in*, no court number. → amended by Q124 (a post's last seat reads *Pay*) |
| 80 | Gender filters count members with a gender set; Mixed pairs only in doubles; sport chips; the draft is kept; three guards on Post. |
| 81 | *Your week* is 7 × 16 hours, tap and drag, no templates, onboarding and You. |
| 82 | Payment setup order: choose → card details (Stripe's fields) → accept the terms → confirm with your bank; only the phone's wallet shows. |
| 83 | Change keeps the old method until the new one is saved; Remove only with nothing live; LIVE YESES · n; chips Off · 35 · 45 · 60 zł. |
| 84 | Screens missing from the mocks are built in their style (Home cards, details additions, chat, Undo toast, It's a game!, intent question, payment interstitial, empty states). |
| 85 | Push notifications are built (free except the Apple membership publishing needs anyway), with money notices also emailed. → extended by Q120 |
| 86 | The club website design is mine as proposed; the Overview shows only what waits for an answer. |
| 87 | Backend shape: the pool is first-class; new event-sourced contexts; availability becomes hours; payments behind a port with a fake adapter. |
| 88 | Every piece of data is seeded through the real use cases, with fake payments; Stripe test keys are a human's. |
| 89 | Order: ADR → documents → PRD and tickets → building; the product owner picks the tickets and nothing is implemented here. |
| 90 | The Competitive / For fun switch is added to Games and stays on Friends; peeking cards fade; the club website keeps its top bar. |
| 91 | A tile without IN is a normal tile. |
| 92 | A posting-grid cell counts the best fits free together at the best hour. |
| 93 | The slot sheet's *Already happening here* lists rescues first, then posts still filling; the red dot covers both. |
| 94 | Push now; every money event also emailed. → extended by Q105 |
| 95 | The setup checklist sits on Overview until the club is live. |
| 96 | The empty deck keeps today's cards plus Post a game; rescue details for non-members; public site unchanged; payment not in onboarding; the product owner runs to-spec and to-tickets. |
| 97 | (2026-10-05, amends Q13) No live-yes cap: games per week and one game per hour already bound what a yes can book. The LIVE YESES list stays. |
| 98 | (2026-10-09, amends Q36; ruled by the product owner from story S-01A, [#605](https://github.com/Raketa02/Raketa/issues/605), F-REQUEST-43.1) *Do the players see when the club must answer?* Yes: while their game waits for its club, the Home card and the details show the deadline the desk is given (*Bonarka answers by 20:45 · Nobody pays until it confirms*), and it disappears once the deadline passes. It moves no money. Evidence: the desk's email says *Answer by …* while the players read only *Waiting for the club*; Playmore's full game reads *Skład pełny · potwierdzimy o {time}*. |
| 99 | (2026-10-09, amends Q36's *Booked* money line; ruled by the product owner from story S-01A, [#605](https://github.com/Raketa02/Raketa/issues/605), F-LEAVE-20.1) *Does the card say "free to leave"?* No. The card, the details and the booking email say the sum: *38,40 zł back if you leave by Wed 19:00*, dropping to *Paid · 40 zł* at the cut-off as before. The booking email (*It's a game! · you paid 40 zł*) says *You can leave until Wed 19:00 and get 38,40 zł back at once (the 1,60 zł card fee isn't returned).*, with the day and time written as the email writes them; a game that filled after its cut-off keeps its sentence. Q47 stands: a refunded leaver still bears the card fee, and the club is still the seller that pays its card fees (Q44). The terms (§12.5, with a note to the lawyer's review, and O3), the deck's *no free cancellation*, the club's *Free-cancellation cut-off*, the line under *Leave the game* and the leave sheet keep their words. Evidence: Playtomic reviewers in Germany and Spain complain of a "free" cancellation that cost a fee (*Die App verlangt 0,95 € Bearbeitungsgebühr!*); Kraków's own systems say *bezpłatnie* and keep a fee (tenis4U keeps 2 %, Playmore its service fee); Playmore's preview says *ze zwrotem wpisowego*. → amended by Q113 |
| 100 | (2026-10-09, amends §14.3's *reached only from the game details* and §2's *Chat has no tab* line, the screens' A4.4 (*the back chevron returns to the details*) and A8's *a Home card has no chat door* (added by the consistency pass [#531](https://github.com/Raketa02/Raketa/issues/531)), and ADR-0189 §6; ruled by the product owner from story S-01A, [#605](https://github.com/Raketa02/Raketa/issues/605), F-HOME-15.1) *Does the Home card's bubble open the chat?* Yes: straight over Home, with Back to whichever screen opened it (Home from the bubble, the details from their *Chat*). The room stays only the conversation, with no way into the details. Opening it from the bubble clears *new*, as opening the details does. The bubble shows when it did before (the chat is open; never on *Waiting for the club* or *Called off*) and carries no count until the unread count owed to the details' *Chat · n* is built (F-HOME-21.1); then it shows the same number. Evidence: a chat icon is a button in every app a player uses, and Playtomic opens a match's chat from the match itself. |
| 101 | (2026-10-09, settles the build's *no count, nothing marked read* ([#549](https://github.com/Raketa02/Raketa/issues/549)); ruled by the product owner from story S-01B, [#606](https://github.com/Raketa02/Raketa/issues/606), F-NOTIFY-17.1, F-NOTIFY-16.1) *Does the bell show a number?* Yes: the notices given since the player last opened the list, *99+* above 99. The server keeps it, so it is the same on every phone. Opening the list clears it, and the rows that came since the last visit stand out on that visit; nothing is marked read row by row, and there is no *mark all*. **Nothing comes down at launch**: what was told while Raketa was closed is in the number. Coming back from the background still shows a banner for the newest notice only, and the number counts the rest. The list stays the newest 30, and the app icon's number waits for push ([§17.2](#172-notifications), the screens A9). Evidence: Playmore's bell counts unread notices to *99+* and opening the list reads them; tenis4U counts them in its header; WhatsApp counts per chat and on its icon; Playtomic lights a dot. No rival was found showing a banner at launch. |
| 102 | (2026-10-09; ruled by the product owner from story S-01B, [#606](https://github.com/Raketa02/Raketa/issues/606), F-NOTIFY-18.1) *Is your own fill announced back to you?* No. The player whose yes filled a game sees *It's a game!*, gets no banner for it, and the bell doesn't count it; the row is still in their list. The same holds for a payment confirmed in the app that completes a game: the payer sees the screen, and their own notice is already seen. Their only banner is the one about money taken by someone else's act, such as *Kazimierz Padel confirmed your game · you paid 25 zł*. §11's *everyone else* already left the filler out. Evidence: the build bannered the filler their own *It's a game! · you paid* up to a minute after the screen ([#549](https://github.com/Raketa02/Raketa/issues/549)), telling them what they had just done. |
| 103 | (2026-10-09, amends Q35 and the consistency pass's line ([#531](https://github.com/Raketa02/Raketa/issues/531)) that at an On request club *"the charge and It's a game! follow when it confirms"* (§11, the screens A2.4); ruled by the product owner from story S-01B, [#606](https://github.com/Raketa02/Raketa/issues/606), F-REQUEST-40.1) *Does It's a game! wait for the club?* No: it marks the four being **matched**, not only booked. At a club that confirms, the yes that fills shows its player *It's a game!* with *Kazimierz Padel answers by 21:15 · Nobody pays until it confirms* instead of the toast, the time written as Home's *answers by* is (the hour alone when it falls today). All four get the always-on notice *It's a game! · Kazimierz Padel answers by 21:15* (*Padel · Fri 19:00. Nobody pays until it confirms.*), which isn't emailed; the filler's copy is already seen (Q102). When the game refills and goes back to the club, they are told again with the new time. The club's yes stays one notice, *Kazimierz Padel confirmed your game*, with no second *It's a game!*. Home is read again whenever a notice arrives, so the game is there when the notice is tapped. Evidence: Playmore's full game reads *Skład pełny · potwierdzimy o {time}* and pushes everyone *Komplet w Waszej grze*; Playtomic tells nobody when an open match fills; no rival has a game that waits for the club's yes. |
| 104 | (2026-10-09, extends §17.2; ruled by the product owner from story S-01B, [#606](https://github.com/Raketa02/Raketa/issues/606), F-REQUEST-33.1, F-REQUEST-38.1) *Is every ending of a full game told?* Yes: every ending and every fall-back of a full game is told to everyone still in it. A game that ends reads *called off*, with why; a leave after the last moment to book while the club decides gives *Your Fri 19:00 is called off · nobody paid* / *Oscar Bertran left after its last moment to book — Padel at Kazimierz Padel.* A game that falls back to filling reads *Your Fri 19:00 at Kazimierz Padel is filling again* / *A seat opened — nobody paid.*, and never says whose card failed, whose week filled or who no longer fits; that covers a request taken back because a player's week filled, or because two players no longer fit at the club's yes. A named leaver keeps *Oscar Bertran left your game — it's filling again.* If the paused yes later comes back and refills the game, all four are told as at any fill (Q103). A card that never filled still disappears untold (§5.4; Q11 stands). Evidence: Playmore can't mute cancellations (*Tego nie wyciszysz. O płatnościach, odwołanych grach…*); Playtomic's club cancel tells *participants … by email and notification*; reviewers complain of not being told of late cancellations. |
| 105 | (2026-10-09, extends Q94: until now only money was emailed; ruled by the product owner from story S-01B, [#606](https://github.com/Raketa02/Raketa/issues/606), F-REQUEST-23.1) *Are the club's no and its silence told apart?* Yes, and both are emailed. The words are *Kazimierz Padel said no* and *Kazimierz Padel didn't answer in time*, both with *Padel · Fri 19:00. Nobody paid — you'll get a new card first.* The same words appear in the notice, the email and on Home's called-off card and details, and the club's Refuse dialog promises the desk exactly those words (§16.8). Evidence: bookings that wait for a yes, outside sport, email the answer (Airbnb's *Declined* / *Expired*, TableCheck's confirmation); push is off on every phone today, so email is the only way to reach a player outside the app. |
| 106 | (2026-10-09, amends §14.1's *Called off* row, which listed *a player left while it waited for the club*, and §13's *Waiting for the club* row, which called the booking off; ruled by the product owner from story S-01B, [#606](https://github.com/Raketa02/Raketa/issues/606), F-HOME-10.1, F-REQUEST-31.1, F-REQUEST-31.2) *Where does a full game that falls back go?* It stays on Home as **Seat open** for those still In: *1 seat open · Kazimierz Padel is asked again when it's full · nobody paid*, or *1 seat open · books when it's full · nobody paid* at a club that books at once. It becomes *Waiting for the club* again when it refills, and *Called off · nobody paid* if its last moment to book passes first. It is also in *You're In*. This mirrors a booked game's *Seat open*. Evidence: the build dropped the spec's *Called off* card for a leave while the club decided, because the same game would read *called off* on Home and *filling* in Play, so it vanished from Home for everybody ([#543](https://github.com/Raketa02/Raketa/issues/543)). |
| 107 | (2026-10-09; ruled by the product owner while grilling story S-01B, [#606](https://github.com/Raketa02/Raketa/issues/606), with no finding of its own) *Is the new card announced?* Yes. Whenever a notice or email promised *you'll get a new card first* (the club said no, didn't answer, or cancelled), the players it is dealt to are told when it arrives: *Your new game · Sat 10:00 at Bonarka Arena* / *The same players · 40 zł a share — say yes to book it.* Tapping it — the banner, the row in the list or, later, a push — opens the group's Games deck with that card on top. It is always on and isn't emailed. Evidence: the four were promised a new card first, and the build deals it into their decks without a word ([#622](https://github.com/Raketa02/Raketa/issues/622)). |
| 108 | (2026-10-09; ruled by the product owner from story S-01B, [#606](https://github.com/Raketa02/Raketa/issues/606), F-LEAVE-26.1, F-EMAIL-13.1) *Is a leaver told what happens to the game?* Only when it touches them. When their empty seat calls the game off at the cut-off: *Tuesday's 19:00 at Bonarka Arena, which you left, was called off* / *Your seat stayed empty, so it counts on your record. Your 38,40 zł refund stands.* When the club's cancel refunds them (they left after the cut-off and their seat was still paid), they are told in a leaver's words, with the reason and the refund, and never promised a new game; the notice and the email both use those words. A leaver already refunded hears nothing more about the game. §15.4 is unchanged: the mark stands, and this only tells the leaver. Evidence: in the build a leaver whose empty seat called the game off is told nothing though it marks their record, and a leaver the club's cancel refunds reads the others' words, a new game promised included ([#623](https://github.com/Raketa02/Raketa/issues/623)). → amended by Q113 |
| 109 | (2026-10-09, amends Q24 and §12.2; ruled by the product owner from story S-01B, [#606](https://github.com/Raketa02/Raketa/issues/606), F-PAY-39.1, F-EMAIL-5.2, F-EMAIL-7.1, F-FILL-42.1, F-REQUEST-15.1, F-REQUEST-14.1) *How long does a player whose payment failed have to pay?* **Time to pay**: 30 minutes. Q24's rule — nobody pays, the seat reopens, the player can take it back — stands; what changes is that the reopening waits. When a share is refused at the fill, or at the club's Accept, the seat is held for that player alone for 30 minutes, and never past the game's last moment to book. The other holds stay on their cards, a confirmed one included; at a club that confirms, the club's yes and its court stay too. The player's notice, email and *To confirm* row name the time: *Confirm your payment by 14:40 to keep your seat.* If they pay in time, the game books at once on the kept holds: nobody's bank is asked again, and the desk isn't asked again. If they don't, the holds are let go, their seat is offered to others as before (they may still take it back while it's free), and the others are told it is filling again. At a club that books at once the court isn't held, as for any game still filling. If no time is left before the last moment to book, the game is called off at once and everyone is told. Nothing retries a card by itself. The book-by stays the only deadline on a card (§5.4): time to pay is one player's, and never outlasts it. Evidence: Playmore gives 30 minutes to pay for a court booking (*dokonaj płatności w ciągu 30 minut*, *Zostało {minutes} min*), and its league seat holds a place (*Trzymamy dla Ciebie miejsce do {time}*); Airbnb gives a guest 24 hours with the dates held; a card hold lasts 4–7 days at Stripe; Stripe can't pass a bank's check without the customer, and its automatic retrying covers only subscriptions. → amended by Q113 |
| 110 | (2026-10-09, amends Q35 with Q103; ruled by the product owner from story S-01B, [#606](https://github.com/Raketa02/Raketa/issues/606), F-FILL-35.1) *What does It's a game! say while one payment is missing?* At a club that books at once, when another player's card fails, the last yes sees *It's a game!* with *Waiting for one payment · until 14:40 · Nobody pays until it's in*, and the others get *It's a game! · waiting for one payment until 14:40*. When the payment comes in, they read *Your Tue 19:00 is booked · you paid 40 zł*: nobody is told *It's a game!* twice. The player whose payment completed it sees the *It's a game!* screen. At a club that confirms, where the four already had *It's a game!*, the others read *Your Fri 19:00 is waiting for one payment, until 21:20*, and the payment then brings *Kazimierz Padel confirmed your game · you paid 25 zł*. Evidence: as Q109's; in the build the last yes sees nothing special and the others are told nothing while one payment is missing. |
| 111 | (2026-10-09, adds a status to Q36's; ruled by the product owner while grilling story S-01B, [#606](https://github.com/Raketa02/Raketa/issues/606), with no finding of its own) *What does Home show while one payment is missing?* For the 30 minutes the game is on all four's Home as **Waiting for one payment**: *Waiting for one payment · until 14:40 · Nobody pays until it's in*. The payer's card reads *Confirm your payment by 14:40*, beside their *To confirm* row. At the end it becomes *Booked*, or *Seat open* (Q106). Evidence: as Q109's — Playmore's held seat says until when (*Trzymamy dla Ciebie miejsce do {time}*). |
| 112 | (2026-10-09, extends §16.7, §16.8 and §16.12; ruled by the product owner when the tickets for story S-01B, [#606](https://github.com/Raketa02/Raketa/issues/606), were cut, with no finding of its own) *What does the desk see during the time to pay?* The accepted booking reads *Accepted · waiting for one player's payment until 21:20* in the club's Bookings. It isn't in *Waiting for you*, because the desk has answered. If the time runs out, the desk is emailed as for a cut-off: *A game didn't go ahead* / *A player's payment didn't come in time — the court is free again.* When the game is full again, the desk is asked again as for any new request. Evidence: as Q109's; in the build the desk's yes is thrown away when one card fails, and the desk is asked a second time once the game is full again ([#626](https://github.com/Raketa02/Raketa/issues/626)). |
| 113 | (2026-10-10, amends Q24, Q47, Q54, Q58, Q99, Q108 and Q109, and Q36's money lines; ruled by the product owner from story S-01A, [#605](https://github.com/Raketa02/Raketa/issues/605#issuecomment-6097600856), F-LEAVE-6.1; specified by [#634](https://github.com/Raketa02/Raketa/issues/634); recorded by ADR-0189's 2026-10-10 amendment and ADR-0190's §1 amendment) *When does a share move, and what does leaving cost?* **The share is held when the game fills and taken at the club's cut-off, the one deadline, the same for everyone; leaving before it is free.** The product owner's rules: the law first; the club never pays for a player's leave; the club's cut-off is the one deadline. At the fill, or at an On request club's yes, every seat's share is held, all or nothing, and the court is booked as before; nothing is taken (amends Q54 and Q58). A seat whose hold would not reach the cut-off — its last moment less than 6 hours after it — gets a **card check**: held for seconds and let go, which proves the money is there that day, and held again at its **holding time**, four days before the cut-off. At the cut-off a full game's shares are taken; a game still short is called off and every hold is let go, so nobody pays anything. A leave before the cut-off lets the hold go: nothing is taken or refunded, and no fee arises for the leaver or the club. The card reads *40 zł · free to leave until Wed 19:00* from the moment the game fills (amends Q99, whose reason — never call a leave free when it costs a fee — is now met), and a leaver whose empty seat called the game off is told *Nothing was taken from you* (amends Q108). A card refused before the cut-off — at the fill, the club's yes, the holding or a rescue — gets **time to fix the card**: 30 minutes with the seat kept and nothing paid, *Fix your card by 14:40 to keep your seat*; not fixed, the seat goes to others and nothing is owed (amends Q109, and Q24, whose rule stands under the new names). After the cut-off money is taken at once — a game filling after it, a club's yes after it, a rescue after it — and a refusal gets time to pay as before. A leaver after the cut-off whose seat is taken gets the share back less exactly what Stripe kept on their payment, shown to the grosz before leaving and on the receipt: *If someone takes your seat, you get 38,24 zł back (40 zł less the 1,76 zł kept on your payment)*. The club neither earns nor loses on it (amends Q47: only after the cut-off, and at the real fee). The terms' wording for it waits for the lawyer (O3); if the lawyer refuses it for personal EU cards, the fallback is everything back on those cards. No estimated card fee is printed anywhere. BLIK can't be held: its rule is decided when it launches, and it is cards only until then. A club's cancel before the cut-off lets every hold go; after it, everyone is refunded in full and the club bears the fees, as before. The terms get a new version, which every player accepts before their next game holds money. **Six calls #634 made without a ruling** are written in as rules, each marked *a call* where it stands, for the product owner to overrule: a seat lost because the card wasn't fixed at its holding counts as leaving before the cut-off on the record (§15.4); the take at the cut-off is a quiet row and a receipt, not a push (§17.2); a refused rescuer keeps the seat for 30 minutes, never past the start (§10.1); the reach margin is 6 hours and the holding lead 4 days, both domain constants (§12.2); the fallback takes a holding early when its last moment still falls short, and refunds a later timely leave in full, the one place the club could pay for a leave (§12.2); and the club's figures drop the estimate too (§16.11). **Words the ruling and its tickets didn't give** were written in while recording it, each marked where it stands: the others' words while one card is being fixed stay *Waiting for one payment* (§12.2); the leaver's emails (§13); the desk reads *Accepted · waiting for one player's card until 21:20*, and is emailed *A player's card wasn't fixed in time* on a lapse (§16.8); the quiet row reads *Your 40 zł for Thu 19:00 was taken* (§17.2); and, in the screens, the toast for a card refused at the fill (A2.4), the method card's line, the terms step and the receipts' footer (A7.3). **Evidence:** Stripe never returns its fee on a refund — *"Stripe's processing fees from the original transaction aren't returned"* — and letting a hold go is free — *"You can cancel a payment before it's completed at no cost"* ([Stripe: refunds](https://docs.stripe.com/refunds)); a Visa hold placed without the customer lasts *"4 days and 18 hours"* and a Mastercard 7 days, and Stripe's own delayed capture runs *"about 6 hours before the expiration time"* ([Stripe: place a hold](https://docs.stripe.com/payments/place-a-hold-on-a-payment-method)); *"the `payment_method_details.card.capture_before` attribute on the charge is the most reliable and accurate way to determine your charge's authorization window"* ([Stripe: CITs and MITs](https://docs.stripe.com/payments/cits-and-mits)); the fee exists only once the money is taken — *"A PaymentIntent must be captured and have a status of `succeeded` for the Stripe fees to be available"* ([Stripe: expand use cases](https://docs.stripe.com/expand/use-cases)) — and a card's tier is known only *"at the point of capture"* ([Stripe support: standard and premium cards](https://support.stripe.com/questions/what-s-the-difference-between-standard-and-premium-cards)), so the 1,60 zł the card and the leave sheet printed was an estimate: in Poland Stripe keeps *"1.5% + 1.00zł for standard European Economic Area cards"*, *"1.9% + 1.00zł for premium"*, *"2.5% + 1.00zł for UK cards"* and *"3.25% + 1.00zł for international cards"* ([Stripe pricing, Poland](https://stripe.com/en-pl/pricing)), so a leaver on a business Visa would have had 1,76 zł kept where 1,60 zł was promised. Stripe's terms say *"Except to the extent the Card Network Rules or Law permits, User must not charge surcharges, other fees, or Taxes for accepting payment cards"* (§3.4(e), [Stripe Services Agreement](https://stripe.com/legal/ssa-service-terms)). Polish payment law says *"Odbiorca nie pobiera opłat za korzystanie z instrumentów płatniczych, w przypadku których opłaty interchange są regulowane w przepisach rozdziału II rozporządzenia (UE) 2015/751"* — no charge for using the personal EU cards whose interchange the EU caps (art. 37a ust. 3, [ustawa o usługach płatniczych, Dz.U. 2026 poz. 623](https://api.sejm.gov.pl/eli/acts/DU/2026/623/text.pdf)). The civil code caps any payment fee at cost — *"Przedsiębiorca nie może żądać od konsumenta opłaty za skorzystanie z określonego sposobu zapłaty przewyższającej poniesione przez przedsiębiorcę koszty w związku z tym sposobem zapłaty"* (art. 383¹, [Kodeks cywilny, Dz.U. 2026 poz. 795](https://api.sejm.gov.pl/eli/acts/DU/2026/795/text.pdf)) — and the European Commission reads that rule as covering *"all kind of fees which are linked to a means of payment, regardless of how they are presented to consumers"* ([guidance on the Consumer Rights Directive, 2021/C 525/01, §8.2](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:52021XC1229(04))). UOKiK says a leisure business whose customer resigns *"może zatrzymać jedynie kwotę odpowiadającą faktycznie poniesionym kosztom"* ([UOKiK, 2014](https://archiwum.uokik.gov.pl/aktualnosci.php?news_id=11103)). A dated sports booking carries no statutory withdrawal right: art. 38 ust. 1 pkt 12 excludes services *"związanych z wypoczynkiem, wydarzeniami rozrywkowymi, sportowymi lub kulturalnymi, jeżeli w umowie oznaczono dzień lub okres świadczenia usługi"* ([ustawa o prawach konsumenta, Dz.U. 2026 poz. 1244](https://api.sejm.gov.pl/eli/acts/DU/2026/1244/text.pdf)), so the leave is the club's own rule and a late leaver is owed nothing back. Stripe's extended authorisation *"only applies to Customer-Initiated Transactions"* on Visa ([Stripe: extended authorization](https://docs.stripe.com/payments/extended-authorization)), and BLIK has *"Manual capture support: No"* ([Stripe: BLIK](https://docs.stripe.com/payments/blik)). |
| 114 | (2026-10-11, amends Q6 and §15.3's *if nobody enters anything, the game ends Never played, as today*, and ADR-0140 §2's ghost; ruled by the product owner from story S-01D, [#608](https://github.com/Raketa02/Raketa/issues/608#issuecomment-6113038779), F-RESULT-10.1; specified by [#649](https://github.com/Raketa02/Raketa/issues/649); recorded by [ADR-0195](../../adr/0195-reliability-is-points-a-no-show-is-caught-at-the-court-and-a-right-score-needs-no-tap.md) §2) *What is a full booked game nobody recorded?* **Played.** It reads *Played · no score* for all of its players when its entry window closes; each gains the 5 points of a game played through, and no Level moves. *Never played* retires, and nobody is charged on *Shows up* for an unrecorded evening. Evidence: in the build, four players who played and paid at Bonarka and went home without opening the app each took a miss on *Shows up*, and a newcomer whose first game it was read 26 out of 100. Playtomic ends such a game *No score recorded — Sometimes it's not about the results, it's about having a good time together*; no platform or Kraków club rulebook checked penalises a casual booked and paid game nobody recorded; and Playmore's own team calls its post-game loop dead (*od 8.06: 3 wyniki*). |
| 115 | (2026-10-11, amends Q62's no-show report and §15.3; ruled by the product owner from story S-01D, [#608](https://github.com/Raketa02/Raketa/issues/608#issuecomment-6113038779), F-RESULT-10.1; specified by [#649](https://github.com/Raketa02/Raketa/issues/649); recorded by [ADR-0195](../../adr/0195-reliability-is-points-a-no-show-is-caught-at-the-court-and-a-right-score-needs-no-tap.md) §3) *How is a no-show caught?* **At the court, while it happens.** In the first half of the game a player within about 300 m of the club taps *"Oscar isn't here yet"*, and Oscar is pushed at once. His arrival — his own location-checked *I'm here*, or a courtmate's *Oscar's here* — is on time within 10 minutes of the start (nothing is recorded), *Came late* from 10 to 30 minutes, and *Didn't come* after that. A phone that died has *I was there* within 24 hours, which a courtmate confirms, and it reads *Came late*. The tap costs its maker nothing; *Didn't come* takes no score, *Came late* plays on, and money never moves. Location is read only at a tap and never stored. Calls made without a ruling: the location rules, 300 m with the fix's accuracy allowed up to 200 m, *They're here* checked too, who may tap, and the retired events folding to nothing (ADR-0195 §10). Evidence: in the build anyone on the court could tap *didn't come* from home for 25 hours, the reported player's *I was there* from the sofa lifted it, and neither was told. Playtomic's terms make arriving 10 minutes or more late a no-show, and its players choose *Wait and Play* or *Declare No-Show*; Playmore's *Spóźnię się* tells the others *żeby nie czekali pod kortem* (not to wait at the court). Complaints name a no-show window *closed even though the slot for our game finished two minutes ago*, and a player *physically present* marked a no-show from *system logs*. |
| 116 | (2026-10-11, amends Q62's optional QR check-in and Q66; ruled by the product owner from story S-01D, [#608](https://github.com/Raketa02/Raketa/issues/608#issuecomment-6113038779), F-RESULT-10.1; specified by [#649](https://github.com/Raketa02/Raketa/issues/649); recorded by [ADR-0195](../../adr/0195-reliability-is-points-a-no-show-is-caught-at-the-court-and-a-right-score-needs-no-tap.md) §4) *Does a club check players in?* **No.** Desk check-in is removed everywhere: the player's *Show at the desk* QR card, the club website's **Check in** page and its *We check players in* switch, *checked in ✓* in Bookings, and the backend's codes and routes. It solved a problem with no evidence that it was real, and it put a desk queue in front of players at every club. The checked-in event and the setting's field stay decodable and fold to nothing. Evidence: Playtomic has no check-in — *Players can go straight to the court … no need to stop at reception* — and none of its 157 club help articles explains one; tenis4U's desk marks a payment (*Oznacz płatność*), never an arrival. The cost: for Visa's *not received* reason Stripe lists *check-in confirmations* among the proof of service ([Stripe: dispute reason codes](https://docs.stripe.com/disputes/reason-codes-defense-requirements)), and the club loses that evidence ([§16.11](#1611-money)). |
| 117 | (2026-10-11, amends §15.4 and ADR-0140 §2–§5, supersedes ADR-0160, reversing rules R-RESULT-34 and R-RESULT-7; ruled by the product owner from story S-01D, [#608](https://github.com/Raketa02/Raketa/issues/608#issuecomment-6113038779), F-RESULT-44.1 and F-RESULT-35.1; specified by [#649](https://github.com/Raketa02/Raketa/issues/649); recorded by [ADR-0195](../../adr/0195-reliability-is-points-a-no-show-is-caught-at-the-court-and-a-right-score-needs-no-tap.md) §1) *What is Player reliability?* **Points.** Everyone starts at 100. *Didn't come* −25, *Came late* −10, leaving after the cut-off with the seat left empty −15, leaving before it (or losing the seat to an unfixed card) when the empty seat calls the game off −10; +5 per game played through, never above 100; each failure drops out after 6 months, rolling. Bands *Very high* 90–100 · *High* 75–89 · *Medium* 50–74 · *Low* below 50, served by the backend; *100 · New* until 3 games are played through. The sheet shows counts only over 6 months — *Shows up*, *Keeps plans*, *Being late* and *Results left in dispute* — and no ledger. *Answers about results* leaves the figure, and silence on a score costs nothing. It is still computed on every read. Calls made without a ruling: a *Came late* game earns nothing back, *New* is fewer than 3 games ever, and *Results left in dispute* counts over the same 6 months. Evidence: in the build a newcomer's first ghost read 26 out of 100 while a veteran's no-show weighed almost nothing, and the words *Reliable · Holding · Under the bar* named a bar at 70 that nothing applies. Playtomic keeps no attendance score (its *reliability* is confidence in the level); Playmore's league collects punctuality ratings that *widzi tylko obsługa klubu* (only club staff see); and a Kraków complaint about tenis4U is that a club's warnings, unseen by the player, block booking at every club. |
| 118 | (2026-10-11, reverses §5.1's *no score, no weight and no toggle* and rule R-ENGINE-15; ruled by the product owner from story S-01D, [#608](https://github.com/Raketa02/Raketa/issues/608#issuecomment-6113038779), F-RESULT-44.1; specified by [#649](https://github.com/Raketa02/Raketa/issues/649); recorded by [ADR-0195](../../adr/0195-reliability-is-points-a-no-show-is-caught-at-the-court-and-a-right-score-needs-no-tap.md) §6) *Can a player keep away from unreliable partners?* **Yes, with an optional switch**, off by default: *Play only with players of at least High reliability* (or *at least Medium*). It is one more clause of the pair rule, in both directions, on *Picked for you*, *Challenges*, *Seat open* and Fill in; a *New* player passes every minimum. It acts from the moment it is switched on, or the moment someone drops below it; yeses already given stand (a call: the fill doesn't re-ask it, unlike a block), and booked games never change. The filtering player reads *Your filter hides 2 of the 11 players in your groups*; a hidden player reads, with nobody named, *Some players in your groups play only with High reliability or above. At 75 you're dealt with everyone again.* Members lists show points and band. Evidence: Playtomic's players ask for exactly this — *I've learnt to only book competitive matches with people whose reliability of their play level is more than 50%*, *falta poner una opción para … poner una fiabilidad mínima para entrar*, *why can't we … limit participation to those with a certain reliabilty rating?* — and Playtomic already refuses some matches with *The match requires a player reliability level of …*. |
| 119 | (2026-10-11, amends Q6 and §15.2's *unchanged from today*, and ADR-0137's acceptance grace and two standing scores, reversing rules R-RESULT-6, R-RESULT-7 and R-RESULT-8; ruled by the product owner from story S-01D, [#608](https://github.com/Raketa02/Raketa/issues/608#issuecomment-6113038779), F-RESULT-35.1; specified by [#649](https://github.com/Raketa02/Raketa/issues/649); recorded by [ADR-0195](../../adr/0195-reliability-is-points-a-no-show-is-caught-at-the-court-and-a-right-score-needs-no-tap.md) §5) *How is a score settled?* **By one tap or by silence.** No score is taken before the hour. When the hour ends, all of a Competitive game's players are asked *How did it go?*, and the other side is asked *Is that right?* when a score goes up. One *That's right* settles it at once and closes the game, so in doubles the first agreement wins. Silence settles it 24 hours after the score, and costs nothing. Corrections end with the entry window, and Levels move within a minute of settling. Two scores naming the same winner count with the closer one; different winners end disputed, with no Level moved and a *Results left in dispute* line for both posters, never points. For fun asks nothing and reads *Played*. Calls made without a ruling: the closer score's tie, a For fun score standing at once, and Levels within a minute through the outbox and a one-minute catch-up job. Evidence: in the build *Is that right?* said silence cost nothing and then charged a year-long miss on *Answers about results*, and a different score at 22:00 wiped out a *That's right* at 20:35. Playtomic: *If one of the opposing team's players accepts the result, it will validate immediately*, results auto-confirm after 24 hours, and a friendly *will not affect your level*. Playmore freezes a disputed result until the club clears it, which Raketa doesn't do: nobody rules on a score. |
| 120 | (2026-10-11, extends Q85, Q94 and §17.2; ruled by the product owner from story S-01D, [#608](https://github.com/Raketa02/Raketa/issues/608#issuecomment-6113038779), F-RESULT-10.1 and F-RESULT-35.1; specified by [#649](https://github.com/Raketa02/Raketa/issues/649); recorded by [ADR-0195](../../adr/0195-reliability-is-points-a-no-show-is-caught-at-the-court-and-a-right-score-needs-no-tap.md) §7) *Who is told about attendance and the score, and how?* Five new notices, always on — *Isn't here yet*, *They're at the club*, *How did it go?*, *Is that right?* and *Were they there?* — each opening the game's result screen, and never for a For fun game. **Push goes end to end on Android and iPhone**: a human follows a step-by-step ticket for the Expo project, Firebase and the Apple Developer Program at 99 USD a year (accepted by the product owner), and the app then switches push on. Every new notice being always on is a call. Evidence: a tap at the court is worth nothing if it reaches the absent player only when they next open the app; Playtomic documents one push after a match and none when the other team enters or confirms a score; Playtomic and Playmore both push through Firebase; and iOS is 32 % of Polish mobile web traffic. |
| 121 | (2026-10-12, reverses Q1 and Q12, amends Q43's minimum notice and time to confirm, and ends On request's own rules — Q98, Q103's club half, Q104's and Q106's *asked again*, Q105, Q109's and Q112's club's yes, and Q113's *at an On request club's yes*; replaces PRD [#530](https://github.com/Raketa02/Raketa/issues/530)'s out-of-scope *live link to a club's own booking system — the Instant way, automated, later*; ruled by the product owner from story S-01E, [#609](https://github.com/Raketa02/Raketa/issues/609#issuecomment-6120454776), F-REQUEST-3.1 and F-REQUEST-23.1, with F-REQUEST-44.1 and 45.1; specified by [#667](https://github.com/Raketa02/Raketa/issues/667); recorded by [ADR-0196](../../adr/0196-only-raketa-until-raketa-is-the-clubs-booking-software-and-a-clubs-cancel-moves-the-game.md) §1) *Does a club choose how it works with Raketa?* **No: Only Raketa is the one way, until Raketa is the club's booking software.** *Instant* and *On request* are removed everywhere — the club website, the player app, the backend, the test console, the seed and these documents — with the choice, its setup step (five steps become four), the minimum notice and the time to confirm. **A full game books the moment its last yes lands, at every club**: requests, Accept and Refuse, *Waiting for the club*, *answers by*, *Waiting for you* and its badge, *Accepted · waiting for one player's payment*, *said no* and *didn't answer in time*, the request-timeout job, the three request notices and the desk's request emails go. A player whose card is refused at the fill keeps their time to fix the card, or to pay. **The book-by is always the release time**, so no game fills later than a day before its start, and by default three; rescues are unaffected, and only a club whose cut-off is longer than its release lead still deals a card past its cut-off. Raketa settings are the release lead, the cut-off, other clubs' courts and pause; the Overview, once live, says so and links to today's Bookings. *Double booking* stays as a cancel reason. **Raketa will become the club's booking software**: one calendar for the desk, the phone, walk-ins, season bookings, players' own bookings and the Games deck, its shape decided in its own grilling. **Calls made without a ruling** (ADR-0196 §7): the release lead keeps its 1–13 days (the alternative, a lead in hours down to 2 h, is a one-line change); the Overview once live; *double booking* stays; a clean cut, the local store reset and a migration dropping only what requests used; every seeded club Only Raketa, one with both kinds of court at the same hours. **Evidence:** Kazimierz Padel opens at 16:00, so a game that filled at 10:15 read *Kazimierz Padel answers by 11:15*, ran out, and was called off before the desk opened, and the desk had to watch the website all day. No court platform makes a club confirm a booking: Playtomic, MATCHi, Padel Mates, Eversports, ClubSpark, tenis4U, Playmore and kluby.org confirm at once, and Playmore's open games book the court when posted — *"Komplet graczy - gra potwierdzona, kort opłacony w całości"* ([Playmore](https://join.playmore.pl/gry-otwarte/)); the one exception, CourtReserve's opt-in approval, is used *"to … control guest bookings, or review certain membership types"* ([CourtReserve](https://help.courtreserve.com/en/articles/4299937-optional-approval-processes-in-courtreserve)). No competitor relies on a desk closing hours by hand, and every one effortless for the club has one calendar: Playtomic Manager takes *"incoming reservations seamlessly, both online and offline"* ([Playtomic](https://helpmanager.playtomic.com/hc/en-gb/articles/20535516949009)), and MATCHi rejects *"a slot that's already taken"* when Matchable writes to it ([MATCHi](https://matchi.zendesk.com/hc/en-gb/articles/27989311536029)). Kraków's tenis4U, Playmore and kluby.org publish no API, feed or calendar export; tenis4U's terms forbid software reading the site, *"do automatycznego lub ręcznego pobierania fragmentów lub całości strony"* ([tenis4U regulamin, §7](https://tenis4u.pl/regulamin/)), and its player app already carries *"Otwarte sparingi"* and *"Rezerwacje współdzielone"*. |
| 122 | (2026-10-12, amends §16.4's *Move* and §16.9's cancel, which always called the game off; ruled by the product owner from story S-01E, [#609](https://github.com/Raketa02/Raketa/issues/609#issuecomment-6120454776), F-REQUEST-22.1; specified by [#667](https://github.com/Raketa02/Raketa/issues/667); recorded by [ADR-0196](../../adr/0196-only-raketa-until-raketa-is-the-clubs-booking-software-and-a-clubs-cancel-moves-the-game.md) §2 and §4) *Must a club's cancel throw the game away?* **No: a free court of the same club absorbs it when nothing about the game changes — a move by cancel.** Raketa first looks at the same club for a free court with the same sport, day, hour and price, of the same kind or indoor for an outdoor game, and indoor only for *weather*; the same kind first, then indoor, in the club's court order. The game moves there: every hold or taken share stays as it was, nothing is refunded or let go, nobody is owed a card or swipes anything, and every player is told *Game moved* — *Bonarka Arena moved your game to Court 3 · Thu 19:00* / *Court 2 can't be played · Padel · indoor · nothing else changes*. The cancel dialog previews it and offers *Cancel the game anyway*, and the cancel decides afresh when the club confirms. Otherwise the game is called off as before, and its players are owed a card (Q123). The club's own *Move* offers only the same kind, or indoor for an outdoor game, and tells the players with the same notice, *Padel · indoor · nothing else changes*. **Players see the kind of court**: a booked game always (*Court 3 · indoor*), and a card when every free court it could be booked on is of one kind; it is not a preference or a filter. A change of club, day, hour, price, or from indoor to outdoor is always a new card. **Calls made without a ruling** (ADR-0196 §7): the same price kept as a condition though price is per club and sport; the kind on a card only when certain; a weather cancel moves only indoors; the same kind before indoor; the preview and *Cancel the game anyway*; *Move* keeps the kind and tells the players; *Game moved* always on, opening the booked game, not emailed. **Evidence:** on Thursday at 15:00 the lights on Bonarka Arena's Court 2 failed; Court 3 was free at 19:00 at the same 160 zł, *Cancel* never offered it, and four 40 zł holds were let go. The club website's help said a court's indoor or outdoor was *shown on a player's card*, and nothing showed it. Playtomic picks an open match's court itself — *"the system automatically assigns courts as the match time approaches"* ([Playtomic](https://helpmanager.playtomic.com/hc/en-gb/articles/20534737902353)) — and cancels only if *"The court becomes unavailable at the club"* ([Playtomic](https://playerhelp.playtomic.com/hc/en-gb/articles/19831672824465)). |
| 123 | (2026-10-12, amends Q107's source and §8.2's order, and lifts the build's rule *never at the club and hour that turned them down*, written for a refusal by [#543](https://github.com/Raketa02/Raketa/issues/543) and applied to a cancel by [#547](https://github.com/Raketa02/Raketa/issues/547); ruled by the product owner from story S-01E, [#609](https://github.com/Raketa02/Raketa/issues/609#issuecomment-6120454776), F-REQUEST-22.1; specified by [#667](https://github.com/Raketa02/Raketa/issues/667); recorded by [ADR-0196](../../adr/0196-only-raketa-until-raketa-is-the-clubs-booking-software-and-a-clubs-cancel-moves-the-game.md) §3) *Which new card does a club's cancel owe, and where is it?* **The closest game to the lost one, first in the deck.** The **owed card** is chosen at (1) the same club, day and hour, on the other kind of court or at a new price; (2) for a player group only, another club at the same day and hour, nearest first; (3) the closest hour in time, the home club first. An official group stays at its home club unless its courts are full. The *never at this club and hour* rule goes entirely, because a refusal was its only other source. It is an ordinary card, its players free and fit, each of them swiping it; a game no hour is found for stays owed until its old hour passes. It is first in the group deck of each player it is owed to, whenever they open it, until they answer it or it is gone, soonest first among owed cards, with no mark for anybody; other members' decks are unaffected. The cancel notice gains *We'll look for another game for you first*, as the email already said; *Your new game* opens the deck on the card, and for a card at the same club and hour names the kind. **Calls made without a ruling** (ADR-0196 §7): the cancel notice's line; the rule lifted entirely, not only for a cancel; first for each player it is owed to, soonest first, unmarked even with push off; the card records the players it is owed to, and the deck orders by that. **Evidence:** after Bonarka's cancel, Marta's new card could never be Bonarka at Thursday 19:00, though the same hour there on another court was the closest game to the one she lost, and it landed eleventh of 33 in her deck, behind every card dealt to her before it, while the email promised *We'll look for another game for you first*. |
| 124 | (2026-10-25, amends Q72, and Q79's *I'm in* on a post's last seat; ruled by the product owner from story S-16A, [#713](https://github.com/Raketa02/Raketa/issues/713#issuecomment-6400470479), F-DECK-34.1 and F-FILL-1.1; specified by [#717](https://github.com/Raketa02/Raketa/issues/717)) *What does the control that binds a player to pay say?* **Pay, with the share, and a vote shows the share too.** The swipe stays the order. A yes that books at once (*Book it now*) or takes a *Seat open* is stamped **PAY · 40 zł**. A vote (*Court available*) is stamped **I'M IN · 40 zł**, reversing Q72's *no price on a vote*: the word, not the price, now tells a vote from a payment. The share is the card's own, fixed when the card was made. Every button that moves money reads **Pay 40 zł**: the Fill in seat row, a rescue's details, Post a game's sheet (a rescue, and a post's last seat) and the details of a *Book it now* game. **Unchanged:** *NOT THIS TIME*, the deck's ball button (*I'm in*) and the pill (*Booking in 10 s*). The words are English, and Polish comes with the app's translation. A lawyer is asked two questions before launch ([§12.5](#125-saving-a-payment-method-and-the-terms), O3): can a swipe stamped *PAY · 40 zł* be the order under art. 17, and does a vote stamped *I'M IN · 40 zł* bind the player to the share taken at the cut-off? If the first is no, the agreed fallback is a confirm screen with a *Pay 40 zł* button on every money-moving yes. **Evidence:** a vote binds a later 40 zł charge that needs no further press, yet the build stamped it *I'M IN*, with no price and no word of paying, and stamped even the yes that books *I'M IN · 40 zł*. Polish law wants the control that binds a consumer to pay marked *"zamówienie z obowiązkiem zapłaty"* or an equivalent, or *"umowa nie zostaje zawarta"*, and the club, as the seller, carries that risk ([art. 17 ust. 3–4](https://api.sejm.gov.pl/eli/acts/DU/2026/1244/text.pdf)). The EU Court applies the rule *"even where the consumer is required to pay … only after a subsequent condition has been satisfied"* ([C-400/22](http://publications.europa.eu/resource/celex/62022CJ0400)), here the game filling, and counts *"only the words that appear on that button or that similar function"* ([C-249/21](http://publications.europa.eu/resource/celex/62021CJ0249)). UOKiK accepts *"kup teraz"*, *"zapłać teraz"* and *"potwierdź zakup"*, and rejects *"zarejestruj"*, *"potwierdź"* and *"zamów teraz"* ([UOKiK](https://prawakonsumenta.uokik.gov.pl/pytania-i-odpowiedzi/prawo-do-informacji/)). The Commission's guidance names *"buy now"*, *"pay now"* and *"confirm purchase"*, and wants the label *"on the button itself or immediately next to it"* ([2021/C 525/01](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:52021XC1229(04))). No authority has ruled on a swipe or a gesture. |
