# ADR-0204 — Home shows who and what is around you, and any player may meet any other

- **Status:** Accepted
- **Date:** 2026-11-14
- **Amends [ADR-0159](0159-a-record-is-read-through-a-prior-disclosure-and-the-refusal-names-nothing.md)
  §3's admission and §4's gates** (§2):
  - **a record opens for any reader**, except across a block made by either side, or when the subject
    has turned *Show me to new people* off and shares no group, no game and no friendship with the
    reader. The four strands of today become the exceptions to that one gate, not the only ways in;
  - **all of a player's photos** are on the record for any reader it is admitted to, where today a
    record carries only the first.
- **Amends [ADR-0203](0203-a-ranking-per-sport-sorted-by-the-level.md)** in four places (§2, §8):
  - **§7: *Show me in General* is replaced** by *Show me to new people*. The ranking no longer has a
    switch, and nobody's row is hidden from it;
  - **§8: a block no longer hides ranking rows.** A blocked pair sees each other in every list at
    their true places. **The record stays closed both ways**, as §8 decided;
  - **§9: a request needs no ranking, and the 10-a-day limit goes**, with `daily_request_limit`. The
    ranking's strand of the record is folded into §2's one rule;
  - **§3: *of N* and every place count everyone**, because nobody is left out of a list any more. The
    projection's *hidden from General* (§10) goes with the switch.
- **Amends [ADR-0202](0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md)
  §1: anyone may be asked**, under §2's one rule, with no daily limit, from Home's rows, which add
  three origins — *same level*, *new players* and *same vibe* — beside Top 10's, which is the
  ranking's (§9).
- **Amends [ADR-0183](0183-a-group-is-a-crowd-at-a-home-club-and-its-link-never-changes.md)** (§3,
  §11):
  - **any player sees any group's card, its sheet, its member faces and its activity**, whether a
    member or not. The group page itself stays members-only;
  - **a Join request can be withdrawn** by the player who made it, which tells nobody (§7's
    membership rules gain one).
- **Amends [ADR-0170](0170-a-player-may-write-one-line-and-it-is-read-as-their-own.md) §3 and §4:**
  the intro is also drawn on the **vibe sheet** (§6), which is a place a person speaks, not a place
  they are merely named.
