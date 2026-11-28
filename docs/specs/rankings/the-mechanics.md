# Rankings — the mechanics

> **Status:** agreed in the rankings grilling on 2026-11-07 (Q1–Q26 there), confirmed by the product
> owner the same day, and specified as PRD [#766](https://github.com/Rakieta02/Rakieta/issues/766).
> Logged as **Q130** in the
> [games and fill-in decision log](../games-and-fill-in/the-mechanics.md#appendix-c--decision-log), and
> recorded by [ADR-0203](../../adr/0203-a-ranking-per-sport-sorted-by-the-level.md).
>
> **Its companion** is [the-screens.md](the-screens.md), which says how each screen looks. Every
> sentence a player reads is in [the words §30](../matchmaking/the-words.md#30-rankings). Where this
> document and the brief ([rankings_feature.md](rankings_feature.md)) disagree, this document wins.
>
> **What the ranking borrows** — the level and how a result moves it (the root
> [`CONTEXT.md`](../../../CONTEXT.md)'s **Skill rating**), a friend and a friend request
> ([the friends mechanics](../friends/the-mechanics.md)), a block (ADR-0193) and the record (ADR-0159)
> — is cited here. Only what the ranking adds or changes is written here.
>
> **Calls marked *(a call)*** were made while specifying PRD #766 or writing this document, and are
> open for the product owner to overrule ([§17](#17-calls-made-without-a-ruling)).
>
> **Amended 2026-11-14** by the Home rows grilling, PRD [#789](https://github.com/Rakieta02/Rakieta/issues/789),
> logged as **Q131** and recorded by [ADR-0204](../../adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md) §2: **the ranking is the real ranking**. *Show me in
> General* is replaced by *Show me to new people*, which closes nothing here ([§10](#10-show-me-in-general));
> **blocked rows are shown**, and the record across a block is refused ([§11](#11-blocks)); every place,
> *of N*, the podium and the gap line count everyone ([§5](#5-order-and-places), [§7.3](#73-whom-it-names));
> records and requests follow one rule with **no daily limit** ([§12](#12-records-q12), [§13](#13-friend-requests)).
> Home gains **Top 10**, places 1–10 of General
> ([the home rows mechanics §10](../home-rows/the-mechanics.md#10-top-10)). Dated notes mark each
> section; the rest stands.

---

## 1. The whole thing in one page

**Tomek** plays competitive padel at 2,71. **Karol** plays at 2,75, **Zofia** at 2,69, and **Inés**,
the best padel player in Rakieta, at 3,40. **Ola** has no level and only browses. **Marek** is in a
group with Tomek, and Tomek blocked Marek.

1. **On Home**, the trophy left of the bell reads *🏆 #7*: Tomek's General place in padel, the sport
   of his last result. He taps it.
2. **Rankings opens on padel, General.** His card reads *YOUR PLACE · 7th · of 13 · 2,71 · ▲ 1 up
   this week*, and under it *0,04 behind Karol · one win closes it · Zofia is 0,02 behind you*.
   Under the card, Inés tops the podium, and the list follows, his row tinted and reading *You*.
   Marek's row isn't there, and Tomek isn't in Marek's list either: the places skip a number, and
   *of 13* still counts them both.
3. **On Saturday he beats Karol.** The moment the result settles, Tomek's level is 2,74, he is 6th,
   and Home's trophy reads *#6*. Karol's chip reads *▼ 1*. Ewa's 5th result puts Ewa on the list
   at 9th; nobody's chip moves for it.
4. **He switches to Friends.** He is *4th of 6* among his friends. The trophy will read *#4* from now
   on, because Friends is the view he last looked at.
5. **He opens Piotr's record** from the podium. They share no group, but Piotr is listed on General,
   so the record opens in full, with **Add friend**. Piotr's Home card reads *Found you in the padel
   ranking*.
6. **Ola opens the same record**, with no level at all, and can ask too.
7. **Zofia turns *Show me in General* off** in You. Zofia's row leaves everybody's General list but
   Zofia's own; the others read #7, then #9. Tomek still sees Zofia in Friends. *(Retired 2026-11-14,
   [§10](#10-show-me-in-general): no switch hides a row; Zofia is 8th for everybody.)*
8. **Inés stops playing in August.** Ninety days after the last result, Inés is off both
   lists. The first result back puts Inés straight back on, with a real chip: *▲ 3*.

---

## 2. Words used in this document

The terms are the root [`CONTEXT.md`](../../../CONTEXT.md)'s: **Ranking**, **General**, **Friends**
(the view), **Place**, **Listed**, **the chip** and **Show me in General** (Rankings); **Level**,
**Skill rating** and **Result update** (Skill rating); **Friend** and **Friend request** (Friends);
**Block** (Blocks); **the player record** and **Run of form** (Player record).

**A result**, in this document, is a **confirmed competitive result with a winner** in the sport *(a
call: PRD #766 call 1)*: exactly a result that moves a level, one `rating.moved_on_result` each. A
For fun game, *Played · no score* and a *Disputed* game move no level and are never a result here.

---

## 3. What is ranked

### 3.1 The number is the level (Q15)

- **The ranking is sorted by the Level**, the number on the Skill passport and every game card.
  There is **no second ranked number**: no points, no seasons, no score built from the level.
- **The ranking never changes a level.** Nobody's level decays or is adjusted to rank them. The
  engine is untouched.
- **5,00 is level with any other 5,00**, and the tie rule ([§5](#5-order-and-places)) decides.

### 3.2 One ranking per sport

- **One list per sport, for all four sports**: padel, tennis, squash and badminton.
- **Men and women in one list** (Q8).
- **No cities** (Q1). General is everybody in Rakieta. Splitting it by city, once a second city opens,
  is a follow-up and not decided ([#782](https://github.com/Rakieta02/Rakieta/issues/782)).

### 3.3 Competitive games only

For fun games never touch the ranking, which is what the page's *Competitive games only* says (Q11).
They move no level, so they can't move a place.

---

## 4. Who is listed

### 4.1 General (Q17, Q24)

- **A player is listed after 5 results in that sport.** *Played · no score* and disputed games don't
  count.
- **The 5 stays "for now"** (Q24): when new players should first appear in General moves to the engine
  review ([#781](https://github.com/Rakieta02/Rakieta/issues/781)).

### 4.2 Friends (Q26)

- **The reader and their friends are listed from their first result** in that sport.
- **The Friends table appears with one listed friend** (Q7).

### 4.3 90 days (Q18, Q26)

- **A player leaves both views 90 days after their last result in that sport settled** *(a call: PRD
  #766 call 2)*.
- **The next result puts them straight back**, at their level then, **with no new 5-result wait**.
  A break isn't punished twice.
- **Leaving the list changes nothing about the level.** *Absence widens, it never lowers.*

---

## 5. Order and places

- **Order:** level, highest first; then more results in that sport; then **who reached that level
  first**; then the player id (Q20). **Every place is unique.**
- **A place** is a player's position in that order, in one view and one sport.
- ***Of N*** counts every listed player in that view and sport, **hidden ones included**
  ([§10](#10-show-me-in-general)) *(a call: PRD #766 call 8)*.
- **Places never renumber** around a row the reader can't see, whether hidden or blocked: the
  reader sees #6, then #8.

> **Amended 2026-11-14** (ADR-0204 §2, Q131). **Every row is shown to every reader**, so there is no
> row the reader can't see: *of N* counts every listed player, and the reader sees #6, #7, #8.

---

## 6. Places moved in 7 days — the chip

- **The window is the last 7 days, rolling** (Q4).
- **The chip compares a player's place now with where today's same players stood**, ordered by their
  levels exactly 7 days earlier (Q5, Q23). It moves only when somebody's level moved:
  - **an arrival moves nobody.** Ewa entering the list moves no chip;
  - **an added friend moves nobody.** Tomek adding Inés as a friend doesn't move his Friends chip;
  - **an overtake moves both.** Karol winning and overtaking Tomek gives Tomek ▼ 1 and Karol ▲ 1;
  - **somebody leaving gives nobody ▲.**
- **The chip reads:** ▲ *n* (up), ▼ *n* (down), — (no change), or ***New***.
- ***New*** shows for the 7 days after a player first enters **that view's** list: their 5th result
  for General, their first for Friends *(a call: PRD #766 call 3)*.
- **A comeback is not new.** A player back after 90 days gets a real chip, because their level 7 days
  ago is known: Inés's comeback win shows ▲ 3.
- **A player with no level 7 days ago** is ordered by their first level. That can only happen to
  somebody *New*, whose chip reads *New* anyway.
- **It is read from a level history**, kept as each level moves ([§16](#16-where-it-lives-inferred)),
  so no night-time job is needed (agreed call 3).

---

## 7. The gap line

The line under the place card turns a place into a target (Q19).

### 7.1 What it says

| Case | The line |
| --- | --- |
| One even win closes the gap to the player above | *0,04 behind Karol · one win closes it · Zofia is 0,02 behind you* |
| Two to five wins close it | *0,04 behind Karol · about 3 wins close it · Zofia is 0,02 behind you* |
| More than five wins | *0,31 behind Karol · Zofia is 0,02 behind you* — the count is left out |
| Level with the player above | *Level with Ewa · one win puts you ahead*, then the part about the player below *(a call)* |
| The player below is level with the reader | *… · Zofia is level with you* *(a call)* |
| Last place | only the part about the player above |
| First place | *Top of the list* |

### 7.2 How the wins are counted

- **One win's move is priced by the rating engine's own stakes for an even game** *(a call: PRD #766
  call 7)*: an opposition at the reader's own level and uncertainty; in doubles, the reader's side
  with an equal partner; and the sport's share.
- **The count is the gap divided by one win's move, rounded up.** 1 reads *one win*, 2–5 *about N
  wins*, above 5 is left out.
- **An exact tie reads *one win puts you ahead*.**
- **The backend counts and the client draws.** The count reads the engine's update rule, so, as with
  **At stake**, nobody else may compute it.
- **The count is honest, not exact.** *About 3 wins* never promises that three wins will do it: the
  next opponent is never exactly even, and the player above may play too.

### 7.3 Whom it names

**The line names only rows the reader can see** *(a call)*. A player above or below who is hidden
from General, or blocked either way, is skipped, and the line reads against the nearest row the
reader can see. Closing that gap passes the hidden player too, so the count stays true, and nobody
the reader can't see is named or measured.

> **Amended 2026-11-14** (ADR-0204 §2, Q131). No row is hidden, so the line always names the true
> neighbours above and below, a blocked player included. The call made while writing #767 behind
> this section has nothing left to decide.

---

## 8. Home's trophy

- **A dark pill on Home's header, just left of the bell** (Q13). The bell keeps its corner.
- **It reads 🏆 and the place**: *🏆 #7*.
- **Its sport** is the sport of the reader's **latest result, in any sport** *(a call: PRD #766
  call 5)*. After a tennis win it shows the tennis place.
- **Its view** is the one the reader last looked at on the Rankings page, **remembered per account on
  the phone**, General the first time (Q3). The number always matches the page the reader lands on.
- **No number** when the reader has no place in that view and sport: not enough results, off the
  list, never played, or, in Friends, no friend listed *(a call: PRD #766 calls 5 and 6)*. The
  trophy is still there and still opens the page.
- **A hidden player's trophy still shows their place** *(a call: PRD #766 call 8)*.
- **A tap opens Rankings** on that sport and view.

---

## 9. The page's sport and view

- **The page opens on the trophy's sport.** With no result ever, it opens on the sport the deck last
  showed; with no level anywhere, on padel.
- **The sport pill offers all four sports** (Q22), the reader's rated sports first, then the rest in
  the app's sport order *(a call: PRD #766 call 9)*. It is the deck's own control, lifted to shared UI
  so both use one *(a call: PRD #766 call 13)*.
- **The view, General or Friends, is remembered per account on the phone**, as the deck's last sport
  is ([ADR-0188](../../adr/0188-the-phone-remembers-three-choices-per-account-and-forgets-them-at-sign-out.md),
  its fourth per-account value), and wiped at sign-out.
- **A sport with no level** shows *Get your {sport} level*, which starts that sport's questionnaire;
  the pass returns to Rankings ([ADR-0200](../../adr/0200-a-level-is-asked-where-play-begins.md)'s *a
  pass ends where it began*).
- **The Home tab stays lit** on Rankings, because Rankings opens from Home (Q11).

---

## 10. Show me in General

- **A switch in You, on by default** (Q9), with *Players who don't know you can see your place, open
  your record and send you a request.*
- **Turned off:**
  - the player's row disappears for everyone else in General;
  - strangers can no longer open the player's record or send them a request **through the ranking**:
    group-mates and people the player played with still open the record as before;
  - friends still see the player in Friends, which ignores the switch;
  - **places never renumber**: the others see #6, then #8, and *of 13* still counts the player.
- **A hidden player still sees their own place**, on the card and on Home. Their card's gap line is
  replaced by *Hidden from General*, with the switch, so it can be turned back on where it shows.
- **The podium and the gap line skip a hidden row** for everyone but its player ([§7.3](#73-whom-it-names)).
- **A hidden player has no *You · 212th* button** in General.
- **Turning it is an event on the Player profile's stream.** The profile read returns it, and the
  ranking follows through the outbox.

> **Retired 2026-11-14** (ADR-0204 §2, Q131). ***Show me to new people*** replaces this switch on You
> ([the home rows mechanics §4.3](../home-rows/the-mechanics.md#43-show-me-to-new-people-q18)). It
> takes a player out of Home's people rows and closes their record and requests to strangers, and
> **closes nothing in the ranking**: every row is shown, with its true place, in General, Friends and
> Top 10. *Hidden from General*, the hidden player's missing *You · 212th* button and the skipped
> podium and gap-line rows go with it. A player who had this off starts with the new one off.

---

## 11. Blocks

A block ([ADR-0193](../../adr/0193-a-block-keeps-two-people-off-one-court-and-the-blocker-can-see-it.md))
reaches the ranking and the record (Q9, Q12, agreed call 1):

- **Rows hide both ways.** Tomek and Marek never see each other's row, in either view. Places don't
  renumber.
- **The record closes both ways, everywhere.** Neither can open the other's record, from the ranking,
  Members, a game or anywhere else, **group-mates included**. The refusal is the record's one
  refusal, *This record isn't available*, which names nothing. This supersedes ADR-0193 §2 for the
  record.
- **Unblock lives in You › Blocked players.** The record's own Unblock button goes, because a blocker
  can no longer open the record it was on. Its *blocked by you* field leaves the contract *(a call:
  PRD #766 call 16)*.
- **Nothing else moves.** Members lists both, a booked game keeps both, a shared chat keeps working,
  the pair is kept off one court, and a block ends a friendship (ADR-0202 §2).

> **Amended 2026-11-14** (ADR-0204 §2, Q131). **Rows no longer hide**: Tomek and Marek see each
> other's rows at their true places, in both views and in Top 10, because the ranking is the true
> ranking (the Home rows grilling's Q17). **The record still closes both ways**: a tap on the other's
> row reads *This record isn't available*. A block keeps the pair out of each other's people rows on
> Home instead.

---

## 12. Records (Q12)

- **A new admission strand**: *the subject is listed on General in at least one sport and not
  hidden*, for **any reader**, with or without a level (agreed call 2). Ola, who only browses, opens
  Piotr's full record.
- **The gates still run**: the gates about accounts, the reader's own hold, and now a block made by
  either side ([§11](#11-blocks)).
- **An unlisted, inactive or hidden player's record** is refused to a stranger with the one refusal.
  Their other strands still admit whoever they admitted: a group-mate, somebody they played with,
  whoever runs their group.
- **A tap on any face or row on the page opens the full record**, a stranger's too. The reader's own
  row opens their own record.
- **The record says whether *Add friend* may be offered** under [§13](#13-friend-requests)'s rule.

> **Amended 2026-11-14** (ADR-0204 §2, Q131). **A record opens for any reader**, listed or not,
> except across a block or when the subject's *Show me to new people* is off and they share no group,
> game or friendship with the reader ([the home rows mechanics §4.1](../home-rows/the-mechanics.md#41-records-q18-q27)).
> The strand above folds into that rule, and an admitted reader sees all of the subject's photos.

---

## 13. Friend requests

### 13.1 Who may be asked

- **A request is admitted when the two share a group, or the addressee is listed on General and not
  hidden** (Q12, agreed call 2). This widens the friends mechanics
  [§3.1](../friends/the-mechanics.md#31-who-can-be-a-friend)'s *a friend is someone from your groups*.
- **A link still asks as before.** Opening a friend link puts its owner's request on the opener's
  Home whatever the ranking says ([the friends mechanics §4](../friends/the-mechanics.md#4-the-friend-link)).

> **Amended 2026-11-14** (ADR-0204 §2, Q131). **Anyone may be asked**, under §12's one rule; the
> ranking is no longer needed. A request from a record opened on Rankings or Top 10 still records the
> ranking and reads *Found you in the padel ranking*.

### 13.2 Where it was made (Q21)

- **A request sent from a record opened on the Rankings page is made from the ranking**, with that
  page's sport, in the friend relation's existing *made from* and sport.
- **Its card and notice read *Found you in the padel ranking***, in place of the group line, as a
  link's *Invited you to Rakieta* stands *(a call)*.
- **A request from the ranking to a group-mate still names the ranking**, and isn't counted towards
  the limit *(a call: PRD #766 call 15)*.

### 13.3 The daily limit (Q21)

- **At most 10 requests a day to people you share no group with.** The 11th is refused with a new
  code, `daily_request_limit`: *You've sent 10 requests to new people today. Try again tomorrow.*
- **Requests to group-mates are never counted**, wherever they are made.
- **A day is a Warsaw day**, and the count resets at Warsaw midnight *(a call: PRD #766 call 10)*.
- **A link's request never counts** *(a call)*: its owner pressed nothing, and the opener asked for it
  by opening the link.
- **Accepting is never limited**: an answer is not a request sent.

> **Retired 2026-11-14** (ADR-0204 §2, Q131). **There is no daily limit.** Its check, its stored
> counts and `daily_request_limit` go.

---

## 14. Notifications

**None** (Q10). No push, no bell line and no email is told about a place, a chip or a list. A request
from the ranking is an ordinary friend request, and its notice is the friends mechanics'
[§12](../friends/the-mechanics.md#12-notifications), reading *Found you in the padel ranking*.

---

## 15. Numbers in one place

| What | Number |
| --- | --- |
| Results to enter General | 5, in that sport (Q17, "for now", Q24) |
| Results to enter Friends | 1 |
| Off both views | 90 days after the last result settled; back on the next |
| The chip's window | the last 7 days, rolling |
| *New* | 7 days after a first entry into that view's list |
| The gap line's count | one win · about 2–5 wins · left out above 5 |
| A page of General | 50 rows |
| The podium | the first 3 rows the reader sees; none below 3 |
| Requests to people outside your groups | ~~at most 10 a Warsaw day~~ no limit since 2026-11-14 (Q131) |
| A sport's General order, cached | at most 1 minute |
| Sports | 4, one ranking each |

---

## 16. Where it lives (inferred)

The proposed shapes; the tickets settle them.

| Where | What |
| --- | --- |
| **Rankings** (new context) | **The projection**: one row per player per sport, made on their first result there: the level (two decimals) and its uncertainty, the count of results, when the last one settled, when the current level was reached, when the player first entered General (the 5th result) and Friends (the 1st), the last five outcomes oldest first, and whether the player is hidden from General. **The level history**: appended on every move, keyed by the event, so a redelivery changes nothing; it answers *a player's level and count of results at any instant*. Both are written on `rating.moved_on_result`, through the outbox, the moment a result settles; a deleted account's rows go. **A rebuild** from the event store fills both from existing rating history, and running it twice changes nothing. **An index**: sport, level descending, results descending, level reached ascending, player id ([#768](https://github.com/Rakieta02/Rakieta/issues/768), [#769](https://github.com/Rakieta02/Rakieta/issues/769)) |
| **Its ports**, each in its own words | the rating's *level moved on a result*; Friends' friend list; blocks, both directions; nicknames and photos; the profile's *Show me in General* |
| **At scale** | a sport's General places and chips worked out together in one database pass and cached per sport, replaced on the next write in that sport or after at most a minute, so a 90-day drop-off shows within a minute; a page is a slice of it; Friends is worked out on each read ([#770](https://github.com/Rakieta02/Rakieta/issues/770), [#771](https://github.com/Rakieta02/Rakieta/issues/771)) |
| **Player profile** | *Show me in General*: a new event on the profile's stream, returned by the profile read ([#772](https://github.com/Rakieta02/Rakieta/issues/772)) |
| **Player record** | the new strand, a block either way among the gates, *blocked by you* removed, whether *Add friend* may be offered ([#773](https://github.com/Rakieta02/Rakieta/issues/773)) |
| **Friends** | the widened admission, *made from* the ranking with its sport, `daily_request_limit` ([#773](https://github.com/Rakieta02/Rakieta/issues/773)) |
| **Player routes** | `GET /rankings/{sport}?view=general\|friends` (the card, the podium, General's first page or the whole of Friends); `GET /rankings/{sport}/general/rows` (pages of 50, after or before a cursor, or around the reader); `GET /home` gains `ranking`; `PUT /players/me/ranking-visibility` |
| **Migrations** | the next numbers after the level-ask one (`0067`) |
| **Since 2026-11-14** | ADR-0204 §2 takes *Show me in General*, the hidden flag, the lists' block filtering and `daily_request_limit` out of these shapes ([#791](https://github.com/Rakieta02/Rakieta/issues/791)), and adds the Top 10 read ([#797](https://github.com/Rakieta02/Rakieta/issues/797)) |
| **Seed** | through the use cases: a padel list longer than 50 with the protagonist below the first page; three or more friends listed in padel Friends; one account with 2–4 padel results; nobody listed in badminton. A second run changes nothing |

**The card**, on `GET /rankings/{sport}`: a state — *listed*, *needs results* (with the count),
*no level*, *off the list*, *hidden with a place*, *just you*, *no friend listed* — and with a place,
the place, *of N*, the level, the chip, the player above (nickname, gap, wins or none, tied), the
player below (nickname, gap), and whether the reader is top of the list.

**A row**: place, player id, nickname, photo, form (the last five results, oldest first), chip (up
*n*, down *n*, same or new), level, and whether it is the reader.

**`GET /home`'s `ranking`**: the sport of the reader's latest result in any sport, their General place
and their Friends place there, either one empty when they have no place in it. Friends is empty when
no friend is listed. The whole field is empty when the reader has no result anywhere.

---

## 17. Calls made without a ruling

**Agreed by the product owner before PRD #766 was published:**

1. **A block closes the record both ways, everywhere**, group-mates included. Unblock stays in You ›
   Blocked players.
2. **Any player**, listed or not, may open the record of anyone listed on General and send them a
   request.
3. **The 7-day chip reads a level history kept as each level moves**, replacing the nightly save named
   in the grilling. No job is needed.

**PRD #766's calls**, open for the product owner to overrule, each marked where it stands above:

1. "A result" for the 5, the 90 days and the form is a settled competitive result with a winner.
2. The 90 days run from when the last result settled.
3. *New* is a first entry into that view's list within 7 days. A comeback is not new.
4. The podium shows the first three rows the reader sees, each step labelled with its true place.
5. The trophy's sport is that of the reader's latest result in any sport. With no result, the
   trophy has no number.
6. Friends' place on Home is empty while no friend is listed (the page reads *Just you so far*).
7. The win move is priced for an even game at the reader's own level and uncertainty.
8. A hidden player sees their own place on the card and on Home, and counts in *of N*.
9. The pill lists rated sports first, then the rest in the app's sport order.
10. Days run on Warsaw time, which is when the daily request limit resets.
11. A sport's General order is cached for at most a minute.
12. A rebuild fills the projection from existing rating history.
13. The sport pill is lifted to shared UI.
14. Friends' empty copy reads *None of your friends is ranked in {sport} yet*, because ranking needs a
    result, not just a level.
15. A ranking request to a group-mate names the ranking and isn't counted.
16. The record's *blocked by you* field and Unblock button are removed.
17. A new ADR, logged as Q130.

**A call made while ticketing:** Friends' not-listed lines use the brief's *Not ranked in padel yet —
your first confirmed competitive game puts you on the list*, and *No squash level yet — get one, then
one competitive game puts you on the list*.

**Calls made while writing [#767](https://github.com/Rakieta02/Rakieta/issues/767)**, open for the
product owner to overrule:

1. **The gap line names only rows the reader can see** ([§7.3](#73-whom-it-names)). A hidden or
   blocked neighbour is skipped, and the line reads against the nearest visible row.
2. **A tie line still names the player below**, and a player below at the reader's own level reads
   *Zofia is level with you* ([§7.1](#71-what-it-says)).
3. **A request from the ranking reads *Found you in the padel ranking* in place of the group line**,
   as a link's request reads *Invited you to Rakieta*.
4. **A link's request never counts towards the limit.**
5. **The record shows *Add friend* only when a request may be sent.** Otherwise **Block** stands
   alone ([the screens §6](the-screens.md#6-the-record-from-the-ranking-designed-no-mock)).
6. **Blocking from the record closes the sheet**, because the record no longer opens for either of
   them; the confirmation says where Unblock is
   ([the screens §6](the-screens.md#6-the-record-from-the-ranking-designed-no-mock)).
7. **With 4 results, the line keeps its count**: *4 of 5 games — 1 more competitive padel game puts
   you on the list*. PRD #766 gives only the part after the dash for 4.
8. **A request from the ranking to a player who turns hidden stays open** ([§18](#18-edge-cases)): the
   switch stops new requests, never old ones.

---

## 18. Edge cases

- **A tie at 5,00**: more results first, then who got there first.
- **Two partners reach the same level on one result** (a side moves together): more results decides
  first; with the same count too, they reached the level at the same instant, and the player id
  decides.
- **A result that settles late** (confirmed after its game): its *when* is when it settled, which
  starts the 90 days.
- **A player with 5 results whose 5th is older than 90 days** isn't listed. Their next result lists
  them at once: the 5 were already met.
- **A player hidden from General who is also a group-mate** of the reader still has a record the
  reader can open, through the group, and can be asked, uncounted.
- **A friend who blocks the reader**: the block ends the friendship, so the friend leaves the reader's
  Friends once its delivery has run, and the rows are hidden at once by the block.
- **A request from the ranking to a player who turns hidden** before it is answered stays open: the
  switch stops new requests, never old ones *(a call)*.
- **A record already open on a phone when its subject turns hidden** stays drawn; the next open is
  refused to a stranger.
- **A reader who is not listed and hidden**: there is no place to show, so the card is the not-listed
  card; the switch stays in You.
- **A sport where the reader sees one or two rows**: the list shows without a podium.
- **A first place can never read ▼, and a last place never ▲**: nobody can have stood above first
  or below last among the same players. Mocks 4, 5 and 7 draw both, because their chips are sample
  data ([the README](README.md#overrides), note 1).

---

## 19. Out of scope

- **The engine review**: how fast a level learns, especially in padel, and when new players should
  first appear in General. It needs research into Playtomic and DUPR first, then its own grilling
  ([#781](https://github.com/Rakieta02/Rakieta/issues/781)).
- **General by city**, once a second city opens ([#782](https://github.com/Rakieta02/Rakieta/issues/782)).
- Points, seasons, or any second ranked number.
- Separate lists by gender, and filters.
- Pushes, bell lines or emails about the ranking.
- A player's place on their record or Skill passport.
- A search for players by name.
- The club website, the public site and the Administrator's views.

---

## 20. Evidence

From [the research](../../research/rankings-market.md):

- **Every serious system separates two numbers**: a *rating* of skill (Playtomic level, UTR, WTN,
  DUPR, Elo, Glicko), and a *ranking* by points in a rolling window (ATP, FIP, both Polish
  federations).
- **Rating-based leaderboards always limit who appears.** Lichess requires 30 games, a game in the
  last week and a settled rating. Chess.com requires 20 games, one in the last 90 days.
- **Rakieta's engine is already a rating:**
  - a padel win moves a player with about 10 games by about 0,03, and a seasoned one by about 0,01;
  - a padel level takes about 42–44 games to be called settled, and a tennis level about 26;
  - after 5 padel games, 56% of a level still comes from the questionnaire;
  - a player who claims 3,80 but plays like 2,70 is still at 3,28 after 20 padel games.

  Those numbers are why the engine review is a follow-up.
- **Small, close comparisons motivate.** Fewer competitors and rivals near a standard make people
  try harder (Garcia & Tor, 2009), which is why the gap line names the players just above and below.
