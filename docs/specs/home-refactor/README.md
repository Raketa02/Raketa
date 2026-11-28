# The Home refactor: the record and its mocks

**What PRD [#810](https://github.com/Rakieta02/Rakieta/issues/810) is drawn from.** The product owner's
brief *Home Screen Refactor*, its mocks, and the decision log of the grilling held on it on 2026-11-16
(Q1–Q46). They are copied here from the product owner's own folder, `homeRefactor`, so that every
session can read them. Landed by [#811](https://github.com/Rakieta02/Rakieta/issues/811) on 2026-11-16.

| File | What it holds |
| --- | --- |
| [home_screen_refactor.md](home_screen_refactor.md) | The product owner's brief, verbatim but for the brand's spelling ([ADR-0211](../../adr/0211-the-brand-is-rakieta-everywhere.md) §6). Its paths point at their own folder: read `…\homeRefactor\5_groupos_heating_up_open.png` as the [index](#index)'s file for that number |
| [decisions.md](decisions.md) | The grilling's decision log, verbatim but for the brand's spelling ([ADR-0211](../../adr/0211-the-brand-is-rakieta-everywhere.md) §6): every ruling with its reason, the facts it rests on (as found on `main` at `bc6ca793`), and the question index Q1–Q46. Its status line and its branch name predate PRD #810 |
| [`mocks/`](mocks/) | The 14 mocks, renamed (the [index](#index) gives each original name). PRD #810 and #811 say 15; the product owner's folder holds 14, numbered 1 to 13 with a 5.1 |

**The decision** is [ADR-0205](../../adr/0205-what-waits-for-your-answer-goes-behind-an-envelope-and-homes-rows-fold-into-for-you.md).
**PRD #810** settled what the decision log left open, such as which context owns the envelope's visit
(Proposals). Where the log and ADR-0205 or PRD #810 disagree, ADR-0205 and PRD #810 win.

**This folder holds the record, not the spec.** Each part is specified where it already lives, amended
in place by the ticket that ships it. PRD #810 names the first of these; the rest are the sections
ADR-0205 also changes:

- the Home rows set ([`home-rows/`](../home-rows/README.md)):
  - the screens §1 and §2 (Home and the row frame), §3.2 (the group card's heat bar and *+N this
    month*), §4.2 (the gap in words, *0,02 below you*), §7.1 (Top 10's heading and *Rankings ›*),
    §9.4 (the request card's line) and §11 (the design-system work);
  - the mechanics §3 (Home, top to bottom), §5.5 (the heat bar, drawn nowhere now), §6.4 (the
    gap in words), §9.2 (on screen, now only while a line is open) and §12 (where a request was
    found, still recorded and no longer drawn);
- the friends set ([`friends/`](../friends/README.md): the screens §6, the mechanics' lines about Home
  and the link, and its README);
- Games and Fill in A8 and the rankings set, for the trophy and the bell;
- the words ([`the-words.md`](../matchmaking/the-words.md)).

Until a ticket amends them, those documents still describe the old Home.

The terms are in the root [`CONTEXT.md`](../../../CONTEXT.md): **Needs your answer** and **Home**
(Proposals), **Ask for a level** (Friends), and the rows' own terms under **Groups**, **Discovery**
and **Rankings**, which keep their names.

## How to read the mocks

1. **The mocks lead on design.** The brief says *"The design presented from those mocks is the priority
   and is how the UI should look like in terms of design and theming."* Where an ADR, a spec or the
   locked design system disagrees with a mock on a look, the document changes, by name: ADR-0205 §9
   names the design system's five exceptions. **On a rule, the decisions win.** Every place a mock is
   overridden is listed under [*Overrides*](#overrides), and nothing here overrides silently.
2. **Their numbers, names and counts are only data.** The brief says *"The data that you see all over
   the mock references is just data so do not hardcode or make decisions based on mocked data."* No
   rule is read off a mock: not *6* or *14* in a pill, *See all 14*, *91%*, *▼1*, *1 h 35*, *25 zł*,
   *Joined 2 days ago*, nor which line is drawn open.
3. **A mock's *Rakieta* is the brand as written**
   ([ADR-0211](../../adr/0211-the-brand-is-rakieta-everywhere.md)). *New in Rakieta*, in mocks 3, 4, 6, 8, 9, 10 and 12, is the line's
   title as built.
4. **The mocks predate rulings that hold everywhere**:
   - a player is named by their **nickname**, never with an @
     ([ADR-0199](../../adr/0199-a-player-is-known-by-their-nickname.md)), so *Inés D.* reads as a
     nickname such as *ines.d*;
   - a face is **today's face**, the photo or the generated court poster, **with no letters**. A
     group's badge keeps its monogram letters (the home rows' note 3).
5. ***Your games* is out of scope** (the brief). Mock 3 draws a *Your games* card, and nothing in it is
   this work's.
6. **Cite a mock by its number**: *home refactor 5.1*. The numbers are the product owner's, the
   decimal included. The file names were cleaned of typos (`groupos`, `player_at_your_level`,
   `players_at_your_vibe`) and zero-padded so they sort.

## Which mock shows what

| # | Mock | What leads | What doesn't |
| --- | --- | --- | --- |
| 1 | The header's buttons | *Home* on the left; on the right, the **envelope** (an ink outline), the **bell**, and the dark trophy pill in the far-right corner, in that order; their spacing | *#7* (note 1). The envelope's badge isn't drawn: it is the bell's ([ADR-0205](../../adr/0205-what-waits-for-your-answer-goes-behind-an-envelope-and-homes-rows-fold-into-for-you.md) §2) |
| 2 | *Needs your answer* | The sheet over Home: the grab handle, the bold title, the × in its beige circle; section labels in grey caps with *· n*; **FRIENDS GAME**'s one big tile at full width, as drawn (the title and clock, the faces with ✓ on who's in and a faded face for who's invited, the when/where/sport line, *Not this time* outlined and *Accept and pay 25 zł* in coral); **FRIEND REQUESTS**' wider tile, the next one peeking, the face, the title, the reliability chip, and *Not now* and *Accept* at the bottom | The request's subtitle (note 5); FRIENDS GAME drawn first (note 6); the names, counts, price and clock (notes 1–2) |
| 3 | Home, FOR YOU closed | The header (1); the **FOR YOU** eyebrow; five white line cards, each a title on the left and a grey count pill and › on the right; *Top 10* with no pill; the lines' spacing and order | *Your games* (note 5 of *How to read*); the counts (note 1); Home's badge *4* (note 1) |
| 4 | FOR YOU closed, close up | The line card's radius, padding and type, the pill's size and grey, the chevron | The counts |
| 5 | Groups heating up, open | The open line: the **ink border** and soft shadow, the chevron turned down (⌄), the pill kept; the next tile peeking; **All groups ›** at the bottom right | The data; the faces' letters (note 3) |
| 5.1 | Groups heating up's tile | **The simplified tile**: the striped band in the group's colour, *▲ HOTTEST*, the shield monogram, the name, *14 games this week* on the left and *11 players* on the right, the faces bottom-left, the chip bottom-right (*Ask to join*). **No heat bar, no *+N this month*, no sport line** | The figures and the tag's holder (note 1) |
| 6 | Players at your level, open | The open line under a closed one; today's dark card; **See all 14 ›** at the bottom right, carrying the line's count | Zofia, a friend, first (note 7); *91%* (note 1) |
| 7 | Players at your level's tile | The card's footer with *2 sports ›* and the round button, and **no *0,02 below you*** | The data |
| 8 | New in Rakieta, open | The open line under two closed ones; today's tiles, unchanged; **See all 6 ›** | *Bartek L.*, *Michał R.* (note 2) |
| 9 | New in Rakieta, close up | Today's tiles inside the open line | As 8 |
| 10 | Players with your vibe, open | The open line under three closed ones; today's tiles, unchanged; **See all 14 ›** | Karol, a friend, first (note 7) |
| 11 | Players with your vibe, close up | Today's tiles inside the open line | As 10 |
| 12 | Top 10, open | The open line last, with **no count**; today's numerals and portrait cards; **the footer**: the sport switcher on the left, **Open the rankings ›** on the right; the bottom bar | The switcher's chevron (note 4); *▼1* on place 1 (note 1); the names |
| 13 | Top 10, close up | The footer: the switcher's white pill with its sport dot, and *Open the rankings ›* | As 12 |

**No mock draws:** the envelope's badge, and the header with the envelope's slot collapsed; the **TO
CONFIRM** and **ASKED FOR A LEVEL** sections; a second friends game and its page dots; a friend
request's sport-levels line, and one with no levels; the sheet at its cap, scrolling; Home's *Get your
level* card; the groupless *Your games* line and *Groups heating up* opened by default; a *99+* pill;
a line hidden while loading, empty or failed, and FOR YOU hidden; the switcher open, sliding to the
right; *Nobody ranked in squash yet* in an open Top 10; the simplified tile's *Join*, *Asked* and
*You're in*; any motion; and the **Groups heating up page**. Each is designed by the ticket that
ships it, from the mocks' own parts, the brief's words and the design system, and named there as
designed, not drawn.

## Overrides

Each is a ruling of the grilling (its Q in [decisions.md](decisions.md#appendix-b--question-index)) or
a rule from an earlier record. The mock is correct everywhere else.

| Note | Mock | What it draws | What is built |
| --- | --- | --- | --- |
| 1 | every mock | Sample counts, figures, prices, times, levels and chips: *6* and *14* in the pills and the footers, *#7*, *91%*, *14 games this week*, *25 zł*, *1 h 35*, *▼1* on place 1, Home's badge *4* | **Sample only.** The backend sends every figure. A count is a pool capped at 100 and drawn *99+* past 99 (ADR-0205 §6, Q17, Q33, Q45), and Home's badge counts what it counts today |
| 2 | every person | *Inés D.*, *Karol*, *Zofia*, *Bartek L.*, *Michał R.*, *Staś W.* | **Nicknames**, never with an @ (ADR-0199) |
| 3 | every face | Two white initials over a court picture | **Today's faces, with no letters.** A group's badge keeps its monogram |
| 4 | 12, 13 | The switcher as *● Padel ‹*, its chevron pointing left | ***Padel ›***: the chevron points the way it opens, to the right (Q19, Q37) |
| 5 | 2 | The friend request's subtitle, *With you in Kazimierz crew · Padel 3,40 ·* | **The where-line and every found-by line are gone** (Q2). In their place, a line with every sport the sender holds a published level in, *● Padel 3,40 · ● Tennis 2,90*, at most two lines, and none when they hold none (Q28). The decision log: *"The mock still draws the old subtitle; the document's text wins."* |
| 6 | 2 | *FRIENDS GAME* as the sheet's first section | **TO CONFIRM comes first** whenever a payment waits (Q14, Q32). The order is always To confirm, Friends game, Friend requests, Asked for a level, each hidden while empty |
| 7 | 6, 10 | A friend first in an open line (Zofia ✓, Karol ✓) | **Fresh good matches first, gaps at the right**, unchanged from the home rows' note 7 |
| 8 | the brief | *Isolate the rows "Friends game", "Friend requests" and "asked for a level"* | **Four sections**: *To confirm* moves into the sheet too, first (Q14, Q32) |
| 9 | the brief | A friend request: *remove the text under the main tile title … but keep the player reliability tag* | Removed, and the reliability chip kept, with **the sport-levels line** of note 5 added (Q28) |
| 10 | the brief | *The bottom sheet height adjusts to the rows* | Only as tall as what it holds, **up to the sheet's usual cap**, and scrolling beyond it (Q8) |

## Index

| # | File | Original name |
| --- | --- | --- |
| 1 | [`01_header_buttons.png`](mocks/01_header_buttons.png) | `1-row_buttons.png` |
| 2 | [`02_needs_your_answer_sheet.png`](mocks/02_needs_your_answer_sheet.png) | `2_bottom_sheet_needs_answer.png` |
| 3 | [`03_for_you_closed.png`](mocks/03_for_you_closed.png) | `3_closed_rows.png` |
| 4 | [`04_for_you_closed_detail.png`](mocks/04_for_you_closed_detail.png) | `4_closed_rows_detailed_view.png` |
| 5 | [`05_groups_heating_up_open.png`](mocks/05_groups_heating_up_open.png) | `5_groupos_heating_up_open.png` |
| 5.1 | [`05.1_groups_heating_up_open_detail.png`](mocks/05.1_groups_heating_up_open_detail.png) | `5.1_groupos_heating_up_tile.png` |
| 6 | [`06_players_at_your_level_open.png`](mocks/06_players_at_your_level_open.png) | `6_players_at_your_level_open.png` |
| 7 | [`07_players_at_your_level_open_detail.png`](mocks/07_players_at_your_level_open_detail.png) | `7_player_at_your_level_detail.png` |
| 8 | [`08_new_in_rakieta_open.png`](mocks/08_new_in_rakieta_open.png) | `8_new_in_rakieta_open.png` |
| 9 | [`09_new_in_rakieta_open_detail.png`](mocks/09_new_in_rakieta_open_detail.png) | `9_new_in_rakieta_open_detail.png` |
| 10 | [`10_players_with_your_vibe_open.png`](mocks/10_players_with_your_vibe_open.png) | `10_players_at_your_vibe_open.png` |
| 11 | [`11_players_with_your_vibe_open_detail.png`](mocks/11_players_with_your_vibe_open_detail.png) | `11_players_at_your_vibe_open_detail.png` |
| 12 | [`12_top_10_open.png`](mocks/12_top_10_open.png) | `12_top_10_open.png` |
| 13 | [`13_top_10_open_detail.png`](mocks/13_top_10_open_detail.png) | `13_top_10_open_detail.png` |