- **Amends the You spec's *a tag is shown, never scored***
  ([§3.11](../specs/you/the-you-screen.md#311-tags)): **tags order one row**, *Same vibe players*,
  and still score nothing else (§6). *A tag is not an intent* stands.
- **Narrows [ADR-0095](0095-block-directed-record-symmetric-effect-gates-fail-closed.md) §7's
  *everywhere*, and ADR-0203's honouring of it, for the ranking alone.** A block keeps a pair out of
  each other's **people rows** — *Same competitive level*, *New in Raketa* and *Same vibe* — and
  their See all screens, which are exactly the surfaces that suggest one player to another. The
  ranking, Top 10 and a group sheet show the pair to each other, because each is a fact about
  everybody (a true list, a group's crowd), not a suggestion (§2). The record stays closed both ways.
  [ADR-0193](0193-a-block-keeps-two-people-off-one-court-and-the-blocker-can-see-it.md)'s *disappear
  from each other's … rankings*, which ADR-0203 made true, is false again of the ranking and true of
  the people rows.
- **States three exceptions to the backend's *derived, never stored*** (`backend/CLAUDE.md`), beside
  ADR-0203 §10's: a **player directory**, every player's **current level per sport**, and the
  per-viewer **rest count**. §10 says why.
- **Leaves standing:**
  - the rating engine and every constant of it; the **Forecast** and its one function, which the
    *% even* reads (§4) and nothing else computes;
  - *a level is proved, never declared*, and *absence widens, it never lowers*;
  - the record's **one refusal**, *This record isn't available*, which names nothing (ADR-0159 §5),
    and its gates about accounts and the reader's own hold;
  - ADR-0193 §1's one court, ADR-0202 §2's *a block ends a friendship* and swallows the blocked
    person's later requests;
  - ADR-0183 §7's membership rules, and
    [ADR-0191](0191-the-club-answers-its-official-groups-requests-and-a-removal-is-emailed.md)'s *the
    club answers its official groups' requests*;
  - ADR-0203's ranking: General after 5 results, the 90 days, the order, the chip, the gap line, the
    trophy and the page;
  - [ADR-0198](0198-the-player-app-is-not-built-for-screen-readers-for-now.md)'s ordinary-touch build.
- **Does not decide:**
  - **the rows by city**, the day a second city opens — a follow-up, beside General by city
    ([#782](https://github.com/Raketa02/Raketa/issues/782));
  - notifications, bell lines or emails about a row: a newcomer arriving, a group heating up;
  - updating a row while the player is looking at it;
  - a group page or member list for non-members, and tapping a face in a group sheet;
  - a search by name, mutual friends, a feed, or dismissing a card by hand;
  - the club website's and the public site's own screens, beyond the club's Join request list
    dropping a withdrawn request;
  - the engine review ([#781](https://github.com/Raketa02/Raketa/issues/781)) and General's entry
    rule.
- Settles PRD [#789](https://github.com/Raketa02/Raketa/issues/789), decided in the Home rows grilling
  on 2026-11-13/14 (Q1–Q37 there, the mechanics' **Q131**) from the product owner's brief and its
  mocks, and written by [#790](https://github.com/Raketa02/Raketa/issues/790). Specified by
  [`docs/specs/home-rows/`](../specs/home-rows/README.md): where this record and those documents
  disagree on a detail, the documents win, and this record holds the shape. **The mocks are design
  only**: the product owner ruled that no rule is read off a mock's numbers, names or tags. Built by
  the backend's [#791](https://github.com/Raketa02/Raketa/issues/791) (who sees whom),
  [#792](https://github.com/Raketa02/Raketa/issues/792) (Hottest groups and Withdraw),
  [#793](https://github.com/Raketa02/Raketa/issues/793) (New in Raketa and the player directory),
  [#794](https://github.com/Raketa02/Raketa/issues/794) (Same competitive level and the level
  projection), [#795](https://github.com/Raketa02/Raketa/issues/795) (Same vibe),
  [#796](https://github.com/Raketa02/Raketa/issues/796) (the rest count) and
  [#797](https://github.com/Raketa02/Raketa/issues/797) (Top 10); and the player app's
  [#798](https://github.com/Raketa02/Raketa/issues/798)–[#805](https://github.com/Raketa02/Raketa/issues/805).
  Walked by [#806](https://github.com/Raketa02/Raketa/issues/806).

## Context

**Home only shows what is already Tomek's.** Tomek plays padel at 2,71 and tennis at 3,10, is in
Kazimierz crew, and is friends with Zofia. Every row on Tomek's Home is something waiting on Tomek:
a friends game invitation, a payment to confirm, a friend request, an ask for a level, Tomek's own
games. Nothing shows which groups are busy, who plays at Tomek's level, who just arrived, who is
alike, or who sits at the top of the ranking.

- **A newcomer sees an almost empty Home.** Bartek signs up, picks a nickname, answers the profile
  steps and lands on Home with no group, no level, no friends and no games. Home says *⚡ Play finds
  you one*, which isn't true until Bartek is in a group, and nothing on the screen helps Bartek find
  one or meet anyone.
- **A player stays in the one group they were invited to.** The only way to find another group is to
  type a club or a group into Join a group's search. A group's page, its members and its activity are
  hidden from anyone outside it: the group page answers a non-member `group_not_found`.
- **Strangers can't meet.** A record opens for people who played together, share a group, run the
  other's group, or found them on General after their 5th competitive result (ADR-0159, ADR-0203
  §9). A friend request needs a shared group or the ranking, and is capped at 10 a day to people
  outside your groups. So a newcomer is invisible for their first weeks, and two players who would
  enjoy a game together never cross paths unless a group puts them in one.

**What the codebase already has:**

- **A forecast for any two sides** from their Levels and Uncertainties, `forecast_the_sides`, read
  for every Games card. With one player a side it answers *how even would these two be*. It falls
  with the gap between the levels **and** with how unsure the engine is of either, and it tops out at
  **96%**: Zofia, 0,02 from Tomek, reads 91%, not 99%, and a questionnaire-only newcomer reads at
  most about 73% against anyone.
- **The ranking's projection**, one row per player per sport from their first result (ADR-0203 §10).
  It has no row for a level that came only from the questionnaire, which is what a newcomer has.
- **Social tags**, 2 to 6 per player from a closed vocabulary of nineteen, shown on the record with
  *· you too* on the shared ones, and scored nowhere.
- **Groups' projections** of members with their joined times, and **Bookings' projection** of the
  games booked in each pool.

**The alternatives:**

- **Keep the record closed to strangers, as ADR-0203 left it.** Then a face in a Home row opens
  nothing, and a newcomer, who has no 5 results, can't be met at all. The product owner overruled
  that (Q11, Q18): *"this is a social app"*.
- **Keep the 10-a-day limit.** It was a cap on asking strangers found in the ranking. With every row
  a way to meet people, a cap reads as a punishment for using the feature. The product owner removed
  it (Q18). A block still swallows a request silently, and *Show me to new people* closes the door
  for anyone who wants it closed.
- **A switch off by default, or two switches** (one for the rows, one for the ranking). Off by
  default would hide every newcomer, which is the problem. Two switches answer a question nobody
  asked: the product owner wanted it simple (Q17, Q18). One switch, on by default, and the ranking
  is always the true ranking.
- **Keep blocks hiding ranking rows.** Then *7th* reads #6, then #8 on one phone, and the ranking is
  not the ranking (Q17). A block keeps the pair out of each other's *suggestions* instead, and their
  records stay closed.
- **Sort Same competitive level by the gap alone.** Zofia at 0,02 would read 99%, and a newcomer
  whose level is a guess would sit beside Zofia as an equal match. The forecast already prices the
  doubt (Q6, Q19): sure players near Tomek come first, and a newcomer is pointed first at players
  whose level is known, so the first games teach the app the newcomer's real level.
- **One score across every shared sport.** It would mix a tennis level with a padel level and show
  neither. Each person is shown in the sport where the two are evenest (Q7).
- **Weight the tags, or make *Open to meet someone* special.** Every tag counts the same, and no tag
  is special (Q15). The vibe % only says *how many*, so nobody has to explain why one tag is worth
  more.
- **A fixed top ten by score.** The same ten faces every day is a row nobody looks at twice. Fresh
  good matches take priority, friends and people already asked step aside to the right, and a card
  ignored on five days rests (Q20, Q33, Q34).
- **Count a rest from every Home open.** A player who opens Home and never scrolls would rest people
  they never saw. Only days the card actually came on screen count (Q34).
- **A nightly job that fills the rows.** Every server process would run it, and a row would be a day
  old by morning. Each row is worked out on each read, against a large seeded crowd, and cached
  briefly only if a measurement asks for it (call 11).
- **Several HOTTEST cards, or GROWING by +4 alone.** Two HOTTEST tags mean nothing. +4 alone would
  call every big group growing every month. One HOTTEST, and GROWING needs +4 **and** a quarter of
  today's players (Q10, Q25).
- **A threshold of 3 ranked players for Top 10.** The number 3 would explain itself nowhere. Top 10
  is the top of the Rankings page, so it shows the 1 or 2 there are, or *Nobody ranked in squash
  yet* (Q35, Q37).
- **Tappable faces on a group sheet, or the group page open to non-members.** The sheet's faces are a
  picture of the group, not a way to its members (Q26), and the group page stays the members' own.

## Decision

### 1. Five rows on Home, below *Your games*

- **The header and today's rows stay on top, unchanged:** the title, the trophy and the bell; *Get
  your level*, **FRIENDS GAME**, *To confirm*, **FRIEND REQUESTS**, **ASKED FOR A LEVEL**, *Your
  games* (Q3).
- **Then the five new rows, in this order:** **Hottest groups**, **Same competitive level players**,
  **New in Raketa**, **Same vibe players**, **Top 10**.
- **A row with nothing to show is hidden with its title**, as Home's rows are today.
- **Each row reads on its own.** One slow row never holds up the others. Pull-to-refresh re-reads
  them all, and Home re-reads them each time the player comes back to it when the last read is older
  than 30 seconds. Changing Top 10's sport changes only that row.
- **Nicknames and today's faces everywhere** (Q4): the photo, or the generated court poster as every
  face draws it. The mocks' names and letter circles are sample data.
- **One list for the whole app**, split by city the day a second city opens (Q2).
- **A player in no group** reads under *Your games*: ***Join a group to get games — the hottest ones
  are just below.*** in place of *⚡ Play finds you one*.

### 2. Who sees whom

- **Any player may open any player's record and send them a friend request** (Q18). **There is no
  daily limit.** A block still swallows a request silently, as ADR-0202 §2 decided.
- **One switch, *Show me to new people*, on the You tab, on by default.** It replaces *Show me in
  General*: a player who had that off starts with this off. Turned off:
  - the player leaves the three **people rows** — *Same competitive level*, *New in Raketa* and *Same
    vibe* — on everybody else's Home, and their See all screens;
  - **anyone who shares no group, no game and no friendship with them** reads *This record isn't
    available* and can't send them a request;
  - they keep their **true place** in the ranking and Top 10, and their face in group sheets;
  - they still see the rows themselves, and can still send requests.
- **A block** keeps a pair out of each other's three people rows, either way round. They see each
  other in the ranking, Top 10 and group sheets, where a tap reads *This record isn't available*, as
  group Members lists already do. **The record is closed both ways**, as ADR-0203 §8 decided.
- **The ranking is the real ranking.** Blocked and switched-off players are on every list at their
  true places, and *of N* counts everyone. The *Hidden from General* card goes.
- **The record shows all of a player's photos** to anyone it is admitted to (Q27). Where somebody
  lives is never named: only a distance, as the record shows it today (Q28).
- **Nobody is in their own people rows**, and accounts that don't play — club staff — are in none.

**The record's admission is one rule.** A record opens for any reader unless (a) a block stands
between the two, made by either side, or (b) the subject has *Show me to new people* off and the
reader shares no group, no game and no friendship with them. ADR-0159's strands — the pair played
together, they share a group, the reader runs the subject's group — and a friendship are what (b)
asks about. Both refusals are the record's one refusal, and a refused friend request is one unnamed
code. A switched-off player's record stays open to the people they share a group, a game or a
friendship with (call 9), and to whoever runs a group they are in, who answers that group's requests
and keeps the strand ADR-0159's 2026-10-02 amendment gave them *(a call made while writing #790)*.

### 3. Hottest groups

**The groups with the most going on, whether the reader is in them or not** — a reason to join a
second or third group.

- **Which groups:** every group with **3 or more players**, Player groups and Official groups alike,
  the reader's own included. **Up to 6** cards.
- **Heat** = 2 × *games this week* + 3 × *new players this month* + *players*, counted up to 20 (Q9):
  - ***games this week***: games booked in the group whose court time falls in the **last 7 days**
    and that weren't called off, scored or not. Friends games booked in the group count (call 4);
  - ***new players this month***: players who joined in the **last 30 days** and are still members;
  - ***players***: members today.
- **Tags** (Q10, Q25):
  - **▲ HOTTEST** on exactly one card: the highest heat, and only if that group had at least one
    game this week;
  - **+ GROWING** on any other card with **+4 or more** new players in 30 days **and** new players
    making up **at least a quarter** of today's players;
  - the rest carry no tag.
- **Order:** HOTTEST, then GROWING by heat, then untagged by heat. Untagged groups drop out when
  tagged ones fill the six.
- **The heat bar** is each card's heat over the HOTTEST card's, which is full. With no HOTTEST, over
  the top card's (call 3), read as the highest heat in the row, so no bar is ever more than full *(a
  call made while writing #790)*.
- **The card** carries the group's band and badge, its name and sports, *games this week*, *players*
  with a green *+3 this month* when it grew, the heat bar, up to **4 member faces** (the reader's
  friends first, then the longest-standing members) and **the chip**: **Join** (Anyone), **Ask to
  join** (People I approve), **Asked** (a Join request waiting), **You're in** (a member).
- **Join** makes the reader a member on the spot. **Ask to join** leaves a Join request. **Asked**
  opens a small sheet, *Waiting for Ogrody 33 to answer*, with **Withdraw request**. **You're in**
  opens the group page.
- **Tapping the card opens the group sheet**: the name and the one button (**Join**, **Ask to join**,
  **Asked**, or **Open group** for a member); the badge, *Open group* or *Closed group*, who runs it,
  the club it plays at, its sports; *games this week* and *players · new this month*; up to **6
  member faces** and *7 of your friends play here*, or *11 players* when none of the reader's friends
  is in it.
- **The sheet's faces can't be tapped**, and there is no See all (Q26). **The group page stays
  members-only.**
- **Withdrawing** removes the request from the Owner's, the Administrator's and the club website's
  lists at once, and **tells nobody** (call 7). An Official group's requests are answered by its
  Administrator or its club (ADR-0191), a Player group's by its Owner.

### 4. Same competitive level players

**The players whose level in a sport the reader also plays is closest** — who a competitive game
would be even with.

- **Shown only once the reader has a level in any sport** (Q14, Q23), and only with players who share
  a sport with the reader and have a level in it. With no level anywhere the row is hidden: a level
  is asked where play begins (ADR-0200), and Hottest groups is how a newcomer gets there.
- **The *% even* is the Forecast for one player against another**, read by the one forecast
  function with one player a side; nothing else computes it (Q6, Q19). In padel the two are treated
  as opposite sides (call 8). It falls with the gap between their levels and with the doubt in
  either, and tops out at 96%.
- **Colours are the game cards'**: green 70% and above, amber 55–69%, red below 55% (Q8). The word
  under the number is always *EVEN*.
- **Each player is shown in the sport where the two are evenest** (Q7), so different cards can show
  different sports. *N sports ›* appears when they share more than one, and opens the comparison
  sheet: one block per shared sport, most even first.
- **The row of 10** follows §7's rule, a **good match** being **70% or more**.
- **See all** is a plain full list, best % first, friends where they fall, in pages. On *All*
  everyone is in their evenest shared sport; picking a sport re-compares everyone in that sport. The
  pill offers only sports the reader shares with somebody.

### 5. New in Raketa

**The players who joined in the last 30 days, newest first** — visible on day one, before they have
a ranking or a history.

- **Who:** players who **finished sign-up in the last 30 days**, strictly (Q13, Q22). *Joined* is the
  profile commit that ends onboarding, the moment a **Newcomer**'s 14 days also run from; players who
  signed up before this ships keep their real date (call 1). **Players with no level are included**
  (Q14).
- **The row:** the **10 newest**, newcomers the reader isn't connected with first, then those the
  reader sent a request to, then friends at the back (Q5). An 11th sign-up pushes the oldest card off
  the row; they stay in See all until their 30 days end. In a quiet month the row may hold one card,
  and with nobody new it is hidden.
- **The tile** says *Joined today*, *Joined yesterday*, *Joined 2 days ago* … *Joined 6 days ago*,
  *Joined last week*, *Joined 2 weeks ago* … *Joined 4 weeks ago*, and every sport they have a level
  in.
- **See all:** the same tiles in a two-column grid, newest first, in pages. Its sport pill offers only
  sports at least one newcomer has a level in, and a sport keeps only players rated in it.

### 6. Same vibe players

**Players whose social tags overlap the reader's** — who they'd enjoy a court and a coffee with.
**Skill plays no part** (Q15).

- **Who:** anyone sharing **at least one** tag with the reader. Every tag counts the same; no tag is
  special. Players with no level are included (Q14).
- **The vibe %** rises with each shared tag, each closing half of what's left: **1 − ½ⁿ**, rounded,
  so **1 → 50%, 2 → 75%, 3 → 88%, 4 → 94%, 5 → 97%, 6 → 98%** (Q24).
- **Order:** more shared tags first; ties go to fewer tags not shared, then the player id.
- **The row of 10** follows §7's rule, a **good match** being **2 or more shared tags**.
- **The vibe sheet** shows the player's face, nickname, *6 things in common* and the distance as the
  record does, all their photos, **their intro**, and all their tags with *· you too* on the shared
  ones. It reads the record, so it opens only where the record would.
- **See all:** the same tiles in a two-column grid, most in common first, friends where they fall, in
  pages, with a sport pill of the sports at least one listed player has a level in.

**Tags now order one row and score nothing else.** The You spec's *a tag is shown, never scored* held
because nothing read a tag but the record. This row reads them to put people in an order, and no
proposal, card, forecast or level reads one. *A tag is not an intent* still holds.

### 7. Keeping the rows alive: fresh, gaps and rest

*Same competitive level* and *Same vibe* each show 10, worked out again on every read (Q20, Q33,
Q34):

1. **Fresh good matches first**, best score first: players at or above the row's good-match line whom
   the reader hasn't sent a request to, isn't friends with, and who haven't rested. Someone who asked
   the reader counts as fresh.
2. **The places left are gaps at the right**, best score first: friends, people the reader sent a
   request to, rested players, and weaker matches.
3. **Every read runs this again.** Each new fresh match takes a gap, and the weakest gap leaves the
   row. Nobody needs a particular score to take a gap.
4. **Resting.** A player **rests** in the reader's row once their card has **come on screen on 5
   different days** without the reader adding them, while the pair is still unconnected. A card is
   **on screen** when at least half of it is visible, and it counts once per card, row and Warsaw day
   (call 2). The phone reports it. Each row keeps its own count. A rested player can still come back
   in a gap.

*New in Raketa* has no rest: its 10 are the newest, ordered unconnected, then sent, then friends
(§5). See all lists never rest anybody.

### 8. Top 10

**The ten highest-ranked players of one sport, straight from General.**

- **Places 1 to 10 of General**, whatever blocks and switches say (Q17).
- **The pill offers all four sports** (Q35). A sport with one or two ranked players shows those
  cards; a sport with nobody ranked reads *Nobody ranked in squash yet* in the row. **The number 3
  plays no part anywhere** (Q37).
- **The row appears once anyone is ranked in any sport.** It opens on the trophy's sport — the
  reader's latest result, else the sport the deck last showed, else padel — and if nobody is ranked
  there, on the next sport in the app's order where somebody is (Q16). A pick lasts while the reader
  is on Home, and only this row changes.
- **Each card** is a numeral 1–10 behind a portrait card with the nickname, the level and the week's
  chip, ▲ or ▼, when there is one: no chip for no change, nor for *New*. **The reader's own card**
  reads *You*, with a volt numeral and a volt ring.
- **A card opens the record**, *This record isn't available* across a block; **Rankings ›** opens the
  Rankings page on the row's sport.
- **The trophy is always visible**, with no number while the reader has no place, and always opens
  the Rankings page (Q32, Q36). The page already says *Nobody ranked in padel yet* for an empty
  sport.

### 9. The round friend button, and where a request was found

- **On every people card, one round button** (Q29): **+** (white) sends a request at once and turns
  to **…** (brown); **…** opens *Request sent* with **Cancel request**; **✓** (green) means friends
  and opens *Remove karol.t as a friend?* with **Remove friend** and **Keep**; **the envelope** (volt)
  means they asked the reader, and a tap accepts at once and turns to ✓. On sheets it is worded: *+
  Add friend*, *Request sent*, *✓ Friends*, *Accept*.
- **One tap updates that person everywhere on Home at once.**
- **A request records where it was found**, beside today's group, record, result, link and ranking:
  **same level** with its sport, **new players**, and **same vibe**. A request sent from a record
  keeps the row the record was opened from. The receiver's card line is **worked out when it is
  read** (call 6):
  - from *Same competitive level*: *Your level in padel · 91% even*, falling back to *Found you at
    your padel level* when either no longer has a level there;
  - from *New in Raketa*: *Found you among new players*;
  - from *Same vibe*: *6 things in common*, falling back to *Found you through your tags* when none
    is shared any more;
  - from *Top 10*: *Found you in the padel ranking*, the ranking's own line.
- **A group sheet's faces can't be tapped**, so no request is ever made from one (Q30).

### 10. Where it lives: a Discovery context, and three stored copies as stated exceptions

**Discovery** is a new bounded context. It owns the three people rows, their See all reads and the
rest count. Each neighbour is reached through a port the context declares in its own words, wired at
bootstrap, so no context imports another's internals:

- **Friends' relations**, per person: none, sent, asked you, friend, with the pending request's id;
- **blocks**, in both directions;
- **the Forecast**, through a port onto the one forecast function;
- **the profile's and the user's events**, and **the rating's events**, through the outbox.

**A player directory projection**, fed by the profile's and the user's events: the player id, the
nickname, the first photo, the area cell, when sign-up finished (*joined*), the social tags (one row
per tag, so overlaps are counted portably in SQL), *Show me to new people*, and whether the account
plays. A deleted account's rows go.

**A current-level projection**, one row per player per sport with a level, fed by the rating's events
from the questionnaire and from results alike: the level (μ) and its uncertainty (σ). Indexed by
sport and level.

**The rest count**: one row per viewer, row and player, holding the distinct Warsaw days the card came
on screen. Five days rest the player, while the pair is still unconnected.

**Each has a rebuild from the event store** that is safe to run twice and must equal live delivery,
which a test asserts. The rest count has none: it is the phone's reports, not a fold of anything.

**Why they are stored.** The backend's rule is *derived, never stored*, and ADR-0203 §10 named the
first exception. These three are the next:

- **A Home read can't replay every player's streams.** *Same vibe* compares the reader's tags with
  every other player's; *Same competitive level* reads every player's level in every shared sport;
  *New in Raketa* asks who finished sign-up in the last 30 days. Folding every profile and rating
  stream on each Home open is the cost the rule never had to pay.
- **The ranking's projection is not enough.** It has a row only after a first result, and a
  questionnaire level is exactly what a newcomer has.
- **The rest count is the phone's reports**, which no stream holds.

**What keeps the copies honest.** The directory and the levels are written only from the owning
contexts' events and checked against a rebuild. **The rating stays the one owner of the level**, and
the profile the one owner of the tags and the switch. The rows are worked out on each read — no
nightly job — and measured against a large seeded crowd; a short per-reader cache only if the
measurement asks for it (call 11). **Every candidate list leaves out** the reader, blocked pairs
either way, players with the switch off, accounts that don't play and deleted accounts.

**The backend's rule names its exceptions.** `backend/CLAUDE.md`'s *Derived, never stored* gains a
pointer to this section beside ADR-0203 §10's, owed by the backend session that builds
[#793](https://github.com/Raketa02/Raketa/issues/793).

### 11. Groups: the heat read and Withdraw

- **Heat** reads members and their joined times from Groups' projections, and games from the
  Bookings projection through a port: the pool is the group, the court time in the last 7 days, not
  called off. Groups with fewer than 3 members are skipped.
- **Each card carries everything the sheet shows**, so the sheet needs no second read: the id, name,
  monogram letters and colour key, kind, Join policy, who runs it (the club's name or the Owner's
  nickname), the club's name, sports, games this week, players, new this month, the heat share, the
  tag, up to 6 faces, how many of the reader's friends are members, and the reader's relation
  (member, requested, none).
- **Withdraw** is a new event on the group's stream that removes the reader's waiting Join request.
  The Owner's, the Administrator's and the club's request lists drop it. **Withdrawing a request
  already answered changes nothing and still succeeds.** The player may ask again under ADR-0183 §7,
  as after a decline.

### 12. On the player surface

Each is regenerated into the player app's types; the tickets settle the shapes.

- **The five row reads**, each with its items and, for the people rows, the reader's relation and
  pending request id per person;
- **the three See all reads**, paged in 20s, with an optional sport;
- **the comparison data rides on each *Same competitive level* item** — every shared sport, both
  levels, the %, the gap — so its sheet needs no read; **the vibe sheet reads the record**;
- **on-screen reports** for *Same competitive level* and *Same vibe*: a batch of player ids,
  idempotent per day;
- **withdrawing a Join request**;
- **the switch**, replacing the ranking-visibility route;
- **the record** gains all photos and loses nothing else; **the ranking** loses the hidden state;
  **a friend request** gains its new origins and loses `daily_request_limit`.

## Consequences

**Easier**

- **Home is alive from day one.** A newcomer with no group, level or friend sees the groups to join,
  the people who just arrived and the people like them.
- **Any two players can meet.** A face in any row is one tap from a request, with no limit to
  ration.
- **One switch says *leave me alone***, on by default, and it costs nobody their ranking.
- **The ranking is the ranking.** A place means the same on every phone, with no gap where somebody
  hid.
- **The *% even* means what a game card means.** One forecast, one colour scale, and nobody else
  computes it.
- **The rows rotate.** New matches come forward, ignored ones rest, and friends step to the right.

**Harder**

- **Three more stored copies.** A directory, a level per player and sport, and a rest count are three
  more places a fact can be stale. The first two are written only from the owners' events and checked
  against a rebuild, but a failed handler leaves a row behind until the event is delivered again. The
  rest count is the phone's word for what was seen, and a phone that never reports rests nobody.
- **Any record is open to anyone by default.** Level, reliability, form, every photo, the intro and
  the tags are one tap from a stranger. The product owner ruled that the record holds nothing
  sensitive (ADR-0203 Q12) and that this is a social app (Q11); *Show me to new people* is the way
  out.
- **A block is visible in the ranking.** A blocked pair sees each other's row, and each other's
  record refuses them. In a list of strangers the refusal reads as any refused record; it names
  nothing, and a switched-off stranger's reads the same.
- **No limit on requests.** One player can ask everybody. A block swallows their requests, and the
  switch takes a player out of reach, but nothing slows a sender down.
- **A group's activity is public.** Its games this week, its size, its growth and some faces are on
  every Home. Somebody switched off still shows in a group sheet, because the sheet is a picture of
  the group.
- **Tags now order something.** The You spec promised they never would, and a player choosing tags
  now also chooses who sees them in a row.
- **A Home read asks more.** Five rows are five reads, each over every player, worked out every time.
  The measurement against a large crowd decides whether a cache is needed.
- **The contract changes in breaking ways.** The ranking-visibility route, the ranking's hidden
  state and `daily_request_limit` leave it. Only `local` runs today, so no installed app reads them,
  and the drift check is red between each backend ticket and the player ticket that regenerates from
  it, accepted until the branch's end.

**Neutral**

- **No notices.** No row tells anybody anything; each is read when Home is opened.
- **Members lists, booked games and chats** are unchanged, and a block still keeps the pair off one
  court and ends a friendship.
- **The club website and the public site** change only in the club's Join request list, which drops
  a withdrawn request.
