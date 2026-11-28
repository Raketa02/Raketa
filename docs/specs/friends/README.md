# Friends: the spec set

**What PRD [#743](https://github.com/Rakieta02/Rakieta/issues/743) is drawn from.** The product owner's
Friends brief and its twelve mocks, copied here from `rakieta_v2.0/4-features/3-Friends` so that every
session can read them, then grilled on 2026-11-05/06 (Q1–Q46 there, the
[games and fill-in mechanics' Q128](../games-and-fill-in/the-mechanics.md#appendix-c--decision-log)).
Landed by [#744](https://github.com/Rakieta02/Rakieta/issues/744) on 2026-11-06.

| File | What it holds |
| --- | --- |
| [the-mechanics.md](the-mechanics.md) | What happens: friendship, the link, asking for a level, official groups' courts hour by hour, the friends game, its money, its empty seats and its leaving, with every number |
| [the-screens.md](the-screens.md) | How each screen looks and behaves, and which mock draws it |
| [`mocks/`](mocks/) | The twelve mocks, renamed (the [index](#index) gives each original name) |
| [friends_feature.md](friends_feature.md) | The product owner's brief, verbatim but for the brand's spelling ([ADR-0211](../../adr/0211-the-brand-is-rakieta-everywhere.md) §6). Its paths point at the product owner's desktop: read `…/3-Friends/N_….png` as `mocks/NN_….png`. Where the brief and these documents disagree, these documents win: they carry the grilling's rulings |

**The decision** is [ADR-0202](../../adr/0202-friends-a-request-between-group-mates-and-a-game-among-them-that-books-the-court-when-it-is-sent.md).
The terms are in the root [`CONTEXT.md`](../../../CONTEXT.md), under **Friends**, and under
**Bookings** (*Friends game*, *Invited seat*, *Guest*, *Split · Whole court*), **Payments**
(*Cover*) and **Proposals** (*Friends card*). Every sentence a player reads is in
[the words §29](../matchmaking/the-words.md#29-friends). The rules a friends game shares with every
other game — the cut-off, holding, rescues, leaving after the cut-off — are the
[games and fill-in mechanics](../games-and-fill-in/the-mechanics.md)', and are cited, never restated.

## How to read the mocks

1. **The mocks lead on design.** Where a mock and a sentence disagree on a look, the mock wins,
   unless PRD #743, ADR-0202 or a ticket overrides it **by name**. Every override known today is
   under [*Overrides*](#overrides), and nothing here overrides silently. On a rule, the mechanics win:
   *"the mock is just a mock"* (the product owner, Q10).
2. **Every name, number, price and date in a mock is mock data.** *Karol T.*, *Wisła Park*,
   *25 zł each*, *Sat 26 Sep* all come from the backend and, for testing, from the seeds.
3. **The mocks predate four rulings that hold everywhere**:
   - a player is named by their **nickname**, never with an @
     ([ADR-0199](../../adr/0199-a-player-is-known-by-their-nickname.md)), so *Karol T.* reads as a
     nickname;
   - the mocks show `rakieta.app/…`: read the configured public site's address
     ([ADR-0187](../../adr/0187-four-deployables-the-club-website-and-the-public-site-live-in-this-repo.md)
     §7). Their *Rakieta* is the brand as written ([ADR-0211](../../adr/0211-the-brand-is-rakieta-everywhere.md));
   - a group page has **three tabs, Games · Fill in · Friends**, and the header opens Info (Q125);
   - the bottom bar is **Home · ⚡ Play · You** (#576), as every mock already draws.
4. **Cite a mock by number**: *friends 7*. The numbers are the product owner's.

## Which parts of each mock lead

| # | Mock | What leads | What doesn't |
| --- | --- | --- | --- |
| 1 | Members with **+ Add** and *friend* | The black **+ Add** pill and the green *friend* tag, their size and place on the right of a row | **The rows themselves.** Members keeps today's row design ([*Overrides*](#overrides), note 1) |
| 2 | Members with *request sent* | The amber *request sent* tag | The rows, as in mock 1 |
| 3 | The Friends page as a picker | The list's card, rows (face, nickname, *2,75 · established*, a circle), **+ Add friends** top right, **Done** at the foot | Nothing; from You the page has tabs instead ([the screens §4](the-screens.md#4-the-friends-page)) |
| 4 | The **Add friends** sheet | The sheet, its groups card (*8 members · 2 to add*, a chevron) and the link card with **Copy** | The link's code (note 4); it gains a small **New link** |
| 5 | A friend request card on Home | The row title *FRIEND REQUESTS · 1*, the card, *With you in Kazimierz crew · Padel 3,40 · ✦ 98*, **Not now** / **Accept** | Nothing |
| 6 | The picker, full | Picked rows ticked, the rest greyed | Nothing |
| 7 | The court, seated | The court with sides, faces, *nickname level* labels and each friend's × | The tab bar's *Info* (note 2); which side each face sits on (note 3); the **Competitive / For fun** switch above the court, which becomes the Friends tab's menu (note 9) |
| 8 | The Friends tab, court and card | The court above the card, the card's layout, **Send game and pay 25 zł** (volt) and **Pick a different court** | The sides, where the court and the card disagree (note 3) |
| 9 | The friends card | The deck card's parts without tiles: the *vs* line, the percentage, the balance bar, the overlap grid, the court panel with *Court available* and the share | *Overlap next week*: the label is the deck's own grade, *High / Good / Slim overlap* (note 6) |
| 10 | *Find a court*, everybody free | The sheet, its day headings, the rows (*19:00 · Bonarka Arena · Court 2 · 32 zł each · Everybody free*), the brightest tint | The game header behind the sheet (note 3) |
| 11 | *Find a court*, scrolled | The day headings and the row layout | *Outside your shared slots* greyed (note 5); the header behind it (note 3) |
| 12 | A friends game invitation on Home | *FRIENDS GAME · 1*, *Karol's game*, the clock, the four faces (✓ on those In, faded on those still to answer, *You*), **Not this time** / **Accept and pay 25 zł** | The line under the faces gains the kind (note 7) |

**No mock draws:** the record's **Add friend** / **Block** row, the **Accept** pill on Members, the
result screen's **PLAYED WITH** card, the Friends page's three tabs from You, the card's loading
state, the blocked-pair sentence, *Ask … to get a padel level*, the send sheet, the sender's game
in Your games, the empty-seat actions, the two-way leave sheet, the cover warning, the public site's
`/f/` page and the club website's new lines. Each is designed in [the-screens.md](the-screens.md)
from the mocks' own parts and the design system, and named there as designed, not drawn.

## Overrides

Each is a ruling of the friends grilling, a call in PRD #743, or a rule from an earlier record;
note 9 is a later decision, PRD [#859](https://github.com/Rakieta02/Rakieta/issues/859), whose record
is [`docs/specs/tab-menu/`](../tab-menu/README.md). The mock is correct everywhere else.

| Note | Mock | What it draws | What is built |
| --- | --- | --- | --- |
| 1 | friends 1, 2 | Members rows redrawn: *Kuba W.*, a reliability chip, *Padel 2,80* | **Members rows keep today's design**; only the pill or tag on the right comes from the mocks. A row also shows a black **Accept** for somebody who asked you (Q2), which no mock draws. The administrator's Members view has no pills |
| 2 | friends 7 | A fourth tab, *Info* | **Mock 7's *Info* tab is stale**: three tabs, and Info opens from the group's header (Q125) |
| 3 | friends 7, 8, 10, 11 | Mock 8's court seats *You + Zofia* against *Ania + Ewa*, while its card reads *YOU + EWA VS ZOFIA + ANIA*; mock 7 seats *You + Staś* against *Filip + Magda*. Mocks 10–11 draw a game header behind the sheet, *Ewa, Ania, Zofia · Padel · withdrawn* | **Mocks 7 and 8 disagree about sides, and the evenest-sides rule decides**: Done seats the picks into the evenest sides, a swap moves them, and the court and the card always name the same sides, your side on the left of the bar (Q10, Q70). **The game header behind mocks 10–11's sheet is a leftover**: the sheet opens over the Friends tab |
| 4 | friends 4 | `rakieta.app/f/tomek-k`, a link made from the nickname | **A random code**, `<public site>/f/<code>`, nobody can guess, and a small **New link** under it that turns the old one off (Q9) |
| 5 | friends 11 | Rows outside the four's shared hours greyed, *Outside your shared slots* | **Every row is tinted by how many of the four are free** at that hour, brightest for all four, dimmer for three, two, one, and labelled *Everybody free*, *Ania busy* or *Magda and Ania busy*. **Every row can be picked** (Q36) |
| 6 | friends 9 | *Overlap next week* | The deck's grade, *High / Good / Slim overlap*, as mock 8 draws it (*Slim overlap*) and the deck card does (games and fill-in Q71) |
| 7 | friends 12 | *Saturday 10:00 · Wisła Park · Court 3 · Padel* | The line names the kind too: *Saturday 10:00 · Ogrody 33 · Court 3 · Padel · Competitive* (Q15). With Whole court the button is **Accept** and a line reads *Tomek paid the court* (Q29) |
| 8 | friends 8, 9 | **Send game and pay 25 zł** sends at once | It opens the **send sheet**, which asks how to pay and carries the order button with the maximum above it (call 8) |
| 9 | friends 7 | The **Competitive / For fun** switch above the court, on screen all the time | **The Friends tab's menu** (2026-11-24, [#859](https://github.com/Rakieta02/Rakieta/issues/859), decided and not yet built): a chevron on the selected Friends tab, and a tap on it opens a menu aligned to the tab's right edge, Competitive then For fun, with a coral tick and **no counts and no door**. It still sets this game's kind only. The court sits right under the tabs, at its own size ([the screens §7.1](the-screens.md#71-the-court); the tab menu's [mocks 2 and 4](../tab-menu/README.md), illustrations) |

## Index

| # | File | Original name |
| --- | --- | --- |
| 1 | [`01_members_friends_add.png`](mocks/01_members_friends_add.png) | `1.members_friends_add.png` |
| 2 | [`02_members_friends_request_waiting.png`](mocks/02_members_friends_request_waiting.png) | `2_members_freinds_request_waiting.png` |
| 3 | [`03_friends_screen.png`](mocks/03_friends_screen.png) | `3_Friends_screen.png` |
| 4 | [`04_add_friends_bottom_dialog.png`](mocks/04_add_friends_bottom_dialog.png) | `4_add_friends_bottom_dislog.png` |
| 5 | [`05_request_card.png`](mocks/05_request_card.png) | `5_reqeust_card.png` |
| 6 | [`06_friends_greyed_out.png`](mocks/06_friends_greyed_out.png) | `6_freinds_grayed_out.png` |
| 7 | [`07_graphic_court_filled.png`](mocks/07_graphic_court_filled.png) | `7_graphic_court_filled.png` |
| 8 | [`08_friends_and_game.png`](mocks/08_friends_and_game.png) | `8_friends_and_game.png` |
| 9 | [`09_friends_game_card.png`](mocks/09_friends_game_card.png) | `9_friends_game_card.png` |
| 10 | [`10_find_court_1.png`](mocks/10_find_court_1.png) | `10_find_court_1.png` |
| 11 | [`11_find_court_2.png`](mocks/11_find_court_2.png) | `11_find_court_2.png` |
| 12 | [`12_game_friend_invitation.png`](mocks/12_game_friend_invitation.png) | `12_game_friend_invitation.png` |

The group page's own Friends mocks, *play 49–55* (the empty court, its four sports and the empty
picker), stay in [`../play-groups/mocks/play/`](../play-groups/README.md#overrides) and still lead on
the empty court.
