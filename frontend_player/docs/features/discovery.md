# discovery

**Home's people rows and their See all screens** — who is around the reader: new to Raketa (#801), at
their level (#802), like them (#803). [ADR-0204](../../../docs/adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md);
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
block re-reads whatever declared it (`rereadPeopleLists`): a tile's round button, the record a tile
opens, an answer on FRIEND REQUESTS, a record Rankings or a notice opened, Members. So no surface hands
this feature's reads down, and `friends` and `blocks` never name its keys — `discovery` draws
`friends`' button, so naming them would run the import both ways. The round button's write settles
once the row and any open See all have read again; See all pushed over Home keeps the row mounted, so
both move. **Nothing is guessed into this feature's cache**: the round button draws its next mark
while its write is out, and the read lands over it. `rereadDiscovery` is only Home's pull. **The
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
the person is looked up in the caller's current list, so a friend write that re-reads it moves the sheet's button. **A write that moves them out of the list closes the sheet**, drawn as they last were — asking a fresh match makes them a gap, and on a row with more fresh matches than places the next takes theirs (§9.1) — and **a later read bringing them back never reopens it** (a call; the spec review found the first version emptied the sheet mid-write and reopened it by itself).

**See all** (`SameLevelScreen`, `/same-level`, pushed over Home with the tab lit) is New in Raketa's
frame: ‹, the title, the pill — _All_ and the sports the reader shares with somebody, from the first
page — and **one full-width card per player**, best % first, friends where they fall, 20 to a page
(`useSameLevelPage`). **A sport re-reads with it**, and the server re-compares everybody holding a
level there (the mechanics §6.7). _Nobody to compare in squash yet_, or _Nobody to compare with right
now_ on _All_ (calls: §31 words neither). `sameLevel.test.tsx` walks the row's place and absence, the
card's fields, colours, gap words and _N sports ›_, the face and the button's origin, the sheet's
blocks and tags, See all's pill, re-compare, paging and empty line, and the request card's line.

**Not seen on a device**: the tile, the wash, the grid and the pill's _All_ against home rows 17–19;
the Same level card, its bar, the comparison sheet and See all against home rows 7–16.
