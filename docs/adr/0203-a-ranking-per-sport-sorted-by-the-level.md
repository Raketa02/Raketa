# ADR-0203 — A ranking per sport, sorted by the level

- **Status:** Accepted — **§3's *of N*, §7, §8's rows, §9 and §10's hidden flag amended 2026-11-14
  by [ADR-0204](0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md)** §2 (Q131): *Show me to new people* replaces §7's switch and closes nothing in
  the ranking, blocks hide no row, requests need no ranking and have no limit, and *of N* counts
  everyone; Home gains **Top 10** (ADR-0204 §8). Dated notes mark §3 and §7–§10. — **§5's *the bell
  keeps its corner* and §9's card line amended 2026-11-16 by
  [ADR-0205](0205-what-waits-for-your-answer-goes-behind-an-envelope-and-homes-rows-fold-into-for-you.md)**
  §1–§2 (PRD [#810](https://github.com/Raketa02/Raketa/issues/810)): the trophy takes the corner,
  the bell sits left of it, and an envelope left of the bell; a request's card no longer reads *Found
  you in the padel ranking*, which the notice still does. Dated notes mark §5 and §9.
- **Date:** 2026-11-07
- **Retires the documents' *nothing ranks players*.** The player-app source document's *"Not a
  ranking ladder. A rating exists to make matches balanced, not to be climbed."*
  ([Part 16](../specs/player-app/rakieta-player-app-documentation-v37.md)) and the You spec's
  *"Nothing on this platform ranks players against each other"*
  ([§4](../specs/you/the-you-screen.md#4-considered-and-left-out)) now point here. Raketa ranks
  players, by the number it already shows (§1).
- **Amends [ADR-0159](0159-a-record-is-read-through-a-prior-disclosure-and-the-refusal-names-nothing.md)
  §3's admission** with a new strand, *the subject is listed on General in at least one sport and not
  hidden*, for any reader (§9). **Its gates gain a block made by either side**, everywhere (§8).
- **Supersedes [ADR-0193](0193-a-block-keeps-two-people-off-one-court-and-the-blocker-can-see-it.md)
  §2 for the record.** A block closes the record **in both directions, everywhere, group-mates
  included** (§8). With it go §2's *the blocker opens the record to unblock*, and §3's second read
  that carries a block, *the player record says whether the reader has blocked the subject*:
  **Blocked players is the one read that carries the reader's own blocks.** ADR-0193's note that the
  promise *"you disappear from each other's … rankings"* is false is corrected: in the ranking it
  holds (§8). Members, booked games and chats already shared stay as §2 left them.
- **Honours [ADR-0095](0095-block-directed-record-symmetric-effect-gates-fail-closed.md) §7's
  *rankings … inherit this rule when they arrive*.** They arrive, and a blocked pair never sees each
  other's row (§8).
- **Amends [ADR-0202](0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md)
  §1:**
  - **A friend request is no longer only between group-mates.** It is also admitted to anybody listed
    on General and not hidden, at most **10 a day** to people the requester shares no group with (§9).
  - Its *Does not decide finding players outside your groups* is decided for the ranking alone, and a
    search by name stays out.
  - **The record's *Unblock* button goes.** Unblock lives in You › Blocked players (§8).
- **Amends [ADR-0200](0200-a-level-is-asked-where-play-begins.md) by one door.** Rankings' *Get your
  {sport} level* starts that sport's questionnaire, and the pass returns to Rankings (§5).
- **Adds a fourth per-account value to
  [ADR-0188](0188-the-phone-remembers-three-choices-per-account-and-forgets-them-at-sign-out.md)**: the
  Rankings view last looked at, *General* or *Friends*. It is kept per account and wiped at sign-out,
  as the deck's last sport is (§5).
- **States an exception to the backend's *derived, never stored*** (`backend/CLAUDE.md`). The ranking
  projection and its level history are stored, and §10 says why.
- **Leaves standing:**
  - the rating engine, every constant and rule of it;
  - *a level is proved, never declared*, and *absence widens, it never lowers*;
  - ADR-0193 §1's one court, and ADR-0202 §2's *a block ends a friendship*;
  - the record's one refusal (ADR-0159 §5), and its gates about accounts;
  - [ADR-0198](0198-the-player-app-is-not-built-for-screen-readers-for-now.md)'s ordinary-touch build.
- **Does not decide:**
  - **the engine review**: how fast a level learns, in padel especially, and when new players should
    first appear in General ([#781](https://github.com/Raketa02/Raketa/issues/781));
  - **General by city**, once a second city opens ([#782](https://github.com/Raketa02/Raketa/issues/782));
  - points, seasons, or any second ranked number;
  - separate lists by gender, and filters;
  - pushes, bell lines or emails about the ranking;
  - a player's place on their record or passport;
  - a search for players by name;
  - the club website, the public site and the Administrator's views, which are untouched.
- Settles PRD [#766](https://github.com/Raketa02/Raketa/issues/766), decided in the rankings grilling
  on 2026-11-07 (Q1–Q26 there, the mechanics' **Q130**) and written by
  [#767](https://github.com/Raketa02/Raketa/issues/767). Specified by
  [`docs/specs/rankings/`](../specs/rankings/README.md): where this record and those documents
  disagree on a detail, the documents win, and this record holds the shape. The market research is
  [`docs/research/rankings-market.md`](../research/rankings-market.md). Built by the backend's
  [#768](https://github.com/Raketa02/Raketa/issues/768) (the General list),
  [#769](https://github.com/Raketa02/Raketa/issues/769) (the chip and the gap line),
  [#770](https://github.com/Raketa02/Raketa/issues/770) (pages, at 50,000 players),
  [#771](https://github.com/Raketa02/Raketa/issues/771) (Friends),
  [#772](https://github.com/Raketa02/Raketa/issues/772) (the switch, and blocks in the lists) and
  [#773](https://github.com/Raketa02/Raketa/issues/773) (strangers' records and requests, and a block
  closing the record); and the player app's
  [#774](https://github.com/Raketa02/Raketa/issues/774)–[#779](https://github.com/Raketa02/Raketa/issues/779).
  Walked by [#780](https://github.com/Raketa02/Raketa/issues/780).

## Context

**Tomek has a level and nothing to measure it against.** He plays competitive padel every week in
Kraków. After every confirmed result his level moves, and it reads *2,71* on his Skill passport and
on every card the deck deals Tomek. **Karol** plays at 2,75, **Zofia** at 2,69, **Inés** at 3,40. No
screen tells Tomek that Karol sits just above, that one win would pass Karol, or how Tomek compares
with the friends Raketa now has.

- **Nothing pulls Tomek back between games.** A level moves by hundredths and is seen only on its own
  passport, so a win changes nothing Tomek can show or chase. The product owner's brief asks for a
  reason to keep playing and climbing.
- **The documents say nothing may rank players.** The player-app source document says a rating *"is
  not a ranking ladder"*, and the You spec that *"nothing on this platform ranks players against each
  other"*. The prototype's ladder was cut with the 2026-08-25 reset. The product owner reverses that
  (Q14): the ranking is the goal.
- **Strangers can't reach each other.** A record opens only for people who played together, share a
  group, or run the other's group (ADR-0159). A friend request needs a shared group (ADR-0202 §1). A
  ranking that shows strangers but whose tap leads nowhere would be a dead end.
- **A block was built for groups.** ADR-0193 §2 kept the record open under a block, so the blocker
  could reach Unblock and the blocked person read nothing unusual from a co-member. A ranking shows
  every listed player to everybody, and would put a blocked pair side by side in every list.

**What the evidence says** ([the research](../research/rankings-market.md)):

- **Every serious system keeps two numbers apart.** A *rating* measures skill: Playtomic's level,
  UTR, WTN, DUPR, Elo and Glicko. A *ranking* counts points in a rolling window: ATP, the
  international padel federation FIP, and both Polish federations.
- **A leaderboard sorted by a rating always limits who appears.** Lichess requires 30 rated games, one
  in the last week, and a settled rating. Chess.com requires 20 games, one in the last 90 days.
- **Raketa's engine is already a rating.** A padel win moves a player with about 10 games by about
  0,03, and a seasoned one by about 0,01. A padel level takes about 42–44 games to be called
  settled, and a tennis level about 26. After 5 padel games, 56% of a level still comes from the
  questionnaire. A player who claims 3,80 but plays like 2,70 is still at 3,28 after 20 padel games.

**The alternatives:**

- **A separate points ranking**, as Playtomic's documentation once described (+10 for playing, +100
  for a win, seasons reset to zero), or as ATP and FIP keep. It rewards how much a player plays, not
  how well, and puts a second number beside the one on every card, which then has to be explained.
  The product owner chose the level itself (Q15).
- **A conservative score**, the level less a multiple of its uncertainty, as TrueSkill's leaderboards
  sort. Tomek would read 2,71 on his passport and something lower on the list: still a second number.
- **List every rated player**, from the questionnaire on. The top of the list would be
  self-assessments: the questionnaire alone never passes 30% confidence, and a player claiming 3,80
  would lead without one game. General waits for 5 results instead (Q17, kept "for now" in Q24).
- **Lower an idle player's level** to move them down. That breaks *absence widens, it never lowers*,
  and the ranking would change the number it ranks by. An idle player leaves the list instead (Q18).
- **Renumber the places around a hidden or blocked player.** Then *7th* would mean one thing on
  Tomek's phone and another on Karol's. Places stay true, and a gap stands where the row is (Q9).
- **Save everybody's place each night** for the weekly chip, as the grilling first said. Every server
  process would run that job on its own today, and a snapshot of places moves a player's chip when
  somebody new arrives. A level history kept as each level moves needs no job (agreed call 3).
- **Keep the record closed to strangers.** Then the ranking's faces open nothing. The product owner
  overruled that (Q12): the ranking is a way to meet players across clubs, and the record holds
  nothing sensitive.
- **Keep ADR-0193 §2's open record under a block.** Then the ranking would hand a blocked person the
  blocker's record from a list of strangers. A block now closes the record both ways (agreed call 1).
- **No limit on requests to strangers.** One player could ask the whole list. Ten a day is the cap
  (Q21).

## Decision

### 1. The ranked number is the level itself

- **A ranking sorts players by their Level** in one sport, the same number as on the Skill passport
  and every game card. There is no second number: no points, no seasons, no conservative score.
- **The ranking never changes a level.** Nothing decays, and nothing is adjusted to rank anybody. The
  rating engine is untouched. A level at the top of the scale, 5,00, is level with any other 5,00,
  and the tie rule (§3) decides.
- **Competitive games only.** A **result** here is a **confirmed competitive result with a winner**
  in that sport: exactly the results that move a level, one `rating.moved_on_result` each. A For fun
  game, *Played · no score* and a *Disputed* game move no level, so they never count.
- **One ranking per sport**, for all four sports. Men and women are in one list (Q8), and there are no
  cities (Q1) until a second city opens.

### 2. Two views: General and Friends

- **General** is everybody in Raketa listed in that sport. A player is **listed after 5 results** in
  the sport (Q17).
- **Friends** is the reader and the reader's friends, each **listed from their first result** (Q26).
- **Both views drop a player 90 days after their last result in the sport settled** (Q18). The next
  result puts them straight back, at their level then, **with no new 5-result wait**.
- **Everything is worked out per view.** *4th* in Friends and *7th* in General are both true.

### 3. Order and places

- **Order:** level, highest first; then more results in the sport; then who reached that level first;
  then the player id (Q20). **Every place is unique.**
- **A place** is a player's position in that order. ***Of N*** counts every listed player in the view,
  hidden ones included (§7).

> **Amended 2026-11-14 by [ADR-0204](0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md) §2.** Nobody is hidden any more, so *of N* counts every listed
> player and every row is shown to every reader.

### 4. The chip: places moved in 7 days

- **The chip covers the last 7 days, rolling** (Q4). It compares a player's place now with where
  **today's same players** stood, ordered by their levels exactly 7 days earlier (Q5, Q23). So:
  - Ewa entering the list moves nobody's chip;
  - Tomek adding Inés as a friend doesn't move his Friends chip;
  - Karol winning and overtaking Tomek gives Tomek ▼1;
  - somebody leaving the list gives nobody ▲.
- ***New*** shows for the 7 days after a player first enters that view's list: the 5th result for
  General, the first for Friends.
- **A comeback gets a real chip**, because the returning player's level 7 days ago is known. Inés's
  comeback win shows ▲3, not *New*.
- **It reads a level history**, appended each time a level moves, which answers *this player's level
  and count of results at any instant*. No night-time job exists, and none is needed.

### 5. The trophy on Home, and the page

- **Home's header gains a dark trophy pill, *🏆 #7*, just left of the bell** (Q13). The bell keeps
  its corner.
  - **Its sport** is the sport of the reader's latest result, in any sport.
  - **Its view** is the one last looked at on the page, remembered per account on the phone
    (General the first time). This is a fourth per-account value under ADR-0188's rule, wiped at
    sign-out.
  - **No number** when the reader has no place in that view and sport. The trophy still opens the
    page.

  > **Amended 2026-11-16 by [ADR-0205](0205-what-waits-for-your-answer-goes-behind-an-envelope-and-homes-rows-fold-into-for-you.md) §2.** **The trophy takes the corner.** The header
  > reads envelope, bell, trophy, right-aligned, the envelope there only while something waits for
  > the reader's answer. The trophy's sport, view, number and page are unchanged.
- **The Rankings page:**
  - the title, with ***Competitive games only*** under it, and the deck's sport pill, offering all
    four sports with the reader's rated sports first;
  - **General | Friends**;
  - the reader's **place card**, with the chip and a gap line (§6);
  - a **podium** of the first three rows the reader sees;
  - **the list**, best first. General is loaded in **pages of 50**, with a floating ***You · 212th***
    button that loads the page around the reader's row (Q16). Friends is shown whole, with the same
    button.
- **The page explains an empty place.** A reader with fewer than 5 results is told how many more
  put them on the list. A reader off the list is told one game puts them back. A reader with no
  level in that sport gets ***Get your {sport} level***. It starts that sport's questionnaire, and the
  pass returns to Rankings, as ADR-0200 has every pass end where it began.
- **Any face opens that player's full record** (§9).
- **No pushes, no bell lines and no emails** about the ranking (Q10).

### 6. The gap line counts wins, honestly

The place card turns a place into a target: *0,04 behind Karol · one win closes it · Zofia is 0,02
behind you* (Q19).

- **One win's move is priced by the rating engine's own stakes for an even game.** The opposition is
  at the reader's own level and uncertainty; in doubles, the reader's side has an equal partner; the
  sport's share applies. **The number of wins is the gap divided by that move, rounded up.**
- **1** reads *one win closes it*, **2–5** *about N wins close it*, and **above 5** the count is left
  out, so a far gap never discourages.
- **A tie** with the player above reads *Level with Ewa · one win puts you ahead*.
- **The top of the list** reads *Top of the list*, and **the last place** only the part about the
  player above.
- **The backend works the count out and the client draws it.** It reads the engine's update rule, so,
  as with **At stake**, nobody else may compute it.

### 7. *Show me in General*

- **A switch in You, on by default** (Q9): *Players who don't know you can see your place, open your
  record and send you a request.*
- **Turned off:**
  - the player's row disappears for everyone else in General;
  - strangers can no longer open the player's record or send a request through the ranking;
  - friends still see the player in Friends;
  - **places never renumber.** The others see #6, then #8, and *of 13* still counts the hidden player.
- **A hidden player still sees their own place**, on the card and on Home.
- **The switch is a fact about the player.** Turning it is a new event on the Player profile's
  stream, the profile read returns it, and the ranking follows through the outbox.

> **Replaced 2026-11-14 by [ADR-0204](0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md) §2.** *Show me to new people* takes its place on You. It
> takes a player out of Home's three people rows and closes their record and requests to anyone who
> shares no group, game or friendship with them; **the ranking shows them at their true place**,
> in General, Friends and Top 10. Its old events fold into the new switch, *hidden* as off.

### 8. A block hides rows both ways, and closes the record both ways

- **In the ranking**, a blocked pair, either way round, never sees each other's row, in either view.
  Places don't renumber.
- **On the record**, **neither of them can open the other's record, anywhere, group-mates
  included.** The refusal is the record's one refusal, which names nothing (ADR-0159 §5). This
  supersedes ADR-0193 §2 for the record: a block is again one of the gates a record is admitted
  under, in both directions.
- **Unblock stays in You › Blocked players, and the record's Unblock button goes.** A blocker who
  can't open the record can't unblock from it. The record's *blocked by you* field leaves the
  contract, because a blocked pair's record never opens. **Blocked players is the one read that
  carries the reader's own blocks**, and ADR-0193 §3's contract walk allows that one place.
- **Nothing else moves.** Groups, Members lists, booked games and chats already shared are as
  ADR-0193 §2 left them. A block still keeps the pair off one court (ADR-0193 §1) and ends a
  friendship (ADR-0202 §2).
- **ADR-0095's promise holds again in the ranking.** The prototype's *"you disappear from each
  other's matchmaking, decks, radar and rankings"* was called false by ADR-0193. The matchmaking,
  decks and radar it names are gone. Rankings is back, and there the promise is true.

> **Amended 2026-11-14 by [ADR-0204](0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md) §2.** **The ranking hides nobody**: a blocked pair sees each
> other's rows at their true places, in both views and in Top 10, because the ranking is the true
> ranking (the Home rows grilling, Q17). A tap on the other's row reads *This record isn't available*:
> **the record stays closed both ways**, as above. A block now keeps the pair out of each other's
> people rows on Home, the surfaces that suggest one player to another, and ADR-0095's promise holds
> there instead.

### 9. Strangers: the record and a friend request

- **The record gains a strand.** It is admitted when *the subject is listed on General in at least
  one sport and not hidden*, for **any reader**. That includes Ola, who has no level and only
  browses. The gates about accounts and the reader's own hold still run, now with a block made by
  either side (§8).
- **A friend request is admitted** when the two share a group, **or** the addressee is listed on
  General and not hidden. The record tells the client whether *Add friend* may be offered.
- **A request from the ranking says so.** It is made from the record opened on the Rankings page, and
  carries that origin and the sport in the friend relation's existing *made from* and sport. The card
  and the notice read ***Found you in the padel ranking***. A request from the ranking to a group-mate
  still names the ranking.
- **At most 10 requests a day to people outside your groups** (Q21). A requester who has already sent
  10 that Warsaw day to people they share no group with is refused with a new code,
  `daily_request_limit`: *You've sent 10 requests to new people today. Try again tomorrow.*
  Requests to group-mates are never counted. The count resets at midnight, Warsaw time.

> **Amended 2026-11-14 by [ADR-0204](0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md) §2.** **Anyone may open any record and ask anyone, with no daily
> limit**, except across a block or when the subject's *Show me to new people* is off and they share no
> group, game or friendship with the reader. The strand above folds into that rule; the limit, its
> counts and `daily_request_limit` go. A request from the ranking still reads *Found you in the padel
> ranking*, and Home's rows add three more origins.

> **Amended 2026-11-16 by [ADR-0205](0205-what-waits-for-your-answer-goes-behind-an-envelope-and-homes-rows-fold-into-for-you.md) §1.** **The card no longer reads it.** A friend
> request waits in *Needs your answer*, and its tile shows the sender's level in every sport they hold
> one in. The notice still reads *Found you in the padel ranking*, and the request still records the
> ranking and its sport.

### 10. Where it lives: a stored projection, as a stated exception

**Rankings** is a new bounded context. It owns the ranking projection and its reads. Each neighbour
is reached through a port the context declares in its own words, wired at bootstrap:

- the rating's `rating.moved_on_result`, delivered through the outbox;
- Friends' friend list;
- blocks, in both directions;
- players' nicknames and photos;
- the Player profile's *Show me in General*.

> **Amended 2026-11-14 by [ADR-0204](0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md) §2.** The port onto *Show me in General* and the row's *hidden
> from General* go, and with them the lists' block filtering. The ranking still reaches
> the rating's events, Friends' friend list, and players' nicknames and photos; Discovery (ADR-0204
> §10) keeps its own copies.

**The projection, fed by the rating's events:**

- **One row per player per sport**, made on their first result in the sport. It holds the level (two
  decimals) and its uncertainty, which prices one win (§6); the count of results; when the last one
  settled; when the current level was reached; when the player first entered General and Friends;
  the last five outcomes, oldest first; and whether the player is hidden from General.
- **The level history**, appended on every move and **keyed by the event**, so a redelivery changes
  nothing.
- **Both are written on the event that moves the level**, so a settled result changes the place at
  once. A deleted account's rows go.
- **A rebuild from the event store** fills both from the rating history already there, so today's
  players appear when it ships. Running it twice changes nothing.
- **An index serves General's order**: sport, level descending, results descending, level reached
  ascending, player id.

**Why it is stored.** The backend's rule is *derived, never stored*: a Player Score, a standing and
what a club can sell are folded from the record on every read. A ranking can't be:

- **A page of General is a slice of an order over every listed player.** At 50,000 players, folding
  every rating stream to answer *who is 212th* on each read is the cost the rule never had to pay.
- **The chip needs every listed player's level as it stood 7 days ago.** That is a history, and no
  fold of today's ratings can answer it.

**What keeps the copy honest.** The level and its history are written only from the rating's
events, and the rebuild from the event store must equal live delivery, which a test asserts. The
only other writes are the profile's *Show me in General*, through the outbox, and an account's
deletion, which removes its rows. **The rating stays the one owner of the level.** A sport's General places and chips are worked out together in one database
pass and cached per sport for at most a minute, replaced on the next write in that sport, so a 90-day
drop-off shows within a minute. Friends is worked out on each read from the friend list and the
projection.

**The backend's rule names its exception.** `backend/CLAUDE.md`'s *Derived, never stored* lists none
today. A pointer to this section is owed there, and in the Rankings context's own rule note, by the
backend session that builds [#768](https://github.com/Raketa02/Raketa/issues/768).

**On the player surface:**

- `GET /rankings/{sport}?view=general|friends` returns the card, the podium and the first page of
  rows (or the whole of Friends);
- `GET /rankings/{sport}/general/rows` pages through General in 50s, after or before a cursor, or
  around the reader;
- `GET /home` gains `ranking`: the sport of the reader's latest result, and their General and Friends
  places in it, either one empty;
- `PUT /players/me/ranking-visibility` sets *Show me in General*.

The record loses *blocked by you* and gains whether *Add friend* may be offered. The friend request
gains its admission, its origin and its daily limit. The shapes are
[the rankings mechanics](../specs/rankings/the-mechanics.md)', and the tickets settle them.

## Consequences

**Easier**

- **A level becomes something to chase.** Tomek sees who is just above, what one win does, and his
  place on Home the moment a result settles.
- **One number everywhere.** The list, the passport and every card agree, so there is nothing new to
  explain and no second number to game.
- **Players meet across clubs.** A face in the ranking opens a full record and a request.
- **A block is a clean break**: no shared row, and no record in either direction.
- **The chip only moves when somebody plays.** Nobody is blamed for an arrival or a new friend.

**Harder**

- **A stored copy of the level.** A copy is a second place for a fact to be true. The projection is
  written only from the rating's events and checked against a rebuild, but a handler that fails
  leaves the list behind the passport until the event is delivered again.
- **Any listed player's record is open to anyone.** Their level, reliability, form, photos, intro and
  tags are one tap from a stranger, and the ranking is itself a list of every listed player. The
  product owner ruled that the record holds nothing sensitive (Q12). *Show me in General* is the way
  out, and it is on by default.
- **A block between group-mates can now be guessed.** Kuba sees Ania in Members, and Ania's
  record refuses Kuba. ADR-0193 §2 kept the record open to avoid exactly that tell. The refusal still names
  nothing, and a hold or an account that may not be shown reads the same, but in a group it is most
  often a block. The product owner chose the clean break.
- **A gap in the places shows that somebody is hidden**, by the switch or a block. It never says who
  or why, and places stay the same on every phone.
- **The level learns slowly in padel.** After 5 games a newcomer's level is still more than half
  questionnaire, and an overclaimer can sit above honest players for months. The engine review
  ([#781](https://github.com/Raketa02/Raketa/issues/781)) is where that is answered, and where 5
  results is revisited: the product owner calls the wait business-sensitive, because a newcomer who
  waits too long may leave.
- **A friend request asks more.** Each one now reads whether the addressee is listed and hidden, and
  counts the requester's day.
- **The record loses a field.** *Blocked by you* leaves the player contract, which is a breaking
  change for an app already installed. Only `local` runs today, so no installed app reads it.
- **The drift check is red** between each backend ticket and the player ticket that regenerates from
  it, accepted until the branch's end.

**Neutral**

- **Members, booked games and chats** are unchanged under a block.
- **No notices.** The ranking tells nobody anything; it is read when opened.
- **The club website, the public site and the Administrator's views** don't show the ranking.
