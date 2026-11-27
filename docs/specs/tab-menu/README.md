# The tab menu: the record, its brief and its mocks

**What PRD [#859](https://github.com/Raketa02/Raketa/issues/859) is drawn from.** Inside a group, the
*Competitive / For fun* row under the tabs goes. The choice moves into a small menu inside the
**Games** or **Friends** tab you are on. A chevron at the tab's right edge marks it, and a second tap
on that tab opens it. On Games, picking the other kind swaps the deck in place, and the deck card
takes the freed height with player tiles of a fixed shape. On Friends, it sets the kind of the game
being built. The PRD comes from the product owner's brief, its four mocks, and the grilling held on
them on 2026-11-24 (Q1–Q19, with Q19a and Q19b). They are copied here from the product owner's own
folder, `5.club_tab`, so every session can read them. Landed by
[#860](https://github.com/Raketa02/Raketa/issues/860) on 2026-11-24.

| File | What it holds |
| --- | --- |
| [Tabs_refactor.md](Tabs_refactor.md) | The product owner's brief, verbatim. Its mock paths point at their own desktop: read each by the [index](#index)'s original name. The folder's `Tabs refactor.pdf` holds the same text and isn't copied |
| [decisions.md](decisions.md) | The grilling's decision log, verbatim: every ruling with its reason, the facts it rests on (§2, with `file:line` positions as of 2026-11-24, and the A32 measurements), the docs and tests it reaches, and the question index Q1–Q19b. Its status line and its delivery section (§11) predate PRD #859. Its §10 lists five calls made while writing, all taken up by the PRD; the spec folder it suggests is this one |
| [`mocks/`](mocks/) | The 4 mocks, renamed by what they show and numbered 1 to 4 (the [index](#index) gives each original name) |

**There is no new ADR** (the log's Q17): this changes how a screen is laid out, not a decision about
the system. Two records get dated notes instead:
[ADR-0201](../../adr/0201-the-other-kind-is-a-door-and-a-changed-intent-leaves-the-cards-you-havent-answered.md)
§2 (the door is now a line in the Games tab's menu) and
[the fill-in split's override 2](../fill-in-split/README.md#overrides) (the chevron is the selected
tab's only mark). ADR-0202's *the Friends tab's switch sets one game's kind* still holds: read
*switch* as the Friends tab's menu. Where the log and PRD #859 disagree, PRD #859 wins.

**This folder holds the record, not the spec.** The layout is specified where the group page already
lives, amended by #860: [the Games and Fill in screens](../games-and-fill-in/the-screens.md) (A1,
A2.1, and the tiles' shape in A2.3) and [mechanics](../games-and-fill-in/the-mechanics.md) (§3,
§4.1), and [the Friends screens](../friends/the-screens.md) (§7) and
[mechanics](../friends/the-mechanics.md) (§7.1). The tiles' numbers and their evidence stay in the
log (§2, §6). [The words](../matchmaking/the-words.md) §28 and §29.6 carry dated notes: the
labels are unchanged, and the menu's spoken names are worded in copy modules by the tickets that
build it. The player app's feature docs, its design system and the code comments that describe
the row are amended by the tickets that build each part:
[#861](https://github.com/Raketa02/Raketa/issues/861) (the menu, on Friends first),
[#862](https://github.com/Raketa02/Raketa/issues/862) (the menu on Games, its counts and its door),
[#863](https://github.com/Raketa02/Raketa/issues/863) (the swap),
[#864](https://github.com/Raketa02/Raketa/issues/864) (the tiles' shape) and
[#865](https://github.com/Raketa02/Raketa/issues/865) (the cap, the floor, the shrinking and the
scroll). [#866](https://github.com/Raketa02/Raketa/issues/866) is the phone walk. Until a ticket
amends them, those docs describe the row.

The door's two sentences in the root [`CONTEXT.md`](../../../CONTEXT.md) are under **Player
profile** (*Play intent*) and **Proposals** (*Group deck*). *The tab's menu* is UI vocabulary, not
a domain term.

## The ground rule: the mocks are illustrations

**No decision rests on a mock.** In the product owner's words (the log's Q15):

> *"do not take decisions based on the mock because it is just a mock. Any decision that you make
> should be based on real evidences."*

1. **Wherever a mock and the log differ, the log wins** (its ground rules and §8). The mocks show
   intent: the chevron, the menu's place and its two lines. Every size, shape and number in the
   built page comes from the evidence the log records: a device measurement, the photo pipeline,
   the design system and today's code.
2. **Their data is only data.** No rule is read off a mock's names, clubs, prices, times, counts or
   the *69%* bar.
3. **Three things the mocks draw are not built:**
   - **the counts drawn beside a tab's label**, as a pale pill or a red number. Today's coral corner
     badge stays, and still counts what the player hasn't seen (the log's Q4);
   - **the count on the selected tab**, *Games 3* on mocks 1 and 3. The tab on screen draws no badge
     ([the fill-in split's override 2](../fill-in-split/README.md#overrides)), and the chevron is its
     only mark;
   - **mock 3's tile shape**, about 1.6 : 1. Doubles tiles are **1.75 : 1** and singles tiles
     **3:4**, from the user's phone measured over adb and the photo's own crop (the log's §6.2,
     Q15, Q18).
4. **Cite a mock by this folder's number**: *tab menu mock 3*. The log's own *Mock index* numbers
   them the same way, 1 to 4.

## Which mock shows what

| # | Mock | What it illustrates | What is not built |
| --- | --- | --- | --- |
| 1 | The Games tab with its chevron | A down-pointing chevron at the right edge of the selected **Games** tab, and the selected tab wider than the rest (Q5) | The pale *3* beside *Games* on the selected tab, and the red counts beside the other labels |
| 2 | The Friends tab with its chevron | The same chevron on the selected **Friends** tab | The red counts beside *Games*, *Fill in* and *You’re in* |
| 3 | The Games menu open | The menu hanging from the Games tab's bottom edge, **aligned to its left edge**, with no arrow: **Competitive** then **For fun**, the coral tick on the current kind, each line's count in a muted face, and the chevron turned up | *Games 3* on the selected tab, the counts beside the other labels, and the tiles' shape. Its *5* and *1* are data |
| 4 | The Friends menu open | The menu hanging from the Friends tab, **aligned to its right edge**, with the tick and **no counts** | The counts beside the other labels |

**No mock draws:** the door line (the kind the intent doesn't want, dimmed, with no number); the
tab while answers or finding are in flight; the states with no chevron; the swap's motion; today's
spinner while the other kind loads; the tiles at 1.75 and 3:4; a small phone, a large text size or
reduced motion. Each is decided in the log and PRD #859, and designed by the ticket that builds it.

## Index

| # | File | Original name |
| --- | --- | --- |
| 1 | [`01_games_tab_with_chevron.png`](mocks/01_games_tab_with_chevron.png) | `1.games_tab_with_chevron.png` |
| 2 | [`02_friends_tab_with_chevron.png`](mocks/02_friends_tab_with_chevron.png) | `2.friends_tab_with_chevron.png` |
| 3 | [`03_games_menu_open.png`](mocks/03_games_menu_open.png) | `3_games_tap_menu_open.png` |
| 4 | [`04_friends_menu_open.png`](mocks/04_friends_menu_open.png) | `4_friends_tap_menu_open.png` |
