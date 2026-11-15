# Home rows — the mechanics

> **Status:** agreed in the Home rows grilling on 2026-11-13/14 (Q1–Q37 there), confirmed by the
> product owner on 2026-11-14 ("agree"), and specified as PRD [#789](https://github.com/Raketa02/Raketa/issues/789).
> Logged as **Q131** in the
> [games and fill-in decision log](../games-and-fill-in/the-mechanics.md#appendix-c--decision-log), and
> recorded by [ADR-0204](../../adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md).
>
> **Its companion** is [the-screens.md](the-screens.md), which says how each row, sheet and See all
> looks. Every sentence a player reads is in [the words §31](../matchmaking/the-words.md#31-home-rows).
> Where this document and the brief ([home_rows_feature.md](home_rows_feature.md)) disagree, this
> document wins. **No rule is read off a mock** ([the README](README.md#how-to-read-the-mocks)).
>
> **What the rows borrow** — the level, its uncertainty and the Forecast (the root
> [`CONTEXT.md`](../../../CONTEXT.md)'s **Skill rating** and **Games**), a friend and a friend request
> ([the friends mechanics](../friends/the-mechanics.md)), the ranking
> ([the rankings mechanics](../rankings/the-mechanics.md)), a group and a Join request (ADR-0183), a
> block (ADR-0193) and the record (ADR-0159) — is cited here. Only what the rows add or change is
> written here.
>
> **Calls marked *(a call)*** were made while specifying PRD #789 or writing this document, and are
> open for the product owner to overrule ([§17](#17-calls-made-without-a-ruling)).

---

## 1. The whole thing in one page

- **Five new rows on Home, below *Your games*:** *Hottest groups*, *Same competitive level players*,
  *New in Raketa*, *Same vibe players*, *Top 10*. Each reads on its own and is hidden when empty.
- **Any player may open any record and send any friend request, with no daily limit.** One switch,
  ***Show me to new people***, on by default, takes a player out of the three people rows and closes
  their record and requests to anyone who shares no group, game or friendship with them. It replaces
  *Show me in General*.
- **The ranking is the real ranking**: blocks and the switch hide nobody from it any more, and *of N*
  counts everyone. A block keeps a pair out of each other's **people rows** and keeps the record
  closed both ways.
- **Hottest groups**: groups with 3+ players, by **heat** = 2 × games this week + 3 × new players this
  month + players (to 20). One **▲ HOTTEST**, any number of **+ GROWING**, six cards. A Join request
  can now be **withdrawn**.
- **Same competitive level**: the **% even** is the Forecast with one player a side, each person in
  their evenest shared sport, coloured as game cards. Hidden until the reader has a level.
- **New in Raketa**: who finished sign-up in the last 30 days, newest first, unrated included.
- **Same vibe**: anyone sharing a tag; the **vibe %** is 1 − ½ⁿ for n shared tags. Skill plays no
  part.
- **Rows stay alive**: *fresh* good matches first, *gaps* at the right, worked out on every read; a
  card seen on 5 days without an add **rests**.
- **Top 10**: places 1–10 of General in one sport, all four sports in its pill, *Nobody ranked in
  squash yet* for an empty one.
- **One round friend button** on every people card, and a request card that says where it was found.
- **No notices** about any row.

---

## 2. Words used in this document

| Word | Meaning here |
| --- | --- |
| **The reader** | The player whose Home it is. In the examples, **Tomek** |
| **People rows** | *Same competitive level players*, *New in Raketa* and *Same vibe players*, and their See all screens |
| **Connected** | Friends with the reader, or the reader sent them a request still open. Someone who asked the reader is **not** connected |
| **Unconnected** | Neither |
| **A good match** | *Same competitive level*: a % even of **70% or more**. *Same vibe*: **2 or more** shared tags |
| **Fresh**, **gap**, **rest**, **on screen** | [§9](#9-keeping-the-rows-alive) |
| **Joined** | The profile commit that ends onboarding: the moment a **Newcomer**'s 14 days also run from |
| **A day** | A Warsaw calendar day, as every day in the app |

**The people in every example.** **Tomek** is the reader: padel 2,71, tennis 3,10, in Kazimierz crew,
friends with Zofia. **Zofia**: padel 2,69, squash 2,55. **Kuba**: padel 2,80, tennis 3,35, a stranger
with 2 games. **Bartek** signed up 2 days ago, padel 2,35 from the questionnaire only. **Karol** shares
6 social tags with Tomek. Groups: **Ogrody 33 Club** (the club's Official group, *People I approve*,
11 players), **Kazimierz crew** (a Player group Tomek is in), **Podgórze tennis ladder** (a Player
group, *Anyone*, 7 players).

---

## 3. Home, top to bottom

- **The header and today's rows stay on top, unchanged** (Q3): the title, the trophy and the bell;
  *Get your level*, **FRIENDS GAME**, *To confirm*, **FRIEND REQUESTS**, **ASKED FOR A LEVEL**, *Your
  games*.
- **Then the five new rows, in this order:** *Hottest groups*, *Same competitive level players*, *New
  in Raketa*, *Same vibe players*, *Top 10*.
- **A row with nothing to show is hidden with its title**, as Home's rows are today.
- **Each row reads on its own.** A slow or failed row never holds up the others.
  - **Pull-to-refresh re-reads them all.**
  - **Home re-reads them each time the reader comes back to it** when the last read is older than 30
    seconds (Q22).
  - **Changing Top 10's sport changes only that row**; nothing else on Home blinks.
- **Nicknames and today's faces everywhere** (Q4): the photo, or the generated court poster as every
  face draws it.
- **One list for the whole app** (Q2). Everything is split by city the day a second city opens.
- **A player in no group** reads under *Your games*: *Join a group to get games — the hottest ones are
  just below.*, instead of *⚡ Play finds you one*.

---

## 4. Who sees whom

### 4.1 Records (Q18, Q27)

- **A record opens for any reader**, with or without a level, except:
  - **(a) across a block** made by either side, as ADR-0203 §8 decided; or
  - **(b) when the subject has *Show me to new people* off** and the reader shares **no group, no game
    and no friendship** with them.
- **Who (b) still admits:** a group-mate, anybody who was on one game's court with the subject (played
  or not, as ADR-0159's strand), a friend, and whoever runs a group the subject is in *(a call)*.
- **Both refusals are the record's one refusal**, *This record isn't available*, which names nothing
  (ADR-0159 §5), as a hold or an account that may not be shown reads.
- **All photos.** An admitted reader sees all of the subject's photos, where today a stranger saw only
  the first. Order is the player's own.
- **A distance, never a district** (Q28): where somebody lives is shown only as a distance, as the
  record shows it today.

### 4.2 Friend requests (Q18)

- **Anyone may be asked**, under §4.1's rule (b): a request to somebody whose record (b) refuses is
  refused with **one unnamed code**. A block still swallows a request silently, as ADR-0202 §2
  decided, so the sender reads *request sent* as after a request set aside.
- **There is no daily limit.** Its check, its stored counts and the `daily_request_limit` refusal go.
- **A request records where it was found** ([§12](#12-where-a-request-was-found)).

### 4.3 *Show me to new people* (Q18)

- **A switch on the You tab, on by default**, with *Players you don't share a group or a game with can
  find you on Home, open your record and send you a request.*
- **It replaces *Show me in General*.** Anyone who had that off starts with this off. Its old events
  fold into the new one: *hidden* reads as **off**.
- **Turned off:**
  - the player leaves the three people rows on everyone else's Home, and their See all screens;
  - §4.1's rule (b) closes their record and requests to anyone who shares no group, game or friendship
    with them;
  - they **keep their true place** in the ranking and Top 10, and **their face in group sheets** (call
    9);
  - they still see the rows themselves, and can still send requests.
- **Turning it is a new event on the Player profile's stream.** The profile read returns it, and the
  rows follow through the outbox.
- **A player who turns it off while on somebody's row** leaves that row on its next read. A request
  already sent to them stays open *(a call, as the rankings mechanics §17's call 8)*.

### 4.4 Blocks (Q17)

- **A blocked pair, either way round, never appear in each other's people rows** or their See all
  screens.
- **They do see each other in the ranking, Top 10 and group sheets.** A tap on the other in the
  ranking or Top 10 reads *This record isn't available*, as a group's Members list already does. A
  group sheet's faces can't be tapped ([§5.9](#59-the-group-sheet)).
- **The record stays closed both ways**, everywhere, group-mates included (ADR-0203 §8).
- **Nothing else moves**: the pair is kept off one court, a block ends a friendship and swallows the
  blocked person's later requests, Members lists and chats are as they were.

### 4.5 The ranking shows everybody (Q17)

- **Blocked and switched-off players are back on every list at their true places**, in General and
  Friends, on the page and in Top 10.
- ***Of N* counts everyone**, and so does every place, the podium, the gap line and the chip. A gap
  line names the true neighbour above and below, whoever they are.
- **The *Hidden from General* card state goes**, with the switch on the Rankings page.

### 4.6 Who is never in a row

- **The reader**, in their own people rows.
- **Accounts that don't play** — club staff — in any row.
- **Deleted accounts.**
- **Players with the switch off**, and **blocked pairs**, in the people rows (§4.3, §4.4).

---

## 5. Hottest groups

**What it is:** the groups with the most going on, whether the reader is in them or not — a reason to
join a second or third group.

### 5.1 Which groups (Q9)

- **Every group with 3 or more players**, Player groups and Official groups alike, the reader's own
  included.
- **Up to 6** cards. With no group of 3, the row is hidden.

### 5.2 Heat (Q9)

**Heat = 2 × *games this week* + 3 × *new players this month* + *players* (counted up to 20).**

- ***Games this week***: games booked in the group whose **court time falls in the last 7 days** and
  that weren't called off, **scored or not** (call 4). Friends games booked in the group count.
- ***New players this month***: players who **joined the group in the last 30 days** and are still
  members. A player who joined and left is not counted.
- ***Players***: members today, counted up to 20 in the heat. The card shows the true count.
- **Both windows are rolling**, to the minute.
- **Worked example:** Ogrody 33 Club (14 games, +3, 11 players) = 28 + 9 + 11 = **48**; Kazimierz
  crew (11, +4, 10) = 22 + 12 + 10 = **44**; Podgórze tennis ladder (12, +2, 7) = 24 + 6 + 7 = **37**.
- **Ties in heat** go to more games this week, then to the group id *(a call)*.

### 5.3 Tags (Q10, Q25)

- **▲ HOTTEST** on **exactly one** card: the highest heat, and **only if that group had at least one
  game this week** (call 3). If the top-heat group had no game, **no card is HOTTEST**, even when a
  lower group had games *(a call: so the HOTTEST card is always the fullest bar)*.
- **+ GROWING** on any other card with **+4 or more** new players in 30 days **and** new players
  making up **at least a quarter** of today's players:
  - Kazimierz crew, 10 players and +4 → GROWING (4 ≥ 2,5);
  - a 120-player group needs **+30**;
  - Ogrody 33 Club, +3 → not growing, whatever its size.
- **The rest carry no tag.**

### 5.4 Order and the six (Q10)

- **HOTTEST first, then GROWING by heat, then untagged by heat.**
- **Untagged groups drop out** when tagged ones fill the six. Six GROWING groups and a seventh
  untagged with more heat show the six GROWING.

### 5.5 The heat bar

- **Each card's heat over the HOTTEST card's**, which is full.
- **With no HOTTEST, over the top card's** (call 3), **read as the highest heat in the row** *(a
  call)*: with no HOTTEST the first card is the strongest GROWING one, which an untagged card can
  out-heat, and a bar over full would say nothing.
- Kazimierz crew's bar is 44 / 48 of Ogrody 33 Club's.

### 5.6 Faces and the friends count (call 5)

- **Up to 4 member faces on the card, up to 6 on the sheet**: the reader's friends first, then the
  longest-standing members. **The reader's own face is never among them** *(a call, as nobody is in
  their own people rows)*.
- ***N of your friends play here*** counts the reader's friends who are members **now**. With none, the
  sheet says *11 players* instead.
- **A switched-off player keeps their face**, and **a blocked pair sees each other's**: a group sheet
  is a picture of the group (call 9, Q17).

### 5.7 The chip and the reader's relation

| The reader | The chip | A tap |
| --- | --- | --- |
| Not a member, the group is *Anyone* | **Join** | joins on the spot; the chip turns to *You're in* |
| Not a member, *People I approve* | **Ask to join** | leaves a Join request; the chip turns to *Asked* |
| A Join request waiting | **Asked** | opens the withdraw sheet ([§5.8](#58-withdrawing-a-join-request-q12)) |
| A member | **You're in** | opens the group page |

- **An Administrator who runs an Official group** reads **Join** on it and joins directly, whatever
  its policy, as ADR-0183 §7 has every Administrator acting as a player do.
- **The relation crosses per group**: *member*, *requested* or *none*, as join search already sends.

### 5.8 Withdrawing a Join request (Q12)

- ***Asked* opens a small sheet**: *Waiting for Ogrody 33 to answer*, with **Withdraw request**.
- **Withdrawing removes the request at once** from the Owner's, the Administrator's and the club
  website's lists. An Official group's requests are answered by its Administrator or its club
  (ADR-0191), a Player group's by its Owner.
- **It tells nobody** (call 7): no notice, no line, no email.
- **Withdrawing a request already answered, or already withdrawn, changes nothing and still succeeds.**
  A request approved a moment earlier leaves the reader a member.
- **The reader may ask again**, as after a decline (ADR-0183 §7).
- **Withdraw is a new event on the group's stream.**

### 5.9 The group sheet

- **Tapping the card opens the group sheet.** Everything it shows rides on the row's read, so the
  sheet needs no second read.
- **Title row:** the name, and in the corner the one button: **Join**, **Ask to join**, **Asked**, or
  **Open group** for a member, which opens the group page.
- **Identity row:** the badge; *Open group* (*Anyone*) or *Closed group* (*People I approve*); ***run
  by*** the club (an Official group) or the Owner's nickname (a Player group); the club it plays at;
  its sports as dots with names. An Official group that **needs an administrator** reads *run by* its
  club, which answers its requests *(a call)*.
- **Two stat cards:** *games this week*; *players · new this month*, with the green growth.
- **People row:** up to 6 faces (§5.6) and *7 of your friends play here*, *1 of your friends plays
  here*, or *11 players*.
- **The faces can't be tapped** (Q26): they are a picture of the group, not a way to its members.
  **No See all.**
- **The group page itself stays members-only.** *Open group* shows only for a member.

---

## 6. Same competitive level players

**What it is:** the players whose level in a sport the reader also plays is closest — who a
competitive game would be even with.

### 6.1 Who (Q14, Q23)

- **Shown only once the reader has a level in any sport.** With no level anywhere the row is hidden:
  a level is asked where play begins (ADR-0200), and Hottest groups is how a newcomer gets there.
- **Only players who share a sport with the reader and have a level in it.** A level from the
  questionnaire alone counts.
- **Never** anyone §4.6 leaves out.

### 6.2 The *% even* (Q6, Q19)

- **The app's existing Forecast for one player against another**, read by the one forecast function
  with one player a side. **Nothing else computes it.**
- **In padel the two are treated as opposite sides** (call 8), one player each.
- **It falls with the gap between their levels and with how unsure the app is of either level**, and
  tops out at **96%**. Zofia, 0,02 from Tomek, reads **91%**, not 99%. A questionnaire-only newcomer
  reads **at most about 73%** against anyone, so sure players near the reader come first and
  newcomers further down; a newcomer is pointed first at players whose level is known.
- **Colours are the game cards'** (Q8): **green 70% and above, amber 55–69%, red below 55%.** The word
  under the number is always *EVEN*.

### 6.3 The evenest shared sport (Q7)

- **For each player, every sport both have a level in is forecast, and the evenest is kept.** That
  sport, its % and its gap are the card's. Different cards can show different sports.
- **Two sports with the same %** go to the app's sport order *(a call)*.
- ***N sports ›*** appears when they share more than one sport, and opens the comparison sheet.

### 6.4 The gap in words

- **The other's level minus the reader's, in the card's sport**, two decimals: *0,02 below you*,
  *0,09 above you*, and ***Same level*** when it rounds to 0,00.
- **The comparison bar** reads the same two levels on the Skill passport scale, 1,00–5,00.

### 6.5 The comparison sheet

- **One block per shared sport, most even first**: both levels, the %, the gap in words and the bar.
- **All of it rides on the row's item**, so the sheet needs no read.

### 6.6 The row of 10

- **[§9](#9-keeping-the-rows-alive)'s rule**, a good match being **70% or more**, the score being the
  % even.
- **Ties in the %** go to the player id *(a call)*.

### 6.7 See all (Q31)

- **A plain full list, best % first, friends where they fall**, in pages of 20. No fresh, gaps or
  rest.
- **On *All*, everyone is in their evenest shared sport.** Picking a sport **re-compares everyone in
  that sport**, and keeps only players with a level in it.
- **The pill offers only sports the reader shares with somebody** in the list.

### 6.8 Worked example

Tomek's row: 7 fresh good matches, then **Zofia** (a friend, 91%), **Ania** (request sent, 90%),
**Piotr** (a stranger, 60%). Marta starts playing and reads 85% → Marta joins the fresh ones and Piotr
leaves. Two more fresh matches → Ania leaves, then Zofia.

---

## 7. New in Raketa

**What it is:** the players who joined in the last 30 days, newest first — visible on day one, before
they have a ranking or a history.

### 7.1 Who (Q13, Q14, Q22)

- **Players who finished sign-up in the last 30 days**, strictly, rolling. *Joined* is the profile
  commit (call 1). Players who signed up before this ships keep their real date.
- **Players with no level are included.** Their tile shows no sport lines.
- **Strictly 30 days**: in a quiet month the row may hold one card, and with nobody new it is hidden.
  Nobody older fills it.
- **Never** anyone §4.6 leaves out.

### 7.2 The row of 10 (Q5, Q22)

- **The 10 newest.** An 11th sign-up pushes the oldest card off the row; they stay in See all until
  their 30 days end.
- **Ordered:** newcomers the reader **isn't connected with** first, then those **the reader sent a
  request to**, then **friends** at the back; newest first within each. Someone who asked the reader
  is with the unconnected *(a call)*.
- **No rest**: the row turns over by itself as people join.

### 7.3 *Joined …*

Counted in Warsaw days *(a call)*:

| Days since joining | Line |
| --- | --- |
| 0 | *Joined today* |
| 1 | *Joined yesterday* |
| 2–6 | *Joined 2 days ago* … *Joined 6 days ago* |
| 7–13 | *Joined last week* |
| 14–20 | *Joined 2 weeks ago* |
| 21–27 | *Joined 3 weeks ago* |
| 28 and up | *Joined 4 weeks ago* |

No weekday names (a call made while writing PRD #789).

### 7.4 See all (Q31)

- **The same tiles in a two-column grid, newest first**, in pages of 20.
- **The pill opens on *All*.** Its other chips are only sports at least one newcomer has a level in,
  and a sport keeps only players rated in it.
- **If a sport leaves nobody:** *Nobody new plays squash yet*. (It can, between the read that offered
  the chip and the read of the sport.)

---

## 8. Same vibe players

**What it is:** players whose social tags overlap the reader's — who they'd enjoy a court and a
coffee with. **Skill plays no part** (Q15).

### 8.1 Who (Q14, Q15)

- **Anyone sharing at least one tag with the reader.** Players with no level are included.
- **Every tag counts the same; no tag is special.** *Open to meet someone* is one tag like any other.
- **Never** anyone §4.6 leaves out.

### 8.2 The vibe % (Q24)

**1 − ½ⁿ for n shared tags, rounded to a whole percent:**

| Shared tags | 1 | 2 | 3 | 4 | 5 | 6 |
| --- | --- | --- | --- | --- | --- | --- |
| Vibe % | 50% | 75% | 88% | 94% | 97% | 98% |

Six is the most: a player holds at most six tags.

### 8.3 Order

- **More shared tags first.**
- **Ties go to fewer tags not shared**: the other player's tags the reader doesn't hold. (Counting
  the reader's unshared tags too orders the same, since the reader's own are the same for everyone.)
- **Then the player id.**

### 8.4 The row of 10

**[§9](#9-keeping-the-rows-alive)'s rule**, a good match being **2 or more shared tags**, the score
being §8.3's order.

### 8.5 The vibe sheet

- **It reads the record**, so it opens only where the record would (§4.1), and shows what the record
  shows: all photos, the intro, the distance, all tags.
- **The intro is drawn here** (ADR-0170's amendment): the sheet is a place a person speaks.

### 8.6 See all (Q31)

- **The same tiles in a two-column grid, most in common first, friends where they fall**, in pages of
  20. Every tile opens the same sheet.
- **The pill's chips are only sports at least one listed player has a level in**, and a sport keeps
  only players rated in it.

### 8.7 Tags order this row, and score nothing else

The You spec said *a tag is shown, never scored*. **Tags now order one row**, *Same vibe players*, and
still score nothing else: no proposal, card, forecast, level or other row reads one. *A tag is not an
intent* stands.

---

## 9. Keeping the rows alive

*Same competitive level* and *Same vibe* each show **10**, worked out again on **every read** (Q20,
Q33).

### 9.1 Fresh, then gaps (Q33)

1. **Fresh good matches first**, best score first: players who are **a good match** (§2), whom the
   reader **hasn't sent a request to**, **isn't friends with**, and who **haven't rested**. Someone who
   asked the reader counts as fresh.
2. **The places left are gaps at the right**, best score first: friends, people the reader sent a
   request to, rested players, and weaker matches, all in one order.
3. **Every read runs this again.** Each new fresh match takes a gap, and the weakest gap leaves the
   row. Nobody needs a particular score to take a gap.

### 9.2 Resting (Q34)

- **A player rests in the reader's row** once their card has **come on screen on 5 different days**
  without the reader adding them, while the pair is still unconnected.
- **On screen** is at least half the card visible (call 2). **One count per card, row and day**, the
  phone reporting it. Opening Home without scrolling down to the row counts nothing.
- **Each row keeps its own count.** Karol resting in *Same vibe* is fresh in *Same competitive level*.
- **A rested player can still come back in a gap.** They are never hidden.
- **A friend added after resting stays a gap** (a call made while writing PRD #789): a friend is a gap
  anyway.
- **The count never resets** *(a call)*: a rested player stays rested in that row.

### 9.3 Where it doesn't apply

- **New in Raketa** turns over by itself (§7.2), and has no rest.
- **See all lists** are plain orders, and rest nobody.

---

## 10. Top 10

**What it is:** the ten highest-ranked players of one sport, straight from the General ranking.

### 10.1 What it shows (Q17, Q37)

- **Places 1 to 10 of General**, whatever blocks and switches say: the true top of the Rankings page.
- **A card**: the numeral, the portrait, the nickname, the level, and the week's chip, **▲ n** or **▼
  n**, when there is one. **No chip for no change, nor for *New*.**
- **The reader's own card** reads *You*.

### 10.2 The pill (Q35, Q37)

- **All four sports.**
- **A sport with one or two ranked players** shows those cards.
- **A sport with nobody ranked** reads *Nobody ranked in squash yet* in the row.
- **The number 3 plays no part anywhere.**

### 10.3 When it shows and which sport it opens on (Q16, Q32, Q37)

- **The row appears once anyone is ranked in any sport.**
- **It opens on the trophy's sport**: the reader's latest result, else the sport the deck last showed,
  else padel. **If nobody is ranked there**, on the next sport in the app's order where somebody is,
  going round to the first after the last *(a call)*.
- **A pick lasts while the reader is on Home**, and only this row changes. It is not remembered on the
  phone.

### 10.4 Taps

- **A card opens the record**: *This record isn't available* across a block.
- **Rankings ›** opens the Rankings page on the row's sport, **in General**, the view Top 10 is drawn
  from, so the reader sees the rest of the same list *(a call)*. The page then remembers General, as
  any look at it does.

### 10.5 The trophy (Q32, Q36)

- **Always visible**, with no number while the reader has no place.
- **Always opens the Rankings page**, which already reads *Nobody ranked in padel yet* for an empty
  sport. No sheet of its own.

---

## 11. The round friend button (Q29)

| State | Mark | Colour | A tap |
| --- | --- | --- | --- |
| Unconnected | **+** | white | sends a request at once → **…** |
| Request sent | **…** | brown | opens *Request sent* · **Cancel request** |
| Friends | **✓** | green | opens *Remove karol.t as a friend?* · **Remove friend** · **Keep** |
| They asked the reader | **the envelope** | volt | accepts at once → **✓** |

- **On sheets it is worded:** *+ Add friend*, *Request sent*, *✓ Friends*, *Accept*. The taps are the
  same.
- **One tap updates that person everywhere on Home at once**: every row, See all and Home read that
  could show them is read again.
- **Cancel and remove are silent**, as the friends mechanics §3.4 has them.
- **A request refused under §4.1's rule (b)** — only possible from a card read before the subject
  turned the switch off — puts the button back to **+**, and the card leaves the row on the read that
  follows *(a call)*.
- **The marks are drawn**, never typed.

---

## 12. Where a request was found

- **Three new origins**, beside today's group, record, result, link and ranking: **same level** (with
  its sport), **new players**, and **same vibe** (Q30).
- **A request sent from a record keeps the row the record was opened from.** A record opened from Top
  10 is the ranking, with the row's sport.
- **No group-sheet origin**: its faces can't be tapped.
- **The receiver's card line is worked out when the card is read** (call 6):

| Found in | Line | Falls back to |
| --- | --- | --- |
| Same competitive level | *Your level in padel · 91% even* | *Found you at your padel level*, when either no longer has a level there |
| New in Raketa | *Found you among new players* | — |
| Same vibe | *6 things in common* | *Found you through your tags*, when none is shared any more |
| Top 10 | *Found you in the padel ranking* | — (today's line) |

- **The % and the count are today's**, not the day it was sent.
- **The notice reads the same line**, as the friends mechanics §12 has a request's notice read its
  card's.

---

## 13. Reading again

- **Each row is its own read** (§3). A row that fails shows nothing, and the rest of Home stands.
- **After any friend or join write from a row**, every row, See all and Home read that could show that
  person or group is read again, so one tap shows everywhere.
- **A people row holds still under the tap** (2026-11-15): the person's card stays where it stands and
  shows the new state, and §9.1 moves them on the row's next read — a return to Home, a pull — never
  under the thumb. Read at the tap, asking a fresh match on *Same vibe* made the card leave as it was
  pressed, the next fresh match taking its place. A block still takes the card off at once.
- **No live connection**: a row never changes while the reader looks at it.

---

## 14. Notifications

**None.** No push, bell line or email is told about any row: a newcomer arriving, a group heating up,
a vibe match. A request from a row is an ordinary friend request, and its notice is the friends
mechanics' [§12](../friends/the-mechanics.md#12-notifications), reading [§12](#12-where-a-request-was-found)'s line.
A withdrawn Join request tells nobody.

---

## 15. Numbers in one place

| What | Number |
| --- | --- |
| Hottest groups' size to appear | 3 or more players |
| Hottest groups' cards | up to 6 |
| Heat | 2 × games this week + 3 × new this month + players (to 20) |
| *Games this week* | court time in the last 7 days, not called off, scored or not |
| *New this month* | joined in the last 30 days, still members |
| HOTTEST | exactly one: the top heat, with at least 1 game this week |
| GROWING | +4 or more **and** at least ¼ of today's players |
| Faces | 4 on a group card · 6 on the sheet |
| *% even*'s colours | green ≥ 70 · amber 55–69 · red < 55 |
| *% even*'s ceiling | 96% |
| A good match | ≥ 70% even · ≥ 2 shared tags |
| People rows | 10 cards each |
| New in Raketa | joined in the last 30 days, strictly |
| Vibe % | 50 · 75 · 88 · 94 · 97 · 98 for 1–6 shared tags |
| Rest | on screen on 5 different days, per row |
| On screen | at least half the card visible; once per card, row and day |
| Top 10 | places 1–10 of General; all 4 sports |
| A See all page | 20 cards |
| Home re-reads the rows on return | when the last read is older than 30 seconds |
| Requests a day | no limit |

---

## 16. Where it lives (inferred)

The proposed shapes; the tickets settle them.

- **A new backend context, Discovery**, owns the three people rows, their See all reads and the rest
  count. It reaches Friends, Blocks, the Forecast, the profile, the user and the rating only through
  ports it declares, wired at bootstrap (ADR-0204 §10).
  - **A player directory projection**, fed through the outbox by the profile's and the user's events:
    the player id, the nickname, the first photo, the area cell, *joined*, the social tags (one row per
    tag), the switch, whether the account plays. A deleted account's rows go. A rebuild from the event
    store, safe to run twice.
  - **A current-level projection**, one row per player per sport with a level, from the rating's events
    (questionnaire and results alike): μ and σ. Indexed by sport and level. A rebuild.
  - **The rest count**: one row per viewer, row and player, with the distinct days on screen.
  - **Row selection** worked out on each read, measured against a large seeded crowd; a short
    per-reader cache only if the measurement asks for it (call 11).
- **Groups** owns the Hottest groups read (members and joined times from its projections, games from
  Bookings' projection through a port) and **Withdraw**, a new event on the group's stream.
- **Rankings** loses the hidden flag and block filtering, and gains the **Top 10 read**: the first ten
  rows of General in a sport (place, player id, nickname, photo, level, chip up/down/none, is-you),
  whether anyone is ranked in any sport, and which sport was chosen — an asked sport exactly, or a
  preferred sport falling through.
- **Player record and Friends**: §4.1's admission and all photos; §4.2's requests, no limit, and the
  new origins and lines.
- **Player profile**: the switch as a new event, the old events folding into it, the profile read
  returning it.
- **On the player surface**: the five row reads, the three See all reads (paged, an optional sport),
  the on-screen reports, Withdraw and the switch.
- **The player app**: one Home row frame in shared UI first; a **Discovery** feature for the people
  rows, their See all screens (pushed inside the Home tab, which stays lit), the comparison and vibe
  sheets and the reports; **Groups** for Hottest groups and the group sheet; **Rankings** for Top 10;
  **Friends** for the round button, exported through its public types. The shell composes them.

---

## 17. Calls made without a ruling

**Agreed by the product owner before PRD #789 was published:**

1. *Joined* is when sign-up finished; earlier players keep their real date.
2. *On screen* is at least half the card visible; one count per card, row and Warsaw day.
3. With no game anywhere this week, no HOTTEST, and bars measure against the top card.
4. *Games this week* counts every booked game in the last 7 days not called off, scored or not.
5. *N of your friends play here* counts friends who are members now.
6. A request card's line is worked out when read.
7. Withdrawing a Join request tells nobody.
8. In padel the % treats the two players as opposite sides.
9. A switched-off player keeps their face in group sheets, and their record stays open to people they
   share a group, game or friendship with.
10. Ranking places count everyone; *of N* counts everyone.
11. Everything is worked out on each read; cache only if measured slow.
12. The seed fills every row.

**Made while writing PRD #789** (open to overrule): the *Joined …* ladder with no weekday names; See
all pages of 20 cards; the request-line fallbacks *Found you at your padel level* and *Found you
through your tags*; a friend added after resting stays a gap; the group page's members-only rule
unchanged; Discovery as the people rows' owner, Groups for Hottest groups, Rankings for Top 10, Friends
for the round button.

**Made while writing this document, [#790](https://github.com/Raketa02/Raketa/issues/790)** (open to
overrule):

1. **Whoever runs a group the subject is in** still opens a switched-off subject's record (§4.1), as
   ADR-0159's 2026-10-02 strand had them: they answer that group's requests.
2. **No HOTTEST when the top-heat group had no game this week**, even when a lower group had games
   (§5.3), so the HOTTEST card is always the fullest bar.
3. **Ties in heat** go to more games this week, then the group id (§5.2).
4. **The reader's own face is never among a group's faces** (§5.6).
5. **An Official group that needs an administrator** reads *run by* its club (§5.9).
6. **Two sports with the same % even** go to the app's sport order; **two players with the same %**
   to the player id (§6.3, §6.6).
7. **Someone who asked the reader** is with the unconnected in New in Raketa (§7.2), as they count as
   fresh in the other two rows.
8. ***Joined …* counts Warsaw days**, and 28 days and up read *Joined 4 weeks ago* (§7.3).
9. **A rested player stays rested** in that row; the count never resets (§9.2).
10. **Top 10's fall-through goes round** the app's sport order (§10.3).
11. **Rankings › opens the page in General**, the list Top 10 is the top of (§10.4).
12. **A player who turns the switch off while on a row** leaves it on the next read, and a request
    already sent to them stays open (§4.3).
13. **A request refused under rule (b)** from a stale card puts the button back to **+**, with no
    sentence; the card leaves on the next read (§11).
14. **A player who left a group and rejoined** counts in *new this month* by the join that stands
    ([§18](#18-edge-cases)).
15. **With no HOTTEST, call 3's *top card* is read as the highest heat in the row** (§5.5), so no bar
    is ever more than full.

**Made while writing [the screens](the-screens.md)** (open to overrule): a row that fails to read is
left out, and the rest of Home stands; withdrawing shows no toast; on a Same competitive level card
only the other's face and nickname, *N sports ›* and the button are taps; the vibe sheet leaves the
carousel out for a player with no photo; the record's photos and the vibe sheet's are one carousel;
the four new sheets carry the mocks' × in a beige circle.

---

## 18. Edge cases

- **A reader with no level and no group** sees Hottest groups, New in Raketa, Same vibe and, once
  anyone is ranked, Top 10. *Same competitive level* is hidden, and *Your games* reads the groupless
  line.
- **A group exactly at 3 players** appears; one member leaving takes it off the row on the next read.
- **A group whose only games were called off** has 0 games this week, so it can't be HOTTEST.
- **A friends game booked in a group** counts towards that group's games this week, whoever was on it.
- **A member who joined 20 days ago, left and rejoined yesterday** counts once in *new this month*,
  by the join that stands *(a call: the joined time is the current membership's)*.
- **A Join request approved while the withdraw sheet is open**: Withdraw succeeds and changes nothing;
  the reader is a member, and the chip reads *You're in* on the next read.
- **Same level with one shared sport**: no *N sports ›*. The comparison sheet is reached only from
  *N sports ›*.
- **A player whose only level is a questionnaire** reads at most about 73% against anyone, so is a
  good match only against a close and sure level, and most often a gap further down the row.
- **Two players sharing all six tags** read 98%; the tie goes to the player id, since neither has an
  unshared tag.
- **A tag the vocabulary retires** still counts, as long as both hold it: a tag id is permanent.
- **New in Raketa and a newcomer with a level in no sport**: their tile shows no sport lines; a sport
  filter in See all leaves them out.
- **Top 10 with the reader at place 4**: the reader's card reads *You*, with the volt numeral and
  ring, among the ten.
- **Top 10 in a sport where the reader is blocked by the first-placed player**: both see the card;
  a tap on it reads *This record isn't available*.
- **A switched-off player in Top 10**: shown, and their record opens only to people they share a group,
  game or friendship with.
- **A blocked pair in one group**: each sees the other's face on the group sheet.

---

## 19. Out of scope

- Splitting any row by city, until a second city opens.
- Notifications, bell lines or emails about any row.
- Updating a row while the player is looking at it.
- A group page or member list for non-members; tapping a face in a group sheet.
- Search by name, mutual friends, a feed.
- Dismissing a card by hand.
- The club website's and the public site's own screens, beyond the club's Join request list dropping a
  withdrawn request.
- The engine review ([#781](https://github.com/Raketa02/Raketa/issues/781)) and General's entry rule.

---

## 20. The seed

**`make seed` fills every row**, through the use cases, and a second run changes nothing (call 12):

- **newcomers across the 30 days**, some unrated, one of them a friend of the protagonist;
- **shared tags** giving 1 to 6 overlaps with the protagonist;
- **group activity** giving one HOTTEST, one GROWING and an untagged group, plus a 2-player group that
  stays out;
- **a waiting Join request** from the protagonist, so *Asked* and Withdraw can be walked;
- **padel and tennis ranked**, **squash with two ranked players**, **badminton empty**, so Top 10's
  three states can be walked.
