# The Fill in / You’re in split: the record and its mocks

**What PRD [#844](https://github.com/Rakieta02/Rakieta/issues/844) is drawn from.** A group's page
gets four tabs, **Games · Fill in · You’re in · Friends**: Fill in keeps only the rescues, the
player's own live yeses move to You’re in, **+ Post a game** floats there, and the badges count what
the player hasn't seen. It was decided in the Fill in refactor grilling on 2026-11-23 (Q1–Q12, with
Q2b and Q3b), from the product owner's brief and 3 mocks. The log and the mocks are copied here from
the product owner's own folder, `3.fill_in_refactor`, so every session can read them. Landed by
[#845](https://github.com/Rakieta02/Rakieta/issues/845) on 2026-11-23.

| File | What it holds |
| --- | --- |
| [decisions.md](decisions.md) | The grilling's decision log, verbatim: every ruling with its reason, the facts it rests on, the docs and tests it reaches, and the question index Q1–Q12. There was no written brief: the brief was given in the session. Its status line and its delivery section (§13) predate PRD #844, and its `file:line` positions are as of 2026-11-23 |
| [`mocks/`](mocks/) | The 3 mocks, renamed by what they show and numbered 1 to 3 (the [index](#index) gives each original name) |

**The one decision about the system is
[ADR-0208](../../adr/0208-the-phone-remembers-which-rows-of-a-group-pages-tabs-a-player-has-seen.md)**:
the phone remembers which rows of a group page's tabs a player has seen, per account, forgotten at
sign-out. The split itself is a change of layout and has no record of its own (Q8). Where the log
and ADR-0208 or PRD #844 disagree, ADR-0208 and PRD #844 win.

**This folder holds the record, not the spec.** The split is specified where the group page already
lives: [the Games and Fill in screens](../games-and-fill-in/the-screens.md) (A1, A3, A5) and
[mechanics](../games-and-fill-in/the-mechanics.md) (§3, §10), amended by #845. The player app's
feature docs and design system are amended by the tickets that build each part,
[#847](https://github.com/Rakieta02/Rakieta/issues/847)–[#850](https://github.com/Rakieta02/Rakieta/issues/850).
Until a ticket amends them, they describe the page as it is today.

The terms are in the root [`CONTEXT.md`](../../../CONTEXT.md), under **Bookings**: **Fill in**
(the rescue board) and **You’re in** (your own live yeses in a group and sport, decided and not yet
built), which **Live yes**, under **Proposals**, points to.

## How to read the mocks

1. **The mocks lead on design**, except where the grilling overrode them. Each override is listed
   under [*Overrides*](#overrides).
2. **Their data is only data.** No rule is read off a mock's names, times, clubs, prices, counts or
   button text. That covers mock 1's ***I’m in · 27 zł***: **the rescue row keeps *Pay {share}***,
   because the cards don't change (Q9).
3. **The cards are today's cards.** Mock 1 draws today's rescue row and mock 2 today's yes row
   ([the screens A3.1 and A3.2](../games-and-fill-in/the-screens.md#a3-fill-in-and-youre-in)). What
   the mocks change is the page around them: four tabs, no section headings, the badges.
4. **The badge's mark is today's.** The mocks draw a count as a pale pill beside the tab's name, as
   the group page's first mocks did (the Games and Fill in mocks 1 and 11). The app draws that as
   the coral corner badge, and the corner badge is unchanged (PRD #844). What changes is what it
   counts.
5. **Cite a mock by this folder's number**: *split mock 2*. The log's own *Mock index* numbers them
   the same way, 1 to 3, though two of the original files begin with *2*.

## Which mock shows what

| # | Mock | What leads | What doesn't |
| --- | --- | --- | --- |
| 1 | The Fill in tab | **Fill in holds only the rescue rows**, today's coral rows, **with no section heading**. The four tabs, Fill in selected | ***+ Post a game***, drawn floating here (override 1). The badge on the selected tab (override 2). *I’m in · 27 zł* (note 2 above) |
| 2 | The You’re in tab | **You’re in holds only the yes rows**, today's mint rows with **Withdraw**, **with no section heading**. The four tabs, You’re in selected | The badge on the selected tab (override 2). It doesn't draw + Post a game, which floats here (override 1) |
| 3 | The tab bar | **Games · Fill in · You’re in · Friends**, in that order, with the label ***You’re in***: lower-case *i* and a curly apostrophe. Friends has no badge | The counts, which are illustration. The badge drawn on the selected tab (override 2) |

**No mock draws:** either tab empty (*No seats to fill right now*; the group's starting card when
both are empty; *You haven’t said yes to a game here yet* when only You’re in is); the level door or
the *add a sport* card on You’re in; a read failing or held offline; Post a game's back control
(*Back to You’re in* / *Back to Games*); a badge clearing; and the bar at a narrow width or a large
text size. Each is specified in the screens spec or designed by the ticket that ships it.

## Overrides

Each is a ruling of the grilling (its Q in [decisions.md](decisions.md#question-index)). The mocks
are right everywhere else.

| Note | Where | What it draws | What is built |
| --- | --- | --- | --- |
| 1 | 1, 2 | **+ Post a game** floating over Fill in, and nothing floating over You’re in | **+ Post a game floats on You’re in, and only there** (Q4): the button that makes a game sits on the tab where that game appears. Fill in has no button |
| 2 | 1, 2, 3 | A badge on the selected tab: *Fill in 2* on mocks 1 and 3, *You’re in 3* on mock 2. The group page's first mocks do the same (*Games 4* on the Games and Fill in mock 1, *Fill in 1* on mock 11) | **The tab on screen draws no badge**, whatever it counts (Q2b, Q10). What it shows is seen while it is on screen; on Games, the other kind's unseen cards show in the Games badge only once you leave the tab. *Noted 2026-11-24 ([#859](https://github.com/Rakieta02/Rakieta/issues/859), decided and not yet built): when the Competitive / For fun choice moves into the Games and Friends tabs' menu, the tab on screen still draws no badge, and on Games and Friends **the chevron is the selected tab's only mark**; Fill in and You’re in draw none. The tab menu's mocks draw a count on the selected tab too (*Games 3*), and it is not built either ([the tab menu's README](../tab-menu/README.md#the-ground-rule-the-mocks-are-illustrations)).* |

## Index

The original files carry two *2*s: `2_youre_in_tap.png` and `2_tap_bar.png`. The log's mock index
puts the tab bar third, and so does this folder.

| # | File | Original name |
| --- | --- | --- |
| 1 | [`01_fill_in_tab.png`](mocks/01_fill_in_tab.png) | `1_fill_in_tap.png` |
| 2 | [`02_youre_in_tab.png`](mocks/02_youre_in_tab.png) | `2_youre_in_tap.png` |
| 3 | [`03_tab_bar.png`](mocks/03_tab_bar.png) | `2_tap_bar.png` |
