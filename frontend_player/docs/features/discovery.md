# discovery

**Home's people rows and their See all screens** — who is around the reader: new to Raketa (#801), at
their level (#802), sharing their tags (#803). [ADR-0204](../../../docs/adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md);
the spec set is [`docs/specs/home-rows/`](../../../docs/specs/home-rows/README.md), the words §31.
The backend context of the same name (#793) owns the rows' rules; this feature draws its answers.

**New in Raketa is the first people row** ([#801](https://github.com/Raketa02/Raketa/issues/801); the
Home rows screens §5; the mechanics §7; home rows 17–19). `NewInRaketaRow` reads `GET /new-in-raketa`
(`useNewInRaketa`, keyed `discoveryKeys.newInRaketa()`) and draws up to ten **portrait tiles**
(`shared/ui`'s `PortraitTile` on `HomeRowRail`'s `tiles` geometry) in the read's order, with _See all
›_ named _See all new players_. **Hidden with its heading** while the read is empty, in flight or
failed — a row that fails is left out (the screens §1), as Hottest groups is. Coming back to Home
re-reads it once its read is older than 30 seconds (`useOnReturn`, Q22). The shell draws it after
Same competitive level (#802), which stands between it and Hottest groups. A person on it is a
**`Joiner`** — the backend's word, since the glossary bars _newcomer_ (the Newcomer's 14 days).

**A tile is the face, _NEW_, the round button and three kinds of line** (`JoinerTile`): the nickname,
every sport with its dot and level — one to a line on Home, as many as fit in See all's columns, **none
for a player with no level** — and _Joined …_ by §7.3's ladder (`joinedAgo`, keyed by its rung in
`joinedLine`, so a rung with no words fails to compile). The tile's press opens the record
(`RowRecord`, every people row's); the corner is `friends`' `RoundFriendButton`, a sibling of that press, never inside
it. The tile is spoken in the order drawn, _NEW_ left out since every tile says it (a call).

**See all is a screen pushed over Home, the tab lit** (`NewInRaketaScreen`, `/new-in-raketa`;
`shellTabs`' `INSIDE_A_TAB`, `pushedScreens`). The header is Rankings' — ‹, the title and the sport
pill on the right — and the pill offers **_All_** first (`shared/ui`'s `ALL_SPORTS`, a two-toned
dot), then the sports the first page says somebody holds a level in (`pillChoices`, which keeps the
chosen sport though it left that list). The grid is a two-column `FlatList`, newest first, **20 to a
page read on as it nears its end** (`useNewInRaketaPage`, an infinite query per sport; an end
reached while a page is coming joins it, and the pages are joined with each person once,
`joinPages`). **The frame, the paging and the pill are every people row's** since #802: `domain/seeAll.ts` (`SeeAllSport`, `SeeAllPage<Person>`, `joinPages`, `pillChoices`), `hooks/useSeeAllPages.ts` (the infinite query, `LISTS_PEOPLE`, `SeeAllList<Person>`) and `components/SeeAllScreen.tsx` (the header, the pill keeping its last sports, every state, the list in one column or the caller's), each row handing in its key, its read and how it draws a person. Home's rows read through `usePeopleRow` (re-read on return, `LISTS_PEOPLE`). Every state is drawn: a
spinner, the failure with _Try again_ (`groups`' `ReadFailure`), offline, a later page refused under
the grid, the pull — the pill kept through a sport's failed read (the screen holds the last sports
offered), so _All_ is a tap away — and _Nobody new plays squash yet_ when a sport leaves nobody, or _Nobody new right
now_ with _All_ (a call: §31.7 words only the sport).

**One tap moves a person everywhere — wherever it is made** (the mechanics §13, the screens §8.5).
Both reads declare **`LISTS_PEOPLE`** (`shared/lib/query-client`), and every friend write and every
block reaches whatever declared it (`rereadPeopleLists`): a tile's round button, the record a tile
opens, an answer on FRIEND REQUESTS, a record Rankings or a notice opened, Members. So no surface hands
this feature's reads down, and `friends` and `blocks` never name its keys — `discovery` draws
`friends`' button, so naming them would run the import both ways. **Home's rows hold still under the
thumb** (`holdsPeople` in `usePeopleRow`; §13's _a row never changes while the reader looks at it_):
a friend write hands in its answer — whom, and where the reader now stands with them — and each row
draws it on the card where it stands and is marked stale rather than read again; the next read (a
return to Home, a pull, foregrounding) works §9.1 out again and moves them. **Read at the tap, the
card left under the thumb** (2026-11-15): asking a fresh match on Same vibe made them a gap, and the
next fresh match took their place; Same competitive level hid it only because nobody reaches 70% yet,
so its row is all gaps. See all reads again (its order is plain, so nobody moves), and a block or a
refusal that is the state moving re-reads every row at once — those cards leave. The round button's
write settles once every list has the answer. **Nothing is guessed into this feature's cache**: the
round button draws its next mark while its write is out, and the write's answer, or the read, lands
over it. `rereadDiscovery` is only Home's pull. **The
record a tile opens** sends its request from _new players_ (`foundIn`, `FOUND_AMONG_NEW_PLAYERS`).
**The first version handed the reads down** (a `reread` on the tile, a `rereadToo` on the record, two
from the shell) and the review found every write made off those surfaces left the row stale — Home's
30-second rule does not help a row read less than 30 seconds ago. `newInRaketa.test.tsx` walks the row, the tiles, every button
state and tap, the request line, and See all's pill, filter, paging and empty line.

**Same competitive level is the second row** ([#802](https://github.com/Raketa02/Raketa/issues/802);
the Home rows screens §4; the mechanics §6, §9; home rows 7–16). `SameLevelRow` reads `GET /same-level`
(`useSameLevel`, keyed `discoveryKeys.sameLevel()`, `LISTS_PEOPLE`, re-read on return as New in Raketa
is) and draws up to ten **dark cards** on a peeking `HomeRowRail`, in the read's order — fresh good
matches first, then the gaps, the server's (§9). **Hidden with its heading** while the read is empty —
the reader holds no level anywhere, or nobody shares a sport (Q23) — in flight or failed. A person on
it is a **`SameLevelPlayer`**: the card's sport (`shown`, the evenest the two share, or See all's
chosen one) and **every** shared sport most even first (`sports`), each a `LevelComparison` — both
levels, the % even, the level gap, the reader's band by name. The code never says _match_ (the
glossary's _Avoid_). **Nothing here computes the %**: it is the app's Forecast with one player a side,
the server's; a card whose own sport this build cannot name is left out, a shared one left off the
sheet.

**The card** (`SameLevelCard`, design-system 7.34) draws the reader's face (`useReaderFace`: the id
off the cached `/users/me`, the photo off `player_record`'s `useOwnFace`, read once per row or screen,
never per card), _You_ and the level; the % in **the game cards' inks** by the game cards' breaks
(`balanceTone`: green from 70, amber 55–69, red under 55), _EVEN_ under it always, the sport and its
dot; the other's face, nickname and level. Under them `shared/ui`'s **`ComparisonBar`** (7.33), its
dark paint: the Skill passport's 1,00–5,00 and four bands, a volt fill to their level, the white _YOU_
mark at the reader's, the reader's band bold. The footer is **the gap in words** (`levelGapOf` reads
the served gap to the hundredth, so −0,0199… is _0,02 below you_; _Same level_ when it rounds to
0,00), _· N sports ›_ in volt **only with more than one shared sport** (`moreSportsOf`), and the round
button. **Three doors** (the screens §4.2, a call): the other's face or nickname opens the record,
_N sports ›_ the comparison sheet, the button acts — every one sending its request from _same level_
in the card's sport (`foundAtSameLevel`). The card stands on **its own ground**, `levelCardGround`:
`night` cannot carry `gameGreen` at large text's 3:1 (2,88), and the ticket names the game cards'
tokens; the mocks' value measured, fenced as the stage's is.

**The comparison sheet** (`ComparisonSheet`, opened through `useComparing` / `ComparingSheet` from
the row and See all alike) is _You vs zofia.b_ with `friends`' worded button on the title row
(`BottomSheet`'s `action`), then one block per shared sport in the served order, divided by hairlines:
the sport and _You 2,71 · zofia.b 2,69_, the bar's light paint (mint fill, ink mark), the gap and the
_91% even_ `Tag` of its tone — the light version of the card's colour. **It reads nothing** (§6.5):
the person is looked up in the caller's current list, so a friend write moves the sheet's button with the card. **A read that moves them out of the list closes the sheet**, drawn as they last were — the row holds still through a write, but its next read works §9.1 out again, and on a row with more fresh matches than places a gap leaves it; a block takes them off at once — and **a later read bringing them back never reopens it** (a call; the spec review found the first version emptied the sheet mid-write and reopened it by itself).

**See all** (`SameLevelScreen`, `/same-level`, pushed over Home with the tab lit) is New in Raketa's
frame: ‹, the title, the pill — _All_ and the sports the reader shares with somebody, from the first
page — and **one full-width card per player**, best % first, friends where they fall, 20 to a page
(`useSameLevelPage`). **A sport re-reads with it**, and the server re-compares everybody holding a
level there (the mechanics §6.7). _Nobody to compare in squash yet_, or _Nobody to compare with right
now_ on _All_ (calls: §31 words neither). `sameLevel.test.tsx` walks the row's place and absence, the
card's fields, colours, gap words and _N sports ›_, the face and the button's origin, the sheet's
blocks and tags, See all's pill, re-compare, paging and empty line, and the request card's line.

**Same vibe is the fourth row** ([#803](https://github.com/Raketa02/Raketa/issues/803); the Home rows
screens §6; the mechanics §8, §9; home rows 2, 20–24). `SameVibeRow` reads `GET /same-vibe`
(`useSameVibe`, keyed `discoveryKeys.sameVibe()`, `LISTS_PEOPLE`, re-read on return as the others are)
and draws up to ten **pale tiles** on a peeking `HomeRowRail`, in the read's order — fresh good matches
(two shared tags or more) first, then the gaps, the server's. **Hidden with its heading** while the
read is empty, in flight or failed. The shell draws it after New in Raketa; Top 10 (#805) comes after
it. A person on it is a **`SameVibePlayer`**: the vibe % (the server's, 1 − ½ⁿ — nothing here
computes it), how many tags the two share (`inCommon`, the server's count), the shared tags in the
vocabulary's order — one this build cannot name left off the chips, the count kept — and the
relation. **Skill plays no part**, so a reader with no level sees it.

**The tile** (`SameVibeTile` on `shared/ui`'s `TintedTile`, design-system 7.35) is a light card
**washed from its top-left in the colour of their court poster** — `courtPosterFor`'s hue, so the same
person is the same colour everywhere — with the face, the nickname, the vibe % in a white circle, _6
things in common_ (`shared/vocabulary`'s `thingsInCommon`, which the request card says too), the
shared tags as 6.4's green `ok` tags, and the round button bottom-right. **The chips are fitted to
three lines by measurement** (`SharedTags`, `tagFit.ts`): every chip and every _+N more_ the tile
could say is laid out once, unseen, at the line's width, and `tagsThatFit` answers from those widths
— every chip when they all fit, else the most that leave _+N more_ (for the count it would then say)
room in the third line. Nothing is drawn until every width is in, and the three lines' room is kept
from the first frame (`shared/ui`'s `TAG_HEIGHT`), so a tile neither flashes a chip nor grows; a chip
is never wider than the line, cut by its own ellipsis at the width it was measured. _+N more_ is 6.4's new `more` tag,
dashed. **Two doors**: the button acts, asking from _same vibe_ (`FOUND_THROUGH_TAGS`, no group and no
sport); a tap anywhere else opens the vibe sheet. The tile's spoken name reads who, the %, the count
and every tag shared — including those under _+N more_, since which are drawn is the screen's width
(a call).

**The vibe sheet** (`VibeSheet`, handed the row's or See all's `usePersonSheet`) is _You and
karol.t_ with `friends`' worded button on the title row, then the face, the nickname and _6 things in
common_, every photo on the record's carousel, the intro in its marks, and every tag — the shared ones
green and reading _· you too_. **It reads the record** (§8.5) through `player_record`'s own parts
(`RecordRead`, `RecordTags`, `RecordIntro`), so it opens only where the record would and says _This
record isn't available_ where the record does. **The face opens the full record over the sheet**,
drawn inside it as the worded button's own sheets are — iOS drops a second native window opened while
the first is closing (#800) — and its requests are found through _same vibe_. **That record belongs
to one open of one person**: when a write in it moves them out of the row, the sheet closes under it
and takes it along, and the next tile opens its own sheet, never the record (the spec review's walk
found the first version reopening it). Which tile's sheet is up is **`usePersonSheet`**, #802's
comparing state made generic — the sheet follows the person's latest read, closes drawn as they were
when a write moves them out of the list, and never reopens by itself — and the comparison sheet now
takes it whole too (`useComparing`, a pass-through, went).

**Two calls against the ticket's words, for the product owner.** **No distance follows the count**:
§6.3's _· In your area · 0,6 km_ is _as the record writes it_, and the record's wire has no
`distance_km` — a record opened from Home writes no identity line — so the row takes §6.3's third
form, nothing. The reader's own area is known (their own record's `area_code`), but _In your area_
without the kilometres is none of §6.3's three forms, so it is not written either. #795's contract
says the sheet reads the distance off the record, which has none: **a backend ask**. **The intro is
upright**, as the record draws it — this app loads no italic Archivo, and a `fontStyle` on it is
synthesised on iOS and dropped on Android (two surfaces already accept that slant; the record chose
the marks), so §6.3's _in italic … as the record draws it_ contradicts itself and the record wins.

**See all** (`SameVibeScreen`, `/same-vibe`, pushed over Home with the tab lit) is the people rows'
frame with the tiles in **two columns**, most in common first, friends where they fall, 20 to a page
(`useSameVibePage`; See all's frame hands each item its column's width, and the three See alls ask
for a page through one `toPageAsked`); the pill offers _All_ and the sports somebody listed holds a level in, and a sport
keeps only them. _Nobody who shares your tags plays squash yet_, or _Nobody shares your tags right
now_ on _All_ (calls: §31 words neither). `sameVibe.test.tsx` walks the row's place and absence, the
tile's fields, the three-line fit with _+N more_ by laid-out widths, the button's origin, the sheet's
fields, carousel, intro, _· you too_, the face's record and its origin, the record going with a
sheet that closes under it, the refusal, See all's
columns, pill, filter, paging and empty line, and the request card's three lines.

**Not seen on a device**: the tile, the wash, the grid and the pill's _All_ against home rows 17–19;
the Same level card, its bar, the comparison sheet and See all against home rows 7–16; the Same vibe
tile, its tint over each poster hue, the chips' fit and _+N more_, the vibe sheet and See all against
home rows 20–24.

**Rows stay alive: the cards that came on screen are reported**
([#804](https://github.com/Raketa02/Raketa/issues/804); the Home rows mechanics §9.2, call 2; the
backend's #796, `POST /on-screen`). On Home — never See all — every card of _Same competitive level_
and every tile of _Same vibe_ that comes **at least half on screen** is told to the server, which
rests a player in that row on the fifth different day without an add. **At least half is of the
card's area**: the share of its height inside Home's band times the share of its width inside the
rail's view, so a card wholly along the rail but half up the screen counts, and so does one wholly
up but half along; the one peeking at a rail's edge never does. The geometry is `shared/ui`'s
(`onScreen.ts`, which `HomeRowRail` asks through `onScreen` and `HomeRow` feeds with where its
section stands), the page's band the shell's (`ShellScreen`'s `watchesOnScreen`); the rows only hand
the rail `useOnScreenReports(row)`. **Once per card, row and Warsaw day** (`domain/onScreen.ts`): a
card seen again that day is not told again, each row keeps its own count, and the day is the
platform's (`shared/date`) — ten past midnight in Warsaw is a new day while it is still yesterday in
UTC. **Batched** (`use-cases/onScreen.ts`): the first owed card opens a two-second window and one
report tells everything owed when it closes, at most the route's fifty in the order seen. **A report
that fails is never said**, and its cards stay owed, ahead of the rest: the next card seen that is
still owed — a new one, or one of them coming back on screen — opens the next window, which carries
them. There is no retry on a timer of its own; what a failed report left owed is dropped at a new
day's first card rather than counted as that day, and the window open at Warsaw's midnight is still
told as it closes — a report answered after the day turned changes nothing on the new day's ledger.
**The ledger lives as long as the row's place on Home** (a ref in the outer row, before it knows
whether it draws anybody): Home stays mounted under every pushed screen and tab and goes at
sign-out, so what was told today is one account's; a Home drawn again starts afresh and may tell a
card the server already counted, which counts it once. The reporter is made at the first card seen
(the rail's effects run before its row's), and the row going closes an open window and calls off a
report on its way. **A card coming into a row while Home is covered** — a friend write on See all
re-reading the row — counts nothing until Home is back in view, when what stands there is told; so
does a re-read landing while the app is in the background, where Android's JavaScript runs on.
**Calls for the product owner**: no time on screen is asked — a card a fling carries past at half
visible between two of the page's samples (ten a second) is seen; a sheet open over Home does not
hide the row from the count; and the phone's clock decides when its own day turns, so a phone set
wrong tells a day late or twice, which the server's own day absorbs. `onScreen.test.tsx` walks it
through the route tree on the fake clock — a card scrolled into view reported once, scrolled out and
in again the same day nothing more, the next day and Warsaw's midnight again, the peeking card and a
card never shown never, the batch, each row's own count, a refused report carried into the next with
nothing said, See all nothing, and a row read under See all or behind the home screen counted only
on the way back; `use-cases/onScreen.test.ts` holds the reporter to its window, the midnight window,
a late answer and its stop on a hand-turned clock.

**The three people rows are FOR YOU's lines** ([#820](https://github.com/Raketa02/Raketa/issues/820);
ADR-0205 §5; home refactor 6–11): **Players at your level**, **New in Raketa** and **Players with your
vibe** — only the words on screen change; the glossary's terms, the code's names and the endpoints
keep theirs (`DISCOVERY_COPY.*.line`). Each row component became a hook the shell calls
(`useSameLevelLine`, `useNewInRaketaLine`, `useSameVibeLine`), handing the line's title, what it
unfolds and its footer — _See all ›_ at the bottom right, to the same See all screen — or `undefined`
while the read holds nobody, is out or failed. **The read and the on-screen reporter are the line's**,
held while Home lives, so a report waiting to be sent outlives a close; **the cards are drawn only
while the line is open**, so a closed line reports nobody (the mechanics §9.2), and the rail settles
on its cards' edges. The copy is read inside each hook rather than at the module's top: `shell`'s
surface imports these, and a module-level read of `DISCOVERY_COPY` met the copy module half-loaded
through that cycle. The paragraphs above that say a row is _hidden with its heading_ and _See all ›
on the heading_ were true until this one. Walked in `sameLevel`, `newInRaketa`, `sameVibe` and
`onScreen.test.tsx` — the last now lays FOR YOU, the line and its fold out as a phone would, and adds
a closed line reporting nothing and only the open line's cards counted.
