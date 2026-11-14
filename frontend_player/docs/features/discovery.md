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
Hottest groups: Same competitive level (#802) will stand between them. A person on it is a
**`Joiner`** — the backend's word, since the glossary bars _newcomer_ (the Newcomer's 14 days).

**A tile is the face, _NEW_, the round button and three kinds of line** (`JoinerTile`): the nickname,
every sport with its dot and level — one to a line on Home, as many as fit in See all's columns, **none
for a player with no level** — and _Joined …_ by §7.3's ladder (`joinedAgo`, keyed by its rung in
`joinedLine`, so a rung with no words fails to compile). The tile's press opens the record
(`JoinerRecord`); the corner is `friends`' `RoundFriendButton`, a sibling of that press, never inside
it. The tile is spoken in the order drawn, _NEW_ left out since every tile says it (a call).

**See all is a screen pushed over Home, the tab lit** (`NewInRaketaScreen`, `/new-in-raketa`;
`shellTabs`' `INSIDE_A_TAB`, `pushedScreens`). The header is Rankings' — ‹, the title and the sport
pill on the right — and the pill offers **_All_** first (`shared/ui`'s `ALL_SPORTS`, a two-toned
dot), then the sports the first page says somebody holds a level in (`pillChoices`, which keeps the
chosen sport though it left that list). The grid is a two-column `FlatList`, newest first, **20 to a
page read on as it nears its end** (`useNewInRaketaPage`, an infinite query per sport; an end
reached while a page is coming joins it, and the pages are joined with each person once,
`joinPages`). Every state is drawn: a
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

**Not seen on a device**: the tile, the wash, the grid and the pill's _All_ against home rows 17–19.
