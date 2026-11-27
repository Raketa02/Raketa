# ADR-0205 — What waits for your answer goes behind an envelope, and Home's rows fold into FOR YOU

- **Status:** Accepted
- **Date:** 2026-11-16
- **Replaces [ADR-0204](0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md)
  §1's order, and its *"the header and today's rows stay on top, unchanged"*** (§1, §4, §5). Home
  now reads the header, *Get your level*, *Your games* and **FOR YOU**. The four cards that waited
  on the player leave Home for **Needs your answer**, and the five rows fold into FOR YOU's lines.
  Three more parts of ADR-0204 move with them:
  - **§3's card** loses its heat bar, its *+N this month* and its sport line. The group sheet keeps
    the sports and *new this month*, as it shows them today. The heat bar is drawn nowhere now,
    though heat still orders the groups and picks the tags (§5);
  - **§8's *Rankings ›*** reads ***Open the rankings ›***, in the open line's footer, beside the
    sport pill, which now opens to the right (§5);
  - **§9's card line** (*Your level in padel · 91% even*, *Found you among new players*, *6 things
    in common*) is no longer drawn on a friend request (§1). Where a request was found is still
    recorded and still served.
- **Amends [ADR-0202](0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md)**
  in four places:
  - **§1's Home bullet:** the **FRIEND REQUESTS · n** row, and its place under the friends game
    invitations and above *Your games*. A request waits in Needs your answer, and its tile names no
    group. In place of the group, it shows the sender's level in every sport they hold one in (§1).
    *Found you in the padel ranking*, which ADR-0203 §9 put on that card, goes with it.
  - **§3's *"the request is at the top of Home"*:** the friend link opens Home with Needs your
    answer already up, and the request in it (§1). The tile no longer reads *Invited you to Rakieta*.
  - **§5's *"a FRIENDS GAME · n row at the very top of Home"*** and its *"Home reads, top to
    bottom"*: an invitation waits in Needs your answer, one big tile at a time, and *Not this time*
    takes it out of the sheet (§1).
  - **Its 2026-11-07 amendment:**
    - the **ASKED FOR A LEVEL · n** row between FRIEND REQUESTS and *Your games*;
    - *"Home now reads, top to bottom: friends game invitations, friend requests, asks for a level,
      Your games"*;
    - **the hand-off that drew the ask's card instead of *Get your level***.

    The ask waits in Needs your answer, and *Get your level* shows whenever ADR-0200 §7 says it
    does, whether or not anybody asked (§4). The bell lists *level asked* while its card waits in
    Needs your answer, as it did while the card was on Home.
- **Amends [ADR-0203](0203-a-ranking-per-sport-sorted-by-the-level.md)** in two places:
  - **§5's *"The bell keeps its corner"*.** The trophy takes the corner, the bell sits left of it,
    and the envelope left of the bell (§2). Nothing else about the trophy or the bell moves.
  - **§9's *"The card … read[s] Found you in the padel ranking"*.** The card no longer draws it
    (§1). The notice still does, and the request still records the ranking.
- **Restores [ADR-0200](0200-a-level-is-asked-where-play-begins.md) §7's Home card as it was
  decided.** ADR-0202's amendment no longer draws an ask in its place (§4).
- **Narrows [ADR-0198](0198-the-player-app-is-not-built-for-screen-readers-for-now.md) §1, for
  three things the grilling ruled by name** (Q11, Q39):
  - FOR YOU's lines open and close at once under the phone's *Reduce motion*;
  - Needs your answer's title takes the screen reader's focus when the sheet opens;
  - each line says whether it is open.

  ADR-0198 §1 asked no new work for screen readers or the phone's settings. These three are asked,
  and nothing else: no announcement, no spoken confirmation and no other setting followed. The rest
  of ADR-0198 stands, and §3's *every pressable carries a name* covers the lines' and the footers'
  labels.
- **Names five exceptions to the locked design system**
  ([ADR-0012](0012-player-app-design-system.md)), because the mocks lead (§9).
