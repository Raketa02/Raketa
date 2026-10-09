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
2. **A swipe right is a free, silent yes.** "I'm in — if everybody is, book it and charge my
   share." No money moves, no court is held, nobody is notified.
3. **Yeses are visible on the card.** Other players see your tile marked **In**, and cards
   with more people In rise to the top of their decks. The card that needs only you says
   **You complete it**.
4. **The last yes books the game.** Every player's saved card is charged at that moment,
   all together or not at all, the court is booked with the club, and everyone sees
   **It's a game!**. Nobody has to confirm anything.
5. **Free to leave until the club's cut-off.** Leave before it and you are refunded at once
   (minus the card fee); your seat becomes a **rescue** that others can take. Leave after it
   and you are refunded only when someone takes your seat.
6. **A game is full at the cut-off, or it is off.** If a seat is still empty at the club's
   cut-off, the game is called off and everyone still in gets all their money back. Nobody ever
   pays more for an empty seat; a seat left after the cut-off may stay empty, and the game goes
   ahead short ([§14.1](#141-home-and-the-statuses)).
7. **Fill in is the rescue board.** It holds the seats of booked games that lost a player,
   and a list of your own yeses that have not become games yet.
8. **Members can post a game.** They pick the hour and the court; the app deals it to their
   best fits as a **Challenge**.
9. **The club is the seller.** On the club website it lists its courts, hours and prices,
   sets how it works with Raketa, answers requests, cancels and checks players in; it gets
   paid through Raketa after the game and pays the card fee as it would at its own terminal.
   Raketa earns nothing for now ([§16](#16-the-club-website)).

---

## 2. Words used in this document

| Word | Meaning here |
| --- | --- |
| **Group** | A crowd of players at a home club (a player group) or a club's own community (an official group). This document is written for "a pool of players plus the courts around them"; a group is the first pool, a whole city (Explore) will be a later one. |
| **Court hour** | One court at one club for one hour. Every game lasts exactly **1 hour**, for every sport. |
| **Game** | Two or four players plus one court hour plus a kind. |
| **Kind** | **Competitive** (a counted game: a confirmed score moves levels) or **For fun** (a friendly: levels stay put). |
| **Share** | The court's price divided by the seats (4 for padel and badminton, 2 for tennis and squash). Fixed on the card. |
| **Card** | A game as one person sees it in their deck. |
| **Version** | One of up to three views of the same game, each shown to different people. All versions share their yeses ([§7](#7-one-game-several-versions)). |
| **Yes / No** | Swipe right / swipe left on a card. |
| **In** | A player who said yes to a game that has not filled yet. |
| **Momentum** | How many players are In on a game. |
| **Fills** | The moment the last seat says yes. The game is then **Booked** — or, at an On request club, *waiting for the club* until it confirms ([§11](#11-the-moment-a-game-fills)). |
| **Book-by** | The latest moment a card can still fill ([§5.4](#54-the-only-deadline-the-courts-book-by)). |
| **Cut-off** | The club's free-cancellation deadline, for example 24 hours before the game. A club setting. |
| **Rescue** | An open seat in a booked game that lost a player. |
| **Post** | A game a member creates by picking the hour and the court. Its players see it as a **Challenge**. |
| **Home** | The first tab of the bottom bar: your games. |

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
  group. Blocking somebody takes back your yeses where they are In, until the club confirms; your
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
  put on one court: **no block** either way, a **mutual gender preference**, and Levels inside
  the kind's **level window**, whose tolerance per kind is the live ruleset's.
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
score, no weight and no toggle — what is new is the assembly (people × hour × court).

### 5.2 What a card promises

A card promises **a court at a club at an hour** — "Bonarka Arena, Sat 17:00" — not a court
number. The number is given when the game is booked. If Bonarka has four courts free at
17:00, four different cards can fill without colliding.

- Only when the **last** court at that club and hour goes do the other cards on it lose their
  court. A card then moves to another court number at the same club and hour if there is
  one, and nobody's yes changes. Otherwise the card disappears, and the players who were In
  are dealt a new card first ("You three were In — Sat 18:00?").
- The **price is fixed on the card**. A club changing its prices affects only new cards.

### 5.3 Keeping the deck clean

- The same people never appear twice in one batch at different hours; only their best hour
  shows.
- A card you swiped left never comes back.
- The same court hour can appear on cards with different people. That is expected.
- You are never dealt a card at an hour where you already have a game.

### 5.4 The only deadline: the court's book-by

A card lives until its court's **book-by** time. Nobody chooses it; it comes from the club:

| Club works with Raketa as… | Book-by is… |
| --- | --- |
| **Only Raketa** | the club's release time: *N* days before the game (club setting, default 3), after which unsold courts go back to the club |
| **Instant** or **On request** | the game's start minus the club's minimum notice (default 2 h) |

There are **no answer windows, no restarts and no ceilings**. A card shows a countdown only
when its book-by is less than 24 hours away. At book-by an unfilled card simply disappears:
nothing was charged, the yeses expire, and nobody is told.

A card whose club **cut-off has already passed** (a last-minute game) says **No free
cancellation** on it before anyone swipes ([§12.3](#123-leaving-before-and-after-the-cut-off)).

---

## 6. The swipe

### 6.1 A yes

- A yes means: **"I'm in. If everybody on this game says yes, book it and charge my share."**
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
only the last seat (Q74) — shows a toast *"Booking in 10 s · Undo"* with a draining ring; the
money moves only when the ten seconds are up. Any other yes is only a vote, and you can withdraw
it free from **Fill in › You're In** until its game fills.

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
- **The court block** — *Day HH:MM · Club* (and the court number once booked), the share, and
  one state tag: **Court available** (your yes is a free vote), **Book it now** (your yes fills
  it) or **Booked** (a rescue). **No free cancellation** when the cut-off has passed.
- **The ribbon countdown** — only when the deadline is under 24 h: *21 h 00*, then *45 min*,
  coral under an hour (Q72).
- **The stamps** — I'M IN / NOT THIS TIME while dragging; **I'M IN · 32 zł** whenever the yes
  charges at once (Book it now, or a rescue). At an On request club the charge waits for the
  club ([§11](#11-the-moment-a-game-fills)), so its *Book it now* stamp carries no price.

### 8.2 The order

Within one group, one sport and one segment, cards are ordered by **how likely you are to
swipe right**:

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
   lists, first, **rescues** at that time you fit (**I'm in · 27 zł**, pays at once) and then
   **posts still filling** you fit (**I'm in**, free until it fills), so you can join instead of
   duplicating (Q79, Q93).
7. **Post — you're In** — disabled until a court is picked. There is no review card; posting is
   your yes. Guards, each explained under the button: a saved payment method (the setup opens
   if missing), at most 2 live posts, and your games per week (Q80).

### 9.2 What happens next

- Posting **is your yes**. Nothing is charged until the game fills.
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
- **I'm in · 30 zł** takes the seat and pays at once, because the game already exists; every
  rescue join gets the 10-second undo ([§6.5](#65-undo)), then **It's a game!**, and the game goes
  straight to **Home**.
- Two people go for the same seat at once: the first wins; the second is told immediately.
- **How long a seat stays:** until the cut-off, whatever the number of open seats (a doubles
  that lost three keeps all three open, because the leavers' refunds depend on them being
  taken). After the cut-off, until the start.

Games that are still filling are **never offered** in Fill in — they are offered only in decks,
and *You're In* lists only your own yeses. Otherwise nobody would need to swipe.

### 10.2 You're In

Your yeses in this group that have not filled yet — **picks, challenges and your own posts
only**; a rescue join goes straight to Home, because that game is booked (Q76). Each row shows
the club, the book-by (or *waiting for the club*), who is In as filled squares and the open
seats as dashed ones, and **Withdraw** (hidden while waiting for the club — leaving then happens
from the game details). The moment a game fills, it appears in **Home** and leaves this list —
except at an On request club, where it also stays here, marked *waiting for the club*, until the
club answers.

---

## 11. The moment a game fills

When the last yes lands (after the 10-second undo, when it applies):

1. **Everyone pays together, or nobody pays** ([§12.2](#122-when-a-game-fills)).
2. The court is booked with the club and gets its number. At an **On request** club, the game
   first waits for the club to confirm (within the club's time to confirm, 30 minutes by
   default); nobody pays until it does ([§16.3](#163-three-ways-to-work-with-raketa)).
3. The player whose yes filled it sees a full screen **It's a game!** — the faces and one word,
   with **Open game** and **Later**.
4. Everyone else gets **It's a game! · you paid 30 zł** and the game appears in their **Home**,
   marked new until opened. Each player gets an email receipt from the club, also kept in
   You › Payments.
5. At the same moment:
   - every version and every card of that game disappears;
   - the players' other yeses at that hour are withdrawn;
   - one court at that club and hour leaves the pool;
   - a player who reached their games per week has their other yeses that week paused.
6. The game's **chat** opens, with the players as members.
7. The **sides** are drawn for the most even game.

---

## 12. Money

### 12.1 The model

- **The club is the seller.** It is named on every payment screen, receipt and bank statement
  ("paid to Bonarka Arena"). It pays the card processing fee on its sales, as it does at its own
  terminal. Raketa takes **no fee** and pays none.
- **Money goes from players to the club through Raketa** — never from one player to another,
  and no player ever pays another player's share.
- **Nothing is charged until a game exists.** A yes costs nothing; so does a card that never
  fills.
- **The share** is the court's price divided by the seats, fixed on the card.

### 12.2 When a game fills

- Every player's saved method is charged **automatically — no screen, no tap** — exactly like a
  subscription: the screen before the first yes was the permission.
- It is **all or nothing**: each payment is authorised first and all are taken only if all
  succeeded, seconds apart. If one fails, **nobody pays**.
- **If your payment fails** (the card is declined, or your bank asks you to confirm — rare, but
  allowed even with permission on file): nobody is charged, your seat reopens, and you are told
  *"Confirm your payment to keep your seat."* Confirming in the app is your yes again; if it goes
  through before somebody else takes the seat, the game fills and everyone else is charged
  automatically.

### 12.3 Leaving, before and after the cut-off

| When | What happens to your money | Your seat |
| --- | --- | --- |
| **Before the club's cut-off** | Refunded **at once**, minus the card fee (about 1.60 zł on a 40 zł share) | Becomes a rescue |
| **At the cut-off, if a seat is still empty** | The game is **called off**. Everyone still in is refunded **in full** (the club absorbs those fees — it is its own free-cancellation rule) | The court goes back to the club |
| **After the cut-off** | Refunded (minus the card fee) **only when someone takes your seat**; otherwise not | Becomes a rescue until the start |
| **A last-minute game** (filled after its cut-off) | As *after the cut-off*, from the start. Its card said **No free cancellation** | — |

How long a refund takes to arrive is shown when it is issued: **BLIK within hours, cards up to
two weeks**.

### 12.4 Payment methods

- **At launch: cards, Google Pay, and Apple Pay** — Apple Pay only if it passes a real test
  (Stripe documents saving Apple Pay for regular recurring charges; Raketa's are one-off). The
  setup shows only the phone's own wallet: Apple Pay on iPhone, Google Pay on Android (Q82).
- **BLIK:** Stripe's BLIK page says a saved BLIK can be charged later without the player
  present; another Stripe page contradicts it, and the recurring version is a preview. **Confirm
  with Stripe before building.** If confirmed, BLIK launches beside cards; if not, it follows
  when Stripe opens it. See also open item [O1](#21-open-items).
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

The terms, in full:

> Your card (or BLIK) is saved. When a game you said yes to fills, the club it is played at
> charges your share at once — the court's price divided by the players. You can leave free
> until the club's cut-off and are refunded at once, minus the card fee. After the cut-off your
> seat is offered to others, and you are refunded (minus the fee) when someone takes it. If a
> game is still missing a player at the cut-off, it is called off and everyone still in gets
> everything back. Refunds reach BLIK within hours and cards within up to two weeks.

The wording is reviewed by a lawyer before launch. **A note for that review (Q99):** the card,
the details and the booking email don't say *free to leave*; they say the sum a leaver gets
back (*38,40 zł back if you leave by Wed 19:00*). The review should word the leave the same way:
the share back less the card fee, until the club's cut-off, and not *free*. The app asks again
only if the bank changes the card's brand (Visa → Mastercard), because a changed brand cannot be
charged without it.

### 12.6 The club's money

The club is paid **after the game is played**, as a normal payout. Until the start, refunds can
still happen, so the money stays where it can pay them. Wording in the app: *"the club's payment
is on its way"*, never *"the club is paid"*.

---

## 13. Leaving a game

**Leave the game** is at the bottom of the game details. A sheet says what it will cost
**before** you confirm:

| When | The sheet says |
| --- | --- |
| Before the cut-off | *"You'll be refunded 38,40 zł now (the 1,60 zł card fee isn't returned). Your seat is offered to others. On your record only if the game is then called off."* |
| After the cut-off | *"Your seat is offered to others. You'll be refunded 38,40 zł when someone takes it; if nobody does, you won't be. On your record if nobody takes it."* |
| Waiting for the club | *"Nobody has paid yet. Leaving withdraws your yes."* The request to the club is cancelled, the booking is called off with nobody paid, and the others are dealt the same court hour again first, your seat open — as when a club refuses. |
| After the start | No button. |

The others in the game are told *"Kuba left — the seat is open"*, in the chat and by
notification, with the new state of the game.

---

## 14. After booking

### 14.1 Home and the statuses

A game card in **Home** (and the status row of its details) shows one status. **Planning, Game
on, Needs a player** and **Held** are gone: the booking *is* the plan.

| Status | When | Money line |
| --- | --- | --- |
| **Waiting for the club** | An On request club has not confirmed yet | Before the club's time to confirm runs out: *Bonarka answers by 20:45 · Nobody pays until it confirms*. After: *Nobody pays until Bonarka confirms* |
| **Booked** | Full and booked | Before the cut-off: *Paid · 30 zł · 28,55 zł back if you leave by Sat 17:00*. After: *Paid · 30 zł* |
| **Seat open** | Someone left | Before the cut-off: *1 seat open · fills by Sat 17:00 or the game is off and everyone is refunded*. After: *1 seat open · offered to others · the game goes ahead* |
| **Needs result · Confirm the result · Counted · Uncounted · Never played** | Unchanged from today | — |
| **Called off** | A seat was empty at the cut-off, the club cancelled, the club refused a request or didn't answer it, or a player left while it waited for the club | The reason, and *refunded 30 zł* or *nobody paid* |

*Back if you leave by* names what leaving before the club's cut-off gives back: the share less
its card fee (1,45 zł on 30 zł), the sum the leave sheet then states ([§13](#13-leaving-a-game)),
so the card never promises what the sheet takes back (Q99). The leaver still bears the fee (Q47).
At the cut-off the clause leaves the line.

*Answers by* names the end of the club's **time to confirm** after the game filled
([§11](#11-the-moment-a-game-fills)): the time its desk is given, in the request email's *Answer
by …* and the countdown on its Bookings page ([§16.8](#168-answering-a-request-on-request)), so
the players can tell five minutes from an hour (Q98). Once that time has passed the clause leaves
the line, as *… back if you leave by …* leaves at the cut-off, until the game reads *Called off ·
no answer*. It moves no money.

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
  the court facts (**WHERE** club · court · distance, **DAY**, **TIME** start–end, the money row).
- **The balance forecast**, as today. Hidden while a seat is open.
- **On the day:** a **QR code** to show at the club desk, with a short code under it
  ([§15.1](#151-check-in-at-the-club)).
- **Leave the game** ([§13](#13-leaving-a-game)).

The same screen serves two more readers (Q75, Q96):

- **Before the game is booked** (tapping a card, its **i**, or a You're In row): the status row
  reads *Filling · 2 of 4 in* or *Waiting for the club*; WHERE names the club with no court
  number; the money row reads *"30 zł if it fills · book by Sat 13:00"* — while waiting for the
  club, the share with *nobody pays until Bonarka confirms* and, until its time to confirm runs
  out, *Bonarka answers by 20:45* ([§14.1](#141-home-and-the-statuses)); the overlap grid and one
  plain paragraph on what a yes means follow; the actions are **I'm in / Not this time**, or
  **Withdraw** if you are In — while waiting for the club, **Leave the game** with its sheet
  ([§13](#13-leaving-a-game)). No Chat.
- **A rescue, seen by a member who is not in it** (a Seat open card or a Seats to fill row):
  the paid tiles, the dashed *You?* tile, the court number, and **I'm in · 27 zł**. No Chat, no
  Leave.

### 14.3 The chat

- **One chat per game.** It opens **when the game is booked** — at an On request club, when the
  club confirms — because there is nothing to talk about before, and yeses are silent.
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

### 15.1 Check-in at the club

- Every player's game details carry a **QR code on the day**, with a short code under it.
- Clubs that choose to can scan it on the club website's **Check in** page (phone or tablet
  camera), or type the code. It doubles as proof of the booking at the desk.
- A scan marks the player as **there**: they can never be reported as a no-show.
- Check-in is **optional per club**, and **money never depends on it** — the club is owed the
  court whether people come or not.

### 15.2 Results and sportsmanship

Unchanged from today: *we played*, the score, the confirmation, counted or friendly by kind, the
sportsmanship stars.

### 15.3 No-shows

- When entering the result, the players who were there can tap **"Kuba didn't come"**. Kuba has
  **24 hours** to dispute it; after that it is confirmed. A player checked in by the club cannot
  be reported.
- He already paid, so there is no debt, and nobody is refunded — the court was used.
- The game does not count and no levels move. A confirmed no-show is the strongest mark on a
  record.
- If nobody enters anything, the game ends **Never played**, as today.

### 15.4 The record

| Never on the record | A mark | The strongest mark |
| --- | --- | --- |
| Swiping left · withdrawing a yes · a card or post that never filled · a failed payment you fixed · leaving before the cut-off when your seat is taken or the game still plays · a game the club cancelled | Leaving before the cut-off when your seat stays empty and the game is called off because of it · leaving after the cut-off when nobody takes your seat | Not turning up |

The reliability score stops counting *answers challenges* (challenges no longer wait for
answers) and counts *keeps booked games* from the table above.

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
| **Overview** | The club's landing page | The setup checklist until the club is live ([§16.2](#162-getting-ready-to-take-bookings)); after that, **only what is waiting for the club's answer** (Q86, Q95). The statistics that will live here later are out of scope. |
| **Details** | Name, district, city, sports, map point | Unchanged |
| **Administrators** | Invite and manage Administrators | Unchanged |
| **Groups** | The club's official groups, their *Games* figure (reads 0 today) and Hand over | *Games* counts the games actually booked in each official group; the "other clubs' courts" setting links from here ([§16.13](#1613-official-groups-and-administrators)) |
| **Courts & prices** | — | **New** ([§16.4](#164-courts), [§16.5](#165-hours-and-prices)) |
| **Raketa settings** | — | **New** ([§16.3](#163-three-ways-to-work-with-raketa), [§16.6](#166-settings)) |
| **Bookings** | — | **New** ([§16.7](#167-bookings)–[§16.9](#169-cancelling-a-booking)) |
| **Check in** | — | **New**, only when the club checks players in ([§16.10](#1610-check-in)) |
| **Money** | — | **New** ([§16.11](#1611-money)) |

### 16.2 Getting ready to take bookings

A club's courts reach players' decks only when **all five** are done. The Overview shows them as a
checklist, says which one is missing, and drops the checklist once the club is live (Q95):

1. **Connect payments** — the club's Stripe account, through **Stripe's own hosted sign-up** (the
   club is sent to Stripe and comes back; company data with REGON, the representative and owners,
   a Polish IBAN). The club gets its **full Stripe dashboard** for payouts and disputes. The club
   is the seller, so without it nothing can be charged (Q86).
2. **Choose how you work with Raketa** — Only Raketa, Instant or On request ([§16.3](#163-three-ways-to-work-with-raketa)).
3. **Add your courts** ([§16.4](#164-courts)).
4. **Set hours and prices** ([§16.5](#165-hours-and-prices)).
5. **Check the settings** — cut-off, release lead or minimum notice ([§16.6](#166-settings)).

Until then the club still exists for search, groups and Administrators exactly as today.

### 16.3 Three ways to work with Raketa

Each club chooses **one way for the whole club** (Q12). It can change it later; the change applies
to hours not yet booked ◇.

| | **Only Raketa** | **Instant** | **On request** |
| --- | --- | --- | --- |
| Who sells the court | Raketa alone, until the release time | Raketa **and** the club's own desk or system | Raketa **and** the club's own desk or system |
| When a game fills | Booked at once | Booked at once; the club promises to honour it and to close hours it sells elsewhere | The club confirms within the time it set (default 30 min); nobody pays until it does |
| Book-by | The release time (default 3 days before) | Start minus minimum notice (default 2 h) | Start minus minimum notice (default 2 h) |
| After the release time | Unsold hours return to the club and leave Raketa | — | — |
| If it goes wrong | — | A double sale: the club cancels ([§16.9](#169-cancelling-a-booking)) | Refused or no answer: nobody paid; the players get a new card first |

A future live link to the club's own booking system is the **Instant** way kept up to date
automatically; nothing else about bookings changes for the club.

### 16.4 Courts

- The club lists its courts ◇: a **name** as the club uses it (*Court 2*, *Kort centralny*), **one
  sport** per court, and **indoor or outdoor** (shown on the card, because it matters to players).
- A court can be switched **off** (not offered to Raketa) without deleting it.
- Players never pick a court number. A card promises "a court at this club at this hour"; the
  number is **given at booking** — the first free court of that sport at that hour ([§5.2](#52-what-a-card-promises)).
- The club can **move** a booked game to another free court of the same sport at the same hour
  (a court needs repair, a better fit for the desk) ◇. Players see the new number; nothing else
  changes.

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
- **Instant clubs** must close, straight away, every hour they sell at their own desk. The calendar
  makes that one click per hour ◇.

### 16.6 Settings

| Setting | Default |
| --- | --- |
| How we work with Raketa: Only Raketa · Instant · On request | — |
| Release lead (Only Raketa): days before the game unsold courts return to us | 3 days |
| Free-cancellation cut-off (players leave free until it; a game still short at it is called off) | 24 h before |
| Minimum notice (Instant / On request): the latest a Raketa game can book | 2 h before |
| Time to confirm (On request) | 30 min |
| Offer our groups other clubs' courts when ours are full ([§4.3](#43-courts)) | off · 10 km |
| We check players in ([§16.10](#1610-check-in)) | off |
| Pause Raketa bookings ([§16.15](#1615-pausing-or-leaving-raketa)) ◇ | off |

A changed setting applies to games booked **after** the change; a booked game keeps the cut-off it
was booked with ◇.

### 16.7 Bookings

One page, by day, listing every Raketa booking at the club ◇:

| Column | What it shows |
| --- | --- |
| **When · court** | Day, hour, court number (with **Move** to another free court) |
| **Sport · kind** | Padel · Competitive, Tennis · friendly… |
| **Players** | Each player's name, **paid ✓**, and **checked in ✓** when the club checks in |
| **Status** | See below |
| **Money** | Court price, collected, refunded |
| **Where it came from** | The group it was booked in (official or player group) |

The statuses the club sees:

| Status | Meaning for the club |
| --- | --- |
| **Waiting for you** | On request only: a full game asks for the court; **Accept** or **Refuse** before the countdown ends |
| **Booked** | Full and paid; before the cut-off it can still be called off if a player leaves and nobody replaces them |
| **Seat open** | A player left; Raketa is finding a replacement. Before the cut-off: if nobody is found, the game is called off at the cut-off and the court comes back to the club |
| **Called off** | With the reason: short at the cut-off, cancelled by the club, refused, or no answer. Everyone was refunded or nobody paid; the hour is free again |
| **Played** | The hour has passed |

Filters: all · waiting for you · seat open · called off
([the-screens.md B4](the-screens.md#b4-bookings)) ◇.

### 16.8 Answering a request (On request)

- A **Waiting for you** booking shows the players, the hour, the sport, the price and the countdown.
- **Accept** books it: everyone is charged at that moment, all together or not at all
  ([§12.2](#122-when-a-game-fills)), and a court number is given.
- **Refuse** (with an optional reason ◇) or **no answer** in time: nobody paid, the booking reads
  *Called off · refused* or *Called off · no answer*, and the players are dealt a new card first.
- While a request waits, the hour stays reserved for it; nobody else is offered that court.
- Because the window is short, the club is alerted by **email** as well as on the website
  ([§16.12](#1612-what-the-club-is-told)). A club that cannot watch the website during its hours
  should choose Only Raketa or Instant.

### 16.9 Cancelling a booking

- **Cancel** on a booking, with a reason ◇: *weather*, *repair*, *double booking*, *other*.
- Everyone is **refunded in full**, it goes on **nobody's record**, and the same players are dealt a
  new card first. They are told the club cancelled, with the reason.
- The card fees on those payments are not returned by Stripe; as the seller, **the club bears
  them** (Q44).
- Not possible once the game has started ◇.
- An Instant club that sold the hour at its desk too cancels here with *double booking*.
- Raketa keeps count of a club's cancellations; frequent cancellations are a quality matter
  between Raketa and the club, not something players are shown ◇.

### 16.10 Check in

- Only for clubs that switched on **We check players in**.
- The **Check in** page opens the device camera (phone or tablet) to scan a player's QR code, or
  takes the **short code** typed by hand.
- It shows the booking and the player, and marks the player **checked in**. A code for another day
  or another club is refused with that reason ◇.
- A checked-in player can never be reported as a no-show. A player who is not scanned is
  **unknown**, never "absent": the club's scan is evidence, not a verdict ([§15.3](#153-no-shows)).
- **Money never depends on it.** The club is paid whether people come or not.

### 16.11 Money

- **The club is the seller.** Its name is on the players' receipts and bank statements.
- **Collected:** each booking's shares, taken from the players when the game filled (or when the
  club accepted a request).
- **Refunds happen automatically** — a leaver before the cut-off, a leaver whose seat was taken
  after it, a game called off, a club cancellation. The club never refunds anybody by hand ◇.
- **Fees:** Stripe's card fee on each payment, paid by the club as at its own terminal (about
  1.5 % + 1 zł per share on EEA cards). Fees on refunded payments are not returned.
- **Payouts:** after the game is played, to the club's IBAN, as normal Stripe payouts. Refunds
  before the start are paid from that money, which is why it waits (open item O2).
- **The Money page** ◇: per booking — collected, refunded, card fee, net; the list of payouts; a
  link to the club's own Stripe dashboard for the detail.
- **Disputes** (a player's bank reverses a payment): handled through Stripe on the club's account,
  where the dispute is raised; the club can answer with the booking's evidence (the check-in, the
  result). Stripe covers a negative balance under Raketa's setup ◇.
- **Receipts and invoices for the club's own accounting** (Polish fiscal-receipt and invoicing
  rules for online sales) are the club's, as the seller — open item O5.

### 16.12 What the club is told

On the website (badges on Bookings and Overview), and by **email** where marked ◇:

| Event | Email |
| --- | --- |
| **A request is waiting for you** (On request), with the countdown | yes, at once |
| A new booking | a daily summary |
| A booking lost a player (Seat open) | no |
| A game was called off at the cut-off — the hour is free again | yes, at once |
| A payout was sent | yes |
| Stripe needs something from you (account details, a dispute) | yes, at once |

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
- **About players** ◇, the club sees only what running the court needs: each player's **name**, whether
  they **paid**, and whether they were **checked in**. No email, no phone, no level, no record, no
  access to the game's chat. The club cannot message players; everything players need to know comes
  from Raketa.

### 16.15 Pausing or leaving Raketa

- **Pause Raketa bookings** ◇: no new cards are built on the club's courts. Games already booked are
  played as booked; games still filling keep their cards until their book-by and can still book.
- **Leaving Raketa** ◇ is a pause plus disconnecting payments once every booked game has been played
  and every payout sent. Disconnecting payments earlier is refused while bookings remain.

### 16.16 The club's edge cases

| Situation | What happens |
| --- | --- |
| The desk sold an hour Raketa had already booked (Instant) | The club cancels with *double booking*: full refund, nobody's record, the players get a new card first. |
| The club forgets to answer a request | It expires: nobody paid, *Called off · no answer*, the players get a new card first. |
| The club closes an hour that has cards on it but no booking | The cards move to another free court at that hour or disappear; nobody was charged. |
| A court breaks on the day | **Move** the game to another free court; if there is none, **Cancel** with *repair*. |
| The club changes a price after cards were dealt | The dealt cards and booked games keep their price. |
| A player leaves after the cut-off and nobody replaces them | The game goes ahead short; the club has been paid in full. |
| A game is still short at the cut-off | Called off; the players are refunded; the hour is free again for the club. |
| A player's bank disputes a payment | Handled on the club's Stripe account; the check-in and the result are the evidence. |
| The club's Stripe account needs attention | New cards stop until it is fixed; booked games are unaffected. |
| The club wants to stop | Pause, then disconnect once everything booked has been played and paid out. |

### 16.17 The pages at a glance

The club website keeps its **top bar** (Q90):

```
Top bar:  Overview · Bookings · Courts & prices · Money · Groups · Administrators   [Club name ▾]
                                                                                    ├ Details
                                                                                    └ Raketa settings
Overview ........ setup checklist until live · then only what is waiting for your answer
Bookings ........ by day · Accept / Refuse · Move · Cancel · [Check in] button (if the club checks in)
Courts & prices . courts · weekly hours · exceptions · price bands
Money ........... per booking · payouts · link to the Stripe dashboard
Raketa settings . way of working · cut-off · release · notice · confirm · pause
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
  and **RECEIPTS** (charges and refunds, the club named as the seller).
- **Notifications** — the always-on list and the three choices ([§17.2](#172-notifications)).

**Your week** stays in *Finding players* ([§4.2](#42-weekly-hours-availability)).

### 17.2 Notifications

Delivered by **push** (built with this feature, through Expo's push service: free on Android;
on iPhone it needs the Apple Developer membership, which publishing the app needs anyway), by an
**in-app banner** when the app is open, and in a **recent notices** list. Every notice about
money is **also emailed** — the standard for bookings and payments (Q85, Q94):
*It's a game! · you paid* (the booking confirmation), *Game called off · with the refund*,
*You've been refunded* and *Confirm your payment to keep your seat*.

| Notification | Setting |
| --- | --- |
| **It's a game! · you paid 30 zł** | always on |
| **Confirm your payment to keep your seat** | always on |
| **Game called off** (with the reason and the refund) | always on |
| **Someone left your game** | always on |
| **You've been refunded** (your seat was taken) | always on |
| **The club confirmed / couldn't take it** (On request) | always on |
| **Your post didn't fill** | always on |
| **You complete it** — a card needs only you | on by default · at most 1 a day, bundled |
| **Challenges for you** — a member's post names you | on by default · at most 3 a day, bundled |
| **Fill in alerts** — a booked game you fit needs one more | off by default · at most 3 a day |

No notification is ever sent for a single swipe.

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
| Book-by | release time (Only Raketa) or start − minimum notice |
| Club defaults | release 3 days · cut-off 24 h · minimum notice 2 h · confirm 30 min · other clubs 10 km |
| Player group reach | home club + 10 km |
| No-show dispute | 24 hours |
| Card fee (club pays; a refunded leaver bears it) | about 1.5 % + 1 zł per share on EEA cards |

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
| A payment fails when the game fills | Nobody pays; your seat reopens; confirm your payment to take it back ([§12.2](#122-when-a-game-fills)). |
| Your card's brand changes | You are asked to accept the terms again; until then, a game filling fails your payment as above. |
| The poster withdraws | The game carries on if others are In; the ribbon drops the name. |
| A post or a picked card reaches book-by unfilled | It disappears; nobody paid; a poster is told. |
| A doubles loses three players before the cut-off | All three seats stay rescues until the cut-off; then the cut-off rule applies. |
| A game is still short at the cut-off | Called off; everyone still in refunded in full; leavers keep their earlier refund. |
| Someone leaves after the cut-off and nobody takes the seat | The game goes ahead short; it ends **Uncounted · a seat was empty**. |
| A last-minute game | No free cancellation from the start; the card said so. |
| An On request club refuses or does not answer | Nobody paid; the same people are dealt a new card first. |
| An Instant club double-sold the court | The club cancels; full refund; a new card first; nobody's record. |
| The club cancels a booked game | Called off; full refund; nobody's record; a new card first. |
| The club changes its prices | Only new cards carry the new price. |
| You leave a group | Your yeses there are withdrawn. Your booked games stay. |
| Somebody you blocked | Never on a card with you. Your yeses where they are In are taken back, until the club confirms. Your booked games stay. |
| Someone doesn't turn up | Reported in the result; 24 h to dispute; strongest mark; no levels move ([§15.3](#153-no-shows)). |
| The club checked someone in | They cannot be reported as a no-show. |

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

---

## 21. Open items

To settle with Stripe (and a lawyer) before building payments:

- **O1 — BLIK with the club as the seller.** Because the club is the seller, each payment is
  made on the club's own Stripe account, with the player's card copied there for that payment.
  Stripe copies **cards only** — not BLIK. Ask Stripe: can a saved BLIK be used for a club's
  payments (for example, one approval in the bank app per club), and is saved BLIK available to
  Raketa at all? If neither, BLIK waits.
- **O2 — Keeping the club's money until after the game.** Refunds before the start come out of
  the club's Stripe balance. Confirm how Raketa can keep the club's payouts until after the game
  when the club is the seller.
- **O3 — The terms' wording** ([§12.5](#125-saving-a-payment-method-and-the-terms)), naming the club as
  the one charging, reviewed by a lawyer. The review should word the leave as the card does
  (Q99): the share back less the card fee, until the cut-off, and not *free*.
- **O4 — Apple Pay** for one-off charges without the player present: test before launch.
- **O5 — The club's receipts and invoices.** The club is the seller, so the Polish rules on fiscal
  receipts and invoices for online sales apply to the club. Confirm with a lawyer or accountant what
  a club needs (and whether Raketa should give it an export per booking) before the first club goes
  live ([§16.11](#1611-money)).
- **O6 — Apple Developer membership** (a human step): iPhone push needs it, as does publishing the
  app. Until it exists, iPhones get the in-app banner, the recent-notices list and the emails.
- **O7 — A Stripe test account** (a human step): its test keys go into `.env` by a person, never by
  an agent. Until then, everything runs on the fake payments adapter.

---

## 22. What this replaces

### 22.1 From the PDFs, removed on purpose

- A hold on the player's money at every swipe; the 5-second background queue built around it;
  the three-shares ceiling.
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

Researched from Stripe's official documentation on 2026-09-28. Every line has its source.

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
  an idempotency key. When every seat is `requires_capture`, capture them all; if any fails,
  cancel the others — cancelling an uncaptured payment costs nothing.
  [place-a-hold](https://docs.stripe.com/payments/place-a-hold-on-a-payment-method),
  [refunds](https://docs.stripe.com/refunds)
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

**Refunds and payouts**

- Refunds are free to issue, but the original processing fee is not returned.
  [pricing FAQ](https://stripe.com/en-pl/pricing)
- With direct charges, refunds come out of the club's balance and stay pending when it is empty
  — see open item O2. Default payouts in Poland: first after 7 days, then 3 business days.
  [connect charges](https://docs.stripe.com/connect/charges#refunds),
  [payouts](https://docs.stripe.com/payouts)

**Fees (Poland, standard):** EEA cards 1.5 % + 1.00 zł (premium 1.9 %), BLIK 1.6 % + 1.00 zł,
dispute 90 zł, no fee for cancelling an uncaptured payment.
[pricing](https://stripe.com/en-pl/pricing)

**Robustness**

- Idempotency keys may be forgotten after 24 h: Raketa's own records must prevent duplicates.
  [idempotent requests](https://docs.stripe.com/api/idempotent_requests)
- Webhooks: `setup_intent.succeeded/setup_failed`, `payment_intent.amount_capturable_updated`,
  `payment_intent.payment_failed`, `payment_intent.canceled`, `charge.captured`,
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
| When you pay | When you **join**, charged at once | When the game **fills** — nothing for games that never form |
| Court | Booked in stages (2 players > 12 h before, 3 > 4 h, 4 always) | Booked when the game fills |
| Not full | Cancelled about 1 h before; everyone refunded | Cards simply expire at book-by; nobody ever paid |
| Leaving | Free until 24 h before; then locked — only the club can swap | Free until the club's cut-off; after it, the seat is a rescue and you are refunded when it is taken |
| A queue for freed seats | None (Polish users ask for one) | Rescues in Fill in, the deck and alerts |
| Poland | Cards, Apple Pay, Google Pay; no BLIK | Cards and wallets; BLIK when Stripe confirms |
| Player fee | 20 %, capped 1.24–3.99 zł per seat | None |
| No-shows | Reported by others within 7 days; charged the court as a debt | Already paid; reported in the result, 24 h to dispute; optional club check-in |

---

## Appendix C — Decision log

| Q | Decision |
| --- | --- |
| 1 | Support both clubs that give Raketa courts to sell alone (release lead set by the club) and clubs that keep selling. → Q12 |
| 2 | A yes is conditional and charged only when the game is complete; no holds on a swipe. |
| 3 | A Picked-for-you card is a shared proposal; a yes holds no court; In tags; a short last-seat line. |
| 4 | The deck shows games that name you; Fill in is separate. → refined by Q38 |
| 5 | Raketa earns nothing for now; the share is the court price ÷ seats. |
| 6 | A booked group game lives like today's games (chat, details, result, stars, record). |
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
| 24 | A failed payment at the fill: nobody pays, the seat reopens, the player can take it back. |
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
| 35 | The moment a game fills. |
| 36 | The statuses. → updated by Q39/Q58/Q98/Q99 |
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
| 47 | A refunded leaver bears the card fee. |
| 48 | → replaced by Q59 |
| 49 | Versions at half-In. |
| 50 | Open seats stay until the cut-off, however many. |
| 51 | The deck order. |
| 52 | One game, shared yeses across versions. |
| 53 | Posts are not in Fill in; a Challenges alert, on by default. |
| 54 | Pay when the game fills; free to leave until the cut-off (B1), after researching Playtomic. |
| 55–56 | → replaced by Q58/Q59 |
| 57 | BLIK: confirm with Stripe first; cards and wallets launch either way. |
| 58 | The money timeline. |
| 59 | The screen before the first yes. |
| 60 | Versions are not a card type; thin posts; singles versions. |
| 61 | Nobody confirms anything at the fill; receipts by email and in the app. |
| 62 | No-shows reported in the result, 24 h to dispute; optional QR check-in that never gates money. |
| 63 | Price fixed on the card; club cancellations; leaving a group; blocks; the empty deck. |
| 64 | This document goes in the repo, the illustrated HTML on the Desktop; then the ADR, then the UI document, then building. |
| 65 | A 10-second undo, only on the yes that fills a game. → amended by Q74 |
| 66 | The club website's bookings and check-in pages. |
| 67 | After the session, on request: a dedicated club-website section ([§16](#16-the-club-website)). Its **◇** items were filled in while writing, not grilled. |
| 68 | FRIEND shows only once a friends feature exists. |
| 69 | The *asked / no answer yet* tag is removed. |
| 70 | Rows are sides; the *vs* line and the bar name the same sides, yours on the left; a rescuer takes the leaver's seat and side. |
| 71 | Card and posting grid use ranges Morning 07–12, Afternoon 12–17, Evening 17–23; bright / dim / ringed; today's High / Good / Slim grading. |
| 72 | The stamp shows the price when the yes charges at once; countdown *21 h 00* / *45 min*, coral under 1 h; tile → record, card or **i** → details. |
| 73 | A week at its games-per-week cap is not dealt, with a slim line at the top of the deck. |
| 74 | Every action that moves money gets the 10-second undo, including every rescue join (amends Q65). |
| 75 | Game details serve a game that is still filling. |
| 76 | You're In holds picks, challenges and posts; a rescue join goes to Home. |
| 77 | The posting grid is 7 days × 3 ranges, grouping real hourly overlaps. |
| 78 | The posting level range defaults to the engine's range for the kind, narrowed in 0,05 steps. |
| 79 | Joining someone else's post from the sheet is allowed if you fit; *I'm in*, no court number. |
| 80 | Gender filters count members with a gender set; Mixed pairs only in doubles; sport chips; the draft is kept; three guards on Post. |
| 81 | *Your week* is 7 × 16 hours, tap and drag, no templates, onboarding and You. |
| 82 | Payment setup order: choose → card details (Stripe's fields) → accept the terms → confirm with your bank; only the phone's wallet shows. |
| 83 | Change keeps the old method until the new one is saved; Remove only with nothing live; LIVE YESES · n; chips Off · 35 · 45 · 60 zł. |
| 84 | Screens missing from the mocks are built in their style (Home cards, details additions, chat, Undo toast, It's a game!, intent question, payment interstitial, empty states). |
| 85 | Push notifications are built (free except the Apple membership publishing needs anyway), with money notices also emailed. |
| 86 | The club website design is mine as proposed; the Overview shows only what waits for an answer. |
| 87 | Backend shape: the pool is first-class; new event-sourced contexts; availability becomes hours; payments behind a port with a fake adapter. |
| 88 | Every piece of data is seeded through the real use cases, with fake payments; Stripe test keys are a human's. |
| 89 | Order: ADR → documents → PRD and tickets → building; the product owner picks the tickets and nothing is implemented here. |
| 90 | The Competitive / For fun switch is added to Games and stays on Friends; peeking cards fade; the club website keeps its top bar. |
| 91 | A tile without IN is a normal tile. |
| 92 | A posting-grid cell counts the best fits free together at the best hour. |
| 93 | The slot sheet's *Already happening here* lists rescues first, then posts still filling; the red dot covers both. |
| 94 | Push now; every money event also emailed. |
| 95 | The setup checklist sits on Overview until the club is live. |
| 96 | The empty deck keeps today's cards plus Post a game; rescue details for non-members; public site unchanged; payment not in onboarding; the product owner runs to-spec and to-tickets. |
| 97 | (2026-10-05, amends Q13) No live-yes cap: games per week and one game per hour already bound what a yes can book. The LIVE YESES list stays. |
| 98 | (2026-10-09, amends Q36; ruled by the product owner from story S-01A, [#605](https://github.com/Raketa02/Raketa/issues/605), F-REQUEST-43.1) *Do the players see when the club must answer?* Yes: while their game waits for its club, the Home card and the details show the deadline the desk is given (*Bonarka answers by 20:45 · Nobody pays until it confirms*), and it disappears once the deadline passes. It moves no money. Evidence: the desk's email says *Answer by …* while the players read only *Waiting for the club*; Playmore's full game reads *Skład pełny · potwierdzimy o {time}*. |
| 99 | (2026-10-09, amends Q36's *Booked* money line; ruled by the product owner from story S-01A, [#605](https://github.com/Raketa02/Raketa/issues/605), F-LEAVE-20.1) *Does the card say "free to leave"?* No. The card, the details and the booking email say the sum: *38,40 zł back if you leave by Wed 19:00*, dropping to *Paid · 40 zł* at the cut-off as before. The booking email (*It's a game! · you paid 40 zł*) says *You can leave until Wed 19:00 and get 38,40 zł back at once (the 1,60 zł card fee isn't returned).*, with the day and time written as the email writes them; a game that filled after its cut-off keeps its sentence. Q47 stands: a refunded leaver still bears the card fee, and the club is still the seller that pays its card fees (Q44). The terms (§12.5, with a note to the lawyer's review, and O3), the deck's *no free cancellation*, the club's *Free-cancellation cut-off*, the line under *Leave the game* and the leave sheet keep their words. Evidence: Playtomic reviewers in Germany and Spain complain of a "free" cancellation that cost a fee (*Die App verlangt 0,95 € Bearbeitungsgebühr!*); Kraków's own systems say *bezpłatnie* and keep a fee (tenis4U keeps 2 %, Playmore its service fee); Playmore's preview says *ze zwrotem wpisowego*. |
| 100 | (2026-10-09, amends §14.3's *reached only from the game details*, set by the consistency pass [#531](https://github.com/Raketa02/Raketa/issues/531), and ADR-0189 §6; ruled by the product owner from story S-01A, [#605](https://github.com/Raketa02/Raketa/issues/605), F-HOME-15.1) *Does the Home card's bubble open the chat?* Yes: straight over Home, with Back to whichever screen opened it (Home from the bubble, the details from their *Chat*). The room stays only the conversation, with no way into the details. Opening it from the bubble clears *new*, as opening the details does. The bubble shows when it did before (the chat is open; never on *Waiting for the club* or *Called off*) and carries no count until the unread count owed to the details' *Chat · n* is built (F-HOME-21.1); then it shows the same number. Evidence: a chat icon is a button in every app a player uses, and Playtomic opens a match's chat from the match itself. |
