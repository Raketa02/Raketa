# Rankings: the spec set

**What PRD [#766](https://github.com/Rakieta02/Rakieta/issues/766) is drawn from.** The product owner's
Rankings brief and its eleven mocks, copied here from `rakieta_v2.0/4-features/4-ranking` so that every
session can read them, then grilled on 2026-11-07 (Q1–Q26 there, the
[games and fill-in mechanics' Q130](../games-and-fill-in/the-mechanics.md#appendix-c--decision-log)).
Landed by [#767](https://github.com/Rakieta02/Rakieta/issues/767) on 2026-11-07. **Amended 2026-11-14**
by [ADR-0204](../../adr/0204-home-shows-who-and-what-is-around-you-and-any-player-may-meet-any-other.md)
(Q131, [the Home rows spec set](../home-rows/README.md)): no row is hidden by a switch or a block,
*Show me in General* is replaced by *Show me to new people*, requests have no daily limit, and Home
gains **Top 10**.

| File | What it holds |
| --- | --- |
| [the-mechanics.md](the-mechanics.md) | What happens: what is ranked, who is listed, the order and ties, the chip, the gap line and its win count, Home's trophy, *Show me in General*, blocks, records, requests and their limit, with every number |
| [the-screens.md](the-screens.md) | The trophy, then the page section by section with every state, and which mock draws it |
| [`mocks/`](mocks/) | The eleven mocks, renamed (the [index](#index) gives each original name) |
| [rankings_feature.md](rankings_feature.md) | The product owner's brief, verbatim but for the brand's spelling ([ADR-0211](../../adr/0211-the-brand-is-rakieta-everywhere.md) §6). Its paths point at the product owner's desktop: read `…/4-ranking/N_….png` as `mocks/NN_….png`. Where the brief and these documents disagree, these documents win: they carry the grilling's rulings |

**The decision** is [ADR-0203](../../adr/0203-a-ranking-per-sport-sorted-by-the-level.md). The terms
are in the root [`CONTEXT.md`](../../../CONTEXT.md), under **Rankings**, and under **Player record**
(its new strand), **Blocks** (a block closes the record) and **Friends** (requests from the ranking).
Every sentence a player reads is in [the words §30](../matchmaking/the-words.md#30-rankings). The
market research behind it is [`docs/research/rankings-market.md`](../../research/rankings-market.md).

## How to read the mocks

1. **The mocks lead on design.** The brief says so: *"the design resultant from the mocks is what is
   prioritized"*. Where a mock and a sentence disagree on a look, the mock wins, unless PRD #766,
   ADR-0203 or a ticket overrides it **by name**. Every override known today is under
   [*Overrides*](#overrides), and nothing here overrides silently. On a rule, the mechanics win.
2. **Every name, number, place and chip in a mock is sample data** (Q20). *Inés D.*, *3,40*, *7th of
   13*, *▲ 2* all come from the backend and, for testing, from the seeds.
3. **The mocks predate rulings that hold everywhere**:
   - a player is named by their **nickname**, never with an @
     ([ADR-0199](../../adr/0199-a-player-is-known-by-their-nickname.md)), so *Inés D.* and *Staś* read
     as nicknames;
   - the bottom bar is **Home · ⚡ Play · You** (#576), as mocks 4–5 draw it.
4. **Cite a mock by number**: *rankings 4*. The numbers are the product owner's.

## Which parts of each mock lead

| # | Mock | What leads | What doesn't |
| --- | --- | --- | --- |
| 1 | The trophy on Home | The dark pill, the drawn trophy and *#7*, their size | Where it sits: just left of the bell (note 5) |
| 2 | The header and the switch | ‹, *Rankings*, the sport pill on the right, the General · Friends segmented control | The subtitle it lacks (note 4); the pill's own drawing (note 6) |
| 3 | Your place card | The dark card: *YOUR PLACE*, the volt place, *of 13*, the level, the chip with *up this week*, the fold line and the gap line with its bold numbers | The numbers and names (note 1) |
| 4 | The page, top | The order of the page: header, switch, card, podium, list | The lit You tab (note 3), the subtitle (note 4), the chips and places (note 1) |
| 5 | The page, scrolled | The list on one white card, the tinted *You* row | The whole list of 13 on one screen: General loads in pages (note 7); the lit You tab (note 3) |
| 6 | The podium | The three steps, the volt first, second left, third right and lower, face, nickname and level on each | First names for nicknames (note 2); when it shows (note 8) |
| 7 | The top three rows | Coral places 1–3, the face, the nickname, the five form squares, the chip, the mono level | *▼ 1* on first place (note 1) |
| 8 | A row going up | The mint *▲ 2* chip | Nothing |
| 9 | A row going down | The red *▼ 1* chip | Nothing |
| 10 | A row unchanged | The grey *—* chip | Nothing |
| 11 | Your row | The tint, *You*, the row otherwise as any | Nothing |

**No mock draws:** *Competitive games only*; the trophy without a number; the not-listed cards
(*2 of 5 games*, *Off the list*, *No squash level yet* with **Get your squash level**); the hidden
card; the Friends view's states (*Just you so far*, *None of your friends is ranked in padel yet*,
**Add friends**); *New*; the gap line's other variants; the *You · 212th* button; *Nobody ranked in
badminton yet*; the record's foot from the ranking and the limit sentence; Home's request card
reading *Found you in the padel ranking*; and the You switch. Each is designed in
[the-screens.md](the-screens.md) from the mocks' own parts and the design system, and named there as
designed, not drawn.

## Overrides

Each is a ruling of the rankings grilling, a call in PRD #766, or a rule from an earlier record. The
mock is correct everywhere else.

| Note | Mock | What it draws | What is built |
| --- | --- | --- | --- |
| 1 | rankings 3–11 | Sample places, levels, chips and form: *Inés D.* first with *▼ 1*, *Filip N.* last with *▲ 1*, *Ewa M.* and *Filip N.* both at *2,60* | **The mock data is sample only** (Q20). The backend sends every place, level, chip and form. A first place can never read ▼, nor a last place ▲; two players at one level are ordered by more results, then who reached it first ([the mechanics §5](the-mechanics.md#5-order-and-places)) |
| 2 | rankings 4–7 | Names: *Inés D.*, *Staś W.* in the list, *Inés*, *Staś* on the podium | **Nicknames replace names**, on the podium and in the list alike, never with an @ (ADR-0199, Q11). The reader's own row reads **You** |
| 3 | rankings 4, 5 | The **You** tab lit | **The Home tab stays lit**, because Rankings opens from Home (Q11) |
| 4 | rankings 2, 4 | *Rankings* alone | ***Competitive games only*** is added under the title, small and grey (Q11) |
| 5 | rankings 1 | The pill alone; the brief puts it in *the top-right corner of Home* | **Just left of the bell**, which keeps the corner (Q13) |
| 6 | rankings 2, 4 | A pill, *● Padel ‹* | **The deck's own sport pill**, lifted to shared UI so the deck and Rankings use one control (call 13, [#774](https://github.com/Rakieta02/Rakieta/issues/774)), offering all four sports, rated first (Q22) |
| 7 | rankings 5 | All 13 rows at once | **General loads in pages of 50**, with a floating ***You · 212th*** button whenever the reader's row is off screen (Q16). Friends is shown whole, with the same button |
| 8 | rankings 6; the brief | *It appears only when at least three players are ranked* | **The first three rows the reader sees**, each step labelled with its true place; only when at least three rows are visible to the reader (call 4) |
| 9 | the brief | *Not ranked in squash yet — your first confirmed competitive game puts you on the list* for General; *Just you so far / Nobody rated in squash yet* for Friends *with fewer than two rated friends* | General lists after **5 results** (Q17): *2 of 5 games — 3 more competitive padel games put you on the list*. The brief's line is **Friends'** (a call made while ticketing). Friends' empty line is ***None of your friends is ranked in squash yet*** (call 14), and the table appears **with one listed friend** (Q7) |
| 10 | the brief | *The ranking uses the player skill level. This is an initial idea* | **The level itself is the ranked number** (Q15): never a second number |
| 11 | rankings 7–11; the brief | Form dots for *the last five competitive games* | **The last five results with a winner** in that sport, the record's Run of form: *Played · no score* and disputed games are not in it (Q6) |

## Index

| # | File | Original name |
| --- | --- | --- |
| 1 | [`01_ranking_button_home.png`](mocks/01_ranking_button_home.png) | `1-ranking_button_home.png` |
| 2 | [`02_ranking_header.png`](mocks/02_ranking_header.png) | `2-ranking_header.png` |
| 3 | [`03_your_place_card.png`](mocks/03_your_place_card.png) | `3_your_place_card.png` |
| 4 | [`04_rankings_screen_1.png`](mocks/04_rankings_screen_1.png) | `4_rankings_screen1.png` |
| 5 | [`05_rankings_screen_2.png`](mocks/05_rankings_screen_2.png) | `5_rankings_screen2.png` |
| 6 | [`06_rankings_podium.png`](mocks/06_rankings_podium.png) | `6_rankings_podium.png` |
| 7 | [`07_top_three.png`](mocks/07_top_three.png) | `7_top_three.png` |
| 8 | [`08_ranking_up.png`](mocks/08_ranking_up.png) | `8_ranking_up.png` |
| 9 | [`09_ranking_down.png`](mocks/09_ranking_down.png) | `9_ranking_down.png` |
| 10 | [`10_ranking_same.png`](mocks/10_ranking_same.png) | `10_ranking_same.png` |
| 11 | [`11_ranking_you.png`](mocks/11_ranking_you.png) | `11_ranking_you.png` |
