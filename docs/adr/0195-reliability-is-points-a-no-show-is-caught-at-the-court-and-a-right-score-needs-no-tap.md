# ADR-0195 — Reliability is points, a no-show is caught at the court, and a right score needs no tap

- **Status:** Accepted
- **Date:** 2026-10-11
- **Amends [ADR-0137](0137-a-result-is-the-record-that-a-game-happened.md)** in four places:
  - **§2's ends.** *Never played* retires, and a full booked game nobody recorded reads **Played ·
    no score** (§2). A game whose two scores name different winners gains an end of its own,
    **disputed** (§5).
  - **§4's acceptance grace.** An acceptance **settles at once** and closes the game, so no counter
    is taken after it. The six-hour grace retires (§5).
  - **§4's two standing proposals nobody accepts leave the game unscored.** They split: the **same
    winner** counts with the closer score, and **different winners** end disputed (§5).
  - **§4's flow** gains two edges: no score is taken **before the hour**, and a correction is
    refused once the **entry window** has closed (§5).

  §5's *no player is penalised for not entering or not agreeing a result* stands, and is now true
  of the figure as well as of the strand it was written about (§1, §5). *We will not arbitrate*
  stands.
- **Amends [ADR-0140](0140-a-player-score-is-what-the-platform-watched-and-two-strands-is-what-it-can-see.md)**
  in four places. **§2's ghost charged to the whole court** retires (§2). **§3's strands**, **§4's
  *no decay beyond the ratio*** and **§5's weights** become fixed prices in points over a 6-month
  rolling window (§1). §1's *no record of its own* stands.
- **Supersedes [ADR-0160](0160-a-results-strand-counts-answers-and-never-agreements.md).**
  *Answers about results* leaves the figure, and silence on a score costs nothing (§1, §5).
- **Amends [ADR-0159](0159-a-record-is-read-through-a-prior-disclosure-and-the-refusal-names-nothing.md)'s
  2026-09-08 amendment, *the two live strands*.** The record's reliability block is points, a band,
  *New* and four counts. The strand rows, their raw pairs and their figures leave the wire (§8).
- **Amends [ADR-0179](0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
  §2's *Player reliability* row.** The ring with the tone ladder's word and the strand rows become
  the figure, the band word, *New*, the four count lines and the filter's switch (§1, §6).
- **Amends [ADR-0189](0189-a-yes-books-a-court-and-the-club-is-the-seller.md)** §5 (the Booking's
  *check-ins*, the Game's *no-show report*) and §7 (the club website's **Check in**). Both go
  (§3, §4).
- **Extends [ADR-0193](0193-a-block-keeps-two-people-off-one-court-and-the-blocker-can-see-it.md)
  §1.** The pair rule gains one more clause, the **reliability filter**, asked exactly where a block
  is asked (§6).
- **Reverses** the mechanics' §5.1 sentence *there is no score, no weight and no toggle* (as
  corrected on 2026-10-06), and rule R-ENGINE-15, *reliability plays no part in which game the
  deck builds*. Reliability is now an optional filter, and it still ranks nothing (§6).
