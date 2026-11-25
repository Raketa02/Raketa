# rankings — the trophy on Home and the Rankings page

The client side of the backend's **Rankings** context: a ranking per sport, sorted by the Level, in
General and among your Friends. Built by [#775](https://github.com/Raketa02/Raketa/issues/775) for
PRD [#766](https://github.com/Raketa02/Raketa/issues/766), on the contract #768–#773 built, and
decided by [ADR-0203](../../../docs/adr/0203-a-ranking-per-sport-sorted-by-the-level.md). The spec
set is [`docs/specs/rankings/`](../../../docs/specs/rankings/README.md) and every sentence is
[the words §30](../../../docs/specs/matchmaking/the-words.md#30-rankings). The shell puts
`RankingTrophy` left of Home's bell; the page is `/rankings`, pushed over Home. The walks are
`components/rankings.test.tsx`.

**Who built what.** #775 drew the header, the reader's card in every General state, the podium and
the first page of the list; [#776](https://github.com/Raketa02/Raketa/issues/776) the later pages and
the _You · 212th_ button; [#777](https://github.com/Raketa02/Raketa/issues/777) the _General |
Friends_ switch, the view the phone remembers, and Friends; [#778](https://github.com/Raketa02/Raketa/issues/778)
the _Show me in General_ switch on the hidden card, and the page following it; and
[#779](https://github.com/Raketa02/Raketa/issues/779) _Add friend_ from a stranger's record, sent from
the ranking. [#869](https://github.com/Raketa02/Raketa/issues/869) made the jump button say _Finding
you…_ while it reads (PRD [#867](https://github.com/Raketa02/Raketa/issues/867), the loading shimmer),
and [#870](https://github.com/Raketa02/Raketa/issues/870) made the page shimmer until it lands — the
first screen on the shared `Skeleton` and `Reveal`.

**Every number is the server's, and this feature computes none of them.** The order, every place,
_of N_, the chip, the gap, and how many wins close it are worked out by the backend — the win count
reads the rating engine's own update rule, so nobody else may (the mechanics §7.2). What is this
feature's own is in `domain/ranking.ts`: which sports the pill offers (`pillSports` — all four, rated
first, each part in the app's order), which sport the page opens on (`openingSport`), and how three
rows stand on the podium (`podiumOf`).

**Sign-up's hero draws a picture of the podium** ([#788](https://github.com/Raketa02/Raketa/issues/788),
`auth.md`): You on a volt first step between `stas.w` and `ines.d`, redrawn in auth because auth may
not import this feature. `PodiumSteps` is not exported for it, so **a change to the podium here does
not reach that picture by itself — whoever changes the podium checks the hero** (`StagePodium.tsx`).

**The page opens on the sport it is asked for, else the trophy's, else the deck's last, else padel**
(the mechanics §9; `openingSport`). The trophy's tap carries the sport of the reader's latest result;
a pass begun on the page carries the sport it was begun on. **With nothing carried the page reads the
trophy's sport itself**, off Home's read — so a tap made before Home answered still opens on it rather
than on the deck's, which the review caught as a race. With no result anywhere it reads `groups`'
`useDeckSport` — the group page's own judgement of the phone's last pick against the ratings, exported
for this — and **draws nothing below the header until it knows**, as ADR-0188 §4 asks of every
remembered choice. A ratings read that fails, and a Home read refused or waiting for a connection,
count as nothing known: the next answer down, and in the end padel and all four sports. A pick on the pill is
held while the page is up and kept nowhere — the phone remembers the view (#777), never the sport.

**The trophy is Home's read, drawn by this feature.** `GET /home`'s `ranking` rides on Home's one
read, so `proposals` maps it (`HomeRanking`, `useHomeRanking`), as it maps the friend requests and the
level asks that `friends` draws. It is drawn whatever Home says — a number only with a place — because
the pill is the way to the page, and a number arriving is the badge's own move. **The place is the
remembered view's** (#777; `placeIn`): General's, or Friends' once the reader last looked at Friends —
never the other view's when this one has none — so the number is always the place on the page it
opens. It draws no number until the phone has said which view.

**What this build cannot read is drawn as nothing, never guessed** (`rankingMappers`). A card in a
state newer than this build, a place sent without its number, a chip moving up with no count: each
would be a sentence about the reader the server never said. The contract check
(`mappers/wireVocabulary.ts`) makes a new code a compile failure first.

**The marks are drawn.** ▲ and ▼ are SVG triangles in `RankChip`, — a short rule, and the trophy an
SVG cup: §30 says so, and Archivo ships none of them.

**_Get your {sport} level_ is a pass of one sport that ends back on Rankings**, on that sport, with
Home beneath it: `onboarding`'s new `rankings` origin (`fromRankings`), landed by the entry gate
through `rankingsRoute`. The last _Your rating_ control reads _Back to Rankings_ — a call: §30 writes
no words for it, and the group pass's _Back to {group}_ is the pattern. The record of the pass is in
[`onboarding.md`](onboarding.md).

**A face, a row or a podium step opens the record**, on the page's sport; the reader's own opens
their own. Whose record is up is the screen's state, as on Members. **A step names its player by
nickname, the reader's own too**, as §30.7 writes it; only a row reads _You_.

**A pull reads the page again**, a refused read says why with _Try again_, and a read waiting for a
connection says so, each where the skeleton stood.

**Until the page has something to draw, it shimmers below the header** ([#870](https://github.com/Raketa02/Raketa/issues/870);
the loading shimmer log §8, Q4–Q7; design system 5.6). **The header and the sport pill are the real
ones throughout**, so the reader can change sport or go back while it loads. Below them, from the first
frame: while the view or the sport is still unknown, a shape of the switch's own size and corner in
the switch's place (the log's §12 call); then the real switch, and in the view's place **one fixed
skeleton for both views and every sport** (`RankingsSkeleton`) — a block at the listed place card's
height and the dark card's corner (the dark card drawn as a skeleton-tone block), three podium steps
at their heights, and rows filling the screen on the list's own white card, each with the row's
padding, the place column's room, the row face's circle, and bars for the name and the level. It
never predicts the page's true shape. **It shows on landing, on a sport change and on a General ↔
Friends change, only when that sport and view have nothing cached**: a sport or view read in the last
few minutes opens at once, read again quietly behind it, as General and Friends always are on opening.
**The page's one read decides it** (`Reveal`): the content is drawn underneath, hidden from sight and
from a listener, and comes in on one 200 ms cross-fade when the read finishes — lands, is refused
after its retries, or is held for a connection — so the failure or the amber note takes the skeleton's
place as the page would. **Once the page is in, it never goes back** during that view's mount: **a
pull never shows the skeleton**, the page staying under the pull's own spinner. A refusal or the
note is not the page, though: when _Try again_ or the connection back sets the read out once more
with still nothing to draw, the skeleton stands again, never a blank page. The sport and the view are
reads too, under a reveal of their own: a page that comes cached fades in from the skeleton that
stood while they were unknown, and one not read yet hands over to its own skeleton — the same shapes
on the same band, since one `SkeletonGround` stands under the header for both.

**_General | Friends_ is remembered per account on the phone** (#777; the screens §3; ADR-0203 §5,
its value under ADR-0188), General the first time: `rankingView`, read and kept as the deck's last
sport is (`useRankingView`), and judged on read (`rankingViewFrom`: anything this build has not heard
of is General). **The page and the trophy read the one value**, so a switch on the page is on the
trophy beneath it at once. The page draws no switch until the phone has answered, and nothing below
it until the sport is known too. **A view is another page**, read for that view — the card, the
podium, the list and the button are all the view's own — and the pill's sport carries over. **Opening
a view always reads it** (`refetchOnMount: 'always'`, General's main read and Friends alike), however
lately it was read: the screens §2–§3 say switching sport or view re-reads the page, and a friend added
or removed anywhere is in the table the next time Friends opens, with no friends write naming this
feature's keys.

**Friends is read whole** (`useFriendsTable`, one query, never paged): the server works it out on each
read. It hands the page the shape General's pages do (`RankingRead`), so one page draws both; its ends
ask for nothing, and its _You · 4th_ only ever scrolls, because the reader's row is always on hand.
**What stands below the card is the domain's** (`belowTheCard`): the podium and the table while
anybody is listed — the reader's own not-listed card above the friends' table included (Q7) —
_Nobody ranked in {sport} yet_ where nobody is, and **nothing where the Friends card is the page**:
_Just you so far_ and _None of your friends is ranked in {sport} yet_, each with **Add friends**.

**Add friends opens `friends`' own sheet** — your groups, each opening its Members, and your friend
link — exported for this, with `groups`' tiles and Members route handed in as the shell hands them to
You › Friends. The sheet and the record are the screen's, drawn beside its root and never inside it,
because the root — header, switch and page — is hidden from a listener while either is up
(`behindOverlay`).

**A not-listed card reads its view's words**, as §30.5 keys them (`notListedLine` takes the view): in
Friends a reader with a level and no result reads _Not ranked in padel yet — your first confirmed
competitive game puts you on the list_, and one with no level is asked for _one competitive game_;
General's lines count to the wire's 5.

**General is read in pages of 50, as two windows over one list** (#776; the screens §5.3;
`useGeneral`), each an infinite query. **From the top**, the main read is the first page — the card,
the podium and the first 50 rows, one kept order's — and each page after it is read below the last
one's cursor. **Around the reader**, the page with them in the middle, then the page above or below.
Every cursor is the server's, handed back as it came. A row that dropped past a cursor between two
reads comes back on the next page that way, and **is drawn once, where it already stands** — on the
page nearest the one the window read first (`joinPages`) — so nothing the reader is looking at moves
under them; a pull reads every page again and puts it right.

**The list is a `FlatList`, the card and the podium its header** (architecture Part 12). Within half a
screen of either end it asks for the next page that way — once: an end reached while its page is on
its way joins it, and **an end reached while the list is read again is owed**, asked for once that
read has landed, because the list says an end once and would not say it again to a reader holding
still at it. A page landing above the rows on screen is laid in without moving them
(`maintainVisibleContentPosition`). A page is drawn whole as it lands, fifty light rows, so the
reader's row is on hand to centre the moment a jump lands. A page refused says why at the end it was
asked for, with _Try again_, and the rows already drawn stay.

**The floating _You · 212th_ shows while the reader's row is off screen** (`jumpPlace`): only while
they are listed — never hidden from General (the mechanics §10), never off the list — and only once
the list has first said what is on screen, so it never flashes up before. A row is on screen once half
of it is. **A tap centres the reader's row**: where the list already draws it, a scroll and nothing
read; further down than the list has read, the page around them, **drawn as a new list only once it
has landed** — until then the list stays where it was. Each jump reads that page afresh. A row not yet
laid out is scrolled to as nearly as the header and an average row put it, and centred once it has
been, on the next few frames and whenever the content grows. **While a centring is owed the top of
the list asks for nothing**: a new list starts at its top, and would otherwise read the page above
before it reached the reader. The reader's own drag takes the list back. A jump refused says why where the button stood, with _Try
again_.

**The page ends at the tab bar's reach, and its rows do not pass under the bar**
([#881](https://github.com/Raketa02/Raketa/issues/881), 2026-11-25; design-system §10.1). Every other
tab screen now runs to the phone's foot under the floating bar and pads its end by the reach; this one
ends its layout at the reach, as a screen with a pinned button does. **On screen** and **centred** are
the list's own measure of its frame — FlatList's viewability, which shows the button, and
`scrollToIndex`'s middle — and it takes no inset, so a list running under the bar would call a row
hidden behind it seen and centre the reader's row half the bar too low. The list keeps its own end
(15, or the room the button covers) and the button its gutter, both inside the frame.

**While a jump reads the page around the reader, the button says so: _◌ Finding you…_**
([#869](https://github.com/Raketa02/Raketa/issues/869); the loading-shimmer log §9). It is
`Button`'s own `busy`: the spinner before the busy word at the dark fill, the busy word the button's
spoken name, and the button sized to its words, so its width changes as they swap. **It is busy only on a
jump that has to read** — a row the list has not drawn. A scroll is over before a spinner would
turn, so it is never busy, and Friends, read whole, never is. **It starts at the press and ends at
the first of three**: the reader's row on screen, when the button goes as it always has; the jump
refused, when the failure with _Try again_ takes its place; or the reader's own drag, when the read
still lands and swaps the list. A page landing with no row of the reader's ends it as well: the
server answers a reader no longer listed with its first page, and a busy button left up would take
no press until a drag. **A busy button takes no press**, so a second press reads nothing,
where it used to reset the read and start it again. A sport changed during a jump is another view,
so the busy goes with it. The state is the list's (`RankingList`), kept beside what it last said
was on screen and the centring it owes.

**Around the reader, the card and the podium wait at the top of the list**: they stand above the rows
again once the pages above reach place 1. A pull there reads the main read and the window around the
reader again.

**The hidden card carries the switch** (#778; the screens §4.5; the mechanics §10). Under the fold,
where the gap line was: _Hidden from General_ and 6.12's switch on the dark card's repaint — You's own
_Show me in General_, `player_profile`'s (`useShowMeInGeneral`, exported for this), written by the
same route and **named _Show me in General_, off**, because _Hidden from General_ is what off means
here. **The card is the server's and the switch is the profile's**: the switch is drawn only while the
card says `HIDDEN`, and stands where the profile holds it — or where it was pressed, while that write
is out. A refused write says why above the card, on paper, as the declaration's card says it, and the
switch is back off. No _You · 7th_ while hidden (`jumpPlace`, as #776 built it).

**The page follows the switch** (`cardBehindTheSwitch`; `useGeneral`'s `SWITCH_FOLLOWED_MS`,
`SWITCH_FOLLOWED_READS`). The ranking follows the profile through the outbox, whose delivery polls
once a second, so a card read the moment the write answers still says what it said before. **While
the card is behind the switch** — hidden with it on, listed with it off — **General is read again a
second after its last read, at most five times**, then waits for a pull, a focus or its half minute.
That is how turning it on from the card re-reads the page — a second after the press, never at once,
because at once is almost always before the delivery — and how a switch turned on You while Rankings
stands under the Home tab reaches the card. The switch followed is the one the profile **holds**
(`useShownInGeneral`), never a press still on its way, so a refused write follows nothing. Friends ignores the switch, and
follows nothing.

**A request from a record opened here is the ranking's** (#779; the screens §6; the mechanics §12–§13).
The page hands the record sheet its sport twice: as `sport`, what the record is about, and as
`rankingSport`, where it was opened — so _Add friend_ sends `RANKING` with the page's sport and no
group, and the other person's Home reads _Found you in the padel ranking_. A blocked pair's record,
or a hidden stranger's, reads the record's one refusal. The foot, the daily limit's sentence and the
Home card are [`friends.md`](friends.md)'s; a block closing the record is [`blocks.md`](blocks.md)'s.

**Calls made here, open to overrule:**

- the spoken names: the trophy _Rankings, 7th in padel_ (or _Rankings_), a row _7th, You, 2,71_, a
  step _1st, Inés, 3,40_, the card _your place: 7th of 13, 2,71, up 1 this week_, the pill's hint
  _Shows the ranking in another sport_ — §30 writes only what is drawn;
- _Back to Rankings_ on the last _Your rating_ — **owed to §30 from a root session**, with a row for
  it;
- places 1–3 in `coralInk` where mock 7 draws `coral` (design-system §1.2) — flagged for the product
  owner, because it departs from the mock by name;
- _Nobody ranked in {sport} yet_ follows the wire's `listed` being 0, so a sport whose only listed
  players are hidden from the reader draws neither that line nor a list;
- _New_ is a neutral `paper2` chip with `ink`: the spec names no colour for it;
- (#776) _You · 212th_ is a `dark` button, centred at the foot — the spec places it at the foot and
  draws no mock — with the hint _Shows your row in the list_;
- (#776) a tap on _You · {n}th_ for a row the list already draws scrolls to it and reads nothing: the
  page around the reader is read only for a row further down;
- (#869) **_Try again_ on a refused jump is a jump of its own**, once per refusal: busy again, and
  owed its centring afresh. The log names only the press, but a plain button during the retry's read
  would restart it on a press, which is what #869 ends, and a drag since the refusal had already
  taken back the centring the press owed. The failure stands until Query's next tick, so a second tap
  on it is ignored;
- (#869) **for the product owner**: a jump made offline is busy until the connection is back — the
  read waits for it and then lands — or until the reader drags. The log's list of ends has no
  offline case, and nothing says _offline_ there; the page's amber note in the button's place is the
  obvious answer, not built;
- (#869) _Finding you…_ is the loading-shimmer log's word (§9, Q8), and §30.7 does not have it yet —
  **owed to §30 from a root session**, as a row under _The jump button_;
- (#870) **a read refused once and asked again keeps the skeleton** through Query's retries, and the
  failure takes its place only once they are spent. The PRD counts _fails once and starts retrying_ as
  finished, but that is the rule for a screen of several reads (#871), so one slow part never holds
  the rest; here the page has one read, and revealing it would draw a blank page;
- (#870) **_Try again_, or the connection back, stands the skeleton again** while the read is out with
  still nothing drawn. The log's _once revealed, never back_ is read as the page's content: a refusal
  or the amber note is not the page, and a blank page between them and the content is the frozen look
  the PRD removes. It was a blank page before #870 too;
- (#870) **a ratings read held for a connection, with nothing read yet, counts as refused** for the
  opening sport (`useOpeningSport`), as a refused one did: offline with nothing cached and a trophy
  that names no sport, the deck's sport waits on the ratings, and the page would otherwise shimmer for
  as long as the phone is offline, where before #870 it stood blank. It opens on padel — or the deck's
  last — and its own read says it is offline; Home's Top 10, which reads the same, opens the same way;
- (#870) **the switch waits for the sport too**: it was drawn once the view was known, and the shape
  in its place stands while the view _or_ the sport is unknown, as the ticket writes it — a moment the
  switch could not be used for anything below it anyway;
- (#870) the switch's shape takes the switch's own corner (`radius.seg`), not a pill's, so it is the
  shape the switch replaces; the face is a circle, as the ticket writes it, where the real face is
  `PlayerPhoto`'s rounded square;
- (#870) the place card's block is the listed card with one gap line — every other card is shorter,
  and the skeleton predicts none of them; the level's bar is four figures of `num.m` wide, IBM Plex
  Mono's 600-unit advance; the name's fills its column, as a name may;
- (#870) a pull made while the skeleton is up reaches the list underneath and reads the page again,
  but its spinner is hidden with the list until the reveal;
- (#776) around the reader, the card and the podium are drawn only once the window reaches the top,
  so the list never reads 3rd and then 187th;
- (#777) the switch is the plain segmented control (6.3), as rankings 2 draws it — the track `line2`,
  the raised segment white — and stands fixed under the header, outside the list, so it never
  scrolls away;
- (#777) **Add friends** is a primary (coral) button in a light card, as _Get your {sport} level_ is:
  §30.6 names no colour, and the Friends page's black pill is that header's own (Part 16);
- (#777) the trophy's spoken name on Friends, _Rankings, 4th among your friends in padel_;
- (#778) the card's switch is drawn _Hidden from General_ and named _Show me in General_ — §30.4
  writes the line, and a listener hearing _Hidden from General, off_ would hear the opposite;
- (#778) turned on, the switch stands on over a card still reading _Hidden from General_ for the
  second or so the ranking takes to follow — §30 has no words for _on its way_, and none are drawn;
- (#778) the page follows a turned switch a second apart, five reads at most, each reading every page
  of General's window — the outbox's pace, and a ceiling so an outbox that has stopped costs five
  reads, not one a second;
- (#778) a refused write from the card is a coral note above the card, the switch back off;
- (#778) **for the product owner**: §30.4 draws _Hidden from General_ with the switch beside it, and
  the switch is _Show me in General_ — so the card reads _Hidden from General_ beside a switch that is
  off, which a sighted reader could take for _not hidden_. Built as the words write it; the line is
  the switch's label, its track on the right;
- (#778) **for the product owner**: _on the fold line's right_ (the screens §4.5) is read as the line
  under the fold, the words on the left and the track at the right edge, as the gap line stands.

#775's and #776's design calls are Part 16 rows of the design system (2026-11-08); #777's depart
from nothing in it — the segmented control and a primary button, each as the system draws it. #778's
switch on the dark card is 6.12's `onDark`, a Part 16 row of its own (2026-11-08).

**Not seen on a device**: the _Show me in General_ switch under the hidden card's fold, the note
above the card, and the gap line coming back as the page follows; the switch under the header and its
two views, the Friends cards with
_Add friends_, the sheet over Rankings, and the whole page — the trophy beside the bell, the dark card's place and
level, the podium's steps, the rows and the tint, the drawn marks, and the pill over the header —
and #776's scrolling: a page landing at either end, the list holding still as a page lands above it,
the jump landing centred, and the button over the list; and #869's _Finding you…_ on the dark
button, with its width change as the words swap; and #870's skeleton — its shapes against the page
they stand for, the band's tone, beat and tilt, and the cross-fade (owed to the phone walk,
[#877](https://github.com/Raketa02/Raketa/issues/877); its frame cost on the A32 is
[#873](https://github.com/Raketa02/Raketa/issues/873)'s). The suites say what the list reports (the
rows on screen, an end reached), because a test renderer lays nothing out.

**The ranking shows everybody, and the page has no switch** ([#799](https://github.com/Raketa02/Raketa/issues/799),
[ADR-0204](../../../docs/adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md)
§2; the Home rows screens §9.2). The server lists every player at their true place — a player the
reader blocked, or who blocked the reader, and one who turned their switch off, included — so the
`HIDDEN` card state, the hidden card with _Hidden from General_ and You's switch under its fold, and
the page following the switch (`cardBehindTheSwitch`, `useGeneral`'s one-second re-reads) are gone,
with `RANKINGS_COPY.hidden` and the `rankings` → `player_profile` import they needed. `useGeneral`
takes the sport alone. **A tap on a blocked player** — a row or a podium step — opens the record
sheet, whose read is refused with the one code and which draws _This record isn't available_, as a
group's Members list already did: nothing here knows about blocks. **Places run without a gap** now,
so the notes that explained a podium reading 1, 3 and 4 and a list skipping places were rewritten;
`podiumOf` is unchanged — it was always the first three rows. The only switch on the page is
_General | Friends_. The paragraphs above on the hidden card, the page following the switch and #778's
calls describe #778 and are superseded. **The record from the ranking** shows all of a stranger's
photos and no daily-limit sentence, and a request the server refuses unnamed re-reads the record
quietly ([`player_record.md`](player_record.md), [`friends.md`](friends.md)). Walked in
`rankings.test.tsx`: Marek, blocked, at 4th and his row's refusal; no switch on the page; all of
Piotr's photos with _Add friend_; no limit sentence; the quiet re-read.

**Top 10 is the last of Home's rows** ([#805](https://github.com/Raketa02/Raketa/issues/805), PRD
[#789](https://github.com/Raketa02/Raketa/issues/789);
[ADR-0204](../../../docs/adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md);
the Home rows mechanics §10, the screens §7; the words §31.1, §31.11; home rows 2, 25–27). The shell
draws `TopTenRow` after Same vibe and re-reads it on Home's pull (`rereadTopTen`). It reads `GET
/top-10` (`useTopTen`, keyed under `rankingKeys.topTen()`), and **every place, level, chip and the
fall-through are the server's**; what is this feature's own is in `domain/topTen.ts`: which read the
row asks for (`topTenAsk`) and what it draws for the answer (`topTenFace`).

- **It opens where the trophy would**: the Rankings page's own reads, lifted into `useOpeningSport`
  so the page and the row share them — the trophy's sport, else the deck's last, else padel, nothing
  read until it is known — **sent as `prefer`**, so the server falls through, going round the app's
  order, to a sport where somebody is ranked, and **says which**: the pill shows the answer's sport.
- **A pick on the pill asks for that sport exactly** — _Nobody ranked in squash yet_ (§30.7's
  `nobodyRankedLine`, as §31.11 cites it) for a sport with nobody in it — and is held while Home is up,
  kept nowhere. **It re-reads this row alone**: its own query, the pill saying the pick at once and
  **the cards on screen staying until the new ones land** (`keepPreviousData`), so nothing blinks.
- **Hidden with its heading** while the read is out, refused, unreadable (a sport this build has never
  heard of reads `null`), or says nobody is ranked in any sport (`anyone_listed`).
- **The pill offers all four**, rated first, as the page's does: `pillSports`, the same reads.
- **The card** (`TopTenCard`): the numeral (`TopTenNumeral`) behind the card's left edge, the card
  covering its last `size.topTen.overlap`; `shared/ui`'s `PortraitTile` with the nickname — _You_ on
  the reader's own (`rowName`) — the level in mono, and the move: a drawn triangle and the count,
  ▲ in `volt`, ▼ in `gameCoral`, no ground, slanted together as an italic. **No chip for no change or
  _New_** — the wire sends none. The reader's own card has a **volt numeral and a volt ring** outside
  its edge. Spoken as its place, name, level and move (`topTenCardLabel`).
- **The numeral is drawn as SVG text** — a gradient fill and an outline take SVG — each figure three
  times: a `line` hairline, the paper outline, then the fill, `numeralTop` → `numeralFoot` (the
  screens' _night-to-teal_). **Its box is worked out from Archivo's metrics**, not measured on screen
  (tabular figures, 0,625 em each), so the card's overlap is known before layout and _10_ is a figure
  wider, tracked so the _0_ stands over the _1_'s foot.
- **A tap opens the record from the ranking**, on the row's sport — `sport` and `rankingSport`, as the
  page hands them (#779) — so a request reads _Found you in the padel ranking_; the reader's own card
  opens their own; **across a block the sheet reads _This record isn't available_**, its own drawing of
  the server's refusal.
- **_Rankings ›_ opens the page on the row's sport, in General** (the mechanics §10.4): it chooses
  General first, so the page — and the trophy, which reads the same view — then remember General.

Walked in `components/topTen.test.tsx`: hidden with nobody ranked and on a refusal; the opening
sport, the fall-through, the deck's and padel, nothing read until Home answers; the pill's four; a pick
re-reading this row and nothing else, the cards held while it is out; the empty line; a failed pick
put back; ten cards, _10_ in two figures, two cards; the reader's volt card; the chips; the record,
the ranking origin, a block and the reader's own; _Rankings ›_ in General; the pull.

**Calls made here (#805), open to overrule:**

- **a pick whose read fails puts the pill back** on the sport before it, its cards never having left —
  the screens leave a failed row out, and a row that vanished on a pick would take its pill with it;
- **while a pick's read is out the pill already says the new sport over the old cards** — the cards
  are held so the row never empties, and the pill answers the tap at once. For that moment the row is
  two sports: _Rankings ›_ names and opens the pill's, and a card opens its record on the card's own;
- **the pill lists the reader's rated sports first**, as the Rankings page's does (`pillSports`; the
  ticket's _as the Rankings page's does_), where the screens §7.3 write _the other sports in the app's
  order_ — the same order for anyone rated in sports that lead the app's order, different for, say, a
  squash-only reader;
- _Rankings ›_ is spoken _Rankings in padel_, and the pill's hint is _Shows Top 10 in another sport_ —
  §31 writes only what is drawn;
- **▼ is `gameCoral`**, coral's hue lifted for a dark ground (the mock's #EF8772 within a step), not
  `coral` itself: on the wash's full `ink` coral is 4,50, a rounding from failing, and the count stands
  where the wash is thinner; `gameCoral` is 7,12 there. ▲ is `volt`, 13,96;
- **the move leans by a skew** (−12°), the triangle with the count: no italic face is loaded, as the
  vibe sheet's intro found (#803), and a number's slant is cheap to draw where a sentence's is not;
- **the reader's volt ring is drawn on paper**, against 1.3's _volt is a stroke only on dark_, and in
  `volt`, not `voltStroke` — the token for a stroke on paper that means volt: the mock draws a bright
  volt ring, `voltStroke` is a dark olive that would read as another colour, and the ring's inner edge
  touches the dark card it bounds, where volt is 13,96. It is not the only mark — the card reads _You_;
- **the numeral's paper outline has a hairline of `line` outside it** — paper on paper alone draws
  nothing, and home rows 25.3 draws a grey edge round the paper;
- **the empty line** is `rlLabel` in `muted`, left-aligned under the heading — the page's line,
  uncentred because a row has no centre to stand on;
- **the bar's backdrop is the row's**: a tap elsewhere on Home leaves it open, and a tap on another
  row's card does what it does — **for the product owner**, since the deck's pill folds on a tap
  anywhere;
- **on a narrow phone the open bar can run past the row's left edge**: it ends where the pill ends and
  grows leftwards, all four sports wide — about 268pt, where the room left of _Rankings ›_ is about
  290 on a 390pt phone and 260 on a 360pt one — and Android lands no touch outside the row, so the
  first sport's leftmost points go dead there. Not clamped: a shorter bar would drop a sport.

**Not seen on a device — a look is owed against home rows 25–27**: the numeral (its size, gradient,
outline and hairline, _10_'s two figures touching, the baseline near the card's foot, the overlap),
the card's portrait and wash, the move's slant and colours on a pale photograph, the volt ring, the
pill on the heading's line and the bar sliding over _TOP 10_ while _Rankings ›_ stays, and the row's
spacing among the others.

**Top 10 is FOR YOU's last line** ([#820](https://github.com/Raketa02/Raketa/issues/820); ADR-0205
§5; home refactor 12, 13). `TopTenRow` became `useTopTenLine`, which hands the shell the line's title
(`TOP_TEN_COPY.line`), the cards on the `numbered` rail — stepping and snapping by an item, the
numeral beside the card (`itemWidth`) — or _Nobody ranked in squash yet_, and **a footer holding
today's pill and _Rankings ›_**, unchanged until #821 turns the pill rightwards and renames the link;
the bar slides over the footer rather than the heading. **The pick is held by the line**, which lives
while Home does, so it outlives a close. **The line never empties under the pill on a pick** (`useTopTen`'s
`lastDrawn`): while a pick's own read has nothing yet — refused, or the pick before it cancelled under a
second pick and read again — the cards last drawn stay, since FOR YOU closes a line that stops being
shown and an open Top 10 would close under the reader. `keepPreviousData` alone covered a read in
flight, not a failure. **On a 360pt phone the open bar's leftmost sport is cut by the line's edge**:
the bar still grows leftwards from the pill, about 268pt, and the footer leaves it some 253 inside the
line, which clips where the row's heading let it run into the gutter. #821 turns it to open rightwards
from the footer's left, where all four fit — **a look is owed** until then. Hidden, as before, while nobody is
ranked in any sport. Walked in `topTen.test.tsx`, which now opens the line first and adds the pick
kept across a close and a second pick, before the first lands, refused with the line kept open.

**Top 10's footer: the switcher on the left, _Open the rankings ›_ on the right**
([#821](https://github.com/Raketa02/Raketa/issues/821); ADR-0205 §5, Q19, Q37; home refactor 12, 13,
note 4). The pill stands first in the open line's footer and reads _● Padel ›_, its chevron pointing
the way it opens — the mocks' _‹_ is overridden — and the link, `TOP_TEN_COPY.rankings`, reads _Open the
rankings ›_, spoken _Open the rankings in padel_ (`topTenRankingsLabel`), going where _Rankings ›_ went:
the Rankings page on the line's sport, in General. **The switcher opens to the right**, with the deck's
own unfold: `RowSportPill` hands `SportPill` and `SportBar` `opens="right"`, so the current sport stands
dark at the bar's left end where the pill stood, its chevron turned back to _‹_, and the others slide
out after it in the app's order, nearest first. The bar's slot starts the bar's inset before the
pill's left end and runs to the footer's right edge, **over the link**: the footer's backdrop takes a
tap there and folds the bar, leaving Home where it is. **How far it fits, measured** in the Archivo
the pill draws (`rowSportBarFit.test.ts`): the open bar is about 322pt, 304 of pills — not the ~268
this record said under #805 and #820. From a 375pt phone up it opens inside the line, every sport in
reach. On a 360pt phone — the product owner's A32 — its round end meets the line's inner edge, cut by
under a point, and badminton's far ~6pt stand past the footer, where Android lands no touch. On a
320pt phone it is cut by about 40pt, badminton half hidden: **a known limit, for the product owner**
(a scrolling bar, or a narrower pill in the footer, would be the ways out). The leftward bar ending at
the pill was cut on a 360pt phone too (#820). A pick still re-reads Top 10 alone, and the closed line
shows neither part.
Walked in `topTen.test.tsx` (the footer's order and words, the bar's direction and slot, the link's
name and destination); the drawing's direction in `SportPill.test.tsx` and `RowSportPill.test.tsx`.
**Not seen on a device** — a look is owed against home refactor 12, 13: the pill at the footer's left,
the link at its right, and the bar sliding open to the right over the link.
