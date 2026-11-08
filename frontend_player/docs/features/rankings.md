# rankings — the trophy on Home and the Rankings page

The client side of the backend's **Rankings** context: a ranking per sport, sorted by the Level, in
General and among your Friends. Built by [#775](https://github.com/Raketa02/Raketa/issues/775) for
PRD [#766](https://github.com/Raketa02/Raketa/issues/766), on the contract #768–#773 built, and
decided by [ADR-0203](../../../docs/adr/0203-a-ranking-per-sport-sorted-by-the-level.md). The spec
set is [`docs/specs/rankings/`](../../../docs/specs/rankings/README.md) and every sentence is
[the words §30](../../../docs/specs/matchmaking/the-words.md#30-rankings). The shell puts
`RankingTrophy` left of Home's bell; the page is `/rankings`, pushed over Home. The walks are
`components/rankings.test.tsx`.

**The page is General only, for now.** #775 draws the header, the reader's card in every General
state, the podium and the first page of the list; [#776](https://github.com/Raketa02/Raketa/issues/776)
the later pages and the _You · 212th_ button. The _General | Friends_ switch and the view the
phone remembers are [#777](https://github.com/Raketa02/Raketa/issues/777)'s, the _Show me in General_
switch on the hidden card [#778](https://github.com/Raketa02/Raketa/issues/778)'s, and Add friend from
a stranger's record [#779](https://github.com/Raketa02/Raketa/issues/779)'s. The domain already
carries every card state the contract has, so `JUST_YOU` and `NO_FRIEND_LISTED` are mapped and draw
nothing on a page that never asks for Friends.

**Every number is the server's, and this feature computes none of them.** The order, every place,
_of N_, the chip, the gap, and how many wins close it are worked out by the backend — the win count
reads the rating engine's own update rule, so nobody else may (the mechanics §7.2). What is this
feature's own is in `domain/ranking.ts`: which sports the pill offers (`pillSports` — all four, rated
first, each part in the app's order), which sport the page opens on (`openingSport`), and how three
rows stand on the podium (`podiumOf`).

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
the pill is the way to the page, and a number arriving is the badge's own move. It shows General's
place until #777 makes it follow the remembered view.

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
connection says so; nothing but the pull is drawn under the header while the first read is out.

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
has landed** — until then the list stays where it was. Each tap reads that page afresh. A row not yet
laid out is scrolled to as nearly as the header and an average row put it, and centred once it has
been, on the next few frames and whenever the content grows. **While a centring is owed the top of
the list asks for nothing**: a new list starts at its top, and would otherwise read the page above
before it reached the reader. The reader's own drag takes the list back. A jump refused says why where the button stood, with _Try
again_.

**Around the reader, the card and the podium wait at the top of the list**: they stand above the rows
again once the pages above reach place 1. A pull there reads the main read and the window around the
reader again.

**Calls made here, open to overrule:**

- the spoken names: the trophy _Rankings, 7th in padel_ (or _Rankings_), a row _7th, You, 2,71_, a
  step _1st, Inés, 3,40_, the card _your place: 7th of 13, 2,71, up 1 this week_, the pill's hint
  _Shows the ranking in another sport_ — §30 writes only what is drawn;
- _Back to Rankings_ on the last _Your rating_ — **owed to §30 from a root session**, with a row for
  it;
- places 1–3 in `coralInk` where mock 7 draws `coral` (design-system §1.2) — flagged for the product
  owner, because it departs from the mock by name;
- the hidden card draws the place and _Hidden from General_ without the switch: the server already
  serves `HIDDEN`, and #778 adds the switch;
- _Nobody ranked in {sport} yet_ follows the wire's `listed` being 0, so a sport whose only listed
  players are hidden from the reader draws neither that line nor a list;
- _New_ is a neutral `paper2` chip with `ink`: the spec names no colour for it;
- (#776) _You · 212th_ is a `dark` button, centred at the foot — the spec places it at the foot and
  draws no mock — with the hint _Shows your row in the list_;
- (#776) a tap on _You · {n}th_ for a row the list already draws scrolls to it and reads nothing: the
  page around the reader is read only for a row further down;
- (#776) around the reader, the card and the podium are drawn only once the window reaches the top,
  so the list never reads 3rd and then 187th.

The design calls are Part 16 rows of the design system (2026-11-08).

**Not seen on a device**: the whole page — the trophy beside the bell, the dark card's place and
level, the podium's steps, the rows and the tint, the drawn marks, and the pill over the header —
and #776's scrolling: a page landing at either end, the list holding still as a page lands above it,
the jump landing centred, and the button over the list. The suites say what the list reports (the
rows on screen, an end reached), because a test renderer lays nothing out.