- **Leaves standing:**
  - **the bell**: its list, its rows, its number and its visit (ADR-0189's 2026-10-09 amendment);
  - **Home's tab badge**, `needing_you`: the games that need you and the payments to confirm;
  - **You › Payments**, and *Your games*: its card, rail and data;
  - **every answer the four cards give**, and their notices: *Not now* and *Accept* on a request,
    *Not this time* and *Accept and pay* on an invitation, *Confirm* and *Fix* on a payment, a level
    ask's *Not now* and its questionnaire, *Carry on*;
  - **every rule of ADR-0204's rows**: who is in each, heat and its tags, the *% even*, the 30 days,
    the vibe %, fresh, gaps and rest, Top 10's sport, a row of at most 6 or 10;
  - **the people See all screens and the group sheet**, which are only reached from a new place;
  - **ADR-0204 §7's *on screen***: a closed line draws no tile, so it reports nobody.
- **Does not decide:**
  - a sport or distance filter on the Groups heating up page;
  - counting good matches, or any count that scores a candidate;
  - new polling, a push, or a socket for counts or for the envelope;
  - a count or a badge on FOR YOU itself, or a line dismissed by hand;
  - remembering the open line across a restart;
  - the club website and the public site, which don't change.
- Settles PRD [#810](https://github.com/Raketa02/Raketa/issues/810). It was decided in the Home
  refactor grilling on 2026-11-16 (Q1–Q46 there), from the product owner's brief *Home Screen
  Refactor* and its mocks, and written by [#811](https://github.com/Raketa02/Raketa/issues/811).
  - **Specified by** [`docs/specs/home-refactor/`](../specs/home-refactor/README.md): the brief, the
    grilling's decision log and the mocks. The home-rows, friends, rankings and Games and Fill in
    specs and the words are amended in place by the ticket that ships each part. Until then,
    where they and this record disagree, this record and PRD #810 win.
  - **The mocks lead on design.** Where an ADR, a spec or the locked design system disagrees with a
    mock on a look, the document changes, by name. **Their numbers, names and counts are only data**:
    no rule is read off them.
  - **Built by** the backend's [#812](https://github.com/Raketa02/Raketa/issues/812) (the people
    rows' totals), [#813](https://github.com/Raketa02/Raketa/issues/813) (Groups heating up's total
    and page), [#814](https://github.com/Raketa02/Raketa/issues/814) (a request's sport levels) and
    [#815](https://github.com/Raketa02/Raketa/issues/815) (what's new in Needs your answer), and the
    player app's [#816](https://github.com/Raketa02/Raketa/issues/816)–[#823](https://github.com/Raketa02/Raketa/issues/823).
    Walked by [#824](https://github.com/Raketa02/Raketa/issues/824).

## Context

**Home is cluttered.** Tomek plays padel at 2,71 and tennis at 3,10, and is in Kazimierz crew. He
opens Home and reads up to ten stacked blocks:

- first, up to four rows that wait on him: a friends game invitation, *To confirm*, friend requests
  and *Asked for a level*. A player rated in nothing reads *Get your level* there too, or a
  friend's ask in its place;
- then *Your games*;
- then five full rails, each drawn whole with faces, figures and subtitles: *Hottest groups*,
  *Same competitive level players*, *New in Rakieta*, *Same vibe players* and *Top 10*.

Everything shouts at once, so nothing is the one thing to look at.

- **The cards that wait on him push his own games down, and they are drawn too small.** A friend
  request is a 74%-wide tile with a face, a title, a where-line and a reliability chip squeezed
  together. Its buttons sit at different heights from tile to tile, depending on how long the lines
  above them run. A friends game invitation carries a lot of information in the same narrow tile.
- **He can't see how much there is to explore.** A rail shows at most six groups or ten people, and
  nothing says whether there are 11 more or 400.
- **He can't browse groups.** *Hottest groups* shows six, and no screen lists more. The only other
  way to find a group is to type a club or group name into Join a group's search.

**What the codebase already has:**

- **The bell's *new*, kept on the server.** Opening the recent notices records a visit,
  `RecentNoticesOpened`, on the player's Bell stream. It is recorded only when later than the last,
  so it is idempotent and never moves back. Its watermark, `seen_through`, is the newest notice the
  list showed, never the moment of the tap. The count, `new_count`, travels on the notices' own read
  and never on Home's, because **nobody knows Notifications exists**: it is told by the other
  contexts and tells none of them (`backend/.claude/rules/notifications.md`).
- **`GET /home`**, which Proposals assembles. It carries the friends game invitations, the friend
  requests and the level asks through Proposals' own ports, and `needing_you`, which counts the
  payments to confirm. A friend request carries one `sport` and `level`: the sport of the screen it
  was sent from.
- **Each row's own read**, none of which returns a total. *Hottest groups*' grouped members query
  already counts every group with 3 or more players, to pick its six.
- **The app's own bottom sheet** on the modal stage, capped at 88% of the screen, with no navigation
  hook allowed inside a sheet. **The row frame**, whose rail peeks at 0.74 of the content width and
  can snap. **Home stays mounted under every tab** since [#809](https://github.com/Raketa02/Raketa/pull/809).
- **A rule against animating a size frame by frame**: under the New Architecture, Reanimated 3.16
  freezes and then jumps. A size changes once, and a layout transition moves the frames
  (`frontend_player/CLAUDE.md`).

**The alternatives:**

- **Keep the cards on Home and shrink them.** It is still five things above *Your games*. The product
  owner asked for one thing at a time.
- **Keep *To confirm* on Home**, because a seat held with a deadline is urgent. It is the most urgent
  thing that waits on him, so it goes **first** in the sheet (Q14, Q32). Home's tab badge still
  counts it, so the tab still pulls him in when money waits, and the notice and the email still carry
  the deadline.
- **An envelope always in the header**, with an empty sheet behind it. A button that is usually empty
  is noise. It is there only while something waits, and its slot collapses with the bell and the
  trophy staying where they are (Q5).
- **Another mark than an envelope**, because the friend button's volt envelope already means *they
  asked you*. Both mean *someone asked you*. The overlap is accepted, and the header's is ink (Q16).
- **Keep *new* on the phone.** Two phones would disagree, and something already seen would be new
  again on the other one. The bell solved this on the server, and the envelope does it the bell's way
  (Q30, Q42).
- **Put the envelope's count on its own read, as the bell's is.** §3 says why it rides on Home's.
- **Count good matches**: players at 70% even or more, or with 2 shared tags or more. It scores every
  candidate one by one, which is the expensive path, and a busy city still reads a big number. A
  count says how much there is to explore (Q17, Q33).
- **No counts.** They were kept because an agent's read of the code found them cheap, and a test per
  row holds them to it (Q34, Q45).
- **Uncapped counts.** *Players at your level* would scan its whole pool. The agent estimated 10–30 ms
  on a row that takes 67 ms at 50,000 players. Capped at 100, it is usually free.
- **Several lines open at once, or the open line remembered across a restart.** One line is open at a
  time, and Home starts quiet (Q10).
- **A See all for *Hottest groups* that lists only groups he isn't in, or that filters.** The page
  shows the row's own order, his groups included, so the row is the page's first six (Q35).

## Decision

### 1. What waits for your answer goes behind an envelope: *Needs your answer*

**Needs your answer** is the sheet the header's envelope opens, and everything waiting in it.

- **Four sections, always in this order, each a sideways rail and each hidden while empty** (Q6,
  Q8, Q14, Q32):
  1. **TO CONFIRM · n**: one tile per payment to confirm, replacing today's one card with stacked
     rows. It shows the game, the club and his share, the deadline in amber while it has one
     (*Confirm your payment by 14:40*, or *Fix your card by 14:40* and that nothing is paid now),
     and **Confirm** or **Fix**, as today. A payment whose time ran out, and which he may still
     confirm while the seat is free, has no deadline, as its row has none today.
  2. **FRIENDS GAME · n**: one big tile at a time on the **paging** rail, full width, with dots from
     two (Q9, Q46). Its content is today's: *Karol's game*, the clock, the faces with who's in,
     *Saturday 10:00 · Wisła Park · Court 3 · Padel*, **Not this time** and **Accept and pay 25 zł**.
  3. **FRIEND REQUESTS · n**: a wider tile, about 0.83 of the content width (Q2, Q28). It shows the
     face, *Inés wants to be your friend*, her reliability chip (*✦ 98*), and a line with **every
     sport she holds a published level in**, in the app's sport order: *● Padel 3,40 · ● Tennis
     2,90*. The line takes at most two lines, and is left out when she holds none. Then **Not now**
     and **Accept**. **The where-line and every found-by line are gone**: *With you in Kazimierz
     crew*, *Invited you to Rakieta*, *Found you in the padel ranking*, and ADR-0204 §9's three.
  4. **ASKED FOR A LEVEL · n**: the faces and *Kuba and Zofia want to play squash with you*, with no
     subtitle, *You're on question 5* included. Then **Not now** and **Get your squash level**, or
     **Carry on** for a questionnaire left halfway.
- **Tiles in a rail are as tall as the tallest, with their buttons at the bottom** and titles held to
  two lines, so the buttons sit level across the row (Q3).
- **The sheet** is the app's own bottom sheet. It is only as tall as what it holds, up to the sheet's
  usual cap, and scrolls beyond that. It closes with ✕, a swipe down or a tap outside it (Q8).
- **Answering** (Q7):
  - the answered tile leaves, and an emptied section goes;
  - answering the last item closes the sheet, and the envelope goes;
  - something that arrives while the sheet is open appears in it at once.
- **A tap that opens something else** (Q24):
  - **another sheet** (her record from a face, the payment confirmation, a card set up for an
    invitation): Needs your answer steps aside, and comes back when that sheet closes if anything
    still waits;
  - **a screen** (the squash questionnaire): Needs your answer closes for good, because nothing
    navigates from inside a sheet.
- **Links and notices that pointed at one of these cards open Home with the sheet already up**
  (Q25): the friend link, the friends game invitation notice, and anything else that targeted one of
  the four. **When nothing waits by then, Home opens as it is**, with no sheet: the sheet is never
  shown empty. A friend link that made friends of a crossing request, or that a block swallowed,
  lands so *(a call made while writing #811)*.
- **The bell lists *level asked* while its card waits in Needs your answer**, as it did while the card
  was on Home. A friend request's and an invitation's rows still clear from the bell once answered.

**Where a request was found is still recorded**, and the line worked out from it is still served,
for the app versions already on phones. No tile in this app draws it.

### 2. The header: envelope, bell, trophy

- **Envelope, bell, trophy, right-aligned in that order** (Q15). The trophy takes the far-right
  corner. The bell and the trophy keep everything else they do.
- **The envelope is there only while something waits for his answer.** When nothing does, its slot
  collapses, and the bell and the trophy don't move (Q5).
- **It is a Feather `mail` mark in ink** (Q16). It carries **the bell's count badge**: the same
  component, tone `news`, ink, *99+* above 99 (Q4). The badge counts what is **new** (§3).
- **It is named *Needs your answer***, with *, 2 new* while the badge shows.

### 3. The envelope's *new*: a visit with a watermark, owned by Proposals, counted on `GET /home`

**What is new** (Q29, Q31): an item that arrived since he last closed the sheet.

- **Each kind of item has an arrival instant:**
  - a friend request, its asked-at, which exists today;
  - a friends game invitation, its Invited seat's invitation;
  - a payment to confirm, its refusal;
  - an ask for a level, **each asker's own ask**, which no read serves per asker today.
- **A new asker on a card already there counts**, by their own ask. A second friend asking him for a
  squash level is a new person.
- **A change of state never moves an arrival.** A payment that moves from *Fix your card* to
  *Confirm* is not new.

**The visit** (Q30, Q42) is the bell's pattern, applied to the sheet:

- **Closing the sheet records a visit**: an event on a stream per player that Proposals owns, as the
  Bell is one per player that Notifications owns. **Every way the sheet goes away is a close**: ✕,
  a swipe down, a tap outside, the last answer, and a screen it hands over to. Stepping aside for
  another sheet is not, because the sheet comes back *(a call made while writing #811)*.
- **Its watermark is the newest item the sheet showed**, never the moment of the tap. Something that
  arrived after that item is still new, even when it reached the server between the phone's read and
  the close. Something that arrived while the sheet was open, and that he therefore saw, is not.
- **A visit is recorded only when its watermark is later than the last visit's**, so it is
  idempotent and **the watermark never moves back**. A phone closing the sheet on an older read,
  after another phone closed it on a newer one, records nothing. The bell's visit is ordered by the
  server's own clock; this one's watermark comes from the phone, so it is the watermark that is
  compared.
- **The count is the items whose arrival is past the watermark.** It is a new field on `GET /home`,
  and the visit is a new write under the player's own path. **It is kept on the server**, so two
  phones agree.
- **Unchanged:** Home's tab badge still counts the payments to confirm, and the bell's number is
  untouched.

**Why its count rides on Home's read when the bell's does not.** The bell's count stays on its own
read because nobody knows Notifications exists: if Home carried it, Proposals would have to ask
Notifications, and the context that is told by everybody would become one that answers somebody. The
envelope's case is the other way round:

- **The items are Home's own.** Proposals already gathers all four kinds through its ports to serve
  `GET /home`: three as lists on the wire, and the payments to confirm into `needing_you`. The count
  is the same four compared with a watermark Proposals keeps, so no context learns about another that
  it doesn't already ask.
- **A count on its own read would gather the four a second time**, through the same ports, on every
  Home open, or keep a copy of them somewhere else.
- **The count arrives with three of the four lists it counts**, so for those the envelope's badge and
  what the sheet holds come from one reading.

So the record belongs to the context that serves Home's read, and the count travels with the lists it
counts. **To confirm's rows stay on their own read**, `GET /players/me/payments-to-confirm`, as
today. When that read fails, no envelope is drawn for them, and Home's usual re-reads retry
(decision log §3.6). Serving them on `GET /home` too is left to the backend ticket.

### 4. Home, top to bottom, and *Get your level*

1. **The header** (§2).
2. ***Get your level***, while Tomek is in a group and rated in nothing (ADR-0200 §7's own
   condition), **whether or not someone asked him** (Q13). The ask itself waits in Needs your answer,
   and is never drawn in this card's place.
3. ***Your games***, unchanged, but for one line: a player in no group reads ***Join a group to get
   games — see Groups heating up, just below.*** (Q38).
4. **FOR YOU** (§5).

### 5. FOR YOU: five folding lines

**The five rows fold into five quiet lines** under the eyebrow **FOR YOU**. Each is a white card
with a title on the left, a grey count pill and a chevron on the right, and nothing else (Q20).

| Line | The row it shows | What its count counts (§6) |
| --- | --- | --- |
| **Groups heating up** | Hottest groups | every group with at least 3 players |
| **Players at your level** | Same competitive level players | everyone holding a level in a sport Tomek plays |
| **New in Rakieta** | New in Rakieta | everyone who joined in the last 30 days |
| **Players with your vibe** | Same vibe players | everyone sharing at least one tag with Tomek |
| **Top 10** | Top 10 | no count |

**Only the words on screen change.** The glossary's terms, the code's names and the endpoints keep
theirs, and the copy deck records the new titles.

- **Opening and closing** (Q10, Q12):
  - a tap anywhere on a line opens it;
  - **one line is open at a time**: tapping another line closes the first and opens the second;
  - tapping the open line's header closes it. Taps on tiles, swipes, the footer links and the Top 10
    sport switcher never close a line.
- **The open line** has an ink border and a soft shadow, and its chevron turns down. The count pill
  stays.
- **Motion** (the brief, Q11):
  - the content unfolds from nothing, fading in as it grows, in about a quarter of a second, fast at
    first and settling at the end. The lines below slide down to make room;
  - if the opened content would be cut off at the bottom of the screen, the page eases down just
    enough to show it;
  - closing folds the content up a little faster, and the lines below slide back;
  - switching lines folds the first, then unfolds the second;
  - **no size is animated frame by frame**: the size changes once, a layout transition moves the
    frames, and per frame only opacity and transform move.
- **Inside an open line** (Q22):
  - the tiles are today's, swiping sideways and now **settling on tile edges**;
  - **Groups heating up**'s tile loses its heat bar, *+N this month* and its sport line. It reads *14
    games this week* on the left and *11 players* on the right. The group sheet keeps every detail;
  - **Players at your level**'s tile loses *0,02 below you*.
- **Footer links, at the bottom right of the open content** (Q18, Q19, Q37):
  - Groups heating up: **All groups ›**, to the new page (§7);
  - the three people lines: **See all N ›**, to their See all screens, N being the line's count;
  - Top 10: **Open the rankings ›**, replacing *Rankings ›*. **The sport switcher moves into the
    footer, on the left**: *Padel ›*, sliding open to the right with today's animation. The closed
    Top 10 line shows neither.
- **Which line is open** (Q10, Q38): at app start, none. Home remembers the open one while the app
  stays alive, across tab switches, and never across a restart. **For a player in no group, Groups
  heating up starts open**, because joining a group is their next step.
- **Empty, loading and failed** (Q21): a line is drawn only once its read has returned something to
  show. With all five hidden, FOR YOU goes too. A line that empties while open closes and goes. Top
  10 keeps *Nobody ranked in squash yet* inside the open line, as the row does today.
- **What a closed line does** (Q23):
  - **every line's read still runs when Home opens**, for its count and for its hidden-when-empty
    rule, on Home's usual schedule;
  - **a closed line draws no tiles**, so a tile is on screen, and reported, only while its line is
    open.

### 6. The counts: pools, not good matches, capped at 100

**A count says how many there are to explore, never how many are a good match** (Q17, Q33). In a
busy city the two people lines will usually read *99+*, and that is intended.

- **The field:** each of *Hottest groups*, *Same competitive level players*, *New in Rakieta* and
  *Same vibe players* answers a new `total`.
- **What it counts:** the distinct groups or people that qualify for the row, under the row's own
  exclusions: the reader, a block either way, *Show me to new people* off, and an account that
  doesn't play. **A person is counted once across sports.**
- **The cap:** counting stops at **100**, and the phone draws **99+** past 99, in the pill and in
  *See all N ›* alike.
- **How each is counted** (Q45): always in SQL, on the row's own qualifying condition.
  - **Hottest groups:** the number of groups its grouped members query already counts. **No new
    statement.**
  - **New in Rakieta:** one COUNT over the last 30 days' sign-ups, on the joined-at index. It costs
    nothing when the row came back with fewer than ten.
  - **Same vibe:** folded into the one pass over the tag rows as a window count. **Never a second
    pass.**
  - **Same competitive level:** taken from the candidates the level windows already read, once there
    are 100 or more. Otherwise, one statement that stops counting at the cap.
- **Forbidden ways to count:** draining the widening level windows, looping the vibe batches, or
  counting players at 70% even or more. Each scores candidates one by one, and none of these totals
  counts good matches.
- **Held by tests:** a statement counter for tests, and a test per row asserting that its total adds
  **at most one statement** to the read, and **none** for *Hottest groups*. A timing of Home on the
  Android phone against #809's numbers comes before the branch merges.
- **They refresh when the line's read does**: returning to Home, pull to refresh, a push, a write that
  invalidates it. Nothing new polls.

### 7. The Groups heating up page

**All groups ›** opens a new screen on Home's stack, *Groups heating up* (Q18, Q35, Q36).

- **Which groups:** every group with at least 3 players, **whether the reader is in it or not**. His
  own are marked *You're in*.
- **Order:** the row's one order. HOTTEST, then GROWING by heat, then untagged by heat; ties go to more
  games this week, then the group id. **The row is the page's first six.**
- **Pages:** 20 at a time by cursor, and the first page carries the total, which is the line's count.
- **Tiles:** the line's simplified group tile, at full width. Each card is the row's card, read whole
  for the twenty on the page: who runs it, the club, the sports, the faces with the reader's friends
  first, the reader's relation and the Join policy.
- **Taps:** a tile opens the same group sheet. The chips (*Join*, *Ask to join*, *Asked*, *You're in*)
  behave as on Home, with the same optimistic writes and the same cache effects.
- **No filter**, by sport or distance.
- **Drift between pages is accepted.** Heat is worked out on every read, so a group whose heat changes
  between two pages can shift place, as on the people See all screens.

### 8. Accessibility and motion, by name

ADR-0198 §1 asked no new work for screen readers or the phone's settings. The grilling asked for three
things by name (Q11, Q39), and only these:

- **Reduce motion:** FOR YOU's lines open and close at once, with no fold or fade. The scroll into
  view still happens. It reads the app's existing reduced-motion hook.
- **Needs your answer's title takes the screen reader's focus** when the sheet opens.
- **Each line is a button that says its title, its count and whether it is open**: *Players at your
  level, 14, collapsed*. Each footer link is its own button.

The labels themselves are ADR-0198 §3's *every pressable carries a name*. Touch targets stay 44 pt.
No announcement, no spoken confirmation and no other setting is added.

### 9. The design system's named exceptions

The design system is locked ([ADR-0012](0012-player-app-design-system.md)). The mocks lead, so where
they break a rule, the system changes to match, each change made with its theme value, its rule, its
audit and a Part 16 row, in the player ticket that first needs it:

1. **Shadow:** a seventh named shadow, for the open FOR YOU line.
2. **Count pill:** the grey count pill, as a fenced pill exception.
3. **Friend request tile width:** a new measured width for the tile in the sheet, about 0.83 of the
   content, taken from the mock, beside the standard 0.74.
4. **The header's envelope:** the ink envelope, beside the friend button's volt one, with one meaning
   for both: *someone asked you*.
5. **New components:** the folding line, closed and open, its footer row, and the sport switcher's
   right-opening direction.

### 10. On the player surface

**Every change is additive.** Old app versions stay on phones for months, and each is regenerated into
the player app's types:

- **a `total`** on each of the four row reads (§6);
- **a friend request's levels**: the sender's published Level per sport, for every sport they hold one
  in, in the app's sport order. The single `sport` and `level` pair stays for old clients;
- **the envelope's count** on `GET /home`, and **the visit**, a new write under the player's own path
  (§3). The reads behind the sheet carry what the phone needs to name its watermark, the newest item
  it showed: each item's arrival, or a token for it. The backend ticket settles which;
- **the Groups heating up page**: a new paged read in the Groups context, on its own router as
  *Hottest groups* is (§7).

Nothing leaves the contract.

## Consequences

**Easier**

- **Home is quiet.** Tomek reads his games and five titles, and opens one thing at a time.
- **Nothing waiting on him is lost.** Everything is behind one envelope, in a fixed order, and the
  envelope says when something is new.
- **A friend request and an invitation are drawn large enough to read**, and their buttons line up.
- **The counts say how much there is**, and a groupless player lands on the groups they could join.
- **Groups can be browsed.** For the first time, a screen lists every group with a crowd.
- **The new count costs Home little**: one more field on a read Home already makes, from lists it
  already gathers.

**Harder**

- **Proposals keeps a second kind of *seen*.** The envelope's visit is a new stream per player beside
  the bell's, with its own watermark. The two *new*s mean different things and must never be read as
  one: the bell's counts notices, and the envelope's counts what waits.
- **Every kind of waiting item needs an arrival instant**, and an ask for a level needs one per asker,
  which no read serves today. A fifth kind added to the sheet later has to bring one, or it is never
  new.
- **The watermark leaves a window open, as the bell's does.** An item whose arrival is older than the
  newest one the sheet showed, but which reached Home's read only after the phone's read, counts as
  seen though it was never shown. The backend ticket keeps that window narrow, and names it where it
  can't close it.
- **A payment's deadline is one tap further away.** *To confirm* leaves Home's body. Home's tab badge,
  the notice and the email still carry it, and it is first in the sheet.
- **So is a friends game invitation's 24 hours, with less to pull him back.** No tab badge counts an
  invitation, as none did on Home. Once he has closed the sheet, an envelope with no badge is the only
  mark on Home, beside the notice. Silence still counts as *Not this time*, so an invitation he
  forgets runs out.
- **Every line still reads when Home opens**, closed or not, because its count and its hiding need the
  read. Four of the five now count too, and *Players at your level* is cheap only because of the cap.
  A test per row holds each to one statement at most, and the phone walk times Home before the merge.
- **Counts read *99+* in a busy city.** That is intended, and it says *there is more*, not *99 people
  are at your level*.
- **A request no longer says where it was found.** The origin is still recorded and served, and no
  tile in this app draws it.
- **The design system takes five exceptions** at once, among them the first shadow on an ordinary card
  and a second meaning drawn as an envelope.
- **Three small screen-reader and motion features are built** while ADR-0198 pauses the rest. Each one
  must be kept working, and tested, until support returns as a whole.
- **Order drift on the groups page.** A group can move between two pages as its heat changes.

**Neutral**

- **The rows' rules don't move.** Who is in each row, its order and its six or ten are ADR-0204's.
  Only how they are drawn, and the count, change.
- **The bell, Home's tab badge, You › Payments and *Your games* are untouched.**
- **The contract only grows.** No field leaves, and an app version already on a phone keeps working.
- **The club website and the public site don't change.**
