# Home rows: the spec set

**What PRD [#789](https://github.com/Raketa02/Raketa/issues/789) is drawn from.** The product owner's
brief *new rows home* and its mocks, copied here from `rakieta_v2.0/4-features/5-login_signup_refactir`
(the brief) and `rakieta_v2.0/4-features/6-home_improve` (the mocks) so that every session can read
them, then grilled on 2026-11-13/14 (Q1–Q37 there, the
[games and fill-in mechanics' Q131](../games-and-fill-in/the-mechanics.md#appendix-c--decision-log)).
Landed by [#790](https://github.com/Raketa02/Raketa/issues/790) on 2026-11-14.

| File | What it holds |
| --- | --- |
| [the-mechanics.md](the-mechanics.md) | What happens: Home's order, who sees whom, each row's rules (heat and its tags, the % even, New in Rakieta's 30 days, the vibe %), fresh, gaps and rest, Top 10, the friend button and where a request was found, with every number |
| [the-screens.md](the-screens.md) | Each row, card, sheet and See all with every state, and which mock draws it |
| [`mocks/`](mocks/) | The 42 mocks, renamed (the [index](#index) gives each original name). PRD #789 says 44; the folder holds 42, and a PDF of the brief that isn't copied |
| [home_rows_feature.md](home_rows_feature.md) | The product owner's brief, verbatim but for the brand's spelling ([ADR-0211](../../adr/0211-the-brand-is-rakieta-everywhere.md) §6). Its paths point at the product owner's desktop: read `…/6-home_improve/N_….png` as the index's file. Where the brief and these documents disagree, these documents win: they carry the grilling's rulings |

**The decision** is [ADR-0204](../../adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md).
The terms are in the root [`CONTEXT.md`](../../../CONTEXT.md), under **Discovery** (the people rows,
the % even, the vibe %, fresh, gap, rest and on screen), **Groups** (Hottest groups, Heat, HOTTEST,
GROWING, and a Join request's withdraw), **Rankings** (Top 10), **Player profile** (*Show me to new
people*), **Player record**, **Blocks** and **Friends**. Every sentence a player reads is in
[the words §31](../matchmaking/the-words.md#31-home-rows).

## How to read the mocks

1. **The mocks lead on design, and on nothing else.** The brief says *"these mockups take priority
   and must guide the final user interface"*, and *"mocks are just mocks … so don't hardcode data"*.
   The product owner ruled in the grilling that **no rule is read off a mock**: not an order, a
   threshold, a percentage, a state or a count. Where a mock and a sentence disagree on a look, the
   mock wins, unless PRD #789, ADR-0204 or a ticket overrides it **by name**. Every override known
   today is under [*Overrides*](#overrides), and nothing here overrides silently. On a rule, the
   mechanics win.
2. **Every name, initial, tag and number in a mock is sample data** (note 1). *Zofia*, *91%*, *14
   games this week*, *▼1*, *Joined on Monday* all come from the backend and, for testing, from the
   seeds.
3. **The mocks predate rulings that hold everywhere**:
   - a player is named by their **nickname**, never with an @
     ([ADR-0199](../../adr/0199-a-player-is-known-by-their-nickname.md)), so *Zofia B.* reads as
     *zofia.b*, and *You vs Zofia B.* as *You vs zofia.b*;
   - the app is **Rakieta** ([ADR-0211](../../adr/0211-the-brand-is-rakieta-everywhere.md)), so the mocks' *Rakieta* reads as written;
   - the bottom bar is **Home · ⚡ Play · You** (#576), with Home lit, as every full-screen mock draws
     it.
4. **Cite a mock by its number**: *home rows 22.1*. The numbers are the product owner's, decimals
   included. The second of two files both numbered 17 is **17.2**. The file names were cleaned of
   typos (`homre`, `competiive`, `se_all`) and zero-padded so they sort.
5. **No mock draws Home's top**: mocks 1 and 2 start at *HOTTEST GROUPS*. The header, today's rows and
   *Your games* stand above it, unchanged ([the screens §1](the-screens.md#1-home-top-to-bottom)).

## Which parts of each mock lead

| # | Mock | What leads | What doesn't |
| --- | --- | --- | --- |
| 1 | Home, the first rows | The rows' order and spacing, the headings in grey caps with *See all ›* in ink, the card sizes and how each row is cut at the right edge | The data and names (notes 1–2); the friend leading Same level (note 7); *Joined on Monday* (note 6); no header above it (note 5 of *How to read*) |
| 2 | Home, the last rows | New in Rakieta, Same vibe and Top 10 in that order, Top 10's header with the pill and *Rankings ›* | *▼1* on place 1 (note 1); the friend leading Same vibe (note 7); the names |
| 3 | A group card, HOTTEST | The striped band in the group's colour, the shield badge overlapping it, *▲ HOTTEST* top-right, the name, the dots and sports (cut with an ellipsis), the two figures, the green *+3 this month*, the heat bar, four faces, the black *Ask to join* | The faces' letters (note 3) |
| 3.2 | A group card, Asked | The white outlined *Asked* chip | Nothing |
| 4 | A group card, GROWING | *+ GROWING*, the green *+4 this month*, the outlined *You're in* | The bar's length (note 1: it is the heat over the HOTTEST card's) |
| 5 | A group card, no tag | A card with no tag, the black *Join* | Nothing |
| 6 | The group sheet | The title row with the one button, the × close in its beige circle, the rounded badge, *Closed group · run by Ogrody 33 · Ogrody 33*, the sports written out, the two outlined stat cards, six faces and *7 of your friends play here*; *Asked* drawn cream-amber here | The faces' letters; only *Asked* is drawn (the screens §3.5 designs the rest) |
| 7 | The Same level row | The dark card: both faces and levels, the % in its colour with *EVEN* and the sport, the *YOU* mark, the volt fill, the band track and its four names with the reader's in bold, the footer | Zofia, a friend, first (note 7) |
| 8, 10 | A Same level card, above you | The fill running just past the mark; the white **+** | Nothing (10 is 8 cropped again) |
| 9 | The comparison sheet, a friend | *You vs …* with *✓ Friends* in mint, one block per sport, the light bar with its `mint` fill (the theme's mid green, as PRD #789's *mint fill* means) over the pale bands and an ink mark, the gap, the *% even* tag; the × | *51% even* drawn amber (note 1: red below 55%) |
| 10.2 | A Same level card, 4 sports | *4 sports ›*, a green ✓ | The four shared sports (note 1) |
| 10.3 | A Same level card, badminton | Another sport on a card; the per-band tints of the unfilled track; the volt envelope | Bartek at 79% (note 1: a questionnaire-only level reads at most about 73%) |
| 11 | The comparison sheet, a stranger | *+ Add friend* as a black pill, two sport blocks | *81% even* in grey and *54% even* in amber (note 1: green, and red) |
| 12 | Same level, See all | ‹, the two-line title, the pill *● All ‹* with a two-tone dot, one full-width card per row, the lit Home tab | The data |
| 13–16 | See all cards | The full-width card; red at 54% (15), amber at 59% (16) | The data |
| 17, 17.2 | The New in Rakieta row | Tall portrait tiles, the volt *NEW*, the round button top-right, the dark fade, the sport lines one per line with dots | *Joined on Monday* (note 6); names |
| 18, 18.2, 18.3 | New tiles | The volt envelope, the white **+**, the green ✓ | Nothing |
| 19, 19.2 | New in Rakieta, See all | The two-column grid, two sports to a line where they fit, the pill and how it slides open over the title, *All* last with *›* | *Joined on Monday* |
| 20, 20.1 | The Same vibe row | The pale tile tinted in the face's colour, the % in a white circle, the face, name, *N things in common*, the green chips, the dashed *+N more*, the round button bottom-right | Where *+2 more* breaks (note 8); Karol, a friend, first (note 7) |
| 21 | The Hottest groups row | The row: no *See all*, the second card cut | Nothing (the file is named *club row*; it draws Hottest groups) |
| 22–22.3 | Vibe tiles | The tile, each in its tint; the envelope; the green ✓ | *77%* for 2 tags (note 1: 75%); the black **+** (note 9) |
| 23 | The vibe sheet | *You and …* with *✓ Friends*, the identity row, the photo carousel from the left padding, the intro in italic with curly quotes, every tag with *· you too* in green and the unshared in grey; the × | *· Kazimierz* (note 5); photos drawn as court pictures (note 1) |
| 24 | Same vibe, See all | The grid of tiles, the pill | *77%* (note 1); Karol's five lines of chips (note 8); the black **+** (note 9) |
| 25–25.3 | The Top 10 row | The huge numeral in a night-to-teal gradient with a paper outline, tucked behind the card; the portrait with its fade; the nickname, level and chip (a triangle and a bold italic digit, coral down, volt up, no background); *10* in two digits; the row ending at 10 | *▼1* on place 1 and chips that can't all be true (note 1); a chip on every card (note 10) |
| 26, 26.1 | A Top 10 card, yours | The volt numeral, the volt ring and *You* (26.1) | *▼1* on place 1 (26) |
| 27 | Top 10's pill, open | The white pill sliding over the heading, the four sports, the chosen one last in ink with *›* | Nothing |

**No mock draws:** Home's header, today's rows and the groupless *Your games* line; the withdraw sheet;
a group card without growth or with fewer than four faces; a row with no HOTTEST; the group sheet's
*Join*, *Ask to join* and *Open group*, an *Open group* identity, a Player group's *run by*, *1 of your
friends plays here* and *11 players*; a Same level card with one shared sport, *Same level* as the
gap, the comparison sheet's *Request sent* and *Accept*; See all with a sport picked; an unrated New
tile, *Joined today*, *Joined yesterday*, *Joined 3/4 weeks ago* and *Nobody new plays squash yet*; vibe
tiles for 1, 4 or 5 tags, a correct 75%, the vibe sheet's other three buttons and a distance; a Top 10
card with no chip, another sport, one or two ranked players and *Nobody ranked in squash yet*; the
round button's **…** (brown); the cancel-request and remove-friend sheets; the request-card lines; the
You switch; the Rankings page without its switch; a record with all photos; and *This record isn't
available*. Each is designed in [the-screens.md](the-screens.md) from the mocks' own parts and the
design system, and named there as designed, not drawn.

## Overrides

Each is a ruling of the Home rows grilling, a call in PRD #789, or a rule from an earlier record. The
mock is correct everywhere else.

| Note | Mock | What it draws | What is built |
| --- | --- | --- | --- |
| 1 | every mock | Sample names, levels, %, counts, tags and chips, some that can't happen: *▼1* on place 1 (2, 25, 26), chips that contradict each other (25.1–25.3), *77%* for 2 tags (22.2, 24), *51%* and *54% even* in amber and *81% even* in grey (9, 11), a questionnaire-only newcomer at 79% (10.3), a bar longer than its heat share (4) | **The mock data is sample only.** The backend sends every figure, and the rules are [the mechanics](the-mechanics.md)': the vibe % is 50/75/88/94/97/98 (§8.2), the colours green ≥ 70, amber 55–69, red < 55 (§6.2), the bar the heat over the HOTTEST card's (§5.5), and a chip is the rankings mechanics' |
| 2 | every person | *Zofia*, *Bartek L.*, *Kuba W.*, *You vs Zofia B.*, *You and Karol* | **Nicknames**, never with an @ (ADR-0199, Q4): *zofia.b*, *You vs zofia.b*, *You and karol.t*. The reader is *You* |
| 3 | every face | Two white initials over a court picture | **Today's faces** (Q4): the photo, or the generated court poster, **with no letters**. A group's badge keeps its monogram letters (ADR-0183 §5) |
| 4 | 1, 2, 9, 17, 17.2, 19, 19.2 | *NEW IN RAKIETA*, *New in Rakieta* | **As drawn.** Not an override since [ADR-0211](../../adr/0211-the-brand-is-rakieta-everywhere.md): the mocks spell the brand as it is built. The row keeps its number |
| 5 | 23 | *6 things in common · Kazimierz* | **A distance, never a district** (Q28): *6 things in common · In your area · 0,6 km*, or the kilometres alone, or nothing, as the record writes it |
| 6 | 1, 2, 17, 19 | *Joined on Monday* | **The ladder, with no weekday** (a call made while writing PRD #789): *Joined today* … *Joined 6 days ago*, *Joined last week*, *Joined 2 weeks ago* … *Joined 4 weeks ago* ([the mechanics §7.3](the-mechanics.md#73-joined-)) |
| 7 | 1, 2, 7, 20 | A friend first on a row (Zofia on Same level, Karol on Same vibe) | **Fresh good matches first, gaps at the right** (Q33): a friend is a gap, after every fresh match ([the mechanics §9](the-mechanics.md#9-keeping-the-rows-alive)). See all lists friends where they fall, as mock 12 does |
| 8 | 20, 22.3, 24 | *+2 more* alone on a third line with room for both chips; five lines of chips in See all | **As many whole chips as fit in three lines**, the last place taken by a dashed *+N more* when more remain (PRD #789) |
| 9 | 22.2, 24 | The **+** drawn as an ink circle on the pale tiles | **The + button is the white one everywhere** (Q29): white with an ink plus, as on the dark cards and the photo tiles |
| 10 | 25–25.3 | A chip on every card | **No chip for no change, nor for *New*** (PRD #789): only ▲ or ▼ |
| 11 | the brief | *A green color with small envelope icon* for someone who asked | **The envelope is volt** (Q29), as every mock draws it |
| 12 | the brief | Top 10's pill: *only those with a ranked field of at least three players* | **All four sports**, with *Nobody ranked in squash yet* in the row (Q35, Q37). The number 3 plays no part |
| 13 | the brief | Top 10 *opens on your main sport* | **The trophy's sport**: the latest result, else the deck's last sport, else padel, falling through to the next sport with anybody ranked (Q16) |
| 14 | the brief | *It has to be determined if more than one hottest group can be displayed* | **Exactly one HOTTEST**, and only with a game this week (Q10) |
| 15 | the brief | GROWING: *gained four or more players this month* | **+4 and at least a quarter of today's players** (Q25) |

## Index

| # | File | Original name |
| --- | --- | --- |
| 1 | [`01_home_rows_1.png`](mocks/01_home_rows_1.png) | `1_home_rows_general_1.png` |
| 2 | [`02_home_rows_2.png`](mocks/02_home_rows_2.png) | `2_homre_rows_general_2.png` |
| 3 | [`03_hottest_group_card_1.png`](mocks/03_hottest_group_card_1.png) | `3_hottest_groups_tile_1.png` |
| 3.2 | [`03.2_hottest_group_card_2.png`](mocks/03.2_hottest_group_card_2.png) | `3.2_hottest_groups_tile_1.png` |
| 4 | [`04_hottest_group_card_3.png`](mocks/04_hottest_group_card_3.png) | `4_hottest_groups_tile2.png` |
| 5 | [`05_hottest_group_card_4.png`](mocks/05_hottest_group_card_4.png) | `5_hottest_groups_tile3.png` |
| 6 | [`06_group_sheet.png`](mocks/06_group_sheet.png) | `6_hottest_groups_bottom_sheet.png` |
| 7 | [`07_same_level_row.png`](mocks/07_same_level_row.png) | `7_same_comptetitve_level_players_row.png` |
| 8 | [`08_same_level_card_1.png`](mocks/08_same_level_card_1.png) | `8_competiive_players_card1.png` (the brief says `…_card.png`) |
| 9 | [`09_comparison_sheet_1.png`](mocks/09_comparison_sheet_1.png) | `9_competiive_players_bottom_sheet2.png` |
| 10 | [`10_same_level_card_2.png`](mocks/10_same_level_card_2.png) | `10_competitive_players_card2.png` |
| 10.2 | [`10.2_same_level_card_3.png`](mocks/10.2_same_level_card_3.png) | `10.2_competitive_row_card.png` |
| 10.3 | [`10.3_same_level_card_4.png`](mocks/10.3_same_level_card_4.png) | `10.3_competitve_card_3.png` |
| 11 | [`11_comparison_sheet_2.png`](mocks/11_comparison_sheet_2.png) | `11_competitive_players_bottom_sheet2.png` |
| 12 | [`12_same_level_see_all.png`](mocks/12_same_level_see_all.png) | `12_se_all_competitve_screen.png` |
| 13 | [`13_same_level_see_all_card_1.png`](mocks/13_same_level_see_all_card_1.png) | `13_se_all_competitive_card.png` |
| 14 | [`14_same_level_see_all_card_2.png`](mocks/14_same_level_see_all_card_2.png) | `14_se_all_competitive_card2.png` |
| 15 | [`15_same_level_see_all_card_3.png`](mocks/15_same_level_see_all_card_3.png) | `15_se_all_competitive_card3.png` |
| 16 | [`16_same_level_see_all_card_4.png`](mocks/16_same_level_see_all_card_4.png) | `16_se_all_competitive_card4.png` |
| 17 | [`17_new_row_1.png`](mocks/17_new_row_1.png) | `17_row_new_in_rakieta.png` |
| 17.2 | [`17.2_new_row_2.png`](mocks/17.2_new_row_2.png) | `17_row_new_in_rakieta2.png` |
| 18 | [`18_new_tile_1.png`](mocks/18_new_tile_1.png) | `18_new_players_card1.png` |
| 18.2 | [`18.2_new_tile_2.png`](mocks/18.2_new_tile_2.png) | `18.2_new_players_card2.png` |
| 18.3 | [`18.3_new_tile_3.png`](mocks/18.3_new_tile_3.png) | `18.3_new_players_card3.png` |
| 19 | [`19_new_see_all_1.png`](mocks/19_new_see_all_1.png) | `19_new_in_rakieta_screen_list.png` |
| 19.2 | [`19.2_new_see_all_2.png`](mocks/19.2_new_see_all_2.png) | `19.2_new_in_rakieta_screen_list2.png` |
| 20 | [`20_same_vibe_row_1.png`](mocks/20_same_vibe_row_1.png) | `20_same_vibe_row.png` |
| 20.1 | [`20.1_same_vibe_row_2.png`](mocks/20.1_same_vibe_row_2.png) | `20.1_same_vibe_row2.png` |
| 21 | [`21_hottest_groups_row.png`](mocks/21_hottest_groups_row.png) | `21-club_row.png` |
| 22 | [`22_same_vibe_tile_1.png`](mocks/22_same_vibe_tile_1.png) | `22_same_vibe_card.png` |
| 22.1 | [`22.1_same_vibe_tile_2.png`](mocks/22.1_same_vibe_tile_2.png) | `22.1_same_vibe_card1.png` |
| 22.2 | [`22.2_same_vibe_tile_3.png`](mocks/22.2_same_vibe_tile_3.png) | `22.2_same_vibe_card2.png` |
| 22.3 | [`22.3_same_vibe_tile_4.png`](mocks/22.3_same_vibe_tile_4.png) | `22.3_same_vibe_card3.png` |
| 23 | [`23_vibe_sheet.png`](mocks/23_vibe_sheet.png) | `23.same_vibe_bottom_sheet.png` |
| 24 | [`24_same_vibe_see_all.png`](mocks/24_same_vibe_see_all.png) | `24.same_vibe_screen_list.png` |
| 25 | [`25_top_10_row_1.png`](mocks/25_top_10_row_1.png) | `25_row_top_players.png` |
| 25.1 | [`25.1_top_10_row_2.png`](mocks/25.1_top_10_row_2.png) | `25.1_row_top_players1.png` |
| 25.2 | [`25.2_top_10_row_3.png`](mocks/25.2_top_10_row_3.png) | `25.2_row_top_players2.png` |
| 25.3 | [`25.3_top_10_row_4.png`](mocks/25.3_top_10_row_4.png) | `25.3_row_top_players3.png` |
| 26 | [`26_top_10_card_1.png`](mocks/26_top_10_card_1.png) | `26_row_top_card.png` |
| 26.1 | [`26.1_top_10_card_2.png`](mocks/26.1_top_10_card_2.png) | `26.1_row_top_card1.png` |
| 27 | [`27_top_10_sport_pill.png`](mocks/27_top_10_sport_pill.png) | `27_top_players_sport_seletor.png` |