- Decided in the grilling of story S-01D's findings F-RESULT-10.1, F-RESULT-44.1 and F-RESULT-35.1
  on 2026-10-11, and confirmed by the product owner
  ([the decisions comment on #608](https://github.com/Rakieta02/Rakieta/issues/608#issuecomment-6113038779)).
  Specified by PRD [#649](https://github.com/Rakieta02/Rakieta/issues/649), and logged as **Q114–Q120**
  in the mechanics' decision log. Built by the backend's
  [#651](https://github.com/Rakieta02/Rakieta/issues/651), [#654](https://github.com/Rakieta02/Rakieta/issues/654),
  [#655](https://github.com/Rakieta02/Rakieta/issues/655), [#657](https://github.com/Rakieta02/Rakieta/issues/657),
  [#659](https://github.com/Rakieta02/Rakieta/issues/659), [#661](https://github.com/Rakieta02/Rakieta/issues/661)
  and [#663](https://github.com/Rakieta02/Rakieta/issues/663); the player app's
  [#653](https://github.com/Rakieta02/Rakieta/issues/653), [#656](https://github.com/Rakieta02/Rakieta/issues/656),
  [#658](https://github.com/Rakieta02/Rakieta/issues/658), [#660](https://github.com/Rakieta02/Rakieta/issues/660),
  [#662](https://github.com/Rakieta02/Rakieta/issues/662), [#664](https://github.com/Rakieta02/Rakieta/issues/664)
  and [#666](https://github.com/Rakieta02/Rakieta/issues/666); the club website's
  [#652](https://github.com/Rakieta02/Rakieta/issues/652); and the push set-up a human walks,
  [#665](https://github.com/Rakieta02/Rakieta/issues/665).

## Context

What happens after a booked game goes wrong lands, in four ways, on the people who played it.

**Nobody recording a game makes everyone a no-show.** Marta, Ivan, Oscar and Paula play Tuesday at
19:00 at Bonarka Arena. Each paid 40 zł of the 160 zł court-hour, and they go home without opening
the app. A day later the game reads *Never played*. Under ADR-0140 §2 that is a **ghost**, charged
to all four on *Shows up*, the heaviest strand. A newcomer whose first game it was reads 26 out of
100. ADR-0140 bet that a ghost was evidence about people. It was the only evidence then, because a
game was a plan nobody had paid for. A booked game is a court the club was paid for, by four people
who each paid their share. Silence after it says nothing about whether they came.

**The real no-show isn't caught, and the honest player isn't protected.** The *no-show report*
(ADR-0189 §5, the mechanics §15.3) is a tap anyone on the court can make, from anywhere, for a day
after the hour, including from home without having gone. The reported player taps *I was there*
from their sofa and the mark falls. Neither is told. The club's QR **check-in** exists to shield a
player from a report. It is off by default, it proves only that somebody came, and it puts a queue
at the desk of every club that switches it on. Somebody who arrives twenty minutes into a one-hour
game has spoiled it, and nothing records that.

**The score asks for taps and then punishes the people who don't make them.** *Is that right?*
says *silence confirms it … there is no penalty*. A day later, everyone who stayed silent takes a
miss on *Answers about results* (ADR-0160), kept for a year, and nobody told them a score was
waiting. Meanwhile an acceptance waits six hours (ADR-0137 §4), so Paula's *That's right* at 20:35
is wiped out by Oscar's different score at 22:00. A loser who puts up a different score and won't
give way turns the game into *No result*: no Level moves and nothing is recorded.

**The figure says the wrong things.** A new player reads *Nothing counted yet*, and the first event
then sets a ratio from nothing, so one bad evening is a disaster for a newcomer and invisible to a
veteran. Its words, *Reliable · Holding · Under the bar*, name a bar at 70 that the old ranking
applied and nothing applies now. The Games deck, Fill in and posting never read the figure, so
players who want to avoid unreliable partners have no way to do it.

The product owner's principle for all four: **only a real exception starts a flow.** On an ordinary
game nobody does anything.

Considered and rejected:

- **Keep the ghost and push a reminder to record.** It still charges four people for one quiet
  evening, and it makes recording a chore everyone must do to protect themselves. The booked, paid
  court is the evidence the ghost stood in for.
- **Make desk check-in the evidence of turning up.** It would need every club to scan every player:
  a queue at every desk, run by a club that is paid whether anyone comes. And it still says only who
  came. A player not scanned is unknown, never absent, so it can never catch a no-show.
- **A photo, background location, a geofence, or continuous tracking.** Each proves more than a tap
  and costs far more: battery, a background-location permission, and a store of where people were.
  One fix, read at the moment somebody makes a claim and never stored, is the least that makes the
  claim checkable.
- **The club, or Rakieta, rules on a tap or a score.** *We will not arbitrate* (ADR-0137 §4) stands.
  The people on the court decide, and when they disagree about the winner, nothing moves.
- **Keep the ratio and add a minimum number of games.** A bar hides the figure, but the first event
  past it still sets the whole ratio, and a veteran's no-show still weighs almost nothing. Fixed
  prices give the same failure the same cost for everyone.
- **Settle a dispute by picking one of the two scores.** Whichever rule picks it, a side that wants
  the win learns to put up a score first or last. A disagreement about the winner moves nothing.
- **Make reliability a ranking term.** Nothing ranks since the Classic play removal; the deck asks one
  pair rule. A filter is one more clause of that rule, the shape a block already has.
- **Have the filter take back yeses already given**, as a block does (ADR-0193 §4). The product owner
  ruled *from then on*: switching a filter on mustn't take a player out of games they chose.

## Decision

### 1. Player reliability is points

**Everyone starts at 100.** A failure takes a fixed price off, and every game **played through**
gives 5 back. The figure never goes above 100 or below 0. Each failure drops out of the figure **6
months** after it happened. The window rolls, so nothing ever resets everything at once.

| What happened | Part | Points |
| --- | --- | --- |
| **Didn't come**: not at the club 30 minutes after the start (§3) | *Shows up* | −25 |
| **Came late**: arrived 10 to 30 minutes after the start (§3) | *Shows up* | −10 |
| Left after the cut-off, and the seat stayed empty, so the game was played short | *Keeps plans* | −15 |
| Left before the cut-off, the seat stayed empty, and the game was called off for everyone | *Keeps plans* | −10 |
| A card not fixed in time lost the seat, and the game was then called off (counted as leaving before the cut-off, Q113) | *Keeps plans* | −10 |
| Each game **played through** | — | +5, up to 100 |

- **Played through** is a booked game that reached its hour full, with the player on its court, not
  *Came late* and not *Didn't come*, and not called off. Scored or not: *Played · no score* (§2)
  counts. A *Came late* game earns nothing back (a call). A game that started short earns the
  players who stayed nothing either way, as today.
- **A *Didn't come* is priced once**, on *Shows up*. It no longer also breaks *Keeps plans*.
- **Never counted:** a swipe, a withdrawn yes, a card that never filled, a card fixed in time,
  leaving when your seat is taken or the game still plays, a club's cancel, and silence on a score.
- **Bands**, served by the backend and drawn under the figure: **Very high** 90–100 · **High** 75–89
  · **Medium** 50–74 · **Low** below 50. The phone draws the word from the band and holds no
  thresholds of its own. As a rule of thumb, one no-show keeps you High, two close together drop
  you to Medium, and three to Low.
- **New** marks a player with fewer than 3 games played through, **ever**, across sports. They read
  *100 · New* and pass every filter (§6). A player who stops for six months doesn't become New again
  (a call).
- **The counts** over the last 6 months are what the record shows beside the figure:
  - *Shows up*: turned up, of the games that reached their hour with the player on the court (late
    counts as turned up);
  - *Keeps plans*: kept, of the games they were in at the hour;
  - *Being late*: how many times they came late;
  - *Results left in dispute* (§5). It is information only, and costs no points.

  No ledger is shown: the product owner chose counts over a list of events.
- **One figure per player, across all sports**, as today.
- **Still no record of its own.** ADR-0140 §1 stands: the figure is folded on every read from the
  games and bookings records, through their published ports, now including one read per deal for
  §6's filter (a call). The 6-month window bounds that read.
  *Answers about results*, *answers challenges* and *settles up* leave the figure and the wire, and
  so do the strand weights and ratios.

### 2. A full booked game nobody recorded was played

A booked game that reaches its hour **full**, that nobody records and in which nobody is *Didn't
come*, reads **Played · no score** for all its players once its entry window closes. Each of them
gains the 5 points of a game played through. **No Level moves**: an evening with no score is not
evidence about skill.

*Never played* retires as an end. Every game is opened by a booking (#569), so there are no
unbooked plans left that could dissolve. ADR-0140 §2's **ghost** retires with it, and so does the
*Ghost game* term: nothing is charged to a court for silence. ADR-0140 §2 named the measurement that
would falsify it, ghost rates that track the week rather than the person. It is retired by a better
source, not by that measurement: a booked, paid court, and §3's taps.

### 3. A no-show is caught at the court, while it happens

Four new acts on the **Game**, each carrying a verdict on whether its maker is **at the club**:

| Act | Who | When |
| --- | --- | --- |
| **Isn't here yet** (*note absent*) | a player on the court, about another | the **tap window**: from the hour's start to 30 minutes after it, the first half of a one-hour game |
| **I'm here** / **They're here** (*note arrival*) | the absent player, or a courtmate about them | in the tap window |
| **I was there** (*claim presence*) | the absent player | within 24 hours of the tap window closing |
| **Yes, they were here** (*confirm presence*) | any other player on that court | within the same 24 hours |

- **Who may tap** (a call): any player on the court who is at the club, about any other, partner
  included; never about yourself; never while you are yourself absent and not yet arrived. Two
  absentees can each be tapped.
- **The arrival** is the first *I'm here* or *They're here*. It decides the outcome:
  - **on time** if it was within 10 minutes of the start. Nothing is recorded, and the tap vanishes;
  - **Came late** if it was 10 to 30 minutes after the start;
  - **Didn't come** if nobody arrived by 30 minutes after the start.
- **A dead phone gets one way back.** *I was there*, confirmed by a courtmate's *Yes, they were
  here*, turns *Didn't come* into **Came late**, because the tap still proves they weren't there
  when it was made. *Didn't come* is **provisional** until that 24 hours ends.
- **Outcomes are folded per player** from these events against the server's clock, never the
  phone's.
- **A *Didn't come* game takes no score and never counts**, as a confirmed no-show did. A *Came late*
  game carries on as usual, score and Level included.
- **The tap costs its maker nothing**, and **money never moves** on any of this: everyone paid, and
  the club was paid for the hour.
- **Everyone who arrives on time does nothing at all.**

**At the club** is decided by the backend from one location fix that the phone sends with the tap:

- **When it is read.** A precise, one-shot fix, in the foreground, while the app is in use, only at
  the moment of an attendance tap.
- **What it is compared with.** The club's map point. The Game doesn't know its club, so the
  application layer reaches the booking's club point through Bookings (a new read), measures the
  great-circle distance with the existing function, and hands the Game only the verdict.
- **What passes** (a call): within **300 m**, allowing for the fix's own stated accuracy up to
  200 m, so that a large indoor hall still passes.
- **What is kept**: only *at the club, at that time*. **The coordinates are never stored**, on the
  phone or on the server. The courtmate's *They're here* is location-checked too (a call).
- **Refusals are plain sentences**: not at the club (*You can say so only from Ogrody 33*), location
  off (the phone asks for it and says why), and outside the window.
- **The permission text** gains the second use: *Rakieta uses your location to set the area you play
  in and, when you say who's at a game, to check you're at the club.* Background location stays off.
  The player app's own rule that location is read once, for the area, is amended to name this use
  (a call).

### 4. Desk check-in is removed

It solved a problem with no evidence that it was real, and it put a desk queue in front of players
at every club that used it. It goes everywhere:

- **the player app:** the *Show at the desk* QR card, its drawing and the QR dependency;
- **the club website:** the **Check in** page, its scanner and typed-code form, the *We check
  players in* switch, the Bookings *Check in* button and its *checked in ✓* mark, and the camera
  and QR dependencies;
- **the backend:** the per-seat code and its keyed derivation, the club's check-in route, the day
  rows' checked-in time, the details' check-in block, the booked tiles' checked-in flag, the
  setting, the error codes only check-in raised, the club check-ins port and its reader, and the
  dev console's check-in press and situation.

Check-ins lived only in event streams, so **no migration is needed**. The checked-in event and the
setting's field stay decodable and fold to nothing (§9).

### 5. The score is asked for once, and settled by one tap or by silence

On a **Competitive** booked game:

1. **No score is taken before the hour.** *State result* is refused until the game's start.
2. **When the hour ends, all four are asked *How did it go?***, and any of them puts the score up.
3. **The other side is asked *Is that right?***. One *That's right* from either of them **settles it
   at once and closes the game**: no counter is taken after an acceptance. In doubles the first
   agreement from the other side wins. One score per side stays the cap. ADR-0137 §4's six-hour
   acceptance grace retires.
4. **Silence settles it 24 hours after the score**, and the screen says so truthfully. **Silence
   costs nothing.**
5. **Corrections end when the entry window closes.** The entry window is unchanged: from the hour's
   start until 24 hours after the hour ends. The answer window is unchanged: 24 hours from the score
   or its last correction.
6. **Levels move within a minute of the result settling.** A result settled by an acceptance is
   settled for rating from the outbox, for that one game; results settled by a window closing
   (silence, or §5's closer score) are picked up by the rating catch-up job at a **one-minute**
   cadence (a call). The hourly cadence retires. Which games move Levels is unchanged: Competitive
   games whose result is final.

**Two scores standing when the answer window closes**, one per side, neither accepted:

- **The same winner:** the game is confirmed with the **closer** score, the one with the smaller
  difference in games won. On a tie, the first score put up wins (a call).
- **Different winners:** the game ends **disputed**. No Level moves, and each of the two players who
  put a score up is counted in ***Results left in dispute*** over the next 6 months (a call). The line
  is information only and costs no points.

**A For fun game asks nothing** and reads *Played*. A score may be added; it settles at once, with no
answer window, and no Level moves, as today (a call).

ADR-0137 §5 stands, and is now true of the figure too: **no player is penalised for not entering or
not agreeing a result.** A dispute is a line on the record, never points.

### 6. The reliability filter is one more clause of the pair rule

The Player reliability screen gets an optional switch, **off by default**: *Play only with players
of at least **High** reliability*, or *at least **Medium***.

- **Where it applies.** It is a clause of `PlayerFit`, the one pair rule, asked exactly where a block
  is (ADR-0193 §1): a pair is unfit when **either player's minimum band is above the other's band**,
  in both directions. So it covers the deal (*Picked for you*), the deck, dealing a post
  (*Challenges*), the posting fits, *Seat open* and Fill in rescues, and the details. **New passes
  every minimum.**
- **From when.** From the moment it is switched on, or the moment someone drops below it. **Yeses
  already given stand**: the yes guard and the fill re-check don't apply this clause to a yes given
  before the switch or the drop. Unlike a block, the filter is not re-asked at the fill for those
  yeses (a call: the grilling ruled *from then on*). **Booked games never change.**
- **The setting** is a player preference: Off, At least Medium, or At least High, written by a new
  player route.
- **What the filtering player sees:** *Your filter hides 2 of the 11 players in your groups.*
- **What a hidden player sees, with nobody named:** *Some players in your groups play only with High
  reliability or above. At 75 you're dealt with everyone again.* The figure is the lowest band floor
  among the filters that hide them. Nobody is ever named: ADR-0193 §3's principle for blocks.

  > **Note — as built, 2026-10-12 ([#661](https://github.com/Rakieta02/Rakieta/issues/661)), a call
  > awaiting a ruling.** The figure is the floor of the **highest** minimum among the filters that
  > hide them, not the lowest. Only that figure passes every one of those filters at once, so only it
  > makes *dealt with everyone again* true for a player below both a Medium and a High filter. For a
  > player hidden by High filters alone, Sergio's case above, the two readings agree.
- **The group's Members list** carries each member's points and band.
- **One read of the members' points per deal.** It still ranks nothing: a card is either fit for a
  pair or it isn't.

### 7. Five new notices, and push end to end

| Notice | Goes to | When |
| --- | --- | --- |
| ***Isn't here yet*** — *Ivan is at Ogrody 33 and you're not there yet — tap I'm here when you arrive* | the absent player | at the tap |
| ***They're at the club*** | whoever tapped | at the arrival |
| ***How did it go?*** | all four of a Competitive booked game | when its hour ends |
| ***Is that right?*** | the other side | when a score goes up |
| ***Were they there?*** | the courtmates | when an absent player claims *I was there* |

- **Every one is always on** (a call), because each decides somebody's record or result. They are
  worded by the backend, as today, and open a new destination: **the game's result screen**.
- **For fun games are told none of them.**
- **The teller subscribes to the games context's events** for the first time. *How did it go?* is
  triggered by the clock, so a job tells it when an hour ends, at the 30-second cadence of the other
  money and seat jobs.
- **Push goes end to end on Android and iPhone.** The push service code is unchanged. A human
  follows a step-by-step set-up ticket (#665): the Expo project, Firebase for Android, the Apple
  Developer Program at 99 USD a year with its push key, rebuilt development builds, and selecting
  Expo pushes in the local environment. The human copies that setting from the example file;
  agents never edit the real environment. The player app then switches push on (#666).

### 8. What the wire carries (a public behaviour change)

- **The player document.**
  - The record's reliability block becomes: points, band and *New*; turned up and of, late, kept
    and of, and results left in dispute; and the filter (its minimum, how many it hides and of how
    many) with the figure that brings a filtered-out player back. The strand rows and their
    vocabulary go.
  - The game read: the no-show rows become attendance rows per player (waiting, on time, came late,
    didn't come, claimed, confirmed, each with its deadlines); the standings lose *Never played*,
    *No-show reported* and *No-show*, and gain *Played · no score*, someone not here yet, didn't
    come, and disputed; the settle moment means *at once* after an acceptance.
  - Routes: the no-show routes go. Four new routes carry the attendance acts, each with a location
    fix in its body. A new route sets the filter.
  - Home and the booking details lose the check-in fields. Home's statuses lose *Never played* and
    gain *Played · no score*, and *Uncounted*'s reasons follow the new endings.
  - The notices gain the five kinds and the new destination. Group members carry points and band.
- **The club document.** The check-in route goes, the Bookings day rows lose the checked-in time, and
  the Rakieta settings lose check-in.
- **The dev document.** The check-in route and situation go. New presses cover the attendance acts,
  as any seeded player, at the club or away ([ADR-0194](0194-the-games-test-console-acts-as-seed-accounts-and-writes-history-never-time.md)).
  The rating press settles what has become final; the console still writes history and never moves
  time.

Every client regenerates with `make gen-api`, and the drift and freshness checks diff every one.

### 9. Retired events stay decodable and fold to nothing

The local store needn't be reset (a call). These keep decoding, and fold to nothing:

- `NoShowReported` and `NoShowDisputed` on the Game. A game that held an old no-show report reads
  *Played · no score*;
- `PlayerCheckedIn` on the Booking;
- the check-in field of the club's Rakieta settings event.

### 10. The calls made without a ruling

PRD #649 made fourteen calls the product owner hasn't ruled on. Each is a rule until overruled, and
each is marked *a call* where it stands above:

1. **Location.** The precise fix travels only with an attendance tap and is never stored; the
   backend keeps only *at the club, at that time*. The permission text gains a second sentence, and
   background location stays off. The player app's own rule that location is used once, for the
   area, is amended.
2. **At the club** is 300 m from the club's map point, with the fix's own stated accuracy allowed
   for up to 200 m.
3. **A *Came late* game earns nothing back.** Only a game played through on time earns +5;
   otherwise a late arrival would net only −5.
4. **The courtmate's *They're here* is location-checked too.**
5. **Who may tap:** any player on the court at the club, about any other, partner included; never
   about yourself; never while yourself absent and not yet arrived; two absentees can each be
   tapped.
6. ***Results left in dispute* counts over the same 6 months** as the figure. The grilling once said
   *this year*.
7. **The closer score** has the smaller difference in games won; on a tie, the first score put up
   wins.
8. **Every new notice is always on.**
9. **A For fun score stands at once with no answer window**, and For fun games are told nothing.
10. **The retired events stay decodable and fold to nothing** (§9).
11. **The figure stays computed on every read**, now including one read per deal for the filter. If
    the deal's cost grows with history, a projection would be ADR-0140's first table, and that
    needs its own ADR.
12. **Levels within a minute:** from the outbox on an acceptance, and by a one-minute catch-up job
    when a window closes. The hourly cadence retires.
13. **The filter isn't re-asked at the fill** for yeses already given, unlike a block.
14. ***New* is fewer than 3 games played through, ever.**

### 11. What stands

- **ADR-0137:** the games context is event-sourced; a game's ends are folded from the record and the
  clock and never stored, except *Called off*; one score per side; a score names a winner; any member
  of a side may correct its score; a counter carries a score; a settled result is final; *we will not
  arbitrate*.
- **ADR-0140 §1:** Player Score keeps no record of its own.
- **ADR-0189:** the club is paid for the hour whatever happens on the court, and its Bookings keeps
  reading *Played* for every game that reached its hour. The club sees no attendance and no scores.
- **ADR-0193:** a block's clause in the pair rule, and what a block takes back.

## Consequences

**Easier**

- **An ordinary game asks nothing of anybody.** Four people who turn up on time and go home are
  played through, gain their points, and are asked one question they may ignore.
- **A no-show is caught by the people waiting for them, at the moment it happens**, and the person
  marked hears about it at once, from the court, while they can still do something.
- **The figure means the same thing for everyone.** A failure costs the same for a newcomer and a
  veteran, and the way back is visible: play on time and it rises by 5 a game, and each failure drops
  out after six months.
- **Players can act on reliability.** The filter is the first control on the platform that uses the
  figure, and it rides the pair rule every surface already asks.
- **Clubs lose a step.** No desk queue, no scanner, and one setting fewer, with their money untouched.
- **Levels move when a result is final**, within a minute, rather than at the next hourly run.

**Harder**

- **Location is read for a second reason.** The permission text widens, and a player who refuses
  location can't tap or be found at the club by their own tap. The verdict is only as good as the
  club's map point: a pin dropped in the wrong place refuses every tap at that club until it is
  fixed. A spoofed location could make a false tap, and nothing on the platform can tell. Because
  the coordinates are never stored, a disputed tap can't be audited later; that is the price of
  storing nothing.
- **A tap is an accusation that costs its maker nothing.** A player who is there lifts it with their
  own *I'm here* from the club. But a player whose phone died has only *I was there*, and that needs
  somebody else on the court to confirm it: in doubles one of three, in singles **the very opponent
  who tapped**. Neither the club nor Rakieta rules on it. That is accepted: the tapper had to be at
  the club in the first half of the game, and the old report needed one person at home.
- **Push is now load-bearing.** *Isn't here yet* is worth little if it reaches a phone only when its
  owner opens the app. Push needs the Expo project, Firebase, and the Apple Developer Program at 99 USD
  a year, and a human must set each up before the flow works as designed.
- **Silence on a wrong score now settles it without cost.** A player who doesn't open the app loses a
  correct result they could have corrected. *Is that right?* is pushed to the other side, and that is
  the whole mitigation.
- **A liar can deny an honest winner their Level move**, by putting up a score naming the other
  winner. It costs the liar a visible *Results left in dispute* line and no points. Someone who
  disputes every game is visible to their groups, and nothing more. *We will not arbitrate* has this
  cost, and it is accepted.
- **The closer score favours the loser.** When both sides name the same winner, the loser gains by
  putting up a closer score. The winner still wins, and the Level move is smaller.
- **A filter can thin a hidden player's deck while they earn their way back.** The way out is playing
  on time, and fewer games deal them fewer chances. New players pass every filter, the filter is off
  by default, and each failure drops out after six months.
- **Every figure moves on the day this ships.** Everyone with a ghost behind them gains it back, every
  *Answers about results* miss disappears, and the prices replace the weighted ratio. Nobody did
  anything to earn the change, and it is worth saying to players if there is a channel for it.
- **The deal reads every member's points once per deal**, folded from history on every read. If that
  cost grows, a projection needs its own ADR.
- **A club loses check-in as evidence.** For Visa's *not received* dispute reason, Stripe lists
  check-in confirmations among the proof of service. Without them, a club answers a dispute with the
  booking and the terms the player accepted.
- **The store keeps three dead events and one dead field**, decoded for as long as the store holds
  them.
- **The rating catch-up job runs every minute**, sixty times as often as before, over games whose
  windows closed.

**Neutral**

- **Money never moves on attendance, lateness or a score.** The club is paid for the hour, as before.
- **The club still reads *Played*** for every game that reached its hour, and sees no attendance and
  no scores.
- **The figure stays one per player across sports**, and still ranks nothing: it is a filter clause
  and a line on a record.
- **Sportsmanship stars after a booked game, a game interrupted by rain or injury, and the future
  player ranking** are outside this record (F-RESULT-31.1, F-RESULT-42.1).
